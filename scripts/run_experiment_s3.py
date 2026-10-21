#!/usr/bin/env python3
"""S3 experiment 1 of <=3: supervised proxy-trained ranking, H33-matched spacing.

Preregistered in docs/preregistration-s3.md (committed before this run). Reuses the shared
vendor/gems57 evaluator, holdout draw, uniqueness audit, writer and validator unchanged.
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
from gems70 import supervised as sv
from restore_data import DATA, PINS, sha
from run_experiment_v4 import stratified_dots, cropped

E = ROOT / 'evidence' / 's3'
CACHE = ROOT / '.cache'
CLONE = Path('/tmp/60GEMSDOE')
AUX = CLONE / 'data/external'
REG = CLONE / 'registry' / 'rasters'
H33 = CLONE / 'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = AUX / 'sgmc_faults_100m.tif'
SGMC_SHA = '26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c'
P4 = ROOT / 'docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif'
P4_SHA = '0fd1ad9ef58c9bbe0ed1781d36a31f76424db11930502623153dd69581ab35e7'
SEED = 70420
GAP_PX = 3.0
NAME = 'gems70-s3-proxyrank-h33spacing-37654-20261020'
NOTE = 'S3 LOQO GBM trained on SGMC off-catalogue proxy, 66 physics+geometry feats; 37654 dots, H33 2.83px spacing'


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False, default=float) + '\n')
    tmp.replace(path)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def binary(path, fp):
    with rasterio.open(path) as src:
        a = src.read(1).astype(np.float32)
    return np.where(np.isfinite(a) & (a > 0.5) & fp, 1.0, 0.0).astype(np.float32)


def predict(model, X_phys, X_geo, rows, chunk=400_000):
    out = np.empty(rows.size, np.float32)
    for s in range(0, rows.size, chunk):
        r = rows[s:s + chunk]
        parts = [p[r].astype(np.float32) for p in (X_phys, X_geo) if p is not None]
        out[s:s + chunk] = model.predict_proba(np.hstack(parts))[:, 1]
    return out


def fit(X_phys, X_geo, rows, y, rng):
    pos = rows[y[rows]]
    neg = rows[~y[rows]]
    neg = rng.choice(neg, min(neg.size, sv.NEG_RATIO * pos.size), replace=False)
    tr = np.concatenate([pos, neg])
    parts = [p[tr].astype(np.float32) for p in (X_phys, X_geo) if p is not None]
    model = HistGradientBoostingClassifier(**sv.HGB_PARAMS)
    model.fit(np.hstack(parts), y[tr])
    return model, int(pos.size), int(neg.size)


def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    for p, pin in ((H33, H33_SHA), (SGMC, SGMC_SHA), (P4, P4_SHA)):
        if sha(p) != pin:
            raise ValueError(f'pin mismatch: {p}')
    aux_sha = {f: sha(AUX / f) for f in sv.AUX_FILES}
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
    log('valid pixels', vidx.size)

    X_phys, phys_names = sv.physics_matrix(DATA / 'training_features.tif', AUX, valid)
    gc.collect()
    log('physics matrix', X_phys.shape, X_phys.nbytes / 1e6, 'MB')
    X_geo, geo_names, d_cat = sv.geometry_matrix(cat, valid)
    log('geometry matrix', X_geo.shape)

    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_cat >= GAP_PX)
    del sgmc
    domain = valid & ~cat & (d_cat >= sv.D_MIN)
    dom_rows = pos_of[np.flatnonzero(domain)]          # rows into the valid matrices
    y = proxy_prime.ravel()[vidx]                       # label per valid row
    quad = holdout.quadrant_ids(fp)
    quad_rows = quad.ravel()[vidx]
    region_rows = {}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        region_rows[k] = region.ravel()[vidx]
    in_domain = np.zeros(vidx.size, bool)
    in_domain[dom_rows] = True

    # ---------------- leakage canary (feature alone, B' label, fixed 1M sample) -------------
    rng = np.random.default_rng(SEED)
    samp = rng.choice(dom_rows, min(1_000_000, dom_rows.size), replace=False)
    canaries = {}
    for j, nm in enumerate(phys_names + geo_names):
        col = (X_phys[samp, j] if j < len(phys_names) else X_geo[samp, j - len(phys_names)]).astype(np.float32)
        ok = np.isfinite(col)
        fill = float(np.median(col[ok])) if ok.any() else 0.0
        col = np.where(ok, col, fill)
        auc = float(roc_auc_score(y[samp], col))
        canaries[nm] = dict(auc=auc, strength=max(auc, 1 - auc), missing_fraction=float(1 - ok.mean()),
                            suspected_leakage=bool(max(auc, 1 - auc) > 0.90))
    alarm = [k for k, v in canaries.items() if v['suspected_leakage']]
    dump(E / 'canaries.json', dict(evidence_class='LEAKAGE-CANARY', label="B' proxy",
                                   sample=int(samp.size), threshold=0.90, alarms=alarm,
                                   features=canaries))
    log('canaries done; alarms', alarm, 'max strength',
        max(v['strength'] for v in canaries.values()))
    if alarm:
        raise SystemExit('leakage canary alarm; stopping per preregistration')

    # ---------------- LOQO out-of-fold scores for candidate and model ablations -------------
    variants = {'candidate': (X_phys, X_geo), 'abl_physics_only': (X_phys, None),
                'abl_geometry_only': (None, X_geo)}
    oof = {v: np.zeros(vidx.size, np.float32) for v in variants}
    fold_info = []
    for k in range(4):
        train_rows = np.flatnonzero(in_domain & (quad_rows != k) &
                                    np.any([region_rows[j] for j in range(4) if j != k], axis=0))
        test_rows = np.flatnonzero(in_domain & (quad_rows == k))
        info = dict(fold=k, train_rows=int(train_rows.size), test_rows=int(test_rows.size))
        for v, (P, G) in variants.items():
            model, npos, nneg = fit(P, G, train_rows, y, np.random.default_rng(SEED + k))
            s = predict(model, P, G, test_rows)
            r = sv.rank_within(s, np.zeros(s.size, np.int8), np.ones(s.size, bool))
            oof[v][test_rows] = r
            t = region_rows[k][test_rows]
            info[v] = dict(n_pos=npos, n_neg=nneg, n_iter=int(model.n_iter_),
                           oof_auc_region=float(roc_auc_score(y[test_rows][t], s[t])))
            del model, s
            gc.collect()
        fold_info.append(info)
        log('LOQO fold', k, {v: round(info[v]['oof_auc_region'], 4) for v in variants})
    dump(E / 'loqo_folds.json', dict(evidence_class='OOF-AUC (B\' proxy, LOQO)', folds=fold_info))

    def to_map(row_values):
        m = np.zeros(shape, np.float32)
        m.ravel()[vidx] = row_values
        return np.where(domain, m, 0.0).astype(np.float32)

    allowed = domain
    arms = {}
    for v in variants:
        arms[v] = sv.place(to_map(oof[v]), allowed).astype(np.float32)
    arms['abl_stratified7_placement'], picked = stratified_dots(to_map(oof['candidate']))
    if picked != sv.DOT_COUNT:
        raise RuntimeError('stratified placement count')
    arms['abl_stratified7_placement'] = arms['abl_stratified7_placement'].astype(np.float32)
    ids = rng.choice(np.flatnonzero(domain), sv.DOT_COUNT, replace=False)
    rnd = np.zeros(shape, np.float32)
    rnd.ravel()[ids] = 1.0
    arms['random_control'] = rnd
    arms['h33_reference'] = binary(H33, fp)
    arms['p4_published'] = binary(P4, fp)
    log('arms placed', {k: int(v.sum()) for k, v in arms.items()})

    terms_b = {a: 0.0 for a in arms}
    terms_ball = {a: 0.0 for a in arms}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for mask, store in ((proxy_prime, terms_b), (proxy, terms_ball)):
            fold = dict(region=region, truth=mask & region & ~cat, visible=cat,
                        masked_known=cat, hidden_all=np.zeros_like(cat))
            for arm, p in arms.items():
                _, t = cropped(fold, p, valid)
                store[arm] += t
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=SEED, candidate='candidate')
    summary_b['instrument'] = "B': SGMC proxy truth restricted to d_cat >= 3 px; LOQO out-of-fold scores"
    summary_b['proxy_positive_pixels_prime'] = int(proxy_prime.sum())
    dump(E / 'instrumentB_prime.json', summary_b)
    summary_ball = evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=SEED, candidate='candidate')
    summary_ball['instrument'] = 'B: unrestricted SGMC proxy (contains duplication band); not gated'
    dump(E / 'instrumentB_all.json', summary_ball)
    log('B prime', {k: round(v['dti'], 4) for k, v in summary_b['scores'].items()})
    del arms
    gc.collect()

    # ---------------- production model: all quadrants, per-quadrant rank ---------------------
    train_rows = np.flatnonzero(in_domain & np.any([region_rows[j] for j in range(4)], axis=0))
    prod_model, npos, nneg = fit(X_phys, X_geo, train_rows, y, np.random.default_rng(SEED + 99))
    s = predict(prod_model, X_phys, X_geo, dom_rows)
    prod_rank_rows = np.zeros(vidx.size, np.float32)
    prod_rank_rows[dom_rows] = sv.rank_within(s, quad_rows[dom_rows], np.ones(s.size, bool))
    surface = to_map(prod_rank_rows)
    del s
    prod = sv.place(surface, allowed).astype(np.float32)
    log('production dots', int(prod.sum()))

    # ---------------- instrument A (diagnostic): visible-catalogue geometry per fold ---------
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    terms_a = {a: 0.0 for a in ('candidate', 'random_control', 'h33_reference')}
    h33 = binary(H33, fp)
    for k, fold in enumerate(folds):
        vis = fold['visible']
        Xg, _, dv = sv.geometry_matrix(vis, valid)
        dom_a = valid & ~vis & (dv >= sv.D_MIN)
        rows_a = pos_of[np.flatnonzero(dom_a)]
        s = predict(prod_model, X_phys, Xg, rows_a)
        rr = np.zeros(vidx.size, np.float32)
        rr[rows_a] = sv.rank_within(s, quad_rows[rows_a], np.ones(s.size, bool))
        m = np.zeros(shape, np.float32)
        m.ravel()[vidx] = rr
        m = np.where(dom_a, m, 0.0).astype(np.float32)
        cand = sv.place(m, dom_a).astype(np.float32)
        ids = rng.choice(np.flatnonzero(dom_a), sv.DOT_COUNT, replace=False)
        rnd = np.zeros(shape, np.float32)
        rnd.ravel()[ids] = 1.0
        for arm, p in (('candidate', cand), ('random_control', rnd), ('h33_reference', h33)):
            _, t = cropped(fold, p, valid)
            terms_a[arm] += t
        del Xg, dv, s, rr, m, cand, rnd
        gc.collect()
        log('A fold', k, 'done')
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=SEED, candidate='candidate')
    summary_a['instrument'] = 'A: shared hide-and-recover catalogue holdout (diagnostic)'
    dump(E / 'instrumentA_holdout.json', summary_a)
    del X_phys, X_geo
    gc.collect()

    # ---------------- uniqueness: surface before placement, then final dots ------------------
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    eg = (grid.shape, grid.crs, grid.transform)
    surf_audit = uniqueness.compare_array_to_registry(np.where(fp, surface, 0).astype(np.float32),
                                                      index, fp, expected_grid=eg,
                                                      include_reverse=False)
    surf_rho = surf_audit['worst_spearman_full_footprint']
    dump(E / 'surface_uniqueness.json', dict(
        stage='production rank surface before placement', rasters_checked=surf_audit['registry_rasters_checked'],
        worst_spearman_full_footprint=surf_rho, worst_rho_submission=surf_audit['worst_rho_submission'],
        rho_limit=0.90, duplicate_by_rho=bool(surf_rho is not None and surf_rho > 0.90)))
    log('surface worst rho', surf_rho)
    tmp_tif = CACHE / 'production_dots_s3.tif'
    tmp_tif.parent.mkdir(parents=True, exist_ok=True)
    if tmp_tif.exists():
        tmp_tif.unlink()
    write_geotiff(tmp_tif, prod, nodata=None)
    audit = uniqueness.compare_to_registry(tmp_tif, index, fp, expected_grid=eg)
    audit['inventory_scope'] = (f'{len(records)} single-band 100 m rasters archived in '
                                'buffedlizard55-lab/60GEMSDOE registry/rasters; not exhaustive')
    dump(E / 'uniqueness.json', audit)
    duplicate = bool(audit['unique'] is False or audit['duplicate_count'] > 0
                     or (surf_rho is not None and surf_rho > 0.90))
    log('final uniqueness: worst mutual', audit['worst_dot_overlap'], 'rho',
        audit['worst_spearman_full_footprint'], 'duplicate', duplicate)

    b, a = summary_b['scores'], summary_a['scores']
    db = summary_b['paired_differences']
    gate_canary = not alarm
    gate_b = bool(db['h33_reference']['delta'] > 0 and db['h33_reference']['ci95'][0] > 0)
    gate_a = bool(a['candidate']['dti'] >= a['h33_reference']['dti'])
    promote_pre_write = bool(gate_canary and gate_b and gate_a and not duplicate)
    suffix = '' if promote_pre_write else '-DO-NOT-SUBMIT'
    receipt = None
    if not duplicate:
        from gems57 import submission_writer
        receipt = submission_writer.write_submission(
            ROOT / 'docs' / 'downloads' / f'{NAME}{suffix}.tif', prod,
            ROOT / 'data/bridge/sample_submission.tif', fp, note=NOTE, name=NAME + suffix,
            catalogue=cat,
            metadata={'evidence_class': "PROXY-DTI (B') + HOLDOUT-DTI (A); not organizer-confirmed"})
    validated = receipt['validator'] if receipt else None
    promoted = bool(promote_pre_write and validated and validated.get('all_checks_passed'))

    def pick(s):
        return {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')} for k, v in s.items()}

    card = {
        'hypothesis': 'S3: physics layers rank unmapped-fault likelihood inside the region H33 samples uniformly',
        'mechanism': ('LOQO HistGradientBoosting on 66 features (19-band stack, 6 gradients, det_elev std, '
                      '33 LiDAR/topo/chi/radiometric bands, 7 catalogue-geometry); label = SGMC-only faults '
                      '>=3 px off catalogue; per-quadrant rank; greedy NMS r=2.5 px (H33 min spacing); 37,654 dots'),
        'non_fault_mimic': 'lithologic contacts / map-compilation density bias (bedrock ranges mapped in more detail); erosional escarpments',
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': "PROXY-DTI (B', LOQO out-of-fold) and HOLDOUT-DTI (A); neither organizer-confirmed",
        'preregistration': 'docs/preregistration-s3.md (commit c8cabe0 before run)',
        'instrument_b_prime_proxy': pick(b),
        'paired_b_prime': db,
        'instrument_b_unrestricted': pick(summary_ball['scores']),
        'instrument_a_holdout': pick(a),
        'paired_a': summary_a['paired_differences'],
        'loqo_oof_auc': {v: [f[v]['oof_auc_region'] for f in fold_info] for v in variants},
        'gates': dict(canary_no_alarm=gate_canary, b_prime_beats_h33_ci_above_0=gate_b,
                      a_candidate_ge_h33=gate_a, unique=not duplicate,
                      validator=bool(validated and validated.get('all_checks_passed'))),
        'canary_max_strength': max(v['strength'] for v in canaries.values()),
        'canary_max_feature': max(canaries, key=lambda k: canaries[k]['strength']),
        'correlation_overlap_vs_registry': {
            'surface_worst_spearman': surf_rho,
            'final_rasters_checked': audit['registry_rasters_checked'],
            'final_worst_mutual_overlap': audit['worst_dot_overlap'],
            'final_worst_mutual_submission': audit['worst_overlap_submission'],
            'final_worst_forward_overlap': audit['worst_forward_overlap'],
            'final_worst_spearman': audit['worst_spearman_full_footprint'],
            'final_worst_jaccard': audit['worst_jaccard_dot_sets'],
            'duplicate': duplicate,
            'inventory_scope': audit['inventory_scope'],
        },
        'raster_sha256': receipt['sha256'] if receipt else None,
        'validator_output': validated,
        'artifact': f'docs/downloads/{NAME}{suffix}.tif' if receipt else None,
        'submission_name': NAME + suffix,
        'submission_note': NOTE,
        'note_chars': len(NOTE),
        'download_ok': bool(receipt and validated and validated.get('all_checks_passed') and not duplicate),
        'submit_recommended': promoted,
        'download_and_submit_ok': promoted,
        'weekly_slots_used': 0,
        'experiment_count_this_session': 1,
        'elapsed_seconds': round(time.monotonic() - start, 1),
        'organizer_confirmed_score': None,
        'inputs_sha256': dict(H33=H33_SHA, SGMC=SGMC_SHA, P4=P4_SHA, aux=aux_sha, **PINS),
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['src/gems70/supervised.py', 'scripts/run_experiment_s3.py']},
        'registered_parameters': dict(dot_count=sv.DOT_COUNT, nms_radius_px=sv.NMS_RADIUS,
                                      d_min_px=sv.D_MIN, neg_ratio=sv.NEG_RATIO, hgb=sv.HGB_PARAMS,
                                      b_prime_gap_px=GAP_PX, seed=SEED,
                                      n_features=len(phys_names) + len(geo_names)),
        'feature_names': phys_names + geo_names,
    }
    dump(E / 'run_card.json', card)
    log('DONE verdict', card['verdict'], 'download_ok', card['download_ok'])
    print(json.dumps({k: card[k] for k in ('verdict', 'gates', 'instrument_b_prime_proxy',
                                           'instrument_a_holdout', 'loqo_oof_auc',
                                           'correlation_overlap_vs_registry', 'raster_sha256')},
                     indent=2, default=float))


if __name__ == '__main__':
    main()
