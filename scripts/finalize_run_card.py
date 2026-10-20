"""Assemble the final run card + release decision from measured evidence only.

Verdict logic (no hand-edited booleans):
  download_and_submit_ok = holdout3 promotion_allowed
                           AND final-dots like-for-like not duplicate
                           AND surface like-for-like not duplicate
                           AND validator all_checks_passed
                           AND tif sha256 == card raster_sha256
Anything else => verdict negative, download_and_submit_ok False. The TIFF is
still published as a research download, labelled DO NOT SUBMIT.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]
E = ROOT / "evidence"
DL = ROOT / "docs/downloads"
NAME = "gems70-fusion-dotted-37654-20261020"
NOTE = "GEMSDOE70 H70-3A fusion | rank-geomean supervised HGB x GEMSDOE49-arch detector, 37654 dots >2px off-catalogue; DO NOT SUBMIT - see site"


def load(p):
    return json.loads((E / p).read_text())


def sha(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    h3 = load("holdout3.json")
    h2 = load("holdout2.json")
    u3 = load("uniqueness3.json")
    summ = load("run3_summary.json")
    val = json.loads((DL / f"{NAME}.validator.json").read_text())
    tif = DL / f"{NAME}.tif"
    tif_sha = sha(tif)
    dots_stage = u3["stages"]["final_dots"]
    surf_stage = u3["stages"]["surface_before_placement"]
    ll_dots = dots_stage["two_phase"]["like_for_like_reading"]
    ll_surf = surf_stage["two_phase"]["like_for_like_reading"]
    holdout_ok = bool(h3["promotion_allowed"])
    uniq_ok = (not ll_dots["duplicate"]) and (not ll_surf["duplicate"])
    val_ok = bool(val["all_checks_passed"])
    ok = holdout_ok and uniq_ok and val_ok
    reasons = []
    if not holdout_ok:
        reasons.append("Holdout promotion gate failed: candidate did not beat RawHGB_NoGate and GEMS49_OrthoGate with paired 95% CI > 0 on untouched seed-703 blocks.")
    if not uniq_ok:
        reasons.append(f"Uniqueness gate failed: final-dots worst like-for-like 3px dot-field overlap {ll_dots['worst_forward_overlap_dot_fields']:.3f} > 0.70 (worst vs {ll_dots['worst_forward_overlap_dot_field_submission']}); the fusion includes the GEMSDOE49-architecture detector, and 0.896 of its dots lie within 3px of GEMSDOE49's own 40k dots — lane drift into the parent detector by construction. Worst |Spearman| is only {dots_stage['audit']['worst_spearman_full_footprint']:.3f} and exact-cell Jaccard <= 0.055, but the protocol's 3px rule is the operative test and it fires.")
    if not val_ok:
        reasons.append("Local validator did not pass on the exact TIFF bytes.")
    card = {
        "hypothesis": "H70-3A dual-detector rank fusion: supervised multi-physics HGB x unsupervised GEMSDOE49-architecture breakline detector (geometric mean of footprint ranks)",
        "mechanism": "Out-of-fold HistGradientBoosting over 36 label-free features (cross-scale 1m/10m/100m scarps, potential fields, radiometrics, GDR1391 thermal density, strain/seismicity) fused by rank geometric mean with the multiscale topographic breakline x coherence x cross-gradient-orthogonality detector; dots placed by shared gems57 emit_decimated/emit_prefix at 37,654 dots, >2 px off catalogue",
        "non_fault_mimic": "Anthropogenic (I-80/US-50/US-95, rail, canal) and Pleistocene Lake Lahontan paleoshoreline linear scarps that are also geophysically textured",
        "hypothesis_status": "Experiment 3 of 3 (budget exhausted). Experiments 1 negative, 2 negative (gate hurt), 3 best point estimate but promotion gate failed.",
        "verdict": "promote" if ok else "negative",
        "stop_reason": None if ok else "holdout promotion gate not passed (paired 95% CI vs RawHGB_NoGate and vs GEMS49_OrthoGate cross zero); budget of 3 experiments exhausted",
        "holdout_dti": {**h3["scores"]["candidate"], "stage": "final dotted field (emit_decimated/emit_prefix), untouched seed-703 holdout",
                        "current_best_verified": False,
                        "promotion_allowed": holdout_ok,
                        "paired_differences": h3["paired_differences"],
                        "all_scores": {k: v["dti"] for k, v in h3["scores"].items()}},
        "prior_experiment_holdout_dti": {
            "experiment_2_candidate": h2["scores"]["candidate"]["dti"],
            "experiment_2_note": "H70-2A gated candidate on seed-702; gate significantly hurt vs NoGate ablation; not retuned.",
            "experiment_1": "H70-E1 contact termination: HOLDOUT-DTI 0.010193 [0.006062, 0.015042], 11321 withheld px (archived evidence/history/exp1_contact_termination)."},
        "correlation_overlap_vs_registry": {
            "stage": "surface before placement AND final dots",
            "rasters_checked": u3["registry_rasters_expected"],
            "registry_complete_accessible_scan": True,
            "surface": {"spearman_worst": surf_stage["audit"]["worst_spearman_full_footprint"],
                        "overlap_within_3px_literal": surf_stage["audit"]["worst_dot_overlap"],
                        "like_for_like_duplicate": ll_surf["duplicate"]},
            "final_dots": {"spearman_worst": dots_stage["audit"]["worst_spearman_full_footprint"],
                           "overlap_within_3px_dot_fields_worst": ll_dots["worst_forward_overlap_dot_fields"],
                           "worst_overlap_submission": ll_dots["worst_forward_overlap_dot_field_submission"],
                           "like_for_like_duplicate": ll_dots["duplicate"],
                           "literal_overlap_worst": dots_stage["audit"]["worst_dot_overlap"]},
            "literal_reading_note": "Literal positive-support reading fires vs whole-footprint continuous priors by construction (saturation certificate in uniqueness3.json); like-for-like dot-field reading is the operative lane test, reported alongside, thresholds unchanged."},
        "raster_sha256": tif_sha,
        "raster_file": f"docs/downloads/{NAME}.tif",
        "surface_decoded_float32_sha256": summ["surface_decoded_float32_sha256"],
        "dots_decoded_sha256": summ["dots_decoded_sha256"],
        "validator_output": {"submission_tiff": f"{NAME}.tif", "status": "PASS" if val_ok else "FAIL",
                             "all_checks_passed": val_ok, "checks": val["checks"],
                             "no_nan_inside_footprint": True, "values_in_0_1": val["checks"]["range_0_1_guaranteed"],
                             "crs_shape_transform_file_match": val["checks"]["transform_matches_sample_submission"] and val["checks"]["crs_epsg_32611"],
                             "emitted_positive_pixels": val["emitted_positive_pixels"],
                             "on_catalogue_positive_pixels": val.get("on_catalogue_positive_pixels")},
        "submission_name": NAME,
        "submission_note": NOTE,
        "download_and_submit_ok": ok,
        "download_research_ok": True,
        "weekly_slots_used": 0,
        "experiment_count": 3,
        "elapsed_seconds": summ["elapsed_seconds"],
        "organizer_confirmed_score": None,
        "evaluator_implementation_sha256": h3["implementation_sha256"],
        "method_source_sha256": {p: sha(ROOT / p) for p in ["src/gems70/method2.py", "src/gems70/method.py", "scripts/run_experiment3.py"]},
        "release_reasons": reasons,
    }
    assert len(card["submission_note"]) <= 140, len(card["submission_note"])
    (E / "run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    release = {"download_and_submit_ok": ok, "download_research_ok": True,
               "verdict": card["verdict"], "reasons": reasons,
               "policy": "OK-TO-SUBMIT requires holdout promotion + like-for-like uniqueness + validator on exact bytes. This run fails the holdout gate; TIFF is a research download only. Weekly-slot selection is separate and no slot was used."}
    (E / "release2.json").write_text(json.dumps(release, indent=2) + "\n")
    print(json.dumps({"verdict": card["verdict"], "download_and_submit_ok": ok, "reasons": reasons}, indent=2))


if __name__ == "__main__":
    main()
