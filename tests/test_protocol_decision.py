"""A proposed representation change is never a release authorization."""
from pathlib import Path

from gems70.release import release_status

ROOT = Path(__file__).resolve().parents[1]


def test_unresolved_decision_is_visible_but_does_not_release():
    memo = (ROOT / 'docs/protocol-decision.md').read_text()
    site = (ROOT / 'docs/protocol-decision.html').read_text()
    overview = (ROOT / 'docs/index.html').read_text()
    assert 'DO NOT SUBMIT' in memo
    assert 'not current policy' in memo
    assert 'shared template' in memo
    assert 'protocol-decision.html' in overview
    assert 'DO NOT SUBMIT' in site
    assert release_status(ROOT)['download_and_submit_ok'] is False
