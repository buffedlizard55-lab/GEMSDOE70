"""Phase-5 multi-sensor localized feature extraction, OOF dual-population models,
and exact unblurred 300 m kernel lazy-greedy submodular dot emission.

All algorithms here use ONLY verified geophysical, topographic, LiDAR, radiometric,
geothermal point, and fold-visible fault-trace inputs. Zero prior submission rasters
are ever read by this module.
"""
from __future__ import annotations

import csv
import heapq
import io
import struct
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score


# Exact positive support of the competition's 300 m (3.0 px) triangular kernel on a 100 m grid:
# K(dy, dx) = max(0, 1 - hypot(dy, dx) / 3.0) for hypot(dy, dx) < 3.0 (21 pixels inside 5x5).
KERNEL_300M: tuple[tuple[int, int, float], ...] = tuple(
    (dy, dx, float(1.0 - np.hypot(dy, dx) / 3.0))
    for dy in range(-2, 3)
    for dx in range(-2, 3)
    if np.hypot(dy, dx) < 3.0
)

FEATURE_NAMES: tuple[str, ...] = (
    # --- Official 19-band localized & raw physical channels (24 features) ---
    "b01_mag_anom_hp",
    "b02_rtp_hp",
    "b03_tmi_hg",
    "b04_geod_2ndinv",
    "b05_iso_grav_slope",
    "b06_tc",
    "b07_geod_shearrate",
    "b08_geod_dilaterate",
    "b09_tmi_vg",
    "b10_deq",
    "b11_iso_grav_vg",
    "b12_det_elev_hp8",
    "b13_iso_grav_hp8",
    "b15_depth_base",
    "b15_basement_grad",
    "b16_ieq",
    "b16_ieq_grad",
    "b17_cond_surf",
    "b17_cond_grad",
    "b18_iso_grav_hg",
    "b19_det_elev_slope",
    "ms_ridge_100m",
    "crossgrad_align",
    "crossgrad_ortho",
    "anderson_strike_fav",
    # --- USGS 3DEP 1 m LiDAR scarp stack (4 features, NaN outside valid LiDAR) ---
    "lidar_scarp_dipole",
    "lidar_step_max",
    "lidar_lap_curv",
    "lidar_coh_cross",
    # --- USGS 3DEP 10 m seamless DEM derived stack across 100% of AOI (5 features) ---
    "topo10_slope_std",
    "topo10_curv_prof",
    "topo10_hs_lineament",
    "topo10_slope_p90",
    "topo10_relief_hp",
    # --- GeoDAWN radiometrics, shallow demagnetization & GDR 1391 thermal conduits (4 features) ---
    "rad_alteration_edge",
    "demag_shallow",
    "hydro_conduit_near",
    "hydro_conduit_far",
    # --- Fold-proper visible-catalogue mechanical transfer features (3 features) ---
    "vis_dist_capped",
    "vis_tip_lobe",
    "vis_host_len_prox",
)
N_STATIC_FEATURES = 38
N_TOTAL_FEATURES = len(FEATURE_NAMES)  # 41


def _clean_band(arr: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Replace non-finite / sentinel values with median over valid cells for safe filtering."""
    out = arr.astype(np.float32, copy=False)
    good = np.isfinite(out) & (out > -1e30) & valid
    med = float(np.median(out[good])) if good.any() else 0.0
    filled = np.where(good, out, med).astype(np.float32)
    return filled


def structure_tensor_ridge_and_strike(
    slope_field: np.ndarray, valid: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Multi-scale edge magnitude x axial coherence + Anderson (1905) strike favorability."""
    f = _clean_band(slope_field, valid)
    ms = np.zeros_like(f, dtype=np.float32)
    for sig in (1.0, 2.0, 3.5):
        sm = ndi.gaussian_filter(f, sigma=sig)
        gy, gx = np.gradient(sm)
        ms += np.hypot(gy, gx).astype(np.float32)
    ms /= 3.0

    sm2 = ndi.gaussian_filter(f, sigma=2.0)
    gy, gx = np.gradient(sm2)
    jxx = ndi.gaussian_filter((gx * gx).astype(np.float32), sigma=3.0)
    jyy = ndi.gaussian_filter((gy * gy).astype(np.float32), sigma=3.0)
    jxy = ndi.gaussian_filter((gx * gy).astype(np.float32), sigma=3.0)
    denom = jxx + jyy + 1e-12
    coh = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0)) / denom

    # Principal gradient normal azimuth clockwise from North -> strike = normal + 90 deg (mod 180)
    # 0.5 * atan2(2*Jxy, Jxx - Jyy) gives principal gradient angle in math (col, row) coordinates
    theta = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)
    normal_az = (np.rad2deg(np.arctan2(np.cos(theta), -np.sin(theta))) + 360.0) % 180.0
    strike_az = (normal_az + 90.0) % 180.0

    diff_norm = np.minimum(np.abs(strike_az - 18.0), 180.0 - np.abs(strike_az - 18.0))
    diff_tran = np.minimum(np.abs(strike_az - 145.0), 180.0 - np.abs(strike_az - 145.0))
    fav = coh * np.maximum(
        np.cos(np.deg2rad(2.0 * diff_norm)),
        0.75 * np.cos(np.deg2rad(2.0 * diff_tran)),
    )
    ridge = (ms * coh).astype(np.float32)
    return ridge, fav.astype(np.float32)


def cross_gradient_coupling(
    grav: np.ndarray, rtp: np.ndarray, valid: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Gallardo & Meju (2004) parallel alignment and orthogonal confounder operators."""
    g = ndi.gaussian_filter(_clean_band(grav, valid), sigma=2.0)
    m = ndi.gaussian_filter(_clean_band(rtp, valid), sigma=2.0)
    ggy, ggx = np.gradient(g)
    mgy, mgx = np.gradient(m)
    ng = np.hypot(ggy, ggx) + 1e-9
    nm = np.hypot(mgy, mgx) + 1e-9
    cos_a = np.abs(ggx * mgx + ggy * mgy) / (ng * nm)
    sin_a = np.abs(ggx * mgy - ggy * mgx) / (ng * nm)
    amp = np.sqrt(ng / (np.median(ng[valid]) + 1e-9) * nm / (np.median(nm[valid]) + 1e-9))
    amp = np.log1p(amp).astype(np.float32)
    return (amp * cos_a).astype(np.float32), (amp * sin_a).astype(np.float32)


def rank01_domain(values: np.ndarray) -> np.ndarray:
    """Tie-averaged empirical quantile rank in (0, 1] on a 1D finite float vector."""
    v = np.asarray(values, dtype=np.float64)
    n = v.size
    if n == 0:
        return np.empty(0, dtype=np.float32)
    if np.ptp(v) == 0.0:
        return np.full(n, 0.5, dtype=np.float32)
    return (rankdata(v, method="average") / float(n)).astype(np.float32)



def submodular_pack_300m(
    surface_2d: np.ndarray,
    allowed_2d: np.ndarray,
    target_n: int = 37654,
    support_quantile: float = 0.90,
    gamma: float = 2.0,
    max_candidates: int = 450000,
) -> tuple[np.ndarray, int]:
    """Unblurred exact 300 m kernel lazy-greedy submodular dot packing (Minoux 1978).

    Maximizes F(D) = sum_g w(g) * max_{x in D} K(||x - g||_2) subject to |D| <= target_n
    and D subset allowed_2d, where w(g) = ((rank(g) - q0)/(1 - q0))^gamma on top-(1 - q0)
    allowed cells and 0 below q0 so sharp 1-px ridges strictly beat broad background blobs.
    """
    h, w = surface_2d.shape
    allow = np.asarray(allowed_2d, dtype=bool)
    vals = surface_2d[allow]
    if vals.size < target_n:
        raise ValueError(f"Allowed support ({vals.size}) smaller than target_n ({target_n})")

    ranks = rank01_domain(vals)
    pos = np.clip((ranks - support_quantile) / max(1.0 - support_quantile, 1e-6), 0.0, 1.0)
    weights_allow = (pos ** gamma).astype(np.float32)
    # Tiny deterministic rank tie-breaker (1e-5) so equal plateaus break cleanly by rank
    weights_allow = weights_allow + (1e-5 * ranks).astype(np.float32)

    pad = 2
    hp, wp = h + 2 * pad, w + 2 * pad
    w_pad = np.zeros((hp, wp), dtype=np.float32)
    ay, ax = np.nonzero(allow)
    w_pad[ay + pad, ax + pad] = weights_allow

    # Vectorized exact initial marginal gain g0(y, x) = sum_{(dy, dx, k)} k * w_pad[y+dy, x+dx]
    g0 = np.zeros((h, w), dtype=np.float32)
    for dy, dx, k in KERNEL_300M:
        g0 += k * w_pad[pad + dy : pad + dy + h, pad + dx : pad + dx + w]

    cand_scores = g0[allow]
    if cand_scores.size > max_candidates:
        part = np.argpartition(cand_scores, -max_candidates)[-max_candidates:]
        part = part[np.argsort(cand_scores[part], kind="mergesort")[::-1]]
    else:
        part = np.argsort(cand_scores, kind="mergesort")[::-1]

    cy = (ay[part] + pad).astype(np.int32)
    cx = (ax[part] + pad).astype(np.int32)
    flat_idx = cy * wp + cx
    init_gains = cand_scores[part]

    # Build Python min-heap of (-upper_bound, flat_padded_index)
    heap = [(-float(init_gains[i]), int(flat_idx[i])) for i in range(flat_idx.size)]
    heapq.heapify(heap)

    w_list = w_pad.ravel().tolist()
    cov_list = [0.0] * (hp * wp)
    off_k = tuple((dy * wp + dx, k) for dy, dx, k in KERNEL_300M)

    dots = np.zeros((h, w), dtype=bool)
    picked = 0
    pop = heapq.heappop
    push = heapq.heappush

    while picked < target_n and heap:
        neg_ub, idx = pop(heap)
        # Recompute exact current marginal gain against cov_list
        gain = 0.0
        for off, k in off_k:
            j = idx + off
            wj = w_list[j]
            if wj > 0.0:
                rem = k - cov_list[j]
                if rem > 0.0:
                    gain += wj * rem
        # Minoux lazy check: if exact gain beats next best upper bound in heap, commit!
        if not heap or gain >= -heap[0][0] - 1e-12:
            y = idx // wp - pad
            x = idx % wp - pad
            if not dots[y, x]:
                dots[y, x] = True
                for off, k in off_k:
                    j = idx + off
                    if k > cov_list[j]:
                        cov_list[j] = k
                picked += 1
        elif gain > 0.0:
            push(heap, (-gain, idx))

    return dots, picked


def _read_dbf_probes(zip_path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Extract Coolbaugh/INGENIOUS 2 m temperature probe anomalies (F2mDAB >= 1.5 C) to grid."""
    h, w = shape
    grid_pts = np.zeros((h, w), dtype=np.float32)
    if not zip_path.is_file():
        return grid_pts
    with zipfile.ZipFile(zip_path) as z:
        dbf = z.read(
            "2m_temperature_probe_INGENIOUS_regional_data/"
            "2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf"
        )
    nrec, hdrlen, reclen = struct.unpack("<IHH", dbf[4:12])
    fields = []
    off = 32
    while dbf[off] != 0x0D:
        fname = dbf[off : off + 11].split(b"\x00")[0].decode("latin1")
        flen = dbf[off + 16]
        fields.append((fname, flen))
        off += 32
    lons, lats, anoms = [], [], []
    pos = hdrlen
    for _ in range(nrec):
        if dbf[pos] == 0x2A:  # deleted DBF record
            pos += reclen
            continue
        p = pos + 1
        row_d = {}
        for fn, fl in fields:
            if fn in ("LatDegreeN", "LongDegree", "F2mDAB"):
                row_d[fn] = dbf[p : p + fl].decode("latin1").strip()
            p += fl
        pos += reclen
        try:
            lat = float(row_d["LatDegreeN"])
            lon = float(row_d["LongDegree"])
            anom = float(row_d["F2mDAB"])
        except (KeyError, ValueError):
            continue
        if np.isfinite(lat) and np.isfinite(lon) and np.isfinite(anom) and anom >= 1.5:
            lons.append(lon)
            lats.append(lat)
            anoms.append(min(anom, 15.0))
    if lons:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        rs = ((4508550.0 - np.asarray(ys)) // 100.0).astype(np.int32)
        cs = ((np.asarray(xs) - 243350.0) // 100.0).astype(np.int32)
        ok = (rs >= 0) & (rs < h) & (cs >= 0) & (cs < w)
        np.add.at(grid_pts, (rs[ok], cs[ok]), np.asarray(anoms, dtype=np.float32)[ok])
    return grid_pts


def _read_paleo_sinter(zip_path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Extract Ayling/INGENIOUS paleo-geothermal sinter/travertine/tufa deposits to grid."""
    h, w = shape
    grid_pts = np.zeros((h, w), dtype=np.float32)
    if not zip_path.is_file():
        return grid_pts
    with zipfile.ZipFile(zip_path) as z:
        txt = z.read("Paleo_geothermal_final.csv").decode("cp1252")
    lons, lats = [], []
    for row in csv.DictReader(io.StringIO(txt)):
        try:
            lon = float(row["Long_deg_NAD83"])
            lat = float(row["Lat_deg_NAD83"])
        except (KeyError, ValueError):
            continue
        if np.isfinite(lon) and np.isfinite(lat):
            lons.append(lon)
            lats.append(lat)
    if lons:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        rs = ((4508550.0 - np.asarray(ys)) // 100.0).astype(np.int32)
        cs = ((np.asarray(xs) - 243350.0) // 100.0).astype(np.int32)
        ok = (rs >= 0) & (rs < h) & (cs >= 0) & (cs < w)
        np.add.at(grid_pts, (rs[ok], cs[ok]), 2.0)
    return grid_pts


def _read_thermal_springs(csv_path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Extract DOE GDR 1391 thermal springs/wells & chemical geothermometers (strictly coordinates only;
    NEVER reads dist_known_fault_px to guarantee zero catalogue-distance leakage)."""
    h, w = shape
    grid_pts = np.zeros((h, w), dtype=np.float32)
    if not csv_path.is_file():
        return grid_pts
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError):
                continue
            if not (0 <= r < h and 0 <= c < w):
                continue
            strength = 0.0
            for k, thr in (
                ("temp_c", 25.0),
                ("geothermquartz_c", 80.0),
                ("geothermchalc_c", 70.0),
                ("geothermcat_c", 90.0),
            ):
                val_s = row.get(k, "")
                if val_s:
                    try:
                        val = float(val_s)
                        if np.isfinite(val) and val >= thr:
                            strength = max(strength, 1.0 + min((val - thr) / 50.0, 2.0))
                    except ValueError:
                        pass
            tcls = (row.get("thermalclass") or "").lower()
            if any(tok in tcls for tok in ("hot", "warm", "therm")):
                strength = max(strength, 1.0)
            if strength > 0.0:
                grid_pts[r, c] += strength
    return grid_pts


def build_feature_matrix(
    valid: np.ndarray,
    data_dir: Path,
    ext_dir: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Build compact (N_valid, 41) float32 feature matrix + unsupervised baseline score vector.

    Peak memory is ~950 MB (only one 2D raster band in memory at any step).
    Columns 0..37 are strictly catalogue-independent static physical features;
    columns 38..40 remain reserved to be overwritten per fold purely from fold['visible'].
    """
    n_val = int(valid.sum())
    X = np.empty((n_val, N_TOTAL_FEATURES), dtype=np.float32)

    with rasterio.open(data_dir / "training_features.tif") as src:
        # High-pass localized anomalies (remove broad regional mountain-block bias)
        b1 = _clean_band(src.read(1), valid)
        X[:, 0] = (b1 - ndi.gaussian_filter(b1, sigma=8.0))[valid]
        del b1

        rtp = _clean_band(src.read(2), valid)
        X[:, 1] = (rtp - ndi.gaussian_filter(rtp, sigma=8.0))[valid]

        X[:, 2] = _clean_band(src.read(3), valid)[valid]   # tmi_hg
        b4 = _clean_band(src.read(4), valid)
        X[:, 3] = (b4 - ndi.gaussian_filter(b4, sigma=12.0))[valid]  # localized geod_2ndinv
        del b4
        X[:, 4] = _clean_band(src.read(5), valid)[valid]   # iso_grav_anom_slope
        X[:, 5] = _clean_band(src.read(6), valid)[valid]   # tc
        b7 = _clean_band(src.read(7), valid)
        X[:, 6] = (b7 - ndi.gaussian_filter(b7, sigma=12.0))[valid]  # localized geod_shearrate
        del b7
        b8 = _clean_band(src.read(8), valid)
        X[:, 7] = (b8 - ndi.gaussian_filter(b8, sigma=12.0))[valid]  # localized geod_dilaterate
        del b8
        X[:, 8] = _clean_band(src.read(9), valid)[valid]   # tmi_vg
        X[:, 9] = _clean_band(src.read(10), valid)[valid]  # deq
        X[:, 10] = _clean_band(src.read(11), valid)[valid]  # iso_grav_anom_vg

        det_el = _clean_band(src.read(12), valid)
        X[:, 11] = (det_el - ndi.gaussian_filter(det_el, sigma=8.0))[valid]
        del det_el

        grav = _clean_band(src.read(13), valid)
        X[:, 12] = (grav - ndi.gaussian_filter(grav, sigma=8.0))[valid]

        dbase = _clean_band(src.read(15), valid)
        X[:, 13] = (dbase - ndi.gaussian_filter(dbase, sigma=12.0))[valid]
        gy, gx = np.gradient(ndi.gaussian_filter(dbase, sigma=2.0))
        X[:, 14] = np.hypot(gy, gx).astype(np.float32)[valid]
        del dbase, gy, gx

        ieq = _clean_band(src.read(16), valid)
        X[:, 15] = (ieq - ndi.gaussian_filter(ieq, sigma=12.0))[valid]
        gy, gx = np.gradient(ndi.gaussian_filter(ieq, sigma=2.0))
        X[:, 16] = np.hypot(gy, gx).astype(np.float32)[valid]
        del ieq, gy, gx

        cond = _clean_band(src.read(17), valid)
        X[:, 17] = (cond - ndi.gaussian_filter(cond, sigma=12.0))[valid]
        gy, gx = np.gradient(ndi.gaussian_filter(cond, sigma=2.0))
        X[:, 18] = np.hypot(gy, gx).astype(np.float32)[valid]
        del cond, gy, gx

        X[:, 19] = _clean_band(src.read(18), valid)[valid]  # iso_grav_anom_hg

        det_sl = _clean_band(src.read(19), valid)
        X[:, 20] = det_sl[valid]

    ms_ridge, strike_fav = structure_tensor_ridge_and_strike(det_sl, valid)
    X[:, 21] = ms_ridge[valid]
    X[:, 24] = strike_fav[valid]
    del det_sl, strike_fav

    cg_align, cg_ortho = cross_gradient_coupling(grav, rtp, valid)
    X[:, 22] = cg_align[valid]
    X[:, 23] = cg_ortho[valid]
    del grav, cg_align

    # --- 1 m LiDAR scarp stack (preserve NaN where valid_band == 0!) ---
    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as lsrc:
        l_valid = lsrc.read(12) > 0
        upf = lsrc.read(7).astype(np.float32)
        dnf = lsrc.read(6).astype(np.float32)
        exm = lsrc.read(1).astype(np.float32)
        stp = lsrc.read(3).astype(np.float32)
        ln = lsrc.read(4).astype(np.float32)
        lp = lsrc.read(5).astype(np.float32)
        crs = lsrc.read(8).astype(np.float32)
        coh = lsrc.read(10).astype(np.float32)

    dipole = np.maximum(np.maximum(upf, dnf), exm)
    lap_c = 0.5 * (ln + lp)
    coh_x = crs * (coh / 255.0)
    for col_i, arr2d in ((25, dipole), (26, stp), (27, lap_c), (28, coh_x)):
        masked = np.where(l_valid, arr2d, np.nan).astype(np.float32)
        X[:, col_i] = masked[valid]
    lidar_norm = np.where(l_valid, dipole / 255.0, np.nan).astype(np.float32)
    del l_valid, upf, dnf, exm, stp, ln, lp, crs, coh, dipole, lap_c, coh_x

    # --- 10 m seamless USGS 3DEP derived stack across 100% of AOI ---
    with rasterio.open(ext_dir / "topo_10m_derived_100m_u8.tif") as tsrc:
        sl_p90 = tsrc.read(1).astype(np.float32)
        sl_std = tsrc.read(4).astype(np.float32)
        rel_loc = tsrc.read(5).astype(np.float32)
        curv_p = tsrc.read(6).astype(np.float32)
        hs_lin = tsrc.read(8).astype(np.float32)

    X[:, 29] = sl_std[valid]
    X[:, 30] = curv_p[valid]
    X[:, 31] = hs_lin[valid]
    X[:, 32] = sl_p90[valid]
    X[:, 33] = (rel_loc - ndi.gaussian_filter(rel_loc, sigma=8.0))[valid]

    # --- Unsupervised multi-scale ridge baseline score (Exp 5A / H-P5-2) ---
    r_ms100 = rank01_domain(ms_ridge[valid])
    r_t10 = rank01_domain((0.40 * sl_std + 0.35 * curv_p + 0.25 * hs_lin)[valid])
    r_ortho = rank01_domain(cg_ortho[valid])
    lid_v = lidar_norm[valid]
    lid_ok = np.isfinite(lid_v)
    r_lid = np.empty_like(r_ms100)
    r_lid[lid_ok] = rank01_domain(lid_v[lid_ok])
    r_lid[~lid_ok] = r_t10[~lid_ok]  # seamless fallback to 10 m 3DEP outside LiDAR flights
    unsup_vec = ((0.40 * r_ms100 + 0.35 * r_t10 + 0.25 * r_lid) * (1.0 - 0.20 * r_ortho)).astype(np.float32)
    del ms_ridge, cg_ortho, lidar_norm, sl_p90, sl_std, rel_loc, curv_p, hs_lin

    # --- GeoDAWN gamma-ray alteration edges & shallow demagnetization ---
    with rasterio.open(ext_dir / "geodawn_extensions_u8.tif") as esrc:
        thk = esrc.read(1).astype(np.float32)
        uk = esrc.read(2).astype(np.float32)
        tmi150 = esrc.read(4).astype(np.float32)
    rad_valid = thk > 0
    thk_s = ndi.gaussian_filter(np.where(rad_valid, thk, float(np.median(thk[rad_valid]))), sigma=1.5)
    uk_s = ndi.gaussian_filter(np.where(rad_valid, uk, float(np.median(uk[rad_valid]))), sigma=1.5)
    gy1, gx1 = np.gradient(thk_s)
    gy2, gx2 = np.gradient(uk_s)
    alt_edge = np.hypot(gy1, gx1) + np.hypot(gy2, gx2)
    X[:, 34] = np.where(rad_valid, alt_edge, np.nan).astype(np.float32)[valid]

    t150_ok = tmi150 > 0
    rtp_z = (rtp - float(np.mean(rtp[valid]))) / (float(np.std(rtp[valid])) + 1e-6)
    t150_m = np.where(t150_ok, tmi150, float(np.mean(tmi150[t150_ok])))
    t150_z = (t150_m - float(np.mean(t150_m[valid]))) / (float(np.std(t150_m[valid])) + 1e-6)
    # Shallow hydrothermal magnetite oxidation creates negative RTP residual vs upward-continued TMI_up150
    X[:, 35] = np.where(t150_ok, t150_z - rtp_z, np.nan).astype(np.float32)[valid]
    del thk, uk, tmi150, rtp, rtp_z, t150_m, t150_z, alt_edge, gy1, gx1, gy2, gx2

    # --- DOE GDR 1391 hydrothermal conduits (springs/geothermometers + 2m probes + sinter) ---
    pts = (
        _read_thermal_springs(ext_dir / "gdr_wellspring_in_footprint.csv", valid.shape)
        + _read_dbf_probes(ext_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip", valid.shape)
        + _read_paleo_sinter(ext_dir / "paleo_geothermal_regional.zip", valid.shape)
    )
    X[:, 36] = np.log1p(ndi.gaussian_filter(pts, sigma=4.0) * 10.0).astype(np.float32)[valid]
    X[:, 37] = np.log1p(ndi.gaussian_filter(pts, sigma=12.0) * 25.0).astype(np.float32)[valid]
    del pts

    X[:, 38:41] = 0.0
    return X, unsup_vec


def write_fold_visible_features(
    X: np.ndarray, valid: np.ndarray, visible: np.ndarray, tip_fn
) -> np.ndarray:
    """Overwrite columns 38..40 strictly from fold-visible faults (zero leakage of hidden truth)."""
    vis = np.asarray(visible, dtype=bool)
    d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
    X[:, 38] = np.minimum(d_vis[valid], 40.0)

    u, v = tip_fn(vis, vis.shape)
    tip = np.exp(-np.clip(u, 0.0, None) / 25.0) * np.exp(-np.abs(v) / 8.0)
    X[:, 39] = np.where(np.isfinite(tip), tip, 0.0).astype(np.float32)[valid]
    del u, v, tip

    # Host fault component length transferred by nearest-pixel EDT index
    comp, _ = ndi.label(vis, structure=np.ones((3, 3), dtype=int))
    sizes = np.bincount(comp.ravel())
    sizes[0] = 0
    len_on_vis = sizes[comp].astype(np.float32)
    _, inds = ndi.distance_transform_edt(~vis, return_indices=True)
    nearest_len = len_on_vis[inds[0], inds[1]]
    host_prox = np.log1p(nearest_len) * np.exp(-d_vis / 15.0)
    X[:, 40] = host_prox.astype(np.float32)[valid]
    del comp, sizes, len_on_vis, inds, nearest_len, host_prox
    return d_vis


def feature_leakage_canaries(
    X: np.ndarray, truth_on_valid: np.ndarray, max_neg: int = 200000, seed: int = 7005
) -> dict[str, dict]:
    """Protocol Rule 4: test EVERY feature alone on withheld truth; AUC > 0.90 stops the run."""
    pos_idx = np.flatnonzero(truth_on_valid)
    neg_pool = np.flatnonzero(~truth_on_valid)
    rng = np.random.default_rng(seed)
    neg_idx = rng.choice(neg_pool, min(max_neg, neg_pool.size), replace=False)
    sample = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])

    out = {}
    for j, name in enumerate(FEATURE_NAMES):
        col = X[sample, j]
        fin = np.isfinite(col)
        if fin.sum() < 100 or y[fin].min() == y[fin].max() or np.ptp(col[fin]) == 0.0:
            auc = 0.5
        else:
            auc = float(roc_auc_score(y[fin], col[fin]))
        leak = bool(max(auc, 1.0 - auc) > 0.90)
        out[name] = {
            "auc": auc,
            "symmetric_auc": float(max(auc, 1.0 - auc)),
            "finite_fraction": float(fin.mean()),
            "n_positive": int(y[fin].sum()),
            "suspected_leakage": leak,
        }
    return out


def fit_oof_expert(
    X: np.ndarray,
    pos_on_valid: np.ndarray,
    eligible_train_on_valid: np.ndarray,
    seed: int,
    max_neg: int = 180000,
    n_features: int | None = None,
) -> HistGradientBoostingClassifier:
    """Fit a shallow L2-regularized HistGradientBoostingClassifier strictly inside eligible_train.

    Note: for M_neo (predicting Quaternary catalogue traces `vis`), callers MUST pass
    `n_features=N_STATIC_FEATURES` (columns 0..37 only) so `vis`-derived distance/tip features
    cannot trivially self-identify `d_vis == 0` on positive training pixels.
    """
    n_cols = X.shape[1] if n_features is None else int(n_features)
    pos_idx = np.flatnonzero(pos_on_valid & eligible_train_on_valid)
    neg_pool = np.flatnonzero((~pos_on_valid) & eligible_train_on_valid)
    rng = np.random.default_rng(seed)
    n_neg = min(max_neg, neg_pool.size)
    neg_idx = rng.choice(neg_pool, n_neg, replace=False)
    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(pos_idx.size, np.int32), np.zeros(neg_idx.size, np.int32)])
    clf = HistGradientBoostingClassifier(
        max_iter=160,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=200,
        l2_regularization=5.0,
        early_stopping=False,
        random_state=seed,
    )
    clf.fit(X[idx, :n_cols], y)
    return clf

