"""P5 negative: measured new research TIFF is NEVER weekly-slot approval."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import zipfile

import numpy as np
import pytest
import rasterio

from gems70 import phase5
from gems70.release import p5_status

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / 'evidence/p5/run_card.json'


def read(path):
    return json.loads(path.read_text())


def test_synthetic_feature_domain_never_includes_farther_than_32_px():
    shape = (90, 90)
    raw = {k: np.full(shape, float(i), np.float32) for i, k in enumerate(phase5.BANDS, start=1)}
    raw['tmi_hg'][0, 0] = -3.4028235e38
    valid0 = phase5.feature_valid(raw, np.ones(shape, bool))
    assert not valid0[0, 0]
    f = phase5.physics(raw, valid0)
    assert tuple(f) == phase5.FEATURE_NAMES
    assert all(np.isfinite(v).all() for v in f.values())
    cat = np.zeros(shape, bool); cat[45, 45] = True
    d = phase5.visible_distance(cat)
    a = phase5.domain(np.ones(shape, bool), cat, d)
    assert d[89, 89] > 32 and not a[89, 89]
    assert a[45, 48] and not a[45, 45] and not a[45, 47]
    # Clipping applies only to model covariates, NOT to the halo domain.
    assert phase5.design(f, d, [0])[-1, -1] == 32
    scores = np.zeros(shape, np.float32)
    scores[a] = np.arange(a.sum(), dtype=np.float32)
    p = phase5.rank_surface(scores, a)
    assert (p >= 0).all() and (p < 1).all() and not p[~a].any()
    assert 0 < (p > 0).sum() <= .021 * a.sum()


def test_new_raster_is_byte_distinct_locally_valid_but_literal_duplicate():
    card = read(CARD)
    path = ROOT / card['raster_path']
    assert card['verdict'] == 'negative' and card['weekly_slots_used'] == 0
    assert card['organizer_confirmed_score'] is None
    assert card['download_ok'] is True and card['submit_recommended'] is False
    assert len(card['submission_note']) == card['note_chars'] <= 140
    assert 'DO-NOT-SUBMIT' in card['submission_name']
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    assert h == card['raster_sha256'] == card['validator_output']['sha256']
    from gems70.release import published_artifacts
    local = published_artifacts(ROOT)
    assert h not in {pin for rel, pin in local.items() if rel != card['raster_path']}  # new bytes
    with rasterio.open(path) as ds, rasterio.open(ROOT / 'data/bridge/sample_submission.tif') as sample:
        a = ds.read(1); ref = sample.read(1); fp = np.isfinite(ref)
        assert ds.count == 1 and ds.dtypes[0] == 'float32'
        assert (ds.shape, ds.crs, ds.transform) == (sample.shape, sample.crs, sample.transform)
        assert a.dtype == np.float32 and np.isfinite(a).all()
        assert 0 <= a.min() <= a.max() < 1
        assert not a[~fp].any() and np.count_nonzero(a) > 0
        with rasterio.open(ROOT / 'data/bridge/existing_faults.tif') as faults:
            cat = (faults.read(1) > 0) & fp
            assert not a[cat].any()
    with zipfile.ZipFile(path.with_suffix('.zip')) as z:
        assert z.namelist() == [path.name] and z.read(path.name) == path.read_bytes()
    assert all(v is True for v in card['validator_output']['checks'].values())
    rel = card['correlation_overlap_vs_registry']
    assert rel['rasters_checked'] >= 68 and rel['binary_one_dots'] == 0
    assert rel['worst_spearman_full_footprint'] < .90
    assert rel['forward_overlap_positive_support_lattice'] == 1.0
    assert rel['literal_3px_forward_gate_passes'] is False
    blocker = read(ROOT / 'evidence/p5/literal_blocker.json')
    assert blocker['feature_valid_uncovered_pixels'] == 0 and blocker['literal_stop_for_any_dot_field_in_valid']
    assert blocker['witness_dots'] == 206895
    status = p5_status(ROOT)
    assert status['download_ok_for_review'] and not status['submit_recommended']


def test_pooled_holdout_and_proxy_terms_match_saved_fold_receipts():
    for summary_name, folds_name, best in [
        ('instrument_a.json', 'folds_a.json', 'visible_only_p4'),
        ('instrument_b_prime.json', 'folds_b_prime.json', 'h33_frozen')]:
        d = read(ROOT / 'evidence/p5' / summary_name)
        folds = read(ROOT / 'evidence/p5' / folds_name)
        for arm, rows in folds.items():
            tp, fp, fn = (sum(r[k] for r in rows) for k in ('tp', 'fp', 'fn'))
            assert d['scores'][arm]['withheld_positive_pixels'] == sum(r['n_truth'] for r in rows)
            assert d['scores'][arm]['dti'] == pytest.approx(tp/(tp+.2*fp+.8*fn+1e-12), abs=1e-12)
        cand = d['scores']['candidate_continuous']; ref = d['scores'][best]
        assert cand['evidence_class'] == 'HOLDOUT-DTI'
        assert cand['evaluator_version'] == 'gems57-pooled-hide-v2'
        assert cand['dti'] < ref['dti']
        delta = d['paired_differences'][best]
        assert delta['delta'] < 0 and delta['ci95'][1] < 0
    card = read(CARD)
    baseline = ROOT / 'evidence/p5/p4_visible_baseline_folds.json'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == card['p4_visible_baseline_folds_sha256']
    assert read(baseline)['candidate'] == read(ROOT / 'evidence/p5/folds_a.json')['visible_only_p4']
    assert not card['gate_results']['a_beats_visible_p4_significant']
    assert not card['gate_results']['b_prime_beats_h33_significant']
    assert card['holdout_dti']['instrument_a']['withheld_positive_pixels'] == 11321
    assert card['holdout_dti']['instrument_b_prime_proxy']['withheld_positive_pixels'] == 59937


def test_leakage_canaries_and_preregistration_source_identity():
    card = read(CARD)
    prereg = ROOT / card['hypothesis_source']
    assert hashlib.sha256(prereg.read_bytes()).hexdigest() == card['preregistration_sha256']
    for rel, pin in card['method_source_sha256'].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == pin
    for row in read(ROOT / 'evidence/p5/canaries.json').values():
        assert row['withheld_positive_pixels'] == 11321
        assert max(row['auc'], row['inverse_auc']) < .90
        assert row['suspected_leakage'] is False
    assert read(ROOT / 'evidence/p5/reporting_amendment.json')['no_retraining'] is True


def test_missing_or_tampered_review_artifact_fails_closed(tmp_path):
    assert not p5_status(tmp_path)['download_ok_for_review']
    card = read(CARD)
    rel = card['raster_path']
    for source in [CARD, ROOT / rel, ROOT / rel.replace('.tif', '.zip'),
                   ROOT / rel.replace('.tif', '.json'),
                   ROOT / 'registry/published_artifacts.json']:
        dst = tmp_path / source.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dst)
    assert p5_status(tmp_path)['download_ok_for_review']
    tif = tmp_path / rel
    tif.write_bytes(tif.read_bytes() + b'corruption')
    assert not p5_status(tmp_path)['download_ok_for_review']


def test_public_site_first_screen_is_unambiguous_and_receipted():
    idx = (ROOT / 'docs/index.html').read_text()
    assert 'Download NEW P5-cover research TIFF — DO NOT SUBMIT' in idx
    assert 'Competition upload / weekly slot: NO' in idx
    assert 'positive cells have' in idx and 'forward 3-pixel overlap' in idx
    detail = (ROOT / 'docs/p5.html').read_text()
    assert 'downloads/p5_run_card.json' in detail
    assert 'sample has NaNs outside its footprint' in detail
    assert 'sample and this conservative output use all-finite zeros' not in detail
    with rasterio.open(ROOT / 'data/bridge/sample_submission.tif') as sample:
        assert int(np.isnan(sample.read(1)).sum()) == 7111787
