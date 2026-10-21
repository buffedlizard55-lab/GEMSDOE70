#!/usr/bin/env python3
"""Fail-closed CLI release gate for GEMSDOE70 (supports both promoted & archived negative checks)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from audit import check_template
from gems70.release import release_status


def status(evidence_subdir: str = "evidence") -> dict:
    result = release_status(ROOT, evidence_subdir=evidence_subdir)
    card = json.loads((ROOT / evidence_subdir / "run_card.json").read_text())
    tmpl_ok = check_template()["ok"]
    ok = bool(result["download_and_submit_ok"] and tmpl_ok)
    return {
        **result,
        "status": "READY TO DOWNLOAD & SUBMIT (LOCAL GATES PASSED)" if ok else "BLOCKED — DO NOT SUBMIT",
        "generated_tif": card.get("submission_paths", {}).get("primary_tif") if ok else None,
        "generated_zip": card.get("submission_paths", {}).get("zip") if ok else None,
        "raster_sha256": card.get("raster_sha256") if ok else None,
        "zip_sha256": card.get("zip_sha256") if ok else None,
        "download_available": ok,
        "approved_for_weekly_slot": False,  # User decides weekly slot usage on DrivenData portal
        "scientific_experiments_run": card.get("experiment_count"),
        "submission_slots_used": card.get("weekly_slots_used"),
        "template_integrity_ok": tmpl_ok,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expect-negative", action="store_true")
    ap.add_argument("--evidence-subdir", default="evidence")
    args = ap.parse_args()
    result = status(args.evidence_subdir)
    if args.evidence_subdir == "evidence":
        (ROOT / "evidence/release-status.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if args.expect_negative:
        return 0 if (not result["download_available"] and result["template_integrity_ok"]) else 2
    return 0 if (result["download_available"] and result["template_integrity_ok"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
