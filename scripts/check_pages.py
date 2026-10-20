"""Check the actual Pages boundary; do not confuse unlinked with unpublished.

Read-only by default. --configure sets main:/docs via the GitHub REST API and
then independently reads it back. No branch checkout or competition action.
"""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'repos/buffedlizard55-lab/GEMSDOE70/pages'
EXPECTED_SOURCE = {'branch': 'main', 'path': '/docs'}


def boundary_status(settings):
    if not isinstance(settings, dict):
        return False
    return (settings.get('build_type') == 'legacy'
            and settings.get('source') == EXPECTED_SOURCE
            and settings.get('https_enforced') is True)


def api(*args, payload=None):
    result = subprocess.run(
        ['gh', 'api', ENDPOINT, *args],
        input=None if payload is None else json.dumps(payload),
        capture_output=True, text=True, check=True, timeout=60,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configure', action='store_true')
    args = parser.parse_args(argv)
    try:
        before = api()
        if args.configure and not boundary_status(before):
            api('--method', 'PUT', '--input', '-', payload={
                'build_type': 'legacy', 'source': EXPECTED_SOURCE,
                'https_enforced': True,
            })
        after = api() if args.configure else before
        receipt = {
            'evidence_class': 'PUBLICATION-CONFIGURATION',
            'endpoint': 'https://api.github.com/' + ENDPOINT,
            'before': before, 'after': after,
            'safe_boundary': boundary_status(after),
            'scope': 'Configuration only; not HTTP deployment verification or scientific clearance.',
            'repository_files_remain_public': True,
        }
        if args.configure:
            (ROOT / 'evidence/pages_publication.json').write_text(
                json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))
        return 0 if receipt['safe_boundary'] else 2
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        failure = {'safe_boundary': False, 'error': str(exc),
                   'detail': getattr(exc, 'stderr', None),
                   'scope': 'No successful Pages configuration change verified.'}
        if args.configure:
            (ROOT / 'evidence/pages_publication.json').write_text(
                json.dumps(failure, indent=2) + '\n')
        print(json.dumps(failure, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
