#!/usr/bin/env python3
"""Verify the canonical run card instead of overwriting it with an older schema.

Supports the stopped-current-run card and archived E1/E2/Phase-4 cards.
Never silently turns a missing holdout or a historical TIFF into a new score.
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
    if card.get('schema_version') == 2:
        stop = json.loads((ROOT / 'evidence/literal_overlap_stop.json').read_text())
        assert card['verdict'] == stop['verdict'] == 'negative'
        assert card['experiment_count'] == card['weekly_slots_used'] == 0
        assert card['lane']['status'] == 'UNASSIGNED'
        assert card['holdout_dti']['dti'] is card['holdout_dti']['ci95'] is None
        assert card['raster_sha256'] is card['submission_name'] is card['submission_note'] is None
        assert card['download_ok'] is card['submit_recommended'] is False
        assert card['organizer_confirmed_score'] is None
        archived = stop['archive_checks'][0]
        assert archived['sha256'] == card['correlation_overlap_vs_registry']['archived_p4_file_sha256']
        assert archived['forward_overlap_within_3px'] == card['correlation_overlap_vs_registry']['archived_p4_forward_dot_overlap_3px']
    elif 'holdout_dti' in card:
        assert card['holdout_dti']['evidence_class'].startswith('HOLDOUT-DTI')
    else:
        # Historical Phase-4 schema: labelled instruments, not organizer-confirmed.
        assert card.get('organizer_confirmed_score') is None
        assert 'instrument_a_holdout' in card and 'instrument_b_prime_proxy' in card
        assert len(card.get('submission_note', '')) <= 140
    for rel, pin in (card.get('method_source_sha256') or {}).items():
        if digest(ROOT / rel) != pin:
            raise ValueError('scientific source changed: ' + rel)
    if card.get('raster_sha256'):
        tif = ROOT / 'docs/downloads' / (card['submission_name'] + '.tif')
        if not tif.is_file() or digest(tif) != card['raster_sha256']:
            raise ValueError('published TIFF does not match the run card')
    print('Verified existing run card and (if present) its published artifact.')


if __name__ == '__main__':
    main()
