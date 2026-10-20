"""The registry-audit CLI must fail with argparse usage, never an IndexError."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'registry_scan.py'


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_help_is_successful_and_describes_required_arguments():
    result = run_cli('--help')
    assert result.returncode == 0
    assert 'candidate_tif' in result.stdout
    assert 'out_json' in result.stdout
    assert 'mine_name' in result.stdout
    normalized = ' '.join(result.stdout.split())
    assert 'does not by itself clear the current prompt' in normalized
    assert not result.stderr


def test_missing_arguments_print_usage_without_traceback():
    result = run_cli()
    assert result.returncode == 2
    assert 'usage:' in result.stderr.lower()
    assert 'the following arguments are required' in result.stderr.lower()
    assert 'Traceback' not in result.stderr
    assert 'IndexError' not in result.stderr
