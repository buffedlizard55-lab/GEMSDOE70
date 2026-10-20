#!/usr/bin/env python3
"""Fail on unsafe legacy-root Pages sources or built output; never creates a TIFF."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems70.pages_policy import check_source, check_output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, help='Also inspect the actual Jekyll build directory')
    args = parser.parse_args()
    try:
        report = check_source(ROOT)
        if args.site is not None:
            inventory = json.loads((ROOT / 'registry/published_artifacts.json').read_text())
            allowed = {r['path']: r['sha256'] for r in inventory['artifacts']}
            report.update(check_output(args.site, allowed_artifacts=allowed))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
        # Surface diagnostics via the Checks API even when log-download hosts
        # are unavailable to the review environment.
        message = str(exc).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print('::error title=Unsafe Pages publication::' + message)
        return 2
    print(json.dumps({'ok': True, **report}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
