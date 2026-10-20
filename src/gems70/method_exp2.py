"""Experiment 2: shallow magnetic lineaments from TMI vertical gradient.

Lane: VG Hessian centerlines (both polarities) OR VG-gradient-magnitude
contact ridges, NMS-thinned, sparse top-k binary emission with spacing and a
catalogue-distance prune. No catalogue values enter any ranking transform;
catalogue geometry is used only for the emission prune and the holdout masks.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from gems70.method import fill_nearest, rank01

SCALES = (1.2, 2.5)
SPACING_PX = 2.0
CATALOGUE_PRUNE_PX = 2.0
DOT_BUDGET = 38000
EW_STOP_FRACTION = 0.50
EW_HALF_WINDOW_DEG = 10.0


def dominant_eig(field, sigma):
    """Hessian eigenvalue of largest |.| (across-structure curvature)."""
    axx = ndi.gaussian_filter(field, sigma, order=(0, 2), mode="nearest")
    ayy = ndi.gaussian_filter(field, sigma, order=(2, 0), mode="nearest")
    axy = ndi.gaussian_filter(field, sigma, order=(1, 1), mode="nearest")
    tmp = np.sqrt(np.maximum(((axx - ayy) * 0.5) ** 2 + axy ** 2, 0.0))
    l1 = (axx + ayy) * 0.5 + tmp
    l2 = (axx + ayy) * 0.5 - tmp
    return np.where(np.abs(l1) >= np.abs(l2), l1, l2)


def multiscale_line(field, valid, both_polarities):
    """Max over fixed scales of dominant-curvature line response.

    Both polarities: |dominant eig| (linear VG highs and lows). Bright-only:
    concave-down dominant eig (maxima such as contact edges in |grad VG|).
    """
    out = np.zeros(field.shape, np.float32)
    for sigma in SCALES:
        eig = dominant_eig(field, sigma)
        resp = np.abs(eig) if both_polarities else np.maximum(-eig, 0)
        out = np.maximum(out, resp)
    return np.where(valid, out, 0).astype(np.float32)


def physical_scores(tmi_vg, valid):
    """Channel A (both-polarity VG centerlines) and B (VG contact edges)."""
    filled = fill_nearest(np.where(valid, tmi_vg, np.nan))
    smooth = ndi.gaussian_filter(filled, 1.0, mode="nearest")
    chan_a = multiscale_line(smooth, valid, both_polarities=True)
    gy, gx = np.gradient(smooth)
    gradmag = np.hypot(gy, gx).astype(np.float32)
    chan_b = multiscale_line(gradmag, valid, both_polarities=False)
    score = np.maximum(rank01(chan_a, valid), rank01(chan_b, valid))
    return {"chan_a": chan_a.astype(np.float32),
            "chan_b": chan_b.astype(np.float32),
            "score": score.astype(np.float32),
            "smooth": smooth.astype(np.float32)}


def skeleton(score, valid):
    """8-connected non-maximum-suppressed centerline support."""
    local_max = ndi.maximum_filter(score, size=3, mode="nearest")
    return (valid & np.isfinite(score) & (score > 0)
            & (score >= local_max - 1e-9))


def structure_theta(field, sigma=2.0):
    """Structure-tensor orientation (gradient convention), H33-style."""
    gx = ndi.gaussian_filter(field, sigma, order=(0, 1), mode="nearest")
    gy = ndi.gaussian_filter(field, sigma, order=(1, 0), mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, sigma, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, sigma, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, sigma, mode="nearest")
    return (0.5 * np.arctan2(2 * jxy, (jxx - jyy) + 1e-12)).astype(np.float32)


def ew_fraction(theta, support):
    """Fraction of support whose line direction is within the E-W window.

    Line direction = theta + pi/2 (mod pi); E-W means direction near 0/pi.
    """
    lam = (theta[support] + np.pi / 2) % np.pi
    window = np.deg2rad(EW_HALF_WINDOW_DEG)
    return float((np.abs(np.sin(lam)) <= np.sin(window)).mean())


def greedy_dots(score, support, catalogue_dist, budget=DOT_BUDGET,
                spacing=SPACING_PX, prune=CATALOGUE_PRUNE_PX):
    """Score-ranked greedy dots with disk spacing and catalogue-distance prune.

    Deterministic: ties broken by row-major order via stable argsort on
    (-score, ravel_index).
    """
    pool = (np.asarray(support, bool)
            & np.isfinite(score) & (score > 0)
            & (np.asarray(catalogue_dist) > prune))
    order = np.flatnonzero(pool)
    if order.size == 0:
        return np.zeros(score.shape, bool), {"pool": 0, "taken": 0}
    key_score = -score.ravel()[order].astype(np.float64)
    seq = np.lexsort((order, key_score))
    order = order[seq]
    h, w = score.shape
    taken = np.zeros(score.shape, bool)
    blocked = np.zeros(score.shape, bool)
    radius = int(np.ceil(spacing))
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    disk = yy * yy + xx * xx <= spacing * spacing
    count = 0
    for flat in order:
        if count >= budget:
            break
        y, x = divmod(int(flat), w)
        if blocked[y, x]:
            continue
        taken[y, x] = True
        count += 1
        y0, y1 = max(0, y - radius), min(h, y + radius + 1)
        x0, x1 = max(0, x - radius), min(w, x + radius + 1)
        ky0, ky1 = y0 - (y - radius), y1 - (y - radius)
        kx0, kx1 = x0 - (x - radius), x1 - (x - radius)
        blocked[y0:y1, x0:x1] |= disk[ky0:ky1, kx0:kx1]
    return taken, {"pool": int(order.size), "taken": int(count)}
