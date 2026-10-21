"""Comprehensive Phase 5 verification suite covering emitters, GeoTIFF/ZIP integrity,
multi-instrument confidence intervals, canaries, handoff artifacts, and README brief."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gems70.phase5_emit import peak_nms_emit, submodular_dti_emit
from gems70.release import valid_canary

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_submodular_emitter_exact_budget_and_superior_coverage():
    """Verify exact binary budget N, zero forbidden support, and superior 300 m DTI coverage on linear ridges."""
    surf = np.zeros((48, 48), dtype=np.float32)
    # Create an elongated 1-px fault trace across row=24, cols 6..41
    surf[24, 6:42] = 0.85
    allowed = np.ones((48, 48), dtype=bool)
    allowed[:4, :] = False

    dots_sub = submodular_dti_emit(surf, allowed, n_dots=10)
    dots_nms = peak_nms_emit(surf, allowed, n_dots=10)

    assert dots_sub.dtype == np.float32
    assert set(np.unique(dots_sub)).issubset({0.0, 1.0})
    assert int((dots_sub > 0.5).sum()) == 10
    assert not (dots_sub[~allowed] > 0.5).any()

    q_sub = np.maximum(0.0, 1.0 - distance_transform_edt(~(dots_sub > 0.5)) / 3.0)
    q_nms = np.maximum(0.0, 1.0 - distance_transform_edt(~(dots_nms > 0.5)) / 3.0)
    tp_sub = float((surf * q_sub).sum())
    tp_nms = float((surf * q_nms).sum())
    assert tp_sub > tp_nms


def test_phase5_geotiff_and_zip_archive_integrity():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card["phase"] == "phase5"
    assert card["verdict"] == "promote"
    assert card["download_ok"] is True
    assert card["submit_recommended"] is True
    assert card["weekly_slots_used"] == 0
    assert len(card["submission_note"]) <= 140

    tif_path = ROOT / "docs/downloads" / f"{card['submission_name']}.tif"
    zip_path = ROOT / "docs/downloads" / f"{card['submission_name']}.zip"
    assert tif_path.is_file() and zip_path.is_file()
    assert _sha256(tif_path) == card["raster_sha256"]
    assert _sha256(zip_path) == card["zip_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()

    with rasterio.open(tif_path) as ds:
        arr = ds.read(1)
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        assert list(ds.transform)[:6] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
        assert ds.nodata is None
    assert np.isfinite(arr).all()
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    assert set(np.unique(arr)).issubset({0.0, 1.0})
    assert int((arr == 1.0).sum()) == 37654


def test_phase5_all_promotion_gates_and_canaries_pass():
    card = json.loads((ROOT / "evidence/phase5/run_card.json").read_text())
    assert card["paired_a_vs_h33"]["ci95"][0] > 0.0
    assert card["paired_b_prime_vs_h33"]["ci95"][0] > 0.0
    assert card["paired_c_pied_vs_h33"]["ci95"][0] > 0.0
    assert card["instrument_a_holdout"]["candidate"]["dti"] > 0.07304229212058164
    assert card["instrument_a_holdout"]["candidate_offcat_static"]["dti"] > card["instrument_a_holdout"]["h33_reference"]["dti"]

    canaries = json.loads((ROOT / "evidence/phase5/canaries.json").read_text())
    assert len(canaries) == 78
    assert all(valid_canary(c) for c in canaries.values())

    uniq = json.loads((ROOT / "evidence/phase5/uniqueness.json").read_text())
    assert uniq["unique"] is True
    assert uniq["duplicate_count"] == 0
    assert uniq["surface_max_abs_spearman"] <= 0.90
    assert uniq["worst_dot_overlap"] <= 0.70
    assert uniq["worst_real_model_forward_overlap"] <= 0.70


def test_handoff_items_and_embedded_prompt_complete():
    e2 = json.loads((ROOT / "evidence/e2/corrected_full_uniqueness.json").read_text())
    assert e2["unique_under_corrected_mutual_gate"] is True
    assert e2["submit_ok"] is False
    assert e2["verdict"] == "negative"

    up = json.loads((ROOT / "evidence/upstream_suite_verification.json").read_text())
    assert up["failed"] == 0 and up["passed"] >= 190
    assert (ROOT / "evidence/upstream_patch.diff").stat().st_size > 100

    readme = (ROOT / "README.md").read_text()
    brief = (ROOT / "PROJECT_BRIEF.md").read_text()
    assert brief in readme
