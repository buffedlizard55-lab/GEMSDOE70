"""Phase-2 structural forecasting: geophysically gated continuation / strand prior.

Registered in ``docs/hypotheses.md`` (Phase-2 addendum) before this run.

No fault catalogue is read by :func:`geophysical_ranks`; catalogue geometry enters
only through :func:`structural_score`, whose ``catalogue_visible`` argument is the
*visible* catalogue of the current holdout fold (never the withheld truth).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

STRUCT8 = np.ones((3, 3), bool)

# Registered constants (docs/hypotheses.md, Phase-2 addendum).
OFFSET_PEAK_PX = 16.0
OFFSET_SIGMA_PX = 9.0
MIN_OFFSET_PX = 4.0
TIP_SIGMA_ALONG_PX = 25.0
TIP_SIGMA_ACROSS_PX = 8.0
DOT_COUNT = 37654
NMS_RADIUS_PX = 2.0


def rank01(values, valid):
    """Average-tie percentile rank in [0, 1]; zero outside ``valid``."""
    a = np.asarray(values)
    valid = np.asarray(valid, bool) & np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    n = int(valid.sum())
    if n > 1:
        out[valid] = ((rankdata(a[valid], method='average') - 1) / (n - 1)).astype(np.float32)
    return out


def fill_nearest(a):
    """Fill non-finite cells with the nearest finite value (no extrapolation)."""
    good = np.isfinite(a)
    if not good.any():
        raise ValueError('empty finite feature')
    idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def _amp(a, sigma_smooth=1.0, sigma_amp=2.0):
    s = ndi.gaussian_filter(a, sigma_smooth)
    gy, gx = np.gradient(s)
    return ndi.gaussian_filter(np.hypot(gy, gx), sigma_amp)


def geophysical_fields(dilaterate, second_invariant, gravity, tilt, relief, valid):
    """Four catalogue-independent geophysical fields (registered set)."""
    dil, inv, grav, tc, rel = [fill_nearest(np.where(valid, a, np.nan))
                               for a in (dilaterate, second_invariant, gravity, tilt, relief)]
    strain = 0.5 * (_amp(dil) + _amp(inv))
    grav_edge = _amp(grav, 3.0, 1.0)
    mag_edge = np.abs(tc)
    relief_edge = np.abs(rel)
    return {'strain': strain.astype(np.float32),
            'gravity_edge': grav_edge.astype(np.float32),
            'magnetic_tilt': mag_edge.astype(np.float32),
            'relief': relief_edge.astype(np.float32)}


def geophysical_ranks(fields, domain):
    """Equal-weight mean of the four field ranks (registered weights)."""
    acc = np.zeros(next(iter(fields.values())).shape, np.float32)
    for a in fields.values():
        acc += rank01(a, domain)
    return (acc / len(fields)).astype(np.float32)


def component_tips(catalogue):
    """Two principal-axis extreme points per connected component.

    Returns (tip_y, tip_x, out_dy, out_dx) with unit outward directions.
    Components smaller than three pixels get an arbitrary axis and duplicate tips;
    that is harmless because the offset prior excludes the catalogue interior.
    """
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
    theta = 0.5 * np.arctan2(2.0 * sxy, sxx - syy)      # major-axis angle
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
        # one representative pixel per component per extreme
        _, first = np.unique(comp, return_index=True)
        yy, xx, comp = yy[first], xx[first], comp[first]
        tip_y.append(yy)
        tip_x.append(xx)
        out_dy.append(sign * np.sin(theta)[comp])
        out_dx.append(sign * np.cos(theta)[comp])
    return (np.concatenate(tip_y).astype(np.int64), np.concatenate(tip_x).astype(np.int64),
            np.concatenate(out_dy), np.concatenate(out_dx))


def tip_kernels(catalogue, shape):
    """Along-strike / across-strike distances to the nearest mapped tip."""
    ty, tx, ody, odx = component_tips(catalogue)
    if ty.size == 0:
        inf = np.full(shape, np.inf, np.float32)
        return inf, inf
    tip_mask = np.zeros(shape, bool)
    tip_id = np.full(shape, -1, np.int64)
    # last write wins; duplicate tips are equivalent neighbours
    tip_id[ty, tx] = np.arange(ty.size)
    tip_mask[ty, tx] = True
    _, (iy, ix) = ndi.distance_transform_edt(~tip_mask, return_distances=True,
                                             return_indices=True)
    k = tip_id[iy, ix]
    del iy, ix
    y = np.arange(shape[0], dtype=np.float32)[:, None]
    x = np.arange(shape[1], dtype=np.float32)[None, :]
    u = (y - ty[k].astype(np.float32)) * ody[k].astype(np.float32) + \
        (x - tx[k].astype(np.float32)) * odx[k].astype(np.float32)
    v = -(y - ty[k].astype(np.float32)) * odx[k].astype(np.float32) + \
        (x - tx[k].astype(np.float32)) * ody[k].astype(np.float32)
    return u.astype(np.float32), v.astype(np.float32)


def score_components(catalogue_visible, geo_rank, valid, *,
                     offset_peak=OFFSET_PEAK_PX, offset_sigma=OFFSET_SIGMA_PX,
                     min_offset=MIN_OFFSET_PX, tip_along=TIP_SIGMA_ALONG_PX,
                     tip_across=TIP_SIGMA_ACROSS_PX):
    """Compute the three registered factors once, so ablations share exact inputs."""
    cat = np.asarray(catalogue_visible, bool)
    allowed = np.asarray(valid, bool) & ~cat
    d = ndi.distance_transform_edt(~cat).astype(np.float32)
    off = np.exp(-(((d - offset_peak) / offset_sigma) ** 2)).astype(np.float32)
    off[d < min_offset] = 0.0
    del d
    u, v = tip_kernels(cat, cat.shape)
    beyond = np.clip(u, 0.0, None)
    tip = np.exp(-beyond / tip_along) * np.exp(-np.abs(v) / tip_across)
    tip = np.where(np.isfinite(tip), tip, 0.0).astype(np.float32)
    del u, v, beyond
    gate = np.clip(np.asarray(geo_rank, np.float32), 0.0, 1.0)
    return {'offset': off, 'tip': tip, 'gate': gate, 'allowed': allowed}


def combine_components(comp, use_offset=True, use_tip=True, use_gate=True):
    """Registered product form; switches exist only for pre-registered ablations."""
    shape = comp['allowed'].shape
    score = np.ones(shape, np.float32)
    if use_offset:
        score *= comp['offset']
    if use_tip:
        score *= (0.5 + 0.5 * comp['tip'])
    if use_gate:
        score *= (0.5 + 0.5 * comp['gate'])
    score = np.where(comp['allowed'], score, 0.0).astype(np.float32)
    if not np.isfinite(score).all():
        raise ValueError('non-finite structural score')
    return score


def structural_score(catalogue_visible, geo_rank, valid, **kwargs):
    """Registered score: offset prior x tip kernel x geophysical gate."""
    return combine_components(score_components(catalogue_visible, geo_rank, valid, **kwargs))


def place_dots(score, allowed, n=DOT_COUNT, radius_px=NMS_RADIUS_PX):
    """Greedy top-score placement with a Euclidean non-maximum-suppression radius."""
    s = np.asarray(score, np.float32)
    allowed = np.asarray(allowed, bool) & np.isfinite(s) & (s > 0)
    if not allowed.any():
        raise ValueError('no allowed cells with positive score')
    flat = np.flatnonzero(allowed & (s > 0))
    order = flat[np.argsort(s.ravel()[flat], kind='stable')[::-1]]
    h, w = s.shape
    r = int(np.ceil(radius_px))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (yy * yy + xx * xx) <= radius_px * radius_px
    blocked = np.zeros((h, w), bool)
    dots = np.zeros((h, w), bool)
    ys, xs = np.divmod(order, w)
    picked = 0
    n = int(n)
    for y, x in zip(ys, xs):
        if blocked[y, x]:
            continue
        dots[y, x] = True
        picked += 1
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        blocked[y0:y1, x0:x1] |= disk[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)]
        if picked >= n:
            break
    return dots, picked


def dots_to_field(dots):
    return np.asarray(dots, np.float32)
