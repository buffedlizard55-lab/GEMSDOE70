"""POST-HOC output-transform diagnostic for experiment 2 (C1). NOT preregistered.

Question: is the C1 deficit against random placement caused by the linear upper-2% rescale
(most candidate dots have values near 0, while the random control uses a constant 0.5)?
Test: give every arm the SAME binary output (top 2% -> 1.0, everything else 0) on the
SAME fresh holdout blocks (seed 71). Result is labelled POST-HOC and cannot promote a
candidate by itself; a fresh preregistered run is required before any claim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]
import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57 import evaluate_holdout, holdout
from gems57.grid import load_grid
from gems70 import strike
from gems70.method import rank01
from restore_data import DATA, PINS, sha
from run_experiment import cropped

E = ROOT / 'evidence'


def binary_top(score, valid, frac=0.02):
    """Binary output: highest ``frac`` of valid cells -> 1.0; all else exactly 0.0."""
    v = score[valid]
    k = int(round(frac * valid.sum()))
    thr = np.partition(v, -k)[-k]
    out = np.zeros(score.shape, np.float32)
    out[valid & (score >= thr)] = 1.0
    return out


def main() -> int:
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError('input pin mismatch: ' + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    with rasterio.open(DATA / 'training_features.tif') as src:
        hits = [i + 1 for i, d in enumerate(src.descriptions) if d and d.split(' ')[0].split('-')[0].strip() == 'rtp']
        rtp = src.read(hits[0]).astype(np.float32)
    rtp[(rtp <= -1e30) | ~np.isfinite(rtp) | ~fp] = np.nan
    valid = ndi.binary_erosion(fp & np.isfinite(rtp), iterations=12)
    folds, _ = holdout.buffered_component_draw(grid, seed=71, buffer_px=3, boundary_px=12)
    visible = folds[0]['visible']
    feats = strike.features(rtp, visible, valid)
    scores = {
        'candidate': strike.combine(feats, valid, 'candidate'),
        'ablation_no_catalogue': strike.combine(feats, valid, 'ablation_no_catalogue'),
        'ablation_no_alignment': strike.combine(feats, valid, 'ablation_no_alignment'),
    }
    arms = {k: binary_top(v, valid) for k, v in scores.items()}
    rng = np.random.default_rng(70071)
    n = int(arms['candidate'].sum())
    rnd = np.zeros(fp.shape, np.float32)
    rnd.ravel()[rng.choice(np.flatnonzero(valid), n, replace=False)] = 1.0
    arms['random_control'] = rnd
    terms = {}
    for name, a in arms.items():
        terms[name] = sum(t for _, t in (cropped(f, a, valid) for f in folds))
    summary = evaluate_holdout.pooled_summary(terms, draws=1000, seed=71, candidate='candidate')
    out = {
        'evidence_class': 'HOLDOUT-DTI',
        'label': 'POST-HOC DIAGNOSTIC, NOT PREREGISTERED, NOT A PROMOTION BASIS',
        'reason': 'Tests whether the output transform (linear upper-2% rescale) explains the deficit.',
        'transform': 'binary top 2% of valid cells -> 1.0, others 0.0 (same for all arms)',
        'holdout_seed': 71,
        'positives_per_arm': n,
        'scores': {k: {'dti': v['dti'], 'ci95': v['ci95'], 'tpw': v['tpw'], 'fpw': v['fpw'], 'fnw': v['fnw']}
                   for k, v in summary['scores'].items()},
        'paired_differences': {k: {'delta': v['delta'], 'ci95': v['ci95']}
                               for k, v in summary['paired_differences'].items()},
        'evaluator_version': evaluate_holdout.VERSION,
    }
    (E / 'c1_posthoc_binary_diagnostic.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    print(json.dumps(out['scores'], indent=2, allow_nan=False))
    print(json.dumps(out['paired_differences'], indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
