"""Fail-closed current release decision; preserve older, negative archives separately.

`download_ok` means an ELIGIBLE new competition submission may be downloaded, not
that an old hash-pinned research TIFF is readable. The user's forward-overlap
rule (>70% of OUR dots near one registry raster) controls this decision;
the inherited mutual-overlap measurement is diagnostic only. Future selector
promotion requires a separately reviewed implementation, never a flag flip.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


def valid_canary(canary):
    """Reject nonfinite, boolean, out-of-range or malformed AUC evidence."""
    if not isinstance(canary, dict):
        return False
    auc = canary.get('auc')
    return (
        canary.get('suspected_leakage') is False
        and type(auc) in (int, float)
        and 0 <= auc <= 1  # range first: math.isfinite(10**1000) raises OverflowError
        and math.isfinite(auc)
        and max(auc, 1 - auc) <= .90
    )


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _load(root, rel):
    p = Path(root) / rel
    return json.loads(p.read_text()) if p.is_file() else None


def release_status(root):
    """Current-run status. The immutable Phase-4 TIFF is a review-only archive.

    No new raster, canaries, same-split holdout, *surface* registry audit and
    *final-dot* registry audit exist for this session. A changed JSON flag or a
    locally valid old TIFF must never become a submission authorization.
    """
    root = Path(root)
    reasons = []
    try:
        card = _load(root, 'evidence/run_card.json')
        stop = _load(root, 'evidence/literal_overlap_stop.json')
        archive = _load(root, 'evidence/phase4/run_card.json')
    except (ValueError, OSError, TypeError) as exc:
        card = stop = archive = None
        reasons.append('Missing or invalid release evidence: ' + str(exc))
    card_ok = (isinstance(card, dict) and card.get('schema_version') == 2
               and card.get('verdict') == 'negative'
               and isinstance(card.get('lane'), dict)
               and card['lane'].get('status') == 'UNASSIGNED'
               and card.get('experiment_count') == card.get('weekly_slots_used') == 0
               and isinstance(card.get('holdout_dti'), dict)
               and card['holdout_dti'].get('dti') is None
               and card['holdout_dti'].get('ci95') is None
               and card.get('raster_sha256') is None
               and card.get('submission_name') is None
               and card.get('submission_note') is None
               and card.get('organizer_confirmed_score') is None
               and isinstance(card.get('validator_output'), dict)
               and card['validator_output'].get('status') == 'NOT_RUN_FOR_NEW_RASTER'
               and card.get('download_ok') is False
               and card.get('submit_recommended') is False
               and card.get('download_and_submit_ok') is False
               and isinstance(card.get('reasons'), list)
               and bool(card['reasons'])
               and all(isinstance(reason, str) and reason for reason in card['reasons']))
    if card_ok:
        reasons.extend(card['reasons'])
    else:
        reasons.append('Current-run card is absent, contradictory or claims unreviewed promotion.')
    stop_ok = (isinstance(stop, dict) and stop.get('verdict') == 'negative'
               and stop.get('new_surface_checked') is False
               and stop.get('new_final_dots_checked') is False
               and stop.get('new_raster_generated') is False
               and stop.get('new_holdout_run') is False)
    if not stop_ok:
        reasons.append('Missing or contradictory forward-overlap stop receipt.')
    reference = None
    if isinstance(archive, dict) and stop_ok:
        name = archive.get('submission_name')
        if isinstance(name, str) and name and Path(name).name == name:
            rel = f'docs/downloads/{name}.tif'
            rows = stop.get('archive_checks', [])
            row = next((r for r in rows if isinstance(r, dict) and r.get('file') == rel), None) \
                  if isinstance(rows, list) else None
            path = root / rel
            context = card.get('correlation_overlap_vs_registry') if card_ok else None
            context = context if isinstance(context, dict) else {}
            witness = stop.get('witness')
            witness = witness if isinstance(witness, dict) else {}
            validator = row.get('shared_validator') if row else None
            validator = validator if isinstance(validator, dict) else {}
            if (row and path.is_file() and archive.get('raster_sha256') == row.get('sha256')
                    and digest(path) == row['sha256']
                    and validator.get('all_checks_passed') is True
                    and row.get('duplicate_under_user_rule') is True
                    and type(row.get('forward_overlap_within_3px')) in (int, float)
                    and .70 < row['forward_overlap_within_3px'] <= 1
                    and witness.get('sha256') == context.get('witness_sha256')
                    and row['sha256'] == context.get('archived_p4_file_sha256')
                    and row['forward_overlap_within_3px'] == context.get('archived_p4_forward_dot_overlap_3px')):
                reference = {'file': rel, 'sha256': row['sha256'],
                             'forward_overlap_within_3px': row['forward_overlap_within_3px'],
                             'download_for_research_only': True, 'submit_ok': False}
    if reference is None:
        reasons.append('Historical reference is missing, hash-drifted or lacks a literal stop receipt.')
    return {
        'evidence_consistent': bool(card_ok and stop_ok and reference is not None),
        'verdict': 'negative',
        'download_ok': False,  # no NEW eligible TIFF; not an archive file-existence flag
        'submit_recommended': False,
        'download_and_submit_ok': False,
        'artifact': None,
        'artifact_sha256': None,
        'submission_name': None,
        'archive_review': reference,
        'reasons': reasons,
        'notes': ['A valid [0,1] format is necessary, not sufficient; no previous raster is promoted.'],
        'weekly_slots_used': 0,
        'policy': ('Forward >0.70 OR Spearman >0.90 is a stop. No lane/holdout/new raster; '
                   'do not spend a weekly slot. Mutual-overlap is diagnostic only.'),
    }


def assert_root_pages_guard(root):
    """Guard the repository-root Pages publication, including files outside docs."""
    import os
    root = Path(root)
    if (root / '.nojekyll').exists():
        raise ValueError('Root .nojekyll bypasses publication exclusions.')
    config = json.loads((root / '_config.yml').read_text())
    excluded = config.get('exclude', [])
    if (not isinstance(excluded, list) or not all(isinstance(x, str) for x in excluded)
            or not {'quarantine', 'data'}.issubset(excluded)
            or 'docs' in excluded):
        raise ValueError('Invalid root publication exclusions.')
    allowed = published_artifacts(root)
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = [d for d in dirs if not d.startswith('.')
                   and not (base == root and d in excluded)]
        for name in dirs + files:
            if name.startswith('.') or (base == root and name in excluded):
                continue
            path = base / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise ValueError('Unsafe root Pages artifact: ' + rel)
            if path.suffix.lower() in {'.tif', '.tiff', '.zip'}:
                if rel not in allowed:
                    raise ValueError('Unsafe root Pages artifact: ' + rel)
                if allowed[rel] and digest(path) != allowed[rel]:
                    raise ValueError('Published artifact hash mismatch: ' + rel)


def published_artifacts(root):
    """SHA-pinned *archives* that may exist in Pages, never release permissions."""
    inv = _load(root, 'registry/published_artifacts.json') or {}
    pins = {}
    for row in inv.get('artifacts', []):
        if not isinstance(row, dict) or not isinstance(row.get('path'), str):
            raise ValueError('Invalid published artifact inventory row')
        rel = row['path']
        if not rel.lower().endswith(('.tif', '.tiff', '.zip')):
            continue  # a JSON writer receipt is not a raster
        pin = row.get('sha256')
        if (not rel.startswith('docs/downloads/') or Path(rel).as_posix() != rel
                or '..' in Path(rel).parts or rel in pins
                or not isinstance(pin, str) or len(pin) != 64
                or any(c not in '0123456789abcdef' for c in pin)):
            raise ValueError('Invalid published archive pin: ' + rel)
        pins[rel] = pin
    return pins


def assert_no_public_rasters(root):
    """Only byte-pinned historical rasters may exist in the public tree.

    Hash matches permit *forensic access*, not current submission eligibility.
    Symlinks and unknown/changed TIFFs or ZIPs stop site builds.
    """
    root = Path(root)
    docs = root / 'docs'
    allowed = published_artifacts(root)
    bad = []
    for p in docs.rglob('*'):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            bad.append(rel + ' (symlink)')
        elif p.is_file() and p.suffix.lower() in {'.tif', '.tiff', '.zip'}:
            if rel not in allowed or digest(p) != allowed[rel]:
                bad.append(rel)
    if bad:
        raise ValueError('Unauthorised or hash-drifted TIFF/ZIP in publication tree: ' + ', '.join(bad))


def assert_no_public_release_claims(root):
    """Do not serve stale affirmative JSON next to today's negative run card.

    Historical receipts with older 'promote' or review-download fields are kept
    under evidence/, which Pages excludes. A direct URL can be misleading even
    without a link, so both source builds and the actual Pages output call this.
    """
    docs = Path(root) / 'docs'
    positive = {'download_ok', 'download_and_submit_ok', 'submit_ok',
                'submit_recommended', 'approved_for_weekly_slot',
                'download_available', 'download_ok_for_selector_review'}

    def claims(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if (key in positive and value is True) or (
                        key == 'verdict' and isinstance(value, str)
                        and value.lower().startswith('promote')):
                    return True
                if claims(value):
                    return True
        if isinstance(obj, list):
            return any(claims(value) for value in obj)
        return False

    for path in docs.rglob('*.json'):
        if path.is_symlink():
            raise ValueError('Unsafe public JSON symlink: ' + str(path))
        try:
            data = json.loads(path.read_text())
        except (OSError, UnicodeError, ValueError) as exc:
            raise ValueError('Malformed public JSON: ' + str(path)) from exc
        if claims(data):
            raise ValueError('Stale affirmative claim in public JSON: ' + str(path))


def candidate_status(root):
    """Older E2 selector entry point: format-valid bytes are now archive ONLY.

    The earlier selector-review wording was superseded by an independent
    forward-overlap stop. The historic publication receipt is immutable; this
    live status must never offer that TIFF as a newly eligible submission.
    """
    root = Path(root)
    out = {"download_ok_for_selector_review": False, "submit_ok": False,
           "download_and_submit_ok": False, "verdict": "negative",
           "status": "DO NOT SUBMIT — historical E2 archive only",
           "reasons": [], "file": None, "sha256": None, "zip_file": None,
           "submission_name": None, "submission_note": None, "weekly_slots_used": 0}
    try:
        card = _load(root, "evidence/e2/run_card.json") or {}
        pub = _load(root, "evidence/e2/publication.json") or {}
        val = _load(root, "evidence/e2/validator.json") or {}
        stop = _load(root, "evidence/literal_overlap_stop.json") or {}
        out["file"] = pub.get("file"); out["zip_file"] = pub.get("zip_file")
        out["submission_name"] = card.get("submission_name")
        out["submission_note"] = card.get("submission_note")
        path = root / "docs" / "downloads" / str(pub.get("file"))
        rows = stop.get('archive_checks', [])
        row = next((r for r in rows if isinstance(r, dict) and r.get('file')
                    == 'docs/downloads/' + str(pub.get('file'))), None) if isinstance(rows, list) else None
        ok = (card.get("verdict") == "negative" and pub.get("recomputation_matches_experiment")
              and val.get("local_format_pass") and path.is_file()
              and digest(path) == pub.get("sha256") == val.get("artifact_sha256")
              and row and row.get('sha256') == pub.get('sha256')
              and row.get('forward_overlap_within_3px', 0) > .70)
        out["sha256"] = digest(path) if path.is_file() else None
        out["reasons"].append(
            "E2 did not beat D28 on catalogue holdout. "
            + ("Verified E2 also has >70% forward overlap with one binary registry raster."
               if ok else "Missing or inconsistent forward-overlap stop receipt; not cleared."))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        out["reasons"].append("Missing or invalid E2 evidence: " + str(exc))
    return out
