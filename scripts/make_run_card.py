#!/usr/bin/env python3
"""Compatibility verifier: never overwrite the scientific run with an older preflight card.

The earlier review-only generator is preserved in
 evidence/history/parallel-review2/make_run_card.py.txt.
"""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from gems70.release import digest

def main():
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    assert card['verdict']=='negative'
    assert card['download_and_submit_ok'] is False
    assert card['raster_sha256'] and len(card['raster_sha256'])==64
    from gems70.release import digest as _d
    assert _d(ROOT/card['raster_file'])==card['raster_sha256']
    assert card['holdout_dti']['evidence_class']=='HOLDOUT-DTI'
    for rel,pin in card['method_source_sha256'].items():
        if digest(ROOT/rel)!=pin: raise ValueError('scientific source changed: '+rel)
    print('Verified existing run card (negative verdict, hash-bound research TIFF); no evidence overwritten.')
if __name__=='__main__':main()
