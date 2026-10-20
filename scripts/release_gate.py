#!/usr/bin/env python3
"""Compatibility CLI for the single canonical stopped-run publication gate."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from audit import check_template
from gems70.release import release_status


def status():
    result=release_status(ROOT)
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    tif=ROOT/card['raster_file'] if card.get('raster_file') else None
    return {**result,'status':'OK TO SUBMIT' if result['download_and_submit_ok'] else 'BLOCKED — DO NOT SUBMIT (research download only)',
            'generated_tif':tif.name if tif else None,
            'download_available':bool(result.get('download_research_ok')),'approved_for_weekly_slot':False,
            'scientific_experiments_run':card['experiment_count'],
            'submission_slots_used':card['weekly_slots_used'],
            'template_integrity_ok':check_template()['ok']}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expect-negative',action='store_true')
    args=ap.parse_args()
    result=status()
    (ROOT/'evidence/release-status.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if args.expect_negative and result['template_integrity_ok'] else 2
if __name__=='__main__':raise SystemExit(main())
