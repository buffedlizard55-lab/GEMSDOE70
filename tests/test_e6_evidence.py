"""Saved E6 arithmetic, scientific gates, uniqueness, buffer audit, and receipt bindings."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
E6 = ROOT / "evidence" / "e6"


def _load(name: str):
    return json.loads((E6 / name).read_text())


def test_e6_saved_scores_recompute_from_folds():
    for summ_name, folds_name in (
        ("instrumentA_holdout.json", "instrumentA_folds.json"),
        ("instrumentB_prime.json", "instrumentB_prime_folds.json"),
        ("instrumentB_all.json", "instrumentB_all_folds.json"),
    ):
        summary = _load(summ_name)
        folds = _load(folds_name)
        for arm, rows in folds.items():
            s = summary["scores"][arm]
            tp = sum(r["tp"] for r in rows)
            fp = sum(r["fp"] for r in rows)
            fn = sum(r["fn"] for r in rows)
            assert s["dti"] == pytest.approx(
                tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12), abs=1e-9
            )
            assert 0 <= s["ci95"][0] <= s["dti"] <= s["ci95"][1] <= 1
        assert summary["evaluator_version"] == "gems57-pooled-hide-v2"


def test_e6_beats_h33_and_ablations_on_b_prime():
    card = _load("run_card.json")
    bp = _load("instrumentB_prime.json")
    db = card["paired_b_prime_vs_h33"]
    assert db["delta"] > 0.015
    assert db["ci95"][0] > 0.004
    assert card["gate_a_candidate_ge_h33"] is True
    assert card["gate_b_prime_candidate_gt_h33_significant"] is True
    assert card["scientific_verdict"] == "promote"
    assert card["mutual_uniqueness_ok"] is True
    assert card["literal_forward_protocol_ok"] is False
    assert card["verdict"] == "negative"
    assert card["download_ok"] is True
    assert card["submit_recommended"] is False
    assert card["submit_recommended_if_mutual_policy_authorized"] is True
    assert card["weekly_slots_used"] == 0
    assert card["organizer_confirmed_score"] is None
    assert len(card["submission_note"]) <= 140

    # Controlled ablations on Instrument B' have strictly positive paired 95% CIs
    for abl in ("ablation_truncated_d32", "ablation_no_external", "random_control", "h33_reference"):
        d_abl = bp["paired_differences"][abl]
        assert d_abl["delta"] > 0.0
        assert d_abl["ci95"][0] > 0.0


def test_e6_artifact_binds_exact_bytes_and_validator():
    card = _load("run_card.json")
    path = ROOT / "docs/downloads" / f"{card['submission_name']}.tif"
    zpath = ROOT / "docs/downloads" / f"{card['submission_name']}.zip"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    zdigest = hashlib.sha256(zpath.read_bytes()).hexdigest()
    assert digest == card["raster_sha256"]
    assert zdigest == card["zip_sha256"]
    val = card["validator_output"]
    assert val["sha256"] == digest and val["all_checks_passed"] is True
    assert val["min"] == 0.0 and val["max"] == 1.0
    assert val["n_nan"] == 0 and val["n_infinite"] == 0
    assert val["emitted_positive_pixels"] == 37654
    assert val["on_catalogue_positive_pixels"] == 0
    assert all(v is True for v in val["checks"].values())
    for rel, sha in card["method_source_sha256"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == sha


def test_e6_uniqueness_and_e2_reaudit():
    surf = _load("surface_uniqueness.json")
    assert surf["registry_rasters_checked"] == 62
    assert surf["duplicate_count"] == 0 and surf["unique"] is True
    assert surf["worst_spearman_full_footprint"] <= 0.90

    fin = _load("uniqueness.json")
    assert fin["registry_rasters_checked"] == 62
    assert fin["duplicate_count"] == 0 and fin["unique"] is True
    assert fin["worst_dot_overlap"] <= 0.70
    assert fin["worst_nonlattice_forward_overlap"] <= 0.70
    assert fin["worst_spearman_full_footprint"] <= 0.90

    loc = _load("local_uniqueness.json")
    assert loc["registry_rasters_checked"] >= 11
    assert loc["duplicate_count"] == 0 and loc["unique"] is True
    assert loc["worst_dot_overlap"] <= 0.70
    assert loc["worst_forward_overlap"] <= 0.70

    e2 = _load("e2_uniqueness_62rasters.json")
    assert e2["registry_rasters_checked"] == 62
    assert e2["duplicate_count"] == 0 and e2["unique"] is True
    assert e2["worst_dot_overlap"] <= 0.70
    assert e2["worst_nonlattice_forward_overlap"] <= 0.70


def test_e6_canaries_sgmc_buffer_and_cross_lane_bprime():
    can = _load("canaries.json")
    assert can["all_passed"] is True
    assert can["worst_symmetric_auc"] <= 0.90
    assert len(can["features"]) == 28
    for vals in can["features"].values():
        assert vals["suspected_leakage"] is False
        assert vals["symmetric_auc_a"] <= 0.90
        assert vals["symmetric_auc_b_prime"] <= 0.90

    buf = _load("sgmc_buffer_audit.json")
    assert len(buf["cumulative_strict_lt"]) == 6
    assert len(buf["cumulative_inclusive_le"]) == 6
    assert len(buf["incremental_shells"]) == 6
    assert buf["distance_quantiles_px"]["sgmc_b_prime"]["fraction_gt_32px"] > 0.35
    assert buf["distance_quantiles_px"]["e6_multimodal_extdomain"]["fraction_gt_32px"] > 0.25

    cross = _load("cross_lane_bprime.json")
    expected_lanes = {
        "e6_multimodal_extdomain",
        "e3_scarpcurv_60k",
        "e2_alluvial",
        "h33_reference",
        "e5_supervised_loqo",
        "p4_stratified",
        "h70_cond_breach",
    }
    assert set(cross["scores"].keys()) == expected_lanes
    assert (
        cross["scores"]["e6_multimodal_extdomain"]["dti"]
        > cross["scores"]["h33_reference"]["dti"]
        > cross["scores"]["e5_supervised_loqo"]["dti"]
        > cross["scores"]["p4_stratified"]["dti"]
    )
