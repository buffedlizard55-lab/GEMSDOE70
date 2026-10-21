#!/usr/bin/env python3
"""Experiment 5 (in-session 1 of 3): supervised within-halo ranking (H-P5-1).

Registered in docs/hypotheses.md (Phase-5 addendum) before this run.
Instruments A (shared hide-and-recover holdout) and B'/B (SGMC proxy, LOQO),
arms candidate / random control / H33 reference / P4 reference, corrected
mutual-overlap uniqueness on the surface BEFORE placement and on the final
dots, shared writer and validator, rich run card.
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
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems70 import method_v2 as m2
from gems70 import method_v5 as m5
from restore_data import DATA, PINS, sha

E = ROOT / 'evidence' / 'p5hgb'
CACHE = ROOT / '.cache'
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry' / 'rasters'
H33 = CLONE / 'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'
P4 = ROOT / 'docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif'
P4_SHA = '0fd1ad9ef58c9bbe0ed1781d36a31f76424db11930502623153dd69581ab35e7'

DOT_COUNT = m5.DOT_COUNT
GAP_PX = 3.0
NAME = 'gems70-p5-halo-rank-hgb-37654-20261020'
NOTE = ('P5 supervised within-halo ranking: HGB on 19-band stack + catalogue geometry, '
        'LOQO on SGMC proxy; 37654 stratified dots')
ARMS = ('candidate', 'random_control', 'h33_reference', 'p4_reference')


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False, default=float) + '\n')
    tmp.replace(path)


def cropped(fold, p, valid):
    """Shared cropped evaluation (verbatim Phase-4 helper)."""
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
    if len(NOTE) > 140:
        raise ValueError('submission note exceeds 140 characters')
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    if sha(H33) != H33_SHA:
        raise ValueError('H33 SHA mismatch')
    if sha(P4) != P4_SHA:
        raise ValueError('P4 reference SHA mismatch')

    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue

    # ------------------------------------------------------------ valid mask
    # All 19 bands must be finite (the model needs finite inputs); this drops
    # exactly 3 band cells versus the Phase-4 rtp-only definition (measured).
    valid = np.ones(fp.shape, bool)
    with rasterio.open(DATA / 'training_features.tif') as src:
        for b in range(1, 20):
            a = src.read(b)
            valid &= np.isfinite(a) & (a > -1e30)
            del a
    valid &= fp
    valid = ndi.binary_erosion(valid, iterations=12)
    if not valid.any():
        raise ValueError('empty valid domain')

    # ------------------------------------------------------------ references
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
    h33 = np.where(np.isfinite(h33) & (h33 > 0.5) & fp, 1.0, 0.0).astype(np.float32)
    with rasterio.open(P4) as src:
        p4 = src.read(1).astype(np.float32)
    p4 = np.where(np.isfinite(p4) & (p4 > 0.5) & fp, 1.0, 0.0).astype(np.float32)
    if int(p4.sum()) != DOT_COUNT:
        raise ValueError('P4 reference is not the expected 37,654-dot field')

    # ----------------------------------------------------- labels and quadrants
    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    d_cat = ndi.distance_transform_edt(~cat)
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_cat >= GAP_PX)
    quad = holdout.quadrant_ids(fp)

    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)

    # ---------------------------------------------- canary cells per A fold
    rng_neg = np.random.default_rng(70522)
    fold_can = []
    for fold in folds:
        pos = np.flatnonzero(fold['truth'])
        act = np.flatnonzero(valid & fold['region'] & ~fold['visible'])
        neg = rng_neg.choice(act, 50_000, replace=False)
        fold_can.append((pos, neg))

    # ------------------------------- geometry: one full-grid pass per variant
    def full_geometry(catalogue):
        d = ndi.distance_transform_edt(~catalogue).astype(np.float32)
        u, v = m2.tip_kernels(catalogue, catalogue.shape)
        return d, u, v

    d_full, u_full, v_full = full_geometry(cat)
    band_full = valid & ~cat & (d_full >= m5.D_MIN) & (d_full <= m5.D_MAX)

    fold_band = []
    geom_fold_U = []      # (N_U, 3) geometry columns at U cells, per fold
    geom_fold_can = []    # (n_can_k, 3) geometry at the fold's canary cells

    # One full-grid geometry pass per fold (bands need d_v; canary and U-cell
    # extractions happen in the same pass so nothing is computed twice).
    fold_d_vis = []
    for fold in folds:
        d_v, u_v, v_v = full_geometry(fold['visible'])
        fold_band.append(valid & ~fold['visible']
                         & (d_v >= m5.D_MIN) & (d_v <= m5.D_MAX))
        fold_d_vis.append((d_v, u_v, v_v))

    union = band_full.copy()
    for b in fold_band:
        union |= b
    uy, ux = np.nonzero(union)
    u_flat = (uy.astype(np.int64) * union.shape[1] + ux.astype(np.int64))

    # ------------------------------------------------------- stack at U cells
    stack_U = np.empty((len(uy), 19), np.float32)
    with rasterio.open(DATA / 'training_features.tif') as src:
        for b in range(19):
            a = src.read(b + 1)
            stack_U[:, b] = a[uy, ux]
            del a
    if not np.isfinite(stack_U).all():
        raise ValueError('non-finite stack values inside the union domain')

    # Extract fold geometry at U cells and canary cells, then free full grids.
    for k, (d_v, u_v, v_v) in enumerate(fold_d_vis):
        geom_fold_U.append(np.stack([d_v[uy, ux], u_v[uy, ux], v_v[uy, ux]], axis=1))
        pos, neg = fold_can[k]
        cells = np.concatenate([pos, neg])
        geom_fold_can.append(np.stack([d_v.ravel()[cells], u_v.ravel()[cells],
                                       v_v.ravel()[cells]], axis=1))
        fold_d_vis[k] = None
        del d_v, u_v, v_v
    geom_full_U = np.stack([d_full[uy, ux], u_full[uy, ux], v_full[uy, ux]], axis=1)
    del d_full, u_full, v_full
    q_u = quad[uy, ux]

    band_full_idx = np.flatnonzero(band_full[uy, ux])
    y_band = proxy_prime[uy, ux][band_full_idx]
    X_band = np.concatenate([stack_U[band_full_idx], geom_full_U[band_full_idx]], axis=1)

    # ------------------------------------------------------------- canaries
    can_pos = np.concatenate([c[0] for c in fold_can])
    can_neg = np.concatenate([c[1] for c in fold_can])
    can_all = np.concatenate([can_pos, can_neg])
    can_y = np.concatenate([np.ones(len(can_pos), bool), np.zeros(len(can_neg), bool)])
    stack_can = np.empty((len(can_all), 19), np.float32)
    order = np.argsort(can_all)
    can_sorted = can_all[order]
    with rasterio.open(DATA / 'training_features.tif') as src:
        for b in range(19):
            a = src.read(b + 1)
            stack_can[order, b] = a.ravel()[can_sorted]
            del a
    if not np.isfinite(stack_can).all():
        raise ValueError('non-finite stack values at canary cells')
    geom_can = np.concatenate(geom_fold_can, axis=0)
    if len(geom_can) != len(can_all):
        raise ValueError('canary geometry alignment broken')
    X_can = np.concatenate([stack_can, geom_can], axis=1)

    canary_a = {}
    for j, fname in enumerate(m5.FEATURE_NAMES):
        canary_a[fname] = m5.canary(m5.auc(can_y, X_can[:, j]))
    canary_a['_stop_rule'] = 'any feature AUC > 0.90 vs instrument-A withheld truth'
    canary_p = {}
    for j, fname in enumerate(m5.FEATURE_NAMES):
        canary_p[fname] = m5.canary(m5.auc(y_band, X_band[:, j]))
    canary_p['_note'] = ('label-structure disclosure: proxy positives hug the catalogue, so '
                         'geometry features can rank them without any physics; reported, '
                         'not a stop rule')

    # ------------------------------------------------------------ models (LOQO)
    models = {}
    oof_prob = np.zeros(len(band_full_idx), np.float32)
    for k in range(4):
        Xk, yk, meta = m5.select_rows(X_band, y_band, q_u[band_full_idx],
                                      n_negatives=m5.N_NEGATIVES,
                                      neg_seed=m5.NEG_SEED, exclude_quad=k)
        model = m5.make_model().fit(Xk, yk)
        models[k] = model
        m_sel = q_u[band_full_idx] == k
        oof_prob[m_sel] = m5.predict_cells(model, stack_U[band_full_idx][m_sel],
                                           geom_full_U[band_full_idx][m_sel])
        print(f'LOQO model {k} trained ({meta["positives"]} pos / {meta["negatives"]} neg)',
              flush=True)
        del Xk, yk
    oof_auc = float(roc_auc_score(y_band, oof_prob))
    canary_oof = m5.canary(oof_auc)
    canary_oof['description'] = 'LOQO out-of-fold model AUC vs SGMC proxy labels (band domain)'
    dump(E / 'canaries.json', dict(
        evidence_class='LEAKAGE-CANARY',
        instrument_a_truth=canary_a, proxy_labels=canary_p, model_oof=canary_oof,
        stop=(any(c['suspected_leakage'] for c in canary_a.values() if isinstance(c, dict))
              or canary_oof['suspected_leakage']),
        registered_stop='feature AUC > 0.90 vs A-truth, or OOF model AUC > 0.90'))
    if canary_oof['suspected_leakage'] or any(
            c['suspected_leakage'] for c in canary_a.values() if isinstance(c, dict)):
        raise ValueError('leakage canary fired; run stopped per rule 4')

    # --------------------------------------------------------- production model
    Xp, yp, meta_p = m5.select_rows(X_band, y_band, q_u[band_full_idx],
                                    n_negatives=m5.N_NEGATIVES, neg_seed=m5.NEG_SEED)
    prod_model = m5.make_model().fit(Xp, yp)
    print(f'production model trained ({meta_p["positives"]} pos / {meta_p["negatives"]} neg)',
          flush=True)
    del Xp, yp

    prod_prob = m5.predict_cells(prod_model, stack_U[band_full_idx], geom_full_U[band_full_idx])
    surface = m5.scatter(u_flat[band_full_idx], prod_prob, fp.shape)
    if not np.isfinite(surface).all() or surface.min() < 0 or surface.max() > 1:
        raise ValueError('production surface outside [0,1] or non-finite')

    # ------------------------------------------ surface uniqueness BEFORE placement
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != grid.shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    surface_audit = uniqueness.compare_array_to_registry(
        surface, index, fp, expected_grid=(grid.shape, grid.crs, grid.transform))
    surface_audit['inventory_scope'] = (
        f'{len(records)} single-band 100 m rasters archived in '
        'buffedlizard55-lab/60GEMSDOE registry/rasters; not an organizer registry and not exhaustive')
    surface_audit['stage'] = 'production score surface (continuous probability) before placement'
    dump(E / 'surface_uniqueness.json', surface_audit)
    if surface_audit['duplicate_count'] > 0:
        raise ValueError('surface pre-check found a duplicate; stopping before placement')

    # ----------------------------------------------------------- production dots
    prod_dots, picked, topup = m5.stratified_dots(surface, return_topup=True)
    if picked != DOT_COUNT:
        raise RuntimeError(f'placed {picked} production dots')
    prod = m2.dots_to_field(prod_dots)
    del prod_dots
    rng = np.random.default_rng(70520)
    ids = rng.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
    prod_random = np.zeros(grid.shape, np.float32)
    prod_random.ravel()[ids] = 1.0

    # ------------------------------- A-truth contamination disclosure (registered)
    d_proxy = ndi.distance_transform_edt(~proxy)
    truth_all = np.zeros(fp.shape, bool)
    for fold in folds:
        truth_all |= fold['truth']
    near = float((d_proxy[truth_all] <= 3.0).mean())
    del d_proxy

    # ------------------------------------------------------------- instrument A
    terms_a = {a: 0.0 for a in ARMS}
    folds_a = {a: [] for a in ARMS}
    for k, fold in enumerate(folds):
        idx_v = np.flatnonzero(fold_band[k][uy, ux])
        score_v = m5.scatter(u_flat[idx_v],
                             m5.predict_cells(prod_model, stack_U[idx_v],
                                              geom_fold_U[k][idx_v]),
                             fp.shape)
        dots_v, picked_v = m5.stratified_dots(score_v)
        if picked_v != DOT_COUNT:
            raise RuntimeError(f'A fold {k}: placed {picked_v} dots')
        r, t = cropped(fold, m2.dots_to_field(dots_v), valid)
        terms_a['candidate'] += t
        folds_a['candidate'].append(r)
        del dots_v, score_v
        ids = rng.choice(np.flatnonzero(valid & ~fold['visible']), DOT_COUNT, replace=False)
        f = np.zeros(grid.shape, np.float32)
        f.ravel()[ids] = 1.0
        for arm, p in (('random_control', f), ('h33_reference', h33), ('p4_reference', p4)):
            r, t = cropped(fold, p, valid)
            terms_a[arm] += t
            folds_a[arm].append(r)
        print('A fold', k, 'done', flush=True)
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70520,
                                                candidate='candidate')
    summary_a['instrument'] = 'A: shared hide-and-recover catalogue holdout'
    summary_a['candidate_construction'] = ('production model, fold-visible catalogue geometry, '
                                           'fold-band domain, stratified emission')
    dump(E / 'instrumentA_holdout.json', summary_a)
    dump(E / 'instrumentA_folds.json', folds_a)

    # ----------------------------------------------------------- instruments B
    quad_terms = {'prime': {a: 0.0 for a in ARMS}, 'all': {a: 0.0 for a in ARMS}}
    quad_folds = {a: [] for a in ARMS}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        score_k = m5.scatter(u_flat[band_full_idx],
                             m5.predict_cells(models[k], stack_U[band_full_idx],
                                              geom_full_U[band_full_idx]),
                             fp.shape)
        dots_k, picked_k = m5.stratified_dots(score_k)
        if picked_k != DOT_COUNT:
            raise RuntimeError(f'B quadrant {k}: placed {picked_k} dots')
        cand_k = m2.dots_to_field(dots_k)
        del dots_k, score_k
        for tag, mask in (('prime', proxy_prime), ('all', proxy)):
            fold = dict(region=region, truth=mask & region & ~cat, visible=cat,
                        masked_known=cat, hidden_all=np.zeros_like(cat))
            for arm, p in (('candidate', cand_k), ('random_control', prod_random),
                           ('h33_reference', h33), ('p4_reference', p4)):
                r, t = cropped(fold, p, valid)
                quad_terms[tag][arm] += t
                if tag == 'prime':
                    quad_folds[arm].append(r)
        print('B quadrant', k, 'done', flush=True)
        del cand_k
    summary_b = evaluate_holdout.pooled_summary(quad_terms['prime'], draws=1000, seed=70520,
                                                candidate='candidate')
    summary_b['instrument'] = "B': SGMC proxy truth restricted to d_cat >= 3 px (LOQO candidate)"
    summary_b['proxy_positive_pixels_prime'] = int(proxy_prime.sum())
    summary_b['proxy_positive_pixels_all'] = int(proxy.sum())
    summary_b['label_source_shared_with_training'] = True
    dump(E / 'instrumentB_prime.json', summary_b)
    dump(E / 'instrumentB_prime_folds.json', quad_folds)
    summary_ball = evaluate_holdout.pooled_summary(quad_terms['all'], draws=1000, seed=70520,
                                                   candidate='candidate')
    summary_ball['instrument'] = ('B: unrestricted SGMC proxy (contains duplication band; '
                                  'LOQO candidate)')
    summary_ball['label_source_shared_with_training'] = True
    dump(E / 'instrumentB_all.json', summary_ball)

    # ---------------------------------------------------- final uniqueness audit
    tmp_tif = CACHE / 'production_dots_p5.tif'
    tmp_tif.parent.mkdir(parents=True, exist_ok=True)
    if tmp_tif.exists():
        tmp_tif.unlink()
    write_geotiff(tmp_tif, prod, nodata=None)
    audit = uniqueness.compare_to_registry(tmp_tif, index, fp,
                                           expected_grid=(grid.shape, grid.crs, grid.transform))
    audit['inventory_scope'] = surface_audit['inventory_scope']
    audit['stage'] = 'final production dots (37,654 binary)'
    dump(E / 'uniqueness.json', audit)
    duplicate = bool(audit['unique'] is False or audit['duplicate_count'] > 0)

    # ------------------------------------------------------------------ writer
    receipt = validated = None
    if not duplicate:
        from gems57 import submission_writer
        receipt = submission_writer.write_submission(
            ROOT / 'docs' / 'downloads' / f'{NAME}.tif', prod,
            ROOT / 'data/bridge/sample_submission.tif', fp,
            note=NOTE, name=NAME, catalogue=cat,
            metadata={'evidence_class': "HOLDOUT-DTI (A) + PROXY-DTI LOQO (B/B'); not organizer-confirmed"})
        validated = receipt['validator']
    dump(E / 'submission_receipt.json', dict(receipt=receipt, validated=validated,
                                             duplicate=duplicate))

    # -------------------------------------------------------------------- gates
    a, b = summary_a['scores'], summary_b['scores']
    db = summary_b['paired_differences']
    da = summary_a['paired_differences']
    gate_a = a['candidate']['dti'] >= a['h33_reference']['dti']
    gate_b = bool(db['h33_reference']['delta'] > 0 and db['h33_reference']['ci95'][0] > 0)
    promoted = bool(not duplicate and validated and gate_a and gate_b)

    history = {}
    prior_path = ROOT / 'evidence/run_card.json'
    if prior_path.is_file():
        try:
            prior = json.loads(prior_path.read_text())
        except json.JSONDecodeError:
            prior = {}
        if all(k in prior for k in ('hypothesis', 'instrument_a_holdout',
                                    'instrument_b_prime_proxy')):
            history = dict(prior.get('experiment_history', {}))
            history['phase4'] = {
                'hypothesis': prior['hypothesis'], 'verdict': prior['verdict'],
                'instrument_a': prior['instrument_a_holdout'],
                'instrument_b_prime': prior['instrument_b_prime_proxy'],
                'note': 'archived under evidence/phase4'}
    history['p5hgb'] = {
        'hypothesis': 'H-P5-1 supervised within-halo ranking (this run)',
        'verdict': 'promote' if promoted else 'negative',
        'instrument_a': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                         for k, v in a.items()},
        'instrument_b_prime': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                               for k, v in b.items()},
        'model_oof_auc': oof_auc}

    worst_can_a = max((c['auc'] for c in canary_a.values()
                       if isinstance(c, dict) and c['auc'] is not None), default=None)
    worst_can_p = max((c['auc'] for c in canary_p.values()
                       if isinstance(c, dict) and c['auc'] is not None), default=None)
    card = {
        'hypothesis': 'H-P5-1 supervised within-halo ranking on the SGMC off-catalogue proxy',
        'mechanism': ('HistGradientBoostingClassifier over 19 physics bands + visible-catalogue '
                      'geometry (d, tip u, v); LOQO by spatial quadrant; emission = P4 '
                      'coverage-stratified 7x7 blocks, 37654 dots, 5-px NMS'),
        'non_fault_mimic': ('SGMC cartographic generalization: mapper/digitization conventions '
                            'learnable as if geology'),
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': "HOLDOUT-DTI (A) and PROXY-DTI LOQO (B/B'); neither organizer-confirmed",
        'instrument_a_holdout': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                 for k, v in a.items()},
        'instrument_b_prime_proxy': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                     for k, v in b.items()},
        'instrument_b_unrestricted': {k: {kk: v[kk] for kk in ('dti', 'ci95')}
                                      for k, v in summary_ball['scores'].items()},
        'paired_a_vs_h33': da['h33_reference'],
        'paired_a_vs_p4': da['p4_reference'],
        'paired_b_prime_vs_h33': db['h33_reference'],
        'paired_b_prime_vs_p4': db['p4_reference'],
        'gate_a_candidate_ge_h33': bool(gate_a),
        'gate_b_prime_candidate_gt_h33_significant': gate_b,
        'canaries': {
            'stop_rule': 'feature AUC > 0.90 vs A-truth, or OOF model AUC > 0.90',
            'fired': False,
            'worst_feature_auc_vs_a_truth': worst_can_a,
            'worst_feature_auc_vs_proxy_labels': worst_can_p,
            'model_oof_auc_vs_proxy': oof_auc,
            'proxy_label_auc_note': canary_p['_note'],
        },
        'contamination_disclosure': {
            'a_truth_pixels_within_3px_of_proxy': near,
            'b_label_source_shared_with_training': True,
            'text': ("B/B' share the SGMC label source with training (LOQO spatial split only); "
                     'instrument A is the only label-independent gate. A fraction of A-truth '
                     'pixels lies within kernel range of proxy pixels (SGMC re-draws), bounded '
                     'above by the measured fraction.'),
        },
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
        'uniqueness_detail': {
            'registry_rasters_checked': audit['registry_rasters_checked'],
            'unique': audit['unique'], 'duplicate_count': audit['duplicate_count'],
            'worst_dot_overlap': audit['worst_dot_overlap'],
            'worst_overlap_submission': audit['worst_overlap_submission'],
            'worst_forward_overlap': audit['worst_forward_overlap'],
            'worst_forward_submission': audit['worst_forward_submission'],
            'worst_spearman_full_footprint': audit['worst_spearman_full_footprint'],
            'worst_rho_submission': audit['worst_rho_submission'],
            'worst_jaccard_dot_sets': audit['worst_jaccard_dot_sets'],
            'inventory_scope': audit['inventory_scope'],
            'overlap_definition': audit['overlap_definition'],
            'surface_precheck': {
                'worst_spearman_full_footprint': surface_audit['worst_spearman_full_footprint'],
                'duplicate_count': surface_audit['duplicate_count'],
                'stage': surface_audit['stage'],
            },
        },
        'raster_sha256': receipt['sha256'] if receipt else None,
        'raster_sha256_reason': None if receipt else 'uniqueness gate failed; no TIFF written',
        'validator_output': validated,
        'submission_name': NAME,
        'submission_note': NOTE,
        'note_chars': len(NOTE),
        'download_and_submit_ok': promoted,
        'download_ok': bool(receipt is not None),
        'submit_recommended': promoted,
        'weekly_slots_used': 0,
        'experiment_count': 5,
        'in_session_experiment': '1 of 3',
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['src/gems70/method_v5.py', 'scripts/run_experiment_v5.py']},
        'registered_parameters': dict(
            dot_count=DOT_COUNT, block_px=m5.BLOCK, nms_px=m5.NMS,
            d_min_px=m5.D_MIN, d_max_px=m5.D_MAX,
            n_negatives=m5.N_NEGATIVES, seed=m5.SEED, neg_seed=m5.NEG_SEED,
            features=m5.FEATURE_NAMES, model='HistGradientBoostingClassifier(300, 0.06, 31)',
            loqo='holdout.quadrant_ids', b_prime_gap_px=GAP_PX,
            valid_mask=('all 19 bands finite & > -1e30 & footprint, eroded 12 px '
                        '(3 band cells fewer than the Phase-4 rtp-only mask)'),
            emission_topup=(f'{topup} of {DOT_COUNT} production dots placed by the registered '
                            'pass-2 completion (best NMS-feasible cell of empty strata); '
                            'pass 1 is byte-identical to Phase-4, see docs/hypotheses.md '
                            'Phase-5 implementation amendment')),
        'phase_evidence': {'dir': 'evidence/p5hgb',
                           'canaries': 'canaries.json',
                           'uniqueness': 'uniqueness.json',
                           'surface_uniqueness': 'surface_uniqueness.json',
                           'instrumentA': 'instrumentA_holdout.json',
                           'instrumentB_prime': 'instrumentB_prime.json'},
        'experiment_history': history,
    }
    if receipt:
        card['artifact'] = f'docs/downloads/{NAME}.tif'
        card['artifact_zip'] = f'docs/downloads/{NAME}.zip'
        card['artifact_receipt'] = f'docs/downloads/{NAME}.json'
        card['decision_note'] = (
            'File is unique, format-validated and downloadable. Gates ' +
            ('PASSED: candidate beat H33 significantly on B\' and matched it on A — '
             'promoted to the selector step (no weekly slot used).'
             if promoted else
             'failed; it is NOT promoted. Submitting is a deliberate test, not a validated improvement.'))
    dump(E / 'run_card.json', card)  # lane card only; the canonical card is a merge decision
    print(json.dumps({k: card[k] for k in ('verdict', 'gate_a_candidate_ge_h33',
                                           'gate_b_prime_candidate_gt_h33_significant',
                                           'raster_sha256', 'elapsed_seconds')}, indent=2),
          flush=True)
    print('A:', {k: round(v['dti'], 4) for k, v in a.items()}, flush=True)
    print("B':", {k: round(v['dti'], 4) for k, v in b.items()}, flush=True)
    print('B:', {k: round(v['dti'], 4) for k, v in summary_ball['scores'].items()}, flush=True)


if __name__ == '__main__':
    main()
