"""Concurrent unverified artifacts stay quarantined and never enter public downloads."""
import hashlib
import json
from pathlib import Path
from gems70.release import assert_no_public_rasters

ROOT = Path(__file__).resolve().parents[1]


def test_archival_bytes_and_no_quarantined_public_artifact():
    report = json.loads((ROOT / "evidence/concurrent_h70c_quarantine.json").read_text())
    assert report["status"].startswith("QUARANTINED")
    quarantined_hashes = set()
    for row in report["artifacts"]:
        p = ROOT / row["path"]
        assert p.is_file()
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == row["sha256"]
        quarantined_hashes.add(h)
    public_hashes = {
        hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "docs").rglob("*")
        if p.is_file()
    }
    assert quarantined_hashes.isdisjoint(public_hashes)
    assert_no_public_rasters(ROOT)
    source = (ROOT / "quarantine/concurrent-h70c/source/generate_h70_submission.py.txt").read_text()
    assert "simulate plausible but label as HOLDOUT" in source
