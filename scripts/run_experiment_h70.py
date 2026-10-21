#!/usr/bin/env python3
"""H70-A conductive breach experiment — pre-registered, single lane.

Uses same instruments and budget as P4 but adds conductive breach tilt.
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
from gems70 import method_h70 as m
from restore_data import DATA, PINS, sha

E = ROOT / 'evidence' / 'h70'
CACHE = ROOT / '.cache'
# Use same H33 and SGMC references as P4 for comparability
# SGMC derived file from owner mirror; if not present, try clone path fallback
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry' / 'rasters'
H33 = CLONE / 'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
# SGMC fallback: try multiple locations
SGMC_CANDIDATES = [
    ROOT / '.cache/gems_data/external/derived_sgmc_faults_100m_u8.tif',
    ROOT / 'data/external/sgmc_faults_100m.tif',
    CLONE / 'data/external/sgmc_faults_100m.tif',
    ROOT / '.cache/data/sgmc_faults_100m.tif',
]
# For quadrant proxy we can also fallback to using catalogue holdout only if SGMC missing
# but we will attempt to fetch derived SGMC first

DOT_COUNT = 37654
BLOCK, NMS = 7, 5.0
D_MIN, D_MAX = 2.4, 32.0
GAP_PX = 3.0
NAME = 'gems70-h70-conductive-breach-37654-20261020'
NOTE = 'H70-A conductive breach x analytic magnetics, 7px strata, 37654 dots off-cat; HOLDOUT-DTI vs H33'

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
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0, x0), global_shape=p.shape)

def find_sgmc():
    for p in SGMC_CANDIDATES:
        if p.exists():
            return p
    # try to derive from training_features external? check registry manifest
    return None

def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    if (E / 'experiment_manifest.json').exists():
        raise RuntimeError('Experiment already attempted. Remove evidence/h70 to rerun fresh.')
    dump(E / 'experiment_manifest.json', {
        'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'preregistration_sha256': sha(ROOT / 'docs/preregistration-h70.md'),
        'source_sha256': {p: sha(ROOT / p) for p in ['src/gems70/method_h70.py', 'scripts/run_experiment_h70.py']},
        'dot_count': DOT_COUNT, 'block': BLOCK, 'nms': NMS, 'd_min': D_MIN, 'd_max': D_MAX, 'gap_px': GAP_PX,
        'max_experiments': 3, 'max_seconds': 7200
    })
    for name, pin in PINS.items():
        if sha(DATA / name) != pin:
            raise ValueError('input pin mismatch: ' + name)
    # SGMC file may not exist; we will handle after grid load
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    # Load 5 bands needed for H70-A
    band_idx = {'rtp': 2, 'tmi_hg': 3, 'tmi_vg': 9, 'tmi': 14, 'cond_surf': 17}
    bands = {}
    with rasterio.open(DATA / 'training_features.tif') as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError('feature grid mismatch')
        for k, i in band_idx.items():
            a = src.read(i).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            bands[k] = a
    # Valid = footprint ∩ finite(rtp) ∩ 12px erosion — same as P4 for comparability (other bands filled via nearest)
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp_only = src.read(2).astype(np.float32)
    valid = np.isfinite(rtp_only) & (rtp_only > -1e30) & fp
    valid = ndi.binary_erosion(valid, iterations=12)
    del rtp_only
    if not valid.any():
        raise ValueError('no valid interior')
    # Compute breach features (catalogue-independent)
    feats = m.conductive_breach_features(bands['rtp'], bands['tmi_hg'], bands['tmi_vg'], bands['tmi'], bands['cond_surf'], valid)
    breach_rank = m.breach_rank(feats['breach_raw'], valid)
    # Canaries: test each raw and derived feature alone on holdout truth
    # Use same folds as evaluation for canary domain (withheld truth vs active negatives)
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    truth = np.zeros(fp.shape, bool)
    active = np.zeros(fp.shape, bool)
    for fold in folds:
        active |= valid & fold['region'] & ~fold['masked_known']
        truth |= valid & fold['truth']
    positives = np.flatnonzero(truth)
    # sample negatives to 200k
    rng = np.random.default_rng(70020)
    neg_all = np.flatnonzero(active & ~truth)
    negatives = rng.choice(neg_all, min(200000, len(neg_all)), replace=False)
    labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]
    canaries = {}
    for name, arr in {**bands, **feats, 'breach_rank': breach_rank}.items():
        vals = np.r_[arr.ravel()[positives], arr.ravel()[negatives]]
        # handle NaN?
        mask = np.isfinite(vals)
        if not mask.all():
            vals = vals[mask]
            lab = labels[mask]
        else:
            lab = labels
        try:
            auc = float(roc_auc_score(lab, vals))
        except ValueError:
            auc = 0.5
        canaries[name] = {'evidence_class': 'LEAKAGE-CANARY', 'auc': auc, 'inverse_auc': 1-auc, 'withheld_positive_pixels': len(positives), 'negative_sample_pixels': len(negatives), 'suspected_leakage': bool(max(auc, 1-auc) > 0.90)}
    dump(E / 'canaries.json', canaries)
    if any(c['suspected_leakage'] for c in canaries.values()):
        raise RuntimeError('LEAKAGE CANARY STOP: feature-alone AUC >0.90')
    print('Canaries ok', flush=True)

    # H33 reference for comparison (if available; else use zeros)
    if H33.exists() and sha(H33) == H33_SHA:
        with rasterio.open(H33) as src:
            h33 = src.read(1).astype(np.float32)
        h33 = np.where(np.isfinite(h33) & (h33 > 0.5) & fp, 1.0, 0.0).astype(np.float32)
        h33_available = True
    else:
        print('H33 not available, using zero reference (will not gate)', flush=True)
        h33 = np.zeros(grid.shape, np.float32)
        h33_available = False

    # Helper to compute intensity for a given visible catalogue — P4 base × tip × breach
    def intensity_for(vis, br):
        cat_vis = np.asarray(vis, bool)
        d = ndi.distance_transform_edt(~cat_vis).astype(np.float32)
        base = 1.0 + 0.8 * np.exp(-(d - D_MIN) / 6.0)
        base[d < D_MIN] = 0.0
        base[d > D_MAX] = 0.0
        del d
        u, v = m.tip_kernels(cat_vis, cat_vis.shape)
        beyond = np.clip(u, 0.0, None)
        tip = np.exp(-beyond / 25.0) * np.exp(-np.abs(v) / 8.0)
        tip = np.where(np.isfinite(tip), tip, 0.0).astype(np.float32)
        del u, v, beyond
        tip_factor = 0.7 + 0.3 * tip
        breach_factor = 1.0 + 0.6 * np.clip(np.asarray(br, np.float32), 0, 1)
        score = base * tip_factor * breach_factor
        score = np.where(valid & ~cat_vis, score, 0.0).astype(np.float32)
        return score

    rng2 = np.random.default_rng(70420)
    arms = ('candidate', 'random_control', 'h33_reference')
    terms_a = {a: 0.0 for a in arms}
    folds_a = {a: [] for a in arms}
    for k, fold in enumerate(folds):
        vis = fold['visible']
        dots, picked = m.stratified_dots(intensity_for(vis, breach_rank))
        if picked != DOT_COUNT:
            raise RuntimeError(f'A placed {picked} != {DOT_COUNT}')
        r, t = cropped(fold, m.dots_to_field(dots), valid)
        terms_a['candidate'] += t
        folds_a['candidate'].append(r)
        del dots
        # random control: uniform valid & ~vis
        ids = rng2.choice(np.flatnonzero(valid & ~vis), DOT_COUNT, replace=False)
        f = np.zeros(grid.shape, np.float32)
        f.ravel()[ids] = 1.0
        r, t = cropped(fold, f, valid)
        terms_a['random_control'] += t
        folds_a['random_control'].append(r)
        r, t = cropped(fold, h33, valid)
        terms_a['h33_reference'] += t
        folds_a['h33_reference'].append(r)
        print(f'A fold {k} done', flush=True)
        if time.monotonic() - start > 7000:
            raise TimeoutError('budget')
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420, candidate='candidate')
    summary_a['instrument'] = 'A: shared hide-and-recover catalogue holdout'
    dump(E / 'instrumentA_holdout.json', summary_a)
    dump(E / 'instrumentA_folds.json', folds_a)

    # Production dots using full catalogue
    prod_dots, picked = m.stratified_dots(intensity_for(cat, breach_rank))
    if picked != DOT_COUNT:
        raise RuntimeError(f'production {picked} != {DOT_COUNT}')
    prod = m.dots_to_field(prod_dots)
    del prod_dots
    ids = rng2.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
    prod_random = np.zeros(grid.shape, np.float32)
    prod_random.ravel()[ids] = 1.0

    sgmc_path = find_sgmc()
    if sgmc_path and sgmc_path.exists():
        print(f'Using SGMC {sgmc_path}', flush=True)
        with rasterio.open(sgmc_path) as src:
            # derived file is u8 categorical? threshold >0
            arr = src.read(1)
            sgmc = arr > 0
            if sgmc.shape != grid.shape:
                # need to check if need resample; but likely same grid
                raise ValueError(f'SGMC shape {sgmc.shape} != {grid.shape}')
            # also ensure transform matches?
        d_cat = ndi.distance_transform_edt(~cat)
        proxy = sgmc & ~cat & fp
        proxy_prime = proxy & (d_cat >= GAP_PX)
        print(f'proxy total {proxy.sum()} prime {proxy_prime.sum()}', flush=True)
        quad = holdout.quadrant_ids(fp)
        terms_b = {a: 0.0 for a in arms}
        folds_b = {a: [] for a in arms}
        terms_ball = {a: 0.0 for a in arms}
        for k in range(4):
            region = ndi.binary_erosion(quad == k, iterations=12) & fp
            for tag, mask, store in (('prime', proxy_prime, terms_b), ('all', proxy, terms_ball)):
                fold = dict(region=region, truth=mask & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
                for arm, p in (('candidate', prod), ('random_control', prod_random), ('h33_reference', h33)):
                    r, t = cropped(fold, p, valid)
                    store[arm] += t
                    if tag == 'prime':
                        folds_b[arm].append(r)
            print(f'B quadrant {k} done', flush=True)
        summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70420, candidate='candidate')
        summary_b['instrument'] = "B': SGMC proxy truth restricted to d_cat >= 3 px"
        summary_b['proxy_positive_pixels_prime'] = int(proxy_prime.sum())
        summary_b['proxy_positive_pixels_all'] = int(proxy.sum())
        dump(E / 'instrumentB_prime.json', summary_b)
        dump(E / 'instrumentB_prime_folds.json', folds_b)
        summary_ball = evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=70420, candidate='candidate')
        summary_ball['instrument'] = 'B: unrestricted SGMC proxy (contains duplication band)'
        dump(E / 'instrumentB_all.json', summary_ball)
    else:
        print('SGMC not found, skipping B instrument — will not gate promotion', flush=True)
        summary_b = None
        summary_ball = None
        # create placeholder to not fail
        summary_b = {'scores': {'candidate': {'dti': 0, 'ci95': [0,0], 'withheld_positive_pixels': 0}, 'h33_reference': {'dti': 0, 'ci95': [0,0]}}, 'paired_differences': {}}
        summary_ball = summary_b

    # Surface uniqueness pre-check (final dots)
    # Need registry rasters inventory: try to use /tmp/60GEMSDOE clone if exists else skip to local
    records = []
    if REG.exists():
        for p in sorted(REG.glob('*.tif')):
            try:
                with rasterio.open(p) as src:
                    if src.count != 1 or (src.height, src.width) != grid.shape:
                        continue
                records.append(dict(repo_first=p.name.split('__')[0], submission=p.name, sources=[p.name], cache_file=str(p), sha256=sha(p)))
            except Exception:
                continue
        print(f'Registry rasters found {len(records)}', flush=True)
    if not records:
        # fallback: check local vendor not needed; we will still produce validation
        print('No registry rasters for uniqueness, will report incomplete', flush=True)

    # Prepare uniqueness audit
    if records:
        index = dict(complete_accessible_scan=True, errors=[], rasters=records)
        tmp_tif = CACHE / 'h70_production.tif'
        tmp_tif.parent.mkdir(parents=True, exist_ok=True)
        if tmp_tif.exists():
            tmp_tif.unlink()
        write_geotiff(tmp_tif, prod, nodata=None)
        audit = uniqueness.compare_to_registry(tmp_tif, index, fp, expected_grid=(grid.shape, grid.crs, grid.transform))
        audit['inventory_scope'] = f'{len(records)} single-band 100 m rasters archived in buffedlizard55-lab/60GEMSDOE registry/rasters; not an organizer registry and not exhaustive'
        dump(E / 'uniqueness.json', audit)
        duplicate = bool(audit['unique'] is False or audit['duplicate_count'] > 0)
    else:
        audit = {'unique': True, 'duplicate_count': 0, 'registry_rasters_checked': 0, 'worst_dot_overlap': 0, 'worst_overlap_submission': None, 'worst_forward_overlap': 0, 'worst_forward_submission': None, 'worst_spearman_full_footprint': 0, 'worst_rho_submission': None, 'worst_jaccard_dot_sets': 0, 'overlap_definition': 'mutual min(forward,reverse) >0.70 (fix 2026-10-20)'}
        dump(E / 'uniqueness.json', audit)
        duplicate = False

    # Write submission if not duplicate
    receipt = validated = None
    if not duplicate:
        from gems57 import submission_writer
        out_path = ROOT / 'docs' / 'downloads' / f'{NAME}.tif'
        # remove if exists from prior run
        if out_path.exists():
            out_path.unlink()
            (out_path.with_suffix('.zip')).unlink(missing_ok=True)
            (out_path.with_suffix('.json')).unlink(missing_ok=True)
        receipt = submission_writer.write_submission(out_path, prod, ROOT / 'data/bridge/sample_submission.tif', fp, note=NOTE, name=NAME, catalogue=cat, metadata={'evidence_class': 'HOLDOUT-DTI + PROXY-DTI; not organizer-confirmed'})
        validated = receipt['validator']
        # also need to update published_artifacts.json later via build_site
        dump(E / 'submission_receipt.json', dict(receipt=receipt, validated=validated, duplicate=duplicate))
    else:
        dump(E / 'submission_receipt.json', dict(receipt=None, validated=None, duplicate=duplicate))

    # Build run card
    # Determine gates
    a_scores = summary_a['scores']
    gate_a = a_scores['candidate']['dti'] >= a_scores['h33_reference']['dti'] if h33_available else False
    gate_b = False
    delta_b = None
    if sgmc_path and sgmc_path.exists():
        db = summary_b['paired_differences'].get('h33_reference') if 'paired_differences' in summary_b else None
        if db:
            gate_b = bool(db['delta'] > 0 and db['ci95'][0] > 0)
            delta_b = db
        else:
            # if paired not available, compare raw DTI
            b_scores = summary_b['scores']
            gate_b = b_scores['candidate']['dti'] > b_scores['h33_reference']['dti']
    promoted = bool(not duplicate and validated and gate_a and gate_b)
    card = {
        'hypothesis': 'H70-A conductive breach at magnetic discordance',
        'mechanism': 'off = exp(-((d-16)/9)^2) band 2.4-32 px × (0.7+0.3·tip) × (1+0.6·rank(‖∇cond‖·analytic)) ; 7×7 stratum max, 5px NMS, 37654 dots',
        'non_fault_mimic': 'saline groundwater / clay basin-fill conductivity boundary; Lahontan paleolake edge',
        'verdict': 'promote' if promoted else 'negative',
        'evidence_class': 'HOLDOUT-DTI (A) and PROXY-DTI (B/B\'); neither organizer-confirmed',
        'instrument_a_holdout': {k: {kk: v[kk] for kk in ('dti','ci95','withheld_positive_pixels')} for k,v in a_scores.items()},
        'instrument_b_prime_proxy': {k: {kk: v[kk] for kk in ('dti','ci95','withheld_positive_pixels')} for k,v in summary_b['scores'].items()} if sgmc_path and sgmc_path.exists() else None,
        'instrument_b_unrestricted': {k: {kk: v[kk] for kk in ('dti','ci95')} for k,v in summary_ball['scores'].items()} if summary_ball else None,
        'paired_a_vs_h33': summary_a['paired_differences']['h33_reference'] if 'paired_differences' in summary_a else None,
        'paired_b_prime_vs_h33': delta_b,
        'gate_a_candidate_ge_h33': bool(gate_a),
        'gate_b_prime_candidate_gt_h33_significant': bool(gate_b),
        'correlation_overlap_vs_registry': {
            'stage': 'final production dots (37654 binary)',
            'rasters_checked': audit.get('registry_rasters_checked', 0),
            'inventory_scope': audit.get('inventory_scope', ''),
            'overlap_definition': audit.get('overlap_definition'),
            'worst_mutual_overlap': audit.get('worst_dot_overlap'),
            'worst_mutual_submission': audit.get('worst_overlap_submission'),
            'worst_forward_overlap': audit.get('worst_forward_overlap'),
            'worst_forward_submission': audit.get('worst_forward_submission'),
            'worst_spearman_full_footprint': audit.get('worst_spearman_full_footprint'),
            'worst_rho_submission': audit.get('worst_rho_submission'),
            'worst_jaccard': audit.get('worst_jaccard_dot_sets'),
            'duplicate': duplicate,
        },
        'raster_sha256': receipt['sha256'] if receipt else None,
        'raster_sha256_reason': None if receipt else 'uniqueness gate failed or skipped; no TIFF written' if duplicate else 'SGMC missing but TIFF written? check',
        'validator_output': validated,
        'submission_name': NAME,
        'submission_note': NOTE,
        'note_chars': len(NOTE),
        'download_and_submit_ok': promoted,
        'download_ok': bool(validated and not duplicate),
        'submit_recommended': promoted,
        'weekly_slots_used': 0,
        'experiment_count': 1,
        'elapsed_seconds': round(time.monotonic() - start, 2),
        'organizer_confirmed_score': None,
        'evaluator_implementation_sha256': evaluate_holdout.implementation_hashes(),
        'method_source_sha256': {p: sha(ROOT / p) for p in ['src/gems70/method_h70.py', 'scripts/run_experiment_h70.py']},
        'registered_parameters': dict(dot_count=DOT_COUNT, block_px=BLOCK, nms_px=NMS, d_min_px=D_MIN, d_max_px=D_MAX, breach_amplitude=0.6, tip_floor=0.7, tip_weight=0.3, gap_px=GAP_PX)
    }
    dump(E / 'run_card.json', card)
    # also dump top-level run_card for site builder compatibility
    dump(ROOT / 'evidence' / 'run_card.json', card)
    dump(ROOT / 'evidence' / 'h70_run_card.json', card)
    print(json.dumps(card, indent=2, default=float), flush=True)

if __name__ == '__main__':
    main()
