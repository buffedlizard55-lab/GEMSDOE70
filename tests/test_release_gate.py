"""A historical archive is never an eligible new submission."""
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


def test_real_card_never_promotes_a_format_valid_archived_tiff():
    result = release_status(ROOT)
    assert result['evidence_consistent'] is True
    assert result['download_ok'] is result['submit_recommended'] is False
    assert result['download_and_submit_ok'] is False
    assert result['verdict'] == 'negative'
    assert result['artifact'] is result['artifact_sha256'] is None
    archive = result['archive_review']
    assert archive['file'].endswith('.tif')
    assert archive['forward_overlap_within_3px'] == 1.0
    assert archive['submit_ok'] is False
    assert archive['download_for_research_only'] is True


@pytest.mark.parametrize('key, value', [
    ('download_ok', True), ('submit_recommended', True),
    ('download_and_submit_ok', True), ('verdict', 'promote'),
    ('raster_sha256', '0' * 64), ('organizer_confirmed_score', .5),
    ('weekly_slots_used', 1), ('submission_name', 'old-raster'),
])
def test_malicious_card_flag_cannot_turn_an_archive_into_a_release(monkeypatch, key, value):
    import gems70.release as release
    original = release._load
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    card[key] = value
    monkeypatch.setattr(release, '_load',
                        lambda root, rel: card if rel == 'evidence/run_card.json'
                        else original(root, rel))
    result = release_status(ROOT)
    assert not result['evidence_consistent']
    assert not result['download_ok'] and not result['submit_recommended']


def test_missing_or_corrupt_artifact_is_closed(tmp_path):
    (tmp_path / 'evidence' / 'phase4').mkdir(parents=True)
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    card['raster_sha256'] = '0' * 64
    (tmp_path / 'evidence/run_card.json').write_text(json.dumps(card))
    (tmp_path / 'evidence/phase4/run_card.json').write_text(json.dumps(card))
    result = release_status(tmp_path)
    assert result['download_ok'] is False
    assert result['submit_recommended'] is False
    assert result['evidence_consistent'] is False


@pytest.mark.parametrize('change, expected', [
    ({}, 0), ({'download_ok': True}, 2), ({'verdict': 'promote'}, 2),
    ({'download_and_submit_ok': True}, 2), ({'submit_recommended': True}, 2),
    ({'approved_for_weekly_slot': True}, 2), ({'reasons': []}, 2),
    ({'evidence_consistent': False}, 2), ({'archive_review': None}, 2),
    ({'template_integrity_ok': False}, 2),
])
def test_expected_negative_cli_checks_actual_result(tmp_path, monkeypatch, change, expected):
    (tmp_path / 'evidence').mkdir()
    result = dict(verdict='negative', download_and_submit_ok=False,
                  download_ok=False, submit_recommended=False,
                  download_available=False, generated_tif=None,
                  approved_for_weekly_slot=False, reasons=['Stopped experiment'],
                  evidence_consistent=True, archive_review={'submit_ok': False},
                  submission_slots_used=0, template_integrity_ok=True)
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
