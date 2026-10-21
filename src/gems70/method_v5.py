"""Phase-5 supervised within-halo ranking (H-P5-1).

Preregistered in ``docs/hypotheses.md`` (Phase-5 addendum) before this code ran.
Every catalogue-dependent feature is derived from the *visible* catalogue of the
current holdout fold (parallel-run protocol rule 2); the SGMC proxy labels never
enter the instruments' truth except through the disclosed B'/B LOQO channel.

The stratified emission is the measured Phase-4 design (one dot per 7x7-px
stratum at the stratum maximum, best ``n`` strata, 5-px Euclidean NMS), copied
verbatim from ``scripts/run_experiment_v4.py`` so the two experiments share the
exact emission operator at fixed mass.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems70 import method_v2 as m2

# 19 cached physics bands, in stack order (evidence/feature_metadata.json).
STACK_FEATURES = [
    'mag_anom', 'rtp', 'tmi_hg', 'geod_2ndinv', 'iso_grav_anom_slope', 'tc',
    'geod_shearrate', 'geod_dilaterate', 'tmi_vg', 'deq_n100a15',
    'iso_grav_anom_vg', 'det_elev', 'iso_grav_anom', 'tmi',
    'depth_to_base_surf', 'ieq_n100a15', 'cond_surf', 'iso_grav_anom_hg',
    'det_elev_slope',
]
GEOMETRY_FEATURES = ['d_vis', 'tip_u', 'tip_v']
FEATURE_NAMES = STACK_FEATURES + GEOMETRY_FEATURES

# Registered constants (docs/hypotheses.md, Phase-5 addendum).
D_MIN, D_MAX = 2.4, 32.0
DOT_COUNT = 37654
BLOCK, NMS = 7, 5.0
N_NEGATIVES = 150_000
SEED = 70520
NEG_SEED = 70521
CANARY_STOP = 0.90


def geometry_columns(catalogue_visible, cells_yx):
    """(d, u, v) at ``cells_yx`` from the VISIBLE catalogue only.

    Full-grid intermediates are freed before returning; only the values at the
    requested cells survive, so five fold variants fit in memory at once.
    """
    cat = np.asarray(catalogue_visible, bool)
    d = ndi.distance_transform_edt(~cat).astype(np.float32)
    u, v = m2.tip_kernels(cat, cat.shape)
    out = (d[cells_yx].astype(np.float32, copy=False),
           u[cells_yx].astype(np.float32, copy=False),
           v[cells_yx].astype(np.float32, copy=False))
    del d, u, v
    return out


def band_mask(d_cells, allowed_cells, d_min=D_MIN, d_max=D_MAX):
    """Registered allowed domain: valid & off-catalogue & d_min <= d <= d_max."""
    d = np.asarray(d_cells, np.float32)
    allowed = np.asarray(allowed_cells, bool)
    return allowed & np.isfinite(d) & (d >= d_min) & (d <= d_max)


def make_model(seed: int = SEED) -> HistGradientBoostingClassifier:
    """Registered hyperparameters; nothing tuned after seeing a score."""
    return HistGradientBoostingClassifier(
        random_state=seed, max_iter=300, learning_rate=0.06,
        max_leaf_nodes=31, min_samples_leaf=40, l2_regularization=1.0,
        early_stopping=True, validation_fraction=0.1)


def select_rows(X, y, quad, *, n_negatives=N_NEGATIVES, neg_seed=NEG_SEED,
                exclude_quad=None):
    """(X, y, meta) with all in-band positives and uniform in-band negatives.

    ``exclude_quad`` implements leave-one-quadrant-out: rows whose quadrant id
    equals it are dropped entirely (both positives and negatives).
    """
    X = np.asarray(X, np.float32)
    y = np.asarray(y, bool)
    q = np.asarray(quad)
    keep = np.ones(len(y), bool)
    if exclude_quad is not None:
        keep &= q != exclude_quad
    Xk = X[keep]
    yk = y[keep]
    pos = np.flatnonzero(yk)
    rng = np.random.default_rng(neg_seed)
    neg = rng.choice(np.flatnonzero(~yk), int(n_negatives), replace=False)
    idx = np.concatenate([pos, neg])
    return Xk[idx], yk[idx], dict(
        positives=int(pos.size), negatives=int(neg.size),
        excluded_quad=None if exclude_quad is None else int(exclude_quad))


def training_rows(stack_cells, geom_cells, labels_cells, quad_cells, **kwargs):
    """Convenience wrapper: build the feature matrix, then :func:`select_rows`."""
    X = np.concatenate([np.asarray(stack_cells, np.float32),
                        np.asarray(geom_cells, np.float32)], axis=1)
    return select_rows(X, labels_cells, quad_cells, **kwargs)


def predict_cells(model, stack_cells, geom_cells, chunk=400_000):
    """Model probability at the given cells, computed in memory-bounded chunks."""
    n = len(stack_cells)
    out = np.empty(n, np.float32)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        X = np.concatenate([np.asarray(stack_cells[s:e], np.float32),
                            np.asarray(geom_cells[s:e], np.float32)], axis=1)
        out[s:e] = model.predict_proba(X)[:, 1].astype(np.float32)
    return out


def scatter(cells_flat, values, shape):
    """Full-grid float32 surface, zero everywhere except ``cells_flat``."""
    out = np.zeros(shape, np.float32)
    out.ravel()[cells_flat] = values
    return out


def stratified_dots(score, n=DOT_COUNT, block=BLOCK, nms=NMS, return_topup=False):
    """One dot per block (argmax), keep the best ``n`` blocks, then NMS.

    Pass 1 is verbatim Phase-4 (scripts/run_experiment_v4.py::stratified_dots):
    when it reaches ``n`` dots the output is identical to Phase-4. Only when a
    spiky surface leaves pass 1 short of the registered fixed mass does a
    second pass place one dot at the best NMS-feasible cell of the
    highest-scoring strata that remain empty (Phase-5 implementation
    amendment, docs/hypotheses.md, fixed before any score was seen).

    With ``return_topup=True`` returns ``(dots, picked, topup)`` where
    ``topup`` counts the dots placed by the second pass.
    """
    h, w = score.shape
    H = int(np.ceil(h / block) * block)
    W = int(np.ceil(w / block) * block)
    pad = np.zeros((H, W), np.float32)
    pad[:h, :w] = score
    nb_y, nb_x = H // block, W // block
    blocks = pad.reshape(nb_y, block, nb_x, block).transpose(0, 2, 1, 3).reshape(nb_y * nb_x, -1)
    best = blocks.argmax(axis=1)
    best_score = blocks.max(axis=1)
    keep = np.flatnonzero(best_score > 0)
    order = keep[np.argsort(best_score[keep], kind='stable')[::-1]]
    by, bx = np.divmod(order, nb_x)
    py, px = np.divmod(best[order], block)
    ys, xs = by * block + py, bx * block + px
    dots = np.zeros((h, w), bool)
    r = int(np.ceil(nms))
    picked = 0
    used = np.zeros(nb_y * nb_x, bool)
    for bi, y, x in zip(order, ys, xs):
        if picked >= n:
            break
        if y >= h or x >= w or dots[y, x]:
            continue
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        if dots[y0:y1, x0:x1].any():
            continue
        dots[y, x] = True
        used[bi] = True
        picked += 1
    if picked >= n:
        return (dots, picked, 0) if return_topup else (dots, picked)
    # Pass 2 (registered amendment): top up to the fixed mass from the best
    # NMS-feasible POSITIVE-SCORE cell of still-empty strata, highest stratum
    # score first. Positive cells are exactly the allowed-domain cells, so no
    # dot can land on the catalogue or outside the footprint.
    within = np.argsort(-blocks, axis=1, kind='stable')
    topup = 0
    for bi in order:
        if picked >= n:
            break
        if used[bi]:
            continue
        bby, bbx = divmod(int(bi), nb_x)
        for cell in within[bi]:
            if blocks[bi, cell] <= 0:
                break  # sorted desc: every later cell is also non-positive
            cy, cx = divmod(int(cell), block)
            y, x = bby * block + cy, bbx * block + cx
            if y >= h or x >= w:
                continue
            y0, y1 = max(0, y - r), min(h, y + r + 1)
            x0, x1 = max(0, x - r), min(w, x + r + 1)
            if dots[y0:y1, x0:x1].any():
                continue
            dots[y, x] = True
            used[bi] = True
            picked += 1
            topup += 1
            break
    return (dots, picked, topup) if return_topup else (dots, picked)


def auc(labels, values):
    """Plain AUC with the registered orientation; NaN only for a degenerate set."""
    y = np.asarray(labels, bool)
    v = np.asarray(values, np.float32)
    ok = np.isfinite(v)
    y, v = y[ok], v[ok]
    if y.size == 0 or y.all() or (~y).any() is False or (not y.any()):
        return float('nan')
    if len(np.unique(v)) < 2:
        return float('nan')
    return float(roc_auc_score(y, v))


def canary(auc_value):
    """Registered canary record; AUC > 0.90 is suspected leakage (rule 4)."""
    a = float(auc_value)
    finite = np.isfinite(a)
    return dict(evidence_class='LEAKAGE-CANARY', auc=None if not finite else a,
                suspected_leakage=bool(finite and a > CANARY_STOP),
                stop_rule=f'auc > {CANARY_STOP} against instrument-A withheld truth')
