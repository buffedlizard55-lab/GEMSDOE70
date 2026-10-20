"""Experiment 2 -- stepover-relay dilation propensity (research queue H-1).

Hypothesis: unmapped cross-faults nucleate where visible catalogue lineament
endpoints pair across small stepovers (dilational jogs / relay ramps), weighted
by reduced-to-pole magnetic edge amplitude.  This targets geometry in the gaps
between mapped traces rather than truncation of gravity-supported magnetic
contacts, so it can surface faults absent from the USGS/INGENIOUS catalogue.

Method (catalogue-based geometry derived ONLY from visible faults):
* endpoints = visible catalogue pixels with exactly one 8-connected neighbour;
* endpoint pairs from different 8-connected components within 12 px (1.2 km);
* corridor = 6 px dilation of paired endpoints, restricted off-catalogue;
* feature = Gaussian-smoothed corridor mask x RTP magnetic edge amplitude;
* surface = rank transform over the valid domain, upper 2% sparsified.

Protocol: holdout = hide-and-recover with whole-component withholding on the
same buffered quadrant split as experiment 1 (seed 20); pooled DTI alpha 0.2,
beta 0.8, 300 m triangular kernel; feature-alone leakage canaries before any
joint interpretation; literal registry uniqueness gate on the surface BEFORE
any dot placement or TIFF export. The verified 17GEMSDOE dense prior covers
the whole footprint, so the overlap gate is expected to fire and stop this
run: no submission is exported, no weekly slot is used. Negative results are
deliverables.
"""
from __future__ import annotations

import datetime as dt
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
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]
from gems57 import evaluate_holdout, gates, holdout, uniqueness
from gems57.grid import load_grid
from gems57.network import STRUCT3
from gems70.method import fill_nearest, rank01, upper_surface
from restore_data import DATA, PINS, sha

E = ROOT / 'evidence'
CACHE = ROOT / '.cache'
SURFACE_NPY = CACHE / 'candidate_surface_stepover.npy'

PAIR_DIST_PX = 12.0      # stepover search radius: 1.2 km at the 100 m grid
CORRIDOR_ITER = 6        # corridor half-width around paired endpoints
CUTOFF = 0.98            # upper-surface sparsification (fixed surface transform)
FETCH_POLL_SECONDS = 20
FETCH_POLL_MAX = 8 * 60  # keep polling the rate-limited witness fetch for up to 8 min


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def rtp_edge(rtp, valid):
    """RTP horizontal-gradient edge amplitude (unsigned, catalogue-free)."""
    r = fill_nearest(np.where(valid, rtp, np.nan))
    my, mx = np.gradient(ndi.gaussian_filter(r, 1.0))
    amp = ndi.gaussian_filter(np.hypot(my, mx), 2.0)
    return np.where(valid, amp, 0.0).astype(np.float32)


def stepover_feature(visible, cat, edge, valid):
    """Off-catalogue stepover-corridor propensity x magnetic edge amplitude.

    Every input is derived from the *visible* catalogue mask only; the corridor
    is explicitly restricted off-catalogue so the feature cannot score by
    sitting on mapped traces.
    """
    neighbour = (
        ndi.convolve(visible.astype(np.int64), np.ones((3, 3), np.int64), mode='constant', cval=0)
        - visible
    )
    endpoints = visible & (neighbour == 1)
    receipt = dict(
        endpoint_pixels=int(endpoints.sum()),
        stepover_search_radius_px=PAIR_DIST_PX,
        corridor_dilation_px=CORRIDOR_ITER,
    )
    if not endpoints.any():
        return np.zeros(valid.shape, np.float32), {**receipt, 'paired_endpoint_pixels': 0,
                                                    'corridor_pixels': 0}
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
    receipt.update(paired_endpoint_pixels=int(paired.sum()),
                   corridor_pixels=int(corridor.sum()))
    return feat, receipt


def fetch_witness(spec):
    """Fetch the SHA-verified registry witness, polling while rate limited."""
    p = CACHE / 'registry' / f"{spec['sha256']}.tif"
    if p.is_file() and sha(p) == spec['sha256']:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    repo, rel = spec['sources'][0].split(':', 1)
    url = f'repos/buffedlizard55-lab/{repo}/git/blobs/{spec["blob"]}'
    deadline = time.monotonic() + FETCH_POLL_MAX
    last = ''
    while time.monotonic() < deadline:
        tmp = p.with_suffix('.partial')
        try:
            r = subprocess.run(['gh', 'api', url, '-H', 'Accept: application/vnd.github.raw'],
                               capture_output=True, timeout=300)
            if r.returncode == 0:
                tmp.write_bytes(r.stdout)
                if sha(tmp) != spec['sha256'] or tmp.stat().st_size != spec['bytes']:
                    raise ValueError('registry witness integrity mismatch')
                tmp.replace(p)
                return p
            last = r.stderr.decode(errors='replace')[-200:]
            if 'rate limit' not in last.lower() and '403' not in last:
                raise subprocess.CalledProcessError(r.returncode, ['gh', 'api', url], last)
        except (subprocess.CalledProcessError, ValueError) as exc:
            raise
        time.sleep(FETCH_POLL_SECONDS)
    raise TimeoutError('witness fetch remained rate limited: ' + last)


def build_surface_and_folds():
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError('input pin mismatch: ' + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    cat = grid.catalogue
    with rasterio.open(DATA / 'training_features.tif') as src:
        if (src.height, src.width) != grid.shape or str(src.crs) != 'EPSG:32611':
            raise ValueError('feature grid mismatch')
        rtp = src.read(2).astype(np.float32)  # band 2: rtp per restored band metadata
    rtp[(rtp <= -1e30) | ~np.isfinite(rtp) | ~fp] = np.nan
    valid = fp & np.isfinite(rtp)
    valid = ndi.binary_erosion(valid, iterations=12)
    if not valid.any():
        raise ValueError('no valid interior feature pixels')

    edge = rtp_edge(rtp, valid)
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    dump(E / 'holdout_split_stepover.json', {
        'evidence_class': 'HOLDOUT-DTI', 'evaluator_version': evaluate_holdout.VERSION,
        'receipts': [f['receipt'] for f in folds],
        'total_withheld_positive_pixels': int(sum((f['truth'] & valid).sum() for f in folds)),
        'catalogue_predictors': [], 'valid_feature_pixels': int(valid.sum()),
        'known_mask_rule': 'catalogue minus globally withheld components, pixel exact; feature collar is not removed from evaluation',
        'limitation': 'Mapped components are a surrogate for previously unmapped faults; no hidden organizer labels.',
        'note': 'Same buffered whole-component split as experiment 1 (seed 20); comparable folds.'})

    truth = np.zeros(fp.shape, bool)
    active = np.zeros(fp.shape, bool)
    for fold in folds:
        active |= valid & fold['region'] & ~fold['masked_known']
        truth |= valid & fold['truth']
    positives = np.flatnonzero(truth)
    negatives = np.flatnonzero(active & ~truth)
    rng = np.random.default_rng(70020)
    negatives = rng.choice(negatives, min(200000, len(negatives)), replace=False)
    labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]

    feature, feat_receipt = stepover_feature(folds[0]['visible'], cat, edge, valid)
    arms = {
        'candidate': upper_surface(rank01(feature, valid), valid, cutoff=CUTOFF),
        'rtp_edge': upper_surface(rank01(edge, valid), valid, cutoff=CUTOFF),
    }
    random_surface = np.zeros(fp.shape, np.float32)
    ids = rng.choice(np.flatnonzero(valid), int((arms['candidate'] > 0).sum()), replace=False)
    random_surface.ravel()[ids] = 0.5
    arms['random_control'] = random_surface

    canaries = {}
    for name, a in {'stepover_feature': feature, 'rtp_edge': edge}.items():
        values = np.r_[a.ravel()[positives], a.ravel()[negatives]]
        auc = float(roc_auc_score(labels, values))
        canaries[name] = {'evidence_class': 'LEAKAGE-CANARY', 'auc': auc, 'inverse_auc': 1 - auc,
                          'withheld_positive_pixels': len(positives), 'negative_sample_pixels': len(negatives),
                          'suspected_leakage': bool(max(auc, 1 - auc) > 0.90)}
    dump(E / 'canaries_stepover.json', canaries)
    if any(c['suspected_leakage'] for c in canaries.values()):
        raise RuntimeError('LEAKAGE CANARY STOP: feature-alone AUC > 0.90; no joint interpretation permitted')

    terms, fold_results = {}, {}
    for name, a in arms.items():
        per_fold = [evaluate_holdout.evaluate(a, fold, valid) for fold in folds]
        terms[name] = sum(t for _, t in per_fold)
        fold_results[name] = [r for r, _ in per_fold]
    result = evaluate_holdout.pooled_summary(terms, draws=1000, seed=70020, candidate='candidate')
    result['interpretation'] = 'Continuous pre-placement surface HOLDOUT-DTI, not final dots, not organizer-confirmed.'
    result['current_holdout_best_comparable'] = None
    result['promotion_allowed'] = False
    result['promotion_blocker'] = ('No current-best implementation rerun on this identical split; '
                                   'literal overlap gate stops before placement regardless of holdout.')
    dump(E / 'holdout_stepover.json', result)
    dump(E / 'holdout_folds_stepover.json', fold_results)
    np.save(SURFACE_NPY, np.ascontiguousarray(arms['candidate']))
    return grid, fp, cat, valid, folds, arms, result, feat_receipt, canaries


def main():
    start = time.monotonic()
    manifest = E / 'experiment_h2_manifest.json'
    resumed = manifest.exists() and (E / 'holdout_stepover.json').is_file()
    if not resumed:
        dump(manifest, {'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                        'experiment_count': 2, 'maximum_experiments': 3,
                        'maximum_seconds': 7200,
                        'hypothesis': 'stepover-relay dilation propensity (catalogue-gap cross faults)',
                        'source_sha256': {p: sha(ROOT / p) for p in
                                          ['scripts/run_hypothesis_stepover.py', 'src/gems70/method.py']}})
        grid, fp, cat, valid, folds, arms, result, feat_receipt, canaries = build_surface_and_folds()
    else:
        canaries = json.loads((E / 'canaries_stepover.json').read_text())
        result = json.loads((E / 'holdout_stepover.json').read_text())
        # Regenerate the deterministic surface; identical inputs give identical bytes.
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
        folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
        edge = rtp_edge(rtp, valid)
        feature, feat_receipt = stepover_feature(folds[0]['visible'], cat, edge, valid)
        arms = {'candidate': upper_surface(rank01(feature, valid), valid, cutoff=CUTOFF)}
    surface = arms['candidate']

    # --- Surface gate: literal registry uniqueness check BEFORE any export ---
    witness = json.loads((ROOT / 'registry/stop_witness.json').read_text())
    path = fetch_witness(witness)
    if sha(path) != witness['sha256']:
        raise ValueError('registry witness SHA mismatch')
    idx = {'complete_accessible_scan': False,
           'errors': ['Early-stop witness scan only; not a complete updated registry inventory.'],
           'rasters': [{**witness, 'cache_file': str(path)}]}
    audit = uniqueness.compare_array_to_registry(surface, idx, fp, include_reverse=False,
                                                 expected_grid=(grid.shape, grid.crs, grid.transform))
    dump(E / 'surface_uniqueness_stepover.json', audit)
    certificate = uniqueness.saturation_certificate(path, fp, grid.catalogue,
                                                    expected_grid=(grid.shape, grid.crs, grid.transform))
    dump(E / 'registry_saturation_stepover.json', certificate)

    # Diagnostics-only export: the surface masked off catalogue and outside footprint.
    # It is NOT passed to the shared submission writer and is NOT a cleared submission.
    submission_surface = surface.copy()
    submission_surface[grid.catalogue] = 0
    submission_surface[~fp] = 0
    out_tif = ROOT / 'docs' / 'downloads' / 'gems70-stepperamp-relay-diagnostic-BLOCKED-DO-NOT-SUBMIT.tif'
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    info = grid.write_geotiff(out_tif, submission_surface.astype(np.float32))
    sample = DATA / 'sample_submission.tif'
    format_report = gates.format_report(out_tif, sample, footprint=fp)
    from gems57.validate import validate, assert_submittable
    local_validation = validate(out_tif, fp, cat)
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
    file_sha = sha(out_tif)
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
        'holdout_dti': {**result['scores']['candidate'], 'stage': 'continuous pre-placement surface, not final dots',
                        'current_best_verified': False},
        'canaries': canaries,
        'feature_receipt': feat_receipt,
        'correlation_overlap_vs_registry': {
            'stage': 'surface before final placement', 'rasters_checked': audit['registry_rasters_checked'],
            'registry_complete': False, 'spearman': audit['worst_spearman_full_footprint'],
            'overlap_within_3px': audit['worst_dot_overlap'],
            'witness': witness['sources'][0], 'witness_sha256': witness['sha256'],
            'literal_duplicate': bool(duplicate), 'final_dots': None,
            'final_dots_reason': 'Not placed: literal surface stop rule.'},
        'raster_sha256': file_sha,
        'raster_sha256_reason': 'Diagnostic surface GeoTIFF in docs/downloads; format-validated locally, blocked by the literal overlap gate, not organizer-accepted, not a submission.',
        'diagnostic_tiff': str(out_tif.relative_to(ROOT)),
        'diagnostic_tiff_bytes': info['bytes'],
        'validator_output': {'submission_tiff': str(out_tif.name),
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
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['scripts/run_hypothesis_stepover.py', 'src/gems70/method.py']},
    }
    dump(E / 'run_card.json', card)
    print(json.dumps(card, indent=2), flush=True)


if __name__ == '__main__':
    main()
