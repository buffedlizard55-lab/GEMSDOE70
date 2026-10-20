"""Literal policy tests: shared measurements cannot be waived by mutual overlap."""
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

from gems57 import uniqueness
from gems70.protocol import literal_lane_status
from gems70.release import release_status

ROOT = Path(__file__).resolve().parents[1]


def audit(forward=.70, rho=.90, **extra):
    row = {'submission': 'toy', 'my_dots_within_3px_of_theirs': forward,
           'spearman_full_footprint': rho, 'mutual_overlap': 0.01,
           'duplicate_by_overlap': False, 'duplicate_by_rho': False, **extra}
    return {'rows': [row], 'complete_accessible_scan': True,
            'registry_rasters_expected': 1, 'source_errors': []}


def test_literal_thresholds_use_or_and_strict_exceedance():
    assert literal_lane_status(audit())['protocol_unique']
    for a in [audit(.700000001, 0), audit(0, .900000001),
              audit(.99, -.9), audit(identical_bytes=True),
              audit(identical_decoded_predictions=True)]:
        result = literal_lane_status(a)
        assert result['stop_required'] and not result['protocol_unique']


@pytest.mark.parametrize('value', [None, True, '0.5', -1, 2, float('nan'), float('inf')])
def test_invalid_measurements_fail_closed(value):
    assert not literal_lane_status(audit(value, .1))['protocol_unique']


@pytest.mark.parametrize('value', [None, True, '0.5', -2, 2, float('nan'), float('inf')])
def test_invalid_correlation_fails_closed(value):
    assert not literal_lane_status(audit(.1, value))['protocol_unique']


def test_subset_pass_is_not_unique_but_positive_witness_stops():
    a = audit(.5, .1); a['complete_accessible_scan'] = False
    assert not literal_lane_status(a)['protocol_unique']
    a['rows'][0]['my_dots_within_3px_of_theirs'] = 1
    assert literal_lane_status(a)['stop_required']
    for invalid in [None, {}, [], {'rows': []}, {'rows': [1]}]:
        assert not literal_lane_status(invalid)['protocol_unique']
    a = audit(.1, .1); a['registry_rasters_expected'] = 2
    assert not literal_lane_status(a)['protocol_unique']


def test_small_reverse_overlap_cannot_cancel_shared_forward_measurement():
    theirs = np.zeros((25, 25), np.float32); theirs[::5, ::5] = 1
    mine = np.zeros_like(theirs); mine[10, 11] = 1
    forward = uniqueness.dot_overlap(mine, theirs)
    reverse = uniqueness.dot_overlap(theirs, mine)
    assert forward == 1 and reverse < .7
    assert literal_lane_status(audit(forward, 0))['stop_required']


def test_fixed_mass_pigeonhole_bound_is_conservative_synthetic_oracle():
    theirs = np.zeros((20, 20), np.float32); theirs[::5, ::5] = 1
    covered = ndi.distance_transform_edt(theirs != 1) <= 3
    uncovered = np.flatnonzero(~covered)
    count = 100
    # Deliberately put as many as possible outside the halo, then inside it.
    selected = np.concatenate([uncovered, np.flatnonzero(covered)])[:count]
    mine = np.zeros_like(theirs); mine.flat[selected] = 1
    bound = max(0, 1 - len(uncovered) / count)
    assert uniqueness.dot_overlap(mine, theirs) == pytest.approx(bound)


def test_fresh_review_binds_every_archived_final_file_and_does_not_claim_universal():
    from gems70.release import digest
    review = json.loads((ROOT / 'evidence/review/literal_protocol_audit.json').read_text())
    cert = review['shared_saturation_certificate']
    assert not cert['universal_overlap_blocker']
    assert cert['uncovered_allowed_pixels'] == 6649
    assert cert['allowed_pixels'] == 5167373
    assert review['minimum_forward_overlap_at_fixed_budget'] == pytest.approx(1 - 6649 / 37654)
    assert review['minimum_forward_overlap_at_fixed_budget'] > .70
    inv = json.loads((ROOT / 'registry/published_artifacts.json').read_text())
    expected = {r['path'] for r in inv['artifacts'] if r['path'].endswith('.tif')}
    assert {r['artifact'] for r in review['archived_artifacts']} == expected
    for row in review['archived_artifacts']:
        assert digest(ROOT / row['artifact']) == row['raster_sha256']
        assert literal_lane_status(row['shared_measurements'])['stop_required']
        assert row['literal_lane_status']['protocol_unique'] is False
        assert row['validator_output']['all_checks_passed']
    card = json.loads((ROOT / 'evidence/review/run_card.json').read_text())
    assert card['raster_sha256'] is None and card['validator_output'] is None
    assert card['holdout_dti']['dti'] is None and card['holdout_dti']['ci95'] is None
    assert card['weekly_slots_used'] == 0 and card['new_scientific_experiments'] == 0
    assert card['verdict'] == 'negative' and len(card['submission_note']) <= 140


def test_release_reports_forensic_download_not_protocol_uniqueness():
    status = release_status(ROOT)
    assert status['download_ok']
    assert status['literal_lane_status']['stop_required']
    assert status['protocol_unique'] is False
    assert status['submit_recommended'] is False
    assert 'review only' in status['download_scope']


def test_promote_flag_alone_cannot_waive_literal_gate(tmp_path):
    import shutil
    for name in ['phase4/run_card.json', 'phase4/uniqueness.json', 'phase2/canaries.json']:
        p = tmp_path / 'evidence' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'evidence' / name, p)
    path = tmp_path / 'evidence/phase4/run_card.json'
    card = json.loads(path.read_text())
    card.update(verdict='promote', download_and_submit_ok=True,
                gate_a_candidate_ge_h33=True, gate_b_prime_candidate_gt_h33_significant=True)
    path.write_text(json.dumps(card))
    artifact = f"docs/downloads/{card['submission_name']}.tif"
    (tmp_path / artifact).parent.mkdir(parents=True)
    shutil.copyfile(ROOT / artifact, tmp_path / artifact)
    result = release_status(tmp_path)
    assert result['download_ok']
    assert result['submit_recommended'] is False


def test_current_pages_have_unambiguous_review_only_banner():
    for page in ['index.html', 'executive-summary.html', 'submission.html', 'protocol-review.html',
                 'results.html', 'h33-analysis.html']:
        text = (ROOT / 'docs' / page).read_text()
        assert 'DO NOT SUBMIT' in text
        assert 'review_run_card.json' in text
    executive = (ROOT / 'docs/executive-summary.html').read_text()
    assert 'http-equiv="refresh"' not in executive
    assert 'live submission-page cap' in executive
    assert 'Download archived TIFF' in executive
