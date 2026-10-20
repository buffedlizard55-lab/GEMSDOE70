"""E3 candidate: independent on-disk, holdout-arithmetic and uniqueness checks."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems57.grid import load_grid
from gems57.validate import assert_submittable, validate
from gems70.method_e2 import dotted_emission
from gems70.release_e3 import digest, release_status_e3

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "evidence"
CARD = json.loads((E / "run_card_e3_amended.json").read_text())
TIF = ROOT / "docs/downloads" / f"{CARD['submission_name']}.tif"


def test_release_contract_all_checks():
    status = release_status_e3(ROOT)
    assert status["download_candidate_ok"] is True
    assert status["download_and_submit_ok"] is False  # slot selection is separate
    assert status["slot_authorized"] is False
    assert all(status["checks"].values()), status


def test_tif_bytes_revalidate_independently():
    assert digest(TIF) == CARD["raster_sha256"]
    grid = load_grid(ROOT / "data/bridge")
    receipt = validate(TIF, grid.footprint, grid.catalogue)
    assert_submittable(receipt)
    assert receipt["all_checks_passed"]
    assert receipt["emitted_positive_pixels"] == CARD["n_final_dots"] == 60000
    with rasterio.open(TIF) as ds:
        a = ds.read(1)
        assert ds.count == 1 and ds.dtypes == ("float32",)
        assert str(ds.crs) == "EPSG:32611"
    assert set(np.unique(a).tolist()) == {0.0, 1.0}  # binary: [0,1] by construction
    assert np.isfinite(a).all()
    assert not a[grid.catalogue].any() and not a[~grid.footprint].any()
    dist_ok = CARD["holdout_dti"]["selected_exclusion_px"]
    from scipy import ndimage as ndi
    dist = ndi.distance_transform_edt(~grid.catalogue)
    assert dist[a > 0].min() > dist_ok


def test_holdout_arithmetic_and_gates_from_folds():
    summary = json.loads((E / "holdout_e3.json").read_text())
    folds = json.loads((E / "holdout_folds_e3.json").read_text())
    for arm, rows in folds.items():
        s = summary["scores"][arm]
        tp = sum(r["tp"] for r in rows)
        fp = sum(r["fp"] for r in rows)
        fn = sum(r["fn"] for r in rows)
        assert s["dti"] == pytest.approx(tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12), abs=1e-12)
        assert s["withheld_positive_pixels"] == sum(r["n_truth"] for r in rows) == 11437
        assert s["evidence_class"] == "HOLDOUT-DTI"
    assert summary["paired_differences"]["random_dotted"]["ci95"][0] > 0
    canaries = json.loads((E / "canaries_e3.json").read_text())
    assert canaries and all(max(c["auc"], 1 - c["auc"]) <= 0.90 for c in canaries.values())


def test_uniqueness_vs_champion_and_erratum_binding():
    uniq = json.loads((E / "final_uniqueness_e3.json").read_text())
    rows = {r["submission"]: r for r in uniq["audit"]["rows"] if "error" not in r}
    h33 = rows["registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif"]
    assert h33["my_dots_within_3px_of_theirs"] <= 0.70
    assert h33["jaccard_dot_sets"] <= 0.50
    assert abs(h33["spearman_full_footprint"]) <= 0.90
    assert uniq["adjusted"]["duplicate_adjusted"] is False
    assert CARD["erratum"]["original_card_sha256"] == digest(E / "run_card_e3.json")
    original = json.loads((E / "run_card_e3.json").read_text())
    assert original["verdict"] == "negative" and original["raster_sha256"] is None
    assert CARD["surface_decoded_float32_sha256"] == original["surface_decoded_float32_sha256"]
    assert len(CARD["submission_note"]) <= 140
    assert CARD["organizer_confirmed_score"] is None
    assert CARD["weekly_slots_used"] == 0 and CARD["experiment_count"] == 3
    for rel, pin in CARD["method_source_sha256"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == pin


def test_emission_separation_and_budget():
    rng = np.random.default_rng(3)
    vals = rng.random((120, 120), dtype=np.float32)
    dots = dotted_emission(vals, np.ones(vals.shape, bool), 200)
    assert int(dots.sum()) == 200
    ys, xs = np.nonzero(dots)
    pts = np.c_[ys, xs].astype(float)
    for i in range(0, len(pts), 29):
        d = np.sqrt(((pts - pts[i]) ** 2).sum(1))
        d[i] = np.inf
        assert d.min() >= 2.8 - 1e-9
