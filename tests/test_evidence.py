"""Saved arithmetic and the published artifact must agree with their receipts."""
import json
from pathlib import Path
import pytest
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('phase', ['phase2', 'phase3', 'phase4'])
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


def test_historical_mutual_pass_is_overruled_by_new_forward_stop():
    audit = json.loads((ROOT / 'evidence/phase4/uniqueness.json').read_text())
    assert audit['registry_rasters_checked'] == 62
    assert audit['unique'] is True  # historical mutual decision, NOT user-rule permission
    assert audit['duplicate_count'] == 0
    assert audit['worst_dot_overlap'] <= 0.70
    assert audit['worst_forward_overlap'] >= audit['worst_dot_overlap']
    assert audit['worst_spearman_full_footprint'] <= 0.90
    assert 'mutual' in audit['overlap_definition']
    stop = json.loads((ROOT / 'evidence/literal_overlap_stop.json').read_text())
    assert len(stop['archive_checks']) == 3
    assert all(r['forward_overlap_within_3px'] == 1.0
               and r['duplicate_under_user_rule'] for r in stop['archive_checks'])
    assert stop['new_surface_checked'] is stop['new_final_dots_checked'] is False


def test_historical_tiff_still_matches_old_card_and_is_binary():
    current = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert current['raster_sha256'] is current['submission_name'] is None
    assert current['download_ok'] is current['submit_recommended'] is False
    archived = json.loads((ROOT / 'evidence/phase4/run_card.json').read_text())
    path = ROOT / 'docs/downloads' / (archived['submission_name'] + '.tif')
    with rasterio.open(path) as src:
        a = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert (src.height, src.width) == (3730, 3292)
        assert str(src.crs) == 'EPSG:32611'
    vals = np.unique(a)
    assert set(np.round(vals, 6)).issubset({0.0, 1.0})
    assert int((a > 0).sum()) == 37654
    assert np.isfinite(a).all()


def test_no_historical_projection_is_current_score():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['organizer_confirmed_score'] is None
    audit = json.loads((ROOT / 'evidence/h33_audit.json').read_text())
    assert audit['organizer_confirmed_scores'] is None
    assert audit['files']['h33']['positive_pixels'] == 37654
    assert audit['comparisons']['h27_to_h33']['removed'] == 2545
