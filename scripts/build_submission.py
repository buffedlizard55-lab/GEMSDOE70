"""Fail-closed entry point for the stopped run; never makes a decoy submission.

The byte-pinned shared writer is vendor/gems57/submission_writer.py. Its real
TIFF/ZIP packaging and range rejection are exercised by tests/test_writer.py.
A fresh successful scientific run and release contract are required before
connecting that writer to publication. This run cannot produce an eligible file.
"""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from gems70.release import release_status
if __name__=='__main__':
    print(json.dumps(release_status(ROOT),indent=2))
    sys.exit(2)
