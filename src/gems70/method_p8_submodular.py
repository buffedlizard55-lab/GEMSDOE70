"""Phase-5 Multi-Physics + Hydrothermal Upflow OOF Synthesis & Submodular DTI Decoder.

Implements the preregistered Phase-5 method family (`docs/hypotheses.md`):
- Strictly label-free multi-physics Earth observation stack across 5 data families:
  1. Core 19-band geophysical/geodetic stack (`training_features.tif`) + multi-scale ridges
  2. 1 m USGS 3DEP LiDAR scarp composite (`lidar_scarp_features_u8.tif`) + Wallace scarp dipole
  3. 10 m DEM lineaments (`topo_10m_derived_100m_u8.tif`) + channel chi/ksn (`dem10_chi_100m_i16.tif`)
     + explicit pluvial paleoshoreline anti-mimic (`contour_obliquity`, `lahontan_band`)
  4. USGS GeoDAWN airborne radiometrics & upward-continued TMI residual (DOI 10.5066/P93LGLVQ)
  5. DOE GDR-1391 INGENIOUS hydrothermal springs/wells geothermometry, sinter/tufa deposits,
     and 2 m shallow temperature probes (DOI 10.15121/1881483; zero catalogue columns read)
- Strictly Leave-One-Quadrant-Out (LOQO) dual-regime gradient-boosted posterior estimation
  with a 24-px (2.4 km) inter-quadrant spatial buffer and hidden-fault exclusion.
- Exact monotone submodular lazy-greedy optimization of expected Distance-Weighted Tversky
  coverage F(S) = sum_g p_hat(g) max_{x in S} (1 - d(x, g) / 3)_+ at matched cardinality S.
"""
from __future__ import annotations

import csv
import heapq
import struct
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

from gems70 import method_v2 as m2


KERNEL_OFFSETS = [
    (dy, dx, float(1.0 - np.hypot(dy, dx) / 3.0))
    for dy in range(-3, 4)
    for dx in range(-3, 4)
    if np.hypot(dy, dx) < 3.0
]

KERNEL_2D = np.zeros((7, 7), dtype=np.float32)
for _dy, _dx, _kw in KERNEL_OFFSETS:
    KERNEL_2D[_dy + 3, _dx + 3] = _kw


def clean_band(arr: np.ndarray, fp: np.ndarray, nodata_floor: float = -1e30) -> np.ndarray:
    """Replace non-finite or sentinel pixels inside footprint with footprint median."""
    out = arr.astype(np.float32, copy=True)
    ok = np.isfinite(out) & (out > nodata_floor) & fp
    med = float(np.median(out[ok])) if ok.any() else 0.0
    out[~ok] = med
    out[~fp] = med
    return out


def grad_mag(arr: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    s = ndi.gaussian_filter(arr, sigma=sigma) if sigma > 0 else arr
    gy, gx = np.gradient(s)
    return np.hypot(gy, gx).astype(np.float32)


def zscore_fp(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    vals = arr[fp].astype(np.float64)
    mu = float(vals.mean())
    sd = float(vals.std()) + 1e-6
    return ((arr - mu) / sd).astype(np.float32)


def build_hydrothermal_fields(
    gems_ext_dir: Path, clone_ext_dir: Path, grid
) -> list[tuple[str, np.ndarray]]:
    """Construct strictly label-free hydrothermal upflow fields on the 100 m grid.

    Explicitly ignores `dist_known_fault_px` so zero catalogue information ever enters.
    """
    fp = grid.footprint
    h, w = fp.shape
    tr = grid.transform

    # 1. Wells & springs temperature + silica/cation geothermometers (GDR-1391)
    temp_grid = np.zeros((h, w), dtype=np.float32)
    geoth_grid = np.zeros((h, w), dtype=np.float32)
    ws_csv = gems_ext_dir / 'gdr_wellspring_in_footprint.csv'
    with ws_csv.open(newline='') as fh:
        reader = csv.DictReader(fh)
        if 'dist_known_fault_px' in (reader.fieldnames or []):
            pass  # verified unused: never read below
        for row in reader:
            ry = int(float(row['row']))
            cx = int(float(row['col']))
            if not (0 <= ry < h and 0 <= cx < w and fp[ry, cx]):
                continue
            tc = float(row['temp_c']) if row['temp_c'] else 0.0
            tq = float(row['geothermquartz_c']) if row['geothermquartz_c'] else 0.0
            tch = float(row['geothermchalc_c']) if row['geothermchalc_c'] else 0.0
            tcat = float(row['geothermcat_c']) if row['geothermcat_c'] else 0.0
            excess_t = max(0.0, min(tc, 150.0) - 20.0)
            excess_g = max(0.0, min(max(tq, tch, tcat), 260.0) - 80.0)
            if excess_t > temp_grid[ry, cx]:
                temp_grid[ry, cx] = excess_t
            if excess_g > geoth_grid[ry, cx]:
                geoth_grid[ry, cx] = excess_g

    hydro_t10 = ndi.gaussian_filter(temp_grid, sigma=10.0).astype(np.float32)
    hydro_t30 = ndi.gaussian_filter(temp_grid, sigma=30.0).astype(np.float32)
    del temp_grid
    hydro_g25 = ndi.gaussian_filter(geoth_grid, sigma=25.0).astype(np.float32)
    del geoth_grid

    # 2. Siliceous sinter, travertine & tufa paleogeothermal vents (GDR-1391)
    sinter_mask = np.zeros((h, w), dtype=bool)
    pz = clone_ext_dir / 'paleo_geothermal_regional.zip'
    with zipfile.ZipFile(pz) as zf:
        txt = zf.read('Paleo_geothermal_final.csv').decode('utf-8-sig', errors='replace').splitlines()
        prows = list(csv.DictReader(txt))
    lons = [float(r['Long_deg_NAD83']) for r in prows if r.get('Long_deg_NAD83')]
    lats = [float(r['Lat_deg_NAD83']) for r in prows if r.get('Lat_deg_NAD83')]
    exs, nys = rio_transform('EPSG:4269', 'EPSG:32611', lons, lats)
    for ex, ny in zip(exs, nys):
        cx = int((ex - tr.c) / tr.a)
        ry = int((ny - tr.f) / tr.e)
        if 0 <= ry < h and 0 <= cx < w and fp[ry, cx]:
            sinter_mask[ry, cx] = True
    d_sinter = ndi.distance_transform_edt(~sinter_mask).astype(np.float32)
    del sinter_mask
    hydro_sinter = np.exp(-d_sinter / 25.0).astype(np.float32)
    del d_sinter

    # 3. 2-meter shallow temperature probes (Coolbaugh et al. F2mDAB °C anomaly)
    probe_grid = np.zeros((h, w), dtype=np.float32)
    tz = clone_ext_dir / '2m_temperature_probe_INGENIOUS_regional_data.zip'
    with zipfile.ZipFile(tz) as zf:
        shp = zf.read('2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp')
        dbf = zf.read('2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf')
    num_rec, hdr_len, rec_len = struct.unpack('<IHH', dbf[4:12])
    fields = []
    pos = 32
    while dbf[pos] != 0x0D:
        fname = dbf[pos:pos + 11].split(b'\x00', 1)[0].decode('latin1')
        flen = dbf[pos + 16]
        fields.append((fname, flen))
        pos += 32
    spos, dpos = 100, hdr_len
    pxs, pys, dabs = [], [], []
    for _ in range(num_rec):
        _, content_len = struct.unpack('>II', shp[spos:spos + 8])
        _, px, py = struct.unpack('<Idd', shp[spos + 8:spos + 28])
        spos += 8 + content_len * 2
        row_bytes = dbf[dpos + 1:dpos + rec_len]
        dpos += rec_len
        rec, off = {}, 0
        for fn, fl in fields:
            rec[fn] = row_bytes[off:off + fl].decode('latin1').strip()
            off += fl
        dab = float(rec.get('F2mDAB') or 0.0)
        pxs.append(px)
        pys.append(py)
        dabs.append(max(0.0, min(dab, 25.0)))
    exs2, nys2 = rio_transform('EPSG:4269', 'EPSG:32611', pxs, pys)
    for ex, ny, dab in zip(exs2, nys2, dabs):
        cx = int((ex - tr.c) / tr.a)
        ry = int((ny - tr.f) / tr.e)
        if 0 <= ry < h and 0 <= cx < w and fp[ry, cx] and dab > probe_grid[ry, cx]:
            probe_grid[ry, cx] = dab
    hydro_probe15 = ndi.gaussian_filter(probe_grid, sigma=15.0).astype(np.float32)
    del probe_grid

    return [
        ('hydro_spring_temp_1km', hydro_t10),
        ('hydro_spring_temp_3km', hydro_t30),
        ('hydro_geotherm_2p5km', hydro_g25),
        ('hydro_paleo_sinter_2p5km', hydro_sinter),
        ('hydro_probe2m_dab_1p5km', hydro_probe15),
    ]


def build_feature_stack(
    data_dir: Path, gems_ext_dir: Path, clone_ext_dir: Path, grid
) -> tuple[np.ndarray, list[str], list[int], list[int]]:
    """Stream all label-free physical features into a compact float16 matrix on `grid.footprint`.

    Returns:
      X_fp: (N_fp, F) float16 standardized feature matrix
      names: list of length F
      e1_cols: column indices belonging to Experiment 1 (geomorphic + core stack + shoreline filter)
      e2_cols: all F column indices belonging to Experiments 2 & 3 (+ radiometrics + hydrothermal)
    """
    fp = grid.footprint
    n_fp = int(fp.sum())
    cols_list: list[np.ndarray] = []
    names: list[str] = []

    def push(name: str, full_arr: np.ndarray, allow_nan: np.ndarray | None = None) -> None:
        v = full_arr[fp].astype(np.float32)
        fin = np.isfinite(v)
        mu = float(np.mean(v[fin], dtype=np.float64)) if fin.any() else 0.0
        sd = float(np.std(v[fin], dtype=np.float64)) + 1e-6
        z = np.where(fin, np.clip((v - mu) / sd, -12.0, 12.0), np.nan).astype(np.float16)
        if allow_nan is not None:
            z = np.where(allow_nan, z, np.float16(np.nan))
        cols_list.append(z)
        names.append(name)

    # 1. Core 19-band geophysical/geodetic stack + multi-scale ridges
    tmi_cached = None
    with rasterio.open(data_dir / 'training_features.tif') as src:
        short_names = [
            'mag_anom', 'rtp', 'tmi_hg', 'geod_2ndinv', 'iso_grav_anom_slope',
            'tc', 'geod_shearrate', 'geod_dilaterate', 'tmi_vg', 'deq_n100a15',
            'iso_grav_anom_vg', 'det_elev', 'iso_grav_anom', 'tmi',
            'depth_to_base_surf', 'ieq_n100a15', 'cond_surf',
            'iso_grav_anom_hg', 'det_elev_slope',
        ]
        for b_idx, bname in enumerate(short_names, start=1):
            b = clean_band(src.read(b_idx), fp)
            push(f'core_{bname}', b)
            if bname == 'rtp':
                push('drv_rtp_grad_s1', grad_mag(b, 1.0))
                push('drv_rtp_dog_1_4', ndi.gaussian_filter(b, 1.0) - ndi.gaussian_filter(b, 4.0))
            elif bname == 'tc':
                push('drv_tc_zero_edge', grad_mag(b, 1.0) * np.exp(-np.abs(b) / 0.5))
            elif bname == 'iso_grav_anom_hg':
                push('drv_grav_hg_dog', ndi.gaussian_filter(b, 1.0) - ndi.gaussian_filter(b, 5.0))
            elif bname == 'depth_to_base_surf':
                push('drv_base_grad_s2', grad_mag(b, 2.0))
                push('drv_base_dog_1_5', ndi.gaussian_filter(b, 1.0) - ndi.gaussian_filter(b, 5.0))
            elif bname == 'cond_surf':
                lb = np.log1p(np.clip(b - float(b[fp].min()), 0.0, None))
                push('drv_cond_grad_s2', grad_mag(lb, 2.0))
                del lb
            elif bname == 'det_elev':
                push('drv_det_elev_dog', ndi.gaussian_filter(b, 1.0) - ndi.gaussian_filter(b, 4.0))
            elif bname == 'tmi':
                tmi_cached = zscore_fp(b, fp)
            del b

    # 2. 1 m LiDAR scarp features + Wallace crest-toe dipole (missing tiles routed via NaN)
    lidar_strike = None
    with rasterio.open(gems_ext_dir / 'lidar_scarp_features_u8.tif') as src:
        lnames = list(src.descriptions)
        lidar_valid_full = src.read(lnames.index('valid') + 1) > 0
        lidar_ok_fp = lidar_valid_full[fp]
        step_b = lapn_b = lapp_b = coh_b = None
        for b_idx, lname in enumerate(lnames, start=1):
            b = src.read(b_idx).astype(np.float32)
            if lname == 'valid':
                push(f'lidar_{lname}', b)
            else:
                push(f'lidar_{lname}', b, allow_nan=lidar_ok_fp)
            if lname == 'step_max':
                step_b = b
            elif lname == 'lapneg_max':
                lapn_b = b
            elif lname == 'lappos_max':
                lapp_b = b
            elif lname == 'coh100':
                coh_b = b
            elif lname == 'strike':
                lidar_strike = b
        push('drv_lidar_dipole', np.sqrt(np.maximum(lapn_b * lapp_b, 0.0)), allow_nan=lidar_ok_fp)
        push('drv_lidar_coh_step_s2', ndi.gaussian_filter(step_b * (coh_b / 255.0), 2.0), allow_nan=lidar_ok_fp)
        del step_b, lapn_b, lapp_b, coh_b, lidar_valid_full, lidar_ok_fp

    # 3. 10 m DEM lineaments + channel chi/ksn + Pluvial Lake Lahontan shoreline rejection
    with rasterio.open(clone_ext_dir / 'topo_10m_derived_100m_u8.tif') as src:
        for b_idx, tname in enumerate(src.descriptions, start=1):
            b = src.read(b_idx).astype(np.float32)
            push(f'topo10_{tname}', b)
            del b

    zmean = None
    with rasterio.open(clone_ext_dir / 'dem10_chi_100m_i16.tif') as src:
        for b_idx, cname in enumerate(src.descriptions, start=1):
            b = clean_band(src.read(b_idx).astype(np.float32), fp, nodata_floor=-30000.0)
            push(f'chi_{cname}', b)
            if cname == 'zmean_m':
                zmean = b
            else:
                del b

    # Hypsometric contour-obliquity vs Lake Lahontan highstand (1,330 m ASL)
    gy, gx = np.gradient(ndi.gaussian_filter(zmean, 1.5))
    theta = (lidar_strike / 255.0) * np.pi
    along_slope = np.abs(gx * np.cos(theta) + gy * np.sin(theta))
    obliq = along_slope / (np.hypot(gy, gx) + 0.5)
    lahontan = np.exp(-((zmean - 1330.0) / 55.0) ** 2).astype(np.float32)
    push('anti_shoreline_obliquity', obliq)
    push('anti_lahontan_elevation_band', lahontan)
    del gy, gx, theta, along_slope, obliq, lahontan, zmean, lidar_strike

    e1_cols = list(range(len(names)))

    # 4. USGS GeoDAWN radiometrics & upward-continued magnetic residual
    with rasterio.open(gems_ext_dir / 'geodawn_rad_u8.tif') as src:
        for b_idx, rname in enumerate(src.descriptions, start=1):
            b = src.read(b_idx).astype(np.float32)
            push(f'rad_{rname}', b)
            del b

    with rasterio.open(gems_ext_dir / 'geodawn_extensions_u8.tif') as src:
        for b_idx, ename in enumerate(src.descriptions, start=1):
            b = src.read(b_idx).astype(np.float32)
            push(f'radext_{ename}', b)
            if ename == 'ThK':
                push('drv_rad_thk_grad', grad_mag(b, 1.5))
            elif ename == 'UTh':
                push('drv_rad_uth_grad', grad_mag(b, 1.5))
            elif ename == 'TMI_up150':
                res = tmi_cached - zscore_fp(b, fp)
                push('drv_tmi_shallow_res', res)
                push('drv_tmi_shallow_grad', grad_mag(res, 1.0))
                del res
            del b
    del tmi_cached

    # 5. DOE GDR-1391 Hydrothermal upflow & geothermometry fields
    for hname, harr in build_hydrothermal_fields(gems_ext_dir, clone_ext_dir, grid):
        push(hname, harr)
        del harr

    e2_cols = list(range(len(names)))
    X_fp = np.column_stack(cols_list)
    assert X_fp.shape == (n_fp, len(names))
    return X_fp, names, e1_cols, e2_cols


def run_feature_canaries(
    X_fp: np.ndarray,
    names: list[str],
    fp: np.ndarray,
    truth_mask: np.ndarray,
    neg_pool_mask: np.ndarray,
    seed: int = 70500,
) -> dict[str, dict]:
    """Evaluate every single feature alone on held-out positives vs 200,000 negatives."""
    from scipy.stats import rankdata

    pos_fp = truth_mask[fp]
    neg_fp = neg_pool_mask[fp]
    pos_idx = np.flatnonzero(pos_fp)
    neg_all = np.flatnonzero(neg_fp)
    rng = np.random.default_rng(seed)
    neg_idx = rng.choice(neg_all, size=min(200_000, len(neg_all)), replace=False)
    idx = np.concatenate([pos_idx, neg_idx])
    n_pos = int(len(pos_idx))
    n_neg = int(len(neg_idx))

    report = {}
    for j, name in enumerate(names):
        vals = X_fp[idx, j].astype(np.float64)
        fin = np.isfinite(vals)
        vp = vals[:n_pos][fin[:n_pos]]
        vn = vals[n_pos:][fin[n_pos:]]
        comb = np.concatenate([vp, vn])
        ranks = rankdata(comb, method='average')
        np_j, nn_j = len(vp), len(vn)
        auc = float((ranks[:np_j].sum() - np_j * (np_j + 1) / 2.0) / (np_j * nn_j))
        leak = bool(not np.isfinite(auc) or max(auc, 1.0 - auc) > 0.90)
        report[name] = {
            'auc': round(auc, 6),
            'n_pos': int(np_j),
            'n_neg': int(nn_j),
            'suspected_leakage': leak,
        }
    return report


def fit_predict_oof_dual(
    X_fp: np.ndarray,
    col_idx: list[int],
    fp: np.ndarray,
    valid: np.ndarray,
    quad: np.ndarray,
    neo_pos_safe: np.ndarray,
    sgmc_pos_safe: np.ndarray,
    neo_weight: float = 0.50,
    collar_px: int = 24,
    seed: int = 70501,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Leave-One-Quadrant-Out dual-head gradient-boosted posterior estimation.

    For each spatial quadrant k in {0, 1, 2, 3}:
      - Excludes all of quadrant k PLUS a 24-px (2.4 km) border buffer from training.
      - Head 1 (Neotectonic active scarps): trained on `neo_pos_safe` (strictly excluding all
        Instrument-A hidden components across all folds so zero held-out trace ever leaks).
      - Head 2 (Concealed bedrock/structural contacts): trained on `sgmc_pos_safe` inside
        the other 3 quadrants (d_cat >= 3 px, strictly excluding hidden components).
      - Predicts out-of-fold probabilities on all pixels of quadrant k.
    """
    rng = np.random.default_rng(seed)
    quad_fp = quad[fp]
    valid_fp = valid[fp]
    neo_fp = neo_pos_safe[fp]
    sgmc_fp = sgmc_pos_safe[fp]

    p_neo_fp = np.zeros(len(quad_fp), dtype=np.float32)
    p_bed_fp = np.zeros(len(quad_fp), dtype=np.float32)

    for k in range(4):
        q_region = quad == k
        forbidden = ndi.binary_dilation(q_region, iterations=collar_px)
        tr_allowed = valid_fp & (~forbidden[fp])

        # Head 1 training sample (Quaternary/INGENIOUS active faults outside hidden sets)
        pos1 = np.flatnonzero(tr_allowed & neo_fp)
        neg1_pool = np.flatnonzero(tr_allowed & (~neo_fp) & (~sgmc_fp))
        neg1 = rng.choice(neg1_pool, size=min(len(pos1) * 5, len(neg1_pool)), replace=False)
        tr1 = np.concatenate([pos1, neg1])
        y1 = np.concatenate([np.ones(len(pos1), np.int8), np.zeros(len(neg1), np.int8)])

        clf1 = HistGradientBoostingClassifier(
            max_iter=220, learning_rate=0.06, max_leaf_nodes=63,
            min_samples_leaf=80, l2_regularization=2.0, random_state=seed + k * 11,
        )
        clf1.fit(X_fp[tr1][:, col_idx].astype(np.float32), y1)

        # Head 2 training sample (Off-catalogue structural contacts in other 3 quadrants)
        pos2 = np.flatnonzero(tr_allowed & sgmc_fp)
        neg2_pool = np.flatnonzero(tr_allowed & (~sgmc_fp) & (~neo_fp))
        neg2 = rng.choice(neg2_pool, size=min(len(pos2) * 5, len(neg2_pool)), replace=False)
        tr2 = np.concatenate([pos2, neg2])
        y2 = np.concatenate([np.ones(len(pos2), np.int8), np.zeros(len(neg2), np.int8)])

        clf2 = HistGradientBoostingClassifier(
            max_iter=220, learning_rate=0.06, max_leaf_nodes=63,
            min_samples_leaf=80, l2_regularization=2.0, random_state=seed + 100 + k * 11,
        )
        clf2.fit(X_fp[tr2][:, col_idx].astype(np.float32), y2)

        te_idx = np.flatnonzero(quad_fp == k)
        for start in range(0, len(te_idx), 500_000):
            sl = te_idx[start:start + 500_000]
            Xb = X_fp[sl][:, col_idx].astype(np.float32)
            p_neo_fp[sl] = clf1.predict_proba(Xb)[:, 1].astype(np.float32)
            p_bed_fp[sl] = clf2.predict_proba(Xb)[:, 1].astype(np.float32)

    # Unsupervised fold-mean alignment across all 4 quadrants: aligns per-quadrant OOF intercept
    # while preserving 100% of true extreme-tail probability contrast in [0, 1]
    for arr_fp in (p_neo_fp, p_bed_fp):
        global_mu = float(np.mean(arr_fp, dtype=np.float64)) + 1e-8
        for k in range(4):
            te_idx = np.flatnonzero(quad_fp == k)
            fold_mu = float(np.mean(arr_fp[te_idx], dtype=np.float64)) + 1e-8
            arr_fp[te_idx] = np.clip(arr_fp[te_idx] * (global_mu / fold_mu), 0.0, 1.0)

    p_neo = np.zeros(fp.shape, dtype=np.float32)
    p_bed = np.zeros(fp.shape, dtype=np.float32)
    p_neo[fp] = p_neo_fp
    p_bed[fp] = p_bed_fp
    p_blend = (neo_weight * p_neo + (1.0 - neo_weight) * p_bed).astype(np.float32)
    return p_blend, p_neo, p_bed


def conditioned_surface(
    base_prob: np.ndarray,
    catalogue_visible: np.ndarray,
    valid: np.ndarray,
    d_min: float = 2.5,
    tip_boost: float = 0.15,
) -> np.ndarray:
    """Apply visible-fault collar mask (d >= d_min) and gentle tip-process-zone boost."""
    cat = np.asarray(catalogue_visible, bool)
    d = ndi.distance_transform_edt(~cat).astype(np.float32)
    allowed = np.asarray(valid, bool) & (d >= d_min)
    del d
    if tip_boost > 0.0:
        u, v = m2.tip_kernels(cat, cat.shape)
        tip = np.exp(-np.clip(u, 0.0, None) / 25.0) * np.exp(-np.abs(v) / 8.0)
        tip = np.where(np.isfinite(tip), tip, 0.0).astype(np.float32)
        del u, v
        s = base_prob * (1.0 + tip_boost * tip)
        del tip
    else:
        s = base_prob
    out = np.where(allowed, np.clip(s, 0.0, 1.0), 0.0).astype(np.float32)
    return out


def submodular_dti_dots(
    prob_surface: np.ndarray,
    allowed_mask: np.ndarray,
    n_dots: int = 37654,
    min_spacing_px: float = 2.5,
    candidate_pool: int = 950_000,
    gamma: float = 1.0,
) -> tuple[np.ndarray, int]:
    """Monotone submodular lazy-greedy selection for exact 300 m triangular DTI kernel.

    Maximizes F(S) = sum_g w(g) * max_{x in S} (1 - d(x, g) / 3)_+ subject to |S| = n_dots
    and pairwise Euclidean spacing >= min_spacing_px, where w(g) = prob_surface(g)**gamma
    concentrates expected TP gain onto high-confidence ridges across the full footprint.
    """
    h, w = prob_surface.shape
    weights = np.where(prob_surface > 0, np.power(prob_surface, gamma), 0.0).astype(np.float32)
    init_gain = ndi.convolve(weights, KERNEL_2D, mode='constant', cval=0.0)
    init_gain = np.where(allowed_mask, init_gain, 0.0).astype(np.float32)

    flat_cand = np.flatnonzero(init_gain > 0)
    if len(flat_cand) > candidate_pool:
        part = np.argpartition(init_gain.ravel()[flat_cand], -candidate_pool)[-candidate_pool:]
        flat_cand = flat_cand[part]

    gains = init_gain.ravel()[flat_cand]
    # Max-heap via negative gain, deterministic tie-breaker = flat pixel index
    heap = [(-float(g), int(idx)) for g, idx in zip(gains, flat_cand)]
    heapq.heapify(heap)
    del init_gain

    cov = np.zeros((h, w), dtype=np.float32)
    dots = np.zeros((h, w), dtype=bool)
    blocked = np.zeros((h, w), dtype=bool)

    r_blk = int(np.ceil(min_spacing_px))
    yy, xx = np.mgrid[-r_blk:r_blk + 1, -r_blk:r_blk + 1]
    disk_y, disk_x = np.nonzero((yy * yy + xx * xx) < min_spacing_px * min_spacing_px)
    disk_dy = (disk_y - r_blk).astype(np.int32)
    disk_dx = (disk_x - r_blk).astype(np.int32)

    picked = 0
    while heap and picked < n_dots:
        neg_upper, idx = heapq.heappop(heap)
        y, x = divmod(idx, w)
        if blocked[y, x]:
            continue

        # Exact current marginal gain under the 300 m triangular kernel
        exact_gain = 0.0
        for dy, dx, kw in KERNEL_OFFSETS:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                inc = kw - cov[ny, nx]
                if inc > 0.0:
                    exact_gain += weights[ny, nx] * inc

        # Peek next upper bound on heap: if exact_gain >= next upper bound, accept immediately!
        next_upper = -heap[0][0] if heap else -1.0
        if exact_gain >= next_upper - 1e-12:
            dots[y, x] = True
            picked += 1
            for dy, dx, kw in KERNEL_OFFSETS:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and kw > cov[ny, nx]:
                    cov[ny, nx] = kw
            by = np.clip(y + disk_dy, 0, h - 1)
            bx = np.clip(x + disk_dx, 0, w - 1)
            blocked[by, bx] = True
        elif exact_gain > 0.0:
            heapq.heappush(heap, (-exact_gain, idx))

    return dots, picked
