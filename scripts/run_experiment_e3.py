"""E3 contingent preregistered experiment: magnetic source-depth step.

Spec: docs/preregistration-e2.md E3 section (identical machinery to E2; only
the ranking differs). Stricter addition, disclosed here: D28 and H19-solid
reference arms are included alongside H33 so promotion bar (a) cannot pass
against an incomplete reference set. Writes evidence/e3/*; refuses reruns.
"""
from __future__ import annotations

import datetime as dt
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
from run_experiment_e2 import REGISTRY_FILES, REF_ARMS, cropped, dump, read_ref

E = ROOT / "evidence" / "e3"
CACHE = ROOT / ".cache"
REG = CACHE / "registry_e2"
BUDGET_S = 7200


def main():
    start = time.monotonic()
    manifest = E / "experiment_manifest.json"
    if manifest.exists():
        raise RuntimeError("E3 already attempted. Inspect evidence/e3; no silent reruns/tuning.")
    E.mkdir(parents=True, exist_ok=True)
    dump(manifest, {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment": "E3-depth-step", "experiment_count_this_session": 2,
        "maximum_experiments": 3, "maximum_seconds": BUDGET_S,
        "contingency": "E2 completed, no canary stop, verdict negative (evidence/e2/run_card.json)",
        "preregistration_sha256": sha(ROOT / "docs/preregistration-e2.md"),
        "protocol_revision_sha256": sha(ROOT / "docs/protocol-revision-uniqueness.md"),
        "source_sha256": {p: sha(ROOT / p) for p in
                          ["src/gems70/method2.py", "src/gems70/method.py",
                           "scripts/run_experiment_e3.py", "scripts/run_experiment_e2.py"]},
    })
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError("input pin mismatch: " + name)
    for name, prefix in REGISTRY_FILES.items():
        if not sha(REG / name).startswith(prefix):
            raise ValueError(f"registry pin mismatch: {name}")

    grid = load_grid(DATA)
    fp = grid.footprint
    raw = {}
    with rasterio.open(DATA / "training_features.tif") as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError("feature grid mismatch")
        for index, name in [(2, "rtp"), (15, "basement")]:
            a = src.read(index).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            raw[name] = a
    valid0 = fp.copy()
    for a in raw.values():
        valid0 &= np.isfinite(a)
    # NOTE: E2 valid0 also required det_elev/det_elev_slope finite. Recompute the
    # E2-identical valid mask by intersecting all four bands for comparability.
    with rasterio.open(DATA / "training_features.tif") as src:
        for index in (12, 19):
            a = src.read(index).astype(np.float32)
            valid0 &= np.isfinite(a) & (np.abs(a) < 1e18) & fp
    valid = ndi.binary_erosion(valid0, iterations=12)
    print("valid(eroded)", int(valid.sum()), flush=True)

    rtp_f = method2.fill_nearest_from(raw["rtp"], valid0)
    base_f = method2.fill_nearest_from(raw["basement"], valid0)
    axis_index, coherence = method2.structure_tensor_normal(rtp_f)
    didx = method2.depth_index(rtp_f)
    depth_step, depth_step_max = method2.oriented_step(didx, axis_index)
    basement_edge = method2.gradient_magnitude(base_f, 2.0)
    features = {
        "depth_index": np.where(valid, didx, 0).astype(np.float32),
        "depth_step": np.where(valid, depth_step, 0).astype(np.float32),
        "depth_step_max": np.where(valid, depth_step_max, 0).astype(np.float32),
        "basement_edge": np.where(valid, basement_edge, 0).astype(np.float32),
    }
    print("features computed", flush=True)

    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
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
        raise RuntimeError("LEAKAGE CANARY STOP: feature-alone AUC > .90")

    candidate_rank = method2.joint_rank(features, valid, ("depth_step", "basement_edge"))
    np.save(CACHE / "e3_candidate_rank.npy", candidate_rank)

    def dots_for(rank_field, allowed):
        mask, n = method2.priority_thin(rank_field, allowed)
        return mask.astype(np.float32), n

    arms, arm_dots = {}, {}
    cand_dots, n_cand = dots_for(candidate_rank, valid)
    arms["candidate_dots"] = cand_dots; arm_dots["candidate_dots"] = n_cand
    arms["candidate_surface"] = upper_surface(candidate_rank, valid)
    for fname in ("depth_step", "basement_edge"):
        d, n = dots_for(rank01(features[fname], valid), valid)
        arms[f"{fname}_dots"] = d; arm_dots[f"{fname}_dots"] = n
        print("thinned", fname, n, flush=True)
    random_dots = np.zeros(fp.shape, np.float32)
    ids = rng.choice(np.flatnonzero(valid), method2.TARGET_DOTS, replace=False)
    random_dots.ravel()[ids] = 1.0
    arms["random_dots"] = random_dots; arm_dots["random_dots"] = method2.TARGET_DOTS
    for arm, fname in REF_ARMS.items():
        a = read_ref(fname)
        arms[arm] = a; arm_dots[arm] = int((a > 0).sum())

    terms, fold_results = {}, {}
    for name, a in arms.items():
        if time.monotonic() - start > BUDGET_S:
            raise TimeoutError("two-hour experiment budget exhausted")
        per_fold = [cropped(f, a, valid) for f in folds]
        terms[name] = sum(t for _, t in per_fold)
        fold_results[name] = [r for r, _ in per_fold]
        print(name, "evaluated", flush=True)
    result = evaluate_holdout.pooled_summary(terms, draws=1000, seed=70020, candidate="candidate_dots")
    result["arm_dot_counts"] = arm_dots
    result["interpretation"] = ("Binary-dot HOLDOUT-DTI (E3 depth-step) on withheld catalogue "
                                "components; not organizer-confirmed.")
    result["reference_caveat"] = ("H33/D28/H19 fields were built with full-catalogue knowledge; "
                                  "reference measurements on this instrument.")
    dump(E / "holdout.json", result)
    dump(E / "holdout_folds.json", fold_results)

    dist_cat = ndi.distance_transform_edt(~grid.catalogue)
    allowed_final = valid & (dist_cat > 2)
    final_dots, n_final = dots_for(candidate_rank, allowed_final)
    np.save(CACHE / "e3_final_dots.npy", final_dots)
    print("final dots", n_final, flush=True)

    def audit_array(arr, label):
        idx = {"complete_accessible_scan": False,
               "errors": ["Disclosed subset audit only (7 rasters); not a complete registry scan."],
               "rasters": [{"repo_first": "subset", "sources": [f"subset:{f}"],
                            "cache_file": str((REG / f).resolve()), "sha256": sha(REG / f)}
                           for f in REGISTRY_FILES]}
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
            support = method2.topn_mask(theirs, fp, n_mine) if dense else None
            r1 = uniqueness.dot_overlap(my_dots.astype(np.float32),
                                        (support.astype(np.float32) if dense else theirs))
            r1_rows.append({"file": fname, "positive_fraction_footprint": frac,
                            "dense_by_R1": bool(dense), "r1_overlap_within_3px": float(r1)})
        return {"stage": label, "template_literal_audit": audit, "r1_rows": r1_rows,
                "r1_worst_overlap": max(r["r1_overlap_within_3px"] for r in r1_rows),
                "scope": "7-raster disclosed subset; complete scan remains a selector prerequisite."}

    surface = arms["candidate_surface"].copy()
    surface[grid.catalogue] = 0
    surface_audit = audit_array(surface, "surface_upper2pct_before_placement")
    dump(E / "surface_uniqueness.json", surface_audit)
    final_audit = audit_array(final_dots, "final_dots")
    dump(E / "final_uniqueness.json", final_audit)
    print("audits done", flush=True)

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
        "hypothesis": "Magnetic source-depth step at a basement edge (E3)",
        "mechanism": "Cross-edge step of multi-scale depth index A3/(A1+eps) along RTP tensor normal, rank-fused with basement edge; 2.8px priority-thinned binary dots",
        "non_fault_mimic": "Intrusive contact with depth change or remanence boundary",
        "hypothesis_status": "Contingent preregistered lane; docs/preregistration-e2.md E3 section",
        "verdict": "pending-writer" if science_pass else "negative",
        "promotion_bars": bars, "best_other_arm": best_other,
        "holdout_dti": {**scores["candidate_dots"], "stage": "binary holdout dots (no catalogue exclusion), seed-20 primary",
                        "current_best_verified": bool(bars["a_point_beats_every_arm"] and bars["b_ci_vs_h33_above_0"])},
        "holdout_all_arms": scores, "paired_vs_h33": d_h33, "paired_vs_random": d_rand,
        "correlation_overlap_vs_registry": {
            "stage": "surface + final dots, 7-raster disclosed subset (R1)",
            "surface_worst_spearman": surface_audit["template_literal_audit"]["worst_spearman_full_footprint"],
            "surface_literal_worst_overlap": surface_audit["template_literal_audit"]["worst_dot_overlap"],
            "surface_r1_worst_overlap": surface_audit["r1_worst_overlap"],
            "final_worst_spearman": final_audit["template_literal_audit"]["worst_spearman_full_footprint"],
            "final_literal_worst_overlap": final_audit["template_literal_audit"]["worst_dot_overlap"],
            "final_r1_worst_overlap": final_audit["r1_worst_overlap"],
            "registry_complete": False,
        },
        "raster_sha256": None, "validator_output": {"status": "NOT_WRITTEN"},
        "submission_name": "GEMSDOE70-E3-depth-step-38000",
        "submission_note": "E3 magnetic depth-step x basement edge, 38k dots d>2px; HOLDOUT-DTI in run card; selector scan pending",
        "download_and_submit_ok": False, "weekly_slots_used": 0,
        "experiment_count": 2, "elapsed_seconds": round(time.monotonic() - start, 2),
        "organizer_confirmed_score": None,
        "evaluator_implementation_sha256": evaluate_holdout.implementation_hashes(),
        "method_source_sha256": {p: sha(ROOT / p) for p in
                                 ["src/gems70/method2.py", "src/gems70/method.py",
                                  "scripts/run_experiment_e3.py"]},
        "final_dot_count": int(n_final), "holdout_dot_count": int(n_cand),
    }
    assert len(card["submission_note"]) <= 140 and len(card["submission_name"]) <= 140
    if science_pass:
        from gems57.submission_writer import write_submission
        from gems57.validate import validate
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = ROOT / "docs" / "downloads" / f"gems70-e3-depthstep-38000-{stamp}-zeros.tif"
        pred = np.where(fp, final_dots, 0).astype(np.float32)
        pred[grid.catalogue] = 0
        receipt = write_submission(out, pred, DATA / "sample_submission.tif", fp,
                                   note=card["submission_note"], name=card["submission_name"],
                                   catalogue=grid.catalogue,
                                   metadata={"experiment": "E3", "holdout_dti": cand_dti})
        v = validate(out, fp, grid.catalogue)
        dump(E / "validator.json", {"writer_receipt": receipt, "validate": v})
        card["verdict"] = "promote" if v["all_checks_passed"] else "negative"
        card["raster_sha256"] = receipt["sha256"]
        card["raster_file"] = out.name
        card["validator_output"] = {"status": "PASS" if v["all_checks_passed"] else "FAIL",
                                    "checks": v["checks"], "min": v["min"], "max": v["max"],
                                    "emitted_positive_pixels": v["emitted_positive_pixels"]}
        card["download_ok_for_selector_review"] = bool(v["all_checks_passed"])
        card["submit_ok"] = False
        card["submit_blocker"] = "Separate selector step + complete registry scan + R1 acknowledgment required (protocol rule 6)."
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
                      "h33_dti": scores["h33_ref"]["dti"], "d28_dti": scores["d28_ref"]["dti"],
                      "random_dti": scores["random_dots"]["dti"], "bars": bars}, indent=2), flush=True)


if __name__ == "__main__":
    main()
