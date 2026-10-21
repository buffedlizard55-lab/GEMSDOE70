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
    frozen = {r['artifact'] for r in review['archived_artifacts']}
    assert len(frozen) >= 6 and frozen < expected  # P5-cover is a *later* separate review.
    # Later, separately reviewed files: P5-cover, and Session-3 files that carry their own
    # literal-lane receipt (evidence/s3/literal_lane.json) with stop_required=True.
    s3 = json.loads((ROOT / 'evidence/s3/literal_lane.json').read_text())['files']
    s3_paths = {f['artifact'] for f in s3.values()}
    for f in s3.values():
        assert f['literal_lane_status']['stop_required'] is True
        assert f['literal_lane_status']['protocol_unique'] is False
        assert digest(ROOT / f['artifact']) == f['raster_sha256']
    s2 = json.loads((ROOT / 'evidence/s2/literal_lane.json').read_text())['files']
    s2_paths = {f['artifact'] for f in s2.values()}
    for f in s2.values():
        assert f['literal_lane_status']['stop_required'] is True
        assert f['literal_lane_status']['protocol_unique'] is False
        assert digest(ROOT / f['artifact']) == f['raster_sha256']
    assert expected - frozen == ({'docs/downloads/gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT.tif',
                                  'docs/downloads/gems70-e6-multimodal-extdomain-loqo-37654-20261020.tif',
                                  'docs/downloads/gems70-p5-loqo-halo-37654-20261020.tif'}
                                 | s3_paths | s2_paths)
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


@pytest.mark.parametrize('damage', ['truthy_string', 'validator_hash', 'validator_summary'])
def test_format_receipt_must_be_literal_true_and_hash_bound(tmp_path, damage):
    from test_release_gate import promotion_fixture
    path, _ = promotion_fixture(tmp_path)
    card = json.loads(path.read_text())
    if damage == 'truthy_string':
        card['validator_output']['checks']['range_0_1_guaranteed'] = 'False'
    elif damage == 'validator_hash':
        card['validator_output']['sha256'] = '0' * 64
    else:
        card['validator_output']['all_checks_passed'] = False
    path.write_text(json.dumps(card))
    result = release_status(tmp_path)
    assert not result['download_ok'] and not result['submit_recommended']


def test_scarp_e3_download_does_not_imply_current_uniqueness():
    from gems70.release_e3 import release_status_e3
    result = release_status_e3(ROOT)
    assert result['download_candidate_ok']  # frozen historical checks unchanged
    assert result['literal_lane_status']['stop_required']
    assert not result['literal_lane_status']['protocol_unique']
    assert not result['slot_authorized'] and not result['download_and_submit_ok']


def test_generator_refuses_witness_drift_before_writing_receipts(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location('review_protocol_cli', ROOT / 'scripts/review_literal_protocol.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, 'ROOT', tmp_path)
    witness = tmp_path / mod.CACHE_PATH
    witness.parent.mkdir(parents=True)
    witness.write_bytes(b'corrupted witness')
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        mod.run()
    assert not (tmp_path / 'evidence/review/run_card.json').exists()


def test_receipt_verification_tolerates_only_non_gate_crossing_spearman_noise():
    import runpy
    verify = runpy.run_path(str(ROOT / 'scripts/review_literal_protocol.py'))['verify_receipt']
    verify({'spearman_full_footprint': -.0004249861963070026},
           {'spearman_full_footprint': -.0004249861963087325})
    for actual, stored in [
        ({'spearman_full_footprint': .9000000000001}, {'spearman_full_footprint': .9}),
        ({'spearman_full_footprint': float('nan')}, {'spearman_full_footprint': .1}),
        ({'my_dots_within_3px_of_theirs': .7}, {'my_dots_within_3px_of_theirs': .70000000001}),
        ({'count': 37654}, {'count': 37655}),
        ({'sha256': 'x'}, {'sha256': 'y'}),
        ({'stop_required': False}, {'stop_required': True}),
        ({'a': True}, {'a': 1}),
    ]:
        with pytest.raises(ValueError, match='Receipt drift'):
            verify(actual, stored)
