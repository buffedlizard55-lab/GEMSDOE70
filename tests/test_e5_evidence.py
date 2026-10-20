"""Saved E5 arithmetic and receipt binding (no experiment rerun)."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
E5 = ROOT / "evidence" / "e5"


def _load(name):
    return json.loads((E5 / name).read_text())


def test_e5_saved_scores_recompute_from_folds():
    for summ_name, folds_name in (
            ("instrumentA_holdout.json", "instrumentA_folds.json"),
            ("instrumentB_prime.json", "instrumentB_prime_folds.json")):
        summary = _load(summ_name)
        folds = _load(folds_name)
        for arm, rows in folds.items():
            s = summary["scores"][arm]
            tp = sum(r["tp"] for r in rows)
            fp = sum(r["fp"] for r in rows)
            fn = sum(r["fn"] for r in rows)
            assert s["dti"] == pytest.approx(tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12),
                                             abs=1e-9)
            assert 0 <= s["ci95"][0] <= s["dti"] <= s["ci95"][1] <= 1
        assert summary["evaluator_version"] == "gems57-pooled-hide-v2"


def test_e5_gates_and_verdict_are_consistent():
    card = _load("run_card.json")
    db = card["paired_b_prime_vs_h33"]
    gate_b = db["delta"] > 0 and db["ci95"][0] > 0
    assert card["gate_b_prime_candidate_gt_h33_significant"] is gate_b
    # Frozen P4 gates: promote requires B' win with CI excluding zero.
    assert card["verdict"] == ("promote" if gate_b and card["gate_a_candidate_ge_h33"]
                               else "negative")
    assert card["submit_recommended"] is (card["verdict"] == "promote")
    assert card["weekly_slots_used"] == 0
    assert card["organizer_confirmed_score"] is None
    assert len(card["submission_note"]) <= 140
    assert card["canary_worst_single_feature_auc"] <= 0.90


def test_e5_artifact_binds_exact_bytes_and_validator():
    card = _load("run_card.json")
    path = ROOT / "docs/downloads" / (card["submission_name"] + ".tif")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == card["raster_sha256"]
    val = card["validator_output"]
    assert val["sha256"] == digest and val["all_checks_passed"] is True
    assert val["min"] == 0.0 and val["max"] == 1.0
    assert val["n_nan"] == 0 and val["n_infinite"] == 0
    assert val["emitted_positive_pixels"] == 37654
    assert val["on_catalogue_positive_pixels"] == 0
    assert all(val["checks"].values())


def test_e5_uniqueness_surface_and_dots():
    surf = _load("surface_uniqueness.json")
    assert surf["duplicate_count"] == 0
    assert surf["worst_spearman_full_footprint"] <= 0.90
    fin = _load("uniqueness.json")
    assert fin["registry_rasters_checked"] == 62
    assert fin["duplicate_count"] == 0 and fin["unique"] is True
    assert fin["worst_dot_overlap"] <= 0.70  # mutual overlap gate
    assert fin["worst_spearman_full_footprint"] <= 0.90


def test_e5_canaries_below_leakage_threshold():
    can = _load("canaries.json")
    assert len(can["features"]) == 25
    for feat, vals in can["features"].items():
        for key, v in vals.items():
            if v is None:
                continue
            if feat in ("d_cat", "log1p_d_cat") and key == "auc_instrument_a":
                # Definitional artifact: A positives ARE catalogue pixels, so
                # full-catalogue distance is 0 for every positive (AUC 0.0).
                # The prediction-time feature is visible-only distance; its
                # corrected canary is bound in canaries_correction.json.
                assert v == 0.0
                continue
            assert max(v, 1 - v) <= 0.90, (feat, key, v)
    corr = _load("canaries_correction.json")
    assert max(corr["auc_instrument_a_d_visible"],
               1 - corr["auc_instrument_a_d_visible"]) <= 0.90
    assert corr["withheld_positive_pixels"] == 11321
