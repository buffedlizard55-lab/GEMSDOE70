"""Candidate C1: strike-coherent catalogue extrapolation (pre-registered in docs/candidates-2026-10-20.md).

Catalogue-derived inputs (structure tensor and proximity) use ONLY the traces passed in
as ``visible``. The caller is responsible for passing the holdout-visible mask during
validation and the full catalogue only for the final, non-holdout export.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .method import rank01

SIG_TRACE = 3.0      # px, smoothing of the visible-trace mask before differentiation
SIG_TENSOR = 10.0    # px, structure-tensor averaging window (1 km)
SIG_MAG = 1.5        # px, magnetic smoothing before gradient
PROX_DECAY_PX = 20.0 # px, 2 km catalogue-proximity decay


def trace_orientation(visible, valid):
    """Trace-normal angle theta_n and coherence from the structure tensor of the visible mask."""
    t = ndi.gaussian_filter(np.asarray(visible, np.float64), SIG_TRACE)
    gy, gx = np.gradient(t)
    jxx = ndi.gaussian_filter(gx * gx, SIG_TENSOR)
    jyy = ndi.gaussian_filter(gy * gy, SIG_TENSOR)
    jxy = ndi.gaussian_filter(gx * gy, SIG_TENSOR)
    theta_n = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)
    energy = jxx + jyy
    coh = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy ** 2) / (energy + 1e-12)
    coh = np.where(valid, np.clip(coh, 0.0, 1.0), 0.0)
    return theta_n.astype(np.float32), coh.astype(np.float32)


def magnetic_gradient(rtp, valid):
    """Gradient magnitude and direction of the smoothed RTP field (valid domain only)."""
    r = np.where(valid, rtp, 0.0).astype(np.float64)
    r = ndi.gaussian_filter(r, SIG_MAG)
    my, mx = np.gradient(r)
    mag = np.hypot(my, mx)
    phi = np.arctan2(my, mx)
    return mag.astype(np.float32), phi.astype(np.float32)


def magnetic_coherence(rtp, valid):
    """Catalogue-FREE linearity of the RTP gradient field (structure tensor of the magnetic field itself)."""
    r = np.where(valid, rtp, 0.0).astype(np.float64)
    r = ndi.gaussian_filter(r, SIG_MAG)
    gy, gx = np.gradient(r)
    jxx = ndi.gaussian_filter(gx * gx, SIG_TENSOR)
    jyy = ndi.gaussian_filter(gy * gy, SIG_TENSOR)
    jxy = ndi.gaussian_filter(gx * gy, SIG_TENSOR)
    coh = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy ** 2) / (jxx + jyy + 1e-12)
    return np.where(valid, np.clip(coh, 0.0, 1.0), 0.0).astype(np.float32)


def catalogue_proximity(visible, valid):
    d = ndi.distance_transform_edt(~np.asarray(visible, bool))
    return np.where(valid, np.exp(-d / PROX_DECAY_PX), 0.0).astype(np.float32)


def features(rtp, visible, valid):
    """All C1 features. Returns a dict of float32 arrays (zero outside ``valid``)."""
    theta_n, coh = trace_orientation(visible, valid)
    mag, phi_m = magnetic_gradient(rtp, valid)
    align = np.where(valid, np.abs(np.cos(phi_m - theta_n)), 0.0).astype(np.float32)
    prox = catalogue_proximity(visible, valid)
    return {'proximity': prox, 'alignment': align, 'magnetic_gradient': np.where(valid, mag, 0).astype(np.float32),
            'coherence': np.where(valid, coh, 0).astype(np.float32),
            'magnetic_coherence': magnetic_coherence(rtp, valid)}


def combine(feats, valid, arm):
    """Arms: 'candidate', 'ablation_no_catalogue', 'ablation_no_alignment'."""
    f = feats
    if arm == 'candidate':
        prod = rank01(f['proximity'], valid) * f['alignment'] * rank01(f['magnetic_gradient'], valid) * f['coherence']
    elif arm == 'ablation_no_catalogue':
        # Catalogue-free: uses no visible-trace quantity at all.
        prod = rank01(f['magnetic_gradient'], valid) * f['magnetic_coherence']
    elif arm == 'ablation_no_alignment':
        prod = rank01(f['proximity'], valid) * rank01(f['magnetic_gradient'], valid) * f['coherence']
    else:
        raise ValueError(f'unknown arm {arm}')
    return rank01(np.where(valid, prod, 0.0), valid)
