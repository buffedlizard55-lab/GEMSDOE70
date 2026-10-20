"""Concurrent artifacts are preserved, not advertised as validated predictions."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[1]

def test_archival_bytes_and_no_public_artifact():
    report=json.loads((ROOT/'evidence/concurrent_h70c_quarantine.json').read_text())
    assert report['status'].startswith('QUARANTINED')
    for row in report['artifacts']:
        p=ROOT/row['path']
        assert p.is_file()
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    from gems70.release_e3 import released_filenames
    public={p.name for p in (ROOT/'docs').rglob('*') if p.is_file() and p.suffix.lower() in {'.tif','.zip'}}
    assert public==released_filenames(ROOT)  # only the hash-bound E3 candidate; quarantine stays unpublished
    source=(ROOT/'quarantine/concurrent-h70c/source/generate_h70_submission.py.txt').read_text()
    assert 'simulate plausible but label as HOLDOUT' in source
