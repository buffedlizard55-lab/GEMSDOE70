"""Verification tests for P9 zero-SGMC Quaternary piedmont multi-physics + 300 m submodular synthesis."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems57 import metric
from gems70.phase5_emit import peak_nms_emit, submodular_dti_emit
from gems70.release import assert_no_public_rasters, digest, p9_status

ROOT = Path(__file__).resolve().parents[1]
SUB_NAME = 'gems70-p5-multiphysics-submodular-37654-20261020'


def test_p9_status_and_artifact_integrity():
    st = p9_status(ROOT)
    assert st['verdict'] == 'promote'
    assert st['download_ok'] is True
    assert st['submit_recommended'] is True
    assert st['holdout_and_proxy_gates_passed'] is True
    assert st['selector_ready'] is True
    assert st['literal_forward_stop'] is True
    assert st['submit_recommended_automatic'] is False
    assert st['weekly_slots_used'] == 0
    assert st['reasons'] == []

    card = json.loads((ROOT / 'evidence/p9_piedmont_submod/run_card.json').read_text())
    assert len(card['submission_note']) == card['note_chars'] <= 140
    assert card['organizer_confirmed_score'] is None
    assert card['experiment_count'] == 3

    tif = ROOT / f'docs/downloads/{SUB_NAME}.tif'
    zp = ROOT / f'docs/downloads/{SUB_NAME}.zip'
    assert tif.is_file() and zp.is_file()
    assert digest(tif) == card['raster_sha256']
    assert digest(zp) == card['zip_sha256']
    with zipfile.ZipFile(zp) as zf:
        assert zf.namelist() == [f'{SUB_NAME}.tif']
        assert zf.read(f'{SUB_NAME}.tif') == tif.read_bytes()

    with rasterio.open(tif) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == 'float32'
        assert ds.shape == (3730, 3292)
        assert ds.crs.to_epsg() == 32611
        arr = ds.read(1)
    assert np.isfinite(arr).all()
    assert set(np.unique(arr).tolist()) == {0.0, 1.0}
    assert int((arr == 1.0).sum()) == 37654


def test_p9_beats_h33_and_p8_oof38k_on_live_calibrated_piedmont_instrument():
    card = json.loads((ROOT / 'evidence/p9_piedmont_submod/run_card.json').read_text())
    cal = json.loads((ROOT / 'evidence/instrument_calibration.json').read_text())
    assert len(cal['historical_submissions_evaluated']) == 22
    assert cal['correlations_vs_user_reported_live_scores']['instrument_c_pied_dti']['spearman_rho'] == pytest.approx(0.866742, abs=1e-4)

    # Strictly positive paired 95% CIs vs H33 across all 3 blind OOF instruments: A, B', and C_pied
    assert card['paired_a_vs_h33']['ci95'][0] > 0.08
    assert card['paired_b_prime_vs_h33']['ci95'][0] > 0.009
    assert card['paired_c_pied_vs_h33']['ci95'][0] > 0.0
    # Strictly positive paired 95% CI vs P8-OOF38k on live-calibrated C_pied
    dp8 = card['cross_lane_head_to_head']['paired_vs_p8_oof38k_on_C_pied']
    assert dp8['delta'] == pytest.approx(0.027010, abs=1e-4)
    assert dp8['ci95'][0] > 0.01


def test_p9_fold_terms_reproduce_pooled_dti_to_machine_precision():
    for summary_name, folds_name in [
        ('instrumentA_holdout.json', 'instrumentA_folds.json'),
        ('instrumentA_quad.json', 'instrumentA_quad_folds.json'),
        ('instrumentB_prime.json', 'instrumentB_prime_folds.json'),
        ('instrumentC_pied.json', 'instrumentC_pied_folds.json'),
    ]:
        summary = json.loads((ROOT / 'evidence/p9_piedmont_submod' / summary_name).read_text())
        folds_doc = json.loads((ROOT / 'evidence/p9_piedmont_submod' / folds_name).read_text())
        for arm, sc in summary['scores'].items():
            tp, fp, fn = np.asarray([(r['tp'], r['fp'], r['fn']) for r in folds_doc[arm]], dtype=np.float64).sum(axis=0)
            recomputed = float(tp / (tp + 0.2 * fp + 0.8 * fn))
            assert recomputed == pytest.approx(sc['dti'], rel=1e-12, abs=1e-12)


def test_p9_all_78_leakage_canaries_and_73_raster_uniqueness():
    feats = json.loads((ROOT / 'evidence/p9_piedmont_submod/canaries.json').read_text())
    assert len(feats) == 78
    assert max(max(v['auc'], 1.0 - v['auc']) for v in feats.values()) <= 0.90
    assert not any('sgmc' in k.lower() for k in feats)

    u73 = json.loads((ROOT / 'evidence/p9_piedmont_submod/uniqueness_all_lanes.json').read_text())
    assert u73['total_rasters_checked'] >= 73
    assert u73['unique'] is True
    assert u73['duplicate_count'] == 0
    assert u73['worst_dot_overlap'] <= 0.70
    assert abs(u73['worst_spearman_full_footprint']) <= 0.90


def test_submodular_expected_dti_allocate_synthetic_unit():
    rng = np.random.default_rng(7)
    post = rng.uniform(0.0, 0.25, size=(48, 48)).astype(np.float32)
    post[20:28, 24] = 0.85
    allowed = np.ones((48, 48), dtype=bool)
    allowed[0, :] = False
    for fn in (submodular_dti_emit, peak_nms_emit):
        out = fn(post, allowed, n_dots=18)
        assert out.dtype == np.float32
        assert set(np.unique(out).tolist()) == {0.0, 1.0}
        assert int((out == 1.0).sum()) == 18
        assert not (out[~allowed] > 0).any()


def test_p9_site_and_readme_integration():
    assert_no_public_rasters(ROOT)
    for page in ('docs/p9.html', 'docs/index.html', 'docs/results.html', 'docs/submission.html',
                 'docs/executive-summary.html', 'README.md'):
        txt = (ROOT / page).read_text()
        assert SUB_NAME in txt
    p9_html = (ROOT / 'docs/p9.html').read_text()
    assert 'assets/phase5_calibration_ablation.svg' in p9_html
    assert 'assets/phase5_uniqueness_audit.svg' in p9_html
    assert 'assets/phase5_map_comparison.png' in p9_html
