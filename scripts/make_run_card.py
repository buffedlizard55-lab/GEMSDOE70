#!/usr/bin/env python3
"""Verify the canonical run card instead of overwriting it with an older schema."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems70.release import digest


def main():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['verdict'] in {'promote', 'negative'}
    assert card['holdout_dti']['evidence_class'].startswith('HOLDOUT-DTI')
    for rel, pin in card['method_source_sha256'].items():
        if digest(ROOT / rel) != pin:
            raise ValueError('scientific source changed: ' + rel)
    if card.get('raster_sha256'):
        tif = ROOT / 'docs/downloads' / (card['submission_name'] + '.tif')
        if not tif.is_file() or digest(tif) != card['raster_sha256']:
            raise ValueError('published TIFF does not match the run card')
    print('Verified existing run card and (if present) its published artifact.')


if __name__ == '__main__':
    main()
