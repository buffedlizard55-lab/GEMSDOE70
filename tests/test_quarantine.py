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
    # Quarantined H70-C bytes must never reappear as downloads (E2 review artifact is unrelated).
    public={p.name for p in (ROOT/'docs').rglob('*') if p.is_file()}
    for row in report['artifacts']:
        assert Path(row['path']).name not in public or 'DO-NOT-SUBMIT' in Path(row['path']).name
    tifs=[p.name for p in (ROOT/'docs').rglob('*.tif')]
    assert len(tifs)==1 and 'DO-NOT-SUBMIT' in tifs[0]
    source=(ROOT/'quarantine/concurrent-h70c/source/generate_h70_submission.py.txt').read_text()
    assert 'simulate plausible but label as HOLDOUT' in source
