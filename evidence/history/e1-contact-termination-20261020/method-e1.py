"""One fixed, catalogue-independent contact-termination hypothesis."""
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata


def rank01(values, valid):
    a = np.asarray(values)
    valid = np.asarray(valid, bool) & np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    n = int(valid.sum())
    if n > 1:
        out[valid] = (rankdata(a[valid], method='average') - 1) / (n - 1)
    return out


def fill_nearest(a):
    good = np.isfinite(a)
    if not good.any():
        raise ValueError('empty finite feature')
    indices = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return a[tuple(indices)]


def physical_features(rtp, gravity, basement, valid):
    """No fault catalogue accepted or read by this function."""
    r, g, b = [fill_nearest(np.where(valid, a, np.nan)) for a in (rtp, gravity, basement)]
    my, mx = np.gradient(ndi.gaussian_filter(r, 1))
    amplitude = ndi.gaussian_filter(np.hypot(my, mx), 2)
    gy, gx = np.gradient(ndi.gaussian_filter(g, 3))
    edge = np.hypot(gy, gx)
    ny = np.divide(gy, edge, out=np.zeros_like(gy), where=edge > 0)
    nx = np.divide(gx, edge, out=np.zeros_like(gx), where=edge > 0)
    ay, ax = np.gradient(amplitude)
    by, bx = np.gradient(ndi.gaussian_filter(b, 3))
    return {
        'termination': np.where(valid, np.abs(-nx * ay + ny * ax), 0).astype(np.float32),
        'gravity_edge': np.where(valid, edge, 0).astype(np.float32),
        'basement_normal': np.where(valid, np.abs(ny * by + nx * bx), 0).astype(np.float32),
    }


def upper_surface(ranks, valid, cutoff=.98):
    """Fixed continuous sparsification; caller masks known faults explicitly."""
    if not 0 <= cutoff < 1:
        raise ValueError('invalid cutoff')
    return np.where(valid, np.maximum(ranks - cutoff, 0) / (1 - cutoff), 0).astype(np.float32)


def joint_field(features, valid, names=('termination', 'gravity_edge', 'basement_normal')):
    if not names:
        raise ValueError('no features')
    product = np.ones(valid.shape, np.float32)
    for name in names:
        product *= rank01(features[name], valid)
    return rank01(product ** (1 / len(names)), valid)
