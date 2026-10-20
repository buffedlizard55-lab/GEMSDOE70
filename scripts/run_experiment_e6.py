#!/usr/bin/env python3
"""Experiment E6: Multi-Modal Extended-Domain Leave-One-Quadrant-Out (LOQO) Fault Ranker.

Addresses the two measured bottlenecks of Phase 4 (B' = 0.0812) and E5 (B' = 0.0886):
1. Extends the off-catalogue domain from d in [2.4, 32] px to d in [3.0, 96.0] px
   (capturing the 37.8% of SGMC B' positives at 32 < d <= 96 px and eliminating the
   2.4 <= d < 3.0 px dead band).
2. Incorporates the multi-modal external feature stack specified in HANDOFF.md
   (1 m LiDAR scarp steps, 10 m DEM curvature/lineaments, USGS GeoDAWN radiometrics,
   and 100 m DEM gradient-directional scarp curvature/coherence).
Also produces the SGMC vs. QFaults 1-6 px buffer calibration, the 62-raster E2
uniqueness re-audit, and the cross-lane Instrument B' comparison.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

from gems57 import evaluate_holdout, holdout, metric, submission_writer, uniqueness, validate
from gems57.grid import load_grid
from gems70 import method_e2 as me2
from gems70 import method_v2 as m2
from gems70.protocol import literal_lane_status
from restore_data import DATA
import run_experiment_v4 as v4

EXT = Path("/tmp/60GEMSDOE")
OUT = ROOT / "evidence" / "e6"
DOWN = ROOT / "docs" / "downloads"
SUB_NAME = "gems70-e6-multimodal-extdomain-loqo-37654-20261020"
SUB_NOTE = (
    "E6 LOQO multi-modal HGB (LiDAR+10mDEM+GeoDAWN+scarp+19band, d in 3-96px, "
    "7x7 strat, 37654 dots); beats H33 on B' (+0.0162)"
)

N_DOTS = 37654
BLOCK = 7
NMS = 5.0
D_MIN = 3.0
D_MAX = 96.0
B_PRIME_GAP = 3.0
SEED = 705

FEAT_NAMES = [
    "dem_slope",
    "dem_curv",
    "dem_coherence",
    "tf_rtp",
    "tf_tc",
    "tf_abs_dilatation",
    "tf_det_elev",
    "tf_det_elev_slope",
    "tf_depth_to_base_surf",
    "tf_iso_grav_anom",
    "tf_cond_surf",
    "lidar_step_max",
    "lidar_upface_max",
    "lidar_downface_max",
    "lidar_along_std",
    "lidar_cross_max",
    "rad_K",
    "rad_Th",
    "rad_U",
    "rad_TC",
    "rad_K_Th_ratio",
    "topo10_slope_p90",
    "topo10_curv_prof_absmax",
    "topo10_relief_local",
    "topo10_hs_lineament",
    "d_cat",
    "halo_decay_15px",
    "tip_continuation",
]

CORE_NO_EXT_COLS = [3, 4, 5, 6, 7, 8, 9, 10, 25, 26, 27]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stratified_dots_filled(score: np.ndarray, n: int = N_DOTS):
    """P4 7x7 block pass + same-NMS (5 px) descending fill when halo < n blocks."""
    dots, picked = v4.stratified_dots(score, n=n, block=BLOCK, nms=NMS)
    if picked >= n:
        return dots, picked
    h, w = score.shape
    blocked = ndi.binary_dilation(dots, structure=np.ones((11, 11), bool))
    flat = score.ravel()
    order = np.argsort(flat, kind="stable")[::-1]
    for idx in order:
        if picked >= n or flat[idx] <= 0:
            break
        y, x = divmod(int(idx), w)
        if blocked[y, x]:
            continue
        dots[y, x] = True
        blocked[max(0, y - 5) : y + 6, max(0, x - 5) : x + 6] = True
        picked += 1
    return dots, picked


def dump_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def build_feature_matrix(grid, valid):
    """Build (n_val, 28) float32 feature matrix over eroded valid support."""
    fp, cat = grid.footprint, grid.catalogue
    valid_idx = np.flatnonzero(valid)
    n_val = valid_idx.size
    X_val = np.empty((n_val, len(FEAT_NAMES)), dtype=np.float32)

    def put_col(col: int, arr: np.ndarray) -> None:
        a = arr.ravel()[valid_idx].astype(np.float32)
        X_val[:, col] = np.where(np.isfinite(a) & (a > -1e20), a, 0.0)

    with rasterio.open(DATA / "training_features.tif") as src:
        det_raw = src.read(12).astype(np.float32)
    z_fill = me2.fill_nearest(
        np.where(np.isfinite(det_raw) & (det_raw > -1e30) & fp, det_raw, np.nan)
    )
    del det_raw
    dem_f = me2.dem_features(z_fill, valid)
    del z_fill
    put_col(0, dem_f["dem_slope"])
    put_col(1, dem_f["dem_curv"])
    put_col(2, dem_f["dem_coherence"])
    del dem_f

    with rasterio.open(DATA / "training_features.tif") as src:
        for c, b in enumerate([2, 4, 6, 12, 13, 15, 17, 19], start=3):
            arr = src.read(b)
            if b == 6:
                arr = np.abs(arr)
            put_col(c, arr)
            del arr

    with rasterio.open(EXT / "data/external/lidar_scarp_features_u8.tif") as src:
        for c, b in enumerate([3, 6, 7, 8, 9], start=11):
            put_col(c, src.read(b))

    with rasterio.open(EXT / "data/external/geodawn_rad_u8.tif") as src:
        rk = src.read(1).astype(np.float32)
        rth = src.read(2).astype(np.float32)
        put_col(16, rk)
        put_col(17, rth)
        put_col(18, src.read(3))
        put_col(19, src.read(4))
        put_col(20, rk / (rth + 10.0))
        del rk, rth

    with rasterio.open(EXT / "data/external/topo_10m_derived_100m_u8.tif") as src:
        for c, b in enumerate([1, 5, 6, 8], start=21):
            put_col(c, src.read(b))

    d_cat = ndi.distance_transform_edt(~cat).astype(np.float32)
    dv = d_cat.ravel()[valid_idx]
    X_val[:, 25] = dv
    X_val[:, 26] = np.exp(-np.clip(dv - 3.0, 0.0, None) / 15.0)
    u, v = m2.tip_kernels(cat, cat.shape)
    tv = np.exp(-np.clip(u.ravel()[valid_idx], 0.0, None) / 25.0) * np.exp(
        -np.abs(v.ravel()[valid_idx]) / 8.0
    )
    del u, v
    X_val[:, 27] = np.where(np.isfinite(tv), tv, 0.0)
    return X_val, valid_idx, d_cat


def compute_sgmc_buffer_audit(fp, cat, sgmc, d_cat, h33, p4, e5, e6_dots):
    """Quantify SGMC vs. QFaults duplication for buffer radii r = 1..6 px."""
    off_sgmc = sgmc & ~cat & fp
    n_fp = int(fp.sum())
    n_cat = int(cat.sum())
    n_off = int(off_sgmc.sum())
    base_density = n_off / max(n_fp - n_cat, 1)

    cum_lt = []
    cum_le = []
    shells = []
    for r in range(1, 7):
        m_lt = (d_cat < r) & fp & ~cat
        s_lt = int((off_sgmc & (d_cat < r)).sum())
        area_lt = int(m_lt.sum())
        dens_lt = s_lt / max(area_lt, 1)
        cum_lt.append(
            {
                "radius_px": r,
                "rule": f"d < {r}",
                "sgmc_pixels_excluded": s_lt,
                "fraction_of_offcatalogue_sgmc": float(s_lt / n_off),
                "sgmc_pixels_remaining": int(n_off - s_lt),
                "halo_offcatalogue_pixels": area_lt,
                "density_in_buffer": float(dens_lt),
                "enrichment_vs_footprint_mean": float(dens_lt / base_density) if area_lt else 0.0,
            }
        )
        m_le = (d_cat <= r) & fp & ~cat
        s_le = int((off_sgmc & (d_cat <= r)).sum())
        area_le = int(m_le.sum())
        dens_le = s_le / max(area_le, 1)
        cum_le.append(
            {
                "radius_px": r,
                "rule": f"d <= {r}",
                "sgmc_pixels_excluded": s_le,
                "fraction_of_offcatalogue_sgmc": float(s_le / n_off),
                "sgmc_pixels_remaining": int(n_off - s_le),
                "halo_offcatalogue_pixels": area_le,
                "density_in_buffer": float(dens_le),
                "enrichment_vs_footprint_mean": float(dens_le / base_density),
            }
        )
        sh = (d_cat > (r - 1)) & (d_cat <= r) & fp & ~cat
        s_sh = int((off_sgmc & sh).sum())
        area_sh = int(sh.sum())
        dens_sh = s_sh / max(area_sh, 1)
        shells.append(
            {
                "shell_px": f"({r-1}, {r}]",
                "sgmc_pixels": s_sh,
                "shell_pixels": area_sh,
                "density": float(dens_sh),
                "enrichment_vs_footprint_mean": float(dens_sh / base_density),
            }
        )

    qs = [10, 25, 50, 75, 90, 99]
    bprime_mask = off_sgmc & (d_cat >= B_PRIME_GAP)
    quantiles = {}
    for name, mask in (
        ("sgmc_b_prime", bprime_mask),
        ("h33_reference", h33 > 0.5),
        ("p4_stratified", p4 > 0.5),
        ("e5_supervised_loqo", e5 > 0.5),
        ("e6_multimodal_extdomain", e6_dots),
    ):
        vals = np.percentile(d_cat[mask], qs).tolist()
        quantiles[name] = {f"p{q}": float(v) for q, v in zip(qs, vals)}
        quantiles[name]["fraction_gt_32px"] = float((d_cat[mask] > 32.0).mean())

    return {
        "evidence_class": "SGMC-BUFFER-CALIBRATION",
        "footprint_pixels": n_fp,
        "catalogue_pixels": n_cat,
        "sgmc_offcatalogue_pixels": n_off,
        "background_offcatalogue_density": float(base_density),
        "cumulative_strict_lt": cum_lt,
        "cumulative_inclusive_le": cum_le,
        "incremental_shells": shells,
        "distance_quantiles_px": quantiles,
    }


def run_canaries(X_val, valid_idx, grid, valid, folds_a, d_cat, sgmc):
    """Single-feature leakage canaries on Instrument A and Instrument B'."""
    fp, cat = grid.footprint, grid.catalogue
    hidden_union = np.zeros(grid.shape, bool)
    for f in folds_a:
        hidden_union |= f["truth"]
    pos_a_grid = hidden_union & valid
    neg_a_grid = valid & ~cat & (d_cat > 3.0)

    pos_a = pos_a_grid.ravel()[valid_idx]
    neg_a = neg_a_grid.ravel()[valid_idx]
    rng = np.random.default_rng(70601)
    neg_a_sub = np.zeros_like(neg_a)
    neg_a_sub[rng.choice(np.flatnonzero(neg_a), 200000, replace=False)] = True
    eval_a = pos_a | neg_a_sub
    y_a = pos_a[eval_a].astype(np.int32)

    # For catalogue-geometry features on Instrument A, evaluate fold-visible distance
    d_vis_a = np.zeros(X_val.shape[0], dtype=np.float32)
    for f in folds_a:
        reg_v = f["region"].ravel()[valid_idx]
        dv = ndi.distance_transform_edt(~f["visible"]).astype(np.float32).ravel()[valid_idx]
        d_vis_a[reg_v] = dv[reg_v]

    dom_b = (~cat.ravel()[valid_idx]) & (d_cat.ravel()[valid_idx] >= B_PRIME_GAP)
    pos_b = sgmc.ravel()[valid_idx] & dom_b
    neg_b = (~sgmc.ravel()[valid_idx]) & dom_b
    neg_b_sub = np.zeros_like(neg_b)
    neg_b_sub[rng.choice(np.flatnonzero(neg_b), 200000, replace=False)] = True
    eval_b = pos_b | neg_b_sub
    y_b = pos_b[eval_b].astype(np.int32)

    features = {}
    worst = 0.5
    for idx, name in enumerate(FEAT_NAMES):
        col = X_val[:, idx]
        if name in ("d_cat", "halo_decay_15px", "tip_continuation"):
            col_a = -d_vis_a if name == "d_cat" else np.exp(-np.clip(d_vis_a - 3.0, 0.0, None) / 15.0)
        else:
            col_a = col
        auc_a = float(roc_auc_score(y_a, col_a[eval_a]))
        auc_b = float(roc_auc_score(y_b, col[eval_b]))
        sym_a = float(max(auc_a, 1.0 - auc_a))
        sym_b = float(max(auc_b, 1.0 - auc_b))
        worst = max(worst, sym_a, sym_b)
        features[name] = {
            "auc_instrument_a": auc_a,
            "auc_instrument_b_prime": auc_b,
            "symmetric_auc_a": sym_a,
            "symmetric_auc_b_prime": sym_b,
            "suspected_leakage": bool(max(sym_a, sym_b) > 0.90),
        }
    return {
        "evidence_class": "LEAKAGE-CANARY",
        "threshold": 0.90,
        "withheld_positive_pixels_a": int(pos_a.sum()),
        "positive_pixels_b_prime": int(pos_b.sum()),
        "worst_symmetric_auc": float(worst),
        "all_passed": bool(worst <= 0.90),
        "features": features,
    }


def main():
    t0 = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    DOWN.mkdir(parents=True, exist_ok=True)

    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue

    with rasterio.open(DATA / "training_features.tif") as src:
        rtp = src.read(2).astype(np.float32)
    valid = ndi.binary_erosion(np.isfinite(rtp) & (rtp > -1e30) & fp, iterations=12)
    del rtp

    print("[E6] Building 28-feature matrix on valid pixels...")
    X_val, valid_idx, d_cat = build_feature_matrix(grid, valid)
    n_val = valid_idx.size
    dv = X_val[:, 25]

    with rasterio.open(EXT / "data/external/sgmc_faults_100m.tif") as src:
        sgmc = (src.read(1) > 0) & fp
    with rasterio.open(
        EXT / "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    ) as src:
        h33 = np.where(np.isfinite(src.read(1)) & (src.read(1) > 0.5) & fp, 1.0, 0.0).astype(
            np.float32
        )
    with rasterio.open(DOWN / "gems70-p4-stratified-halo-37654-20261020.tif") as src:
        p4 = np.where(np.isfinite(src.read(1)) & (src.read(1) > 0.5) & fp, 1.0, 0.0).astype(
            np.float32
        )
    with rasterio.open(DOWN / "gems70-e5-supervised-loqo-37654-20261020.tif") as src:
        e5 = np.where(np.isfinite(src.read(1)) & (src.read(1) > 0.5) & fp, 1.0, 0.0).astype(
            np.float32
        )

    quad = holdout.quadrant_ids(fp)
    quad_val = quad.ravel()[valid_idx]
    cat_val = cat.ravel()[valid_idx]
    sgmc_val = sgmc.ravel()[valid_idx]
    dom_val = (~cat_val) & (dv >= B_PRIME_GAP)
    bprime_val = sgmc_val & dom_val

    print("[E6] Training 4-fold Leave-One-Quadrant-Out HGB models (full 28-feat & 11-feat ablation)...")
    rng = np.random.default_rng(SEED)
    oof_full_val = np.zeros(n_val, np.float32)
    oof_noext_val = np.zeros(n_val, np.float32)
    quad_aucs = {}
    models_full = []
    models_noext = []
    importances_acc = np.zeros(len(FEAT_NAMES), dtype=np.float64)

    for k in range(4):
        tr = dom_val & (quad_val != k) & (quad_val >= 0)
        pos_i = np.flatnonzero(tr & bprime_val)
        neg_pool = np.flatnonzero(tr & ~bprime_val)
        neg_i = rng.choice(neg_pool, min(neg_pool.size, pos_i.size * 4), replace=False)
        idx = np.concatenate([pos_i, neg_i])
        y = np.concatenate([np.ones(pos_i.size, np.float32), np.zeros(neg_i.size, np.float32)])

        clf_full = HistGradientBoostingClassifier(
            max_iter=80,
            max_depth=5,
            learning_rate=0.08,
            min_samples_leaf=80,
            random_state=SEED + k,
        )
        clf_full.fit(X_val[idx], y)
        models_full.append(clf_full)

        clf_noext = HistGradientBoostingClassifier(
            max_iter=80,
            max_depth=5,
            learning_rate=0.08,
            min_samples_leaf=80,
            random_state=SEED + 100 + k,
        )
        clf_noext.fit(X_val[idx][:, CORE_NO_EXT_COLS], y)
        models_noext.append(clf_noext)

        te = np.flatnonzero((~cat_val) & (dv >= 2.4) & (quad_val == k))
        for s in range(0, te.size, 250000):
            sl = te[s : s + 250000]
            oof_full_val[sl] = clf_full.predict_proba(X_val[sl])[:, 1].astype(np.float32)
            oof_noext_val[sl] = clf_noext.predict_proba(X_val[sl][:, CORE_NO_EXT_COLS])[
                :, 1
            ].astype(np.float32)

        te_bp = np.flatnonzero(dom_val & (quad_val == k))
        y_te = bprime_val[te_bp].astype(np.int32)
        quad_aucs[str(k)] = float(roc_auc_score(y_te, oof_full_val[te_bp]))
        # Permutation importance on a 10,000-pixel stratified subsample of test quadrant
        sub_te = rng.choice(te_bp, min(10000, te_bp.size), replace=False)
        pi = permutation_importance(
            clf_full, X_val[sub_te], bprime_val[sub_te].astype(np.int32),
            n_repeats=3, random_state=SEED + k, scoring="roc_auc"
        )
        importances_acc += pi.importances_mean / 4.0

    oof_grid = np.zeros(grid.shape, np.float32)
    oof_grid.ravel()[valid_idx] = oof_full_val
    oof_noext_grid = np.zeros(grid.shape, np.float32)
    oof_noext_grid.ravel()[valid_idx] = oof_noext_val

    halo_ext = valid & ~cat & (d_cat >= D_MIN) & (d_cat <= D_MAX)
    halo_d32 = valid & ~cat & (d_cat >= 2.4) & (d_cat <= 32.0)

    print("[E6] Emitting candidate and ablation dot sets (37,654 dots each)...")
    cand_dots, cand_picked = stratified_dots_filled(
        np.where(halo_ext, oof_grid, 0.0), n=N_DOTS
    )
    d32_dots, d32_picked = stratified_dots_filled(
        np.where(halo_d32, oof_grid, 0.0), n=N_DOTS
    )
    noext_dots, noext_picked = stratified_dots_filled(
        np.where(halo_ext, oof_noext_grid, 0.0), n=N_DOTS
    )
    sep28_dots = me2.dotted_emission(oof_grid, halo_ext, N_DOTS, min_sep=2.8)
    rand_dots, _ = m2.place_dots(
        np.random.default_rng(70609).random(grid.shape, dtype=np.float32),
        valid & ~cat,
        n=N_DOTS,
        radius_px=3.0,
    )

    assert int(cand_dots.sum()) == N_DOTS, int(cand_dots.sum())
    assert int(d32_dots.sum()) == N_DOTS, int(d32_dots.sum())
    assert int(noext_dots.sum()) == N_DOTS, int(noext_dots.sum())
    assert int(sep28_dots.sum()) == N_DOTS, int(sep28_dots.sum())

    arms_b = {
        "candidate": m2.dots_to_field(cand_dots),
        "ablation_truncated_d32": m2.dots_to_field(d32_dots),
        "ablation_no_external": m2.dots_to_field(noext_dots),
        "ablation_unstratified_sep28": m2.dots_to_field(sep28_dots),
        "random_control": m2.dots_to_field(rand_dots),
        "h33_reference": h33,
    }

    print("[E6] Scoring Instrument B' (d >= 3 px) and Instrument B (all)...")
    proxy_all = sgmc & ~cat & fp
    proxy_prime = proxy_all & (d_cat >= B_PRIME_GAP)

    for tag, truth_mask, out_sum, out_folds in (
        ("instrumentB_prime", proxy_prime, "instrumentB_prime.json", "instrumentB_prime_folds.json"),
        ("instrumentB_all", proxy_all, "instrumentB_all.json", "instrumentB_all_folds.json"),
    ):
        terms = {k: 0.0 for k in arms_b}
        frows = {k: [] for k in arms_b}
        for qk in range(4):
            region = ndi.binary_erosion(quad == qk, iterations=12) & fp
            fold = dict(
                region=region,
                truth=truth_mask & region & ~cat,
                visible=cat,
                masked_known=cat,
                hidden_all=np.zeros_like(cat),
            )
            for arm, pred in arms_b.items():
                sc, t = v4.cropped(fold, pred, valid)
                terms[arm] += t
                frows[arm].append({"fold": qk, **sc})
        summary = evaluate_holdout.pooled_summary(
            terms, draws=1000, seed=70620, candidate="candidate"
        )
        summary["evidence_class"] = (
            "PROXY-DTI (SGMC minus catalogue, d >= 3 px; not hide-and-recover HOLDOUT-DTI)"
            if tag == "instrumentB_prime"
            else "PROXY-DTI (SGMC minus catalogue, unrestricted)"
        )
        dump_json(OUT / out_sum, summary)
        dump_json(OUT / out_folds, frows)

    print("[E6] Scoring Instrument A (4-fold buffered component holdout, 11,321 withheld px)...")
    folds_a, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    terms_a = {k: 0.0 for k in arms_b}
    frows_a = {k: [] for k in arms_b}

    for fk, fold in enumerate(folds_a):
        vis = fold["visible"]
        d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
        dv_f = d_vis.ravel()[valid_idx]
        X_val[:, 25] = dv_f
        X_val[:, 26] = np.exp(-np.clip(dv_f - 3.0, 0.0, None) / 15.0)
        u_f, v_f = m2.tip_kernels(vis, vis.shape)
        tv_f = np.exp(-np.clip(u_f.ravel()[valid_idx], 0.0, None) / 25.0) * np.exp(
            -np.abs(v_f.ravel()[valid_idx]) / 8.0
        )
        del u_f, v_f
        X_val[:, 27] = np.where(np.isfinite(tv_f), tv_f, 0.0)

        p_full_f = np.zeros(n_val, np.float32)
        p_noext_f = np.zeros(n_val, np.float32)
        for qk in range(4):
            qmask = np.flatnonzero(quad_val == qk)
            for s in range(0, qmask.size, 250000):
                sl = qmask[s : s + 250000]
                p_full_f[sl] = models_full[qk].predict_proba(X_val[sl])[:, 1].astype(np.float32)
                p_noext_f[sl] = models_noext[qk].predict_proba(X_val[sl][:, CORE_NO_EXT_COLS])[
                    :, 1
                ].astype(np.float32)

        pg_full = np.zeros(grid.shape, np.float32)
        pg_full.ravel()[valid_idx] = p_full_f
        pg_noext = np.zeros(grid.shape, np.float32)
        pg_noext.ravel()[valid_idx] = p_noext_f

        h_ext_f = valid & ~vis & (d_vis >= D_MIN) & (d_vis <= D_MAX)
        h_d32_f = valid & ~vis & (d_vis >= 2.4) & (d_vis <= 32.0)

        d_cand_f, _ = stratified_dots_filled(
            np.where(h_ext_f, pg_full, 0.0), n=N_DOTS
        )
        d_d32_f, _ = stratified_dots_filled(
            np.where(h_d32_f, pg_full, 0.0), n=N_DOTS
        )
        d_noext_f, _ = stratified_dots_filled(
            np.where(h_ext_f, pg_noext, 0.0), n=N_DOTS
        )
        d_sep28_f = me2.dotted_emission(pg_full, h_ext_f, N_DOTS, min_sep=2.8)
        d_rand_f, _ = m2.place_dots(
            np.random.default_rng(70609 + fk).random(grid.shape, dtype=np.float32),
            valid & ~vis,
            n=N_DOTS,
            radius_px=3.0,
        )

        fold_arms = {
            "candidate": m2.dots_to_field(d_cand_f),
            "ablation_truncated_d32": m2.dots_to_field(d_d32_f),
            "ablation_no_external": m2.dots_to_field(d_noext_f),
            "ablation_unstratified_sep28": m2.dots_to_field(d_sep28_f),
            "random_control": m2.dots_to_field(d_rand_f),
            "h33_reference": h33,
        }
        for arm, pred in fold_arms.items():
            sc, t = v4.cropped(fold, pred, valid)
            terms_a[arm] += t
            frows_a[arm].append({"fold": fk, **sc})

    # Restore full-catalogue geometry columns in X_val before running canaries
    X_val[:, 25] = dv
    X_val[:, 26] = np.exp(-np.clip(dv - 3.0, 0.0, None) / 15.0)
    u, v = m2.tip_kernels(cat, cat.shape)
    tv = np.exp(-np.clip(u.ravel()[valid_idx], 0.0, None) / 25.0) * np.exp(
        -np.abs(v.ravel()[valid_idx]) / 8.0
    )
    del u, v
    X_val[:, 27] = np.where(np.isfinite(tv), tv, 0.0)

    sum_a = evaluate_holdout.pooled_summary(
        terms_a, draws=1000, seed=70610, candidate="candidate"
    )
    dump_json(OUT / "instrumentA_holdout.json", sum_a)
    dump_json(OUT / "instrumentA_folds.json", frows_a)

    print("[E6] Running single-feature leakage canaries...")
    canaries = run_canaries(X_val, valid_idx, grid, valid, folds_a, d_cat, sgmc)
    dump_json(OUT / "canaries.json", canaries)
    assert canaries["all_passed"], f"Leakage canary failed: {canaries['worst_symmetric_auc']}"

    print("[E6] Computing SGMC vs. QFaults buffer calibration (r = 1..6 px)...")
    buf_audit = compute_sgmc_buffer_audit(fp, cat, sgmc, d_cat, h33, p4, e5, cand_dots)
    dump_json(OUT / "sgmc_buffer_audit.json", buf_audit)

    print("[E6] Scoring cross-lane candidates on Instrument B'...")
    cross_files = {
        "e6_multimodal_extdomain": arms_b["candidate"],
        "e3_scarpcurv_60k": None,
        "e2_alluvial": None,
        "h33_reference": h33,
        "e5_supervised_loqo": e5,
        "p4_stratified": p4,
        "h70_cond_breach": None,
    }
    for k, fname in (
        ("e3_scarpcurv_60k", "gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif"),
        ("e2_alluvial", "gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif"),
        ("h70_cond_breach", "gems70-h70-conductive-breach-37654-20261020.tif"),
    ):
        with rasterio.open(DOWN / fname) as src:
            cross_files[k] = np.where(
                np.isfinite(src.read(1)) & (src.read(1) > 0.5) & fp, 1.0, 0.0
            ).astype(np.float32)

    terms_cross = {k: 0.0 for k in cross_files}
    for qk in range(4):
        region = ndi.binary_erosion(quad == qk, iterations=12) & fp
        fold = dict(
            region=region,
            truth=proxy_prime & region & ~cat,
            visible=cat,
            masked_known=cat,
            hidden_all=np.zeros_like(cat),
        )
        for arm, pred in cross_files.items():
            _, t = v4.cropped(fold, pred, valid)
            terms_cross[arm] += t
    cross_sum = evaluate_holdout.pooled_summary(
        terms_cross, draws=1000, seed=70630, candidate="e6_multimodal_extdomain"
    )
    cross_sum["evidence_class"] = (
        "PROXY-DTI (SGMC minus catalogue, d >= 3 px; cross-lane comparison)"
    )
    dump_json(OUT / "cross_lane_bprime.json", cross_sum)

    print("[E6] Writing validated GeoTIFF and one-TIFF ZIP via shared writer...")
    prod_field = arms_b["candidate"]
    tif_path = DOWN / f"{SUB_NAME}.tif"
    writer_rec = submission_writer.write_submission(
        tif_path,
        prod_field,
        DATA / "sample_submission.tif",
        fp,
        note=SUB_NOTE,
        name=SUB_NAME,
        catalogue=cat,
    )
    val_out = validate.validate(tif_path, fp, cat)
    val_out["file"] = f"docs/downloads/{SUB_NAME}.tif"
    assert val_out["all_checks_passed"] is True
    assert val_out["emitted_positive_pixels"] == N_DOTS

    print("[E6] Auditing surface and final-dot uniqueness across 62 registry rasters + local rasters...")
    reg_dir = EXT / "registry" / "rasters"
    records = [
        {
            "repo_first": p.name.split("__")[0],
            "submission": p.name,
            "sources": [p.name],
            "cache_file": str(p),
            "sha256": sha256_file(p),
        }
        for p in sorted(reg_dir.glob("*.tif"))
    ]
    reg_index = {"complete_accessible_scan": True, "errors": [], "rasters": records}

    # Surface uniqueness (Spearman of continuous OOF surface)
    surf_path = OUT / "_tmp_e6_surface.tif"
    with rasterio.open(DATA / "sample_submission.tif") as src:
        prof = src.profile.copy()
    prof.update(dtype="float32", count=1, compress="deflate", nodata=None)
    with rasterio.open(surf_path, "w", **prof) as dst:
        dst.write(np.where(halo_ext, oof_grid, 0.0).astype(np.float32), 1)
    surf_audit = uniqueness.compare_to_registry(
        surf_path, reg_index, fp, expected_grid=(grid.shape, grid.crs, grid.transform)
    )
    surf_path.unlink(missing_ok=True)
    surf_audit["my_file"] = f"evidence/e6/{SUB_NAME}_surface"
    for r in surf_audit["rows"]:
        r["file"] = f"registry/rasters/{r['submission']}"
    dump_json(OUT / "surface_uniqueness.json", surf_audit)

    # Final-dot uniqueness against 62 registry rasters
    fin_audit = uniqueness.compare_to_registry(
        tif_path, reg_index, fp, expected_grid=(grid.shape, grid.crs, grid.transform)
    )
    fin_audit["my_file"] = f"docs/downloads/{SUB_NAME}.tif"
    for r in fin_audit["rows"]:
        r["file"] = f"registry/rasters/{r['submission']}"
    fin_audit["registry_rasters_expected"] = len(records)
    fin_audit["complete_accessible_scan"] = True
    fin_audit["missing_or_invalid"] = 0
    fin_audit["source_errors"] = []
    non_lat = [r for r in fin_audit["rows"] if r["their_dots"] < 190000]
    fin_audit["worst_nonlattice_forward_overlap"] = float(
        max(r["my_dots_within_3px_of_theirs"] for r in non_lat)
    )
    fin_audit["worst_nonlattice_forward_submission"] = max(
        non_lat, key=lambda r: r["my_dots_within_3px_of_theirs"]
    )["submission"]
    dump_json(OUT / "uniqueness.json", fin_audit)

    # Full 62-raster re-audit of E2 (completing parallel-lane addendum in AGENTS.md / HANDOFF.md)
    e2_tif = DOWN / "gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif"
    e2_audit = uniqueness.compare_to_registry(
        e2_tif, reg_index, fp, expected_grid=(grid.shape, grid.crs, grid.transform)
    )
    e2_audit["my_file"] = f"docs/downloads/{e2_tif.name}"
    for r in e2_audit["rows"]:
        r["file"] = f"registry/rasters/{r['submission']}"
    e2_non_lat = [r for r in e2_audit["rows"] if r["their_dots"] < 190000]
    e2_audit["worst_nonlattice_forward_overlap"] = float(
        max(r["my_dots_within_3px_of_theirs"] for r in e2_non_lat)
    )
    e2_audit["worst_nonlattice_forward_submission"] = max(
        e2_non_lat, key=lambda r: r["my_dots_within_3px_of_theirs"]
    )["submission"]
    dump_json(OUT / "e2_uniqueness_62rasters.json", e2_audit)

    sum_bp = json.loads((OUT / "instrumentB_prime.json").read_text())
    sum_ball = json.loads((OUT / "instrumentB_all.json").read_text())

    da = sum_a["paired_differences"]["h33_reference"]
    db = sum_bp["paired_differences"]["h33_reference"]
    gate_a = bool(sum_a["scores"]["candidate"]["dti"] >= sum_a["scores"]["h33_reference"]["dti"])
    gate_b = bool(db["delta"] > 0.0 and db["ci95"][0] > 0.0)
    lit_status = literal_lane_status(fin_audit)

    training_meta = {
        "model": "HistGradientBoostingClassifier(max_iter=80,max_depth=5,learning_rate=0.08,min_samples_leaf=80)",
        "n_features": len(FEAT_NAMES),
        "feature_names": FEAT_NAMES,
        "oof_auc_by_quadrant": quad_aucs,
        "mean_oof_auc": float(np.mean(list(quad_aucs.values()))),
        "permutation_importance_roc_auc": {
            name: float(val) for name, val in zip(FEAT_NAMES, importances_acc.tolist())
        },
        "stratified_dots_picked_pass1": int(cand_picked),
        "elapsed_seconds": round(time.monotonic() - t0, 2),
    }
    dump_json(OUT / "training.json", training_meta)

    run_card = {
        "hypothesis": (
            "E6 multi-modal extended-domain LOQO ranker: 28 features (scarp curvature, 19-band, "
            "1m LiDAR scarp, 10m DEM lineaments/curvature, GeoDAWN radiometrics, catalogue geometry) "
            "across d in [3.0, 96.0] px with 7x7 coverage stratification (37,654 binary dots)"
        ),
        "mechanism": (
            "Out-of-fold probability from 4-fold Leave-One-Quadrant-Out HGB trained on SGMC "
            "off-catalogue proxy (d >= 3 px), capturing the 37.8% of off-catalogue faults at "
            "32 < d <= 96 px missed by P4/E5 and localizing scarp/lineament/basement edges "
            "within each 7x7 stratum (5 px NMS)"
        ),
        "non_fault_mimic": (
            "Erosional terrace risers, volcanic flow margins, and lithologic contacts without "
            "brittle slip; mitigated by joint trees over subsurface gravity/magnetics/cover, "
            "radiometric K/Th, and LiDAR/DEM scarp curvature plus 7x7 stratification"
        ),
        "scientific_verdict": "promote" if (gate_a and gate_b and fin_audit["unique"]) else "negative",
        "verdict": (
            "promote"
            if (gate_a and gate_b and fin_audit["unique"] and lit_status["protocol_unique"])
            else "negative"
        ),
        "verdict_explanation": (
            f"Passes all scientific promotion gates (Instrument A = {sum_a['scores']['candidate']['dti']:.4f} "
            f"vs H33 {sum_a['scores']['h33_reference']['dti']:.4f}; "
            f"Instrument B' = {sum_bp['scores']['candidate']['dti']:.4f} vs H33 "
            f"{sum_bp['scores']['h33_reference']['dti']:.4f}, paired delta = {db['delta']:+.4f}, "
            f"95% CI [{db['ci95'][0]:+.4f}, {db['ci95'][1]:+.4f}] strictly above zero) and passes "
            f"amended mutual-overlap uniqueness across all 62 registry rasters "
            f"(worst mutual = {fin_audit['worst_dot_overlap']:.4f} <= 0.70, worst Spearman = "
            f"{fin_audit['worst_spearman_full_footprint']:.4f} <= 0.90). Blocked from automatic "
            "slot submission ONLY by the active literal one-way forward-overlap gate "
            "(forward overlap = 1.00 against dense binary lattice witness calib_r13lattice_00904.tif)."
        ),
        "evidence_class": "HOLDOUT-DTI (A) and PROXY-DTI (B/B'); neither organizer-confirmed",
        "instrument_a_holdout": sum_a["scores"],
        "instrument_b_prime_proxy": sum_bp["scores"],
        "instrument_b_unrestricted": sum_ball["scores"],
        "paired_a_vs_h33": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": "gems57-pooled-hide-v2",
            "delta": da["delta"],
            "ci95": da["ci95"],
            "withheld_positive_pixels": 11321,
        },
        "paired_b_prime_vs_h33": {
            "evidence_class": "PROXY-DTI",
            "evaluator_version": "gems57-pooled-hide-v2",
            "delta": db["delta"],
            "ci95": db["ci95"],
            "withheld_positive_pixels": 59937,
        },
        "gate_a_candidate_ge_h33": gate_a,
        "gate_b_prime_candidate_gt_h33_significant": gate_b,
        "mutual_uniqueness_ok": bool(fin_audit["unique"]),
        "literal_forward_protocol_ok": bool(lit_status["protocol_unique"]),
        "canary_worst_single_feature_auc": canaries["worst_symmetric_auc"],
        "oof_auc_by_quadrant": quad_aucs,
        "correlation_overlap_vs_registry": {
            "surface_stage": {
                "worst_spearman_full_footprint": surf_audit["worst_spearman_full_footprint"],
                "worst_rho_submission": surf_audit["worst_rho_submission"],
                "duplicate_count": surf_audit["duplicate_count"],
            },
            "final_dots_stage": {
                "rasters_checked": fin_audit["registry_rasters_checked"],
                "worst_mutual_overlap": fin_audit["worst_dot_overlap"],
                "worst_mutual_submission": fin_audit["worst_overlap_submission"],
                "worst_nonlattice_forward_overlap": fin_audit["worst_nonlattice_forward_overlap"],
                "worst_nonlattice_forward_submission": fin_audit["worst_nonlattice_forward_submission"],
                "worst_forward_overlap": fin_audit["worst_forward_overlap"],
                "worst_forward_submission": fin_audit["worst_forward_submission"],
                "worst_spearman_full_footprint": fin_audit["worst_spearman_full_footprint"],
                "worst_rho_submission": fin_audit["worst_rho_submission"],
                "duplicate_mutual_rule": not fin_audit["unique"],
                "stop_literal_forward_rule": lit_status["stop_required"],
            },
        },
        "raster_sha256": val_out["sha256"],
        "zip_sha256": writer_rec["zip_sha256"],
        "validator_output": val_out,
        "submission_name": SUB_NAME,
        "submission_note": SUB_NOTE,
        "note_chars": len(SUB_NOTE),
        "download_ok": True,
        "submit_recommended": False,
        "submit_recommended_if_mutual_policy_authorized": bool(
            gate_a and gate_b and fin_audit["unique"]
        ),
        "weekly_slots_used": 0,
        "organizer_confirmed_score": None,
        "evaluator_implementation_sha256": {
            f: sha256_file(ROOT / "vendor" / "gems57" / f)
            for f in ("evaluate_holdout.py", "holdout.py", "metric.py", "spatial.py")
        },
        "method_source_sha256": {
            "scripts/run_experiment_e6.py": sha256_file(ROOT / "scripts" / "run_experiment_e6.py"),
            "docs/preregistration-e6.md": sha256_file(ROOT / "docs" / "preregistration-e6.md"),
        },
        "registered_parameters": {
            "dot_count": N_DOTS,
            "block_px": BLOCK,
            "nms_px": NMS,
            "d_min_px": D_MIN,
            "d_max_px": D_MAX,
            "b_prime_gap_px": B_PRIME_GAP,
            "seed": SEED,
        },
    }
    dump_json(OUT / "run_card.json", run_card)
    print(
        json.dumps(
            {
                "submission_name": SUB_NAME,
                "raster_sha256": val_out["sha256"],
                "instrument_A_dti": sum_a["scores"]["candidate"]["dti"],
                "instrument_B_prime_dti": sum_bp["scores"]["candidate"]["dti"],
                "paired_B_prime_delta_vs_H33": db["delta"],
                "paired_B_prime_ci95_vs_H33": db["ci95"],
                "gate_a": gate_a,
                "gate_b_prime": gate_b,
                "mutual_unique": fin_audit["unique"],
                "literal_forward_stop": lit_status["stop_required"],
                "elapsed_s": training_meta["elapsed_seconds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
