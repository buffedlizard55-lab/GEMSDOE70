"""Publication diagnostics must reject invalid evidence, not merely block export."""
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


@pytest.mark.parametrize('document', ['run_card', 'holdout', 'surface_uniqueness', 'experiment_manifest'])
def test_nonobject_evidence_is_reported(tmp_path, document):
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    for name in ['run_card', 'holdout', 'canaries', 'surface_uniqueness', 'experiment_manifest']:
        (evidence / (name + '.json')).write_text((ROOT / 'evidence' / (name + '.json')).read_text())
    (evidence / (document + '.json')).write_text('[]')
    result = release_status(tmp_path)
    assert result['download_and_submit_ok'] is False
    assert any('must be JSON objects' in reason for reason in result['reasons'])


@pytest.mark.parametrize('change', [
    {}, {'verdict': 'promote'}, {'download_and_submit_ok': True},
    {'download_available': True}, {'generated_tif': 'unsafe.tif'},
    {'approved_for_weekly_slot': True}, {'reasons': []}, {'template_integrity_ok': False},
])
def test_expected_negative_cli_checks_actual_result(tmp_path, monkeypatch, change):
    (tmp_path / 'evidence').mkdir()
    result = dict(verdict='negative', download_and_submit_ok=False,
                  download_available=False, generated_tif=None,
                  approved_for_weekly_slot=False, reasons=['Stopped experiment'],
                  template_integrity_ok=True)
    result.update(change)
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    monkeypatch.setattr(cli, 'status', lambda: result)
    monkeypatch.setattr(sys, 'argv', ['release_gate.py', '--expect-negative'])
    assert cli.main() == (0 if not change else 2)
    assert json.loads((tmp_path / 'evidence/release-status.json').read_text()) == result


def test_default_cli_never_authorizes_submission(tmp_path, monkeypatch):
    (tmp_path / 'evidence').mkdir()
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    monkeypatch.setattr(cli, 'status', lambda: {'template_integrity_ok': True})
    monkeypatch.setattr(sys, 'argv', ['release_gate.py'])
    assert cli.main() == 2
