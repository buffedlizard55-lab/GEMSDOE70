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
    assert card['submission_name'] is None and card['raster_sha256'] is None
    archived = json.loads((ROOT / 'evidence/phase4/run_card.json').read_text())
    assert f"docs/downloads/{archived['submission_name']}.tif" in paths
    source = (ROOT / 'quarantine/concurrent-h70c/source/generate_h70_submission.py.txt').read_text()
    assert 'simulate plausible but label as HOLDOUT' in source
