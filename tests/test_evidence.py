"""Saved arithmetic and the published artifact must agree with their receipts."""
import json
from pathlib import Path
import pytest
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('phase', ['phase2', 'phase3', 'phase4', 'phase5'])
def test_saved_pooled_scores_match_fold_terms(phase):
    base = ROOT / 'evidence' / phase
    files = {'instrumentA_holdout.json': 'instrumentA_folds.json',
             'instrumentB_proxy.json': 'instrumentB_folds.json',
             'instrumentB_prime.json': 'instrumentB_prime_folds.json',
             'instrumentB_all.json': None}
    checked = 0
    for summary_name, folds_name in files.items():
        summary_p = base / summary_name
        if not summary_p.is_file():
            continue
        summary = json.loads(summary_p.read_text())
        if folds_name and (base / folds_name).is_file():
            folds = json.loads((base / folds_name).read_text())
            for arm, rows in folds.items():
                if arm not in summary['scores']:
                    continue
                tp = sum(r['tp'] for r in rows)
                fp = sum(r['fp'] for r in rows)
                fn = sum(r['fn'] for r in rows)
                assert summary['scores'][arm]['dti'] == pytest.approx(
                    tp / (tp + .2 * fp + .8 * fn + 1e-12), abs=1e-12)
                assert summary['scores'][arm]['withheld_positive_pixels'] == sum(
                    r['n_truth'] for r in rows)
                checked += 1
        assert 0 <= summary['scores']['candidate']['ci95'][0] <= summary['scores']['candidate']['ci95'][1] <= 1
    assert checked > 0


@pytest.mark.parametrize('phase', ['phase4', 'phase5'])
def test_uniqueness_receipt_is_mutual_and_complete(phase):
    audit = json.loads((ROOT / f'evidence/{phase}/uniqueness.json').read_text())
    assert audit['registry_rasters_checked'] == 62
    assert audit['unique'] is True
    assert audit['duplicate_count'] == 0
    assert audit['worst_dot_overlap'] <= 0.70
    assert audit['worst_forward_overlap'] >= audit['worst_dot_overlap']
    assert audit['worst_spearman_full_footprint'] <= 0.90
    assert 'mutual' in audit['overlap_definition']


def test_phase5_card_extra_receipts_exist_and_agree():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['phase_evidence']['dir'] == 'evidence/phase5'
    for rel in ('uniqueness.json', 'canaries.json', 'surface_uniqueness.json',
                'instrumentA_holdout.json', 'instrumentB_prime.json'):
        p = ROOT / 'evidence/phase5' / rel
        assert p.is_file(), rel
    canaries = json.loads((ROOT / 'evidence/phase5/canaries.json').read_text())
    assert canaries['stop'] is False
    assert canaries['model_oof']['suspected_leakage'] is False
    surface = json.loads((ROOT / 'evidence/phase5/surface_uniqueness.json').read_text())
    assert surface['duplicate_count'] == 0
    assert surface['worst_spearman_full_footprint'] <= 0.90
    # the card's contamination disclosure is a measured fraction in [0, 1]
    frac = card['contamination_disclosure']['a_truth_pixels_within_3px_of_proxy']
    assert 0.0 <= frac <= 1.0


def test_published_tiff_matches_card_and_is_binary():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    path = ROOT / 'docs/downloads' / (card['submission_name'] + '.tif')
    with rasterio.open(path) as src:
        a = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert (src.height, src.width) == (3730, 3292)
        assert str(src.crs) == 'EPSG:32611'
    vals = np.unique(a)
    assert set(np.round(vals, 6)).issubset({0.0, 1.0})
    assert int((a > 0).sum()) == card['registered_parameters']['dot_count']
    assert np.isfinite(a).all()


def test_no_historical_projection_is_current_score():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['organizer_confirmed_score'] is None
    audit = json.loads((ROOT / 'evidence/h33_audit.json').read_text())
    assert audit['organizer_confirmed_scores'] is None
    assert audit['files']['h33']['positive_pixels'] == 37654
    assert audit['comparisons']['h27_to_h33']['removed'] == 2545
