"""Release diagnostics must keep download permission and promotion independent."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from gems70.release import release_status, valid_canary

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('release_gate_cli', ROOT / 'scripts/release_gate.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


@pytest.mark.parametrize('auc', [float('nan'), float('inf'), -float('inf'), -1, 2, True, None, '0.5', .91, .09])
def test_invalid_canaries(auc):
    assert not valid_canary({'auc': auc, 'suspected_leakage': False})


@pytest.mark.parametrize('auc', [.1, .5, .9])
def test_valid_canaries(auc):
    assert valid_canary({'auc': auc, 'suspected_leakage': False})


@pytest.mark.parametrize('value', [None, [], 1, {}, {'auc': .5, 'suspected_leakage': True}])
def test_malformed_canaries(value):
    assert not valid_canary(value)


def test_real_card_separates_download_from_promotion():
    result = release_status(ROOT)
    assert result['download_ok'] is True
    assert result['submit_recommended'] is False
    assert result['download_and_submit_ok'] is False
    assert result['verdict'] == 'negative'
    assert result['artifact_sha256']
    assert any("B'" in r or 'B' in r for r in result['reasons'])


def test_missing_or_corrupt_artifact_is_closed(tmp_path):
    (tmp_path / 'evidence' / 'phase4').mkdir(parents=True)
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    card['raster_sha256'] = '0' * 64
    (tmp_path / 'evidence/run_card.json').write_text(json.dumps(card))
    (tmp_path / 'evidence/phase4/run_card.json').write_text(json.dumps(card))
    result = release_status(tmp_path)
    assert result['download_ok'] is False
    assert result['submit_recommended'] is False


@pytest.mark.parametrize('change, expected', [
    ({}, 0), ({'download_ok': True}, 0), ({'verdict': 'promote'}, 2),
    ({'download_and_submit_ok': True}, 2), ({'submit_recommended': True}, 2),
    ({'approved_for_weekly_slot': True}, 2), ({'reasons': []}, 2),
    ({'template_integrity_ok': False}, 2),
])
def test_expected_negative_cli_checks_actual_result(tmp_path, monkeypatch, change, expected):
    (tmp_path / 'evidence').mkdir()
    result = dict(verdict='negative', download_and_submit_ok=False,
                  download_ok=False, submit_recommended=False,
                  download_available=False, generated_tif=None,
                  approved_for_weekly_slot=False, reasons=['Stopped experiment'],
                  template_integrity_ok=True)
    result.update(change)
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    monkeypatch.setattr(cli, 'status', lambda: result)
    monkeypatch.setattr(sys, 'argv', ['release_gate.py', '--expect-negative'])
    assert cli.main() == expected
    assert json.loads((tmp_path / 'evidence/release-status.json').read_text()) == result


def test_default_cli_never_authorizes_submission(tmp_path, monkeypatch):
    (tmp_path / 'evidence').mkdir()
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    monkeypatch.setattr(cli, 'status', lambda: {'template_integrity_ok': True})
    monkeypatch.setattr(sys, 'argv', ['release_gate.py'])
    assert cli.main() == 2


def promotion_fixture(tmp_path):
    import shutil
    for rel in ('evidence/phase4', 'evidence/phase2', 'docs/downloads'):
        shutil.copytree(ROOT / rel, tmp_path / rel)
    card_path = tmp_path / 'evidence/phase4/run_card.json'
    card = json.loads(card_path.read_text())
    card.update(download_and_submit_ok=True, verdict='promote',
                gate_a_candidate_ge_h33=True,
                gate_b_prime_candidate_gt_h33_significant=True)
    card_path.write_text(json.dumps(card))
    audit_path = tmp_path / 'evidence/phase4/uniqueness.json'
    audit = json.loads(audit_path.read_text())
    for row in audit['rows']:
        row['my_dots_within_3px_of_theirs'] = .2
        row['spearman_full_footprint'] = .1
    audit_path.write_text(json.dumps(audit))
    return card_path, audit_path


@pytest.mark.parametrize('gate', ['gate_a_candidate_ge_h33',
                                  'gate_b_prime_candidate_gt_h33_significant'])
def test_stale_promotion_cannot_override_scientific_gate(tmp_path, gate):
    card_path, _ = promotion_fixture(tmp_path)
    assert release_status(tmp_path)['submit_recommended']
    card = json.loads(card_path.read_text())
    card[gate] = False
    card_path.write_text(json.dumps(card))
    assert not release_status(tmp_path)['submit_recommended']


def test_stale_promotion_cannot_override_canary(tmp_path):
    promotion_fixture(tmp_path)
    (tmp_path / 'evidence/phase2/canaries.json').write_text(
        json.dumps({'bad': {'auc': .99, 'suspected_leakage': True}}))
    assert not release_status(tmp_path)['submit_recommended']


@pytest.mark.parametrize('overlap', [.70001, None, float('nan'), '0.2', True])
def test_literal_forward_rule_overrides_mutual_clearance(tmp_path, overlap):
    _, audit_path = promotion_fixture(tmp_path)
    audit = json.loads(audit_path.read_text())
    audit['rows'][0]['my_dots_within_3px_of_theirs'] = overlap
    audit_path.write_text(json.dumps(audit))
    result = release_status(tmp_path)
    assert result['download_ok']
    assert not result['submit_recommended']
    assert any('forward-overlap' in r for r in result['reasons'])
