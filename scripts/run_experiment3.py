"""Experiment 3 (H70-3A dual-detector rank fusion): one preregistered run, seed 703 untouched holdout.

Refuses to rerun if evidence/experiment2_manifest.json exists. Uses only the
shared vendor/gems57 evaluator, holdout draw and emit ranking. No prior
submission raster is read as an input.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]
import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems57 import emit, evaluate_holdout, holdout
from gems57.grid import load_grid
from gems70.method import physical_features, joint_field
from gems70.method2 import coherence, corroboration_gate, dequant, domain_surfaces, multiscale_edge, ortho_gate_score, road_factor

E = ROOT / "evidence"
CACHE = ROOT / ".cache"
DATA = CACHE / "data"
EXT = CACHE / "gems_data/external"
DEM10 = CACHE / "gems_data/dem10"
SEED = 703
GLOBAL_BUDGET = 37654


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cropped(fold, p, valid):
    y, x = np.nonzero(fold["region"])
    y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
    y1, x1 = min(p.shape[0], int(y.max()) + 7), min(p.shape[1], int(x.max()) + 7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k: v[sl] for k, v in fold.items() if isinstance(v, np.ndarray) and v.shape == p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0, x0), global_shape=p.shape)


def main():
    start = time.monotonic()
    manifest = E / "experiment3_manifest.json"
    if manifest.exists():
        raise RuntimeError("Experiment 3 already attempted. Inspect evidence; no silent reruns/tuning on these folds.")
    dump(manifest, {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "experiment_id": "H70-3A",
        "experiment_count_total": 3, "maximum_experiments": 3, "maximum_seconds": 7200, "seed": SEED,
        "preregistration_sha256": sha(ROOT / "docs/hypotheses-exp3.md"),
        "source_sha256": {p: sha(ROOT / p) for p in ["src/gems70/method2.py", "src/gems70/method.py", "scripts/run_experiment3.py"]},
    })

    grid = load_grid(DATA)
    fp = grid.footprint
    cat = grid.catalogue
    H, W = fp.shape
    fp_idx = np.flatnonzero(fp.ravel())
    N = len(fp_idx)

    def vec(grid_arr):
        return np.nan_to_num(grid_arr.ravel()[fp_idx], nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    def to_grid(v):
        g = np.zeros(H * W, np.float32)
        g[fp_idx] = v
        return g.reshape(H, W)

    print("[1/6] Loading label-free feature stack (band-by-band, memory-lean)...", flush=True)
    _src = rasterio.open(DATA / "training_features.tif")
    def band(i):
        a = _src.read(i).astype(np.float32)
        a[(a <= -1e30) | ~np.isfinite(a)] = np.nan
        return a
    F: dict[str, np.ndarray] = {}
    slope = np.where(fp, band(19), 0).astype(np.float32)
    grav = np.where(fp, band(13), 0).astype(np.float32)
    rtp = np.where(fp, band(2), 0).astype(np.float32)
    F["elev_slope"] = vec(slope)
    F["topo_edge"] = vec(multiscale_edge(slope, fp))
    F["topo_coh"] = vec(coherence(slope, fp))
    F["mag_hg_log"] = vec(np.log1p(np.maximum(band(3), 0)))
    F["mag_vg"] = vec(band(9))
    F["mag_edge"] = F["mag_hg_log"]
    F["grav_hg_abs"] = vec(np.abs(band(18)))
    F["grav_edge"] = F["grav_hg_abs"]
    F["grav_slope"] = vec(band(5))
    F["tc"] = vec(band(6))
    base_sm = ndi.gaussian_filter(np.where(fp, band(15), 0), 3)
    gy, gx = np.gradient(base_sm)
    F["basement_grad"] = vec(np.hypot(gy, gx))
    del gy, gx
    _c = np.where(fp, band(17), 0); F["cond_anom"] = vec(_c - ndi.uniform_filter(_c, size=21)); del _c
    _r = np.where(fp, band(2), 0); F["rtp_anom"] = vec(_r - ndi.uniform_filter(_r, size=15)); del _r
    _e = np.where(fp, band(12), 0); F["elev_anom"] = vec(_e - ndi.uniform_filter(_e, size=15)); del _e
    F["shear_abs"] = vec(np.abs(band(7)))
    F["dil_abs"] = vec(np.abs(band(8)))
    F["ieq_log"] = vec(np.log1p(np.maximum(band(16), 0)))
    _src.close()
    # Gallardo-Meju style magnitude-weighted alignment of gravity vs magnetic gradients
    ggy, ggx = np.gradient(ndi.gaussian_filter(grav, 2))
    mgy, mgx = np.gradient(ndi.gaussian_filter(rtp, 2))
    gm = np.hypot(ggy, ggx); mm = np.hypot(mgy, mgx)
    ok = fp & (gm > 0) & (mm > 0)
    cos2 = np.where(ok, ((ggx * mgx + ggy * mgy) / np.maximum(gm * mm, 1e-12)) ** 2, 0)
    gn = np.where(ok, np.clip(gm / np.percentile(gm[ok], 95), 0, 1), 0)
    mn = np.where(ok, np.clip(mm / np.percentile(mm[ok], 95), 0, 1), 0)
    F["xgrad_align"] = vec((gn * mn * cos2).astype(np.float32))
    del ggy, ggx, mgy, mgx, gm, mm, ok, cos2, gn, mn
    # --- 1 m LiDAR scarp (dequantised) ---
    lid_meta = json.loads((EXT / "lidar_scarp_features.json").read_text())["quantisation"]
    lid_names = ["ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max", "downface_max",
                 "upface_max", "cross_max", "relief", "coh100", "strike", "valid"]
    lid = {}
    with rasterio.open(EXT / "lidar_scarp_features_u8.tif") as src:
        for i, n in enumerate(lid_names, start=1):
            lid[n] = dequant(src.read(i), *lid_meta[n])
    tect = (np.maximum(lid["downface_max"], 1.35 * lid["upface_max"]) * (0.3 + lid["coh100"])) / (lid["cross_max"] + 0.08)
    F["lid_tect"] = vec(np.where(lid["valid"] > 0.5, tect, 0))
    F["lid_dipole"] = vec(np.sqrt(np.maximum(lid["lapneg_max"] * lid["lappos_max"], 0)))
    F["lid_step"] = vec(lid["step_max"])
    F["lid_valid"] = vec((lid["valid"] > 0.5).astype(np.float32))
    del lid, tect
    # --- 1 m Openness/LRM high-prior tiles (footprint vectors) ---
    npz = np.load(EXT / "dem1m_high_prior_openness_lrm.npz")
    cov = npz["cov_fp_indices"].astype(int)
    for key, name in [("openness_dipole_max", "open_dipole"), ("lrm_grad_max", "lrm_grad")]:
        v = np.zeros(N, np.float32)
        v[cov] = npz[key].astype(np.float32)
        F[name] = v
    # --- 10 m DEM channels (footprint vectors, manifest order) ---
    for ch, name in [("dem10_onesided3", "dem10_onesided3"), ("dem10_onesided", "dem10_onesided"),
                     ("dem10_steep_ratio_max", "dem10_steep"), ("dem10_curv_absmax", "dem10_curv"),
                     ("dem10_slope_max", "dem10_slope_max")]:
        v = np.load(DEM10 / f"{ch}.f32.npy").astype(np.float32)
        assert len(v) == N, ch
        F[name] = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)
    # --- GeoDAWN radiometrics + up150 ---
    with rasterio.open(EXT / "geodawn_rad_u8.tif") as src:
        k_u8, th_u8, tc_u8 = src.read(1).astype(np.float32), src.read(2).astype(np.float32), src.read(4).astype(np.float32)
    kth = (k_u8 + 1.0) / (th_u8 + 10.0)
    F["kth_anom"] = vec(kth - ndi.uniform_filter(kth, size=21))
    tcg = np.hypot(*np.gradient(tc_u8))
    F["rad_grad"] = vec(tcg)
    with rasterio.open(EXT / "geodawn_extensions_u8.tif") as src:
        up150 = src.read(4).astype(np.float32)
    F["up150_grad"] = vec(np.hypot(*np.gradient(up150)))
    del k_u8, th_u8, tc_u8, kth, tcg, up150
    # --- GDR 1391 thermal/geochemical conduit density (dist_known_fault_px never read as feature) ---
    import csv
    thermal = np.zeros((H, W), np.float32)
    with open(EXT / "gdr_wellspring_in_footprint.csv") as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(row["row"]), int(row["col"])
                temp = float(row["temp_c"] or 0)
                geo = max([float(row[k] or 0) for k in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c")])
            except (ValueError, KeyError):
                continue
            wgt = np.clip(temp, 0, 120) / 120.0 + np.clip(geo, 0, 220) / 220.0
            if 0 <= r < H and 0 <= c < W and wgt > 0.3:
                thermal[r, c] += wgt
    thermal = ndi.gaussian_filter(thermal, 4)
    F["thermal_density"] = vec(thermal)
    for fn, name in [("derived_gdr_2m_probes_100m_u8.tif", "probe_density"), ("derived_gdr_paleo_100m_u8.tif", "paleo_density")]:
        with rasterio.open(EXT / fn) as src:
            a = src.read(1).astype(np.float32)
        F[name] = vec(ndi.gaussian_filter(a, 2))
    with rasterio.open(EXT / "tiger_road_distance_m.tif") as src:
        road = src.read(1).astype(np.float32)
    F["road_dist"] = vec(np.clip(road, 0, 3000))
    road_grid = np.where(fp, road, 0).astype(np.float32)
    del road

    FEATURES = [k for k in F.keys()]
    CROSS = {"lid_tect", "lid_dipole", "lid_step", "lid_valid", "open_dipole", "lrm_grad",
             "dem10_onesided3", "dem10_onesided", "dem10_steep", "dem10_curv", "dem10_slope_max"}
    NOCROSS = [f for f in FEATURES if f not in CROSS]
    X = np.column_stack([F[f] for f in FEATURES]).astype(np.float32)
    NC_IDX = [FEATURES.index(f) for f in NOCROSS]
    print(f"  features={len(FEATURES)} footprint_px={N:,}", flush=True)

    print("[2/6] Holdout draw seed=703 + leakage canaries...", flush=True)
    folds, quad = holdout.buffered_component_draw(grid, seed=SEED, buffer_px=3, boundary_px=12)
    dump(E / "holdout3_split.json", {"evidence_class": "HOLDOUT-DTI", "evaluator_version": evaluate_holdout.VERSION,
        "seed": SEED, "receipts": [f["receipt"] for f in folds],
        "total_withheld_positive_pixels": int(sum(f["truth"].sum() for f in folds)),
        "catalogue_predictors": [], "limitation": "Mapped components are a surrogate for previously unmapped faults; no hidden organizer labels."})
    truth_all = np.zeros(fp.shape, bool)
    active_all = np.zeros(fp.shape, bool)
    for f in folds:
        truth_all |= f["truth"]
        active_all |= fp & f["region"] & ~f["masked_known"]
    pos_flat = np.flatnonzero(truth_all.ravel())
    pos_pos = np.searchsorted(fp_idx, pos_flat)
    rng = np.random.default_rng(SEED)
    neg_candidates = np.flatnonzero((active_all & ~truth_all).ravel())
    neg_flat = rng.choice(neg_candidates, min(200000, len(neg_candidates)), replace=False)
    neg_pos = np.searchsorted(fp_idx, neg_flat)
    canaries = {}
    for name in FEATURES:
        v = np.r_[F[name][pos_pos], F[name][neg_pos]]
        labels = np.r_[np.ones(len(pos_pos)), np.zeros(len(neg_pos))]
        auc = float(roc_auc_score(labels, v))
        canaries[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc, "inverse_auc": 1 - auc,
                          "withheld_positive_pixels": int(len(pos_pos)), "negative_sample_pixels": int(len(neg_pos)),
                          "suspected_leakage": bool(max(auc, 1 - auc) > 0.90)}
    dump(E / "canaries3.json", canaries)
    if any(c["suspected_leakage"] for c in canaries.values()):
        raise RuntimeError("LEAKAGE CANARY STOP: feature-alone AUC > .90")
    print("  canaries pass. max |AUC-0.5| =", max(abs(c["auc"] - 0.5) for c in canaries.values()), flush=True)
    _keep = {"lid_tect", "dem10_onesided3", "topo_edge", "mag_edge", "grav_edge", "kth_anom", "thermal_density"}
    for _k in list(F):
        if _k not in _keep:
            del F[_k]
    import gc; gc.collect()

    print("[3/6] Out-of-fold supervised models (full + no-cross-scale)...", flush=True)
    visible = folds[0]["visible"]
    vis_pos_all = np.searchsorted(fp_idx, np.flatnonzero(visible.ravel()))
    quad_fp = quad.ravel()[fp_idx]
    surf_oof = np.zeros(N, np.float32)
    surf_oof_nc = np.zeros(N, np.float32)

    def train_predict(cols, train_quads_exclude, target_mask_fp):
        Xmat = X if cols is None else X[:, cols]
        tr_pos = vis_pos_all[np.isin(quad_fp[vis_pos_all], train_quads_exclude, invert=True)]
        # negatives: footprint, training quads, >3px from any catalogue pixel
        dist_cat = ndi.distance_transform_edt(~cat)
        neg_pool = np.flatnonzero((fp & (dist_cat > 3)).ravel())
        neg_pool_pos = np.searchsorted(fp_idx, neg_pool)
        neg_pool_pos = neg_pool_pos[np.isin(quad_fp[neg_pool_pos], train_quads_exclude, invert=True)]
        r = np.random.default_rng(SEED + int(train_quads_exclude[0]))
        tr_neg = r.choice(neg_pool_pos, min(10 * len(tr_pos), len(neg_pool_pos)), replace=False)
        Xtr = np.vstack([Xmat[tr_pos], Xmat[tr_neg]])
        ytr = np.r_[np.ones(len(tr_pos)), np.zeros(len(tr_neg))]
        wtr = np.r_[np.full(len(tr_pos), len(tr_neg) / max(len(tr_pos), 1)), np.ones(len(tr_neg))]
        clf = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.06, max_leaf_nodes=63,
                                             min_samples_leaf=40, l2_regularization=1.0, random_state=SEED)
        clf.fit(Xtr, ytr, sample_weight=wtr)
        return clf.predict_proba(Xmat[target_mask_fp])[:, 1].astype(np.float32)  # target rows only

    for f in folds:
        q = f["fold"]
        region_fp = f["region"].ravel()[fp_idx]
        surf_oof[region_fp] = train_predict(None, [q], region_fp)
        surf_oof_nc[region_fp] = train_predict(NC_IDX, [q], region_fp)
        print(f"  fold {f['name']} done ({time.monotonic()-start:.0f}s)", flush=True)

    print("[4/6] Final model on all visible catalogue + domain gate...", flush=True)
    allq = [0, 1, 2, 3]
    # final: train excluding nothing (train_quads_exclude empty trick: use all quads as train)
    dist_cat = ndi.distance_transform_edt(~cat)
    neg_pool = np.flatnonzero((fp & (dist_cat > 3)).ravel())
    neg_pool_pos = np.searchsorted(fp_idx, neg_pool)
    r = np.random.default_rng(SEED + 99)
    tr_neg = r.choice(neg_pool_pos, min(10 * len(vis_pos_all), len(neg_pool_pos)), replace=False)
    Xtr = np.vstack([X[vis_pos_all], X[tr_neg]])
    ytr = np.r_[np.ones(len(vis_pos_all)), np.zeros(len(tr_neg))]
    wtr = np.r_[np.full(len(vis_pos_all), len(tr_neg) / max(len(vis_pos_all), 1)), np.ones(len(tr_neg))]
    clf_final = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.06, max_leaf_nodes=63,
                                               min_samples_leaf=40, l2_regularization=1.0, random_state=SEED)
    clf_final.fit(Xtr, ytr, sample_weight=wtr)
    surf_final_vec = clf_final.predict_proba(X)[:, 1].astype(np.float32)

    feat_grid = {k: to_grid(F[k]) for k in ("lid_tect", "dem10_onesided3", "topo_edge", "mag_edge", "grav_edge", "kth_anom", "thermal_density")}
    domains = domain_surfaces(feat_grid, fp)
    gate = corroboration_gate(domains, fp)
    roadf = road_factor(road_grid, fp)
    gated_oof_grid = to_grid(surf_oof) * gate * roadf
    # H70-3A candidate: geometric mean of footprint ranks of the raw supervised
    # surface and the unsupervised GEMSDOE49-architecture surface.
    from gems70.method import rank01 as _r01f
    g49_grid = ortho_gate_score(slope, grav, rtp, fp, w=0.25)
    cand_oof_grid = np.sqrt(np.maximum(_r01f(to_grid(surf_oof), fp), 0) * np.maximum(_r01f(g49_grid, fp), 0)).astype(np.float32)
    cand_final_grid = np.sqrt(np.maximum(_r01f(to_grid(surf_final_vec), fp), 0) * np.maximum(_r01f(g49_grid, fp), 0)).astype(np.float32)
    np.save(CACHE / "candidate3_surface.npy", cand_final_grid)
    np.save(CACHE / "candidate3_oof_surface.npy", cand_oof_grid)
    np.save(CACHE / "candidate3_oof_raw.npy", to_grid(surf_oof))
    np.save(CACHE / "candidate3_oof_nc_raw.npy", to_grid(surf_oof_nc))
    np.save(CACHE / "candidate3_gated_oof.npy", gated_oof_grid)
    np.save(CACHE / "candidate3_g49.npy", g49_grid)
    del X, F, feat_grid, domains
    import gc as _gc; _gc.collect()

    print("[5/6] Comparator surfaces + dotted arms (one surface at a time)...", flush=True)
    from gems70.method import rank01 as _r01
    dist_vis = ndi.distance_transform_edt(~visible)
    arms_terms: dict[str, list] = {}
    fold_results: dict[str, list] = {}

    def eval_surface(name, surf):
        arms_terms[name] = []
        fold_results[name] = []
        for f in folds:
            region = f["region"]
            allowed = fp & region & (dist_vis > 2)
            budget = int(round(GLOBAL_BUDGET * float(region[fp].sum()) / float(fp.sum())))
            ranked, _ = emit.emit_decimated(np.where(fp, surf, 0).astype(np.float32), allowed)
            dots = emit.emit_prefix(ranked, budget)
            del ranked
            res, terms = cropped(f, dots.astype(np.float32), fp)
            del dots
            arms_terms[name].append(terms)
            fold_results[name].append(res)
        print(f"  arm {name} evaluated ({time.monotonic()-start:.0f}s)", flush=True)

    eval_surface("candidate", cand_oof_grid)
    eval_surface("RawHGB_NoGate", to_grid(surf_oof))
    eval_surface("Gated_H70_2A", gated_oof_grid)
    eval_surface("GEMS49_OrthoGate", g49_grid)
    eval_surface("SingleBand_ElevSlope", _r01(np.where(fp, slope, 0), fp))
    raw = {}
    for nm, arr in [("rtp", rtp), ("gravity", grav)]:
        a = arr.astype(np.float32).copy(); a[~fp] = np.nan; raw[nm] = a
    valid_e1 = ndi.binary_erosion(fp, iterations=12)
    feats_e1 = physical_features(raw["rtp"], raw["gravity"], np.where(fp, base_sm, np.nan), valid_e1)
    del raw
    eval_surface("GEMS70_E1_ContactTermination", joint_field(feats_e1, valid_e1))
    del feats_e1
    # random matched-budget control
    arms_terms["Random_Sparse_Control"] = []
    fold_results["Random_Sparse_Control"] = []
    for f in folds:
        region = f["region"]
        allowed = fp & region & (dist_vis > 2)
        budget = int(round(GLOBAL_BUDGET * float(region[fp].sum()) / float(fp.sum())))
        pool = np.flatnonzero(allowed.ravel())
        pick = rng.choice(pool, min(budget, len(pool)), replace=False)
        dots = np.zeros(fp.size, bool); dots[pick] = True
        res, terms = cropped(f, dots.reshape(fp.shape).astype(np.float32), fp)
        arms_terms["Random_Sparse_Control"].append(terms)
        fold_results["Random_Sparse_Control"].append(res)
    print(f"  arm Random_Sparse_Control evaluated ({time.monotonic()-start:.0f}s)", flush=True)

    terms = {n: sum(t) for n, t in arms_terms.items()}
    result = evaluate_holdout.pooled_summary(terms, draws=1000, seed=SEED, candidate="candidate")
    result["interpretation"] = "Dotted (emit_decimated/emit_prefix) HOLDOUT-DTI on untouched seed-702 holdout; not organizer-confirmed."
    result["experiment_id"] = "H70-3A"
    result["global_budget_dots"] = GLOBAL_BUDGET
    key = ["RawHGB_NoGate", "GEMS49_OrthoGate", "Gated_H70_2A", "Random_Sparse_Control"]
    result["promotion_allowed"] = bool(all(result["paired_differences"][k]["ci95"][0] > 0 for k in key))
    result["promotion_blocker"] = None if result["promotion_allowed"] else "Candidate did not beat every key comparator with paired 95% CI > 0."
    dump(E / "holdout3.json", result)
    dump(E / "holdout3_folds.json", fold_results)

    print("[6/6] Final dots (full-footprint, >2px off catalogue)...", flush=True)
    allowed_final = fp & (dist_cat > 2)
    ranked_final, _ = emit.emit_decimated(cand_final_grid.astype(np.float32), allowed_final)
    dots_final = emit.emit_prefix(ranked_final, GLOBAL_BUDGET)
    np.save(CACHE / "candidate3_dots.npy", dots_final)
    summary = {
        "experiment_id": "H70-3A", "seed": SEED, "elapsed_seconds": round(time.monotonic() - start, 1),
        "candidate_holdout_dti": result["scores"]["candidate"],
        "promotion_allowed_holdout": result["promotion_allowed"],
        "final_dots": int(dots_final.sum()),
        "surface_decoded_float32_sha256": hashlib.sha256(np.ascontiguousarray(cand_final_grid).tobytes()).hexdigest(),
        "dots_decoded_sha256": hashlib.sha256(np.ascontiguousarray(dots_final).tobytes()).hexdigest(),
        "features": FEATURES,
    }
    dump(E / "run3_summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
