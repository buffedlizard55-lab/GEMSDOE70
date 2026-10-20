#!/usr/bin/env python3
"""Re-audit archived files; certify the lane stop BEFORE any new experiment.

Uses shared saturation_certificate, compare_to_registry and validate unchanged.
Never creates predictions or consumes a submission slot. The witness is a binary
lattice, so the continuous-raster dot-definition dispute cannot affect the proof.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor')]
from gems57 import grid, uniqueness, validate
from gems70.protocol import literal_lane_status
from gems70.release import digest

REF = '32024716f218d06a94e01464157392119c03cb15'
REPO = 'buffedlizard55-lab/60GEMSDOE'
WITNESS_PATH = 'registry/rasters/calib_r13lattice_00904.tif'
WITNESS_SHA = 'b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2'
CACHE_PATH = '.cache/registry/calib_r13lattice_00904.tif'


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def verify_receipt(actual, recorded, path='receipt'):
    """Exact receipt comparison except harmless cross-CPU Spearman summation noise.

    Never tolerate a threshold crossing, boolean/identity, count, hash or overlap
    difference. The actual gate was evaluated at full precision before this check.
    """
    key = path.rsplit('.', 1)[-1]
    rho = key in {'spearman_full_footprint', 'worst_spearman_full_footprint'}
    if (rho and type(actual) in (int, float) and type(recorded) in (int, float)
            and math.isfinite(actual) and math.isfinite(recorded)
            and (actual > .90) == (recorded > .90)
            and math.isclose(actual, recorded, rel_tol=1e-11, abs_tol=1e-12)):
        return
    if isinstance(actual, dict) and isinstance(recorded, dict) and actual.keys() == recorded.keys():
        for k in actual:
            verify_receipt(actual[k], recorded[k], path + '.' + k)
        return
    if isinstance(actual, list) and isinstance(recorded, list) and len(actual) == len(recorded):
        for i, (a, b) in enumerate(zip(actual, recorded)):
            verify_receipt(a, b, path + '.' + str(i))
        return
    if type(actual) is not type(recorded) or actual != recorded:
        raise ValueError('Receipt drift at ' + path)


def run(fetch=False, verify=False):
    path = ROOT / CACHE_PATH
    if fetch and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.partial')
        try:
            with temp.open('wb') as out:
                subprocess.run(['gh', 'api', f'repos/{REPO}/contents/{WITNESS_PATH}?ref={REF}',
                                '-H', 'Accept: application/vnd.github.raw'], stdout=out,
                               check=True, timeout=120)
            if digest(temp) != WITNESS_SHA:
                raise ValueError('witness SHA-256 mismatch')
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
    if digest(path) != WITNESS_SHA:
        raise ValueError('witness SHA-256 mismatch; no conclusion permitted')
    for name, pin in [('sample_submission.tif', grid.SHA256_SAMPLE_SUBMISSION),
                      ('existing_faults.tif', grid.SHA256_EXISTING_FAULTS)]:
        if digest(ROOT / 'data/bridge' / name) != pin:
            raise ValueError('input SHA-256 mismatch: ' + name)
    g = grid.load_grid(ROOT / 'data/bridge')
    expected = (g.shape, g.crs, g.transform)
    cert = uniqueness.saturation_certificate(path, g.footprint, expected_grid=expected)
    cert['witness_file'] = CACHE_PATH
    # The archived claim of 100% coverage is false: boundary cells are uncovered.
    # Pigeonhole bound for the fixed mass from the handoff, not every dot budget.
    budget = 37654
    lower_bound = max(0.0, 1 - cert['uncovered_allowed_pixels'] / budget)
    if lower_bound <= .70:
        raise ValueError('fixed-mass blockage not established; do not force a stop')
    inventory = json.loads((ROOT / 'registry/published_artifacts.json').read_text())
    index = [{'repo': REPO, 'submission': WITNESS_PATH, 'file': str(path), 'sha256': WITNESS_SHA}]
    results = []
    for item in inventory['artifacts']:
        if not item['path'].endswith('.tif'):
            continue
        tif = ROOT / item['path']
        if digest(tif) != item['sha256']:
            raise ValueError('archived artifact SHA-256 mismatch: ' + item['path'])
        audit = uniqueness.compare_to_registry(tif, index, g.footprint, expected_grid=expected)
        # Strip machine-specific locations from the reproducible receipt.
        audit['my_file'] = item['path']
        for row in audit['rows']:
            row['file'] = CACHE_PATH
        lane = literal_lane_status(audit)
        val = validate.validate(tif, g.footprint, g.catalogue)
        val['file'] = item['path']
        results.append({'artifact': item['path'], 'raster_sha256': item['sha256'],
                        'shared_measurements': audit, 'literal_lane_status': lane,
                        'validator_output': val})
    source = f'https://github.com/{REPO}/blob/{REF}/{WITNESS_PATH}'
    result = {
        'evidence_class': 'REGISTRY-MEASUREMENT', 'policy': 'literal-forward-v1',
        'date_utc': '2026-10-20', 'witness_source': source,
        'witness_sha256': WITNESS_SHA,
        'shared_saturation_certificate': cert, 'archived_artifacts': results,
        'fixed_dot_budget': budget, 'minimum_forward_overlap_at_fixed_budget': lower_bound,
        'stop_required': True, 'new_scientific_experiments': 0,
        'new_rasters_generated': 0, 'weekly_slots_used': 0,
        'surface_stage': 'Stopped before a new candidate surface: at the fixed 37654-dot mass, at most 6649 dots can escape this witness halo, so every placement exceeds 70% forward overlap. Not a universal proof at smaller masses.',
        'final_stage': 'Existing archived final TIFFs re-audited only; no new final dots placed.',
        'scope': 'One positive binary witness suffices to reject, not to certify uniqueness. No full-registry or new-surface rank-correlation claim.',
    }
    out = ROOT / 'evidence/review'
    if verify:
        verify_receipt(result, json.loads((out / 'literal_protocol_audit.json').read_text()))
    else:
        dump(out / 'literal_protocol_audit.json', result)
    p4 = next(r for r in results if '-p4-' in r['artifact'])
    historical = json.loads((ROOT / 'evidence/phase4/run_card.json').read_text())
    holdout = historical['instrument_a_holdout']['candidate']
    card = {
        'hypothesis': 'Deferred: supervised within-halo ranking from the previous handoff',
        'mechanism': 'Learn residual fault evidence using leave-one-quadrant-out proxy training; not run because literal lane preflight stops.',
        'non_fault_mimic': 'SGMC re-digitization offsets, lithologic contacts and erosional scarps',
        'holdout_dti': {'evidence_class': 'HOLDOUT-DTI',
                        'evaluator_version': 'gems57-pooled-hide-v2',
                        'dti': None, 'ci95': None, 'withheld_positive_pixels': None,
                        'reason': 'No new experiment after fixed-mass overlap stop.'},
        'archived_p4_holdout_not_a_new_result': {
            'evidence_class': 'HOLDOUT-DTI', 'evaluator_version': 'gems57-pooled-hide-v2',
            **holdout, 'source': 'evidence/phase4/run_card.json'},
        'correlation_overlap_vs_registry': {
            'source': 'evidence/review/literal_protocol_audit.json',
            'witness_sha256': WITNESS_SHA, 'witness_rasters_checked': 1,
            'footprint_halo_coverage': cert['covered_allowed_fraction'],
            'minimum_forward_overlap_at_fixed_budget': lower_bound,
            'new_surface_spearman': None,
            'archived_p4_vs_witness': p4['shared_measurements']['rows'][0],
            'stop_required': True},
        'raster_sha256': None, 'new_raster_generated': False,
        'validator_output': None,
        'archived_p4': {'artifact': p4['artifact'], 'raster_sha256': p4['raster_sha256'],
                        'validator_output': p4['validator_output'],
                        'download_ok_for_review': True, 'protocol_unique': False,
                        'submit_recommended': False},
        'submission_name': 'gems70-literal-lane-review-20261020-NO-SUBMISSION',
        'submission_note': 'Negative preflight: fixed-mass overlap exceeds literal gate against binary registry lattice. No new TIFF or slot.',
        'verdict': 'negative', 'download_ok': False, 'submit_recommended': False,
        'weekly_slots_used': 0, 'new_scientific_experiments': 0,
        'organizer_confirmed_score': None,
    }
    if verify:
        verify_receipt(card, json.loads((out / 'run_card.json').read_text()))
    else:
        dump(out / 'run_card.json', card)
    print(json.dumps({'stop_required': True, 'archived_files_checked': len(results),
                      'covered_fraction': cert['covered_allowed_fraction'],
                      'new_rasters_generated': 0, 'verdict': 'negative'}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Fetch only the pinned binary witness if absent')
    parser.add_argument('--verify', action='store_true', help='Recompute and verify stored receipts without overwriting their full-precision measurements')
    args = parser.parse_args()
    run(args.fetch, args.verify)
