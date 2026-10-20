"""Publication is fail-closed, distinct from format validity and slot selection."""
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
        and math.isfinite(auc)
        and 0 <= auc <= 1
        and max(auc, 1 - auc) <= .90
    )


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
        if not all(isinstance(item, dict) for item in (card, holdout, audit, manifest)):
            raise ValueError('Evidence documents must be JSON objects.')
        if card.get('verdict') != 'promote': reasons.append('Run verdict is negative.')
        if audit.get('stop_required') is not False or audit.get('unique') is not True:
            reasons.append('Surface uniqueness is blocked or incomplete.')
        if not card.get('holdout_dti',{}).get('current_best_verified'):
            reasons.append('Comparable current holdout best has not been beaten.')
        if holdout.get('promotion_allowed') is not True:
            reasons.append('Holdout evidence does not permit promotion.')
        if not isinstance(canaries, dict) or not canaries or not all(valid_canary(c) for c in canaries.values()):
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
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        reasons.append('Missing or invalid evidence: '+str(exc))
    return {'download_and_submit_ok':False, 'verdict':'negative', 'reasons':reasons,
            'policy':'This stopped experiment cannot be promoted by editing metadata. A fresh reviewed run is required.'}


def assert_root_pages_guard(root):
    """Guard legacy main:/ publication, including files outside docs.

    The root .nojekyll marker must be absent or GitHub would bypass exclusions.
    The JSON-formatted YAML config intentionally uses top-level exclusions only.
    This checks source policy, not whether a remote deployment has completed.
    """
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
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = [d for d in dirs if not d.startswith('.')
                   and not (base == root and d in excluded)]
        for name in dirs + files:
            if name.startswith('.') or (base == root and name in excluded):
                continue
            path = base / name
            if path.is_symlink() or path.suffix.lower() in {'.tif', '.tiff', '.zip'}:
                raise ValueError('Unsafe root Pages artifact: ' + path.relative_to(root).as_posix())


def assert_no_public_rasters(root):
    """Fail builds on stale/accidentally copied predictions, never silently serve them."""
    docs = Path(root)/'docs'
    # Symlinks can expose quarantined files under an innocuous extension. Never
    # allow them in the publication tree, even if dangling or pointing to a dir.
    paths = [p.relative_to(root).as_posix() for p in docs.rglob('*')
             if p.is_symlink() or (p.is_file() and p.suffix.lower() in {'.tif','.tiff','.zip'})]
    if paths:
        raise ValueError('Stopped run must not publish TIFF/ZIP artifacts: '+', '.join(paths))
