#!/usr/bin/env python3
"""Experiment 3: registered fault damage-zone intensity model (see docs/hypotheses.md).

Instruments: A (shared hide-and-recover) and B' (SGMC proxy outside the measured
cartographic-duplication band). Then corrected binary-dot uniqueness, shared writer
and validator. Writes evidence/phase3/*.json and, if the registered gates pass, the
downloadable submission TIFF.
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

E = ROOT / 'evidence' / 'phase3'
CACHE = ROOT / '.cache'
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry' / 'rasters'
H33 = CLONE / 'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'

DOT_COUNT = 37654
NMS_RADIUS = 2.0
D_MIN = 2.4          # px; live-evidence floor (H33 minimum sqrt(5))
DAMAGE_FLOOR = 0.35
DAMAGE_AMPLITUDE = 0.65
DAMAGE_SCALE = 5.0   # px = 500 m
TIP_ALONG = 25.0
TIP_ACROSS = 8.0
GAP_PX = 3.0         # B' instrument: exclude proxy pixels closer than this to catalogue

NAME = 'gems70-p3-damagezone-37654-20261020'
NOTE = ('P3 damage-zone intensity x tip kernel, 37654 binary dots off-catalogue; '
        'dual-instrument evidence; unique vs 62 archived rasters')


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


def damage_score(catalogue_visible, valid, *, tip=True):
    """Registered intensity: damage-zone decay from mapped traces x tip kernel."""
    cat = np.asarray(catalogue_visible, bool)
    allowed = np.asarray(valid, bool) & ~cat
    d = ndi.distance_transform_edt(~cat).astype(np.float32)
    lam = DAMAGE_FLOOR + DAMAGE_AMPLITUDE * np.exp(-(d - D_MIN) / DAMAGE_SCALE)
    lam[d < D_MIN] = 0.0
    del d
    if tip:
        u, v = m2.tip_kernels(cat, cat.shape)
        beyond = np.clip(u, 0.0, None)
        t = np.exp(-beyond / TIP_ALONG) * np.exp(-np.abs(v) / TIP_ACROSS)
        lam = lam * (0.5 + 0.5 * np.where(np.isfinite(t), t, 0.0))
        del u, v, beyond, t
    lam = np.where(allowed, lam, 0.0).astype(np.float32)
    if not np.isfinite(lam).all():
        raise ValueError('non-finite intensity')
    return lam


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

    rng = np.random.default_rng(70320)
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
    h33 = np.where(np.isfinite(h33) & (h33 > 0.5) & fp, 1.0, 0.0).astype(np.float32)
    if int((h33 > 0).sum()) != DOT_COUNT or (h33[cat] > 0).any():
        raise ValueError('H33 reference invalid')

    # ---------------------------------------------------------------- instrument A
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    arms = ('candidate', 'ablation_no_tip', 'random_control', 'h33_reference')
    terms_a = {a: 0.0 for a in arms}
    folds_a = {a: [] for a in arms}
    for k, fold in enumerate(folds):
        vis = fold['visible']
        for name, score in (('candidate', damage_score(vis, valid, tip=True)),
                            ('ablation_no_tip', damage_score(vis, valid, tip=False))):
            dots, picked = m2.place_dots(score, valid & ~vis, n=DOT_COUNT, radius_px=NMS_RADIUS)
            if picked != DOT_COUNT:
                raise RuntimeError(f'{name}: {picked} dots')
            r, t = cropped(fold, m2.dots_to_field(dots), valid)
            terms_a[name] += t
            folds_a[name].append(r)
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
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70320,
                                                candidate='candidate')
    summary_a['instrument'] = ('A: shared hide-and-recover catalogue holdout (catalogue recovery; '
                              'biased against the off-catalogue target)')
    dump(E / 'instrumentA_holdout.json', summary_a)
    dump(E / 'instrumentA_folds.json', folds_a)

    # ------------------------------------------------------- production dots + B'
    prod_score = damage_score(cat, valid, tip=True)
    prod_dots, picked = m2.place_dots(prod_score, valid & ~cat, n=DOT_COUNT, radius_px=NMS_RADIUS)
    if picked != DOT_COUNT:
        raise RuntimeError('production dot count mismatch')
    prod = m2.dots_to_field(prod_dots)
    del prod_score, prod_dots
    ids = rng.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
    prod_random = np.zeros(grid.shape, np.float32)
    prod_random.ravel()[ids] = 1.0

    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    d_cat = ndi.distance_transform_edt(~cat)
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_cat >= GAP_PX)
    quad = holdout.quadrant_ids(fp)
    terms_b = {a: 0.0 for a in ('candidate', 'random_control', 'h33_reference')}
    folds_b = {a: [] for a in terms_b}
    terms_b_all = {a: 0.0 for a in terms_b}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for name, mask in (('prime', proxy_prime), ('all', proxy)):
            truth = mask & region & ~cat
            fold = dict(region=region, truth=truth, visible=cat, masked_known=cat,
                        hidden_all=np.zeros_like(cat))
            for arm, p in (('candidate', prod), ('random_control', prod_random),
                           ('h33_reference', h33)):
                r, t = cropped(fold, p, valid)
                if name == 'prime':
                    terms_b[arm] += t
                    folds_b[arm].append(r)
                else:
                    terms_b_all[arm] += t
        print('B quadrant', k, 'done', flush=True)
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70320,
                                                candidate='candidate')
    summary_b['instrument'] = ("B': SGMC proxy truth restricted to d_cat >= 3 px "
                               "(cartographic-duplication band excluded)")
    summary_b['proxy_positive_pixels_prime'] = int(proxy_prime.sum())
    summary_b['proxy_positive_pixels_all'] = int(proxy.sum())
    dump(E / 'instrumentB_prime.json', summary_b)
    dump(E / 'instrumentB_prime_folds.json', folds_b)
    summary_b_all = evaluate_holdout.pooled_summary(terms_b_all, draws=1000, seed=70320,
                                                    candidate='candidate')
    summary_b_all['instrument'] = 'B: unrestricted SGMC proxy (contains duplication band)'
    dump(E / 'instrumentB_all.json', summary_b_all)

    # ------------------------------------------------------------- uniqueness
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != grid.shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    tmp_tif = CACHE / 'production_dots_p3.tif'
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
    flagged = [r for r in audit['rows']
               if r.get('duplicate_by_overlap') or r.get('duplicate_by_rho')]
    duplicate = bool(flagged or not audit['unique'])

    # ------------------------------------------------------------- submission
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

    # ---------------------------------------------------------------- run card
    a, b = summary_a['scores'], summary_b['scores']
    db = summary_b['paired_differences']
    gate_a = a['candidate']['dti'] >= a['h33_reference']['dti']
    gate_b = bool(db['h33_reference']['delta'] > 0 and db['h33_reference']['ci95'][0] > 0)
    promoted = bool(not duplicate and validated and gate_a and gate_b)
    card = {
        'hypothesis': 'H-P3-1 fault damage-zone intensity x along-strike tip kernel',
        'mechanism': ('lambda(d)=0.35+0.65*exp(-(d-2.4)/5.0) for d>=2.4 px, times '
                      '(0.5+0.5*exp(-u+/25)*exp(-|v|/8)); no geophysical gate'),
        'non_fault_mimic': 'colluvial/collapse lineaments within the damage band, basin-floor playa',
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': 'HOLDOUT-DTI (A) and PROXY-DTI (B/B\'); neither organizer-confirmed',
        'instrument_a_holdout': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                 for k, v in a.items()},
        'instrument_b_prime_proxy': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                     for k, v in b.items()},
        'instrument_b_unrestricted': {k: {kk: v[kk] for kk in ('dti', 'ci95')}
                                      for k, v in summary_b_all['scores'].items()},
        'paired_a_vs_h33': summary_a['paired_differences']['h33_reference'],
        'paired_b_prime_vs_h33': db['h33_reference'],
        'gate_a_candidate_ge_h33': bool(gate_a),
        'gate_b_prime_candidate_gt_h33_significant': gate_b,
        'correlation_overlap_vs_registry': {
            'stage': 'final production dots (37,654 binary)',
            'rasters_checked': audit['registry_rasters_checked'],
            'inventory_scope': audit['inventory_scope'],
            'worst_spearman_full_footprint': audit['worst_spearman_full_footprint'],
            'worst_rho_submission': audit['worst_rho_submission'],
            'worst_dot_overlap': audit['worst_dot_overlap'],
            'worst_overlap_submission': audit['worst_overlap_submission'],
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
        'experiment_count': 3,
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['src/gems70/method_v2.py', 'scripts/run_experiment_v3.py']},
        'registered_parameters': dict(dot_count=DOT_COUNT, nms_radius_px=NMS_RADIUS,
                                      d_min_px=D_MIN, damage_floor=DAMAGE_FLOOR,
                                      damage_amplitude=DAMAGE_AMPLITUDE,
                                      damage_scale_px=DAMAGE_SCALE, tip_along_px=TIP_ALONG,
                                      tip_across_px=TIP_ACROSS, b_prime_gap_px=GAP_PX),
    }
    dump(E / 'run_card.json', card)
    print(json.dumps(card, indent=2, default=float), flush=True)


if __name__ == '__main__':
    main()
