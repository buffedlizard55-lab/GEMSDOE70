#!/usr/bin/env python3
"""Experiment E5-1: supervised within-halo ranking, SGMC proxy, LOQO.

Preregistered in docs/preregistration-e5.md before this run. Instruments,
emission, gates, writer and validator are inherited unchanged from
scripts/run_experiment_v4.py (P4); only the candidate intensity changes:
a HistGradientBoosting model trained on the SGMC off-catalogue proxy
(d_cat >= 3 px) with leave-one-quadrant-out. Production dots are emitted
from the out-of-fold surface, so the evaluated artifact is byte-identical
to the published artifact.
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems70 import method_v2 as m2
from restore_data import DATA, PINS, sha
from run_experiment_v4 import cropped, dump, stratified_dots, GAP_PX, H33, H33_SHA, SGMC, REG

E = ROOT / 'evidence' / 'e5'
CACHE = ROOT / '.cache'
DOT_COUNT = 37654
D_MIN, D_MAX = 2.4, 32.0
SEED = 70501
NEG_CAP = 240_000
BAND_NAMES = ['mag_anom', 'rtp', 'tmi_hg', 'geod_2ndinv', 'iso_grav_anom_slope',
              'tc', 'geod_shearrate', 'geod_dilaterate', 'tmi_vg', 'deq_n100a15',
              'iso_grav_anom_vg', 'det_elev', 'iso_grav_anom', 'tmi',
              'depth_to_base_surf', 'ieq_n100a15', 'cond_surf',
              'iso_grav_anom_hg', 'det_elev_slope']
DERIVED = ['analytic_signal', 'gradmag_rtp', 'gradmag_depth_to_base_surf',
           'gradmag_iso_grav_anom']
GEOMETRY = ['d_cat', 'log1p_d_cat']
FEATURES = BAND_NAMES + DERIVED + GEOMETRY
N_CUBE = len(BAND_NAMES) + len(DERIVED)
NAME = 'gems70-e5-supervised-loqo-37654-20261020'
NOTE = ('E5 supervised LOQO within-halo ranking on SGMC proxy, 37654 binary '
        'dots; HOLDOUT+PROXY evidence')


def gradmag(a):
    fin = np.isfinite(a)
    med = float(np.nanmedian(a[fin])) if fin.any() else 0.0
    f = np.where(fin, a, med).astype(np.float64)
    gy = ndi.sobel(f, axis=0)
    gx = ndi.sobel(f, axis=1)
    out = np.hypot(gy, gx).astype(np.float32)
    out[~fin] = np.nan
    return out


def build_cube(shape):
    path = CACHE / 'e5_feature_cube.dat'
    cube = np.memmap(path, dtype=np.float32, mode='w+', shape=(N_CUBE, *shape))
    keep = {}
    with rasterio.open(DATA / 'training_features.tif') as src:
        for i in range(19):
            a = src.read(i + 1).astype(np.float32)
            a[~np.isfinite(a) | (a <= -1e30)] = np.nan
            cube[i] = a
            if BAND_NAMES[i] in ('tmi_hg', 'tmi_vg', 'rtp', 'depth_to_base_surf',
                                'iso_grav_anom'):
                keep[BAND_NAMES[i]] = a.copy()
            del a
    with np.errstate(invalid='ignore'):
        cube[19] = np.sqrt(keep['tmi_hg'] ** 2 + keep['tmi_vg'] ** 2)
    cube[20] = gradmag(keep['rtp'])
    cube[21] = gradmag(keep['depth_to_base_surf'])
    cube[22] = gradmag(keep['iso_grav_anom'])
    cube.flush()
    del keep
    gc.collect()
    return cube


def gather(cube, ys, xs, dmap):
    x = np.empty((len(ys), len(FEATURES)), np.float32)
    x[:, :N_CUBE] = cube[:, ys, xs].T
    d = dmap[ys, xs].astype(np.float32)
    x[:, N_CUBE] = d
    x[:, N_CUBE + 1] = np.log1p(d)
    return x


def predict(model, cube, mask, dmap):
    ys, xs = np.nonzero(mask)
    out = np.zeros(len(ys), np.float32)
    for s in range(0, len(ys), 200_000):
        sl = slice(s, s + 200_000)
        out[sl] = model.predict_proba(gather(cube, ys[sl], xs[sl], dmap))[:, 1]
    surf = np.zeros(mask.shape, np.float32)
    surf[ys, xs] = out
    return surf


def stratified_dots_filled(score, n=DOT_COUNT):
    """P4 block pass + Amendment-1 fill (same 5 px NMS, descending score)."""
    dots, picked = stratified_dots(score, n=n)
    if picked >= n:
        return dots, picked
    h, w = score.shape
    blocked = ndi.binary_dilation(dots, structure=np.ones((11, 11), bool))
    order = np.argsort(score.ravel(), kind='stable')[::-1]
    for idx in order:
        if picked >= n:
            break
        if score.ravel()[idx] <= 0:
            break
        y, x = divmod(int(idx), w)
        if blocked[y, x]:
            continue
        dots[y, x] = True
        blocked[max(0, y - 5):y + 6, max(0, x - 5):x + 6] = True
        picked += 1
    return dots, picked


def auc_or_none(score, pos, neg):
    s = np.concatenate([score[pos], score[neg]])
    ok = np.isfinite(s)
    y = np.concatenate([np.ones(int(pos.sum())), np.zeros(int(neg.sum()))])
    if ok.sum() < 100 or y[ok].sum() in (0, ok.sum()):
        return None
    return float(roc_auc_score(y[ok], s[ok]))


def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    if sha(H33) != H33_SHA:
        raise ValueError('H33 SHA mismatch')
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    shape = grid.shape
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp = src.read(2).astype(np.float32)
    valid = np.isfinite(rtp) & (rtp > -1e30) & fp
    valid = ndi.binary_erosion(valid, iterations=12)
    del rtp
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
    h33 = np.where(np.isfinite(h33) & (h33 > 0.5) & fp, 1.0, 0.0).astype(np.float32)
    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0

    d_full = ndi.distance_transform_edt(~cat).astype(np.float32)
    d_sgmc = ndi.distance_transform_edt(~sgmc).astype(np.float32)
    eligible = valid & ~cat & (d_full >= D_MIN) & (d_full <= D_MAX)
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_full >= GAP_PX)
    pos_mask = proxy_prime & eligible
    neg_mask = eligible & (d_sgmc > 3.0)
    quad = holdout.quadrant_ids(fp)
    print('grid ok; eligible', int(eligible.sum()), 'pos', int(pos_mask.sum()),
          'neg', int(neg_mask.sum()), flush=True)

    cube = build_cube(shape)
    print('cube built', flush=True)

    # ---- canaries: each feature alone, before any model is trusted ----
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3,
                                               boundary_px=12)
    hidden = folds[0]['hidden_all']
    region_all = np.zeros(shape, bool)
    for f in folds:
        region_all |= f['region']
    rng_c = np.random.default_rng(SEED)
    a_neg_ids = rng_c.choice(np.flatnonzero(region_all & valid & ~cat & ~hidden),
                             200_000, replace=False)
    a_neg = np.zeros(shape, bool); a_neg.ravel()[a_neg_ids] = True
    a_pos = hidden & region_all
    p_neg_ids = rng_c.choice(np.flatnonzero(neg_mask), 200_000, replace=False)
    p_neg = np.zeros(shape, bool); p_neg.ravel()[p_neg_ids] = True
    canaries = {'instrument_a_withheld_positive_pixels': int(a_pos.sum()),
                'proxy_prime_positive_pixels_in_band': int(pos_mask.sum()),
                'stop_threshold_auc': 0.90, 'features': {}}
    full = {}
    for i, nm in enumerate(BAND_NAMES + DERIVED):
        full[nm] = np.array(cube[i])
    full['d_cat'] = d_full
    full['log1p_d_cat'] = np.log1p(d_full)
    for nm in FEATURES:
        canaries['features'][nm] = {
            'auc_instrument_a': auc_or_none(full[nm], a_pos, a_neg),
            'auc_proxy_prime': auc_or_none(full[nm], pos_mask, p_neg)}
    del full
    gc.collect()
    dump(E / 'canaries.json', canaries)
    worst = max((v[k] or 0.0) for v in canaries['features'].values()
                for k in ('auc_instrument_a', 'auc_proxy_prime'))
    print('canaries done; worst single-feature AUC', round(worst, 4), flush=True)
    if worst > 0.90:
        raise RuntimeError('leakage canary fired: single-feature AUC > 0.90; stop')

    # ---- LOQO training ----
    rng = np.random.default_rng(SEED)
    models, train_rows = [], []
    oof_surface = np.zeros(shape, np.float32)
    oof_auc = {}
    for k in range(4):
        train_ok = (quad >= 0) & (quad != k) & ~ndi.binary_dilation(quad == k, iterations=12)
        pos_ids = np.flatnonzero(pos_mask & train_ok)
        neg_ids_all = np.flatnonzero(neg_mask & train_ok)
        neg_ids = rng.choice(neg_ids_all, min(NEG_CAP, len(neg_ids_all)),
                             replace=False)
        ids = np.concatenate([pos_ids, neg_ids])
        ys, xs = np.unravel_index(ids, shape)
        x = gather(cube, ys, xs, d_full)
        y = np.concatenate([np.ones(len(pos_ids), np.int32),
                            np.zeros(len(neg_ids), np.int32)])
        w = np.where(y == 1, len(neg_ids) / max(1, len(pos_ids)), 1.0)
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                           max_leaf_nodes=31, min_samples_leaf=40,
                                           l2_regularization=1.0,
                                           early_stopping=False, random_state=SEED)
        m.fit(x, y, sample_weight=w)
        models.append(m)
        train_rows.append(dict(quadrant=k, n_pos=int(len(pos_ids)),
                               n_neg=int(len(neg_ids))))
        del x, y, w
        qmask = eligible & (quad == k)
        oof_surface += predict(m, cube, qmask, d_full)
        oof_auc[str(k)] = auc_or_none(oof_surface, pos_mask & (quad == k),
                                      neg_mask & (quad == k))
        print('model', k, 'trained; OOF AUC', oof_auc[str(k)], flush=True)
        gc.collect()
    dump(E / 'training.json', dict(rows=train_rows, oof_auc_by_quadrant=oof_auc,
                                   features=FEATURES, seed=SEED))

    # ---- surface uniqueness BEFORE placement ----
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    surf_tif = CACHE / 'e5_oof_surface.tif'
    if surf_tif.exists():
        surf_tif.unlink()
    write_geotiff(surf_tif, np.clip(oof_surface, 0, 1).astype(np.float32), nodata=None)
    surf_audit = uniqueness.compare_to_registry(
        surf_tif, index, fp, expected_grid=(shape, grid.crs, grid.transform))
    surf_audit['stage'] = 'OOF continuous surface before placement'
    dump(E / 'surface_uniqueness.json', surf_audit)
    if surf_audit['duplicate_count'] > 0 or (
            surf_audit['worst_spearman_full_footprint'] or 0) > 0.90:
        raise RuntimeError('surface duplicates a registry raster; lane stop')
    print('surface uniqueness ok; worst rho',
          surf_audit['worst_spearman_full_footprint'], flush=True)

    # ---- production dots from the OOF surface (evaluated == published) ----
    prod_dots, picked = stratified_dots_filled(oof_surface)
    if picked != DOT_COUNT:
        raise RuntimeError('production dot count mismatch')
    prod = m2.dots_to_field(prod_dots)
    del prod_dots
    rng2 = np.random.default_rng(70420)
    ids = rng2.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
    prod_random = np.zeros(shape, np.float32)
    prod_random.ravel()[ids] = 1.0

    # ---- Instrument A: per-fold visible-catalogue geometry ----
    arms = ('candidate', 'random_control', 'h33_reference')
    terms_a = {a: 0.0 for a in arms}
    folds_a = {a: [] for a in arms}
    for k, fold in enumerate(folds):
        vis = fold['visible']
        d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
        elig_vis = valid & ~vis & (d_vis >= D_MIN) & (d_vis <= D_MAX)
        surf_k = predict(models[k], cube, elig_vis, d_vis)
        del d_vis, elig_vis
        dots, picked = stratified_dots_filled(surf_k)
        del surf_k
        if picked != DOT_COUNT:
            raise RuntimeError(f'A fold {k}: placed {picked} dots')
        r, t = cropped(fold, m2.dots_to_field(dots), valid)
        terms_a['candidate'] += t
        folds_a['candidate'].append(r)
        del dots
        ids = rng2.choice(np.flatnonzero(valid & ~vis), DOT_COUNT, replace=False)
        f = np.zeros(shape, np.float32)
        f.ravel()[ids] = 1.0
        r, t = cropped(fold, f, valid)
        terms_a['random_control'] += t
        folds_a['random_control'].append(r)
        del f
        r, t = cropped(fold, h33, valid)
        terms_a['h33_reference'] += t
        folds_a['h33_reference'].append(r)
        print('A fold', k, 'done', flush=True)
        gc.collect()
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420,
                                                candidate='candidate')
    summary_a['instrument'] = 'A: shared hide-and-recover catalogue holdout'
    dump(E / 'instrumentA_holdout.json', summary_a)
    dump(E / 'instrumentA_folds.json', folds_a)

    # ---- Instruments B' and B on the production dots ----
    terms_b = {a: 0.0 for a in arms}
    folds_b = {a: [] for a in arms}
    terms_ball = {a: 0.0 for a in arms}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for tag, mask, store in (('prime', proxy_prime, terms_b),
                                 ('all', proxy, terms_ball)):
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
    summary_ball = evaluate_holdout.pooled_summary(terms_ball, draws=1000,
                                                   seed=70420, candidate='candidate')
    summary_ball['instrument'] = 'B: unrestricted SGMC proxy (contains duplication band)'
    dump(E / 'instrumentB_all.json', summary_ball)

    # ---- final-dot uniqueness, then shared writer/validator ----
    tmp_tif = CACHE / 'e5_production_dots.tif'
    if tmp_tif.exists():
        tmp_tif.unlink()
    write_geotiff(tmp_tif, prod, nodata=None)
    audit = uniqueness.compare_to_registry(
        tmp_tif, index, fp, expected_grid=(shape, grid.crs, grid.transform))
    audit['inventory_scope'] = (
        f'{len(records)} single-band 100 m rasters archived in '
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
        'hypothesis': ('E5-1 supervised within-halo ranking: HGB on SGMC '
                       'off-catalogue proxy (d>=3px), leave-one-quadrant-out'),
        'mechanism': ('OOF probability surface from 25 features (19-band stack, '
                      'analytic signal, 3 gradient magnitudes, catalogue geometry); '
                      'P4 emission (one dot per 7x7 stratum at stratum max, 5px NMS) '
                      'plus Amendment-1 same-NMS fill to exactly 37,654 binary dots, '
                      'band 2.4-32 px'),
        'non_fault_mimic': ('SGMC compilation/redrawing bias and lithologic '
                            'contacts sharing the potential-field signature'),
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': "HOLDOUT-DTI (A) and PROXY-DTI (B/B'); neither organizer-confirmed",
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
        'canary_worst_single_feature_auc': worst,
        'oof_auc_by_quadrant': oof_auc,
        'correlation_overlap_vs_registry': {
            'surface_stage': {
                'worst_spearman_full_footprint': surf_audit['worst_spearman_full_footprint'],
                'worst_rho_submission': surf_audit['worst_rho_submission'],
                'duplicate_count': surf_audit['duplicate_count']},
            'final_dots_stage': {
                'rasters_checked': audit['registry_rasters_checked'],
                'inventory_scope': audit['inventory_scope'],
                'worst_mutual_overlap': audit['worst_dot_overlap'],
                'worst_mutual_submission': audit['worst_overlap_submission'],
                'worst_forward_overlap': audit['worst_forward_overlap'],
                'worst_forward_submission': audit['worst_forward_submission'],
                'worst_spearman_full_footprint': audit['worst_spearman_full_footprint'],
                'worst_rho_submission': audit['worst_rho_submission'],
                'worst_jaccard': audit['worst_jaccard_dot_sets'],
                'duplicate': duplicate}},
        'raster_sha256': receipt['sha256'] if receipt else None,
        'raster_sha256_reason': None if receipt else 'uniqueness gate failed; no TIFF written',
        'validator_output': validated,
        'submission_name': NAME,
        'submission_note': NOTE,
        'note_chars': len(NOTE),
        'download_ok': bool(receipt),
        'submit_recommended': promoted,
        'weekly_slots_used': 0,
        'experiment_count_this_lane': 1,
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['scripts/run_experiment_e5.py',
                                  'scripts/run_experiment_v4.py',
                                  'docs/preregistration-e5.md']},
        'registered_parameters': dict(dot_count=DOT_COUNT, block_px=7, nms_px=5.0,
                                      d_min_px=D_MIN, d_max_px=D_MAX,
                                      b_prime_gap_px=GAP_PX, seed=SEED,
                                      neg_cap=NEG_CAP,
                                      model='HistGradientBoostingClassifier(max_iter=300,'
                                            'learning_rate=0.06,max_leaf_nodes=31,'
                                            'min_samples_leaf=40,l2=1.0)'),
    }
    dump(E / 'run_card.json', card)
    print(json.dumps(card, indent=2, default=float), flush=True)


if __name__ == '__main__':
    main()
