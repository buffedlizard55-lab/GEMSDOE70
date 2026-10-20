"""Current forward stop cannot be bypassed by a historical mutual pass."""
import json
from pathlib import Path
import pytest
from gems70.protocol import strict_gate
from gems70.release import release_status

ROOT = Path(__file__).resolve().parents[1]


def audit(rho=.2, overlap=.1):
    return {'complete_accessible_scan': True, 'registry_rasters_expected': 1,
            'rows': [{'submission': 'witness', 'sha256': 'a'*64,
                      'spearman_full_footprint': rho,
                      'my_dots_within_3px_of_theirs': overlap,
                      'their_dots_within_3px_of_mine': .01}]}


@pytest.mark.parametrize('rho,overlap,stop', [(.9,.7,False),(.900001,0,True),
    (0,.700001,True),(-.99,.1,False),(0,1,True)])
def test_exact_stated_thresholds(rho, overlap, stop):
    assert strict_gate(audit(rho, overlap))['stop_required'] is stop


@pytest.mark.parametrize('bad', [None, True, '0.3', float('nan'), float('inf'), -2, 2])
def test_invalid_measurements_fail_closed(bad):
    assert strict_gate(audit(bad,.1))['stop_required']
    assert strict_gate(audit(.1,bad))['stop_required']


def test_missing_inventory_fails_closed():
    assert strict_gate({})['stop_required']
    a = audit(); a['registry_rasters_expected'] = 2
    assert strict_gate(a)['stop_required']
    a = audit(); a['source_errors'] = ['inaccessible']
    assert strict_gate(a)['stop_required']


def test_historical_failure_is_not_unique_submission_clearance():
    card = json.loads((ROOT/'evidence/current_protocol_review.json').read_text())
    assert card['correlation_overlap_vs_registry']['stop_required']
    assert card['correlation_overlap_vs_registry']['witnesses']
    assert not card['new_tif_generated']
    assert card['validator_output']['all_pass']
    assert len(card['submission_note']) <= 140
    result = release_status(ROOT)
    assert result['review_only'] is True
    assert result['current_forward_protocol_ok'] is False
    assert result['submit_recommended'] is False


def test_site_warning_and_protocol_card_are_published():
    for name in ('index.html', 'submission.html', 'executive-summary.html'):
        text = (ROOT/'docs'/name).read_text()
        if name == 'executive-summary.html':
            assert 'submission.html' in text  # legacy redirect
        else:
            assert 'CURRENT PROTOCOL: DO NOT SUBMIT.' in text
            assert 'protocol-review.html' in text
    assert json.loads((ROOT/'docs/current_protocol_review.json').read_text()) == json.loads(
        (ROOT/'evidence/current_protocol_review.json').read_text())


@pytest.mark.parametrize('bad', [None, [], {'rows': None}, {'rows': [None]}, {'rows': ['x']}])
def test_malformed_inventory_is_a_closed_gate(bad):
    assert strict_gate(bad)['stop_required']


def test_current_card_reproduces_from_actual_tiff_bytes():
    import runpy
    module = runpy.run_path(str(ROOT/'scripts/audit_current_protocol.py'))
    assert module['build'](ROOT) == json.loads((ROOT/'evidence/current_protocol_review.json').read_text())
