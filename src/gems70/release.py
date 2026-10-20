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
        _holdout = root/'evidence'/'holdout_stepover.json'
        holdout = json.loads((_holdout if _holdout.is_file() else root/'evidence'/'holdout.json').read_text())
        _canaries = root/'evidence'/'canaries_stepover.json'
        canaries = json.loads((_canaries if _canaries.is_file() else root/'evidence'/'canaries.json').read_text())
        _audit = root/'evidence'/'surface_uniqueness_stepover.json'
        audit = json.loads((_audit if _audit.is_file() else root/'evidence'/'surface_uniqueness.json').read_text())
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


# One explicitly blocked diagnostics-only surface is allowed in docs/downloads:
# its name carries BLOCKED-DO-NOT-SUBMIT and the run card marks it
# download_and_submit_ok: false with reasons.  It is never passed to the shared
# submission writer and is never a releasable competition artifact.
BLOCKED_DIAGNOSTIC_SUFFIX = 'BLOCKED-DO-NOT-SUBMIT.tif'


def assert_no_public_rasters(root):
    """Fail builds on stale/accidentally copied predictions, never silently serve them.

    A single diagnostics-only surface whose filename ends in
    BLOCKED-DO-NOT-SUBMIT.tif under docs/downloads/ is explicitly allowed: its
    status is machine-readable (run_card.json download_and_submit_ok: false) and
    the site banner states it must not be downloaded for submission.
    """
    docs = Path(root)/'docs'
    for p in docs.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.tif','.tiff','.zip'}:
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith('docs/downloads/') and p.name.endswith(BLOCKED_DIAGNOSTIC_SUFFIX):
            continue
        raise ValueError('Stopped run must not publish TIFF/ZIP artifacts: '+rel)


def release_status(root):
    """Publication is fail-closed, distinct from format validity and slot selection."""
    root = Path(root)
    reasons = []
    diagnostic = root/'docs'/'downloads'/f'gems70-stepperamp-relay-diagnostic-{BLOCKED_DIAGNOSTIC_SUFFIX}'
    try:
        card = json.loads((root/'evidence/run_card.json').read_text())
        _holdout = root/'evidence'/'holdout_stepover.json'
        holdout = json.loads((_holdout if _holdout.is_file() else root/'evidence'/'holdout.json').read_text())
        _canaries = root/'evidence'/'canaries_stepover.json'
        canaries = json.loads((_canaries if _canaries.is_file() else root/'evidence'/'canaries.json').read_text())
        _audit = root/'evidence'/'surface_uniqueness_stepover.json'
        audit = json.loads((_audit if _audit.is_file() else root/'evidence'/'surface_uniqueness.json').read_text())
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
            'policy':'This stopped experiment cannot be promoted by editing metadata. A fresh reviewed run is required.',
            'diagnostic_tif': str(diagnostic.relative_to(root)) if diagnostic.is_file() else None,
            'download_available': False,
            'download_blocked_reason': 'Literal uniqueness gate fired on the generated surface (100% forward overlap with the SHA-verified dense prior); holdout DTI below the random-sparse control; no organizer-confirmed score.'}
