"""Historical E2 entry point; never creates or authorizes a new submission.

Prints its current archival forward-overlap stop and exits 2. The old E2
selector-review permission was superseded; the shared writer remains in
vendor/gems57/submission_writer.py and is not invoked here.
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
