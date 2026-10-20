"""Release contract for the published candidate.

Two independent facts are tracked and must never be conflated:

* ``download_ok``  - the file exists, matches its recorded SHA-256, passed the shared
  validator. This authorizes forensic download only, not uniqueness or upload.
* ``submit_recommended`` - the pre-registered scientific promotion gate passed.

The page and the run card always show both. A downloadable file is not a promise.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from .protocol import strict_gate

from .protocol import literal_lane_status


def valid_canary(canary):
    """Reject nonfinite, boolean, out-of-range or malformed AUC evidence."""
    if not isinstance(canary, dict):
        return False
    auc = canary.get('auc')
    return (
        canary.get('suspected_leakage') is False
        and type(auc) in (int, float)
        and math.isfinite(auc)
        and 0 <= auc <= 1
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
    """Report the published candidate's status without ever inventing a score."""
    root = Path(root)
    card = _load(root, 'evidence/phase4/run_card.json')
    canaries = _load(root, 'evidence/phase2/canaries.json')
    audit = _load(root, 'evidence/phase4/uniqueness.json')
    reasons, notes = [], []
    lane = literal_lane_status(audit)
    download_ok = False
    submit = False
    tif = sha = None
    if not card:
        reasons.append('Phase-4 run card is missing.')
    else:
        name = card.get('submission_name', '')
        tif = root / 'docs/downloads' / f'{name}.tif'
        sha = card.get('raster_sha256')
        if tif.is_file() and sha and digest(tif) == sha:
            download_ok = True
        else:
            reasons.append('Published TIFF is absent or does not match the recorded SHA-256.')
        validator = card.get('validator_output') or {}
        checks = validator.get('checks') or {}
        if (not isinstance(checks, dict) or not checks
                or not all(v is True for v in checks.values())
                or validator.get('all_checks_passed') is not True
                or validator.get('sha256') != sha):
            reasons.append('Shared validator evidence is not all true and hash-bound to this artifact.')
            download_ok = False
        if validator.get('emitted_positive_pixels') != 37654:
            reasons.append('Emitted dot count differs from the registered 37,654.')
            download_ok = False
        audit_bound = bool(audit and audit.get('candidate_file_sha256') == sha)
        if not audit_bound or not lane['protocol_unique']:
            reasons.append('Literal forward-overlap lane gate is not cleared; mutual overlap is not an exemption.')
        canaries_ok = bool(canaries and isinstance(canaries, dict)
                           and all(valid_canary(c) for c in canaries.values()))
        if not canaries_ok:
            reasons.append('Feature-alone leakage evidence is missing or fails.')
        # Every prerequisite is an actual gate, not just a printed reason.
        submit = bool(card.get('download_and_submit_ok') is True and download_ok
                      and card.get('verdict') == 'promote' and audit_bound
                      and lane['protocol_unique'] and canaries_ok
                      and card.get('gate_a_candidate_ge_h33') is True
                      and card.get('gate_b_prime_candidate_gt_h33_significant') is True)
        if not card.get('gate_a_candidate_ge_h33'):
            reasons.append("Candidate did not match H33 on instrument A.")
        if not card.get('gate_b_prime_candidate_gt_h33_significant'):
            reasons.append("Candidate did not beat H33 on instrument B' with a 95% CI above zero.")
        notes.append('A downloadable, validated file is not a validated leaderboard improvement.')
    current_review = _load(root, 'evidence/literal_protocol_review.json')
    if current_review and current_review.get('correlation_overlap_vs_registry', {}).get('stop') is True:
        submit = False
        reasons.append('Current literal one-way uniqueness audit requires STOP; review download only.')
    protocol = strict_gate(audit or {})
    protocol_ok = not protocol['stop_required']
    if not protocol_ok:
        submit = False
        reasons.append('Current forward-overlap protocol requires STOP; archive download is review-only.')
    return {
        'current_forward_protocol_ok': protocol_ok,
        'review_only': not protocol_ok,
        'verdict': (card or {}).get('verdict', 'negative'),
        'download_ok': download_ok,
        'download_scope': 'archived negative; forensic review only',
        'protocol_unique': lane['protocol_unique'],
        'literal_lane_status': lane,
        'submit_recommended': submit,
        'download_and_submit_ok': bool(download_ok and submit),
        'artifact': str(tif) if tif else None,
        'artifact_sha256': sha,
        'submission_name': (card or {}).get('submission_name'),
        'reasons': reasons,
        'notes': notes,
        'weekly_slots_used': int((card or {}).get('weekly_slots_used', 0)),
        'policy': ('Never describe a non-promoted artifact as an improvement. Both flags are '
                   'always published together.'),
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
    """Every published TIFF/ZIP, from the hash-pinned publication inventory.

    A file may be published without being promoted (parallel-session artifacts are
    preserved this way). Nothing outside the inventory may live in docs/.
    """
    inv = _load(root, 'registry/published_artifacts.json') or {}
    return {row['path']: row.get('sha256') for row in inv.get('artifacts', [])
            if row.get('path', '').lower().endswith(('.tif', '.tiff', '.zip'))}


def assert_no_public_rasters(root):
    """Fail builds on stale or unauthorised prediction files.

    Only the hash-inventoried artifacts may live in the public
    tree; anything else (old candidates, quarantined copies, symlinks) is rejected.
    """
    root = Path(root)
    docs = root / 'docs'
    allowed = published_artifacts(root)
    bad = []
    for p in docs.rglob('*'):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            bad.append(rel + ' (symlink)')
        elif p.is_file() and p.suffix.lower() in {'.tif', '.tiff', '.zip'} and rel not in allowed:
            bad.append(rel)
    if bad:
        raise ValueError('Unauthorised TIFF/ZIP in the publication tree: ' + ', '.join(bad))


def p5_status(root):
    """Fail-closed download permission for the *new* P5 research map.

    This only authorizes a hash-verified REVIEW download. It never promotes a
    raster: P5 failed both paired holdout bars and the literal forward-dot
    witness. The frozen Phase-4 release_status and old review are untouched.
    """
    root = Path(root)
    card = _load(root, 'evidence/p5/run_card.json') or {}
    receipt_path = root / 'docs/downloads' / (card.get('submission_name', '') + '.json')
    receipt = _load(root, receipt_path.relative_to(root)) if receipt_path.is_file() else {}
    receipt = receipt or {}
    name = card.get('submission_name', '')
    tif = root / 'docs/downloads' / (name + '.tif')
    zip_file = tif.with_suffix('.zip')
    inv = _load(root, 'registry/published_artifacts.json') or {}
    pins = {r.get('path'): r.get('sha256') for r in inv.get('artifacts', []) if isinstance(r, dict)}
    checks = (card.get('validator_output') or {}).get('checks') or {}
    forward = (card.get('correlation_overlap_vs_registry') or {}).get('forward_overlap_positive_support_lattice')
    research_only = (card.get('verdict') == 'negative'
                     and card.get('submit_recommended') is False
                     and card.get('download_and_submit_ok') is False
                     and forward == 1.0
                     and (card.get('correlation_overlap_vs_registry') or {}).get('literal_3px_forward_gate_passes') is False
                     and (card.get('gate_results') or {}).get('literal_dot_overlap_gate_passed') is False)
    valid = (bool(name and 'DO-NOT-SUBMIT' in name and tif.is_file() and zip_file.is_file())
             and research_only and card.get('note_chars') == len(card.get('submission_note', ''))
             and len(card.get('submission_note', '')) <= 140
             and isinstance(checks, dict) and bool(checks)
             and all(v is True for v in checks.values())
             and (card.get('validator_output') or {}).get('all_checks_passed') is True)
    if valid:
        try:
            valid = (digest(tif) == card.get('raster_sha256')
                     == (card.get('validator_output') or {}).get('sha256')
                     == receipt.get('sha256') == pins.get(tif.relative_to(root).as_posix())
                     and digest(zip_file) == receipt.get('zip_sha256')
                     == pins.get(zip_file.relative_to(root).as_posix()))
        except (OSError, ValueError):
            valid = False
    return dict(download_ok_for_review=bool(valid), submit_recommended=False,
                download_and_submit_ok=False, verdict='negative',
                tif=tif.relative_to(root).as_posix() if name else None,
                zip_file=zip_file.relative_to(root).as_posix() if name else None,
                sha256=card.get('raster_sha256'),
                reason=('Format/hash verified; failed scientific holdouts and the literal forward-dot gate. '
                        'No organizer acceptance; DO NOT SUBMIT.'))


def candidate_status(root):
    """Parallel E2-lane status (selector-review only; never a submit approval).

    Kept distinct from release_status (Phase-4 candidate). submit_ok is False
    unconditionally here: complete R1 scan, R1 acknowledgment, cap check and
    separate selector authorization remain (docs/publication-amendment-e2.md).
    """
    root = Path(root)
    out = {"download_ok_for_selector_review": False, "submit_ok": False,
           "download_and_submit_ok": False, "verdict": "negative",
           "status": "DO NOT SUBMIT YET — selector-review candidate only",
           "reasons": [], "file": None, "sha256": None, "zip_file": None,
           "submission_name": None, "submission_note": None, "weekly_slots_used": 0}
    try:
        card = _load(root, "evidence/e2/run_card.json") or {}
        pub = _load(root, "evidence/e2/publication.json") or {}
        val = _load(root, "evidence/e2/validator.json") or {}
        out["file"] = pub.get("file"); out["zip_file"] = pub.get("zip_file")
        out["submission_name"] = card.get("submission_name")
        out["submission_note"] = card.get("submission_note")
        path = root / "docs" / "downloads" / str(pub.get("file"))
        ok = (card.get("verdict") == "negative" and pub.get("recomputation_matches_experiment")
              and val.get("local_format_pass") and path.is_file()
              and digest(path) == pub.get("sha256") == val.get("artifact_sha256"))
        out["sha256"] = digest(path) if path.is_file() else None
        out["download_ok_for_selector_review"] = bool(ok)
        out["reasons"].append(
            "E2 promotion bars failed (D28 catalogue-holdout best not beaten); selector gates remain.")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        out["reasons"].append("Missing or invalid E2 evidence: " + str(exc))
    return out
