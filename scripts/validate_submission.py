#!/usr/bin/env python3
"""Run shared byte-level format validation only; NEVER authorizes a submission slot."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'vendor'), str(ROOT / 'scripts')]
from audit import check_template, sha
from gems57 import grid, gates
from gems57.validate import validate


def json_safe(value):
    """Encode nonfinite *report metadata*, never repair raster predictions."""
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def run_validation(path):
    report = dict(evidence_class='LOCAL-FORMAT-VALIDATION-NOT-ORGANIZER-ACCEPTANCE',
                  artifact_sha256=None, approved_for_weekly_slot=False,
                  warning='Format checks do not establish novelty, geological accuracy, improvement, or organizer acceptance.')
    try:
        if not check_template()['ok']:
            raise ValueError('shared tools differ from pinned template')
        bridge = ROOT / 'data/bridge'
        for name, pin in [('sample_submission.tif', grid.SHA256_SAMPLE_SUBMISSION),
                          ('existing_faults.tif', grid.SHA256_EXISTING_FAULTS)]:
            if sha(bridge / name) != pin:
                raise ValueError(f'{name}: mirror integrity mismatch')
        g = grid.load_grid(bridge)
        report['artifact_sha256'] = sha(path)
        report['sample_comparison'] = gates.format_report(path, bridge / 'sample_submission.tif', footprint=g.footprint)
        report['shared_validator'] = validate(path, g.footprint, g.catalogue)
        report['local_format_pass'] = bool(report['shared_validator']['all_checks_passed'] and report['sample_comparison']['ok'])
    except (OSError, ValueError, TypeError) as exc:
        report['local_format_pass'] = False
        report['error'] = str(exc)
    return json_safe(report)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('tif', type=Path)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    report = run_validation(args.tif)
    text = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text)
    return 0 if report['local_format_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
