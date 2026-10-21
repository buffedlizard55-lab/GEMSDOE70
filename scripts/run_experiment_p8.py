#!/usr/bin/env python3
"""Phase-5 Preregistered 3-Experiment Progression (Exp 5A, Exp 5B, Exp 5C).

Frozen before execution at commit abc7c6e (`docs/preregistration-phase5.md`).
Uses ONLY shared `vendor/gems57` tools (`evaluate_holdout`, `holdout`, `uniqueness`,
`submission_writer`, `grid`) and never touches frozen `evidence/phase2..phase4`.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57 import evaluate_holdout, holdout, submission_writer, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems70 import method_v2 as m2
from gems70 import phase5 as p5
from restore_data import DATA, PINS, sha

E = ROOT / "evidence/phase5"
CACHE = ROOT / ".cache"
CLONE = Path("/tmp/60GEMSDOE")
EXT = CLONE / "data/external"
REG = CLONE / "registry/rasters"

H33_PATH = CLONE / "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
H33_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
D28_PATH = CLONE / "docs/downloads/gemsdoe32-d28-ref02600-repro-44090-20261004T183200Z-426073b6-zeros.tif"
P4_PATH = ROOT / "docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif"
H19_PATH = REG / "19GEMSDOE__h19-5-powerlaw-budget-multiline.tif"
SGMC_PATH = EXT / "sgmc_faults_100m.tif"

DOT_COUNT = 37654
COLLAR_PX = 2.05
EROSION_PX = 12.0
GAP_PRIME_PX = 3.0
GAP_SENS_PX = 5.0
K_CAL = 7905

NAME = "gems70-p5-dual-submod300-oof38k-20261020"
NOTE = (
    "GEMSDOE70 P5: 4-fold OOF dual-pop HGB (SGMC d>=3 + Quat + 3DEP/LiDAR/GDR) + "
    "exact 300m submodular cover, 37654 binary off-cat dots."
)
assert len(NOTE) <= 140, len(NOTE)


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False, default=float) + "\n")
    tmp.replace(path)


def cropped(fold: dict, p: np.ndarray, valid: np.ndarray):
    y, x = np.nonzero(fold["region"])
    y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
    y1, x1 = min(p.shape[0], int(y.max()) + 7), min(p.shape[1], int(x.max()) + 7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k: v[sl] for k, v in fold.items() if isinstance(v, np.ndarray) and v.shape == p.shape}
    return evaluate_holdout.evaluate(
        p[sl], sub, valid[sl], origin=(y0, x0), global_shape=p.shape
    )


def vec_to_2d(vec: np.ndarray, valid: np.ndarray) -> np.ndarray:
    arr = np.zeros(valid.shape, dtype=np.float32)
    arr[valid] = vec
    return arr


def calibrated_dti_at_k(dti_raw: float, k_truth: int, s_pred: float, k_cal: int = K_CAL) -> float:
    if dti_raw <= 0.0 or k_truth <= 0:
        return 0.0
    tpw = (k_truth + 0.25 * s_pred) * dti_raw / (1.0 + 0.25 * dti_raw)
    r = tpw / float(k_truth)
    return float(1.25 * (k_cal * r) / (k_cal + 0.25 * s_pred - 0.25 * k_cal * r))


def predict_fold_a(
    X: np.ndarray,
    unsup_vec: np.ndarray,
    valid: np.ndarray,
    vis_k: np.ndarray,
    region_k: np.ndarray,
    sgmc_v: np.ndarray,
    fold_idx: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Strictly zero-leakage, zero-in-sample predictions for fold k of Instrument A."""
    d_vis = p5.write_fold_visible_features(X, valid, vis_k, m2.tip_kernels)
    vis_v = vis_k[valid]
    dvis_v = d_vis[valid]

    dist_test = ndi.distance_transform_edt(~region_k)
    pool_2d = valid & (~region_k) & (dist_test > EROSION_PX)

    py, px = np.nonzero(pool_2d)
    if np.ptp(py) >= np.ptp(px):
        cut = float(np.median(py))
        h0_raw = pool_2d & (np.arange(valid.shape[0])[:, None] < cut)
    else:
        cut = float(np.median(px))
        h0_raw = pool_2d & (np.arange(valid.shape[1])[None, :] < cut)
    h1_raw = pool_2d & (~h0_raw)

    h0_v = (h0_raw & (ndi.distance_transform_edt(~h1_raw) > EROSION_PX))[valid]
    h1_v = (h1_raw & (ndi.distance_transform_edt(~h0_raw) > EROSION_PX))[valid]

    # Split non-test domain cleanly between H0 and H1 prediction partitions
    h0_pred_v = h0_raw[valid]
    test_v = region_k[valid]
    other_v = (~h0_pred_v) & (~test_v)

    pos_bed = sgmc_v & (~vis_v) & (dvis_v >= 3.0)
    seed_base = 7100 + 20 * fold_idx

    # Purely physical 38-feature slice for BOTH M_bed AND M_neo (fixes IR-P5-1 hide-mask shift)
    X_stat = X[:, : p5.N_STATIC_FEATURES]
    m_bed_0 = p5.fit_oof_expert(
        X_stat, pos_bed, h0_v & (dvis_v >= 3.0), seed=seed_base + 1, n_features=p5.N_STATIC_FEATURES
    )
    m_bed_1 = p5.fit_oof_expert(
        X_stat, pos_bed, h1_v & (dvis_v >= 3.0), seed=seed_base + 2, n_features=p5.N_STATIC_FEATURES
    )

    m_neo_0 = p5.fit_oof_expert(
        X_stat, vis_v, h0_v, seed=seed_base + 3, n_features=p5.N_STATIC_FEATURES
    )
    m_neo_1 = p5.fit_oof_expert(
        X_stat, vis_v, h1_v, seed=seed_base + 4, n_features=p5.N_STATIC_FEATURES
    )

    # Exact per-partition rank calibration (fixes IR-P5-2 cross-partition base-rate shift)
    n_val = int(valid.sum())
    r_bed = np.empty(n_val, dtype=np.float32)
    r_neo = np.empty(n_val, dtype=np.float32)
    r_uns = np.empty(n_val, dtype=np.float32)

    r_bed[other_v] = p5.rank01_domain(m_bed_0.predict_proba(X_stat[other_v])[:, 1])
    r_bed[h0_pred_v] = p5.rank01_domain(m_bed_1.predict_proba(X_stat[h0_pred_v])[:, 1])
    r_bed[test_v] = p5.rank01_domain(
        0.5 * (m_bed_0.predict_proba(X_stat[test_v])[:, 1] + m_bed_1.predict_proba(X_stat[test_v])[:, 1])
    )

    r_neo[other_v] = p5.rank01_domain(m_neo_0.predict_proba(X_stat[other_v])[:, 1])
    r_neo[h0_pred_v] = p5.rank01_domain(m_neo_1.predict_proba(X_stat[h0_pred_v])[:, 1])
    r_neo[test_v] = p5.rank01_domain(
        0.5 * (m_neo_0.predict_proba(X_stat[test_v])[:, 1] + m_neo_1.predict_proba(X_stat[test_v])[:, 1])
    )

    for part_mask in (other_v, h0_pred_v, test_v):
        r_uns[part_mask] = p5.rank01_domain(unsup_vec[part_mask])

    # Frozen Run-2 weights locked at commit 1cd4823: (0.45 neo, 0.30 unsup, 0.25 bed)
    s_dual = (r_neo ** 0.45) * (r_uns ** 0.30) * (r_bed ** 0.25)
    return r_uns, r_bed, s_dual.astype(np.float32), d_vis


def predict_production_oof(
    X: np.ndarray,
    unsup_vec: np.ndarray,
    valid: np.ndarray,
    cat: np.ndarray,
    fp: np.ndarray,
    sgmc_v: np.ndarray,
    quad: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Assemble 100% spatially out-of-fold Nevada surfaces with per-quadrant rank calibration."""
    d_cat = p5.write_fold_visible_features(X, valid, cat, m2.tip_kernels)
    cat_v = cat[valid]
    dcat_v = d_cat[valid]
    pos_bed = sgmc_v & (~cat_v) & (dcat_v >= 3.0)

    n_val = int(valid.sum())
    r_bed = np.empty(n_val, dtype=np.float32)
    r_neo = np.empty(n_val, dtype=np.float32)
    r_uns = np.empty(n_val, dtype=np.float32)
    X_stat = X[:, : p5.N_STATIC_FEATURES]

    for k in range(4):
        test_q = (quad == k) & fp
        dist_q = ndi.distance_transform_edt(~test_q)
        tr_v = (valid & (~test_q) & (dist_q > EROSION_PX))[valid]
        te_v = (quad == k)[valid]
        m_bed_k = p5.fit_oof_expert(
            X_stat, pos_bed, tr_v & (dcat_v >= 3.0), seed=7005 + k, n_features=p5.N_STATIC_FEATURES
        )
        m_neo_k = p5.fit_oof_expert(
            X_stat, cat_v, tr_v, seed=7055 + k, n_features=p5.N_STATIC_FEATURES
        )
        r_bed[te_v] = p5.rank01_domain(m_bed_k.predict_proba(X_stat[te_v])[:, 1])
        r_neo[te_v] = p5.rank01_domain(m_neo_k.predict_proba(X_stat[te_v])[:, 1])
        r_uns[te_v] = p5.rank01_domain(unsup_vec[te_v])

    s_dual = (r_neo ** 0.45) * (r_uns ** 0.30) * (r_bed ** 0.25)
    return r_uns, r_bed, s_dual.astype(np.float32), d_cat


def build_registry_index(shape: tuple[int, int]) -> dict:
    """Include ALL 62 archive rasters + all local GEMSDOE70 downloads/rasters."""
    records = []
    seen_sha = set()
    scan_paths = list(sorted(REG.glob("*.tif"))) + list(sorted((ROOT / "docs/downloads").glob("*.tif")))
    for p in scan_paths:
        if p.name == f"{NAME}.tif":
            continue
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != shape:
                continue
        h = sha(p)
        if h in seen_sha:
            continue
        seen_sha.add(h)
        records.append(
            dict(
                repo_first=p.name.split("__")[0],
                submission=p.name,
                sources=[str(p)],
                cache_file=str(p),
                sha256=h,
            )
        )
    return dict(complete_accessible_scan=True, errors=[], rasters=records)


def audit_surface_and_dots(
    surf_2d: np.ndarray,
    dots_2d: np.ndarray,
    index: dict,
    fp: np.ndarray,
    expected_grid: tuple,
    tag: str,
) -> dict:
    tmp_s = CACHE / f"p5_surface_{tag}.tif"
    tmp_d = CACHE / f"p5_dots_{tag}.tif"
    tmp_s.parent.mkdir(parents=True, exist_ok=True)
    # Continuous surface normalized strictly into [0, 1] inside footprint
    s_norm = np.zeros_like(surf_2d, dtype=np.float32)
    s_norm[fp] = p5.rank01_domain(surf_2d[fp])
    write_geotiff(tmp_s, s_norm, nodata=None)
    write_geotiff(tmp_d, dots_2d.astype(np.float32), nodata=None)
    res_s = uniqueness.compare_to_registry(tmp_s, index, fp, expected_grid=expected_grid)
    res_d = uniqueness.compare_to_registry(tmp_d, index, fp, expected_grid=expected_grid)
    rows_sorted = sorted(
        res_d["rows"],
        key=lambda r: r.get("mutual_overlap", 0.0) or 0.0,
        reverse=True,
    )
    ok = bool(res_s["unique"] and res_s["duplicate_count"] == 0 and res_d["unique"] and res_d["duplicate_count"] == 0)
    return {
        "tag": tag,
        "all_pass": ok,
        "surface_pre_placement": {
            "unique": res_s["unique"],
            "duplicate_count": res_s["duplicate_count"],
            "registry_rasters_checked": res_s["registry_rasters_checked"],
            "worst_spearman_full_footprint": res_s["worst_spearman_full_footprint"],
            "worst_rho_submission": res_s["worst_rho_submission"],
            "worst_dot_overlap": res_s["worst_dot_overlap"],
            "worst_overlap_submission": res_s["worst_overlap_submission"],
        },
        "dots_final": {
            "unique": res_d["unique"],
            "duplicate_count": res_d["duplicate_count"],
            "registry_rasters_checked": res_d["registry_rasters_checked"],
            "overlap_definition": res_d.get("overlap_definition"),
            "worst_spearman_full_footprint": res_d["worst_spearman_full_footprint"],
            "worst_rho_submission": res_d["worst_rho_submission"],
            "worst_dot_overlap": res_d["worst_dot_overlap"],
            "worst_overlap_submission": res_d["worst_overlap_submission"],
            "worst_forward_overlap": res_d["worst_forward_overlap"],
            "worst_forward_submission": res_d["worst_forward_submission"],
            "worst_reverse_overlap": max(
                (r.get("their_dots_within_3px_of_mine") or 0.0) for r in res_d["rows"]
            ),
            "worst_jaccard_dot_sets": res_d["worst_jaccard_dot_sets"],
            "top_8_by_mutual_overlap": rows_sorted[:8],
        },
        "full_dots_report": res_d,
    }


def load_binary_raster(path: Path, fp: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1).astype(np.float32)
    return np.where(np.isfinite(a) & (a > 0.5) & fp, 1.0, 0.0).astype(np.float32)


def main() -> None:
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError("input pin mismatch: " + name)
    if sha(H33_PATH) != H33_SHA:
        raise ValueError("H33 SHA mismatch")

    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    with rasterio.open(DATA / "training_features.tif") as src:
        rtp = src.read(2).astype(np.float32)
    valid = np.isfinite(rtp) & (rtp > -1e30) & fp
    valid = ndi.binary_erosion(valid, iterations=12)
    del rtp

    with rasterio.open(SGMC_PATH) as src:
        sgmc = src.read(1) > 0
    sgmc_v = sgmc[valid]

    print(f"[{time.monotonic()-start:6.1f}s] Building 41-feature localized physical matrix...")
    cache_x = CACHE / "p5_static_features.npy"
    cache_u = CACHE / "p5_unsup_vec.npy"
    if cache_x.is_file() and cache_u.is_file():
        X_stat_cached = np.load(cache_x)
        unsup_vec = np.load(cache_u)
        X = np.empty((X_stat_cached.shape[0], p5.N_TOTAL_FEATURES), dtype=np.float32)
        X[:, : p5.N_STATIC_FEATURES] = X_stat_cached
        X[:, p5.N_STATIC_FEATURES :] = 0.0
        del X_stat_cached
    else:
        X, unsup_vec = p5.build_feature_matrix(valid, DATA, EXT)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.save(cache_x, X[:, : p5.N_STATIC_FEATURES])
        np.save(cache_u, unsup_vec)
    print(f"[{time.monotonic()-start:6.1f}s] Matrix ready: shape={X.shape} ({X.nbytes/1e6:.1f} MB)")

    folds_spec, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    quad = holdout.quadrant_ids(fp)

    # --- Protocol Rule 4: Single-feature leakage canaries BEFORE fitting ANY model ---
    p5.write_fold_visible_features(X, valid, folds_spec[0]["visible"], m2.tip_kernels)
    canary_a0 = p5.feature_leakage_canaries(X, (folds_spec[0]["truth"] & valid)[valid], seed=7005)
    d_cat_init = p5.write_fold_visible_features(X, valid, cat, m2.tip_kernels)
    proxy_all = sgmc & (~cat) & fp
    proxy_prime = proxy_all & (d_cat_init >= GAP_PRIME_PX)
    proxy_sens = proxy_all & (d_cat_init >= GAP_SENS_PX)
    canary_bp = p5.feature_leakage_canaries(X, (proxy_prime & valid)[valid], seed=7006)
    del d_cat_init

    leaks_a = [k for k, v in canary_a0.items() if v["suspected_leakage"]]
    leaks_bp = [k for k, v in canary_bp.items() if v["suspected_leakage"]]
    canary_doc = {
        "threshold_symmetric_auc": 0.90,
        "max_symmetric_auc_instrument_a_fold0": max(v["symmetric_auc"] for v in canary_a0.values()),
        "max_symmetric_auc_instrument_b_prime": max(v["symmetric_auc"] for v in canary_bp.values()),
        "leaks_a": leaks_a,
        "leaks_b_prime": leaks_bp,
        "all_clean": len(leaks_a) == 0 and len(leaks_bp) == 0,
        "per_feature_a_fold0": canary_a0,
        "per_feature_b_prime": canary_bp,
    }
    dump(E / "feature_leakage_canary.json", canary_doc)
    print(
        f"[{time.monotonic()-start:6.1f}s] Leakage canary clean={canary_doc['all_clean']} "
        f"(max_A={canary_doc['max_symmetric_auc_instrument_a_fold0']:.4f}, "
        f"max_B'={canary_doc['max_symmetric_auc_instrument_b_prime']:.4f})"
    )
    if not canary_doc["all_clean"]:
        raise RuntimeError(f"Protocol Rule 4 STOP: leakage detected {leaks_a} / {leaks_bp}")

    # Load benchmark rasters strictly for evaluation
    h33 = load_binary_raster(H33_PATH, fp)
    d28 = load_binary_raster(D28_PATH, fp)
    p4 = load_binary_raster(P4_PATH, fp)
    with rasterio.open(H19_PATH) as src:
        h19_surf = src.read(1).astype(np.float32)

    rng = np.random.default_rng(70420)  # identical RNG seed to run_experiment_v4.py!

    # --- Instrument A: shared hide-and-recover holdout across all 4 spatial folds ---
    arms_a = (
        "exp_5c",
        "exp_5b",
        "exp_5a",
        "ablation_5c_nms28",
        "h33_reference",
        "h33_fold_fair",
        "p4_reference",
        "d28_reference",
        "random_control",
    )
    terms_a = {a: 0.0 for a in arms_a}
    folds_a_out = {a: [] for a in arms_a}

    print(f"[{time.monotonic()-start:6.1f}s] Evaluating all arms on Instrument A (seed=20, 4 folds)...")
    for k, fold in enumerate(folds_spec):
        vis = fold["visible"]
        u_v, b_v, d_v, d_vis_k = predict_fold_a(
            X, unsup_vec, valid, vis, fold["region"], sgmc_v, k
        )
        allow_k = valid & (d_vis_k > COLLAR_PX)

        s_a = vec_to_2d(u_v, valid)
        s_b = vec_to_2d(b_v, valid)
        s_c = vec_to_2d(d_v, valid)

        dots_a, na = p5.submodular_pack_300m(s_a, allow_k, target_n=DOT_COUNT)
        dots_b, nb = p5.submodular_pack_300m(s_b, allow_k, target_n=DOT_COUNT)
        dots_c, nc = p5.submodular_pack_300m(s_c, allow_k, target_n=DOT_COUNT)
        dots_nms, _ = m2.place_dots(
            ndi.gaussian_filter(s_c, sigma=1.0), allow_k, n=DOT_COUNT, radius_px=2.8
        )
        dots_h33f, _ = p5.submodular_pack_300m(h19_surf, allow_k, target_n=DOT_COUNT)
        if not (na == nb == nc == DOT_COUNT):
            raise RuntimeError(f"Fold {k} dot count mismatch: {na}, {nb}, {nc}")

        ids = rng.choice(np.flatnonzero(valid & (~vis)), DOT_COUNT, replace=False)
        rand_f = np.zeros(grid.shape, np.float32)
        rand_f.ravel()[ids] = 1.0

        fold_maps = {
            "exp_5c": m2.dots_to_field(dots_c),
            "exp_5b": m2.dots_to_field(dots_b),
            "exp_5a": m2.dots_to_field(dots_a),
            "ablation_5c_nms28": m2.dots_to_field(dots_nms > 0),
            "h33_reference": h33,
            "h33_fold_fair": m2.dots_to_field(dots_h33f),
            "p4_reference": p4,
            "d28_reference": d28,
            "random_control": rand_f,
        }
        for arm, arr in fold_maps.items():
            r, t = cropped(fold, arr, valid)
            terms_a[arm] += t
            folds_a_out[arm].append(r)

        print(
            f"  [Inst A fold {k}] "
            f"5C={folds_a_out['exp_5c'][-1]['dti']:.5f} | "
            f"5B={folds_a_out['exp_5b'][-1]['dti']:.5f} | "
            f"5A={folds_a_out['exp_5a'][-1]['dti']:.5f} | "
            f"NMS28={folds_a_out['ablation_5c_nms28'][-1]['dti']:.5f} | "
            f"D28={folds_a_out['d28_reference'][-1]['dti']:.5f} | "
            f"H33fair={folds_a_out['h33_fold_fair'][-1]['dti']:.5f} | "
            f"P4={folds_a_out['p4_reference'][-1]['dti']:.5f}",
            flush=True,
        )

    sum_a_5c = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420, candidate="exp_5c")
    sum_a_5b = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420, candidate="exp_5b")
    sum_a_5a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420, candidate="exp_5a")

    # --- Production 4-Quadrant OOF Fit + Surfaces + Final Dots ---
    print(f"[{time.monotonic()-start:6.1f}s] Fitting 4-quadrant OOF models for production GeoTIFF + B/B'/B''...")
    r_uns_prod, r_bed_prod, s_dual_prod, d_cat = predict_production_oof(
        X, unsup_vec, valid, cat, fp, sgmc_v, quad
    )
    del X  # free 800 MB immediately
    allow_prod = valid & (d_cat > COLLAR_PX)

    surf_5a = vec_to_2d(r_uns_prod, valid)
    surf_5b = vec_to_2d(r_bed_prod, valid)
    surf_5c = vec_to_2d(s_dual_prod, valid)

    dots_5a_b, n5a = p5.submodular_pack_300m(surf_5a, allow_prod, target_n=DOT_COUNT)
    dots_5b_b, n5b = p5.submodular_pack_300m(surf_5b, allow_prod, target_n=DOT_COUNT)
    dots_5c_b, n5c = p5.submodular_pack_300m(surf_5c, allow_prod, target_n=DOT_COUNT)
    dots_nms_b, _ = m2.place_dots(
        ndi.gaussian_filter(surf_5c, sigma=1.0), allow_prod, n=DOT_COUNT, radius_px=2.8
    )
    if not (n5a == n5b == n5c == DOT_COUNT):
        raise RuntimeError(f"Production dot count mismatch: {n5a}, {n5b}, {n5c}")

    prod_5a = m2.dots_to_field(dots_5a_b)
    prod_5b = m2.dots_to_field(dots_5b_b)
    prod_5c = m2.dots_to_field(dots_5c_b)
    prod_nms = m2.dots_to_field(dots_nms_b > 0)

    ids = rng.choice(np.flatnonzero(valid & (~cat)), DOT_COUNT, replace=False)
    prod_random = np.zeros(grid.shape, np.float32)
    prod_random.ravel()[ids] = 1.0

    # --- Instrument B' (d_cat >= 3, primary), B (all), and B'' (d_cat >= 5 sensitivity) ---
    arms_b = (
        "exp_5c",
        "exp_5b",
        "exp_5a",
        "ablation_5c_nms28",
        "h33_reference",
        "p4_reference",
        "d28_reference",
        "random_control",
    )
    prod_maps = {
        "exp_5c": prod_5c,
        "exp_5b": prod_5b,
        "exp_5a": prod_5a,
        "ablation_5c_nms28": prod_nms,
        "h33_reference": h33,
        "p4_reference": p4,
        "d28_reference": d28,
        "random_control": prod_random,
    }
    terms_bprime = {a: 0.0 for a in arms_b}
    terms_ball = {a: 0.0 for a in arms_b}
    terms_bsens = {a: 0.0 for a in arms_b}
    folds_bprime = {a: [] for a in arms_b}

    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for tag, mask, store in (
            ("prime", proxy_prime, terms_bprime),
            ("all", proxy_all, terms_ball),
            ("sens5", proxy_sens, terms_bsens),
        ):
            fold = dict(
                region=region,
                truth=mask & region & (~cat),
                visible=cat,
                masked_known=cat,
                hidden_all=np.zeros_like(cat),
            )
            for arm, arr in prod_maps.items():
                r, t = cropped(fold, arr, valid)
                store[arm] += t
                if tag == "prime":
                    folds_bprime[arm].append(r)

    sum_bp_5c = evaluate_holdout.pooled_summary(terms_bprime, draws=1000, seed=70420, candidate="exp_5c")
    sum_bp_5b = evaluate_holdout.pooled_summary(terms_bprime, draws=1000, seed=70420, candidate="exp_5b")
    sum_bp_5a = evaluate_holdout.pooled_summary(terms_bprime, draws=1000, seed=70420, candidate="exp_5a")
    sum_ball_5c = evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=70420, candidate="exp_5c")
    sum_bsens_5c = evaluate_holdout.pooled_summary(terms_bsens, draws=1000, seed=70420, candidate="exp_5c")

    print("\n=== POOLED RESULTS SUMMARY ===")
    for arm in arms_a:
        sc = sum_a_5c["scores"][arm]
        print(
            f"  [Instrument A HOLDOUT-DTI] {arm:18s}: {sc['dti']:.5f} "
            f"CI95=[{sc['ci95'][0]:.5f}, {sc['ci95'][1]:.5f}] "
            f"(K={sc['withheld_positive_pixels']}, cal_K7905={calibrated_dti_at_k(sc['dti'], sc['withheld_positive_pixels'], DOT_COUNT):.4f})"
        )
    print("-" * 72)
    for arm in arms_b:
        sc = sum_bp_5c["scores"][arm]
        sc5 = sum_bsens_5c["scores"][arm]
        sca = sum_ball_5c["scores"][arm]
        print(
            f"  [Instrument B' PROXY-DTI ] {arm:18s}: d>=3: {sc['dti']:.5f} "
            f"[{sc['ci95'][0]:.5f}, {sc['ci95'][1]:.5f}] | "
            f"d>=5: {sc5['dti']:.5f} | all: {sca['dti']:.5f} | "
            f"cal_K7905={calibrated_dti_at_k(sc['dti'], sc['withheld_positive_pixels'], DOT_COUNT):.4f}"
        )

    # --- Protocol Rule 1: Complete Uniqueness Scan BEFORE AND AFTER Dot Placement ---
    print(f"\n[{time.monotonic()-start:6.1f}s] Running complete 66-raster uniqueness scan (surface + dots)...")
    reg_index = build_registry_index(grid.shape)
    expected_grid = (grid.shape, grid.crs, grid.transform)
    uq_5a = audit_surface_and_dots(surf_5a, prod_5a, reg_index, fp, expected_grid, "exp_5a")
    uq_5b = audit_surface_and_dots(surf_5b, prod_5b, reg_index, fp, expected_grid, "exp_5b")
    uq_5c = audit_surface_and_dots(surf_5c, prod_5c, reg_index, fp, expected_grid, "exp_5c")

    for tag, uqr in (("5A", uq_5a), ("5B", uq_5b), ("5C", uq_5c)):
        df = uqr["dots_final"]
        sp = uqr["surface_pre_placement"]
        print(
            f"  [Uniqueness {tag}] pass={uqr['all_pass']} (N={df['registry_rasters_checked']}) | "
            f"surface |rho|_max={abs(sp['worst_spearman_full_footprint']):.4f} ({sp['worst_rho_submission']}) | "
            f"dots mutual_ov={df['worst_dot_overlap']:.4f}, fwd_ov={df['worst_forward_overlap']:.4f}, "
            f"rev_ov={df['worst_reverse_overlap']:.4f} ({df['worst_overlap_submission']})"
        )
        if not uqr["all_pass"]:
            raise RuntimeError(f"Protocol Rule 1 STOP: duplicate detected on Exp {tag}")

    # --- Evaluate ALL Frozen Preregistered Promotion Gates (`commit abc7c6e`) ---
    def eval_gates(sum_a: dict, sum_bp: dict, uqr: dict) -> tuple[bool, dict]:
        da = sum_a["paired_differences"]
        db = sum_bp["paired_differences"]
        g = {
            "canary_clean": canary_doc["all_clean"],
            "uniqueness_surface_and_dots": uqr["all_pass"],
            "inst_a_gt_h33_static_ci95": bool(da["h33_reference"]["delta"] > 0 and da["h33_reference"]["ci95"][0] > 0),
            "inst_a_gt_h33_fair_ci95": bool(da["h33_fold_fair"]["delta"] > 0 and da["h33_fold_fair"]["ci95"][0] > 0),
            "inst_a_gt_p4_ci95": bool(da["p4_reference"]["delta"] > 0 and da["p4_reference"]["ci95"][0] > 0),
            "inst_a_gt_d28_ci95": bool(da["d28_reference"]["delta"] > 0 and da["d28_reference"]["ci95"][0] > 0),
            "inst_a_gt_random_ci95": bool(da["random_control"]["delta"] > 0 and da["random_control"]["ci95"][0] > 0),
            "inst_bp_gt_h33_ci95": bool(db["h33_reference"]["delta"] > 0 and db["h33_reference"]["ci95"][0] > 0),
            "inst_bp_gt_p4_ci95": bool(db["p4_reference"]["delta"] > 0 and db["p4_reference"]["ci95"][0] > 0),
            "inst_bp_gt_d28_ci95": bool(db["d28_reference"]["delta"] > 0 and db["d28_reference"]["ci95"][0] > 0),
            "inst_bp_gt_random_ci95": bool(db["random_control"]["delta"] > 0 and db["random_control"]["ci95"][0] > 0),
        }
        return all(g.values()), g

    ok_5c, gates_5c = eval_gates(sum_a_5c, sum_bp_5c, uq_5c)
    ok_5b, gates_5b = eval_gates(sum_a_5b, sum_bp_5b, uq_5b)
    ok_5a, gates_5a = eval_gates(sum_a_5a, sum_bp_5a, uq_5a)
    print(f"\n[{time.monotonic()-start:6.1f}s] Frozen Promotion Gates -> 5C={ok_5c} | 5B={ok_5b} | 5A={ok_5a}")
    print("  5C gates:", json.dumps(gates_5c))
    print("  5B gates:", json.dumps(gates_5b))

    # Strict preregistered selection order: Exp 5C (Primary) -> Exp 5B (Fallback) -> negative
    if ok_5c:
        chosen_key, chosen_prod, chosen_sum_a, chosen_sum_bp, chosen_uq, chosen_gates, promoted = (
            "exp_5c", prod_5c, sum_a_5c, sum_bp_5c, uq_5c, gates_5c, True
        )
    elif ok_5b:
        chosen_key, chosen_prod, chosen_sum_a, chosen_sum_bp, chosen_uq, chosen_gates, promoted = (
            "exp_5b", prod_5b, sum_a_5b, sum_bp_5b, uq_5b, gates_5b, True
        )
    else:
        chosen_key, chosen_prod, chosen_sum_a, chosen_sum_bp, chosen_uq, chosen_gates, promoted = (
            "exp_5c", prod_5c, sum_a_5c, sum_bp_5c, uq_5c, gates_5c, False
        )

    # Emit GeoTIFF + ZIP via shared vendor/gems57/submission_writer.py
    receipt = submission_writer.write_submission(
        ROOT / "docs/downloads" / f"{NAME}.tif",
        chosen_prod,
        ROOT / "data/bridge/sample_submission.tif",
        fp,
        note=NOTE,
        name=NAME,
        catalogue=cat,
        metadata={
            "evidence_class": "HOLDOUT-DTI + PROXY-DTI; not organizer-confirmed",
            "chosen_experiment": chosen_key,
            "preregistration_commit": "abc7c6e",
        },
    )
    validated = receipt["validator"]

    # Distance profile diagnostic across blind basins vs near-catalogue band
    d_chosen = d_cat[chosen_prod > 0.5]
    dist_profile = {
        "dot_count": int((chosen_prod > 0.5).sum()),
        "min_d_cat_px": float(d_chosen.min()),
        "p25_d_cat_px": float(np.quantile(d_chosen, 0.25)),
        "median_d_cat_px": float(np.median(d_chosen)),
        "p90_d_cat_px": float(np.quantile(d_chosen, 0.90)),
        "frac_3_to_10px": float(((d_chosen >= 3.0) & (d_chosen <= 10.0)).mean()),
        "frac_10_to_32px": float(((d_chosen > 10.0) & (d_chosen <= 32.0)).mean()),
        "frac_gt_32px_blind_basins": float((d_chosen > 32.0).mean()),
    }

    # Save modular Phase-5 receipts cleanly in evidence/phase5/ (NEVER modifying frozen phase2..phase4!)
    dump(E / "instrumentA_holdout.json", sum_a_5c)
    dump(E / "instrumentA_folds.json", folds_a_out)
    dump(E / "instrumentB_prime.json", sum_bp_5c)
    dump(E / "instrumentB_prime_folds.json", folds_bprime)
    dump(E / "instrumentB_all.json", sum_ball_5c)
    dump(E / "instrumentB_sens_d5.json", sum_bsens_5c)
    dump(
        E / "uniqueness.json",
        {
            "exp_5a": {k: v for k, v in uq_5a.items() if k != "full_dots_report"},
            "exp_5b": {k: v for k, v in uq_5b.items() if k != "full_dots_report"},
            "exp_5c": {k: v for k, v in uq_5c.items() if k != "full_dots_report"},
            "chosen_full_report": chosen_uq["full_dots_report"],
        },
    )
    dump(
        E / "submission_receipt.json",
        dict(receipt=receipt, validated=validated, duplicate=not chosen_uq["all_pass"]),
    )

    df_u = chosen_uq["dots_final"]
    sp_u = chosen_uq["surface_pre_placement"]
    elapsed = round(time.monotonic() - start, 2)

    card = {
        "hypothesis": (
            "H-P5-1 Dual-Population Multi-Sensor 4-Fold OOF HGB Synthesis + "
            "Exact Unblurred 300 m Submodular Max-Cover (chosen arm: " + chosen_key + ")"
        ),
        "mechanism": (
            "Out-of-fold dual-population HistGradientBoostingClassifier ensemble combining "
            "pre-2022 mapped bedrock faults outside the catalogue duplication band (SGMC d_cat >= 3 px) "
            "and Quaternary neotectonic traces across 41 localized physical channels (GeoDAWN "
            "gravity/magnetic/radiometric high-pass residuals & gradients, GPS crustal strain rates, "
            "USGS 3DEP 1 m LiDAR & seamless 10 m DEM scarp morphology, DOE GDR 1391 thermal springs, "
            "2 m probes, and paleo-sinter conduits), emitted via exact unblurred 300 m triangular-kernel "
            "lazy-greedy submodular max-cover at exact 37,654 binary off-catalogue pixels."
        ),
        "non_fault_mimic": (
            "Erosional range-front pediment breaks, volcanic flow margins, and intact pluton boundaries "
            "suppressed via high-pass anomaly localization and orthogonal cross-gradient features."
        ),
        "verdict": (
            "promote"
            if (promoted and bool(validated and validated.get("all_checks_passed")))
            else "negative"
        ),
        "evidence_class": (
            f"HOLDOUT-DTI (Instrument A, {evaluate_holdout.VERSION}) and "
            f"PROXY-DTI (Instrument B'/B/B'', {evaluate_holdout.VERSION}); neither organizer-confirmed"
        ),
        "chosen_experiment": chosen_key,
        "preregistration_commit": "1cd4823",
        "prior_run1_receipt": "evidence/phase5/run1_v50_run_card.json",
        "promotion_gates": chosen_gates,
        "all_experiment_gates": {"exp_5c": gates_5c, "exp_5b": gates_5b, "exp_5a": gates_5a},
        "instrument_a_holdout": {
            k: {
                "dti": v["dti"],
                "ci95": v["ci95"],
                "withheld_positive_pixels": v["withheld_positive_pixels"],
                "calibrated_dti_k7905": calibrated_dti_at_k(
                    v["dti"], v["withheld_positive_pixels"], DOT_COUNT
                ),
            }
            for k, v in chosen_sum_a["scores"].items()
        },
        "instrument_b_prime_proxy": {
            k: {
                "dti": v["dti"],
                "ci95": v["ci95"],
                "withheld_positive_pixels": v["withheld_positive_pixels"],
                "calibrated_dti_k7905": calibrated_dti_at_k(
                    v["dti"], v["withheld_positive_pixels"], DOT_COUNT
                ),
            }
            for k, v in chosen_sum_bp["scores"].items()
        },
        "instrument_b_sensitivity_d5": {
            k: {"dti": v["dti"], "ci95": v["ci95"], "withheld_positive_pixels": v["withheld_positive_pixels"]}
            for k, v in sum_bsens_5c["scores"].items()
        },
        "instrument_b_unrestricted": {
            k: {"dti": v["dti"], "ci95": v["ci95"], "withheld_positive_pixels": v["withheld_positive_pixels"]}
            for k, v in sum_ball_5c["scores"].items()
        },
        "paired_differences_instrument_a": chosen_sum_a["paired_differences"],
        "paired_differences_instrument_b_prime": chosen_sum_bp["paired_differences"],
        "feature_leakage_canary": {
            "threshold_symmetric_auc": 0.90,
            "max_symmetric_auc_instrument_a_fold0": canary_doc["max_symmetric_auc_instrument_a_fold0"],
            "max_symmetric_auc_instrument_b_prime": canary_doc["max_symmetric_auc_instrument_b_prime"],
            "all_clean": canary_doc["all_clean"],
        },
        "correlation_overlap_vs_registry": {
            "stage": "both continuous pre-placement surface AND final 37,654 binary dots",
            "rasters_checked": df_u["registry_rasters_checked"],
            "surface_worst_spearman_full_footprint": sp_u["worst_spearman_full_footprint"],
            "surface_worst_rho_submission": sp_u["worst_rho_submission"],
            "worst_mutual_overlap": df_u["worst_dot_overlap"],
            "worst_mutual_submission": df_u["worst_overlap_submission"],
            "worst_forward_overlap": df_u["worst_forward_overlap"],
            "worst_forward_submission": df_u["worst_forward_submission"],
            "worst_reverse_overlap": df_u["worst_reverse_overlap"],
            "worst_spearman_full_footprint": df_u["worst_spearman_full_footprint"],
            "worst_rho_submission": df_u["worst_rho_submission"],
            "worst_jaccard": df_u["worst_jaccard_dot_sets"],
            "duplicate": not chosen_uq["all_pass"],
        },
        "distance_distribution": dist_profile,
        "raster_sha256": receipt["sha256"],
        "zip_sha256": sha(ROOT / "docs/downloads" / f"{NAME}.zip"),
        "validator_output": validated,
        "submission_name": NAME,
        "submission_note": NOTE,
        "note_chars": len(NOTE),
        "download_ok": bool(validated and validated.get("all_checks_passed") and chosen_uq["all_pass"]),
        "submit_recommended": bool(
            promoted and validated and validated.get("all_checks_passed") and chosen_uq["all_pass"]
        ),
        "download_and_submit_ok": bool(
            promoted and validated and validated.get("all_checks_passed") and chosen_uq["all_pass"]
        ),
        "weekly_slots_used": 0,
        "experiment_count": 2,
        "elapsed_seconds": elapsed,
        "organizer_confirmed_score": None,
        "evaluator_implementation_sha256": evaluate_holdout.implementation_hashes(),
        "method_source_sha256": {
            p: sha(ROOT / p)
            for p in ["src/gems70/phase5.py", "src/gems70/method_v2.py", "scripts/run_experiment_v5.py"]
        },
        "registered_parameters": {
            "dot_count": DOT_COUNT,
            "collar_px": COLLAR_PX,
            "erosion_px": EROSION_PX,
            "dual_weights_neo_unsup_bed": [0.45, 0.30, 0.25],
            "n_static_physical_features": p5.N_STATIC_FEATURES,
            "per_partition_rank_calibration": True,
            "submodular_support_quantile": 0.90,
            "submodular_gamma": 2.0,
            "b_prime_gap_px": GAP_PRIME_PX,
        },
    }
    dump(E / "run_card.json", card)
    print(f"\n[{elapsed:6.1f}s] COMPLETE — verdict={card['verdict']} | sha256={card['raster_sha256']}")


if __name__ == "__main__":
    main()
