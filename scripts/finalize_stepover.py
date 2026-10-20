"""Finish experiment 2 after the registry witness fetch becomes available.

Runs the literal registry uniqueness gate on the regenerated stepover surface,
exports the diagnostics-only GeoTIFF (blocked, not a submission), validates it,
and writes the canonical run card.  Safe to rerun; outputs are pinned by name.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]
from gems57 import gates, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems57.validate import assert_submittable, validate
from gems57.network import STRUCT3
from gems70.method import fill_nearest, rank01, upper_surface
from restore_data import DATA, PINS, sha

E = ROOT / 'evidence'
CACHE = ROOT / '.cache'
OUT_TIF = ROOT / 'docs' / 'downloads' / 'gems70-stepperamp-relay-diagnostic-BLOCKED-DO-NOT-SUBMIT.tif'

PAIR_DIST_PX = 12.0
CORRIDOR_ITER = 6
CUTOFF = 0.98


def rtp_edge(rtp, valid):
    r = fill_nearest(np.where(valid, rtp, np.nan))
    my, mx = np.gradient(ndi.gaussian_filter(r, 1.0))
    amp = ndi.gaussian_filter(np.hypot(my, mx), 2.0)
    return np.where(valid, amp, 0.0).astype(np.float32)


def stepover_surface(grid, fp, cat, valid):
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp = src.read(2).astype(np.float32)
    rtp[(rtp <= -1e30) | ~np.isfinite(rtp) | ~fp] = np.nan
    edge = rtp_edge(rtp, valid)
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    visible = folds[0]['visible']
    neighbour = (
        ndi.convolve(visible.astype(np.int64), np.ones((3, 3), np.int64), mode='constant', cval=0)
        - visible
    )
    endpoints = visible & (neighbour == 1)
    comp, _ = ndi.label(visible, STRUCT3)
    ys, xs = np.nonzero(endpoints)
    ecomp = comp[ys, xs]
    tree = cKDTree(np.column_stack([ys, xs]).astype(np.float64))
    pairs = tree.query_pairs(PAIR_DIST_PX)
    paired = np.zeros(endpoints.shape, bool)
    for a, b in pairs:
        if ecomp[a] != ecomp[b]:
            paired[ys[a], xs[a]] = True
            paired[ys[b], xs[b]] = True
    corridor = ndi.binary_dilation(paired, iterations=CORRIDOR_ITER) & ~cat & valid
    feat = ndi.gaussian_filter(corridor.astype(np.float32), 2.0) * edge
    feat = np.where(valid, feat, 0.0).astype(np.float32)
    return upper_surface(rank01(feat, valid), valid, cutoff=CUTOFF)


def fetch_witness(spec):
    p = CACHE / 'registry' / f"{spec['sha256']}.tif"
    if p.is_file() and sha(p) == spec['sha256']:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    repo, _ = spec['sources'][0].split(':', 1)
    r = subprocess.run(['gh', 'api', f'repos/buffedlizard55-lab/{repo}/git/blobs/{spec["blob"]}',
                        '-H', 'Accept: application/vnd.github.raw'],
                       capture_output=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError('witness fetch failed: ' + r.stderr.decode(errors='replace')[-300:])
    tmp = p.with_suffix('.partial')
    tmp.write_bytes(r.stdout)
    if sha(tmp) != spec['sha256'] or tmp.stat().st_size != spec['bytes']:
        raise ValueError('registry witness integrity mismatch')
    tmp.replace(p)
    return p


def implementation_hashes():
    return {n: hashlib.sha256((ROOT / 'vendor' / 'gems57' / n).read_bytes()).hexdigest()
            for n in ('evaluate_holdout.py', 'holdout.py', 'metric.py', 'spatial.py')}


def main():
    witness = json.loads((ROOT / 'registry/stop_witness.json').read_text())
    path = fetch_witness(witness)
    if sha(path) != witness['sha256']:
        raise ValueError('registry witness SHA mismatch')

    holdout = json.loads((E / 'holdout_stepover.json').read_text())
    canaries = json.loads((E / 'canaries_stepover.json').read_text())
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError('input pin mismatch: ' + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    cat = grid.catalogue
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp = src.read(2).astype(np.float32)
    rtp[(rtp <= -1e30) | ~np.isfinite(rtp) | ~fp] = np.nan
    valid = fp & np.isfinite(rtp)
    valid = ndi.binary_erosion(valid, iterations=12)
    surface = stepover_surface(grid, fp, cat, valid)

    idx = {'complete_accessible_scan': False,
           'errors': ['Early-stop witness scan only; not a complete updated registry inventory.'],
           'rasters': [{**witness, 'cache_file': str(path)}]}
    audit = uniqueness.compare_array_to_registry(surface, idx, fp, include_reverse=False,
                                                 expected_grid=(grid.shape, grid.crs, grid.transform))
    (E / 'surface_uniqueness_stepover.json').write_text(json.dumps(audit, indent=2) + '\n')
    certificate = uniqueness.saturation_certificate(path, fp, grid.catalogue,
                                                    expected_grid=(grid.shape, grid.crs, grid.transform))
    (E / 'registry_saturation_stepover.json').write_text(json.dumps(certificate, indent=2) + '\n')

    submission_surface = surface.copy()
    submission_surface[grid.catalogue] = 0
    submission_surface[~fp] = 0
    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)
    info = write_geotiff(OUT_TIF, submission_surface.astype(np.float32))
    format_report = gates.format_report(OUT_TIF, DATA / 'sample_submission.tif', footprint=fp)
    local_validation = validate(OUT_TIF, fp, cat)
    try:
        assert_submittable(local_validation)
        format_ok = True
    except AssertionError as exc:
        format_ok = False
        format_report['problems'] = list(format_report.get('problems', [])) + [str(exc)]

    checks = {'no_nan_inside_footprint': bool(np.isfinite(surface[fp]).all()),
              'all_values_finite': bool(np.isfinite(surface).all()),
              'values_in_0_1': bool((surface >= 0).all() and (surface <= 1).all()),
              'shape_matches': surface.shape == grid.shape,
              'zero_on_catalogue_export': bool(not submission_surface[grid.catalogue].any()),
              'zero_outside_footprint_export': bool(not submission_surface[~fp].any()),
              'format_report_ok': bool(format_report.get('ok')),
              'local_validation_all_checks_passed': bool(local_validation.get('all_checks_passed'))}
    duplicate = any(r.get('duplicate_by_overlap') or r.get('duplicate_by_rho') for r in audit['rows'])

    name = 'gems70-stepperamp-relay-diagnostic-BLOCKED-DO-NOT-SUBMIT'
    note = ('Stepover-relay dilation diagnostic surface; literal registry overlap gate fired '
            '1.00 > 0.70; holdout DTI negative; DO NOT SUBMIT.')
    assert len(name) <= 140 and len(note) <= 140
    file_sha = sha(OUT_TIF)

    d = holdout['scores']['candidate']
    card = {
        'hypothesis': ('Stepover-relay dilation propensity: unmapped cross-faults nucleate where visible '
                       'catalogue lineament endpoints pair across small stepovers, weighted by RTP magnetic '
                       'edge amplitude'),
        'mechanism': ('Endpoint pairs from different visible catalogue components within 1.2 km dilate into an '
                      'off-catalogue corridor (6 px), smoothed and multiplied by RTP gradient magnitude; '
                      'rank-transformed, upper-2% sparsified surface'),
        'non_fault_mimic': 'Volcanic intrusive contact endpoints, line-leveling artifacts, depositional pinchouts',
        'hypothesis_status': 'Tested this session; research-queue candidate H-1',
        'verdict': 'negative',
        'stop_reason': 'duplicate' if duplicate else 'incomplete registry and unavailable comparable current-best',
        'holdout_dti': {**d, 'stage': 'continuous pre-placement surface, not final dots',
                        'current_best_verified': False},
        'canaries': canaries,
        'correlation_overlap_vs_registry': {
            'stage': 'surface before final placement', 'rasters_checked': audit['registry_rasters_checked'],
            'registry_complete': False, 'spearman': audit['worst_spearman_full_footprint'],
            'overlap_within_3px': audit['worst_dot_overlap'],
            'witness': witness['sources'][0], 'witness_sha256': witness['sha256'],
            'literal_duplicate': bool(duplicate), 'final_dots': None,
            'final_dots_reason': 'Not placed: literal surface stop rule.'},
        'raster_sha256': file_sha,
        'raster_sha256_reason': 'Diagnostic surface GeoTIFF in docs/downloads; format-validated locally, blocked by the literal overlap gate, not organizer-accepted, not a submission.',
        'diagnostic_tiff': str(OUT_TIF.relative_to(ROOT)),
        'diagnostic_tiff_bytes': info['bytes'],
        'validator_output': {'submission_tiff': str(OUT_TIF.name),
                             'status': 'LOCALLY_FORMAT-VALIDATED-BLOCKED-BY-GATE',
                             'format_report_ok': format_ok,
                             'all_checks_passed': bool(local_validation.get('all_checks_passed')),
                             'pre_export_array_checks': checks,
                             'crs_shape_transform_file_match': bool(format_report.get('ok')),
                             'sha256': file_sha,
                             'bytes': info['bytes'],
                             'reason': 'Local format/range checks pass; uniqueness gate fired (duplicate), so the file is explicitly not releasable as a submission.'},
        'submission_name': name,
        'submission_note': note,
        'download_and_submit_ok': False,
        'weekly_slots_used': 0,
        'experiment_count': 2,
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['scripts/finalize_stepover.py', 'scripts/run_hypothesis_stepover.py',
                                  'src/gems70/method.py']},
    }
    (E / 'run_card.json').write_text(json.dumps(card, indent=2) + '\n')
    print(json.dumps(card, indent=2))


if __name__ == '__main__':
    main()
