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
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    assert result['download_ok'] is True
    # The promoted supervised lane should have submit_recommended True; legacy negative had False
    assert result['submit_recommended'] == bool(card.get('download_and_submit_ok'))
    assert result['download_and_submit_ok'] == bool(card.get('download_and_submit_ok'))
    assert result['verdict'] == card.get('verdict')
    assert result['artifact_sha256']
    # Reasons may be empty for promoted, or contain gate failures for negative
    if card.get('verdict')=='negative':
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
