"""Phase-5 structural forecasting: leave-one-quadrant-out supervised and unsupervised
within-halo breakline/scarp/radiometric ranking with submodular dual-horizon allocation.

Registered in ``docs/hypotheses.md`` (Phase-5 preregistration addendum) before this run.
Executes Handoff Priority #1 (within-halo physical ranking with leave-one-quadrant-out CV)
and Priority #2 (SGMC vs QFaults buffer calibration 1-6 px).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from sklearn.linear_model import LogisticRegression

from gems70 import method_v2 as m2

STRUCT8 = np.ones((3, 3), bool)

DOT_COUNT = 37654
D_MIN_PX = 2.4
D_MAX_HALO_PX = 80.0
TILT_AMPLITUDE = 0.8
TILT_SCALE_PX = 6.0
TIP_FLOOR = 0.7
TIP_WEIGHT = 0.3
TIP_ALONG_PX = 25.0
TIP_ACROSS_PX = 8.0

# Exp 5.1 / 5.2 (7x7 single-dot strata, 5.0 px NMS) vs Exp 5.3 (5x5 strata, 3.2 px NMS)
BLOCK_7 = 7
NMS_5 = 5.0
BLOCK_5 = 5
NMS_3P2 = 3.2


def _grad_mag(arr, valid, sigma=1.0):
    filled = m2.fill_nearest(np.where(valid, arr, np.nan))
    s = ndi.gaussian_filter(filled.astype(np.float32), sigma)
    gy, gx = np.gradient(s)
    return np.hypot(gy, gx).astype(np.float32)


def physical_feature_ranks(
    det_slope,
    depth_base,
    iso_grav,
    geod_2nd,
    geod_shr,
    tmi_hg,
    lidar_bands,
    topo10_bands,
    rad_bands,
    ext_bands,
    valid,
):
    """Compute catalogue-independent percentile-ranked physical features in [0, 1].

    Parameters
    ----------
    det_slope, depth_base, iso_grav, geod_2nd, geod_shr, tmi_hg : 2D ndarray
        Bands 19, 15, 13, 4, 7, 3 from training_features.tif.
    lidar_bands : sequence of 2D ndarray
        1 m LiDAR scarp bands (step_max, downface_max, upface_max, cross_max).
    topo10_bands : sequence of 2D ndarray
        10 m 3DEP breakline bands (slope_p90, slope_std, relief_local, curv_prof_absmax, hs_lineament).
    rad_bands : sequence of 2D ndarray
        GeoDAWN radiometric bands (K, Th, U, TC) from geodawn_rad_u8.tif.
    ext_bands : sequence of 2D ndarray
        GeoDAWN extension bands (ThK, UK, TMI_up150) from geodawn_extensions_u8.tif.
    valid : 2D bool ndarray
        Valid footprint domain.
    """
    valid = np.asarray(valid, bool)
    r_slope = m2.rank01(det_slope, valid)
    r_shallow = m2.rank01(-np.asarray(depth_base, np.float32), valid)
    r_grav = m2.rank01(iso_grav, valid)
    r_strain = (0.5 * (m2.rank01(geod_2nd, valid) + m2.rank01(geod_shr, valid))).astype(np.float32)
    r_tmi_hg = m2.rank01(tmi_hg, valid)

    r_lidar = np.zeros(valid.shape, np.float32)
    for b in lidar_bands:
        r_lidar += m2.rank01(b, valid)
    r_lidar /= max(len(lidar_bands), 1)

    r_topo10 = np.zeros(valid.shape, np.float32)
    for b in topo10_bands:
        r_topo10 += m2.rank01(b, valid)
    r_topo10 /= max(len(topo10_bands), 1)

    # Radiometric alteration: combine Th/K, U/K, upward-continued TMI and spatial gradients of K, Th
    r_rad_acc = np.zeros(valid.shape, np.float32)
    n_rad = 0
    for b in ext_bands:
        r_rad_acc += m2.rank01(b, valid)
        n_rad += 1
    for b in rad_bands[:2]:
        r_rad_acc += m2.rank01(_grad_mag(b, valid, sigma=1.5), valid)
        n_rad += 1
    r_rad = (r_rad_acc / max(n_rad, 1)).astype(np.float32)

    features = {
        'det_elev_slope': r_slope,
        'topo10_breakline': r_topo10,
        'lidar_scarp': r_lidar,
        'shallow_basement': r_shallow,
        'iso_grav_anom': r_grav,
        'geod_strain': r_strain,
        'rad_alteration': r_rad,
        'tmi_hg': r_tmi_hg,
    }
    feature_names = list(features.keys())
    matrix = np.stack([features[k] for k in feature_names], axis=-1).astype(np.float32)
    return features, feature_names, matrix


def catalogue_geometry(
    catalogue_visible,
    valid,
    *,
    d_min=D_MIN_PX,
    d_max=D_MAX_HALO_PX,
    tilt_amp=TILT_AMPLITUDE,
    tilt_scale=TILT_SCALE_PX,
    tip_floor=TIP_FLOOR,
    tip_weight=TIP_WEIGHT,
):
    """Derive distance, host fault length, across-strike side, tip kernel and halo envelope
    strictly from ``catalogue_visible`` (never from withheld truth).
    """
    cat = np.asarray(catalogue_visible, bool)
    allowed = np.asarray(valid, bool) & ~cat
    if not cat.any():
        zeros = np.zeros(cat.shape, np.float32)
        return {
            'd_cat': np.full(cat.shape, np.inf, np.float32),
            'host_len': zeros,
            'side': zeros,
            'tip': zeros,
            'envelope': zeros,
            'allowed_halo': np.zeros(cat.shape, bool),
            'allowed_full': allowed,
        }
    lab, _ = ndi.label(cat, STRUCT8)
    sizes = np.bincount(lab.ravel()).astype(np.float32)
    sizes[0] = 0.0
    d_cat, (ny, nx) = ndi.distance_transform_edt(~cat, return_distances=True, return_indices=True)
    d_cat = d_cat.astype(np.float32)
    host_len = np.log1p(sizes[lab[ny, nx]]).astype(np.float32)
    del ny, nx, lab
    host_rank = m2.rank01(host_len, allowed)

    u, v = m2.tip_kernels(cat, cat.shape)
    tip = np.exp(-np.clip(u, 0.0, None) / TIP_ALONG_PX) * np.exp(-np.abs(v) / TIP_ACROSS_PX)
    tip = np.where(np.isfinite(tip), tip, 0.0).astype(np.float32)
    side = np.where(np.isfinite(v), np.tanh(v / 10.0), 0.0).astype(np.float32)
    del u, v

    band_halo = allowed & (d_cat >= d_min) & (d_cat <= d_max)
    band_full = allowed & (d_cat >= d_min)
    w = (1.0 + tilt_amp * np.exp(-(d_cat - d_min) / tilt_scale)).astype(np.float32)
    w = w * (tip_floor + tip_weight * tip) * (0.9 + 0.1 * host_rank)
    env = np.where(band_halo, w, 0.0).astype(np.float32)
    if not np.isfinite(env).all():
        raise ValueError('non-finite catalogue envelope')
    return {
        'd_cat': d_cat,
        'host_len': host_len,
        'side': side,
        'tip': tip,
        'envelope': env,
        'allowed_halo': band_halo,
        'allowed_full': band_full,
    }


def fit_loqo_ranker(
    X_phys,
    proxy_prime,
    quad,
    valid,
    cat,
    d_cat,
    *,
    seed=70500,
    c_reg=1.0,
    neg_ratio=4,
    feature_names=None,
):
    """Fit 4 leave-one-quadrant-out L2 logistic models on ``d_cat >= 3.0`` off-catalogue pixels.

    Each quadrant ``k`` receives predictions strictly from the model fitted on ``quad != k``.
    """
    h, w, n_feat = X_phys.shape
    flat_X = X_phys.reshape(-1, n_feat)
    p_oof = np.zeros((h, w), np.float32)
    rng = np.random.default_rng(seed)
    fold_models = []
    for k in range(4):
        tr_mask = (quad != k) & valid & ~cat & (d_cat >= 3.0)
        pos_idx = np.flatnonzero(tr_mask & proxy_prime)
        neg_pool = np.flatnonzero(tr_mask & ~proxy_prime)
        if pos_idx.size == 0 or neg_pool.size == 0:
            raise ValueError(f'empty training class in quadrant {k}')
        n_neg = min(int(pos_idx.size * neg_ratio), int(neg_pool.size))
        neg_idx = rng.choice(neg_pool, n_neg, replace=False)
        idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([np.ones(pos_idx.size, np.float64), np.zeros(n_neg, np.float64)])
        clf = LogisticRegression(C=float(c_reg), max_iter=200, solver='lbfgs')
        clf.fit(flat_X[idx], y_tr)
        te_mask = (quad == k) & valid
        te_idx = np.flatnonzero(te_mask)
        p_oof.ravel()[te_idx] = clf.predict_proba(flat_X[te_idx])[:, 1].astype(np.float32)
        coefs = {
            (feature_names[i] if feature_names else f'f{i}'): float(clf.coef_[0][i])
            for i in range(n_feat)
        }
        fold_models.append({
            'held_out_quadrant': int(k),
            'n_train_pos': int(pos_idx.size),
            'n_train_neg': int(n_neg),
            'intercept': float(clf.intercept_[0]),
            'coefficients': coefs,
        })
    p_oof_rank = m2.rank01(p_oof, valid)
    return p_oof_rank, p_oof, fold_models


def unsupervised_breakline_rank(features, valid):
    """Label-free concordance rank of 10 m 3DEP breaklines, detrended slope, 1 m LiDAR scarp, and radiometrics."""
    raw = (
        0.45 * features['topo10_breakline']
        + 0.25 * features['det_elev_slope']
        + 0.20 * features['lidar_scarp']
        + 0.10 * features['rad_alteration']
    )
    return m2.rank01(raw, valid)


def exp5_1_surface(envelope, p_oof_rank):
    """H-P5-1: supervised within-stratum ranker modulating the extended halo envelope."""
    s = np.asarray(envelope, np.float32) * (0.30 + 0.70 * np.asarray(p_oof_rank, np.float32))
    return np.where(np.isfinite(s) & (s > 0), s, 0.0).astype(np.float32)


def exp5_2_surface(envelope, breakline_rank):
    """H-P5-2: unsupervised breakline concordance modulating the extended halo envelope."""
    s = np.asarray(envelope, np.float32) * (0.30 + 0.70 * np.asarray(breakline_rank, np.float32))
    return np.where(np.isfinite(s) & (s > 0), s, 0.0).astype(np.float32)


def exp5_3_surface(envelope, p_oof_rank, allowed_full):
    """H-P5-3: submodular dual-horizon surface combining near-field tip/damage halo and far-field ranker."""
    s = 0.35 * np.asarray(envelope, np.float32) + 0.65 * np.asarray(p_oof_rank, np.float32)
    s = np.where(np.asarray(allowed_full, bool) & np.isfinite(s) & (s > 0), s, 0.0).astype(np.float32)
    return s


def stratified_dots(score, n=DOT_COUNT, block=BLOCK_5, nms=NMS_3P2):
    """One dot per block (argmax), keep the best ``n`` non-colliding blocks under Euclidean NMS."""
    score = np.asarray(score, np.float32)
    h, w = score.shape
    H = int(np.ceil(h / block) * block)
    W = int(np.ceil(w / block) * block)
    pad = np.zeros((H, W), np.float32)
    pad[:h, :w] = np.where(np.isfinite(score) & (score > 0), score, 0.0)
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
    blocked = np.zeros((h, w), bool)
    picked = 0
    n = int(n)
    for y, x in zip(ys, xs):
        if y >= h or x >= w or blocked[y, x]:
            continue
        dots[y, x] = True
        picked += 1
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        blocked[y0:y1, x0:x1] |= disk[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)]
        if picked >= n:
            break
    return dots, picked
