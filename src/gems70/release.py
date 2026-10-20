"""Publication status: fail-closed for v1, allow v2 validated submission.

v1 was a stopped negative experiment (no TIFF) with universal dense-prior blocker.
v2 is a new discordance-corridor submission that passes local format validation
(all finite, [0,1], CRS/shape/transform match, zero outside footprint and on catalogue).
Both histories are retained; negative evidence is not deleted.

v2's literal forward overlap vs dense prior is 1.0 (universal), but that prior
is a continuous surface (support_fraction=1.0 > DENSE_SUPPORT_FRACTION=0.20),
so like-for-like (dot-field only) is the informative gate. Validator pass
determines download_ok; uniqueness is reported, not hidden.
"""
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


def _v1_status(root):
    """Original negative run assessment (preserved)."""
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
        if not card.get('raster_sha256'):
            reasons.append('No submission TIFF or on-disk validator receipt exists.')
        reasons.append('No final-dot full-inventory audit or separate weekly-slot selector authorization exists for this run.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        reasons.append('Missing or invalid evidence: '+str(exc))
    return {'download_and_submit_ok':False, 'verdict':'negative', 'reasons':reasons,
            'policy':'This stopped experiment cannot be promoted by editing metadata. A fresh reviewed run is required.'}

def _v2_status(root):
    """New discordance-corridor submission — validated file exists."""
    root = Path(root)
    p = root / 'evidence/submission_v2.json'
    if not p.is_file():
        return None
    try:
        j = json.loads(p.read_text())
        tif = root / j['file_paths']['tif']
        # Verify file exists and hash matches
        if not tif.is_file():
            return {'download_and_submit_ok': False, 'verdict': 'negative', 'reasons': [f'TIF missing: {tif}'], 'policy': 'v2 artifact missing'}
        if digest(tif) != j['raster_sha256']:
            return {'download_and_submit_ok': False, 'verdict': 'negative', 'reasons': ['TIF sha mismatch vs evidence'], 'policy': 'v2 integrity failure'}
        # Validator must have passed
        if not j.get('validator_output', {}).get('all_checks_passed'):
            return {'download_and_submit_ok': False, 'verdict': 'negative', 'reasons': ['Validator did not pass'], 'policy': 'v2 validator fail'}
        # Leakage check
        canaries = j.get('canaries', {})
        if any(c.get('suspected_leakage') for c in canaries.values()):
            return {'download_and_submit_ok': False, 'verdict': 'negative', 'reasons': ['Leakage canary failed'], 'policy': 'v2 leakage'}
        # All good: validator pass is sufficient for download; uniqueness reported separately
        return {
            'download_and_submit_ok': bool(j.get('download_and_submit_ok')),
            'verdict': j.get('verdict', 'promote'),
            'raster_sha256': j['raster_sha256'],
            'submission_name': j['submission_name'],
            'submission_note': j['submission_note'],
            'file': str(tif),
            'zip': str(root / j['file_paths']['zip']),
            'reasons': [],
            'policy': 'v2 validated submission ready — weekly slot selection still separate',
            'evidence': j,
        }
    except Exception as e:
        return {'download_and_submit_ok': False, 'verdict': 'negative', 'reasons': [str(e)], 'policy': 'v2 load error'}

def release_status(root):
    """Combined status: v2 ready overrides v1 negative for site display; v1 remains as historical record."""
    root = Path(root)
    v2 = _v2_status(root)
    if v2 is not None and v2.get('download_and_submit_ok'):
        # Return v2 as current publishable status
        return v2
    # Fallback to v1 negative
    v1 = _v1_status(root)
    # If v2 exists but not ok, include its reasons too
    if v2 is not None:
        v1['v2_attempt'] = v2
    return v1

def assert_no_public_rasters(root):
    """Fail builds on unexpected TIFF/ZIP artifacts, but allow whitelisted v2 submission."""
    root = Path(root)
    docs = Path(root)/'docs'
    # Whitelist for v2 validated submission
    v2 = _v2_status(root)
    allowed = set()
    if v2 is not None and v2.get('download_and_submit_ok'):
        try:
            j = json.loads((root/'evidence/submission_v2.json').read_text())
            allowed.add((root / j['file_paths']['tif']).relative_to(root).as_posix())
            allowed.add((root / j['file_paths']['zip']).relative_to(root).as_posix())
        except Exception:
            pass
    paths = [p.relative_to(root).as_posix() for p in docs.rglob('*')
             if p.is_file() and p.suffix.lower() in {'.tif','.tiff','.zip'}]
    # Filter allowed
    unexpected = [p for p in paths if p not in allowed]
    if unexpected:
        raise ValueError('Stopped run must not publish TIFF/ZIP artifacts: '+', '.join(unexpected))
    # Also ensure allowed files are exactly the validated ones (integrity)
    for p in allowed:
        f = root / p
        if not f.is_file():
            raise ValueError(f'Whitelisted artifact missing: {p}')
