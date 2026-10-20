"""Malformed evidence must remain diagnostic and cannot imply validation."""
import json
from pathlib import Path

import pytest

from gems70.release import release_status, valid_canary

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('auc', [10**1000, -(10**1000)])
def test_arbitrary_precision_auc_rejected_without_overflow(auc):
    assert valid_canary({'auc': auc, 'suspected_leakage': False}) is False


@pytest.mark.parametrize('claim', ['true', 'false', 1, [True], {'verified': True}])
def test_best_requires_literal_boolean(tmp_path, claim):
    # Include source and preregistration so unrelated missing-file errors cannot
    # conceal the diagnostic under test. No scientific experiment is executed.
    for relative in ['evidence/run_card.json', 'evidence/holdout.json',
                     'evidence/canaries.json', 'evidence/surface_uniqueness.json',
                     'evidence/experiment_manifest.json', 'docs/hypotheses.md',
                     'src/gems70/method.py', 'scripts/run_experiment.py']:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    card_path = tmp_path / 'evidence/run_card.json'
    card = json.loads(card_path.read_text())
    card['holdout_dti']['current_best_verified'] = claim
    card_path.write_text(json.dumps(card))
    status = release_status(tmp_path)
    assert status['download_and_submit_ok'] is False
    assert 'Comparable current holdout best has not been beaten.' in status['reasons']
    assert not any('Missing or invalid evidence' in r for r in status['reasons'])
