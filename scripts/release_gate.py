#!/usr/bin/env python3
"""Current publication gate: fail closed. No model or release candidate exists."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit import check_template


def status():
    pin_ok = check_template()['ok']
    return dict(status='BLOCKED — DO NOT SUBMIT', verdict='negative',
                generated_tif=None, download_available=False, approved_for_weekly_slot=False,
                scientific_experiments_run=0, submission_slots_used=0,
                template_integrity_ok=pin_ok,
                blockers=[
                    'No single-method lane paragraph was supplied in the brief.',
                    'A hash-verified registry witness is positive at every sample-footprint pixel; the literal any-raster overlap gate rejects every nonempty candidate.',
                    'No fitted model, feature-alone canaries, pooled spatial holdout result, or comparable current-best holdout exists in this repository.',
                    'No current full-registry two-phase uniqueness scan or organizer submission receipt exists for a new GEMSDOE70 candidate.',
                    'The all-finite shared writer is a local precaution; official documentation describes null/NaN outside the footprint. Organizer acceptance of zero-outside export is unverified here.'
                ] + ([] if pin_ok else ['Shared template integrity FAILED.']),
                policy='Negative-only publication. A future positive release requires an explicitly resolved protocol and a separately reviewed evidence-bound gate; editing a run-card verdict cannot enable a download.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expect-negative', action='store_true', help='For CI: succeed when the expected blocked state is enforced.')
    args = ap.parse_args()
    result = status()
    (ROOT / 'evidence/release-status.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if args.expect_negative and result['template_integrity_ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
