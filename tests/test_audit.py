"""Shared-tool audits and the release contract on the current evidence."""
import json
from pathlib import Path
import sys
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit import coverage_report, check_template, sha
from gems57 import grid, uniqueness


def test_template_is_pinned_with_reported_fix():
    assert check_template()['ok']
    pin = json.loads((ROOT / 'registry/template_pin.json').read_text())
    assert pin['all_identical'] is False
    fixed = [f for f in pin['files'] if f['file'] == 'uniqueness.py'][0]
    assert fixed['identical_to_template'] is False
    assert 'binary' in fixed['fix_note']


def test_bridge_identities_and_grid():
    assert sha(ROOT / 'data/bridge/sample_submission.tif') == grid.SHA256_SAMPLE_SUBMISSION
    assert sha(ROOT / 'data/bridge/existing_faults.tif') == grid.SHA256_EXISTING_FAULTS
    g = grid.load_grid(ROOT / 'data/bridge')
    assert g.shape == (3730, 3292)
    assert int(g.footprint.sum()) == 5167373


def test_dot_definition_is_binary_not_any_positive():
    fp = np.ones((7, 9), bool)
    binary = np.ones(fp.shape)
    assert coverage_report(binary, fp)['strictly_positive_on_entire_footprint']
    tiny = np.full(fp.shape, np.nextafter(0., 1.))
    assert not coverage_report(tiny, fp)['strictly_positive_on_entire_footprint']
    # dense continuous surfaces have an empty dot set under the corrected rule
    rng = np.random.default_rng(70)
    dense = rng.random(fp.shape) * .9
    candidate = (rng.random(fp.shape) > .8).astype(float)
    assert uniqueness.dot_overlap(candidate, dense) == 0
    assert uniqueness.dot_overlap(candidate, binary) == 1


@pytest.mark.parametrize('missing', [0., -1., np.nan, np.inf])
def test_not_universal_if_any_cell_is_not_a_dot(missing):
    w = np.ones((5, 5)); w[2, 2] = missing
    assert not coverage_report(w, np.ones(w.shape, bool))['strictly_positive_on_entire_footprint']


def test_empty_and_mismatched_footprints_rejected():
    for fp in [np.zeros((3, 3), bool), np.ones((4, 4), bool)]:
        with pytest.raises(ValueError):
            coverage_report(np.ones((3, 3)), fp)


def test_overlap_radius_is_inclusive_euclidean():
    mine = np.zeros((11, 11)); theirs = np.zeros_like(mine)
    mine[5, 5] = 1; theirs[5, 8] = 1
    assert uniqueness.dot_overlap(mine, theirs) == 1
    theirs[:] = 0; theirs[5, 8] = 0.5   # continuous, not a dot
    assert uniqueness.dot_overlap(mine, theirs) == 0
    theirs[:] = 0; theirs[8, 8] = 1
    assert uniqueness.dot_overlap(mine, theirs) == 0


def test_card_does_not_fabricate_missing_evidence():
    card = json.loads((ROOT / 'evidence/history/parallel-review2/run_card.json').read_text())
    assert card['raster_sha256'] is None
    assert card['holdout']['dti'] is None
    assert len(card['note']) <= 140


def test_phase1_negative_is_preserved_without_conversion():
    p1 = json.loads((ROOT / 'evidence/history/phase1_negative/run_card.json').read_text())
    assert p1['verdict'] == 'negative'
    assert p1['holdout_dti']['dti'] == pytest.approx(0.010192889039757751)
    assert p1['organizer_confirmed_score'] is None
