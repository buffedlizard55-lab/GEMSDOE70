#!/usr/bin/env python3
"""S3 experiment 2 of <=3: marginal-matched proxy ranking (docs/preregistration-s3-e2.md)."""
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
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems70 import supervised as sv
from restore_data import DATA, PINS, sha
from run_experiment_v4 import cropped
from run_experiment_s3 import (AUX, CACHE, H33, H33_SHA, P4_SHA, REG, SGMC, SGMC_SHA, SEED,
                               GAP_PX, binary, dump, fit, log, predict)

E = ROOT / 'evidence' / 's3' / 'e2'
E1_TIF = ROOT / 'docs/downloads/gems70-s3-proxyrank-h33spacing-37654-20261020.tif'
NAME = 'gems70-s3e2-marginmatched-proxyrank-37654-20261020'
NOTE = 'S3-E2 proxy-trained GBM ranks within H33 distance x slope strata; 37654 dots, 2.83px spacing'


def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    for p, pin in ((H33, H33_SHA), (SGMC, SGMC_SHA)):
        if sha(p) != pin:
            raise ValueError(f'pin mismatch: {p}')
    e1_sha = sha(E1_TIF)
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    shape = grid.shape
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp = src.read(2).astype(np.float32)
    valid = ndi.binary_erosion(np.isfinite(rtp) & (rtp > -1e30) & fp, iterations=12)
    del rtp
    vidx = np.flatnonzero(valid)
    pos_of = np.full(valid.size, -1, np.int64)
    pos_of[vidx] = np.arange(vidx.size)
    X_phys, phys_names = sv.physics_matrix(DATA / 'training_features.tif', AUX, valid)
    X_geo, geo_names, d_cat = sv.geometry_matrix(cat, valid)
    log('features', X_phys.shape, X_geo.shape)
    with rasterio.open(AUX / 'topo_10m_derived_100m_u8.tif') as src:
        slope = src.read(1)
    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_cat >= GAP_PX)
    del sgmc
    domain = valid & ~cat & (d_cat >= sv.D_MIN)
    dom_rows = pos_of[np.flatnonzero(domain)]
    y = proxy_prime.ravel()[vidx]
    quad = holdout.quadrant_ids(fp)
    quad_rows = quad.ravel()[vidx]
    region_rows = {k: (ndi.binary_erosion(quad == k, iterations=12) & fp).ravel()[vidx] for k in range(4)}
    in_domain = np.zeros(vidx.size, bool)
    in_domain[dom_rows] = True

    h33 = binary(H33, fp)
    sid, slope_q = sv.strata_map(d_cat, slope, domain)
    quota = sv.quotas_from_reference(sid, h33 > 0)
    dump(E / 'strata.json', dict(dist_edges_px=[float(x) if x != float('inf') else 'inf' for x in sv.DIST_EDGES_E2],
                                 slope_p90_u8_quartiles=slope_q, quota=quota.tolist(),
                                 h33_dots_in_domain=int(((h33 > 0) & domain).sum())))
    log('quota total', int(quota.sum()))

    # LOQO out-of-fold ranks (E1 candidate feature set and parameters)
    oof = np.zeros(vidx.size, np.float32)
    aucs = []
    for k in range(4):
        tr = np.flatnonzero(in_domain & (quad_rows != k) &
                            np.any([region_rows[j] for j in range(4) if j != k], axis=0))
        te = np.flatnonzero(in_domain & (quad_rows == k))
        model, _, _ = fit(X_phys, X_geo, tr, y, np.random.default_rng(SEED + k))
        s = predict(model, X_phys, X_geo, te)
        oof[te] = sv.rank_within(s, np.zeros(s.size, np.int8), np.ones(s.size, bool))
        t = region_rows[k][te]
        aucs.append(float(roc_auc_score(y[te][t], s[t])))
        del model, s
        gc.collect()
        log('LOQO', k, round(aucs[-1], 4))

    def to_map(rows_vals, dom):
        m = np.zeros(shape, np.float32)
        m.ravel()[vidx] = rows_vals
        return np.where(dom, m, 0.0).astype(np.float32)

    rng = np.random.default_rng(SEED)
    arms = {}
    dots, short = sv.place_quota(to_map(oof, domain), sid, quota)
    if short:
        raise RuntimeError(f'E2 candidate quota shortfall {short}')
    arms['candidate'] = dots.astype(np.float32)
    order = rng.permutation(np.flatnonzero(sid >= 0))
    dots, short = sv.place_quota(None, sid, quota, order=order)
    if short:
        raise RuntimeError(f'random-stratified quota shortfall {short}')
    arms['random_stratified'] = dots.astype(np.float32)
    ids = rng.choice(np.flatnonzero(domain), sv.DOT_COUNT, replace=False)
    rnd = np.zeros(shape, np.float32)
    rnd.ravel()[ids] = 1.0
    arms['random_control'] = rnd
    arms['h33_reference'] = h33
    arms['s3_e1_candidate'] = binary(E1_TIF, fp)
    log('arms', {k: int(v.sum()) for k, v in arms.items()})

    terms_b, terms_ball = {a: 0.0 for a in arms}, {a: 0.0 for a in arms}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for mask, store in ((proxy_prime, terms_b), (proxy, terms_ball)):
            fold = dict(region=region, truth=mask & region & ~cat, visible=cat,
                        masked_known=cat, hidden_all=np.zeros_like(cat))
            for arm, p in arms.items():
                store[arm] += cropped(fold, p, valid)[1]
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=SEED, candidate='candidate')
    summary_b['instrument'] = "B': SGMC proxy, d_cat >= 3 px; LOQO out-of-fold"
    dump(E / 'instrumentB_prime.json', summary_b)
    summary_ball = evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=SEED, candidate='candidate')
    dump(E / 'instrumentB_all.json', summary_ball)
    log('B prime', {k: round(v['dti'], 4) for k, v in summary_b['scores'].items()})

    q75 = slope_q[2]
    def marginals(p):
        m = (p > 0) & fp
        dd = d_cat[m]
        return dict(n=int(m.sum()), steep_top_quartile=float((slope[m] > q75).mean()),
                    d_quantiles_5_25_50_75_95=[float(v) for v in np.percentile(dd, [5, 25, 50, 75, 95])])
    marg = {k: marginals(v) for k, v in arms.items()}
    del arms
    gc.collect()

    # production
    tr = np.flatnonzero(in_domain & np.any([region_rows[j] for j in range(4)], axis=0))
    prod_model, _, _ = fit(X_phys, X_geo, tr, y, np.random.default_rng(SEED + 99))
    s = predict(prod_model, X_phys, X_geo, dom_rows)
    rr = np.zeros(vidx.size, np.float32)
    rr[dom_rows] = sv.rank_within(s, quad_rows[dom_rows], np.ones(s.size, bool))
    surface = to_map(rr, domain)
    del s, rr
    dots, short = sv.place_quota(surface, sid, quota)
    if short:
        raise RuntimeError('production quota shortfall')
    prod = dots.astype(np.float32)
    marg['production'] = marginals(prod)
    log('production', marg['production'])

    # instrument A
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    terms_a = {a: 0.0 for a in ('candidate', 'random_stratified', 'h33_reference')}
    for k, fold in enumerate(folds):
        vis = fold['visible']
        Xg, _, dv = sv.geometry_matrix(vis, valid)
        dom_a = valid & ~vis & (dv >= sv.D_MIN)
        sid_a, _ = sv.strata_map(dv, slope, dom_a)
        rows_a = pos_of[np.flatnonzero(dom_a)]
        s = predict(prod_model, X_phys, Xg, rows_a)
        ra = np.zeros(vidx.size, np.float32)
        ra[rows_a] = sv.rank_within(s, quad_rows[rows_a], np.ones(s.size, bool))
        cand, short_c = sv.place_quota(to_map(ra, dom_a), sid_a, quota)
        rs, short_r = sv.place_quota(None, sid_a, quota, order=rng.permutation(np.flatnonzero(sid_a >= 0)))
        for arm, p in (('candidate', cand), ('random_stratified', rs), ('h33_reference', h33)):
            terms_a[arm] += cropped(fold, p.astype(np.float32), valid)[1]
        del Xg, dv, sid_a, s, ra, cand, rs
        gc.collect()
        log('A fold', k, 'shortfalls', short_c, short_r)
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=SEED, candidate='candidate')
    dump(E / 'instrumentA_holdout.json', summary_a)
    del X_phys, X_geo
    gc.collect()

    # uniqueness
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    eg = (grid.shape, grid.crs, grid.transform)
    surf = uniqueness.compare_array_to_registry(np.where(fp, surface, 0).astype(np.float32), index, fp,
                                                expected_grid=eg, include_reverse=False)
    surf_rho = surf['worst_spearman_full_footprint']
    tmp_tif = CACHE / 'production_dots_s3e2.tif'
    if tmp_tif.exists():
        tmp_tif.unlink()
    write_geotiff(tmp_tif, prod, nodata=None)
    audit = uniqueness.compare_to_registry(tmp_tif, index, fp, expected_grid=eg)
    audit['inventory_scope'] = f'{len(records)} single-band rasters in 60GEMSDOE registry/rasters; not exhaustive'
    # E1 sibling is not in the registry; measure it explicitly
    e1 = binary(E1_TIF, fp) > 0
    near_e1 = ndi.binary_dilation(e1, structure=np.ones((7, 7), bool) & (np.hypot(*np.mgrid[-3:4, -3:4]) <= 3))
    near_p = ndi.binary_dilation(prod > 0, structure=np.ones((7, 7), bool) & (np.hypot(*np.mgrid[-3:4, -3:4]) <= 3))
    e1_overlap = min(float(near_e1[prod > 0].mean()), float(near_p[e1].mean()))
    audit['sibling_s3_e1_mutual_overlap'] = e1_overlap
    dump(E / 'uniqueness.json', audit)
    dump(E / 'surface_uniqueness.json', dict(worst_spearman_full_footprint=surf_rho,
                                             worst_rho_submission=surf['worst_rho_submission'],
                                             rasters_checked=surf['registry_rasters_checked']))
    duplicate = bool(audit['unique'] is False or audit['duplicate_count'] > 0 or surf_rho > 0.90)
    log('uniqueness mutual', audit['worst_dot_overlap'], 'rho', audit['worst_spearman_full_footprint'],
        'surface rho', surf_rho, 'E1 sibling overlap', e1_overlap)

    b, a = summary_b['scores'], summary_a['scores']
    db = summary_b['paired_differences']
    g1 = bool(db['h33_reference']['delta'] > 0 and db['h33_reference']['ci95'][0] > 0)
    g2 = bool(db['random_stratified']['delta'] > 0 and db['random_stratified']['ci95'][0] > 0)
    g3 = bool(a['candidate']['dti'] >= a['h33_reference']['dti'])
    g5 = abs(marg['production']['steep_top_quartile'] - marg['h33_reference']['steep_top_quartile']) <= 0.03
    pre = bool(g1 and g2 and g3 and g5 and not duplicate)
    suffix = '' if pre else '-DO-NOT-SUBMIT'
    receipt = None
    if not duplicate:
        from gems57 import submission_writer
        receipt = submission_writer.write_submission(
            ROOT / 'docs/downloads' / f'{NAME}{suffix}.tif', prod, ROOT / 'data/bridge/sample_submission.tif',
            fp, note=NOTE, name=NAME + suffix, catalogue=cat,
            metadata={'evidence_class': "PROXY-DTI (B') + HOLDOUT-DTI (A); not organizer-confirmed"})
    validated = receipt['validator'] if receipt else None
    promoted = bool(pre and validated and validated.get('all_checks_passed'))

    def pick(s):
        return {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')} for k, v in s.items()}

    card = {
        'hypothesis': 'S3-E2: proxy-trained physics ranking adds information within H33 distance x slope strata',
        'mechanism': ('E1 LOQO HistGradientBoosting (66 features) ranks pixels; greedy NMS r=2.5 px with per-stratum '
                      'quotas equal to H33 counts over 11 distance bands x 5 slope classes; 37,654 dots'),
        'non_fault_mimic': 'within-stratum lithologic contacts and map-compilation density; erosional escarpments',
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': "PROXY-DTI (B', LOQO out-of-fold) and HOLDOUT-DTI (A); neither organizer-confirmed",
        'preregistration': 'docs/preregistration-s3-e2.md (commit 97cb1d3 before run)',
        'instrument_b_prime_proxy': pick(b), 'paired_b_prime': db,
        'instrument_b_unrestricted': pick(summary_ball['scores']),
        'instrument_a_holdout': pick(a), 'paired_a': summary_a['paired_differences'],
        'loqo_oof_auc': aucs,
        'marginals': marg,
        'gates': dict(b_prime_beats_h33=g1, b_prime_beats_random_stratified=g2, a_ge_h33=g3,
                      steep_fraction_matched=g5, unique=not duplicate,
                      validator=bool(validated and validated.get('all_checks_passed'))),
        'correlation_overlap_vs_registry': dict(
            surface_worst_spearman=surf_rho, final_rasters_checked=audit['registry_rasters_checked'],
            final_worst_mutual_overlap=audit['worst_dot_overlap'],
            final_worst_mutual_submission=audit['worst_overlap_submission'],
            final_worst_forward_overlap=audit['worst_forward_overlap'],
            final_worst_spearman=audit['worst_spearman_full_footprint'],
            sibling_s3_e1_mutual_overlap=e1_overlap, duplicate=duplicate,
            inventory_scope=audit['inventory_scope']),
        'raster_sha256': receipt['sha256'] if receipt else None,
        'validator_output': validated,
        'artifact': f'docs/downloads/{NAME}{suffix}.tif' if receipt else None,
        'submission_name': NAME + suffix, 'submission_note': NOTE, 'note_chars': len(NOTE),
        'download_ok': bool(receipt and validated and validated.get('all_checks_passed') and not duplicate),
        'submit_recommended': promoted, 'download_and_submit_ok': promoted,
        'weekly_slots_used': 0, 'experiment_count_this_session': 2,
        'elapsed_seconds': round(time.monotonic() - start, 1), 'organizer_confirmed_score': None,
        'inputs_sha256': dict(H33=H33_SHA, SGMC=SGMC_SHA, S3_E1=e1_sha, **PINS),
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['src/gems70/supervised.py', 'scripts/run_experiment_s3_e2.py']},
    }
    dump(E / 'run_card.json', card)
    log('DONE', card['verdict'], card['gates'])
    print(json.dumps({k: card[k] for k in ('verdict', 'gates', 'instrument_b_prime_proxy', 'instrument_a_holdout',
                                           'marginals', 'correlation_overlap_vs_registry', 'raster_sha256')},
                     indent=2, default=float))


if __name__ == '__main__':
    main()
