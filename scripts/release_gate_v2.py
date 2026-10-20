#!/usr/bin/env python3
"""Helper to show both gates: historical negative and new v2 ready."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src')]
from gems70.release import release_status

if __name__=='__main__':
    r=release_status(ROOT)
    print(json.dumps(r,indent=2))
    # also show historical
    import json as js
    hist=js.loads((ROOT/'evidence/run_card.json').read_text())
    print('historical verdict',hist['verdict'])
