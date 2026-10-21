"""Phase-5 Leave-One-Quadrant-Out (LOQO) supervised within-halo structural ranker.

Registered in ``docs/preregistration-phase5.md`` and ``docs/hypotheses.md`` before execution.

Key properties:
1. Physical features (19-band GeoDAWN/INGENIOUS stack, 12-band LiDAR scarp stack,
   8-band GeoDAWN radiometrics + ratios, and 2 DOE GDR 1391 hydrothermal conduit
   distance features) are completely independent of the fault catalogue.
2. Catalogue geometry features (8 features: distance, log-distance, host component
   log-length, along-strike cosine, signed cross-strike sine, tip u, tip |v|, and
   tip continuation kernel) are computed strictly from ``catalogue_visible``.
3. Leave-One-Quadrant-Out (LOQO) training fits ``HistGradientBoostingClassifier``
   for each quadrant k in {0, 1, 2, 3} strictly on the other three 12-px-eroded
   quadrants {j != k}, ensuring >= 2.4 km (24 px = 8x kernel radius) separation
   between any training pixel and any scored evaluation pixel in quadrant k.
4. Predictions in each test quadrant are rank-normalized to [0, 1] within that
   quadrant to remove inter-quadrant baseline shifts before global 7x7 block-stratum
   argmax selection and 5.0-px Euclidean NMS (37,654 binary dots).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier

from gems70 import method_v2 as m2

DOT_COUNT = 37654
BLOCK_PX = 7
NMS_PX = 5.0
D_MIN_PX = 3.0
TILT_AMPLITUDE = 0.5
TILT_SCALE_PX = 10.0
TIP_FLOOR = 0.75
TIP_WEIGHT = 0.25
TIP_ALONG_PX = 25.0
TIP_ACROSS_PX = 8.0
LOQO_FLOOR = 0.35
LOQO_WEIGHT = 0.65
HYDRO_SCALE_PX = 15.0


def rank01_vec(values: np.ndarray) -> np.ndarray:
    """Average-tie percentile rank in [0, 1] for a 1-D finite vector."""
    v = np.asarray(values, np.float32)
    n = int(v.size)
    if n <= 1:
        return np.zeros(n, np.float32)
    if float(np.ptp(v)) == 0.0:
        return np.zeros(n, np.float32)
    return ((rankdata(v, method='average') - 1.0) / (n - 1)).astype(np.float32)


def hydrothermal_features(conduit_mask: np.ndarray, valid_idx: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Compute catalogue-independent distance and kernel to verified hydrothermal conduits."""
    mask = np.asarray(conduit_mask, bool)
    if not mask.any():
        n = int(valid_idx.size)
        z = np.zeros((n, 2), np.float32)
        g = np.zeros(mask.shape, np.float32)
        return z, {'hydro_neg_log_dist': g, 'hydro_kernel': g}
    d = ndi.distance_transform_edt(~mask).astype(np.float32)
    log_d = np.log1p(d).astype(np.float32)
    kern = np.exp(-d / HYDRO_SCALE_PX).astype(np.float32)
    dv = d.ravel()[valid_idx]
    mat = np.column_stack([np.log1p(dv), np.exp(-dv / HYDRO_SCALE_PX)]).astype(np.float32)
    return mat, {'hydro_neg_log_dist': -log_d, 'hydro_kernel': kern}


def catalogue_geometry_features(catalogue_visible: np.ndarray,
                                valid_idx: np.ndarray,
                                out_mat: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute 8 geometric features strictly from ``catalogue_visible``.

    Returns ``(G_valid, d_grid, tip_grid)`` where ``G_valid`` has shape
    ``(len(valid_idx), 8)``. If ``out_mat`` is supplied, writes in-place.
    """
    cat_vis = np.asarray(catalogue_visible, bool)
    h, w = cat_vis.shape
    G = out_mat if out_mat is not None else np.empty((int(valid_idx.size), 8), np.float32)
    if not cat_vis.any():
        G[:] = 0.0
        inf = np.full((h, w), np.inf, np.float32)
        zero = np.zeros((h, w), np.float32)
        return G, inf, zero

    lab, n_comp = ndi.label(cat_vis, m2.STRUCT8)
    sizes = np.bincount(lab.ravel(), minlength=n_comp + 1).astype(np.float32)
    ys, xs = np.nonzero(cat_vis)
    ids = lab[ys, xs]
    cnt = np.maximum(sizes, 1.0)
    cy = np.bincount(ids, weights=ys, minlength=n_comp + 1) / cnt
    cx = np.bincount(ids, weights=xs, minlength=n_comp + 1) / cnt
    dy = ys - cy[ids]
    dx = xs - cx[ids]
    sxx = np.bincount(ids, weights=dx * dx, minlength=n_comp + 1)
    syy = np.bincount(ids, weights=dy * dy, minlength=n_comp + 1)
    sxy = np.bincount(ids, weights=dx * dy, minlength=n_comp + 1)
    theta = 0.5 * np.arctan2(2.0 * sxy, sxx - syy)
    cos_t = np.cos(theta).astype(np.float32)
    sin_t = np.sin(theta).astype(np.float32)
    del ys, xs, ids, cnt, cy, cx, dy, dx, sxx, syy, sxy, theta

    d, (iy, ix) = ndi.distance_transform_edt(~cat_vis, return_distances=True, return_indices=True)
    d = d.astype(np.float32)
    dv = d.ravel()[valid_idx]
    G[:, 0] = dv
    G[:, 1] = np.log1p(dv)

    vy_r, vx_r = np.divmod(valid_idx, w)
    iy_v = iy.ravel()[valid_idx]
    ix_v = ix.ravel()[valid_idx]
    comp_v = lab.ravel()[iy_v * w + ix_v]
    del iy, ix, lab
    denom = np.maximum(dv, 1.0)
    dy_v = (vy_r.astype(np.float32) - iy_v.astype(np.float32)) / denom
    dx_v = (vx_r.astype(np.float32) - ix_v.astype(np.float32)) / denom
    del vy_r, vx_r, iy_v, ix_v, denom

    G[:, 2] = np.log1p(sizes[comp_v])
    G[:, 3] = np.abs(dx_v * cos_t[comp_v] + dy_v * sin_t[comp_v])
    G[:, 4] = dx_v * (-sin_t[comp_v]) + dy_v * cos_t[comp_v]
    del comp_v, dx_v, dy_v, cos_t, sin_t, sizes

    u, v = m2.tip_kernels(cat_vis, cat_vis.shape)
    tip_k = (np.exp(-np.clip(u, 0.0, None) / TIP_ALONG_PX) *
             np.exp(-np.abs(v) / TIP_ACROSS_PX)).astype(np.float32)
    tip_k = np.where(np.isfinite(tip_k), tip_k, 0.0).astype(np.float32)
    uv = u.ravel()[valid_idx]
    vv = v.ravel()[valid_idx]
    del u, v
    G[:, 5] = np.clip(np.where(np.isfinite(uv), uv, 200.0), -50.0, 200.0)
    G[:, 6] = np.clip(np.where(np.isfinite(vv), np.abs(vv), 200.0), 0.0, 200.0)
    G[:, 7] = tip_k.ravel()[valid_idx]
    del uv, vv
    return G, d, tip_k


def fit_predict_loqo(X_valid: np.ndarray,
                     y_proxy_valid: np.ndarray,
                     eligible_valid: np.ndarray,
                     quad_valid: np.ndarray,
                     eroded_quad_valid: np.ndarray,
                     grid_shape: tuple[int, int],
                     valid_idx: np.ndarray,
                     *,
                     col_indices: list[int] | np.ndarray | None = None,
                     seed: int = 70500,
                     neg_pos_ratio: int = 3) -> tuple[np.ndarray, list[dict]]:
    """Train 4 Leave-One-Quadrant-Out HGB models and return full-grid quadrant-rank surface."""
    n_val = int(valid_idx.size)
    oof_rank = np.zeros(n_val, np.float32)
    fold_Diagnostics = []
    rng = np.random.default_rng(seed)

    for k in range(4):
        tr_mask = (eroded_quad_valid >= 0) & (eroded_quad_valid != k) & eligible_valid
        pos_idx = np.flatnonzero(tr_mask & y_proxy_valid)
        neg_pool = np.flatnonzero(tr_mask & ~y_proxy_valid)
        if pos_idx.size == 0 or neg_pool.size == 0:
            raise ValueError(f'Empty training class in LOQO fold {k}')
        n_neg = min(int(neg_pool.size), int(pos_idx.size) * int(neg_pos_ratio))
        neg_idx = rng.choice(neg_pool, n_neg, replace=False)
        tr_idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([np.ones(pos_idx.size, np.int32),
                               np.zeros(neg_idx.size, np.int32)])

        clf = HistGradientBoostingClassifier(
            max_iter=80,
            max_leaf_nodes=31,
            min_samples_leaf=100,
            l2_regularization=10.0,
            random_state=seed + k,
        )
        X_tr = X_valid[tr_idx] if col_indices is None else X_valid[tr_idx][:, col_indices]
        clf.fit(X_tr, y_tr)
        del X_tr
        te_mask = (quad_valid == k)
        X_te = X_valid[te_mask] if col_indices is None else X_valid[te_mask][:, col_indices]
        pr = clf.predict_proba(X_te)[:, 1].astype(np.float32)
        del X_te
        oof_rank[te_mask] = rank01_vec(pr)
        fold_Diagnostics.append({
            'quadrant': int(k),
            'n_train_pos': int(pos_idx.size),
            'n_train_neg': int(neg_idx.size),
            'n_test_valid': int(te_mask.sum()),
            'test_prob_mean': float(pr.mean()),
            'test_prob_std': float(pr.std()),
        })

    rank_grid = np.zeros(grid_shape, np.float32)
    rank_grid.ravel()[valid_idx] = oof_rank
    return rank_grid, fold_Diagnostics


def combine_loqo_halo(rank_grid: np.ndarray,
                      d_grid: np.ndarray,
                      tip_grid: np.ndarray,
                      catalogue_visible: np.ndarray,
                      valid: np.ndarray,
                      *,
                      use_loqo: bool = True,
                      use_halo: bool = True,
                      d_min_px: float = D_MIN_PX) -> np.ndarray:
    """Combine out-of-fold LOQO rank surface and continuation halo envelope."""
    cat_vis = np.asarray(catalogue_visible, bool)
    allowed = np.asarray(valid, bool) & ~cat_vis & (d_grid >= d_min_px)
    score = np.ones(cat_vis.shape, np.float32)
    if use_loqo:
        score = score * (LOQO_FLOOR + LOQO_WEIGHT * np.clip(rank_grid, 0.0, 1.0))
    if use_halo:
        halo = (1.0 + TILT_AMPLITUDE * np.exp(-(d_grid - d_min_px) / TILT_SCALE_PX))
        tip = TIP_FLOOR + TIP_WEIGHT * np.clip(tip_grid, 0.0, 1.0)
        score = score * halo.astype(np.float32) * tip.astype(np.float32)
    score = np.where(allowed, score, 0.0).astype(np.float32)
    if not np.isfinite(score).all():
        raise ValueError('Non-finite score in combine_loqo_halo')
    return score


def stratified_dots(score: np.ndarray,
                    n: int = DOT_COUNT,
                    block: int = BLOCK_PX,
                    nms: float = NMS_PX) -> tuple[np.ndarray, int]:
    """One dot per block (argmax), keep the best ``n`` blocks, then Euclidean NMS."""
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
