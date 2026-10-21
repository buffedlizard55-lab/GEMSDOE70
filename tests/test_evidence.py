"""Verify saved arithmetic on both active promoted run (seed=70 & seed=20) AND archived E1 negative."""
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_saved_pooled_scores_match_fold_terms_seed70():
    summary = json.loads((ROOT / "evidence/holdout.json").read_text())
    folds = json.loads((ROOT / "evidence/holdout_folds.json").read_text())
    for arm, rows in folds.items():
        score = summary["scores"][arm]
        tp = sum(r["tp"] for r in rows)
        fp = sum(r["fp"] for r in rows)
        fn = sum(r["fn"] for r in rows)
        assert score["dti"] == pytest.approx(tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12), abs=1e-12)
        assert score["withheld_positive_pixels"] == sum(r["n_truth"] for r in rows)
        assert score["withheld_positive_pixels"] == 11387
        assert len(score["ci95"]) == 2
        assert 0 <= score["ci95"][0] <= score["ci95"][1] <= 1
    assert summary["scores"]["candidate"]["dti"] > summary["scores"]["experiment2_h70_2"]["dti"]
    assert summary["scores"]["candidate"]["dti"] > summary["scores"]["random_control"]["dti"]
    assert summary["scores"]["candidate"]["dti"] > summary["scores"]["g49_reimpl_control"]["dti"]
    assert summary["scores"]["candidate"]["dti"] > summary["scores"]["experiment1_h70_1"]["dti"]
    assert summary["paired_differences"]["random_control"]["ci95"][0] > 0


def test_saved_historical_seed20_comparison_and_archived_e1():
    s20 = json.loads((ROOT / "evidence/holdout_seed20_comparison.json").read_text())
    assert s20["pooled"]["scores"]["candidate"]["withheld_positive_pixels"] == 11321
    assert s20["pooled"]["scores"]["candidate"]["dti"] > 0.11
    assert s20["pooled"]["scores"]["experiment1_h70_1"]["dti"] == pytest.approx(0.010192889039757751, abs=1e-9)

    arch_audit = json.loads((ROOT / "evidence/history/experiment1_contact_termination/surface_uniqueness.json").read_text())
    cert = json.loads((ROOT / "evidence/registry_saturation.json").read_text())
    assert arch_audit["registry_rasters_checked"] == 1
    assert arch_audit["complete_accessible_scan"] is False
    assert arch_audit["unique"] is False
    assert arch_audit["stop_required"]
    assert cert["universal_overlap_blocker"]
    assert cert["uncovered_allowed_pixels"] == 0
    assert cert["positive_pixels"] == 5167373


def test_complete_931_registry_uniqueness_verified():
    surf = json.loads((ROOT / "evidence/surface_uniqueness.json").read_text())
    final = json.loads((ROOT / "evidence/final_uniqueness.json").read_text())
    assert surf["registry_rasters_checked"] == 931
    assert surf["complete_accessible_scan"] is True
    assert abs(surf["worst_spearman_full_footprint"]) <= 0.90
    assert final["registry_rasters_checked"] == 931
    assert final["byte_unique_among_checked"] is True
    assert final["pixel_unique_among_checked"] is True
    assert abs(final["worst_spearman_full_footprint"]) <= 0.90


def test_no_historical_projection_is_current_score():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card["organizer_confirmed_score"] is None
    audit = json.loads((ROOT / "evidence/h33_audit.json").read_text())
    assert audit["organizer_confirmed_scores"] is None
    assert audit["files"]["h33"]["positive_pixels"] == 37654
    assert audit["comparisons"]["h27_to_h33"]["exactly_old_with_distance_gt_2"]
    assert audit["comparisons"]["h27_to_h33"]["removed"] == 2545
