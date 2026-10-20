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
    # Historical card for experiment count; v2 may have separate
    try:
        card=json.loads((ROOT/'evidence/run_card.json').read_text())
    except Exception:
        card={'experiment_count':1,'weekly_slots_used':0}
    # If new v2 is ready, report it as READY; otherwise BLOCKED
    if result.get('download_and_submit_ok') and result.get('verdict')=='promote' and result.get('raster_sha256'):
        return {**result,'status':'READY — VALIDATED TIFF AVAILABLE','generated_tif':result.get('file'),'download_available':True,'approved_for_weekly_slot':False,
                'scientific_experiments_run':card.get('experiment_count',1),'submission_slots_used':card.get('weekly_slots_used',0),'template_integrity_ok':check_template()['ok']}
    return {**result,'status':'BLOCKED — DO NOT SUBMIT','generated_tif':None,
            'download_available':False,'approved_for_weekly_slot':False,
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
