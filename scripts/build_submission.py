"""Report E3 candidate release status; never writes a decoy submission.

The released TIFF was written once by scripts/complete_e3_release.py through
the byte-pinned shared writer (vendor/gems57/submission_writer.py) after all
preregistered gates passed. This entry point only verifies/reports that
hash-bound artifact. Exit 0 iff the candidate download is intact; uploading
remains a separate selector step.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems70.release_e3 import release_status_e3  # noqa: E402

if __name__ == "__main__":
    status = release_status_e3(ROOT)
    print(json.dumps(status, indent=2))
    sys.exit(0 if status["download_candidate_ok"] else 2)
