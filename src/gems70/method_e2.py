"""E2 fixed hypothesis: DEM scarp curvature x geodetic strain x shallow cover.

Preregistration: docs/hypotheses-e2.md (written before any E2 result).
Catalogue-independent: no function here reads the fault catalogue. Catalogue
masking / distance exclusion happen only in the experiment driver, from the
fold-visible mask for holdout scoring and the full catalogue for final dots.
Lane code only; shared evaluator/writer/validator stay in vendor/gems57.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

EPS_RANK = 1e-6


def rank01(values, valid):
    """Average-tie ranks scaled to [0, 1] over ``valid`` finite cells; 0 else."""
    a = np.asarray(values)
    valid = np.asarray(valid, bool) & np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    n = int(valid.sum())
    if n > 1:
        out[valid] = ((rankdata(a[valid], method="average") - 1) / (n - 1)).astype(np.float32)
    return out


def fill_nearest(a):
    """Nearest-finite fill; caller passes NaN outside the ORIGINAL finite domain."""
    good = np.isfinite(a)
    if not good.any():
        raise ValueError("empty finite feature")
    idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return np.asarray(a[tuple(idx)], np.float32)


def _g(a, sigma, order=(0, 0)):
    return ndi.gaussian_filter(np.asarray(a, np.float32), sigma, order=order).astype(np.float32)


def dem_features(z_filled, valid):
    """Slope, gradient-directional curvature magnitude, tensor coherence.

    ``z_filled`` is detrended elevation already nearest-filled from the
    original finite domain; outputs are zero outside ``valid`` (eroded support).
    Curvature is the second derivative along the gradient direction,
    (gx^2 hxx + 2 gx gy hxy + gy^2 hyy) / (gx^2 + gy^2), whose magnitude peaks
    at scarp crests/toes. No catalogue input.
    """
    valid = np.asarray(valid, bool)
    gy = _g(z_filled, 1.0, (1, 0))
    gx = _g(z_filled, 1.0, (0, 1))
    slope = np.hypot(gy, gx).astype(np.float32)
    hyy = _g(z_filled, 1.0, (2, 0))
    hxy = _g(z_filled, 1.0, (1, 1))
    hxx = _g(z_filled, 1.0, (0, 2))
    den = (gx * gx + gy * gy).astype(np.float32)
    curv = np.divide(gx * gx * hxx + 2.0 * gx * gy * hxy + gy * gy * hyy,
                     den, out=np.zeros_like(den), where=den > 0).astype(np.float32)
    del hyy, hxy, hxx, den
    jxx = _g(gx * gx, 2.0)
    jxy = _g(gx * gy, 2.0)
    jyy = _g(gy * gy, 2.0)
    del gy, gx
    tr = (jxx + jyy).astype(np.float32)
    disc = np.sqrt(np.maximum(((jxx - jyy) * 0.5) ** 2 + jxy * jxy, 0)).astype(np.float32)
    del jxx, jxy, jyy
    coh = np.divide(2.0 * disc, tr, out=np.zeros_like(tr), where=tr > 0).astype(np.float32)
    np.clip(coh, 0.0, 1.0, out=coh)
    del tr, disc
    return {
        "dem_slope": np.where(valid, slope, 0).astype(np.float32),
        "dem_curv": np.where(valid, np.abs(curv), 0).astype(np.float32),
        "dem_coherence": np.where(valid, coh, 0).astype(np.float32),
    }


def physical_features_e2(filled, valid):
    """All E2 derived fields from nearest-filled raw bands. No catalogue read.

    ``filled`` keys: det_elev, inv2, shear, dilat, depth (full-grid float32).
    Returns raw-scale derived fields (zero outside ``valid``) plus ranked
    composites ``scarp``, ``scarp_nocoh``, ``strain``, ``shallow`` in [0, 1].
    """
    valid = np.asarray(valid, bool)
    feats = dem_features(filled["det_elev"], valid)
    r_slope = rank01(feats["dem_slope"], valid)
    r_curv = rank01(feats["dem_curv"], valid)
    base = np.sqrt(np.maximum(r_slope * r_curv, 0)).astype(np.float32)
    feats["scarp_nocoh"] = rank01(base, valid)
    w = (0.25 + 0.75 * feats["dem_coherence"]).astype(np.float32)
    feats["scarp"] = rank01(base * w, valid)
    del r_slope, r_curv, base, w
    s_inv = rank01(_g(filled["inv2"], 5.0), valid)
    s_shear = rank01(_g(filled["shear"], 5.0), valid)
    s_dil = rank01(np.abs(_g(filled["dilat"], 5.0)), valid)
    geo = np.exp((np.log(np.maximum(s_inv, EPS_RANK)) + np.log(np.maximum(s_shear, EPS_RANK))
                  + np.log(np.maximum(s_dil, EPS_RANK))) / 3.0).astype(np.float32)
    feats["strain"] = rank01(geo, valid)
    del s_inv, s_shear, s_dil, geo
    feats["shallow"] = np.where(valid, 1.0 - rank01(_g(filled["depth"], 3.0), valid), 0).astype(np.float32)
    return feats


def joint_field_e2(feats, valid, w_scarp=0.60, w_strain=0.20, w_shallow=0.20,
                   scarp_key="scarp"):
    """Weighted geometric mean of ranked components, re-ranked to [0, 1]."""
    ws = (w_scarp, w_strain, w_shallow)
    if any(w < 0 for w in ws) or abs(sum(ws) - 1.0) > 1e-9:
        raise ValueError("joint weights must be non-negative and sum to 1")
    acc = np.zeros(np.asarray(valid).shape, np.float32)
    for key, w in ((scarp_key, w_scarp), ("strain", w_strain), ("shallow", w_shallow)):
        if w:
            acc += (w * np.log(np.maximum(feats[key], EPS_RANK))).astype(np.float32)
    return rank01(np.exp(acc), valid)


def upper_surface_e2(ranks, valid, cutoff=0.98):
    """E1-continuity continuous field: upper tail rescaled to [0, 1] (not dots)."""
    if not 0 <= cutoff < 1:
        raise ValueError("invalid cutoff")
    return np.where(valid, np.maximum(ranks - cutoff, 0) / (1 - cutoff), 0).astype(np.float32)


def _disk_offsets(min_sep):
    r = int(np.ceil(min_sep))
    return [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if np.hypot(dy, dx) < min_sep]


def dotted_emission(order_values, allowed, budget, min_sep=2.8, candidate_factor=12):
    """Greedy dots in descending ``order_values`` with min separation.

    Deterministic (stable argsort). Only the top ``budget*candidate_factor``
    allowed cells by value are considered; the caller must confirm the budget
    was reached (returned count) so truncation is never silent.
    """
    allowed = np.asarray(allowed, bool)
    vals = np.asarray(order_values)
    if vals.shape != allowed.shape or budget <= 0 or min_sep <= 0:
        raise ValueError("emission shape/budget/separation invalid")
    ys, xs = np.nonzero(allowed)
    if ys.size == 0:
        return np.zeros(allowed.shape, bool)
    v = vals[ys, xs]
    keep = min(ys.size, int(budget) * int(candidate_factor))
    if keep < ys.size:
        part = np.argpartition(-v, keep - 1)[:keep]
        ys, xs, v = ys[part], xs[part], v[part]
    order = np.argsort(-v, kind="stable")
    ys, xs = ys[order], xs[order]
    del v, order
    h, w = allowed.shape
    blocked = np.zeros(allowed.shape, bool)
    dots = np.zeros(allowed.shape, bool)
    offs = _disk_offsets(float(min_sep))
    n = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        if blocked[y, x]:
            continue
        dots[y, x] = True
        n += 1
        if n >= budget:
            break
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy, xx] = True
    return dots


def random_dotted(allowed, budget, seed, min_sep=2.8, candidate_factor=12):
    """Same spacing rule as :func:`dotted_emission` with random visit order."""
    allowed = np.asarray(allowed, bool)
    flat = np.flatnonzero(allowed)
    if flat.size == 0 or budget <= 0:
        return np.zeros(allowed.shape, bool)
    rng = np.random.default_rng(seed)
    take = min(flat.size, int(budget) * int(candidate_factor))
    cand = rng.choice(flat, size=take, replace=False)
    h, w = allowed.shape
    blocked = np.zeros(allowed.shape, bool)
    dots = np.zeros(allowed.shape, bool)
    offs = _disk_offsets(float(min_sep))
    n = 0
    for f in cand.tolist():
        y, x = divmod(int(f), w)
        if blocked[y, x]:
            continue
        dots[y, x] = True
        n += 1
        if n >= budget:
            break
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy, xx] = True
    return dots
