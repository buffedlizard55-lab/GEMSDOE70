"""Saved E2/E3 arithmetic and receipt binding (no experiment rerun)."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _check_saved(exp, candidate_beats):
    summary = json.loads((ROOT / f"evidence/{exp}/holdout.json").read_text())
    folds = json.loads((ROOT / f"evidence/{exp}/holdout_folds.json").read_text())
    for arm, rows in folds.items():
        s = summary["scores"][arm]
        tp = sum(r["tp"] for r in rows); fp = sum(r["fp"] for r in rows); fn = sum(r["fn"] for r in rows)
        assert s["dti"] == pytest.approx(tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12), abs=1e-12)
        assert s["withheld_positive_pixels"] == 11321
        assert 0 <= s["ci95"][0] <= s["ci95"][1] <= 1
    can = json.loads((ROOT / f"evidence/{exp}/canaries.json").read_text())
    assert all(not c["suspected_leakage"] and max(c["auc"], 1 - c["auc"]) <= 0.90 for c in can.values())
    card = json.loads((ROOT / f"evidence/{exp}/run_card.json").read_text())
    assert card["verdict"] == "negative" and card["organizer_confirmed_score"] is None
    assert card["weekly_slots_used"] == 0 and len(card["submission_note"]) <= 140
    for other, expect_above in candidate_beats.items():
        lo = summary["paired_differences"][other]["ci95"][0]
        assert (lo > 0) is expect_above, (exp, other, lo)
    return summary, card


def test_e2_saved_scores_and_bars():
    summary, _ = _check_saved("e2", {"random_dots": True, "h33_ref": True, "d28_ref": False})
    assert summary["scores"]["candidate_dots"]["dti"] < summary["scores"]["d28_ref"]["dti"]
    assert summary["scores"]["h33_ref"]["dti"] < summary["scores"]["random_dots"]["dti"]


def test_e3_saved_scores():
    _check_saved("e3", {"h33_ref": True, "random_dots": False})


def test_e2_publication_binds_exact_bytes():
    pub = json.loads((ROOT / "evidence/e2/publication.json").read_text())
    val = json.loads((ROOT / "evidence/e2/validator.json").read_text())
    path = ROOT / "docs/downloads" / pub["file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == pub["sha256"] == val["artifact_sha256"]
    assert val["local_format_pass"] and val["shared_validator"]["all_checks_passed"]
    assert pub["recomputation_matches_experiment"] and pub["submit_ok"] is False
    assert pub["validate"]["emitted_positive_pixels"] == 38000
    fin = json.loads((ROOT / "evidence/e2/final_uniqueness.json").read_text())
    assert fin["r1_worst_overlap"] <= 0.70
    assert fin["template_literal_audit"]["worst_spearman_full_footprint"] <= 0.90
    assert fin["template_literal_audit"]["worst_dot_overlap"] == 1.0  # literal dense degeneracy, published not hidden


def test_preregistration_hash_pinned():
    for exp in ("e2", "e3"):
        man = json.loads((ROOT / f"evidence/{exp}/experiment_manifest.json").read_text())
        assert man["preregistration_sha256"] == hashlib.sha256(
            (ROOT / "docs/preregistration-e2.md").read_bytes()).hexdigest()
