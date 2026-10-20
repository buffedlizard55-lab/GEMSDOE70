"""The current prompt must not be weakened by the historical mutual gate."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('literal_audit', ROOT / 'scripts/audit_literal_protocol.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def audit(rho=0, overlap=0):
    return {'rows': [{'submission': 'witness.tif', 'spearman_full_footprint': rho,
                      'my_dots_within_3px_of_theirs': overlap}],
            'complete_accessible_scan': True, 'missing_or_invalid': 0,
            'registry_rasters_expected': 1}


def test_thresholds_are_strict_and_forward_only():
    assert not module.literal_gate(audit(.90, .70))['stop']
    assert module.literal_gate(audit(0, .700001))['duplicate']
    assert module.literal_gate(audit(.900001, 0))['duplicate']
    assert not module.literal_gate(audit(-.99, 0))['stop']


def test_fail_closed_for_missing_nonfinite_and_wrong_type():
    assert module.literal_gate({})['stop']
    for value in (None, True, float('nan'), float('inf'), -1, 1.01):
        assert module.literal_gate(audit(overlap=value))['stop']
    incomplete = audit()
    incomplete['registry_rasters_expected'] = 2
    assert module.literal_gate(incomplete)['stop']
    missing_name = audit(overlap=.8)
    del missing_name['rows'][0]['submission']
    assert module.literal_gate(missing_name)['stop']
    malformed_row = audit()
    malformed_row['rows'] = [None]
    assert module.literal_gate(malformed_row)['stop']


def test_current_card_is_negative_and_does_not_invent_experiment():
    card = json.loads((ROOT / 'evidence/literal_protocol_review.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['submit_recommended'] is False
    assert card['new_candidate_generated'] is False
    assert card['correlation_overlap_vs_registry']['duplicate'] is True
    assert len(card['note']) <= 140
    assert card['holdout']['withheld_positive_pixels'] == 11321


def test_generated_pages_show_current_stop():
    for name in ('index.html', 'submission.html', 'results.html', 'protocol-review.html'):
        text = (ROOT / 'docs' / name).read_text()
        assert 'DO NOT SUBMIT — literal protocol stop' in text
    readme = (ROOT / 'README.md').read_text()
    assert 'CURRENT STATUS: DO NOT SUBMIT' in readme
    assert 'Download the archived Phase-4 TIFF for review only' in readme
    assert 'Do not upload this TIFF' in readme
    assert 'A unique, format-validated competition TIFF is published' not in readme
    home = (ROOT / 'docs/index.html').read_text()
    assert 'Download archived TIFF (review only)' in home
    assert 'Download submission TIFF' not in home
    assert 'fails the current literal' in (ROOT / 'docs/submission.html').read_text()
    card = json.loads((ROOT / 'evidence/literal_protocol_review.json').read_text())
    assert card['surface_check']['status'] == 'not_run'


def test_release_api_enforces_current_stop():
    from gems70.release import release_status
    status = release_status(ROOT)
    assert status['submit_recommended'] is False
    assert status['download_for_review_only'] is True
    assert status['literal_uniqueness_stop'] is True
    assert status['download_purpose'] == 'review only'
    assert any('literal one-way' in reason for reason in status['reasons'])
