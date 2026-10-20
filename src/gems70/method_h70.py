"""H70-A conductive breach at magnetic discordance — catalogue-independent ranking.

Implements the pre-registered H70-A hypothesis without reading any fault catalogue.
Catalogue geometry (distance, tip) is supplied by the caller as visible-only.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

STRUCT8 = np.ones((3, 3), bool)


def rank01(values, valid):
    a = np.asarray(values)
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


def _grad_amp(arr, sigma_smooth=1.0, sigma_amp=2.0):
    s = ndi.gaussian_filter(arr, sigma_smooth)
    gy, gx = np.gradient(s)
    return ndi.gaussian_filter(np.hypot(gy, gx), sigma_amp)


def conductive_breach_features(rtp, tmi_hg, tmi_vg, tmi, cond_surf, valid):
    """All catalogue-independent. Returns dict of fields."""
    r, hg, vg, t, c = [fill_nearest(np.where(valid, a, np.nan))
                       for a in (rtp, tmi_hg, tmi_vg, tmi, cond_surf)]
    # conductivity gradient magnitude
    cond_grad = _grad_amp(c, sigma_smooth=1.0, sigma_amp=2.0)
    # RTP horizontal gradient magnitude
    rtp_grad = _grad_amp(r, sigma_smooth=1.0, sigma_amp=2.0)
    # analytic signal: sqrt(hg^2 + vg^2 + rtp_grad^2) — total gradient including vertical
    analytic = np.sqrt(hg.astype(np.float64)**2 + vg.astype(np.float64)**2 + rtp_grad.astype(np.float64)**2).astype(np.float32)
    # breach raw = product of two edge magnitudes (both >=0)
    breach_raw = (cond_grad.astype(np.float64) * analytic.astype(np.float64)).astype(np.float32)
    # also keep components for canary
    return {
        'cond_grad': np.where(valid, cond_grad, 0).astype(np.float32),
        'rtp_grad': np.where(valid, rtp_grad, 0).astype(np.float32),
        'analytic': np.where(valid, analytic, 0).astype(np.float32),
        'breach_raw': np.where(valid, breach_raw, 0).astype(np.float32),
        'cond_surf': np.where(valid, c, 0).astype(np.float32),
        'rtp': np.where(valid, r, 0).astype(np.float32),
        'tmi_hg': np.where(valid, hg, 0).astype(np.float32),
        'tmi_vg': np.where(valid, vg, 0).astype(np.float32),
        'tmi': np.where(valid, t, 0).astype(np.float32),
    }


def breach_rank(breach_raw, valid):
    """Rank normalized breach product in [0,1]; zero outside valid."""
    return rank01(breach_raw, valid)


# Reuse tip logic from method_v2 (with same constants for comparability)
OFFSET_PEAK_PX = 16.0
OFFSET_SIGMA_PX = 9.0
MIN_OFFSET_PX = 2.4  # updated to match P4's 2.4, not 4.0, for H33 parity
TIP_SIGMA_ALONG_PX = 25.0
TIP_SIGMA_ACROSS_PX = 8.0

# P4 halo constants
DOT_COUNT = 37654
BLOCK_PX = 7
NMS_PX = 5.0
D_MIN_PX = 2.4
D_MAX_PX = 32.0
BREACH_AMPLITUDE = 0.6  # 1 + 0.6*rank
TIP_FLOOR = 0.7
TIP_WEIGHT = 0.3


def component_tips(catalogue):
    cat = np.asarray(catalogue, bool)
    lab, n = ndi.label(cat, STRUCT8)
    if n == 0:
        return (np.zeros(0, np.int64),) * 4
    ys, xs = np.nonzero(cat)
    ids = lab[ys, xs]
    count = np.bincount(ids, minlength=n + 1).astype(np.float64)
    cy = np.bincount(ids, weights=ys, minlength=n + 1) / np.maximum(count, 1)
    cx = np.bincount(ids, weights=xs, minlength=n + 1) / np.maximum(count, 1)
    dy = ys - cy[ids]
    dx = xs - cx[ids]
    sxx = np.bincount(ids, weights=dx * dx, minlength=n + 1)
    syy = np.bincount(ids, weights=dy * dy, minlength=n + 1)
    sxy = np.bincount(ids, weights=dx * dy, minlength=n + 1)
    theta = 0.5 * np.arctan2(2.0 * sxy, sxx - syy)
    cos_t = np.cos(theta)[ids]
    sin_t = np.sin(theta)[ids]
    proj = dx * cos_t + dy * sin_t
    pmin = np.full(n + 1, np.inf)
    pmax = np.full(n + 1, -np.inf)
    np.minimum.at(pmin, ids, proj)
    np.maximum.at(pmax, ids, proj)
    at_min = proj <= pmin[ids] + 1e-9
    at_max = proj >= pmax[ids] - 1e-9
    tip_y, tip_x, out_dy, out_dx = [], [], [], []
    for mask, sign in ((at_min, -1.0), (at_max, 1.0)):
        yy, xx = ys[mask], xs[mask]
        comp = ids[mask]
        _, first = np.unique(comp, return_index=True)
        yy, xx, comp = yy[first], xx[first], comp[first]
        tip_y.append(yy)
        tip_x.append(xx)
        out_dy.append(sign * np.sin(theta)[comp])
        out_dx.append(sign * np.cos(theta)[comp])
    return (np.concatenate(tip_y).astype(np.int64), np.concatenate(tip_x).astype(np.int64),
            np.concatenate(out_dy), np.concatenate(out_dx))


def tip_kernels(catalogue, shape):
    ty, tx, ody, odx = component_tips(catalogue)
    if ty.size == 0:
        inf = np.full(shape, np.inf, np.float32)
        return inf, inf
    tip_mask = np.zeros(shape, bool)
    tip_id = np.full(shape, -1, np.int64)
    tip_id[ty, tx] = np.arange(ty.size)
    tip_mask[ty, tx] = True
    _, (iy, ix) = ndi.distance_transform_edt(~tip_mask, return_distances=True, return_indices=True)
    k = tip_id[iy, ix]
    del iy, ix
    y = np.arange(shape[0], dtype=np.float32)[:, None]
    x = np.arange(shape[1], dtype=np.float32)[None, :]
    u = (y - ty[k].astype(np.float32)) * ody[k].astype(np.float32) + \
        (x - tx[k].astype(np.float32)) * odx[k].astype(np.float32)
    v = -(y - ty[k].astype(np.float32)) * odx[k].astype(np.float32) + \
        (x - tx[k].astype(np.float32)) * ody[k].astype(np.float32)
    return u.astype(np.float32), v.astype(np.float32)


def halo_intensity(catalogue_visible, breach_rank_arr, valid, *,
                   d_min_px=D_MIN_PX, d_max_px=D_MAX_PX,
                   breach_amplitude=BREACH_AMPLITUDE,
                   tip_floor=TIP_FLOOR, tip_weight=TIP_WEIGHT,
                   offset_peak=OFFSET_PEAK_PX, offset_sigma=OFFSET_SIGMA_PX,
                   tip_along=TIP_SIGMA_ALONG_PX, tip_across=TIP_SIGMA_ACROSS_PX):
    """Compute intensity for visible catalogue. All arrays in pixel units."""
    cat = np.asarray(catalogue_visible, bool)
    allowed = np.asarray(valid, bool) & ~cat
    d = ndi.distance_transform_edt(~cat).astype(np.float32)
    # Gaussian distance prior peaked at 16 px, narrow band 2.4-32 px
    off = np.exp(-(((d - offset_peak) / offset_sigma) ** 2)).astype(np.float32)
    off[d < d_min_px] = 0.0
    off[d > d_max_px] = 0.0
    # tip kernel
    u, v = tip_kernels(cat, cat.shape)
    beyond = np.clip(u, 0.0, None)
    tip = np.exp(-beyond / tip_along) * np.exp(-np.abs(v) / tip_across)
    tip = np.where(np.isfinite(tip), tip, 0.0).astype(np.float32)
    del u, v, beyond, d
    tip_factor = tip_floor + tip_weight * tip
    breach_factor = 1.0 + breach_amplitude * np.clip(np.asarray(breach_rank_arr, np.float32), 0.0, 1.0)
    score = off * tip_factor * breach_factor
    score = np.where(allowed, score, 0.0).astype(np.float32)
    if not np.isfinite(score).all():
        raise ValueError('non-finite halo intensity')
    return score, {'off': off, 'tip': tip, 'tip_factor': tip_factor, 'breach_factor': breach_factor, 'allowed': allowed}


def stratified_dots(score, n=DOT_COUNT, block=BLOCK_PX, nms=NMS_PX):
    """One dot per block (argmax), keep the best `n` blocks, then NMS — identical to P4."""
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


def dots_to_field(dots):
    return np.asarray(dots, np.float32)
