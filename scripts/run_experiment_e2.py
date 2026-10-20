"""E2 preregistered experiment: subsurface-strike-guided alluvial step.

Spec: docs/preregistration-e2.md (hashed into the manifest before scoring).
Uniqueness: docs/protocol-revision-uniqueness.md (R1) + literal template numbers.
E1 evidence at evidence/*.json is never overwritten; E2 writes evidence/e2/*.
Refuses to rerun if its manifest exists (no silent tuning on these folds).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid
from gems70.method import rank01, upper_surface
from gems70 import method2
from restore_data import DATA, PINS, sha

E = ROOT / "evidence" / "e2"
CACHE = ROOT / ".cache"
REG = CACHE / "registry_e2"
BUDGET_S = 7200
# Registry subset (file -> expected sha256). Dense witness + H33 lineage + scorers.
REGISTRY_FILES = {
    "h33_b2.tif": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "d28.tif": "3e78737f0da8dd2ca66cc6caac0ce8eeefcd6715707f8d1bd3091845cd9bcc30",
    "h27.tif": "2fc94a38d77f74d4f4ed1a97a83e7bb71a1ceea090515ec641e6681cc47c44c8",
    "h19solid.tif": "ef2ae808eb717986",
    "anderson.tif": "e15891020b9c5705",
    "gateortho.tif": "3722e26fbf912987",
    "dense17.tif": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
}
REF_ARMS = {"h33_ref": "h33_b2.tif", "d28_ref": "d28.tif", "h19solid_ref": "h19solid.tif"}


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def cropped(fold, p, valid):
    y, x = np.nonzero(fold["region"])
    y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
    y1, x1 = min(p.shape[0], int(y.max()) + 7), min(p.shape[1], int(x.max()) + 7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k: v[sl] for k, v in fold.items() if isinstance(v, np.ndarray) and v.shape == p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0, x0), global_shape=p.shape)


def read_ref(name):
    p = REG / name
    with rasterio.open(p) as src:
        a = src.read(1).astype(np.float32)
    return a


def main():
    start = time.monotonic()
    manifest = E / "experiment_manifest.json"
    if manifest.exists():
        raise RuntimeError("E2 already attempted. Inspect evidence/e2; no silent reruns/tuning.")
    E.mkdir(parents=True, exist_ok=True)
    dump(manifest, {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment": "E2-alluvial-step", "experiment_count_this_session": 1,
        "maximum_experiments": 3, "maximum_seconds": BUDGET_S,
        "preregistration_sha256": sha(ROOT / "docs/preregistration-e2.md"),
        "protocol_revision_sha256": sha(ROOT / "docs/protocol-revision-uniqueness.md"),
        "source_sha256": {p: sha(ROOT / p) for p in
                          ["src/gems70/method2.py", "src/gems70/method.py",
                           "scripts/run_experiment_e2.py"]},
    })

    def budget():
        if time.monotonic() - start > BUDGET_S:
            raise TimeoutError("two-hour experiment budget exhausted")

    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError("input pin mismatch: " + name)
    for name, prefix in REGISTRY_FILES.items():
        h = sha(REG / name)
        if not h.startswith(prefix):
            raise ValueError(f"registry pin mismatch: {name} {h} !~ {prefix}")

    grid = load_grid(DATA)
    fp = grid.footprint
    print("grid loaded", grid.shape, "footprint", int(fp.sum()), flush=True)

    raw = {}
    with rasterio.open(DATA / "training_features.tif") as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError("feature grid mismatch")
        for index, name in [(12, "det_elev"), (2, "rtp"), (15, "basement"), (19, "det_elev_slope")]:
            a = src.read(index).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            raw[name] = a
    valid0 = fp.copy()
    for a in raw.values():
        valid0 &= np.isfinite(a)
    valid = ndi.binary_erosion(valid0, iterations=12)
    if not valid.any():
        raise ValueError("no valid interior features")
    print("valid0", int(valid0.sum()), "valid(eroded)", int(valid.sum()), flush=True)

    elev_f = method2.fill_nearest_from(raw["det_elev"], valid0)
    rtp_f = method2.fill_nearest_from(raw["rtp"], valid0)
    base_f = method2.fill_nearest_from(raw["basement"], valid0)
    elev_s = ndi.gaussian_filter(elev_f.astype(np.float64), 1.0)
    axis_index, coherence = method2.structure_tensor_normal(rtp_f)
    step_oriented, step_max = method2.oriented_step(elev_s, axis_index)
    basement_edge = method2.gradient_magnitude(base_f, 2.0)
    features = {
        "step_oriented": np.where(valid, step_oriented, 0).astype(np.float32),
        "step_max": np.where(valid, step_max, 0).astype(np.float32),
        "coherence": np.where(valid, coherence, 0).astype(np.float32),
        "basement_edge": np.where(valid, basement_edge, 0).astype(np.float32),
    }
    print("features computed", flush=True)

    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    dump(E / "holdout_split.json", {
        "evidence_class": "HOLDOUT-DTI", "evaluator_version": evaluate_holdout.VERSION,
        "receipts": [f["receipt"] for f in folds],
        "total_withheld_positive_pixels": int(sum((f["truth"] & valid).sum() for f in folds)),
        "catalogue_predictors": [], "valid_feature_pixels": int(valid.sum()),
        "known_mask_rule": "catalogue minus globally withheld components, pixel exact",
        "limitation": "Mapped components are a surrogate for previously unmapped faults; no hidden organizer labels.",
    })

    truth = np.zeros(fp.shape, bool)
    active = np.zeros(fp.shape, bool)
    for fold in folds:
        active |= valid & fold["region"] & ~fold["masked_known"]
        truth |= valid & fold["truth"]
    positives = np.flatnonzero(truth)
    negatives = np.flatnonzero(active & ~truth)
    rng = np.random.default_rng(70020)
    negatives = rng.choice(negatives, min(200000, len(negatives)), replace=False)
    labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]
    canaries = {}
    for name, a in {**raw, **features}.items():
        values = np.r_[a.ravel()[positives], a.ravel()[negatives]]
        if not np.isfinite(values).all():
            raise ValueError(f"canary {name}: non-finite values on evaluation domain")
        auc = float(roc_auc_score(labels, values))
        canaries[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc, "inverse_auc": 1 - auc,
                          "withheld_positive_pixels": int(len(positives)),
                          "negative_sample_pixels": int(len(negatives)),
                          "suspected_leakage": bool(max(auc, 1 - auc) > 0.90)}
        print("canary", name, round(auc, 4), flush=True)
    dump(E / "canaries.json", canaries)
    if any(c["suspected_leakage"] for c in canaries.values()):
        raise RuntimeError("LEAKAGE CANARY STOP: feature-alone AUC > .90; no joint interpretation permitted")

    candidate_rank = method2.joint_rank(features, valid, ("step_oriented", "basement_edge"))
    np.save(CACHE / "e2_candidate_rank.npy", candidate_rank)

    def dots_for(rank_field, allowed):
        mask, n = method2.priority_thin(rank_field, allowed)
        return mask.astype(np.float32), n

    arms, arm_dots = {}, {}
    cand_dots, n_cand = dots_for(candidate_rank, valid)
    arms["candidate_dots"] = cand_dots; arm_dots["candidate_dots"] = n_cand
    arms["candidate_surface"] = upper_surface(candidate_rank, valid)
    for fname in ("step_oriented", "step_max", "basement_edge"):
        r = rank01(features[fname], valid)
        d, n = dots_for(r, valid)
        arms[f"{fname}_dots"] = d; arm_dots[f"{fname}_dots"] = n
        print("thinned", fname, n, flush=True)
    random_dots = np.zeros(fp.shape, np.float32)
    ids = rng.choice(np.flatnonzero(valid), method2.TARGET_DOTS, replace=False)
    random_dots.ravel()[ids] = 1.0
    arms["random_dots"] = random_dots; arm_dots["random_dots"] = method2.TARGET_DOTS
    for arm, fname in REF_ARMS.items():
        a = read_ref(fname)
        if a.shape != fp.shape or not np.isfinite(a).all() or (a < 0).any() or (a > 1).any():
            raise ValueError(f"reference {fname}: not finite [0,1] on grid")
        arms[arm] = a; arm_dots[arm] = int((a > 0).sum())
    print("arms built", arm_dots, flush=True)

    terms, fold_results = {}, {}
    for name, a in arms.items():
        budget()
        per_fold = [cropped(f, a, valid) for f in folds]
        terms[name] = sum(t for _, t in per_fold)
        fold_results[name] = [r for r, _ in per_fold]
        print(name, "evaluated", flush=True)
    result = evaluate_holdout.pooled_summary(terms, draws=1000, seed=70020, candidate="candidate_dots")
    result["arm_dot_counts"] = arm_dots
    result["interpretation"] = ("Binary-dot HOLDOUT-DTI (candidate_dots primary) on withheld catalogue "
                                "components; not final submission dots, not organizer-confirmed.")
    result["reference_caveat"] = ("H33/D28/H19 fields were built with full-catalogue knowledge; "
                                  "reference measurements on this instrument, not clean generalization.")
    dump(E / "holdout.json", result)
    dump(E / "holdout_folds.json", fold_results)

    # Confirmatory untouched draw (candidate dots + H33 only; never tuned on).
    folds21, _ = holdout.buffered_component_draw(grid, seed=21, buffer_px=3, boundary_px=12)
    terms21 = {}
    for name in ("candidate_dots", "h33_ref"):
        per_fold = [cropped(f, arms[name], valid) for f in folds21]
        terms21[name] = sum(t for _, t in per_fold)
    confirm = evaluate_holdout.pooled_summary(terms21, draws=1000, seed=70021, candidate="candidate_dots")
    dump(E / "holdout_confirm_seed21.json", confirm)
    print("confirmatory seed21 done", flush=True)

    # Final submission dots: full-catalogue distance > 2 px hygiene, refilled to budget.
    dist_cat = ndi.distance_transform_edt(~grid.catalogue)
    allowed_final = valid & (dist_cat > 2)
    final_dots, n_final = dots_for(candidate_rank, allowed_final)
    print("final dots", n_final, flush=True)
    np.save(CACHE / "e2_final_dots.npy", final_dots)

    # Uniqueness subset audit (literal template rows + R1 clarified overlaps).
    def audit_array(arr, label):
        idx = {"complete_accessible_scan": False,
               "errors": ["Disclosed subset audit only (7 rasters); not a complete registry scan."],
               "rasters": []}
        for fname in REGISTRY_FILES:
            idx["rasters"].append({
                "repo_first": "subset", "sources": [f"subset:{fname}"],
                "cache_file": str((REG / fname).resolve()), "sha256": sha(REG / fname)})
        audit = uniqueness.compare_array_to_registry(
            arr, idx, fp, include_reverse=False,
            expected_grid=(grid.shape, grid.crs, grid.transform))
        my_dots = (np.asarray(arr) > 0) & fp
        n_mine = int(my_dots.sum())
        r1_rows = []
        for fname in REGISTRY_FILES:
            theirs = read_ref(fname)
            pos = np.isfinite(theirs) & (theirs > 0) & fp
            frac = float(pos.sum() / fp.sum())
            dense = frac > 0.10
            if dense:
                support = method2.topn_mask(theirs, fp, n_mine)
                r1_overlap = uniqueness.dot_overlap(my_dots.astype(np.float32),
                                                    support.astype(np.float32))
            else:
                r1_overlap = uniqueness.dot_overlap(my_dots.astype(np.float32), theirs)
            r1_rows.append({"file": fname, "positive_fraction_footprint": frac,
                            "dense_by_R1": bool(dense), "r1_overlap_within_3px": float(r1_overlap)})
        return {"stage": label, "template_literal_audit": audit, "r1_rows": r1_rows,
                "r1_worst_overlap": max(r["r1_overlap_within_3px"] for r in r1_rows),
                "scope": "7-raster disclosed subset; complete 862-raster scan remains a selector prerequisite."}

    surface = arms["candidate_surface"].copy()
    surface[grid.catalogue] = 0
    surface_audit = audit_array(surface, "surface_upper2pct_before_placement")
    dump(E / "surface_uniqueness.json", surface_audit)
    print("surface audit done", flush=True)
    final_audit = audit_array(final_dots, "final_dots")
    dump(E / "final_uniqueness.json", final_audit)
    print("final audit done", flush=True)

    scores = result["scores"]
    cand_dti = scores["candidate_dots"]["dti"]
    best_other = max((n for n in scores if n != "candidate_dots"), key=lambda n: scores[n]["dti"])
    d_h33 = result["paired_differences"]["h33_ref"]
    d_rand = result["paired_differences"]["random_dots"]
    def rho_ok(audit):
        rows = [r for r in audit["template_literal_audit"]["rows"] if "error" not in r]
        return all((r.get("spearman_full_footprint") is None or
                    r["spearman_full_footprint"] <= uniqueness.RHO_LIMIT) for r in rows)
    bars = {
        "a_point_beats_every_arm": bool(all(cand_dti > scores[n]["dti"] for n in scores if n != "candidate_dots")),
        "b_ci_vs_h33_above_0": bool(d_h33["ci95"][0] > 0),
        "b_ci_vs_random_above_0": bool(d_rand["ci95"][0] > 0),
        "c_no_canary_alarm": bool(not any(c["suspected_leakage"] for c in canaries.values())),
        "d_surface_rho_ok_subset": bool(rho_ok(surface_audit)),
        "d_surface_r1_overlap_ok_subset": bool(surface_audit["r1_worst_overlap"] <= 0.70),
        "d_final_rho_ok_subset": bool(rho_ok(final_audit)),
        "d_final_r1_overlap_ok_subset": bool(final_audit["r1_worst_overlap"] <= 0.70),
    }
    science_pass = all(bars.values())
    print("bars", bars, "best_other", best_other, flush=True)

    card = {
        "hypothesis": "Subsurface-strike-guided alluvial step (E2)",
        "mechanism": "Oriented detrended-elevation mean-shift across RTP tensor normal, rank-fused with basement edge; 2.8px priority-thinned binary dots",
        "non_fault_mimic": "Terrace riser, paleoshoreline, or road grade",
        "hypothesis_status": "Declared lane: method paragraph absent from supplied prompt; preregistered docs/preregistration-e2.md",
        "verdict": "pending-writer" if science_pass else "negative",
        "promotion_bars": bars, "best_other_arm": best_other,
        "holdout_dti": {**scores["candidate_dots"], "stage": "binary holdout dots (no catalogue exclusion), seed-20 primary",
                        "current_best_verified": bool(bars["a_point_beats_every_arm"] and bars["b_ci_vs_h33_above_0"])},
        "holdout_all_arms": scores, "paired_vs_h33": d_h33, "paired_vs_random": d_rand,
        "confirmatory_seed21": {"candidate_dots": confirm["scores"]["candidate_dots"],
                                "h33_ref": confirm["scores"]["h33_ref"],
                                "paired_vs_h33": confirm["paired_differences"]["h33_ref"]},
        "correlation_overlap_vs_registry": {
            "stage": "surface + final dots, 7-raster disclosed subset (R1)",
            "surface_worst_spearman": surface_audit["template_literal_audit"]["worst_spearman_full_footprint"],
            "surface_literal_worst_overlap": surface_audit["template_literal_audit"]["worst_dot_overlap"],
            "surface_r1_worst_overlap": surface_audit["r1_worst_overlap"],
            "final_worst_spearman": final_audit["template_literal_audit"]["worst_spearman_full_footprint"],
            "final_literal_worst_overlap": final_audit["template_literal_audit"]["worst_dot_overlap"],
            "final_r1_worst_overlap": final_audit["r1_worst_overlap"],
            "registry_complete": False,
            "literal_dense_overlap_degenerate": "Dense witness positive on whole footprint; see protocol revision R1. Literal values published in audits, not hidden.",
        },
        "raster_sha256": None, "validator_output": {"status": "NOT_WRITTEN"},
        "submission_name": "GEMSDOE70-E2-alluvial-step-38000",
        "submission_note": "E2 oriented elev step x basement edge, 38k dots d>2px; HOLDOUT-DTI in run card; selector scan pending",
        "download_and_submit_ok": False, "weekly_slots_used": 0,
        "experiment_count": 1, "elapsed_seconds": round(time.monotonic() - start, 2),
        "organizer_confirmed_score": None,
        "evaluator_implementation_sha256": evaluate_holdout.implementation_hashes(),
        "method_source_sha256": {p: sha(ROOT / p) for p in
                                 ["src/gems70/method2.py", "src/gems70/method.py",
                                  "scripts/run_experiment_e2.py"]},
        "final_dot_count": int(n_final), "holdout_dot_count": int(n_cand),
    }
    assert len(card["submission_note"]) <= 140 and len(card["submission_name"]) <= 140

    if science_pass:
        from gems57.submission_writer import write_submission
        from gems57.validate import validate
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = ROOT / "docs" / "downloads" / f"gems70-e2-alluvialstep-38000-{stamp}-zeros.tif"
        pred = np.where(fp, final_dots, 0).astype(np.float32)
        pred[grid.catalogue] = 0
        receipt = write_submission(out, pred, DATA / "sample_submission.tif", fp,
                                   note=card["submission_note"], name=card["submission_name"],
                                   catalogue=grid.catalogue,
                                   metadata={"experiment": "E2", "holdout_dti": cand_dti})
        v = validate(out, fp, grid.catalogue)
        dump(E / "validator.json", {"writer_receipt": receipt, "validate": v})
        card["verdict"] = "promote"
        card["raster_sha256"] = receipt["sha256"]
        card["raster_file"] = out.name
        card["validator_output"] = {"status": "PASS" if v["all_checks_passed"] else "FAIL",
                                    "checks": v["checks"], "min": v["min"], "max": v["max"],
                                    "emitted_positive_pixels": v["emitted_positive_pixels"]}
        card["download_ok_for_selector_review"] = True
        card["submit_ok"] = False
        card["submit_blocker"] = "Separate selector step + complete registry scan + R1 acknowledgment required (protocol rule 6)."
        if not v["all_checks_passed"]:
            card["verdict"] = "negative"
    else:
        card["raster_sha256_reason"] = "Promotion bars failed; no submission TIFF written or published."
        card["validator_output"] = {
            "status": "NOT_WRITTEN",
            "pre_export_array_checks": {
                "no_nan_inside_footprint": bool(np.isfinite(final_dots[fp]).all()),
                "values_in_0_1": bool((final_dots >= 0).all() and (final_dots <= 1).all()),
                "shape_matches": final_dots.shape == grid.shape,
                "zero_on_catalogue": not bool(final_dots[grid.catalogue].any()),
            },
            "reason": "Array checks are not a TIFF validator receipt; export stopped by promotion bars.",
        }
    card["elapsed_seconds"] = round(time.monotonic() - start, 2)
    dump(E / "run_card.json", card)
    print(json.dumps({"verdict": card["verdict"], "candidate_dti": cand_dti,
                      "h33_dti": scores["h33_ref"]["dti"], "random_dti": scores["random_dots"]["dti"],
                      "bars": bars}, indent=2), flush=True)


if __name__ == "__main__":
    main()
