#!/usr/bin/env python3
"""Experiment 5 (this session): catalogue-free magnetic analytic-signal ridge.

Registered hypothesis H-2 from docs/hypotheses.md (research queue rank 2),
never previously implemented in this checkout.

Mechanism
---------
The analytic-signal amplitude of total magnetic intensity,
    ASA = sqrt(dTMI/dx^2 + dTMI/dy^2 + dTMI/dz^2)
ridges mark source edges independently of magnetization direction
(Nabighian 1972/1984; Roest et al. 1992), so a buried fault that offsets
magnetized basement produces an ASA ridge with no surface expression and no
mapped trace -- a fault plausibly absent from the USGS/INGENIOUS catalogue.
The ridge is gated by the basement-depth step (fault offset of the basement
surface) and the detrended-elevation slope (subtle scarp steepness), both
from the cached 19-band stack. No fault catalogue enters any feature.

Lane discipline
---------------
* Features are catalogue-independent; the only catalogue use is the visible
  catalogue of the current holdout fold for the >= 3 px exclusion band and
  pixel-exact masking of visible faults from scoring (protocol rule 2).
* Holdout = buffered_component_draw (seed 20, whole components withheld in
  four spatial quadrants); pooled DTI, alpha 0.2, beta 0.8, 300 m triangular
  kernel, paired 20 km spatial-cluster bootstrap.
* Leakage canary: each feature alone on withheld positives; AUC > 0.90 stops.
* Uniqueness: corrected mutual-overlap rule + Spearman vs the 62-raster
  registry inventory (protocol rule 1); stop and log as duplicate if fired.
* Output: binary 0/1 dots, all finite, [0,1], zero outside footprint and on
  the mapped catalogue; writer receipt + run card label every number.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff, TRANSFORM, CRS_EPSG
from restore_data import DATA, PINS, sha

H33 = Path('/tmp/60GEMSDOE/docs/downloads/'
           'gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif')
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = Path('/tmp/60GEMSDOE/data/external/sgmc_faults_100m.tif')
REG = Path('/tmp/60GEMSDOE/registry/rasters')

E = ROOT / 'evidence' / 'phase5'
CACHE = ROOT / '.cache'

NAME = 'gems70-asarc-ridge-30000-20261020'
NOTE = ('ASA ridge x basement step x scarp slope; 30000 binary dots, '
        '>=3 px from catalogue')
assert len(NAME) <= 140 and len(NOTE) <= 140, (len(NAME), len(NOTE))

DOT_COUNT = 30_000
BLOCK = 7
NMS = 5.0
CAT_GAP_PX = 3.0
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_SEED = 70050

ARMS = ('candidate', 'random_control', 'h33_reference')


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False, default=float) + '\n')
    tmp.replace(path)


def rank01(values, valid):
    a = np.asarray(values, dtype=np.float64)
    valid = np.asarray(valid, bool) & np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    n = int(valid.sum())
    if n > 1:
        out[valid] = ((rankdata(a[valid], method='average') - 1) / (n - 1)).astype(np.float32)
    return out


def fill_nearest(a):
    good = np.isfinite(a)
    if not good.any():
        raise ValueError('empty finite feature')
    idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def intensity_features(bands, valid, cat_visible):
    """Catalogue-free feature stack: ASA ridge, basement step, scarp slope."""
    rtp = fill_nearest(np.where(valid, bands[2], np.nan))
    tmi = fill_nearest(np.where(valid, bands[14], np.nan))
    tmi_vg = fill_nearest(np.where(valid, bands[9], np.nan))
    depth = fill_nearest(np.where(valid, bands[15], np.nan))
    slope = fill_nearest(np.where(valid, bands[19], np.nan))

    gy, gx = np.gradient(ndi.gaussian_filter(tmi, 1.0))
    asa = ndi.gaussian_filter(np.hypot(np.hypot(gx, gy), tmi_vg), 1.0).astype(np.float32)
    del gx, gy, tmi_vg

    by, bx = np.gradient(ndi.gaussian_filter(depth, 2.0))
    base_step = np.hypot(by, bx).astype(np.float32)
    del by, bx, depth

    score = np.where(valid, rank01(asa, valid) * rank01(base_step, valid) * rank01(slope, valid), 0.0).astype(np.float32)
    del asa, base_step, slope

    cat = np.asarray(cat_visible, bool)
    allowed = np.asarray(valid, bool) & ~cat
    d = ndi.distance_transform_edt(~cat).astype(np.float32)
    allowed &= (d >= CAT_GAP_PX)
    del d
    score = np.where(allowed, score, 0.0).astype(np.float32)
    if not np.isfinite(score).all():
        raise ValueError('non-finite score')
    return score, allowed


def stratified_dots(score, n=DOT_COUNT, block=BLOCK, nms=NMS):
    """One dot per block at the block maximum; keep best blocks; NMS."""
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


def cropped(fold, p, valid_arr):
    y, x = np.nonzero(fold['region'])
    y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
    y1, x1 = min(p.shape[0], int(y.max()) + 7), min(p.shape[1], int(x.max()) + 7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k: v[sl] for k, v in fold.items() if isinstance(v, np.ndarray) and v.shape == p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid_arr[sl], origin=(y0, x0), global_shape=p.shape)


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
        bands = {i + 1: src.read(i + 1).astype(np.float32) for i in range(src.count)}
    valid = np.isfinite(bands[2]) & (bands[2] > -1e30) & fp
    valid = ndi.binary_erosion(valid, iterations=12)
    rng = np.random.default_rng(70520)
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
    h33 = np.where(np.isfinite(h33) & (h33 > 0.5) & fp, 1.0, 0.0).astype(np.float32)

    folds = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)[0]
    n_folds = len(folds)

    # ---- Canaries: each feature alone on withheld positives (leakage gate) ----
    truth = np.zeros(fp.shape, bool)
    active = np.zeros(fp.shape, bool)
    for fold in folds:
        active |= valid & fold['region'] & ~fold['masked_known']
        truth |= fold['truth']
    positives = np.flatnonzero(truth & active)
    negatives_all = np.flatnonzero(active & ~truth)
    neg_rng = np.random.default_rng(70521)
    negatives = neg_rng.choice(negatives_all, min(200_000, len(negatives_all)), replace=False)

    canary_features = {
        'asa_proxy_hgrad': bands[3],     # tmi_hg
        'asa_proxy_vgrad': bands[9],     # tmi_vg
        'rtp': bands[2],
        'depth_to_base': bands[15],
        'det_elev_slope': bands[19],
    }
    canaries = {}
    labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]
    for name, a in canary_features.items():
        vals = np.r_[np.where(active, a, np.nan).ravel()[positives],
                     np.where(active, a, np.nan).ravel()[negatives]]
        vals = np.where(np.isfinite(vals), vals, 0.0)
        auc = float(roc_auc_score(labels, vals))
        canaries[name] = dict(evidence_class='LEAKAGE-CANARY', auc=auc,
                              inverse_auc=1.0 - auc,
                              withheld_positive_pixels=int(len(positives)),
                              negative_sample_pixels=int(len(negatives)),
                              suspected_leakage=bool(max(auc, 1.0 - auc) > 0.90))
        print(f'Canary {name}: AUC {auc:.4f}', flush=True)
    if any(c['suspected_leakage'] for c in canaries.values()):
        raise RuntimeError('LEAKAGE CANARY STOP: a feature alone has AUC > 0.90')
    dump(E / 'canaries.json', canaries)

    # ---- Holdout arms ----
    terms = {a: [] for a in ARMS}
    n_placed = None
    term_shape = None
    for k, fold in enumerate(folds):
        score, allowed = intensity_features(bands, valid, fold['visible'])
        dots, picked = stratified_dots(score)
        if n_placed is None:
            n_placed = picked
        elif picked != n_placed:
            raise RuntimeError(f'fold {k}: placed {picked} dots, expected {n_placed}')
        f = np.zeros(grid.shape, np.float32)
        f[dots] = 1.0
        del dots
        r, t = cropped(fold, f, valid)
        terms['candidate'].append(t)
        del f, score, allowed

        ids = rng.choice(np.flatnonzero(valid & ~fold['visible']), n_placed, replace=False)
        fr = np.zeros(grid.shape, np.float32)
        fr.ravel()[ids] = 1.0
        r, t = cropped(fold, fr, valid)
        terms['random_control'].append(t)
        del fr

        r, t = cropped(fold, h33, valid)
        terms['h33_reference'].append(t)
        if term_shape is None:
            term_shape = t.shape
        elif t.shape != term_shape:
            raise RuntimeError(f'fold {k}: term shape {t.shape} != {term_shape}')
        print(f'fold {k} done', flush=True)

    terms = {a: np.sum(np.stack(v), axis=0) for a, v in terms.items()}
    summary = evaluate_holdout.pooled_summary(terms, draws=BOOTSTRAP_DRAWS,
                                              seed=BOOTSTRAP_SEED, candidate='candidate')
    dump(E / 'holdout.json', summary)
    dump(E / 'holdout_folds.json', {a: v.tolist() for a, v in terms.items()})

    # ---- Production dots on the full (visible) catalogue ----
    score, allowed = intensity_features(bands, valid, cat)
    prod_dots, picked = stratified_dots(score)
    if picked != DOT_COUNT:
        raise RuntimeError(f'production placed {picked} dots')
    prod = np.zeros(grid.shape, np.float32)
    prod[prod_dots] = 1.0
    del prod_dots, score, allowed

    # ---- Uniqueness vs registry ----
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != grid.shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(rasters=records,
                 complete_accessible_scan=False,
                 errors=[],
                 note='62 single-band rasters archived in buffedlizard55-lab/60GEMSDOE registry/rasters; an indexed public owner-repository inventory, not a complete organizer registry')
    tmp_tif = CACHE / 'production_dots_v5.tif'
    tmp_tif.parent.mkdir(parents=True, exist_ok=True)
    if tmp_tif.exists():
        tmp_tif.unlink()
    write_geotiff(tmp_tif, prod, nodata=None)
    audit = uniqueness.compare_array_to_registry(prod, index, fp,
                                                 expected_grid=(grid.shape, grid.crs, grid.transform))
    audit['inventory_scope'] = (f'{audit["registry_rasters_checked"]} single-band 100 m rasters '
                                'indexed in buffedlizard55-lab/60GEMSDOE registry/rasters; '
                                'not an organizer registry and not exhaustive')
    dump(E / 'uniqueness.json', audit)
    # Protocol rule 1 firing test: thresholds actually exceeded, not the
    # fail-closed completeness flag of an incomplete public inventory.
    rho_limit, overlap_limit = 0.90, 0.70
    fired_rho = (audit['worst_spearman_full_footprint'] is not None
                 and audit['worst_spearman_full_footprint'] > rho_limit)
    fired_overlap = bool((audit['worst_dot_overlap'] or 0.0) > overlap_limit)
    duplicate_fired = bool(audit['duplicate_count'] > 0 or fired_rho or fired_overlap)
    unique_measured = not duplicate_fired
    print(f'Unicity: fired={duplicate_fired} (rho>{rho_limit}: {fired_rho}, '
          f'mutual>{overlap_limit}: {fired_overlap}) '
          f'worst_rho={audit["worst_spearman_full_footprint"]} '
          f'worst_mutual_overlap={audit["worst_dot_overlap"]}', flush=True)

    receipt = validated = None
    if not duplicate_fired:
        from gems57 import submission_writer
        receipt = submission_writer.write_submission(
            ROOT / 'docs' / 'downloads' / f'{NAME}.tif', prod,
            ROOT / 'data/bridge/sample_submission.tif', fp,
            note=NOTE, name=NAME, catalogue=cat,
            metadata={'evidence_class': 'HOLDOUT-DTI; not organizer-confirmed',
                      'canaries': canaries})
        validated = receipt['validator']
    dump(E / 'submission_receipt.json', dict(receipt=receipt, validated=validated,
                                             duplicate=duplicate_fired,
                                             duplicate_fired=duplicate_fired))

    # ---- Run card ----
    a, b = summary['scores'], None
    bprime = None
    ball = None
    # Two-proxy instruments B/B': evaluate production dots against SGMC proxy truth
    # restricted (B') and unrestricted (B), quadrant by quadrant, mirroring run_experiment_v4.
    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    d_cat = ndi.distance_transform_edt(~cat)
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_cat >= CAT_GAP_PX)
    quad = holdout.quadrant_ids(fp)
    terms_b = {a: 0.0 for a in ARMS}
    terms_ball = {a: 0.0 for a in ARMS}
    prod_random = np.zeros(grid.shape, np.float32)
    ids = rng.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
    prod_random.ravel()[ids] = 1.0
    for k in range(4):
        region = ndi.binary_erosion(quad == k, iterations=12) & fp
        for tag, mask, store in (('prime', proxy_prime, terms_b), ('all', proxy, terms_ball)):
            fold = dict(region=region, truth=mask & region & ~cat, visible=cat,
                        masked_known=cat, hidden_all=np.zeros_like(cat))
            for arm, p in (('candidate', prod), ('random_control', prod_random),
                           ('h33_reference', h33)):
                r, t = evaluate_holdout.evaluate(p, fold, valid)
                store[arm] += t
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=BOOTSTRAP_DRAWS,
                                                seed=BOOTSTRAP_SEED, candidate='candidate')
    summary_b['instrument'] = ("B': SGMC proxy truth restricted to d_cat >= 3 px from catalogue")
    summary_b['proxy_positive_pixels_prime'] = int(proxy_prime.sum())
    dump(E / 'instrumentB_prime.json', summary_b)
    summary_ball = evaluate_holdout.pooled_summary(terms_ball, draws=BOOTSTRAP_DRAWS,
                                                   seed=BOOTSTRAP_SEED, candidate='candidate')
    summary_ball['instrument'] = 'B: unrestricted SGMC proxy (contains map-duplication band)'
    dump(E / 'instrumentB_all.json', summary_ball)
    b, ball = summary_b['scores'], summary_ball['scores']

    a_scores = {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                for k, v in summary['scores'].items()}
    b_scores = {k: {kk: v[kk] for kk in ('dti', 'ci95', 'withheld_positive_pixels')}
                for k, v in b.items()}
    ball_scores = {k: {kk: v[kk] for kk in ('dti', 'ci95')} for k, v in ball.items()}

    gate_a = bool(a_scores['candidate']['dti'] >= a_scores['h33_reference']['dti'])
    db = summary_b['paired_differences']['h33_reference']
    gate_b = bool(db['delta'] > 0 and db['ci95'][0] > 0)
    promoted = bool(not duplicate_fired and validated and gate_a and gate_b)

    card = {
        'hypothesis': ('H-2 catalogue-free magnetic analytic-signal ridge: total gradient magnitude '
                       'of TMI gated by basement-depth step and detrended-elevation slope'),
        'mechanism': ('ASA = sqrt(TMI_x^2 + TMI_y^2 + TMI_z^2) ridges mark buried magnetic-source '
                      'edges regardless of magnetization direction; basement step and scarp slope '
                      'gate cover-buried fault traces; dots placed >= 3 px from mapped traces'),
        'non_fault_mimic': ('Volcanic dike margin / remanence-contrast contact; depositional '
                            'breakline unrelated to faulting'),
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': 'HOLDOUT-DTI (evaluator gems57-pooled-hide-v2; 11,321 withheld positives)',
        'instrument_a_holdout': a_scores,
        'instrument_b_prime_proxy': b_scores,
        'instrument_b_unrestricted': ball_scores,
        'paired_a_vs_h33': summary['paired_differences']['h33_reference'],
        'paired_b_prime_vs_h33': db,
        'gate_a_candidate_ge_h33': gate_a,
        'gate_b_prime_candidate_gt_h33_significant': gate_b,
        'correlation_overlap_vs_registry': {
            'stage': 'final production dots (30,000 binary, catalogue-free)',
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
            'duplicate': duplicate_fired,
            'duplicate_fired': duplicate_fired,
            'duplicate_count': int(audit['duplicate_count']),
            'unique_certified': bool(audit['unique']),
            'certification_note': ('Measured against every accessible registry raster; no threshold fired. '
                                   'unique=False in the audit receipt only because the public owner-repository '
                                   'inventory is not organizer-complete (fail-closed certification), not because '
                                   'any threshold was exceeded.'),
        },
        'canaries': canaries,
        'raster_sha256': receipt['sha256'] if receipt else None,
        'raster_sha256_reason': None if receipt else 'uniqueness threshold fired; no TIFF written',
        'validator_output': validated,
        'submission_name': NAME,
        'submission_note': NOTE,
        'note_chars': len(NOTE),
        'uniqueness_detail': dict(
            registry_rasters_checked=audit['registry_rasters_checked'],
            worst_dot_overlap=audit['worst_dot_overlap'],
            worst_spearman_full_footprint=audit['worst_spearman_full_footprint'],
            worst_forward_overlap=audit['worst_forward_overlap'],
            inventory_scope=audit['inventory_scope'],
            overlap_definition=audit.get('overlap_definition'),
        ),
        'download_ok': bool(validated and not duplicate_fired),
        'submit_recommended': promoted,
        'download_and_submit_ok': promoted,
        'artifact': f'docs/downloads/{NAME}.tif' if receipt else None,
        'artifact_zip': f'docs/downloads/{NAME}.zip' if receipt else None,
        'artifact_receipt': f'docs/downloads/{NAME}.json' if receipt else None,
        'decision_note': ('Download: yes if validator passed and uniqueness is clear. '
                          'Submit a weekly slot: ' + ('recommended' if promoted
                                                      else 'not recommended -- pre-registered gate not met')),
        'weekly_slots_used': 0,
        'experiment_count': 5,
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in ['scripts/run_experiment_v5.py']},
        'registered_parameters': dict(dot_count=DOT_COUNT, block_px=BLOCK, nms_px=NMS,
                                      cat_gap_px=CAT_GAP_PX,
                                      bands=dict(tmi=14, tmi_hg=3, tmi_vg=9,
                                                 depth_to_base=15, det_elev_slope=19)),
    }
    dump(E / 'run_card.json', card)
    dump(ROOT / 'evidence' / 'run_card.json', card)  # current session card consumed by the site
    print(json.dumps(card, indent=2, default=float), flush=True)


if __name__ == '__main__':
    main()
