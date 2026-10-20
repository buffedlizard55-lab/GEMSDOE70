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
    # v2 validated submission is whitelisted; only quarantined TIFFs must stay hidden
    allowed = {'docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif','docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.zip'}
    assert set(p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').rglob('*.tif')) == {'docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif'}
    assert set(p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').rglob('*.zip')) == {'docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.zip'}
    # ensure unexpected TIFFs (quarantined) not in docs
    assert not any('quarantine' in str(pp) for pp in (ROOT/'docs').rglob('*.tif'))
    source=(ROOT/'quarantine/concurrent-h70c/source/generate_h70_submission.py.txt').read_text()
    assert 'simulate plausible but label as HOLDOUT' in source
