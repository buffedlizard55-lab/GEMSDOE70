#!/usr/bin/env python3
"""Compatibility CLI for the publication/release contract (two independent flags)."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from audit import check_template
from gems70.release import release_status


def status():
    result = release_status(ROOT)
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    download_ok = bool(result['download_ok'])
    return {**result,
            'status': ('REVIEW ONLY — LITERAL LANE STOP' if result.get('literal_lane_status', {}).get('stop_required')
                       else 'DOWNLOADABLE — NOT PROMOTED' if download_ok and not result['submit_recommended']
                       else 'PROMOTED' if result['submit_recommended'] else 'BLOCKED'),
            'download_available': download_ok,
            'generated_tif': result.get('artifact') if download_ok else None,
            'approved_for_weekly_slot': bool(result['submit_recommended']),
            'scientific_experiments_run': card.get('experiment_count'),
            'submission_slots_used': card.get('weekly_slots_used'),
            'template_integrity_ok': check_template()['ok']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expect-negative', action='store_true')
    args = ap.parse_args()
    result = status()
    (ROOT / 'evidence/release-status.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not args.expect_negative:
        return 0 if result.get('approved_for_weekly_slot') is True else 2
    # '--expect-negative' now means: verdict negative, NOT promoted, no slot used.
    # A downloadable (non-promoted) artifact is the expected state of this repo.
    expected = (result.get('verdict') == 'negative'
                and result.get('download_and_submit_ok') is False
                and result.get('submit_recommended') is False
                and result.get('approved_for_weekly_slot') is False
                and bool(result.get('reasons')))
    return 0 if expected and result['template_integrity_ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
