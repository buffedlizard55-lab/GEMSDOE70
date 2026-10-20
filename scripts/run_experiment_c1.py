"""Experiment 2 (session 2026-10-20): candidate C1, strike-coherent catalogue extrapolation.

Pre-registered in docs/candidates-2026-10-20.md BEFORE this file was run. Uses FRESH
holdout blocks (seed 71), not the seed-20 blocks already reported in evidence/holdout.json.
Writes evidence/c1_* only. Never writes a TIFF; the export step is a separate script.
"""
from __future__ import annotations

import datetime as dt
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

from gems57 import evaluate_holdout, holdout
from gems57.grid import load_grid
from gems70.method import rank01, upper_surface
from gems70 import strike
from restore_data import DATA, PINS, sha
from run_experiment import cropped  # shared crop helper from the stopped run (unchanged code)

E = ROOT / 'evidence'
SEED = 71
CANARY_SEED = 70071
CANARY_NEG = 200000


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def main() -> int:
    t0 = time.monotonic()
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError('input pin mismatch: ' + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    with rasterio.open(DATA / 'training_features.tif') as src:
        # Band descriptions are free text ("rtp - Reduced to pole ..."); match on the name prefix.
        hits = [i + 1 for i, d in enumerate(src.descriptions) if d and d.split(' ')[0].split('-')[0].strip() == 'rtp']
        if len(hits) != 1 or hits[0] != 2:
            raise ValueError(f'rtp band not uniquely identified: {hits}')
        rtp = src.read(hits[0]).astype(np.float32)
    rtp[(rtp <= -1e30) | ~np.isfinite(rtp) | ~fp] = np.nan
    valid = fp & np.isfinite(rtp)
    valid = ndi.binary_erosion(valid, iterations=12)
    if not valid.any():
        raise ValueError('no valid interior')

    folds, _ = holdout.buffered_component_draw(grid, seed=SEED, buffer_px=3, boundary_px=12)
    visible = folds[0]['visible']          # global holdout-visible catalogue (same for all folds)
    dump(E / 'c1_holdout_split.json', {
        'evidence_class': 'HOLDOUT-DTI', 'seed': SEED, 'fresh_blocks_not_seed20': True,
        'receipts': [f['receipt'] for f in folds],
        'total_withheld_positive_pixels': int(sum((f['truth'] & valid).sum() for f in folds)),
        'visible_catalogue_pixels': int(visible.sum()),
        'catalogue_features_from': 'visible traces only (holdout-visible mask)'})

    feats = strike.features(rtp, visible, valid)
    truth = np.zeros(fp.shape, bool)
    active = np.zeros(fp.shape, bool)
    for fold in folds:
        active |= valid & fold['region'] & ~fold['masked_known']
        truth |= valid & fold['truth']
    positives = np.flatnonzero(truth)
    negatives = np.flatnonzero(active & ~truth)
    rng = np.random.default_rng(CANARY_SEED)
    negatives = rng.choice(negatives, min(CANARY_NEG, len(negatives)), replace=False)
    labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]

    canaries = {}
    for name, a in {'rtp': rtp, **feats}.items():
        a = np.where(np.isfinite(a), a, 0.0)
        values = np.r_[a.ravel()[positives], a.ravel()[negatives]]
        auc = float(roc_auc_score(labels, values))
        canaries[name] = {'evidence_class': 'LEAKAGE-CANARY', 'auc': auc, 'inverse_auc': 1 - auc,
                          'withheld_positive_pixels': int(len(positives)),
                          'negative_sample_pixels': int(len(negatives)),
                          'suspected_leakage': bool(max(auc, 1 - auc) > 0.90)}
    dump(E / 'c1_canaries.json', canaries)
    leak = [k for k, v in canaries.items() if v['suspected_leakage']]
    if leak:
        dump(E / 'c1_result.json', {'stop': 'LEAKAGE CANARY', 'features': leak})
        print('LEAKAGE CANARY STOP', leak, flush=True)
        return 2
    print('canaries complete', flush=True)

    arms = {'candidate': strike.combine(feats, valid, 'candidate'),
            'ablation_no_catalogue': strike.combine(feats, valid, 'ablation_no_catalogue'),
            'ablation_no_alignment': strike.combine(feats, valid, 'ablation_no_alignment')}
    arms = {k: upper_surface(v, valid) for k, v in arms.items()}
    npos = int((arms['candidate'] > 0).sum())
    random = np.zeros(fp.shape, np.float32)
    ids = rng.choice(np.flatnonzero(valid), npos, replace=False)
    random.ravel()[ids] = 0.5
    arms['random_control'] = random

    terms, per_fold = {}, {}
    for name, a in arms.items():
        pf = [cropped(f, a, valid) for f in folds]
        terms[name] = sum(t for _, t in pf)
        per_fold[name] = [r for r, _ in pf]
        print(name, 'evaluated', flush=True)

    result = evaluate_holdout.pooled_summary(terms, draws=1000, seed=SEED, candidate='candidate')
    result.update({
        'experiment': 'C1 strike-coherent catalogue extrapolation (experiment 2 of session budget)',
        'evaluator_version': evaluate_holdout.VERSION,
        'holdout_seed': SEED,
        'interpretation': 'Continuous pre-placement surface HOLDOUT-DTI; not final dots; not organizer-confirmed.',
        'candidate_positive_pixels': npos,
        'elapsed_seconds': round(time.monotonic() - t0, 2),
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    })
    dump(E / 'c1_holdout.json', result)
    dump(E / 'c1_holdout_folds.json', per_fold)
    cand = result['scores']['candidate']
    cat_free = result['scores']['ablation_no_catalogue']
    rnd = result['scores']['random_control']
    verdict = {
        'pass_no_leakage': True,
        'pass_beats_no_catalogue': cand['dti'] > cat_free['dti'],
        'pass_beats_random_control': cand['dti'] > rnd['dti'],
        'paired_difference_vs_random': result['paired_differences'].get('random_control'),
        'paired_difference_vs_no_catalogue': result['paired_differences'].get('ablation_no_catalogue'),
    }
    dump(E / 'c1_result.json', verdict)
    print(json.dumps(verdict, indent=2, allow_nan=False), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
