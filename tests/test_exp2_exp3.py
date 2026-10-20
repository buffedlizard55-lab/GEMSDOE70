"""Verify experiments 2-3 arithmetic and preregistration binding without rerunning.

No test here depends on .cache (reconstructible, git-ignored) or spends the
exhausted experiment budget. Preregistration SHA checks make post-hoc edits
visible: the manifests bind the exact prereg text the gates ran under.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def test_preregistration_binding():
    m2 = json.loads((ROOT / "evidence/exp2_manifest.json").read_text())
    assert m2["preregistration_sha256"] == sha(ROOT / "docs/hypotheses-round2.md")
    for rel, pin in m2["source_sha256"].items():
        assert sha(ROOT / rel) == pin, rel
    assert m2["experiment_count"] == 2
    m3 = json.loads((ROOT / "evidence/exp3_manifest.json").read_text())
    assert m3["preregistration_sha256"] == sha(ROOT / "docs/exp3-prereg.md")
    assert sha(ROOT / "scripts/run_experiment_exp3.py") == m3["source_sha256"]["scripts/run_experiment_exp3.py"]
    assert m3["method_exp2_sha256"] == m2["source_sha256"]["src/gems70/method_exp2.py"]
    assert sha(ROOT / "src/gems70/method_exp2.py") == m3["method_exp2_sha256"]
    assert m3["experiment_count"] == 3


def test_run_cards_negative_no_slots():
    for name in ("exp2_run_card.json", "exp3_run_card.json"):
        card = json.loads((ROOT / "evidence" / name).read_text())
        assert card["verdict"] == "negative"
        assert card["weekly_slots_used"] == 0
        assert card["organizer_confirmed_score"] is None
        assert card["experiment"] in (2, 3)
    card2 = json.loads((ROOT / "evidence/exp2_run_card.json").read_text())
    assert card2["gates"]["gate2_beat_exp1"] is False
    assert card2["gates"]["gate3_beat_random"] is False
    assert card2["gates"]["gate6_rho"] is True
    assert card2["gates"]["gate7_overlap"] is True
    assert card2["emission"] == {"pool": 222341, "taken": 38000}
    assert card2["ew_fraction"] < 0.50
    card3 = json.loads((ROOT / "evidence/exp3_run_card.json").read_text())
    assert card3["gates"]["gateA_instrument"] is False
    assert card3["gates"]["gateB_signal"] is False
    assert "raster_sha256" not in card3


def test_exp2_holdout_arithmetic_and_futility():
    for seed, npos in ((20, 11321), (71, 11425)):
        summary = json.loads((ROOT / f"evidence/exp2_holdout_seed{seed}.json").read_text())
        folds = json.loads((ROOT / "evidence/exp2_holdout_folds.json").read_text())[str(seed)]
        for arm, rows in folds.items():
            score = summary["scores"][arm]
            tp = sum(r["tp"] for r in rows)
            fp = sum(r["fp"] for r in rows)
            fn = sum(r["fn"] for r in rows)
            assert score["dti"] == pytest.approx(tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12), abs=1e-9)
            assert score["withheld_positive_pixels"] == sum(r["n_truth"] for r in rows)
            assert len(score["ci95"]) == 2
        cand = summary["scores"]["candidate"]
        avoid = summary["scores"]["random_avoiding"]
        assert cand["withheld_positive_pixels"] == avoid["withheld_positive_pixels"] == npos
        # Tied with avoiding-random: intervals overlap on both seeds.
        assert not (cand["ci95"][0] > avoid["ci95"][1] or avoid["ci95"][0] > cand["ci95"][1])
        assert summary["scores"]["ablation_no_prune"]["dti"] > 10 * cand["dti"]
        for cname, can in json.loads((ROOT / f"evidence/exp2_canaries_seed{seed}.json").read_text()).items():
            assert can["suspected_leakage"] is False
            assert 0 <= can["auc"] <= 1
            assert max(can["auc"], 1 - can["auc"]) <= 0.90


def test_exp3_proxy_arithmetic_and_ladder():
    summary = json.loads((ROOT / "evidence/exp3_holdout.json").read_text())
    assert summary["truth_provenance"]["n_truth"] == 62122
    assert summary["truth_provenance"]["sha256"] == "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"
    for arm, score in summary["scores"].items():
        assert score["dti"] == pytest.approx(
            score["tpw"] / (score["tpw"] + 0.2 * score["fpw"] + score["fnw"] * 0.8 + 1e-12),
            abs=1e-9)
    s = summary["scores"]
    # Live-ladder direction reproduces on the proxy; candidate ties random.
    assert s["h33"]["dti"] > s["h27"]["dti"] > s["d28"]["dti"]
    assert s["h33"]["ci95"][0] > s["random_avoiding"]["ci95"][1]
    assert not (s["candidate"]["ci95"][0] > s["random_avoiding"]["ci95"][1])
    assert summary["paired_differences"]["h33"]["ci95"][1] < 0


def test_uniqueness_subset_transparency():
    audit = json.loads((ROOT / "evidence/exp2_uniqueness_subset.json").read_text())
    assert audit["evidence_class"] == "REGISTRY-MEASUREMENT-PARTIAL"
    assert "NOT a complete" in audit["scope"]
    rows = {r["key"]: r for r in audit["rows"]}
    for key in ("h33", "h27", "d28", "g17F", "g17D", "g17A", "h70c", "g52h70", "g17E_dense"):
        assert key in rows, key
    dense = rows["g17E_dense"]
    assert dense["sparse"] is False
    assert dense["overlap_final_dots"] == 1.0  # reported, not gated (R1)
    assert dense["duplicate_by_overlap_gated"] is False
    assert dense["duplicate_by_rho"] is False
    assert rows["h33"]["overlap_final_dots"] < 0.70
    assert rows["g52h60_sup"]["error"]  # honest missing-file record
    add = json.loads((ROOT / "evidence/exp2_uniqueness_addendum.json").read_text())
    assert add["their_dots"] == 37654
    assert add["overlap_final_dots"] < 0.70
    # Registry identities measured this session or in prior evidence.
    pins = {
        "h33": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
        "h27": "2fc94a38d77f74d4f4ed1a97a83e7bb71a1ceea090515ec641e6681cc47c44c8",
        "d28": "3e78737f0da8dd2ca66cc6caac0ce8eeefcd6715707f8d1bd3091845cd9bcc30",
        "g17F": "0210da4395b209450e52e9efc780ab3ca6aceffd60c26d6f623da2b8fe76b691",
        "g17D": "8612586354611df8602a2b0bad8a7916946d1bc0bc32f63e39f1fffbcccced8d",
        "g17A": "c5ea501eba0ab840d26f0c017d01074c4bd9040ec5e2c5ac19bde8655d150e64",
        "h70c": "36d2c3c4366e88cb25690fa8640bdde0adf618fa36d57775de3e40d8cd3c5768",
        "g17E_dense": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
        "g52h70": "ea9774a871929427e60261cdfe2f64fdab0d0c8c2253cf2eac119cc404e28af3",
        "g52h97b_sup": "1b0b00aa711fde1a0e7dfbdb3680bc9f8652a09f7ff6ee3709e7ccafda9656a2",
        "g52h83_sup": "de580306e2cb6460fced1b745d1d40ff9735fb5497d493a56cca7630ad2a0ef7",
    }
    for key, pin in pins.items():
        assert rows[key]["sha256"] == pin, key
    assert add["sha256"] == "59abe557302c158463911f388bcf2ec7edafc511e6948f431f3fee339f947333"


def test_no_submission_artifacts_written():
    assert not list((ROOT / "docs/downloads").glob("*.tif"))
    assert not list((ROOT / "docs/downloads").glob("*.zip"))
    assert not list((ROOT / "evidence").glob("*.tif"))
    assert not list((ROOT / "evidence").glob("*.zip"))


def test_session_cards_complete_and_negative():
    for name, run in (("session_card_exp2.json", "exp2_run_card.json"),
                      ("session_card_exp3.json", "exp3_run_card.json")):
        card = json.loads((ROOT / "evidence" / name).read_text())
        for key in ("hypothesis", "mechanism", "non_fault_mimic", "holdout_dti",
                    "correlation_overlap_vs_registry", "raster_sha256",
                    "validator_output", "submission_name", "submission_note",
                    "verdict"):
            assert key in card, (name, key)
        assert card["verdict"] == "negative"
        assert card["raster_sha256"] is None
        assert card["validator_output"]["status"] == "NOT_WRITTEN"
        assert len(card["submission_note"]) <= 140
        assert "DO NOT SUBMIT" in card["submission_note"]
        assert card["run_card"] == f"evidence/{run}"
    card = json.loads((ROOT / "evidence/session_card_exp2.json").read_text())
    checks = card["validator_output"]["pre_export_array_checks"]
    assert checks["n_dots"] == 38000
    assert all(v is True for k, v in checks.items() if k != "n_dots")


def test_site_covers_all_runs():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_site import main
    main()
    for name in ("exp2_run_card.json", "exp3_run_card.json", "exp2_holdout_seed20.json",
                 "exp2_holdout_seed71.json", "exp3_holdout.json",
                 "exp2_uniqueness_subset.json", "exp3_manifest.json",
                 "session_card_exp2.json", "session_card_exp3.json"):
        assert (ROOT / "docs/downloads" / name).is_file(), name
    for name in ("hypotheses-round2.html", "exp3-prereg.html", "session-status.json",
                 "exp2-run-card.json", "exp3-run-card.json"):
        assert (ROOT / "docs" / name).is_file(), name
    home = (ROOT / "docs/index.html").read_text()
    assert "3/3" in home
    session = json.loads((ROOT / "docs/session-status.json").read_text())
    assert session["download_and_submit_ok"] is False
    assert [r["verdict"] for r in session["runs"]] == ["negative"] * 3
