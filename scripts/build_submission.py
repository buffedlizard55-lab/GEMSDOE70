"""Status entry point. Never creates a submission; publishing is publish_e2_candidate.py.

Prints the E2 selector-review status (download-for-review vs submit are kept
distinct) and exits 2 while submit_ok is False, so automation cannot mistake
this for an approval. The shared writer is vendor/gems57/submission_writer.py.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems70.release import candidate_status  # noqa: E402

if __name__ == "__main__":
    status = candidate_status(ROOT)
    print(json.dumps(status, indent=2))
    sys.exit(0 if status["submit_ok"] else 2)
