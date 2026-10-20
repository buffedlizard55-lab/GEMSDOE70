"""Publication is fail-closed, distinct from format validity and slot selection."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def release_status(root):
    """Current run is negative. No booleans alone can authorize a download."""
    root = Path(root)
    reasons = []
    try:
        card = json.loads((root/'evidence/run_card.json').read_text())
        holdout = json.loads((root/'evidence/holdout.json').read_text())
        canaries = json.loads((root/'evidence/canaries.json').read_text())
        audit = json.loads((root/'evidence/surface_uniqueness.json').read_text())
        manifest = json.loads((root/'evidence/experiment_manifest.json').read_text())
        if card.get('verdict') != 'promote': reasons.append('Run verdict is negative.')
        if audit.get('stop_required') is not False or audit.get('unique') is not True:
            reasons.append('Surface uniqueness is blocked or incomplete.')
        if not card.get('holdout_dti',{}).get('current_best_verified'):
            reasons.append('Comparable current holdout best has not been beaten.')
        if holdout.get('promotion_allowed') is not True:
            reasons.append('Holdout evidence does not permit promotion.')
        if not canaries or any(c.get('suspected_leakage') is not False or max(c['auc'],1-c['auc']) > .90 for c in canaries.values()):
            reasons.append('Feature-alone leakage evidence is missing or fails.')
        expected = manifest['source_sha256']
        if expected != card['method_source_sha256']:
            reasons.append('Run-card source pins differ from the experiment manifest.')
        for rel, pin in expected.items():
            if digest(root/rel) != pin: reasons.append('Source changed since experiment: '+rel)
        if digest(root/'docs/hypotheses.md') != manifest['preregistration_sha256']:
            reasons.append('Preregistration changed since experiment.')
        # The current instrument intentionally has no final placement evidence. A future
        # method must supply a new reviewed release contract, not edit booleans in a card.
        if not card.get('raster_sha256'):
            reasons.append('No submission TIFF or on-disk validator receipt exists.')
        reasons.append('No final-dot full-inventory audit or separate weekly-slot selector authorization exists for this run.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        reasons.append('Missing or invalid evidence: '+str(exc))
    return {'download_and_submit_ok':False, 'verdict':'negative', 'reasons':reasons,
            'policy':'This stopped experiment cannot be promoted by editing metadata. A fresh reviewed run is required.'}


def assert_no_public_rasters(root):
    """Fail builds on stale/accidentally copied predictions, never silently serve them."""
    docs = Path(root)/'docs'
    paths = [p.relative_to(root).as_posix() for p in docs.rglob('*')
             if p.is_file() and p.suffix.lower() in {'.tif','.tiff','.zip'}]
    if paths:
        raise ValueError('Stopped run must not publish TIFF/ZIP artifacts: '+', '.join(paths))


def candidate_status(root):
    """E2 selector-review status. Download-for-review is distinct from submit.

    Returns submit_ok=False unconditionally in this instrument: slot selection,
    the complete registry scan and R1 acknowledgment are separate selector
    steps (docs/publication-amendment-e2.md). Any missing/mismatched evidence
    fails closed to download_ok_for_selector_review=False as well.
    """
    root = Path(root)
    out = {"download_ok_for_selector_review": False, "submit_ok": False,
           "download_and_submit_ok": False, "verdict": "negative",
           "status": "DO NOT SUBMIT YET — selector-review candidate only",
           "reasons": [], "file": None, "sha256": None, "zip_file": None,
           "submission_name": None, "submission_note": None, "weekly_slots_used": 0}
    try:
        card = json.loads((root / "evidence/e2/run_card.json").read_text())
        pub = json.loads((root / "evidence/e2/publication.json").read_text())
        val = json.loads((root / "evidence/e2/validator.json").read_text())
        path = root / "docs" / "downloads" / pub["file"]
        out["file"] = pub["file"]
        out["zip_file"] = pub.get("zip_file")
        out["submission_name"] = card.get("submission_name")
        out["submission_note"] = card.get("submission_note")
        if card.get("verdict") != "negative":
            out["reasons"].append("E2 frozen verdict is not the recorded negative.")
        if not pub.get("recomputation_matches_experiment"):
            out["reasons"].append("Candidate bytes were not verified against recomputation.")
        if not val.get("local_format_pass"):
            out["reasons"].append("Local format validation did not pass.")
        if not path.is_file():
            out["reasons"].append("Candidate TIFF missing on disk.")
        else:
            out["sha256"] = digest(path)
            if out["sha256"] != pub.get("sha256") or out["sha256"] != val.get("artifact_sha256"):
                out["reasons"].append("On-disk TIFF hash differs from publication/validator receipts.")
        out["reasons"].append(
            "Promotion bars failed (D28 holdout best not beaten); complete registry scan, "
            "R1 acknowledgment, weekly-cap check and separate selector authorization are still required.")
        out["download_ok_for_selector_review"] = bool(
            card.get("verdict") == "negative"
            and pub.get("recomputation_matches_experiment")
            and val.get("local_format_pass")
            and out["sha256"] is not None
            and out["sha256"] == pub.get("sha256") == val.get("artifact_sha256"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        out["reasons"].append("Missing or invalid E2 evidence: " + str(exc))
    return out


def assert_review_rasters(root):
    """Only the hash-pinned E2 review artifact (TIFF+ZIP) may be public."""
    root = Path(root)
    pub_path = root / "evidence/e2/publication.json"
    allowed = set()
    if pub_path.is_file():
        pub = json.loads(pub_path.read_text())
        allowed = {pub["file"], pub["zip_file"]}
    docs = root / "docs"
    found = {p.name for p in docs.rglob("*")
             if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}}
    extra = sorted(found - allowed)
    if extra:
        raise ValueError("unapproved public raster artifacts: " + ", ".join(extra))
    missing = sorted(allowed - found)
    if missing:
        raise ValueError("pinned review artifacts missing from docs: " + ", ".join(missing))
