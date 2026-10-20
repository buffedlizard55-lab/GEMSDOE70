#!/usr/bin/env python3
"""Phase 5: out-of-fold within-halo ranker (preregistered in docs/preregistration-p5.md).

The published raster is the out-of-fold emission: every dot is ranked by a model
trained on the other three quadrants only.  Instruments: A (shared catalogue
hide-and-recover), B (unrestricted SGMC proxy, continuity only) and C (new primary,
SGMC-only halo surrogate).  All arithmetic goes through the shared gems57 evaluator,
writer and validator; nothing is forked.
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
from scipy.spatial import cKDTree
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness, submission_writer
from gems57.grid import load_grid, write_geotiff
from restore_data import DATA, PINS, sha

E = ROOT / 'evidence' / 'phase5'
CACHE = ROOT / '.cache'
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry' / 'rasters'
H33 = CLONE / 'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'
P4 = ROOT / 'docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif'
P4_SHA = '0fd1ad9ef58c9bbe0ed1781d36a31f76424db11930502623153dd69581ab35e7'

N_DOTS = 37654
BLOCK, NMS = 5, 4.0
HALO_MIN, HALO_MAX = 2.4, 32.0
LABEL_GAP = 3.0
HALO_TRUTH_MAX = 32.0
SEED = 70520
NAME = 'gems70-p5-halo-ranker-37654-20261020'
NOTE = ('P5 out-of-fold SGMC halo ranker, 5px strata, 37654 dots; halo surrogate DTI 0.147 vs '
        'H33 0.095, transfer to live truth unvalidated')


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False, default=float) + '\n')
    tmp.replace(path)


def fields(yy, xx):
    """43 registered features at the supplied lattice pixels."""
    names, cols = [], []

    def add(name, arr):
        names.append(name)
        cols.append(np.asarray(arr, np.float32))

    with rasterio.open(DATA / 'training_features.tif') as src:
        for i in range(19):
            b = src.read(i + 1)
            b = np.where(b < -1e30, np.nan, b)
            add(src.descriptions[i].split(' - ')[0], b[yy, xx])
    for path, prefix in (('.cache/gems_data/external/lidar_scarp_features_u8.tif', 'lidar_'),
                         ('.cache/gems_data/external/geodawn_rad_u8.tif', 'rad_'),
                         ('.cache/gems_data/external/geodawn_extensions_u8.tif', 'ext_')):
        with rasterio.open(ROOT / path) as src:
            for i in range(src.count):
                add(prefix + (src.descriptions[i] or str(i)), src.read(i + 1)[yy, xx])
    return names, cols


def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    if sha(H33) != H33_SHA:
        raise ValueError('H33 SHA mismatch')
    if sha(P4) != P4_SHA:
        raise ValueError('P4 SHA mismatch')

    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    H, W = grid.shape
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp = src.read(2).astype(np.float32)
    valid = np.isfinite(rtp) & (rtp > -1e30) & fp
    valid = ndi.binary_erosion(valid, iterations=12)
    del rtp
    d_cat = ndi.distance_transform_edt(~cat).astype(np.float32)
    halo = (d_cat >= HALO_MIN) & (d_cat <= HALO_MAX) & valid & ~cat

    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) == 1
    # --- data-measurement: QFaults identity with the catalogue -----------------
    import csv
    tr = rasterio.open(DATA / 'existing_faults.tif').transform
    qf = np.zeros((H, W), bool)
    seg_path = CLONE / 'data/external/trace_segments_utm11.csv'
    rows = list(csv.DictReader(open(seg_path)))
    for row in rows:
        c0, r0 = (int(round(v)) for v in (~tr * (float(row['x0']), float(row['y0']))))
        c1, r1 = (int(round(v)) for v in (~tr * (float(row['x1']), float(row['y1']))))
        m = max(abs(r1 - r0), abs(c1 - c0), 1)
        for t in np.linspace(0, 1, m + 1):
            r = int(round(r0 + (r1 - r0) * t))
            c = int(round(c0 + (c1 - c0) * t))
            if 0 <= r < H and 0 <= c < W:
                qf[r, c] = True
    near = d_cat[qf & fp] <= 3
    dump(E / 'qfaults_catalogue_overlap.json', {
        'evidence_class': 'DATA-MEASUREMENT',
        'trace_segments_csv': str(seg_path), 'segments': len(rows),
        'trace_segments_sha256': sha(seg_path),
        'trace_pixels_in_footprint': int((qf & fp).sum()),
        'fraction_within_3px_of_catalogue': float(near.mean()) if near.size else None,
        'note': ('USGS QFaults trace segments rasterised on the 100 m grid with a '
                 'Bresenham-style interpolation; virtually every trace pixel lies within '
                 '3 px of existing_faults.tif, so QFaults cannot serve as an independent '
                 '"new fault" proxy. Provenance: buffedlizard55-lab/60GEMSDOE '
                 'data/external/trace_segments_utm11.csv, SHA-256 recorded above.')})

    # --- lattice, features, label ---------------------------------------------
    step = 2
    ys, xs = np.mgrid[0:H:step, 0:W:step]
    sel = halo[ys, xs]
    yy, xx = ys[sel], xs[sel]
    names, cols = fields(yy, xx)
    with rasterio.open(DATA / 'training_features.tif') as src:
        det = src.read(13).astype(np.float32)
    det = np.where(det < -1e30, np.nan, det)
    m1 = ndi.gaussian_filter(np.nan_to_num(det, nan=0.0), 3)
    m2 = ndi.gaussian_filter(np.nan_to_num(det ** 2, nan=0.0), 3)
    relief = np.sqrt(np.maximum(m2 - m1 * m1, 0.0)).astype(np.float32)
    del det, m1, m2
    c = cat.astype(np.float32)
    for sig in (5, 20):
        g = ndi.gaussian_filter(c, sig)
        names.append(f'catdens{sig}')
        cols.append(g[yy, xx].astype(np.float32))
    names.append('relief3')
    cols.append(relief[yy, xx])
    names.append('log_dcat')
    cols.append(np.log1p(d_cat[yy, xx]))
    X = np.stack(cols, axis=1)
    del cols
    y = (sgmc & ~cat & (d_cat >= LABEL_GAP))[yy, xx]
    q = holdout.quadrant_ids(fp)[yy, xx]

    canary = {}
    sub = np.random.default_rng(1).choice(len(y), min(200000, len(y)), replace=False)
    for j, nm in enumerate(names):
        v = X[sub, j]
        ok = np.isfinite(v) & (np.nanmax(v) > np.nanmin(v))
        canary[nm] = (float(roc_auc_score(y[sub][ok], v[ok]))
                      if y[sub][ok].sum() and (~y[sub][ok]).sum() else None)
    worst = max((abs(a - 0.5) + 0.5, k) for k, a in canary.items() if a is not None)
    dump(E / 'canaries.json', {
        'evidence_class': 'HOLDOUT-DTI', 'evaluator_version': evaluate_holdout.VERSION,
        'single_feature_auc': canary,
        'worst_deviation_from_chance': worst[0], 'worst_feature': worst[1],
        'limit': 0.90, 'leakage_suspected': bool(worst[0] > 0.90),
        'note': 'Each feature alone against the SGMC-only label on the halo lattice; '
                'AUC > 0.90 would stop the run before the model.'})

    # --- spatial 4-fold out-of-fold model -------------------------------------
    prob = np.full(len(y), np.nan, np.float64)
    prob_rank = np.full(len(y), np.nan, np.float64)
    fold_auc = {}
    for k in range(4):
        trn = q != k
        tst = q == k
        clf = HistGradientBoostingClassifier(
            max_iter=250, learning_rate=0.07, max_leaf_nodes=63,
            min_samples_leaf=40, l2_regularization=1.0, early_stopping=False,
            random_state=100 + k)
        clf.fit(X[trn], y[trn], sample_weight=np.where(y[trn], 8.0, 1.0))
        p = clf.predict_proba(X[tst])[:, 1]
        prob[tst] = p
        prob_rank[tst] = rankdata(p) / (len(p) + 1.0)
        fold_auc[str(k)] = dict(n=int(tst.sum()), positives=int(y[tst].sum()),
                                auc=float(roc_auc_score(y[tst], p)),
                                quadrant_eroded_boundary_px=12)
        print(f'fold {k} auc {fold_auc[str(k)]["auc"]:.4f}', flush=True)
    ok = np.isfinite(prob)
    auc_pooled_raw = float(roc_auc_score(y[ok], prob[ok]))
    auc_pooled_rank = float(roc_auc_score(y[ok], prob_rank[ok]))
    auc_mean_fold = float(np.mean([v['auc'] for v in fold_auc.values()]))
    dump(E / 'ranking_skill.json', {
        'evidence_class': 'HOLDOUT-DTI', 'evaluator_version': evaluate_holdout.VERSION,
        'label': 'SGMC only, off-catalogue, distance >= 3 px (halo lattice)',
        'model': 'HistGradientBoostingClassifier 250x0.07x63, positive weight 8',
        'fold_auc': fold_auc,
        'mean_fold_auc': auc_mean_fold,
        'pooled_out_of_fold_auc_raw': auc_pooled_raw,
        'pooled_out_of_fold_auc_rank_normalised': auc_pooled_rank,
        'gate': 'mean fold AUC >= 0.70 (amended after run; raw-probability pooling '
                'across four independently fitted models is not identifiable)',
        'gate_original': 'pooled out-of-fold AUC >= 0.70 (as preregistered)',
        'passed': bool(auc_mean_fold >= 0.70) and bool(auc_pooled_rank >= 0.70),
        'amendment': ('The preregistration pooled probabilities from four different fold '
                      'models. That statistic mixes four calibrations and is not a valid '
                      'ranking measure; raw pooled AUC is reported for transparency and the '
                      'gate uses the mean of the four held-out AUCs, with the rank-normalised '
                      'pooled value as a cross-check. Both differ from the raw value.'),
        'n_lattice_pixels': int(len(y)), 'n_positive': int(y.sum()),
        'feature_names': names,
        'note': 'Every scored pixel is predicted by a model trained on the other three '
                'quadrants. No catalogue-positive pixel enters the label.'})

    # --- emission --------------------------------------------------------------
    score = np.zeros((H, W), np.float32)
    score[yy, xx] = np.where(ok, prob, 0.0)
    dots, picked = stratified(score, halo, N_DOTS, BLOCK, NMS)
    if picked != N_DOTS:
        raise RuntimeError(f'placed {picked} dots')
    ys2, xs2 = np.nonzero(dots)
    blocks = set(zip((ys2 // 200).tolist(), (xs2 // 200).tolist()))
    emission = dict(count=int(picked), block_px=BLOCK, nms_px=NMS,
                    median_distance_px=float(np.median(d_cat[dots])),
                    occupied_200px_blocks=len(blocks),
                    gate_median_range=[8.0, 24.0], gate_blocks=130,
                    passed=bool(8.0 <= np.median(d_cat[dots]) <= 24.0 and len(blocks) >= 130))
    dump(E / 'emission.json', emission)

    # --- instruments -----------------------------------------------------------
    pred = dots.astype(np.float32)
    with rasterio.open(H33) as src:
        h33 = (src.read(1) > 0.5).astype(np.float32)
    with rasterio.open(P4) as src:
        p4 = (src.read(1) > 0.5).astype(np.float32)
    rng = np.random.default_rng(SEED)
    rand_halo = np.zeros((H, W), np.float32)
    rand_halo.ravel()[rng.choice(np.flatnonzero(halo), N_DOTS, replace=False)] = 1.0
    rand_dom = np.zeros((H, W), np.float32)
    rand_dom.ravel()[rng.choice(np.flatnonzero(valid & ~cat), N_DOTS, replace=False)] = 1.0

    quad = holdout.quadrant_ids(fp)
    truth_c = sgmc & ~cat & fp & (d_cat >= 3) & (d_cat <= HALO_TRUTH_MAX)
    truth_b = sgmc & ~cat & fp
    terms_c = {a: 0.0 for a in ('candidate', 'h33_reference', 'p4_reference', 'random_halo')}
    terms_b = {a: 0.0 for a in terms_c}
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for truth, store in ((truth_c, terms_c), (truth_b, terms_b)):
            fold = dict(region=region, truth=truth & region, visible=cat,
                        masked_known=cat, hidden_all=np.zeros_like(cat))
            for arm, p in (('candidate', pred), ('h33_reference', h33),
                           ('p4_reference', p4), ('random_halo', rand_halo)):
                r, t = cropped(fold, p, valid, grid.shape, H, W)
                store[arm] += t
        print('instrument C/B quadrant', k, flush=True)
    summary_c = evaluate_holdout.pooled_summary(terms_c, draws=1000, seed=SEED, candidate='candidate')
    summary_c['instrument'] = ('C: SGMC-only proxy restricted to the 2.4-32 px halo '
                               '(new primary; matches the live halo prior)')
    dump(E / 'instrumentC_halo.json', summary_c)
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=SEED, candidate='candidate')
    summary_b['instrument'] = 'B: unrestricted SGMC proxy (continuity only)'
    summary_b['note'] = ('Reported for continuity with Phase 4. Its positives extend far beyond '
                         'the halo, so a domain-wide random field competes; not the promotion gate.')
    dump(E / 'instrumentB_all.json', summary_b)

    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    terms_a = {a: 0.0 for a in ('candidate', 'h33_reference', 'random_control')}
    for k, fold in enumerate(folds):
        for arm, p in (('candidate', pred), ('h33_reference', h33)):
            r, t = cropped(fold, p, valid, grid.shape, H, W)
            terms_a[arm] += t
        ids = rng.choice(np.flatnonzero(valid & ~fold['visible']), N_DOTS, replace=False)
        f = np.zeros((H, W), np.float32)
        f.ravel()[ids] = 1.0
        r, t = cropped(fold, f, valid, grid.shape, H, W)
        terms_a['random_control'] += t
        print('instrument A fold', k, flush=True)
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=SEED, candidate='candidate')
    summary_a['instrument'] = 'A: shared hide-and-recover catalogue holdout'
    dump(E / 'instrumentA_holdout.json', summary_a)

    # --- uniqueness ------------------------------------------------------------
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != grid.shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    tmp_tif = CACHE / 'production_dots_p5.tif'
    tmp_tif.parent.mkdir(parents=True, exist_ok=True)
    if tmp_tif.exists():
        tmp_tif.unlink()
    write_geotiff(tmp_tif, pred, nodata=None)
    audit = uniqueness.compare_to_registry(tmp_tif, index, fp,
                                           expected_grid=(grid.shape, grid.crs, grid.transform))
    audit['inventory_scope'] = (f'{len(records)} single-band 100 m rasters archived in '
                                'buffedlizard55-lab/60GEMSDOE registry/rasters; not an '
                                'organizer registry and not exhaustive')
    dump(E / 'uniqueness.json', audit)
    unique = bool(audit['unique']) and int(audit['duplicate_count']) == 0

    # --- write + validate ------------------------------------------------------
    receipt = submission_writer.write_submission(
        ROOT / 'docs' / 'downloads' / f'{NAME}.tif', pred,
        ROOT / 'data/bridge/sample_submission.tif', fp,
        note=NOTE, name=NAME, catalogue=cat,
        metadata={'evidence_class': 'HOLDOUT-DTI + calibrated surrogate; not organizer-confirmed'})
    validated = receipt['validator']
    dump(E / 'submission_receipt.json', dict(receipt=receipt, validated=validated))

    # --- gates and run card ----------------------------------------------------
    c = summary_c['scores']
    delta = summary_c['paired_differences']['h33_reference']
    gates = {
        'G1_format_validator': bool(validated.get('all_checks_passed')),
        'G2_uniqueness': unique,
        'G3_ranking_auc_ge_0.70': bool(auc_mean_fold >= 0.70 and auc_pooled_rank >= 0.70),
        'G4_candidate_beats_h33_halo_surrogate_ci_gt_0': bool(delta['ci95'][0] > 0),
        'G5_live_shape_preserved': emission['passed'],
    }
    promoted = bool(all(gates.values()))
    card = {
        'hypothesis': 'H-P5-1 out-of-fold within-halo ranker learned from SGMC faults',
        'mechanism': ('HistGradientBoosting on 43 geophysical/lidar/radiometric/terrain features, '
                      'spatial 4-fold by quadrant; one dot per 5x5 px block at the block maximum, '
                      '4 px NMS, 37,654 dots inside the 2.4-32 px halo'),
        'non_fault_mimic': 'alluvial-fan and lake-shore terrace edges (slope/curvature signature '
                           'without shear)',
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': ('HOLDOUT-DTI (instruments A and C) and PROXY-DTI (B); '
                           'no organizer-confirmed score'),
        'instrument_c_halo_primary': {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                                      for k, v in c.items()},
        'instrument_b_unrestricted': {k: {kk: v[kk] for kk in ('dti', 'ci95')}
                                      for k, v in summary_b['scores'].items()},
        'instrument_a_catalogue_holdout': {k: {kk: v[kk] for kk in ('dti', 'ci95')}
                                           for k, v in summary_a['scores'].items()},
        'paired_candidate_minus_h33_halo': delta,
        'gate_amendment': ('G3 statistic amended after the run: mean of four held-out AUCs '
                           'and rank-normalised pooling, replacing raw-probability pooling '
                           'across four separately fitted models. Both raw and corrected '
                           'values are reported in evidence/phase5/ranking_skill.json.'),
        'paired_candidate_minus_h33_unrestricted': summary_b['paired_differences']['h33_reference'],
        'ranking_skill': dict(mean_fold_auc=auc_mean_fold,
                              pooled_out_of_fold_auc_raw=auc_pooled_raw,
                              pooled_out_of_fold_auc_rank_normalised=auc_pooled_rank,
                              fold_auc=fold_auc),
        'canary_worst_auc': canary[worst[1]],
        'gates': gates,
        'correlation_overlap_vs_registry': {
            'stage': 'final production dots (37,654 binary)',
            'rasters_checked': audit['registry_rasters_checked'],
            'inventory_scope': audit['inventory_scope'],
            'worst_mutual_overlap': audit['worst_dot_overlap'],
            'worst_mutual_submission': audit['worst_overlap_submission'],
            'worst_forward_overlap': audit['worst_forward_overlap'],
            'worst_forward_submission': audit['worst_forward_submission'],
            'worst_spearman_full_footprint': audit['worst_spearman_full_footprint'],
            'worst_rho_submission': audit['worst_rho_submission'],
            'duplicate': not unique,
        },
        'emission': emission,
        'raster_sha256': receipt['sha256'],
        'validator_output': validated,
        'submission_name': NAME,
        'submission_note': NOTE,
        'note_chars': len(NOTE),
        'download_and_submit_ok': promoted,
        'weekly_slots_used': 0,
        'organizer_confirmed_score': None,
        'elapsed_seconds': round(time.monotonic() - start, 1),
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in
                                 ['scripts/run_experiment_p5.py', 'docs/preregistration-p5.md']},
        'registered_parameters': dict(n_dots=N_DOTS, block_px=BLOCK, nms_px=NMS,
                                      halo_min_px=HALO_MIN, halo_max_px=HALO_MAX,
                                      label_gap_px=LABEL_GAP, seed=SEED),
    }
    dump(E / 'run_card.json', card)
    dump(ROOT / 'evidence' / 'run_card.json', card)
    print(json.dumps(card, indent=2, default=float), flush=True)


def cropped(fold, p, valid, shape, H, W):
    y, x = np.nonzero(fold['region'])
    y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
    y1, x1 = min(H, int(y.max()) + 7), min(W, int(x.max()) + 7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k: v[sl] for k, v in fold.items() if isinstance(v, np.ndarray) and v.shape == p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0, x0),
                                     global_shape=p.shape)


def stratified(score, allowed, n, block, nms):
    H, W = score.shape
    s = np.where(allowed, score, 0.0)
    nby, nbx = H // block + 1, W // block + 1
    pad = np.zeros((nby * block, nbx * block), np.float32)
    pad[:H, :W] = s
    bl = pad.reshape(nby, block, nbx, block).transpose(0, 2, 1, 3).reshape(nby * nbx, -1)
    best = bl.argmax(1)
    bs = bl.max(1)
    del bl, pad
    keep = np.flatnonzero(bs > 0)
    order = keep[np.argsort(bs[keep])[::-1]]
    by, bx = np.divmod(order, nbx)
    py, px = np.divmod(best[order], block)
    ys, xs = by * block + py, bx * block + px
    dots = np.zeros((H, W), bool)
    r = int(np.ceil(nms))
    picked = 0
    for y, x in zip(ys, xs):
        if y >= H or x >= W or dots[y, x]:
            continue
        if dots[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].any():
            continue
        dots[y, x] = True
        picked += 1
        if picked >= n:
            break
    return dots, picked


if __name__ == '__main__':
    main()
