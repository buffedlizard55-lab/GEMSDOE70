import json
from pathlib import Path
import sys
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit import check_template, coverage_report, sha
from release_gate import status
from gems57 import grid, uniqueness


def test_template_is_byte_pinned_and_upstream_checked():
    assert check_template()["ok"]
    assert json.loads((ROOT / "evidence/template-upstream.json").read_text())["ok"]


def test_bridge_identities_and_grid():
    assert sha(ROOT / "data/bridge/sample_submission.tif") == grid.SHA256_SAMPLE_SUBMISSION
    assert sha(ROOT / "data/bridge/existing_faults.tif") == grid.SHA256_EXISTING_FAULTS
    g = grid.load_grid(ROOT / "data/bridge")
    assert g.shape == (3730, 3292)
    assert int(g.footprint.sum()) == 5167373


def test_universal_support_proof_uses_literal_positivity():
    fp = np.ones((7, 9), bool)
    w = np.full(fp.shape, np.nextafter(0.0, 1.0))
    r = coverage_report(w, fp)
    assert r["strictly_positive_on_entire_footprint"]
    assert r["implied_forward_overlap_for_any_nonempty_in_footprint_candidate"] == 1
    rng = np.random.default_rng(70)
    for _ in range(12):
        candidate = rng.random(fp.shape) > 0.8
        assert uniqueness.dot_overlap(candidate, w) == 1


@pytest.mark.parametrize("missing", [0.0, -1.0, np.nan, np.inf])
def test_not_universal_if_any_cell_is_not_finite_positive(missing):
    w = np.ones((5, 5))
    w[2, 2] = missing
    assert not coverage_report(w, np.ones(w.shape, bool))["strictly_positive_on_entire_footprint"]


def test_empty_and_mismatched_footprints_rejected():
    for fp in [np.zeros((3, 3), bool), np.ones((4, 4), bool)]:
        with pytest.raises(ValueError):
            coverage_report(np.ones((3, 3)), fp)


def test_shared_overlap_radius_is_inclusive_euclidean():
    mine = np.zeros((11, 11))
    theirs = np.zeros_like(mine)
    mine[5, 5] = 1
    theirs[5, 8] = 0.00001
    assert uniqueness.dot_overlap(mine, theirs) == 1
    theirs[:] = 0
    theirs[8, 8] = 1
    assert uniqueness.dot_overlap(mine, theirs) == 0


def test_active_release_is_promoted_and_archived_e1_is_negative():
    r_prom = status()
    assert r_prom["verdict"] == "promote"
    assert r_prom["download_available"] is True
    assert r_prom["approved_for_weekly_slot"] is False
    assert r_prom["generated_tif"] == "docs/downloads/gemsdoe70-h70-3-dual-expert-submodular-20261020T223000Z.tif"
    assert r_prom["scientific_experiments_run"] == 3
    assert r_prom["submission_slots_used"] == 0

    r_arch = status("evidence/history/experiment1_contact_termination")
    assert r_arch["verdict"] == "negative"
    assert not r_arch["download_available"]
    assert r_arch["generated_tif"] is None


def test_card_does_not_fabricate_missing_evidence():
    card = json.loads((ROOT / "evidence/history/parallel-review2/run_card.json").read_text())
    assert card["raster_sha256"] is None
    assert card["holdout"]["dti"] is None
    assert card["holdout"]["ci95"] is None
    assert card["registry"]["spearman"] is None
    assert card["validator"]["values_in_0_1"] is None
    assert len(card["note"]) <= 140


def test_negative_proof_receipt_is_not_a_complete_scan_claim():
    r = json.loads((ROOT / "evidence/preflight.json").read_text())
    assert r["coverage"]["strictly_positive_on_entire_footprint"]
    assert r["shared_saturation_certificate"]["universal_overlap_blocker"]
    assert r["minimum_forward_overlap"] > r["literal_overlap_limit"]
    assert "NOT a complete" in r["scope"]
