#!/usr/bin/env python3
"""Diagnostic (not an experiment, no candidate): do our offline instruments track the live board?

For every archived raster with a user/owner-reported live score, compute
* B'  : pooled DTI vs SGMC-only faults >= 3 px off catalogue (4 eroded quadrants),
* A   : pooled DTI on the shared hide-and-recover catalogue holdout (seed 20),
and the Spearman rank correlation of each instrument with the reported live score.

Live scores are OWNER-REPORT / user-supplied (registry/calibration_manifest.json of
buffedlizard55-lab/60GEMSDOE and the project brief); none is organizer-confirmed here.
Name-to-file identity for brief-sourced rows is by repository file name only (flagged).
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
from scipy.stats import spearmanr

from gems57 import evaluate_holdout, holdout
from gems57.grid import load_grid
from restore_data import DATA, sha
from run_experiment_v4 import cropped

CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry/rasters'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'
OUT = ROOT / 'evidence/s3/proxy_calibration.json'

ROWS = [  # (file, live score, source)
    ('dotted_b2_prune_02778.tif', 0.2778, 'calibration_manifest'),
    ('dotted_d2_8_02708.tif', 0.2708, 'calibration_manifest'),
    ('tip_stepover_r30_02632.tif', 0.2632, 'calibration_manifest'),
    ('dotted_d2_8_02600.tif', 0.2600, 'calibration_manifest'),
    ('calib_d15_02477.tif', 0.2477, 'calibration_manifest'),
    ('calib_h195_01922.tif', 0.1922, 'calibration_manifest'),
    ('calib_h194_01894.tif', 0.1894, 'calibration_manifest'),
    ('calib_h161_01855.tif', 0.1855, 'calibration_manifest'),
    ('calib_h28ridge_01839.tif', 0.1839, 'calibration_manifest'),
    ('calib_h25ctx_01280.tif', 0.1280, 'calibration_manifest'),
    ('calib_r13lattice_00904.tif', 0.0904, 'calibration_manifest'),
    ('GEMSDOE28__h32-1-prethin-tip-euler-d2-8.tif', 0.2649, 'user brief (name match only)'),
    ('GEMSDOE28__h36-1-rung30-blind-r1.tif', 0.2710, 'user brief (name match only)'),
    ('GEMSDOE28__h38-1-hf-euler-r30-r1.tif', 0.2707, 'user brief (name match only)'),
    ('GEMSDOE29__wormrank-d28.tif', 0.2560, 'user brief (name match only)'),
    ('GEMSDOE36__anderson-geothermal-pinn-38854.tif', 0.2750, 'user brief (name match only)'),
    ('GEMSDOE49__gate_ortho_w0.25-40k.tif', 0.2376, 'user brief (name match only)'),
    ('GEMSDOE27__topo-gap-closure-t-v2-on-d1-5.tif', 0.2449, 'user brief (name match only)'),
]


def load_pred(path, fp):
    with rasterio.open(path) as src:
        a = src.read(1).astype(np.float32)
    a = np.where(np.isfinite(a) & fp, a, 0.0)
    return np.clip(a, 0.0, 1.0).astype(np.float32)   # diagnostic read only; never written


def main():
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    with rasterio.open(DATA / 'training_features.tif') as src:
        rtp = src.read(2)
    valid = ndi.binary_erosion(np.isfinite(rtp) & (rtp > -1e30) & fp, iterations=12)
    del rtp
    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    d = ndi.distance_transform_edt(~cat)
    proxy_prime = sgmc & ~cat & fp & (d >= 3)
    quad = holdout.quadrant_ids(fp)
    regions = [ndi.binary_erosion(quad == k, iterations=12) & fp for k in range(4)]
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    tb, ta, rows = {}, {}, []
    for fname, live, source in ROWS:
        p = REG / fname
        if not p.exists():
            rows.append(dict(file=fname, error='missing'))
            continue
        pred = load_pred(p, fp)
        tb[fname] = 0.0
        for k in range(4):
            fold = dict(region=regions[k], truth=proxy_prime & regions[k], visible=cat,
                        masked_known=cat, hidden_all=np.zeros_like(cat))
            tb[fname] += cropped(fold, pred, valid)[1]
        ta[fname] = 0.0
        for fold in folds:
            ta[fname] += cropped(fold, pred, valid)[1]
        rows.append(dict(file=fname, sha256=sha(p), live_score_reported=live, score_source=source,
                         positive_pixels=int((pred > 0).sum()), mean_value=float(pred[fp].mean())))
        print(fname, flush=True)
    sb = evaluate_holdout.pooled_summary(tb, draws=200, seed=1, candidate=ROWS[0][0])['scores']
    sa = evaluate_holdout.pooled_summary(ta, draws=200, seed=1, candidate=ROWS[0][0])['scores']
    ok = [r for r in rows if 'error' not in r]
    for r in ok:
        r['b_prime_dti'] = sb[r['file']]['dti']
        r['a_dti'] = sa[r['file']]['dti']
    live = [r['live_score_reported'] for r in ok]
    res = dict(
        evidence_class='INSTRUMENT-CALIBRATION DIAGNOSTIC (owner/user-reported live scores; not organizer-confirmed)',
        n=len(ok),
        spearman_live_vs_b_prime=float(spearmanr(live, [r['b_prime_dti'] for r in ok])[0]),
        spearman_live_vs_a=float(spearmanr(live, [r['a_dti'] for r in ok])[0]),
        rows=rows,
        note=('Positive correlation means the instrument orders archived files the way the live '
              'board did. Values were clipped to [0,1] in memory for evaluation only.'))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: res[k] for k in ('n', 'spearman_live_vs_b_prime', 'spearman_live_vs_a')}))
    for r in sorted(ok, key=lambda r: -r['live_score_reported']):
        print(f"{r['live_score_reported']:.4f}  B'={r['b_prime_dti']:.4f}  A={r['a_dti']:.4f}  n={r['positive_pixels']}  {r['file']}")


if __name__ == '__main__':
    main()
