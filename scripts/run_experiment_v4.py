#!/usr/bin/env python3
"""Experiment 4 (in-session 3 of 3): coverage-stratified halo sample with weak tilt.

Registered in docs/hypotheses.md (Phase-4 preregistration) before this run.
Instruments A (shared holdout) and B' (SGMC proxy outside the duplication band),
corrected mutual-overlap uniqueness, shared writer and validator.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems70 import method_v2 as m2
from restore_data import DATA, PINS, sha

E = ROOT / 'evidence' / 'phase4'
CACHE = ROOT / '.cache'
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry' / 'rasters'
H33 = CLONE / 'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'

DOT_COUNT = 37654
D_MIN, D_MAX = 2.4, 32.0
TILT_AMPLITUDE, TILT_SCALE = 0.8, 6.0
TIP_FLOOR, TIP_WEIGHT = 0.7, 0.3
TIP_ALONG, TIP_ACROSS = 25.0, 8.0
BLOCK, NMS = 7, 5.0
GAP_PX = 3.0

NAME = 'gems70-p4-stratified-halo-37654-20261020'
NOTE = ('P4 coverage-stratified halo 7px, weak damage tilt, 37654 binary dots off-catalogue; '
        'dual-instrument evidence')


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False, default=float) + '\n')
    tmp.replace(path)


def cropped(fold, p, valid):
    y, x = np.nonzero(fold['region'])
    y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
    y1, x1 = min(p.shape[0], int(y.max()) + 7), min(p.shape[1], int(x.max()) + 7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k: v[sl] for k, v in fold.items() if isinstance(v, np.ndarray) and v.shape == p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0, x0),
                                     global_shape=p.shape)


def intensity(catalogue_visible, valid):
    """Registered weak-tilt halo intensity (all factors explicit)."""
    cat = np.asarray(catalogue_visible, bool)
    allowed = np.asarray(valid, bool) & ~cat
    d = ndi.distance_transform_edt(~cat).astype(np.float32)
    band = allowed & (d >= D_MIN) & (d <= D_MAX)
    w = 1.0 + TILT_AMPLITUDE * np.exp(-(d - D_MIN) / TILT_SCALE)
    del d
    u, v = m2.tip_kernels(cat, cat.shape)
    t = np.exp(-np.clip(u, 0.0, None) / TIP_ALONG) * np.exp(-np.abs(v) / TIP_ACROSS)
    w = w * (TIP_FLOOR + TIP_WEIGHT * np.where(np.isfinite(t), t, 0.0))
    del u, v, t
    w = np.where(band, w, 0.0).astype(np.float32)
    if not np.isfinite(w).all():
        raise ValueError('non-finite intensity')
    return w


def stratified_dots(score, n=DOT_COUNT, block=BLOCK, nms=NMS):
    """One dot per block (argmax), keep the best `n` blocks, then NMS."""
    h, w = score.shape
    H = int(np.ceil(h / block) * block)
    W = int(np.ceil(w / block) * block)
    pad = np.zeros((H, W), np.float32)
    pad[:h, :w] = score
    nb_y, nb_x = H // block, W // block
    blocks = pad.reshape(nb_y, block, nb_x, block).transpose(0, 2, 1, 3).reshape(nb_y * nb_x, -1)
    best = blocks.argmax(axis=1)
    best_score = blocks.max(axis=1)
    del blocks, pad
    keep = np.flatnonzero(best_score > 0)
    order = keep[np.argsort(best_score[keep], kind='stable')[::-1]]
    by, bx = np.divmod(order, nb_x)
    py, px = np.divmod(best[order], block)
    ys, xs = by * block + py, bx * block + px
    dots = np.zeros((h, w), bool)
    r = int(np.ceil(nms))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (yy * yy + xx * xx) <= nms * nms
    picked = 0
    for y, x in zip(ys, xs):
        if y >= h or x >= w or dots[y, x]:
            continue
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        if dots[y0:y1, x0:x1].any():
            continue
        dots[y, x] = True
        picked += 1
        if picked >= n:
            break
    return dots, picked


def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    if sha(H33) != H33_SHA:
        raise ValueError('H33 SHA mismatch')
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp = src.read(2).astype(np.float32)
    valid = np.isfinite(rtp) & (rtp > -1e30) & fp
    valid = ndi.binary_erosion(valid, iterations=12)
    del rtp
    rng = np.random.default_rng(70420)
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
    h33 = np.where(np.isfinite(h33) & (h33 > 0.5) & fp, 1.0, 0.0).astype(np.float32)

    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    arms = ('candidate', 'random_control', 'h33_reference')
    terms_a = {a: 0.0 for a in arms}
    folds_a = {a: [] for a in arms}
    for k, fold in enumerate(folds):
        vis = fold['visible']
        dots, picked = stratified_dots(intensity(vis, valid))
        if picked != DOT_COUNT:
            raise RuntimeError(f'placed {picked} dots')
        r, t = cropped(fold, m2.dots_to_field(dots), valid)
        terms_a['candidate'] += t
        folds_a['candidate'].append(r)
        del dots
        ids = rng.choice(np.flatnonzero(valid & ~vis), DOT_COUNT, replace=False)
        f = np.zeros(grid.shape, np.float32)
        f.ravel()[ids] = 1.0
        r, t = cropped(fold, f, valid)
        terms_a['random_control'] += t
        folds_a['random_control'].append(r)
        r, t = cropped(fold, h33, valid)
        terms_a['h33_reference'] += t
        folds_a['h33_reference'].append(r)
        print('A fold', k, 'done', flush=True)
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420,
                                                candidate='candidate')
    summary_a['instrument'] = 'A: shared hide-and-recover catalogue holdout'
    dump(E / 'instrumentA_holdout.json', summary_a)
    dump(E / 'instrumentA_folds.json', folds_a)

    prod_dots, picked = stratified_dots(intensity(cat, valid))
    if picked != DOT_COUNT:
        raise RuntimeError('production dot count mismatch')
    prod = m2.dots_to_field(prod_dots)
    del prod_dots
    ids = rng.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
    prod_random = np.zeros(grid.shape, np.float32)
    prod_random.ravel()[ids] = 1.0

    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    d_cat = ndi.distance_transform_edt(~cat)
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_cat >= GAP_PX)
    quad = holdout.quadrant_ids(fp)
    terms_b = {a: 0.0 for a in arms}
    folds_b = {a: [] for a in arms}
    terms_ball = {a: 0.0 for a in arms}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for tag, mask, store in (('prime', proxy_prime, terms_b), ('all', proxy, terms_ball)):
            fold = dict(region=region, truth=mask & region & ~cat, visible=cat,
                        masked_known=cat, hidden_all=np.zeros_like(cat))
            for arm, p in (('candidate', prod), ('random_control', prod_random),
                           ('h33_reference', h33)):
                r, t = cropped(fold, p, valid)
                store[arm] += t
                if tag == 'prime':
                    folds_b[arm].append(r)
        print('B quadrant', k, 'done', flush=True)
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70420,
                                                candidate='candidate')
    summary_b['instrument'] = "B': SGMC proxy truth restricted to d_cat >= 3 px"
    summary_b['proxy_positive_pixels_prime'] = int(proxy_prime.sum())
    summary_b['proxy_positive_pixels_all'] = int(proxy.sum())
    dump(E / 'instrumentB_prime.json', summary_b)
    dump(E / 'instrumentB_prime_folds.json', folds_b)
    summary_ball = evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=70420,
                                                   candidate='candidate')
    summary_ball['instrument'] = 'B: unrestricted SGMC proxy (contains duplication band)'
    dump(E / 'instrumentB_all.json', summary_ball)

    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != grid.shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    tmp_tif = CACHE / 'production_dots_p4.tif'
    tmp_tif.parent.mkdir(parents=True, exist_ok=True)
    if tmp_tif.exists():
        tmp_tif.unlink()
    write_geotiff(tmp_tif, prod, nodata=None)
    audit = uniqueness.compare_to_registry(tmp_tif, index, fp,
                                           expected_grid=(grid.shape, grid.crs, grid.transform))
    audit['inventory_scope'] = (f'{len(records)} single-band 100 m rasters archived in '
                                'buffedlizard55-lab/60GEMSDOE registry/rasters; not an organizer '
                                'registry and not exhaustive')
    dump(E / 'uniqueness.json', audit)
    duplicate = bool(audit['unique'] is False or audit['duplicate_count'] > 0)

    receipt = validated = None
    if not duplicate:
        from gems57 import submission_writer
        receipt = submission_writer.write_submission(
            ROOT / 'docs' / 'downloads' / f'{NAME}.tif', prod,
            ROOT / 'data/bridge/sample_submission.tif', fp,
            note=NOTE, name=NAME, catalogue=cat,
            metadata={'evidence_class': 'HOLDOUT-DTI + PROXY-DTI; not organizer-confirmed'})
        validated = receipt['validator']
    dump(E / 'submission_receipt.json', dict(receipt=receipt, validated=validated,
                                             duplicate=duplicate))

    a, b = summary_a['scores'], summary_b['scores']
    db = summary_b['paired_differences']
    gate_a = a['candidate']['dti'] >= a['h33_reference']['dti']
    gate_b = bool(db['h33_reference']['delta'] > 0 and db['h33_reference']['ci95'][0] > 0)
    promoted = bool(not duplicate and validated and gate_a and gate_b)
    card = {
        'hypothesis': 'H-P4-1 coverage-stratified halo sample with weak damage tilt and tip kernel',
        'mechanism': ('one dot per 7x7-px stratum at the stratum maximum of '
                      '(1+0.8*exp(-(d-2.4)/6))*(0.7+0.3*tip), 5-px NMS, band 2.4-32 px'),
        'non_fault_mimic': 'colluvial/collinear basin-floor lineaments inside the halo',
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': 'HOLDOUT-DTI (A) and PROXY-DTI (B/B\'); neither organizer-confirmed',
        'instrument_a_holdout': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                 for k, v in a.items()},
        'instrument_b_prime_proxy': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                     for k, v in b.items()},
        'instrument_b_unrestricted': {k: {kk: v[kk] for kk in ('dti', 'ci95')}
                                      for k, v in summary_ball['scores'].items()},
        'paired_a_vs_h33': summary_a['paired_differences']['h33_reference'],
        'paired_b_prime_vs_h33': db['h33_reference'],
        'gate_a_candidate_ge_h33': bool(gate_a),
        'gate_b_prime_candidate_gt_h33_significant': gate_b,
        'correlation_overlap_vs_registry': {
            'stage': 'final production dots (37,654 binary)',
            'rasters_checked': audit['registry_rasters_checked'],
            'inventory_scope': audit['inventory_scope'],
            'overlap_definition': audit.get('overlap_definition'),
            'worst_mutual_overlap': audit['worst_dot_overlap'],
            'worst_mutual_submission': audit['worst_overlap_submission'],
            'worst_forward_overlap': audit['worst_forward_overlap'],
            'worst_forward_submission': audit['worst_forward_submission'],
            'worst_spearman_full_footprint': audit['worst_spearman_full_footprint'],
            'worst_rho_submission': audit['worst_rho_submission'],
            'worst_jaccard': audit['worst_jaccard_dot_sets'],
            'duplicate': duplicate,
        },
        'raster_sha256': receipt['sha256'] if receipt else None,
        'raster_sha256_reason': None if receipt else 'uniqueness gate failed; no TIFF written',
        'validator_output': validated,
        'submission_name': NAME,
        'submission_note': NOTE,
        'note_chars': len(NOTE),
        'download_and_submit_ok': promoted,
        'weekly_slots_used': 0,
        'experiment_count': 4,
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['src/gems70/method_v2.py', 'scripts/run_experiment_v4.py']},
        'registered_parameters': dict(dot_count=DOT_COUNT, block_px=BLOCK, nms_px=NMS,
                                      d_min_px=D_MIN, d_max_px=D_MAX,
                                      tilt_amplitude=TILT_AMPLITUDE, tilt_scale_px=TILT_SCALE,
                                      tip_floor=TIP_FLOOR, tip_weight=TIP_WEIGHT,
                                      b_prime_gap_px=GAP_PX),
    }
    dump(E / 'run_card.json', card)
    print(json.dumps(card, indent=2, default=float), flush=True)


if __name__ == '__main__':
    main()
