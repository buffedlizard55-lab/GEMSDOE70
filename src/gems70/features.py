"""Multi-scale physical, geothermal, bedrock, and collar-safe fault-anatomy features.

Every feature is strictly derived from:
  1. Official GEMS `training_features.tif` (all 19 channels verified by exact
     GDAL band description name, 100 m EPSG:32611, nodata `-3.4028235e+38` masked),
  2. SHA-256 verified open U.S. federal datasets in `.cache/data/external/`
     (USGS 3DEP 10 m DEM & 1 m Earth MRI LiDAR, USGS GeoDAWN radiometrics &
     upward-continued magnetics, USGS SGMC raw 100 m bedrock fault traces, and
     DOE GDR-1391 INGENIOUS thermal springs, 2 m temperature probes, paleo
     sinter/travertine deposits, volcanic vents, and recorded slip-sense table),
  3. Inside any holdout fold, ONLY `fold["visible"]` (with collar-safe floor
     `d_eff = maximum(d_vis, 3.2)` pixels so the `buffer_px = 3` holdout collar
     can never leak into split thresholds).
"""
from __future__ import annotations

import csv
import gc
import json
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi

from gems57 import relay_bend_anatomy
from gems57.grid import Grid

COLLAR_SAFE_PX: float = 3.2


@dataclass(frozen=True)
class FeatureStack:
    """Footprint-indexed physical feature matrix and auxiliary domain fields."""

    X: np.ndarray  # float32 (N_fp, F)
    names: tuple[str, ...]
    domains: tuple[str, ...]
    relief_fp: np.ndarray  # float32 (N_fp,) local topographic relief proxy
    domain_scores: dict[str, np.ndarray]  # domain -> [0, 1] rank score on fp
    sgmc_raw_fp: np.ndarray  # float32 (N_fp,) raw un-dilated SGMC indicator
    blind_hydro_fp: np.ndarray  # float32 (N_fp,) thermal/2m-probe/sinter score
    sense_src_2d: np.ndarray  # int8 (H, W) unmasked sense raster gated by `known_mask`


def _fill_footprint(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Cleanly replace float32 sentinel nodata (`-3.4e38`) and non-finite cells."""
    out = np.asarray(arr, dtype=np.float32).copy()
    valid = fp & np.isfinite(out) & (np.abs(out) < 1e20)
    med = float(np.median(out[valid])) if np.any(valid) else 0.0
    out[~valid] = med
    return out


def _rank01(v: np.ndarray) -> np.ndarray:
    """Exact empirical quantile rank in [0, 1] over finite 1-D vector."""
    n = v.shape[0]
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(n, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, n, dtype=np.float32)
    return ranks


def _grad_xy(field: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gy = ndi.sobel(field, axis=0).astype(np.float32) * 0.125
    gx = ndi.sobel(field, axis=1).astype(np.float32) * 0.125
    mag = np.hypot(gx, gy).astype(np.float32)
    return gx, gy, mag


def _cross_grad_coupling(
    gx1: np.ndarray,
    gy1: np.ndarray,
    m1: np.ndarray,
    gx2: np.ndarray,
    gy2: np.ndarray,
    m2: np.ndarray,
) -> np.ndarray:
    """Collinear structural gradient strength (Gallardo & Meju, 2004)."""
    denom = m1.astype(np.float64) * m2.astype(np.float64) + 1e-6
    num = np.abs(gx1.astype(np.float64) * gy2.astype(np.float64) - gy1.astype(np.float64) * gx2.astype(np.float64))
    collinear = np.clip(1.0 - num / denom, 0.0, 1.0)
    return (np.sqrt(np.maximum(m1.astype(np.float64) * m2.astype(np.float64), 0.0)) * collinear).astype(np.float32)


def _oriented_worm_contrast(mag: np.ndarray, length_px: int = 15, flank_px: float = 5.0) -> np.ndarray:
    """8-orientation strike-coherent lineament response minus regional background."""
    angles = (0.0, 22.5, 45.0, 67.5, 90.0, 112.5, 135.0, 157.5)
    half = length_px // 2
    t = np.arange(-half, half + 1, dtype=np.float32)
    best = np.full(mag.shape, -1e30, dtype=np.float32)
    size = 2 * half + 1
    for deg in angles:
        rad = np.deg2rad(deg)
        rr = np.round(half + t * np.sin(rad)).astype(int)
        cc = np.round(half + t * np.cos(rad)).astype(int)
        kern = np.zeros((size, size), dtype=np.float32)
        kern[rr, cc] = 1.0
        kern /= float(kern.sum())
        resp = ndi.convolve(mag, kern, mode="nearest")
        np.maximum(best, resp, out=best)
    bg = ndi.gaussian_filter(mag, sigma=flank_px, mode="nearest")
    return (best - bg).astype(np.float32)


def _multiscale_hessian_ridge(elev: np.ndarray, sigmas: tuple[float, ...] = (1.2, 2.8)) -> tuple[np.ndarray, np.ndarray]:
    """Scale-normalized Hessian ridge strength and Walker Lane / Great Basin strike alignment."""
    best_ridge = np.zeros(elev.shape, dtype=np.float32)
    best_align = np.zeros(elev.shape, dtype=np.float32)
    s_nw = (np.cos(np.deg2rad(145.0)), np.sin(np.deg2rad(145.0)))
    s_nne = (np.cos(np.deg2rad(18.0)), np.sin(np.deg2rad(18.0)))
    for sig in sigmas:
        hxx = ndi.gaussian_filter(elev, sigma=sig, order=(0, 2), mode="nearest") * (sig ** 2)
        hyy = ndi.gaussian_filter(elev, sigma=sig, order=(2, 0), mode="nearest") * (sig ** 2)
        hxy = ndi.gaussian_filter(elev, sigma=sig, order=(1, 1), mode="nearest") * (sig ** 2)
        tr = hxx + hyy
        disc = np.hypot(hxx - hyy, 2.0 * hxy)
        lam1 = 0.5 * (tr + disc)
        lam2 = 0.5 * (tr - disc)
        use_abs_max = np.abs(lam2) > np.abs(lam1)
        dom = np.where(use_abs_max, np.abs(lam2), np.abs(lam1))
        sub = np.where(use_abs_max, np.abs(lam1), np.abs(lam2))
        aniso = np.clip(1.0 - sub / (dom + 1e-6), 0.0, 1.0)
        ridge = (dom * aniso).astype(np.float32)
        nx = 2.0 * hxy
        ny = (hyy - hxx) + disc
        nrm = np.hypot(nx, ny) + 1e-8
        tx = -ny / nrm
        ty_north = -nx / nrm
        align_nw = np.abs(tx * s_nw[0] + ty_north * s_nw[1])
        align_nne = np.abs(tx * s_nne[0] + ty_north * s_nne[1])
        align = np.maximum(align_nw, align_nne).astype(np.float32)
        upd = ridge > best_ridge
        best_ridge = np.where(upd, ridge, best_ridge)
        best_align = np.where(upd, align, best_align)
    return best_ridge, best_align


def _read_u8_norm(path: Path, band: int, fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Read quantized uint8 band (`0 == nodata`, `1..255` scaled linearly to `[0, 1]`)."""
    with rasterio.open(path) as src:
        raw = src.read(band)
    valid = fp & (raw > 0)
    val = np.zeros(raw.shape, dtype=np.float32)
    val[valid] = (raw[valid].astype(np.float32) - 1.0) / 254.0
    if np.any(valid) and not np.all(valid[fp]):
        val[fp & ~valid] = float(np.median(val[valid]))
    return val, valid


def _point_seed_distance_px(shape: tuple[int, int], rows: list[int], cols: list[int]) -> np.ndarray:
    seed = np.zeros(shape, dtype=bool)
    h, w = shape
    for r, c in zip(rows, cols):
        if 0 <= r < h and 0 <= c < w:
            seed[r, c] = True
    if not np.any(seed):
        return np.full(shape, 500.0, dtype=np.float32)
    return ndi.distance_transform_edt(~seed).astype(np.float32)


def _load_sense_raster(grid: Grid, csv_path: Path) -> np.ndarray:
    """Rasterize INGENIOUS segment slip-sense (`N=1, RL=2, LL=3`), strictly masked by `visible` later."""
    from rasterio.features import rasterize

    shapes_by_code: dict[int, list] = {1: [], 2: [], 3: []}
    code_map = {"N": 1, "RL": 2, "LL": 3}
    with csv_path.open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            s = (row.get("sense") or "").strip().upper()
            code = code_map.get(s)
            if code is None:
                continue
            try:
                x0, y0 = float(row["x0"]), float(row["y0"])
                x1, y1 = float(row["x1"]), float(row["y1"])
            except (KeyError, ValueError):
                continue
            shapes_by_code[code].append(({"type": "LineString", "coordinates": [(x0, y0), (x1, y1)]}, code))

    all_shapes = shapes_by_code[1] + shapes_by_code[2] + shapes_by_code[3]
    if not all_shapes:
        return np.zeros(grid.shape, dtype=np.int8)
    return rasterize(all_shapes, out_shape=grid.shape, transform=grid.transform, fill=0, dtype="int8", all_touched=True)


def _load_gdr_geothermal_fields(grid: Grid, ext_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build distance-decay proximity fields from open DOE GDR-1391 point surveys."""
    h, w = grid.shape
    fp = grid.footprint
    inv_tf = ~grid.transform

    hot_r, hot_c, warm_r, warm_c = [], [], [], []
    with (ext_dir / "gdr_wellspring_in_footprint.csv").open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError):
                continue
            tc = float(row["temp_c"]) if row.get("temp_c") not in (None, "", "nan") else 0.0
            qtz = float(row["geothermquartz_c"]) if row.get("geothermquartz_c") not in (None, "", "nan") else 0.0
            cls = (row.get("thermalclass") or "").strip().lower()
            if tc >= 35.0 or qtz >= 90.0 or cls in ("hot", "boiling"):
                hot_r.append(r)
                hot_c.append(c)
            elif tc >= 20.0 or qtz >= 60.0 or cls == "warm":
                warm_r.append(r)
                warm_c.append(c)

    probe_hi_r, probe_hi_c = [], []
    with zipfile.ZipFile(ext_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip") as zf:
        dbf = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf")
    num_rec, hdr_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields = []
    pos = 32
    while pos < hdr_len - 1:
        fname = dbf[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        flen = dbf[pos + 16]
        fields.append((fname, flen))
        pos += 32
    lons, lats = [], []
    for i in range(num_rec):
        rec = dbf[hdr_len + i * rec_len : hdr_len + (i + 1) * rec_len]
        if not rec or rec[0:1] == b"*":
            continue
        off = 1
        vals = {}
        for fname, flen in fields:
            vals[fname] = rec[off : off + flen].decode("ascii", errors="ignore").strip()
            off += flen
        try:
            lon = float(vals["LongDegree"])
            lat = float(vals["LatDegreeN"])
            f2m = float(vals["F2mDAB"]) if vals["F2mDAB"] else 0.0
        except ValueError:
            continue
        if f2m >= 1.2:
            lons.append(lon)
            lats.append(lat)
    if lons:
        xs, ys = warp_transform("EPSG:4269", grid.crs, lons, lats)
        for x, y in zip(xs, ys):
            col_f, row_f = inv_tf * (x, y)
            r, c = int(round(row_f)), int(round(col_f))
            if 0 <= r < h and 0 <= c < w and fp[r, c]:
                probe_hi_r.append(r)
                probe_hi_c.append(c)

    paleo_r, paleo_c, p_lons, p_lats = [], [], [], []
    with zipfile.ZipFile(ext_dir / "paleo_geothermal_regional.zip") as zf:
        txt = zf.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace").splitlines()
    for row in csv.DictReader(txt):
        try:
            p_lons.append(float(row["Long_deg_NAD83"]))
            p_lats.append(float(row["Lat_deg_NAD83"]))
        except (KeyError, ValueError):
            continue
    if p_lons:
        xs, ys = warp_transform("EPSG:4269", grid.crs, p_lons, p_lats)
        for x, y in zip(xs, ys):
            col_f, row_f = inv_tf * (x, y)
            r, c = int(round(row_f)), int(round(col_f))
            if 0 <= r < h and 0 <= c < w and fp[r, c]:
                paleo_r.append(r)
                paleo_c.append(c)

    vent_r, vent_c = [], []
    with (ext_dir / "gdr_volcanic_vents_in_footprint.csv").open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            try:
                vent_r.append(int(float(row["row"])))
                vent_c.append(int(float(row["col"])))
            except (KeyError, ValueError):
                continue

    d_hot = _point_seed_distance_px(grid.shape, hot_r + warm_r, hot_c + warm_c)
    d_probe_paleo = _point_seed_distance_px(grid.shape, probe_hi_r + paleo_r, probe_hi_c + paleo_c)
    d_strict_upflow = _point_seed_distance_px(grid.shape, hot_r + probe_hi_r + paleo_r, hot_c + probe_hi_c + paleo_c)
    d_vent = _point_seed_distance_px(grid.shape, vent_r, vent_c)

    return (
        -np.log1p(np.minimum(d_hot[fp], 25.0)).astype(np.float32),
        -np.log1p(np.minimum(d_probe_paleo[fp], 25.0)).astype(np.float32),
        -np.log1p(np.minimum(d_vent[fp], 30.0)).astype(np.float32),
        np.exp(-d_strict_upflow[fp] / 10.0).astype(np.float32),
    )


def build_physical_feature_stack(grid: Grid, data_dir: Path) -> FeatureStack:
    """Construct or load memory-mapped zero-catalogue 4-domain physical FeatureStack."""
    cache_dir = data_dir.parent / "feature_stack_v1"
    meta_file = cache_dir / "meta.json"
    x_file = cache_dir / "X.npy"
    aux_file = cache_dir / "aux.npz"
    if meta_file.exists() and x_file.exists() and aux_file.exists():
        meta = json.loads(meta_file.read_text())
        X_mm = np.load(x_file, mmap_mode="r")
        aux = np.load(aux_file)
        return FeatureStack(
            X=X_mm,
            names=tuple(meta["names"]),
            domains=tuple(meta["domains"]),
            relief_fp=aux["relief_fp"],
            domain_scores={
                "geomorph": aux["dom_geomorph"],
                "potential": aux["dom_potential"],
                "hydrothermal": aux["dom_hydro"],
                "geodesy": aux["dom_geodesy"],
            },
            sgmc_raw_fp=aux["sgmc_raw_fp"],
            blind_hydro_fp=aux["blind_hydro_fp"],
            sense_src_2d=aux["sense_src_2d"],
        )

    cache_dir.mkdir(parents=True, exist_ok=True)
    fp = grid.footprint
    n_fp = int(fp.sum())
    ext_dir = data_dir / "external"

    cols: list[np.ndarray] = []
    names: list[str] = []
    domains: list[str] = []

    def add(name: str, domain: str, vec_fp: np.ndarray) -> np.ndarray:
        v = np.asarray(vec_fp, dtype=np.float32)
        v = np.where(np.isfinite(v), v, np.nanmedian(v) if np.any(np.isfinite(v)) else 0.0).astype(np.float32)
        cols.append(v)
        names.append(name)
        domains.append(domain)
        return v

    tf_path = data_dir / "training_features.tif"
    with rasterio.open(tf_path) as src:
        band_by_name = {
            desc.split(" - ", 1)[0].strip(): idx
            for idx, desc in enumerate(src.descriptions, start=1)
        }
        expected_19 = {
            "mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope", "tc",
            "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15", "iso_grav_anom_vg",
            "det_elev", "iso_grav_anom", "tmi", "depth_to_base_surf", "ieq_n100a15",
            "cond_surf", "iso_grav_anom_hg", "det_elev_slope",
        }
        if set(band_by_name.keys()) != expected_19:
            raise ValueError(f"Unexpected band descriptions in training_features.tif: {band_by_name}")

        def read_tf(short_name: str) -> np.ndarray:
            return _fill_footprint(src.read(band_by_name[short_name]), fp)

        # --- Domain 1: Multi-scale Geomorphology (100 m + 10 m 3DEP + chi/ksn + 1 m LiDAR) ---
        det_elev = read_tf("det_elev")
        det_slope = read_tf("det_elev_slope")

        hess_ridge, strike_align = _multiscale_hessian_ridge(det_elev, sigmas=(1.2, 2.8))
        scarp_worm = _oriented_worm_contrast(det_slope, length_px=15, flank_px=5.0)
        slope_local_anom = det_slope - ndi.gaussian_filter(det_slope, sigma=8.0, mode="nearest")
        gx_topo, gy_topo, m_topo = _grad_xy(det_elev)

        add("det_elev_slope", "geomorph", det_slope[fp])
        add("det_slope_local_anom", "geomorph", slope_local_anom[fp])
        add("hessian_ridge_multiscale", "geomorph", hess_ridge[fp])
        f_scarp_worm = add("scarp_worm_1500m", "geomorph", scarp_worm[fp])
        add("tectonic_strike_align", "geodesy", strike_align[fp])

        del hess_ridge, strike_align, scarp_worm, slope_local_anom, det_elev, det_slope
        gc.collect()

        # 10 m USGS 3DEP derived bands (100% coverage)
        topo10_path = ext_dir / "topo_10m_derived_100m_u8.tif"
        t10_slope_p90, _ = _read_u8_norm(topo10_path, 1, fp)
        t10_relief, _ = _read_u8_norm(topo10_path, 5, fp)
        t10_curv_prof, _ = _read_u8_norm(topo10_path, 6, fp)
        t10_aspect_coh, _ = _read_u8_norm(topo10_path, 7, fp)
        t10_hs_lin, _ = _read_u8_norm(topo10_path, 8, fp)

        piedmont_scarp = (t10_slope_p90 * t10_aspect_coh) - ndi.gaussian_filter(
            t10_slope_p90 * t10_aspect_coh, sigma=10.0, mode="nearest"
        )
        relief_fp = t10_relief[fp].astype(np.float32)

        f_t10_curv = add("topo10_curv_prof_absmax", "geomorph", t10_curv_prof[fp])
        f_t10_coh = add("topo10_aspect_coherence", "geomorph", t10_aspect_coh[fp])
        add("topo10_hs_lineament", "geomorph", t10_hs_lin[fp])
        f_piedmont = add("topo10_piedmont_scarp_anom", "geomorph", piedmont_scarp[fp])

        # 10 m hydrologically conditioned chi-step & ksn knickpoint bands (100% coverage)
        with rasterio.open(ext_dir / "dem10_chi_100m_i16.tif") as chi_src:
            chi_step_raw = chi_src.read(1).astype(np.float32)
            ksn_raw = chi_src.read(3).astype(np.float32)
        chi_step = _fill_footprint(
            np.where((chi_step_raw > -32000) & fp, np.log1p(np.maximum(chi_step_raw, 0.0)), np.nan), fp
        )
        ksn = _fill_footprint(
            np.where((ksn_raw > -32000) & fp, np.log1p(np.maximum(ksn_raw, 0.0)), np.nan), fp
        )
        ksn_anom = ksn - ndi.gaussian_filter(ksn, sigma=10.0, mode="nearest")

        add("dem10_chi_step_log", "geomorph", chi_step[fp])
        f_ksn = add("dem10_ksn_knickzone_anom", "geomorph", ksn_anom[fp])
        del chi_step_raw, ksn_raw, chi_step, ksn, ksn_anom
        gc.collect()

        # 1 m Earth MRI LiDAR scarplet channels quantile-fused across non-LiDAR gap
        lidar_path = ext_dir / "lidar_scarp_features_u8.tif"
        li_ex_max, li_valid_mask = _read_u8_norm(lidar_path, 1, fp)
        li_ex_mean, _ = _read_u8_norm(lidar_path, 2, fp)
        li_step, _ = _read_u8_norm(lidar_path, 3, fp)
        li_lapneg, _ = _read_u8_norm(lidar_path, 4, fp)
        li_lappos, _ = _read_u8_norm(lidar_path, 5, fp)
        li_down, _ = _read_u8_norm(lidar_path, 6, fp)
        li_up, _ = _read_u8_norm(lidar_path, 7, fp)
        li_coh, _ = _read_u8_norm(lidar_path, 10, fp)

        li_valid_f = li_valid_mask[fp].astype(np.float32)
        scarplet_raw = (np.maximum(li_up, li_down) * (0.5 + 0.5 * li_coh))[fp]
        dipole_raw = np.sqrt(np.maximum(li_lapneg * li_lappos, 0.0))[fp]
        step_raw = (li_step * (0.5 + 0.5 * li_coh))[fp]
        dist_ratio = (li_ex_mean / (li_ex_max + 0.02))[fp]

        proxy_rank = _rank01((t10_curv_prof * (0.5 + 0.5 * t10_aspect_coh))[fp])
        li_sub = li_valid_mask[fp]
        for arr_li, feat_name in (
            (scarplet_raw, "lidar_scarplet_rank_fused"),
            (dipole_raw, "lidar_crest_toe_dipole_fused"),
            (step_raw, "lidar_step_coh_fused"),
        ):
            r_all = np.empty(n_fp, dtype=np.float32)
            r_all[li_sub] = _rank01(arr_li[li_sub])
            r_all[~li_sub] = proxy_rank[~li_sub]
            add(feat_name, "geomorph", r_all)
        dist_med = float(np.median(dist_ratio[li_sub])) if np.any(li_sub) else 0.5
        add("lidar_distributed_damage_ratio", "geomorph", np.where(li_sub, dist_ratio, dist_med).astype(np.float32))
        add("lidar_coverage_flag", "geomorph", li_valid_f)

        f_li_scarp = cols[-5]
        del (
            t10_slope_p90, t10_relief, t10_curv_prof, t10_aspect_coh, t10_hs_lin, piedmont_scarp,
            li_ex_max, li_ex_mean, li_step, li_lapneg, li_lappos, li_down, li_up, li_coh,
        )
        gc.collect()

        # --- Domain 2: Potential Fields, Cross-Gradients, Worms & Shallow Magnetite Destruction ---
        rtp = read_tf("rtp")
        tmi_hg = read_tf("tmi_hg")
        tilt_c = read_tf("tc")
        tmi_vg = read_tf("tmi_vg")
        grav = read_tf("iso_grav_anom")
        grav_slope = read_tf("iso_grav_anom_slope")
        grav_vg = read_tf("iso_grav_anom_vg")
        grav_hg = read_tf("iso_grav_anom_hg")
        depth_base = read_tf("depth_to_base_surf")

        gx_mag, gy_mag, m_mag = _grad_xy(rtp)
        gx_grv, gy_grv, m_grv = _grad_xy(grav)
        _, _, m_base = _grad_xy(depth_base)

        xg_topo_grav = _cross_grad_coupling(gx_topo, gy_topo, m_topo, gx_grv, gy_grv, m_grv)
        xg_topo_mag = _cross_grad_coupling(gx_topo, gy_topo, m_topo, gx_mag, gy_mag, m_mag)
        xg_grav_mag = _cross_grad_coupling(gx_grv, gy_grv, m_grv, gx_mag, gy_mag, m_mag)

        mag_worm = _oriented_worm_contrast(tmi_hg, length_px=15, flank_px=5.0)
        grav_worm = _oriented_worm_contrast(grav_slope, length_px=15, flank_px=5.0)
        base_worm = _oriented_worm_contrast(m_base, length_px=15, flank_px=6.0)

        tmi_up150, _ = _read_u8_norm(ext_dir / "geodawn_extensions_u8.tif", 4, fp)
        _, _, m_up150 = _grad_xy(tmi_up150)
        shallow_demag = _rank01(tmi_hg[fp]) - _rank01(m_up150[fp])

        add("rtp_local_anom", "potential", (rtp - ndi.gaussian_filter(rtp, sigma=12.0, mode="nearest"))[fp])
        add("tmi_hg", "potential", tmi_hg[fp])
        add("tilt_abs_zero_crossing", "potential", -np.abs(tilt_c[fp]))
        add("tmi_vg_abs", "potential", np.abs(tmi_vg[fp]))
        add("iso_grav_slope", "potential", grav_slope[fp])
        add("iso_grav_vg_abs", "potential", np.abs(grav_vg[fp]))
        add("iso_grav_hg", "potential", grav_hg[fp])
        add("depth_to_basement_km", "potential", depth_base[fp])
        f_base_worm = add("basement_step_worm_1500m", "potential", base_worm[fp])
        f_xg_tg = add("xgrad_topo_gravity", "potential", xg_topo_grav[fp])
        f_xg_tm = add("xgrad_topo_magnetics", "potential", xg_topo_mag[fp])
        add("xgrad_gravity_magnetics", "potential", xg_grav_mag[fp])
        f_mag_worm = add("mag_worm_1500m", "potential", mag_worm[fp])
        f_grav_worm = add("grav_worm_1500m", "potential", grav_worm[fp])
        f_demag = add("shallow_magnetite_destruction", "potential", shallow_demag)

        del (
            gx_topo, gy_topo, m_topo, rtp, tmi_hg, tilt_c, tmi_vg, grav, grav_slope,
            grav_vg, grav_hg, depth_base, gx_mag, gy_mag, m_mag, gx_grv, gy_grv, m_grv,
            m_base, xg_topo_grav, xg_topo_mag, xg_grav_mag, mag_worm, grav_worm, base_worm,
            tmi_up150, m_up150,
        )
        gc.collect()

        # --- Domain 3: Hydrothermal Alteration, Clay-Cap Edges & GDR-1391 Conduits ---
        cond = read_tf("cond_surf")
        _, _, m_cond = _grad_xy(cond)
        cond_anom = cond - ndi.gaussian_filter(cond, sigma=12.0, mode="nearest")

        rad_k, _ = _read_u8_norm(ext_dir / "geodawn_rad_u8.tif", 1, fp)
        ext_thk, _ = _read_u8_norm(ext_dir / "geodawn_extensions_u8.tif", 1, fp)
        ext_uth, _ = _read_u8_norm(ext_dir / "geodawn_extensions_u8.tif", 3, fp)
        k_alter = (rad_k - 0.5 * ext_thk) - ndi.gaussian_filter(rad_k - 0.5 * ext_thk, sigma=12.0, mode="nearest")
        _, _, m_uth = _grad_xy(ext_uth)

        gdr_hot_logd, gdr_probe_logd, gdr_vent_logd, blind_hydro_fp = _load_gdr_geothermal_fields(grid, ext_dir)

        f_cond_edge = add("mt_cond_claycap_edge", "hydrothermal", m_cond[fp])
        add("mt_cond_local_anom", "hydrothermal", cond_anom[fp])
        f_kalter = add("geodawn_potassic_alteration_anom", "hydrothermal", k_alter[fp])
        f_uredox = add("geodawn_uranium_redox_edge", "hydrothermal", m_uth[fp])
        f_gdr_hot = add("gdr_thermal_spring_neglogd", "hydrothermal", gdr_hot_logd)
        f_gdr_probe = add("gdr_2m_probe_paleo_neglogd", "hydrothermal", gdr_probe_logd)
        add("gdr_volcanic_vent_neglogd", "hydrothermal", gdr_vent_logd)

        del cond, m_cond, cond_anom, rad_k, ext_thk, ext_uth, k_alter, m_uth
        gc.collect()

        # --- Domain 4: Active Crustal Strain & Microseismicity ---
        g_inv = read_tf("geod_2ndinv")
        g_shr = read_tf("geod_shearrate")
        g_dil = read_tf("geod_dilaterate")
        eq_dist = read_tf("deq_n100a15")
        eq_int = read_tf("ieq_n100a15")

        transtension = np.sqrt(np.maximum(g_shr, 0.0) * np.abs(g_dil))
        eq_prox = -np.log1p(np.maximum(eq_dist, 0.0)) + np.log1p(np.maximum(eq_int, 0.0))

        f_g2 = add("geod_strain_2ndinv", "geodesy", g_inv[fp])
        f_trans = add("geod_transtension_coupling", "geodesy", transtension[fp])
        add("geod_dilatation_rate", "geodesy", g_dil[fp])
        f_seis = add("seismicity_proximity_intensity", "geodesy", eq_prox[fp])

        del g_inv, g_shr, g_dil, eq_dist, eq_int, transtension, eq_prox
        gc.collect()

    dom_geomorph = (
        0.22 * _rank01(f_li_scarp)
        + 0.20 * _rank01(f_t10_curv)
        + 0.16 * _rank01(f_t10_coh)
        + 0.14 * _rank01(f_piedmont)
        + 0.14 * _rank01(f_scarp_worm)
        + 0.14 * _rank01(f_ksn)
    ).astype(np.float32)
    dom_potential = (
        0.22 * _rank01(f_xg_tg)
        + 0.18 * _rank01(f_xg_tm)
        + 0.20 * _rank01(f_mag_worm)
        + 0.20 * _rank01(f_grav_worm)
        + 0.10 * _rank01(f_base_worm)
        + 0.10 * _rank01(f_demag)
    ).astype(np.float32)
    dom_hydro = (
        0.28 * _rank01(f_gdr_probe)
        + 0.24 * _rank01(f_gdr_hot)
        + 0.18 * _rank01(f_cond_edge)
        + 0.16 * _rank01(f_kalter)
        + 0.14 * _rank01(f_uredox)
    ).astype(np.float32)
    dom_geodesy = (
        0.40 * _rank01(f_trans) + 0.30 * _rank01(f_g2) + 0.30 * _rank01(f_seis)
    ).astype(np.float32)

    with rasterio.open(ext_dir / "sgmc_faults_100m.tif") as s_src:
        sgmc_raw_fp = (s_src.read(1) > 0).astype(np.float32)[fp]

    sense_src_2d = _load_sense_raster(grid, ext_dir / "trace_segments_utm11.csv")
    X_mm_w = np.lib.format.open_memmap(
        x_file, mode="w+", dtype="float32", shape=(n_fp, len(cols))
    )
    for j, col_v in enumerate(cols):
        X_mm_w[:, j] = col_v
    X_mm_w.flush()
    del cols, X_mm_w
    gc.collect()

    np.savez(
        aux_file,
        relief_fp=relief_fp,
        dom_geomorph=dom_geomorph,
        dom_potential=dom_potential,
        dom_hydro=dom_hydro,
        dom_geodesy=dom_geodesy,
        sgmc_raw_fp=sgmc_raw_fp,
        blind_hydro_fp=blind_hydro_fp,
        sense_src_2d=sense_src_2d,
    )
    meta_file.write_text(json.dumps({"names": names, "domains": domains}, indent=2) + "\n")
    X_mm = np.load(x_file, mmap_mode="r")

    return FeatureStack(
        X=X_mm,
        names=tuple(names),
        domains=tuple(domains),
        relief_fp=relief_fp,
        domain_scores={
            "geomorph": dom_geomorph,
            "potential": dom_potential,
            "hydrothermal": dom_hydro,
            "geodesy": dom_geodesy,
        },
        sgmc_raw_fp=sgmc_raw_fp,
        blind_hydro_fp=blind_hydro_fp,
        sense_src_2d=sense_src_2d,
    )


def build_collar_safe_anatomy_features(
    grid: Grid,
    known_mask: np.ndarray,
    phys_corrob_fp: np.ndarray,
    sense_src_2d: np.ndarray | None = None,
) -> tuple[np.ndarray, tuple[str, ...], np.ndarray]:
    """Compute strictly collar-safe (`d >= 3.2 px`) crack-tip, two-host relay & bend features.

    Uses exact shared primitives from `vendor/gems57/relay_bend_anatomy.py`
    (`two_host_frame`, `host_bend_fields`, `kinematic_transition_field`) strictly
    restricted to `known_mask` (`fold["visible"]` in holdout, `grid.catalogue` in
    production), clamping all distances below `COLLAR_SAFE_PX = 3.2` so the
    `buffer_px = 3` holdout collar cannot leak into any split threshold.
    """
    fp = grid.footprint
    ys_fp, xs_fp = np.nonzero(fp)

    th = relay_bend_anatomy.two_host_frame(known_mask)
    bend = relay_bend_anatomy.host_bend_fields(known_mask, fine_px=3.0, coarse_px=9.0)
    trans = (
        relay_bend_anatomy.kinematic_transition_field(known_mask, sense_src_2d, smooth_px=15.0)[fp]
        if sense_src_2d is not None
        else np.zeros(ys_fp.size, dtype=np.float32)
    )

    ay1 = th["iy1"][ys_fp, xs_fp]
    ax1 = th["ix1"][ys_fp, xs_fp]
    ay2 = th["iy2"][ys_fp, xs_fp]
    ax2 = th["ix2"][ys_fp, xs_fp]
    d1_raw = th["d1"][ys_fp, xs_fp]
    d2_raw = th["d2"][ys_fp, xs_fp]

    d1_eff = np.maximum(d1_raw, COLLAR_SAFE_PX)
    d2_eff = np.maximum(d2_raw, COLLAR_SAFE_PX)

    # Local strike at nearest visible host anchor (degrees clockwise from north / image convention in network.local_strike)
    s_anc = bend["strike_fine"][ay1, ax1]
    s_anc = np.where(np.isfinite(s_anc), s_anc, 0.0).astype(np.float32)
    th_rad = np.radians(s_anc)
    # Unit tangent along visible host trace in (dx=east, dy=row-south) coordinates
    tx = np.sin(th_rad).astype(np.float32)
    ty = -np.cos(th_rad).astype(np.float32)

    dy1 = (ys_fp - ay1).astype(np.float32)
    dx1 = (xs_fp - ax1).astype(np.float32)
    d_par_abs = np.abs(dx1 * tx + dy1 * ty)
    d_perp_raw = np.abs(-dx1 * ty + dy1 * tx)
    d_perp_eff = np.maximum(d_perp_raw, COLLAR_SAFE_PX)

    # Two-host step-over relay facing & medial ratio
    dy2 = (ys_fp - ay2).astype(np.float32)
    dx2 = (xs_fp - ax2).astype(np.float32)
    facing = -((dx1 * dx2 + dy1 * dy2) / (d1_raw * d2_raw + 1e-6))
    relay_ratio = d1_eff / (d1_eff + d2_eff)
    relay_bridge = (
        np.clip(0.5 + 0.5 * facing, 0.0, 1.0)
        * (2.0 * relay_ratio)
        * np.exp(-(d1_eff + d2_eff) / 28.0)
    ).astype(np.float32)

    comp_len = th["comp_len"][th["c1"][ys_fp, xs_fp]].astype(np.float32)
    sb_width_px = 1.5 + 0.40 * np.sqrt(np.maximum(comp_len / 10.0, 0.5))
    damage_norm = d1_eff / sb_width_px

    tip_cone = (
        np.exp(-d_perp_eff / 4.5)
        * np.tanh(d_par_abs / 3.5)
        * np.exp(-d_par_abs / 26.0)
    ).astype(np.float32)
    bend_fp = (bend["turn"][ay1, ax1] * np.exp(-d1_eff / 14.0)).astype(np.float32)

    X_anat = np.column_stack(
        [
            np.log1p(d1_eff).astype(np.float32),
            np.log1p(d_perp_eff).astype(np.float32),
            tip_cone,
            relay_bridge,
            bend_fp,
            np.log1p(d2_eff).astype(np.float32),
            np.log1p(damage_norm).astype(np.float32),
            np.log1p(comp_len).astype(np.float32),
            trans.astype(np.float32),
            (tip_cone * phys_corrob_fp).astype(np.float32),
            (relay_bridge * phys_corrob_fp).astype(np.float32),
        ]
    ).astype(np.float32, copy=False)

    anat_names = (
        "vis_log_deff_clamped",
        "vis_log_dperp_clamped",
        "vis_crack_tip_cone",
        "vis_two_host_relay_bridge",
        "vis_host_bend_hinge",
        "vis_log_second_host_deff",
        "vis_savage_brodsky_norm_dist",
        "vis_host_length_logpx",
        "vis_kinematic_sense_transition",
        "vis_tip_x_physical_corrob",
        "vis_relay_x_physical_corrob",
    )

    is_sharp_tip_fp = ((d_par_abs >= 2.0) & (d_perp_raw <= 2.6)).astype(np.float32)
    del th, bend, ay1, ax1, ay2, ax2, d1_raw, d2_raw, dy1, dx1, dy2, dx2
    gc.collect()
    return X_anat, anat_names, is_sharp_tip_fp
