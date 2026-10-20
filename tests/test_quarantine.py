"""Concurrent artifacts are preserved, not advertised as validated predictions."""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[1]


def test_archival_bytes_and_no_unauthorised_artifact():
    report = json.loads((ROOT / 'evidence/concurrent_h70c_quarantine.json').read_text())
    assert report['status'].startswith('QUARANTINED')
    for row in report['artifacts']:
        p = ROOT / row['path']
        assert p.is_file()
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256']
    inv = json.loads((ROOT / 'registry/published_artifacts.json').read_text())
    paths = {r['path'] for r in inv['artifacts']}
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert f"docs/downloads/{card['submission_name']}.tif" not in paths
    manifest = json.loads((ROOT / 'quarantine/published-downloads-2026-10-20/manifest.json').read_text())
    assert any(row['file'] == card['submission_name'] + '.tif' for row in manifest['files'])
    source = (ROOT / 'quarantine/concurrent-h70c/source/generate_h70_submission.py.txt').read_text()
    assert 'simulate plausible but label as HOLDOUT' in source
