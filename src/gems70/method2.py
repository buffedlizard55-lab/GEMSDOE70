"""E2/E3 preregistered lanes (docs/preregistration-e2.md). Catalogue-free ranking.

E1 (`gems70.method`) is frozen and untouched. Everything here is new code for
the 2026-10-20 E2/E3 preregistration; shared metric/holdout/writer code in
`vendor/gems57` is reused unmodified by the experiment scripts.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from gems70.method import rank01  # average-tie ranks over a valid mask (E1, reused)

# Undirected step axes as (dy, dx): E-W, NE-SW (image coords), N-S, NW-SE.
AXES = ((0, 1), (1, 1), (1, 0), (1, -1))
STEP_OFFSET_PX = 2
THIN_MIN_DIST_PX = 2.8
THIN_POOL = 400_000
TARGET_DOTS = 38_000


def fill_nearest_from(values, valid0):
    """Nearest-valid fill using *valid0* cells only (E2 fix of the E1 order flaw)."""
    a = np.asarray(values, dtype=np.float64)
    v = np.asarray(valid0, bool) & np.isfinite(a)
    if not v.any():
        raise ValueError("no valid cells to fill from")
    if v.all():
        return a.astype(np.float32)
    idx = ndi.distance_transform_edt(~v, return_distances=False, return_indices=True)
    return a[tuple(idx)].astype(np.float32)


def structure_tensor_normal(filled, smooth_grad=1.0, smooth_tensor=2.0):
    """Return (axis_index, coherence) of the dominant gradient (edge normal).

    x = column axis, y = row axis. Principal gradient angle from the x-axis is
    0.5*atan2(2*Jxy, Jxx-Jyy); its (row, col) direction is (sin a, cos a).
    Axis choice is by maximum absolute dot product with the 4 undirected axes.
    Synthetic checks: an x-step (gx only) -> angle 0 -> E-W axis (0,1);
    a y-step (gy only) -> angle pi/2 -> N-S axis (1,0). See tests/test_method2.py.
    """
    s = ndi.gaussian_filter(np.asarray(filled, np.float64), smooth_grad)
    gy, gx = np.gradient(s)
    jxx = ndi.gaussian_filter(gx * gx, smooth_tensor)
    jyy = ndi.gaussian_filter(gy * gy, smooth_tensor)
    jxy = ndi.gaussian_filter(gx * gy, smooth_tensor)
    angle = 0.5 * np.arctan2(2.0 * jxy, (jxx - jyy) + 1e-30)
    coherence = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy ** 2) / (jxx + jyy + 1e-12)
    coherence = np.clip(coherence, 0.0, 1.0).astype(np.float32)
    dir_r, dir_c = np.sin(angle), np.cos(angle)
    dots = []
    for dy, dx in AXES:
        n = float(np.hypot(dy, dx))
        dots.append(np.abs(dir_r * (dy / n) + dir_c * (dx / n)))
    axis_index = np.argmax(np.stack(dots), axis=0).astype(np.int8)
    return axis_index, coherence


def _shift_no_wrap(a, dy, dx):
    """Shift by (dy, dx) with zero fill; destination[y,x] = a[y+dy, x+dx] in bounds."""
    h, w = a.shape
    out = np.zeros_like(a)
    y_dst = slice(max(0, -dy), min(h, h - dy) if dy > 0 else h)
    y_src = slice(max(0, dy), min(h, h + dy) if dy < 0 else h)
    x_dst = slice(max(0, -dx), min(w, w - dx) if dx > 0 else w)
    x_src = slice(max(0, dx), min(w, w + dx) if dx < 0 else w)
    # slice lengths must agree; recompute defensively from starts/stops
    yd0, yd1 = (y_dst.start or 0), y_dst.stop
    ys0 = y_src.start or 0
    xd0, xd1 = (x_dst.start or 0), x_dst.stop
    xs0 = x_src.start or 0
    ny, nx = yd1 - yd0, xd1 - xd0
    out[yd0:yd0 + ny, xd0:xd0 + nx] = a[ys0:ys0 + ny, xs0:xs0 + nx]
    return out


def axis_step(smoothed, offset=STEP_OFFSET_PX):
    """List of 4 step maps |f(+offset*axis) - f(-offset*axis)|, one per AXES entry.

    Pixels whose + or - sample falls outside the array are exactly 0 (zero-fill
    must never manufacture a step on a constant field; regression-tested).
    """
    a = np.asarray(smoothed, np.float64)
    h, w = a.shape
    steps = []
    for dy, dx in AXES:
        plus = _shift_no_wrap(a, offset * dy, offset * dx)
        minus = _shift_no_wrap(a, -offset * dy, -offset * dx)
        step = np.abs(plus - minus)
        ok = np.ones(a.shape, bool)
        oy, ox = offset * abs(dy), offset * abs(dx)
        if oy:
            ok[:oy, :] = False
            ok[h - oy:, :] = False
        if ox:
            ok[:, :ox] = False
            ok[:, w - ox:] = False
        steps.append(np.where(ok, step, 0.0).astype(np.float32))
    return steps


def oriented_step(smoothed, axis_index, offset=STEP_OFFSET_PX):
    """Return (step_oriented, step_max) float32 maps for a smoothed field."""
    steps = np.stack(axis_step(smoothed, offset=offset))  # (4, H, W)
    idx = np.asarray(axis_index)
    oriented = np.take_along_axis(steps, idx[None, :, :].astype(np.int64), axis=0)[0]
    return oriented.astype(np.float32), steps.max(axis=0).astype(np.float32)


def gradient_magnitude(filled, sigma):
    s = ndi.gaussian_filter(np.asarray(filled, np.float64), sigma)
    gy, gx = np.gradient(s)
    return np.hypot(gy, gx).astype(np.float32)


def depth_index(rtp_filled):
    """E3 depth proxy A3/(A1+eps): deeper sources keep long-wavelength gradients."""
    a1 = gradient_magnitude(rtp_filled, 1.0).astype(np.float64)
    a3 = gradient_magnitude(rtp_filled, 3.0).astype(np.float64)
    idx = a3 / (a1 + 1e-12)
    return ndi.gaussian_filter(idx, 1.0).astype(np.float32)


def joint_rank(features, valid, names):
    """Geometric mean of per-feature ranks, re-ranked to [0,1] (E1 joint form)."""
    if not names:
        raise ValueError("no features")
    product = np.ones(np.asarray(valid).shape, np.float32)
    for name in names:
        product *= rank01(features[name], valid)
    return rank01(product ** (1.0 / len(names)), valid)


def priority_thin(rank_field, allowed, target_n=TARGET_DOTS,
                  min_dist=THIN_MIN_DIST_PX, pool=THIN_POOL):
    """Priority thinning: descending rank order, min Euclidean spacing, fixed budget.

    Deterministic: candidates enumerated in row-major flat order, stable-sorted
    by descending rank (ties keep flat order). A candidate is accepted iff no
    accepted dot lies at distance < min_dist. Returns (bool mask, n_accepted).
    """
    rank = np.asarray(rank_field)
    allow = np.asarray(allowed, bool)
    if rank.ndim != 2 or rank.shape != allow.shape:
        raise ValueError("rank/allowed shape mismatch")
    if not np.isfinite(rank[allow]).all():
        raise ValueError("rank field must be finite on allowed cells")
    flat_idx = np.flatnonzero(allow.ravel())
    if flat_idx.size == 0 or target_n <= 0:
        return np.zeros(rank.shape, bool), 0
    vals = rank.ravel()[flat_idx]
    order = np.argsort(-vals, kind="stable")[:pool]
    cand = flat_idx[order]
    h, w = rank.shape
    r = int(np.ceil(min_dist))
    oy, ox = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (oy * oy + ox * ox) < (min_dist * min_dist)  # strictly closer than min_dist
    blocked = np.zeros(rank.shape, bool)
    emitted = np.zeros(rank.shape, bool)
    n = 0
    for f in cand:
        y, x = divmod(int(f), w)
        if blocked[y, x]:
            continue
        emitted[y, x] = True
        n += 1
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        sub = disk[y0 - (y - r): disk.shape[0] - ((y + r + 1) - y1),
                   x0 - (x - r): disk.shape[1] - ((x + r + 1) - x1)]
        blocked[y0:y1, x0:x1] |= sub
        if n >= target_n:
            break
    return emitted, n


def topn_mask(values, footprint, n):
    """Top-n footprint pixels by value, stable row-major tie-break (R1 support)."""
    v = np.asarray(values)
    fp = np.asarray(footprint, bool)
    flat_idx = np.flatnonzero(fp.ravel())
    vals = v.ravel()[flat_idx].astype(np.float64)
    vals = np.where(np.isfinite(vals), vals, -np.inf)
    order = np.argsort(-vals, kind="stable")[: max(0, int(n))]
    out = np.zeros(v.shape, bool)
    out.ravel()[flat_idx[order]] = True
    return out
