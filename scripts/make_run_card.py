#!/usr/bin/env python3
"""Verify the canonical run card instead of overwriting it with an older schema.

Supports both schemas present in this repo's history:
- Phase-4 card (evidence/run_card.json): instrument_a_holdout / instrument_b_prime_proxy
- E1/E2-style cards: holdout_dti
Fixes the stale-schema KeyError that left the Verify workflow red on main
(pre-existing before PR #16; recorded in HANDOFF integration notes).
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems70.release import digest


def main():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['verdict'] in {'promote', 'negative'}
    if 'holdout_dti' in card:
        assert card['holdout_dti']['evidence_class'].startswith('HOLDOUT-DTI')
    else:
        # Phase-4 schema: labelled instruments, no organizer-confirmed score.
        assert card.get('organizer_confirmed_score') is None
        assert 'instrument_a_holdout' in card and 'instrument_b_prime_proxy' in card
        assert len(card.get('submission_note', '')) <= 140
    for rel, pin in (card.get('method_source_sha256') or {}).items():
        if digest(ROOT / rel) != pin:
            raise ValueError('scientific source changed: ' + rel)
    if card.get('raster_sha256'):
        name = card['submission_name'] + '.tif'
        tif = ROOT / 'docs/downloads' / name
        hold_path = ROOT / 'evidence/release_hold.json'
        hold = json.loads(hold_path.read_text()) if hold_path.is_file() else {}
        if hold.get('verdict') == 'negative':
            archived = ROOT / hold.get('quarantine_directory', 'quarantine') / name
            if tif.exists() or not archived.is_file() or digest(archived) != card['raster_sha256']:
                raise ValueError('release-held TIFF must be absent from Pages and hash-match quarantine')
        elif not tif.is_file() or digest(tif) != card['raster_sha256']:
            raise ValueError('published TIFF does not match the run card')
    print('Verified existing run card and (if present) its published artifact.')


if __name__ == '__main__':
    main()
