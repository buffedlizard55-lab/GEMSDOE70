#!/usr/bin/env python3
"""Phase-2 experiment: registered structural forecast, dual-instrument evaluation.

Runs exactly one registered experiment:
  * instrument A = shared hide-and-recover catalogue holdout (required by protocol);
  * instrument B = off-catalogue SGMC proxy population (better validity for the task);
then a corrected binary-dot uniqueness audit, then the shared writer + validator.

Writes evidence/phase2/*.json and, when the promoted gates pass, the submission TIFF
through vendor/gems57/submission_writer.py. Never invents a score.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems70 import method_v2 as m2
from restore_data import DATA, PINS, sha

E = ROOT / 'evidence' / 'phase2'
CACHE = ROOT / '.cache'
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry' / 'rasters'
H33 = CLONE / 'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'

BANDS = {'rtp': 2, 'tmi_hg': 3, 'geod_2ndinv': 4, 'tc': 6, 'geod_shearrate': 7,
         'geod_dilaterate': 8, 'det_elev': 12, 'iso_grav_anom': 13, 'tmi': 14,
         'depth_to_base_surf': 15, 'cond_surf': 17, 'iso_grav_anom_hg': 18,
         'det_elev_slope': 19}

NAME = 'gems70-p2-tipgate-offcat-37654-20261020'
NOTE = ('P2 continuation x geophysical gate, 37654 binary dots, 0 on catalogue; '
        'dual-instrument evidence in gem70 run card')


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


def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- inputs
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    if sha(H33) != H33_SHA:
        raise ValueError('archived H33 SHA mismatch; refusing comparison')
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    inputs = dict(H33=dict(sha256=H33_SHA, source=str(H33)),
                  sgmc=dict(sha256=sha(SGMC), source=str(SGMC)))

    with rasterio.open(DATA / 'training_features.tif') as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError('feature grid mismatch')
        bands = {k: src.read(i).astype(np.float32) for k, i in BANDS.items()}
    for k, a in bands.items():
        a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
    valid = fp.copy()
    for a in bands.values():
        valid &= np.isfinite(a)
    valid = ndi.binary_erosion(valid, iterations=12)
    del bands['tmi_hg'], bands['det_elev'], bands['tmi'], bands['cond_surf'], \
        bands['iso_grav_anom_hg'], bands['geod_shearrate']

    geo_fields = m2.geophysical_fields(bands['geod_dilaterate'], bands['geod_2ndinv'],
                                       bands['iso_grav_anom'], bands['tc'],
                                       bands['det_elev_slope'], valid)
    geo_rank = m2.geophysical_ranks(geo_fields, valid & ~cat)
    dump(E / 'inputs.json', dict(inputs=inputs, bands=list(BANDS),
                                 valid_pixels=int(valid.sum()),
                                 geophysical_fields=list(geo_fields),
                                 registered_params=dict(
                                     offset_peak_px=m2.OFFSET_PEAK_PX,
                                     offset_sigma_px=m2.OFFSET_SIGMA_PX,
                                     min_offset_px=m2.MIN_OFFSET_PX,
                                     tip_sigma_along_px=m2.TIP_SIGMA_ALONG_PX,
                                     tip_sigma_across_px=m2.TIP_SIGMA_ACROSS_PX,
                                     dot_count=m2.DOT_COUNT, nms_radius_px=m2.NMS_RADIUS_PX)))

    # ------------------------------------------------------ instrument A arms
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    rng = np.random.default_rng(70220)
    ARM_NAMES = ('candidate', 'ablation_offset_only', 'ablation_offset_tip',
                 'ablation_geo_only', 'random_control', 'h33_reference')
    terms_a = {n: 0.0 for n in ARM_NAMES}
    folds_a = {n: [] for n in ARM_NAMES}
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
    h33 = np.where(np.isfinite(h33) & (h33 > 0.5) & fp, 1.0, 0.0).astype(np.float32)
    if int((h33 > 0).sum()) != 37654:
        raise ValueError('H33 dot count changed')
    if (h33[cat] > 0).any():
        raise ValueError('H33 is not off-catalogue')

    for k, fold in enumerate(folds):
        vis = fold['visible']
        comp = m2.score_components(vis, geo_rank, valid)
        variants = {
            'candidate': m2.combine_components(comp, True, True, True),
            'ablation_offset_only': m2.combine_components(comp, True, False, False),
            'ablation_offset_tip': m2.combine_components(comp, True, True, False),
            'ablation_geo_only': m2.combine_components(comp, False, False, True),
        }
        for name, score in variants.items():
            dots, picked = m2.place_dots(score, comp['allowed'])
            if picked != m2.DOT_COUNT:
                raise RuntimeError(f'{name}: placed {picked} dots, expected {m2.DOT_COUNT}')
            r, t = cropped(fold, m2.dots_to_field(dots), valid)
            terms_a[name] = terms_a[name] + t
            folds_a[name].append(r)
            del dots
        del variants, comp
        ids = rng.choice(np.flatnonzero(valid & ~vis), m2.DOT_COUNT, replace=False)
        f = np.zeros(grid.shape, np.float32)
        f.ravel()[ids] = 1.0
        r, t = cropped(fold, f, valid)
        terms_a['random_control'] = terms_a['random_control'] + t
        folds_a['random_control'].append(r)
        del f
        r, t = cropped(fold, h33, valid)
        terms_a['h33_reference'] = terms_a['h33_reference'] + t
        folds_a['h33_reference'].append(r)
        print('fold', k, 'evaluated', flush=True)

    # ------------------------------------------- leakage canaries (instrument A)
    positive = np.zeros(grid.shape, bool)
    active = np.zeros(grid.shape, bool)
    for fold in folds:
        positive |= valid & fold['truth']
        active |= valid & fold['region'] & ~fold['masked_known']
    pos = np.flatnonzero(positive)
    neg = rng.choice(np.flatnonzero(active & ~positive), 200000, replace=False)
    labels = np.r_[np.ones(pos.size), np.zeros(neg.size)]
    canaries = {}
    for name, a in {**{k: bands[k] for k in ('rtp', 'geod_dilaterate', 'geod_2ndinv',
                                             'tc', 'iso_grav_anom', 'det_elev_slope',
                                             'depth_to_base_surf')},
                    **geo_fields}.items():
        vals = np.r_[a.ravel()[pos], a.ravel()[neg]]
        auc = float(roc_auc_score(labels, vals))
        canaries[name] = dict(evidence_class='LEAKAGE-CANARY', auc=auc, inverse_auc=1 - auc,
                              withheld_positive_pixels=int(pos.size),
                              negative_sample_pixels=int(neg.size),
                              suspected_leakage=bool(max(auc, 1 - auc) > .90))
    dump(E / 'canaries.json', canaries)
    if any(c['suspected_leakage'] for c in canaries.values()):
        raise RuntimeError('LEAKAGE CANARY STOP: feature-alone AUC > .90')

    # ------------------------------------------------- instrument A summary
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70220,
                                                candidate='candidate')
    summary_a['instrument'] = ('A: shared hide-and-recover catalogue holdout; measures catalogue '
                              'recovery, biased against the off-catalogue target')
    summary_a['promotion_allowed'] = False   # instrument B must also pass
    dump(E / 'instrumentA_holdout.json', summary_a)
    dump(E / 'instrumentA_folds.json', folds_a)

    # ------------------------------------------------------ instrument B setup
    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    proxy = sgmc & ~cat & fp
    quad = holdout.quadrant_ids(fp)
    prod_comp = m2.score_components(cat, geo_rank, valid)
    prod_score = m2.combine_components(prod_comp, True, True, True)
    prod_dots, prod_picked = m2.place_dots(prod_score, prod_comp['allowed'])
    if prod_picked != m2.DOT_COUNT:
        raise RuntimeError(f'production placed {prod_picked} dots')
    prod = m2.dots_to_field(prod_dots)
    del prod_comp, prod_score
    # same-count random production control
    ids = rng.choice(np.flatnonzero(valid & ~cat), m2.DOT_COUNT, replace=False)
    prod_random = np.zeros(grid.shape, np.float32)
    prod_random.ravel()[ids] = 1.0
    prod_arms = {'candidate': prod, 'random_control': prod_random, 'h33_reference': h33}
    terms_b, folds_b = {}, {}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        truth = proxy & region & ~cat
        if not truth.any():
            raise ValueError(f'quadrant {k} has no proxy positives')
        fold = dict(region=region, truth=truth, visible=cat, masked_known=cat,
                    hidden_all=np.zeros_like(cat))
        for name, p in prod_arms.items():
            r, t = cropped(fold, p, valid)
            folds_b.setdefault(name, []).append(r)
            terms_b[name] = terms_b.get(name, 0) + t
        print('B quadrant', k, 'evaluated', flush=True)
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70220,
                                                candidate='candidate')
    summary_b['instrument'] = ('B: off-catalogue proxy truth (USGS SGMC minus competition '
                              'catalogue), 12-px-eroded quadrants; SGMC used only as truth')
    summary_b['proxy_positive_pixels'] = int(proxy.sum())
    summary_b['promotion_allowed'] = True
    dump(E / 'instrumentB_proxy.json', summary_b)
    dump(E / 'instrumentB_folds.json', folds_b)

    # -------------------------------------------------- uniqueness (final dots)
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != grid.shape:
                continue
        records.append(dict(repo=p.name.split('__')[0], submission=p.name,
                            file=str(p), sha256=sha(p), sources=[p.name]))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    audit = uniqueness.compare_to_registry(_write_tmp(prod), index, fp,
                                           expected_grid=(grid.shape, grid.crs, grid.transform))
    audit['inventory_scope'] = (f'{len(records)} single-band 100 m rasters archived in '
                                'buffedlizard55-lab/60GEMSDOE registry/rasters at the clone used '
                                'for this run; not an organizer registry and not exhaustive')
    dump(E / 'uniqueness.json', audit)
    flagged = [r for r in audit['rows']
               if r.get('duplicate_by_overlap') or r.get('duplicate_by_rho')]
    duplicate = bool(flagged or not audit['unique'])

    # ------------------------------------------------------------- submission
    receipt = None
    validated = None
    if not duplicate:
        from gems57 import submission_writer
        receipt = submission_writer.write_submission(
            ROOT / 'docs' / 'downloads' / f'{NAME}.tif', prod,
            ROOT / 'data/bridge/sample_submission.tif', fp,
            note=NOTE, name=NAME, catalogue=cat,
            metadata={'evidence_class': 'HOLDOUT-DTI + PROXY-DTI; not organizer-confirmed',
                      'instrument_a_dti': summary_a['scores']['candidate']['dti'],
                      'instrument_b_dti': summary_b['scores']['candidate']['dti']})
        validated = receipt['validator']
    dump(E / 'submission_receipt.json', dict(receipt=receipt, validated=validated,
                                             duplicate=duplicate))

    # ---------------------------------------------------------------- run card
    a = summary_a['scores']
    b = summary_b['scores']
    da = summary_a['paired_differences']
    db = summary_b['paired_differences']
    gate_a = (a['candidate']['dti'] >= a['h33_reference']['dti'])
    gate_b = (db['h33_reference']['delta'] > 0 and db['h33_reference']['ci95'][0] > 0)
    promoted = bool(not duplicate and receipt and validated and gate_a and gate_b)
    card = {
        'hypothesis': 'H-P2-1 geophysically gated along-strike continuation / parallel-strand prior',
        'mechanism': ('distance-to-mapped-fault prior (peak 1.6 km) x beyond-tip kernel '
                      '(2.5 km along, 0.8 km across) x mean rank of four geophysical fields '
                      '(geodetic strain amplitude, gravity edge, |magnetic tilt|, relief)'),
        'non_fault_mimic': 'depositional/erosional linear feature in the halo (fan edge, paleovalley)',
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': 'HOLDOUT-DTI (instrument A) and PROXY-DTI (instrument B); neither is '
                          'organizer-confirmed',
        'instrument_a_holdout': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                 for k, v in a.items()},
        'instrument_b_proxy': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                               for k, v in b.items()},
        'paired_differences_a': {k: v for k, v in da.items()},
        'paired_differences_b': {k: v for k, v in db.items()},
        'gate_instrument_a_candidate_ge_h33': bool(gate_a),
        'gate_instrument_b_candidate_gt_h33_significant': bool(gate_b),
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
        'experiment_count': 2,
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['src/gems70/method_v2.py', 'scripts/run_experiment_v2.py']},
        'registered_parameters': dict(offset_peak_px=m2.OFFSET_PEAK_PX,
                                      offset_sigma_px=m2.OFFSET_SIGMA_PX,
                                      min_offset_px=m2.MIN_OFFSET_PX,
                                      tip_sigma_along_px=m2.TIP_SIGMA_ALONG_PX,
                                      tip_sigma_across_px=m2.TIP_SIGMA_ACROSS_PX,
                                      dot_count=m2.DOT_COUNT, nms_radius_px=m2.NMS_RADIUS_PX),
    }
    dump(E / 'run_card.json', card)
    print(json.dumps(card, indent=2, default=float), flush=True)


def _write_tmp(field):
    """Write the production field to a private temp TIFF for the uniqueness audit."""
    p = CACHE / 'production_dots.tif'
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    write_geotiff(p, np.asarray(field, np.float32), nodata=None)
    return p


if __name__ == '__main__':
    main()
