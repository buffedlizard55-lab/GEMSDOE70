"""Reconcile frozen registry evidence with the user's forward-overlap stop rule.

Not a metric fork or a new experiment: no fitting, placement, writing or upload.
A historical positive witness is enough to STOP, never enough to certify a pass.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems70.protocol import strict_gate




def build(root=ROOT):
    import numpy as np
    import rasterio
    root = Path(root)
    raw = root / 'evidence/phase4/uniqueness.json'
    audit = json.loads(raw.read_text())
    card = json.loads((root / 'evidence/phase4/run_card.json').read_text())
    tif_name = card['submission_name'] + '.tif'
    tif = root / 'docs/downloads' / tif_name
    if not tif.is_file():
        tif = root / 'quarantine/published-downloads-2026-10-20' / tif_name
    sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    meta = json.loads((root / 'evidence/feature_metadata.json').read_text())
    with rasterio.open(tif) as src:
        a = src.read(1)
        checks = {'single_band': src.count == 1,
                  'shape_matches_cached_reference': list(src.shape) == meta['shape'],
                  'crs_matches_cached_reference': str(src.crs) == meta['crs'],
                  'transform_matches_cached_reference': list(src.transform)[:6] == meta['transform'],
                  'no_nan_anywhere_including_footprint': bool(np.isfinite(a).all()),
                  'values_in_0_1': bool(((a >= 0) & (a <= 1)).all()),
                  'file_sha_matches_frozen_card': sha == card['raster_sha256'],
                  'file_sha_matches_registry_audit': sha == audit['candidate_file_sha256']}
    gate = strict_gate(audit)
    h = card['instrument_a_holdout']['candidate']
    return {
        'hypothesis': 'Protocol reconciliation of existing P4 coverage-stratified halo (not a new experiment)',
        'mechanism': card['mechanism'], 'non_fault_mimic': card['non_fault_mimic'],
        'holdout_dti': {'evidence_class': 'HOLDOUT-DTI', 'source': 'evidence/phase4/run_card.json',
                        'evaluator_version': 'gems57-pooled-hide-v2', **h,
                        'status': 'Historical measurement, not rerun; not an organizer score'},
        'correlation_overlap_vs_registry': gate,
        'registry_audit_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
        'raster_sha256': sha, 'validator_output': {'checks': checks, 'all_pass': all(checks.values()),
            'scope': 'Fresh byte/range/grid audit against cached reference metadata, not organizer acceptance'},
        'submission_name': card['submission_name'],
        'submission_note': 'No file cleared; historical P4 TIFF is quarantined for audit only. DO NOT SUBMIT.',
        'verdict': 'negative', 'download_ok_for_review': False,
        'submit_ok': False, 'new_tif_generated': False, 'experiments_this_session': 0,
        'weekly_slots_used_this_session': 0,
        'stop_reason': 'Historical final-dot witness violates requested forward-overlap rule; lane paragraph absent. No new placement permitted.',
        'surface_check': 'Not run: stopped before a new surface or dots; historical final-dot failure already sufficient.',
        'limitation': 'No new unique submission certified. Existing distinct bytes do not establish protocol uniqueness.'}


def main():
    out = ROOT / 'evidence/current_protocol_review.json'
    result = build()
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['correlation_overlap_vs_registry']['stop_required'] and result['validator_output']['all_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
