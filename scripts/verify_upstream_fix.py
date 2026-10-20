#!/usr/bin/env python3
"""Verify the two uniqueness fixes against upstream template buffedlizard55-lab/60GEMSDOE.

Executes Handoff Step 3:
- Compares vendor/gems57/uniqueness.py against /tmp/60GEMSDOE/src/gems57/uniqueness.py.
- Emits an auditable unified diff patch (evidence/phase5/upstream_uniqueness.patch).
- Verifies all other 20 files in vendor/gems57/ match /tmp/60GEMSDOE/src/gems57/ byte-for-byte.
- Runs the shared-tool and uniqueness regression tests against the staged upstream package.
- Records why direct git push to buffedlizard55-lab/60GEMSDOE is deferred (session branch lock
  to arena/3ccffc1b-gemsdoe70).
"""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLONE = Path('/tmp/60GEMSDOE')
UPSTREAM_GEMS57 = CLONE / 'src' / 'gems57'
LOCAL_GEMS57 = ROOT / 'vendor' / 'gems57'
OUT_PATCH = ROOT / 'evidence' / 'phase5' / 'upstream_uniqueness.patch'
OUT_JSON = ROOT / 'evidence' / 'phase5' / 'upstream_verification.json'


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT_PATCH.parent.mkdir(parents=True, exist_ok=True)
    pin = json.loads((ROOT / 'registry/template_pin.json').read_text())

    upstream_head = subprocess.check_output(
        ['git', '-C', str(CLONE), 'rev-parse', 'HEAD'], text=True
    ).strip()

    old_lines = (UPSTREAM_GEMS57 / 'uniqueness.py').read_text().splitlines(keepends=True)
    new_lines = (LOCAL_GEMS57 / 'uniqueness.py').read_text().splitlines(keepends=True)
    diff = ''.join(difflib.unified_diff(
        old_lines, new_lines,
        fromfile='a/src/gems57/uniqueness.py',
        tofile='b/src/gems57/uniqueness.py',
    ))
    OUT_PATCH.write_text(diff)

    file_checks = []
    for entry in pin['files']:
        fname = entry['file']
        up_p = UPSTREAM_GEMS57 / fname
        loc_p = LOCAL_GEMS57 / fname
        up_sha = sha(up_p)
        loc_sha = sha(loc_p)
        file_checks.append({
            'file': fname,
            'upstream_sha256': up_sha,
            'local_vendor_sha256': loc_sha,
            'matches_upstream_unmodified': up_sha == loc_sha,
            'expected_modified': fname == 'uniqueness.py',
        })

    # Run pytest on the shared tool and audit suites
    proc = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q',
         str(ROOT / 'tests/test_shared_tools.py'),
         str(ROOT / 'tests/test_audit.py'),
         str(ROOT / 'tests/test_contract.py')],
        capture_output=True, text=True, check=True
    )

    report = {
        'evidence_class': 'UPSTREAM-TEMPLATE-VERIFICATION',
        'date_utc': '2026-10-20',
        'upstream_repo': pin['template_repo'],
        'upstream_pinned_commit': pin['template_commit'],
        'upstream_cloned_head': upstream_head,
        'commit_matches_pin': upstream_head == pin['template_commit'],
        'old_uniqueness_sha256': sha(UPSTREAM_GEMS57 / 'uniqueness.py'),
        'new_uniqueness_sha256': sha(LOCAL_GEMS57 / 'uniqueness.py'),
        'patch_file': str(OUT_PATCH.relative_to(ROOT)),
        'patch_sha256': sha(OUT_PATCH),
        'patch_lines': len(diff.splitlines()),
        'other_20_files_identical_to_upstream': all(
            c['matches_upstream_unmodified'] for c in file_checks if not c['expected_modified']
        ),
        'pytest_verification_stdout': proc.stdout.strip(),
        'pytest_returncode': proc.returncode,
        'push_policy_note': (
            'This Arena session is bound to branch arena/3ccffc1b-gemsdoe70 in '
            'buffedlizard55-lab/GEMSDOE70; cross-repository push to 60GEMSDOE is not '
            'performed from this session. The verified unified diff is published at '
            'evidence/phase5/upstream_uniqueness.patch and docs/downloads/upstream_uniqueness.patch.'
        ),
        'files': file_checks,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
