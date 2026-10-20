"""P5 analytic-signal stratified halo - catalogue-independent ranking.

Uses only training_features bands 3 (tmi_hg) and 9 (tmi_vg) to compute
analytic-signal amplitude A = hypot(hg, vg). No catalogue input.
Halo geometry (distance to catalogue) remains for placement band,
but ranking inside halo is from magnetic amplitude.
"""
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
        out[valid] = ((rankdata(a[valid], method='average') - 1) / (n - 1)).astype(np.float32)
    return out

def fill_nearest(a):
    good = np.isfinite(a)
    if not good.any():
        raise ValueError('empty finite feature')
    idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return a[tuple(idx)]

def analytic_signal_features(tmi_hg, tmi_vg, valid):
    """Compute analytic-signal amplitude from tmi_hg and tmi_vg (no catalogue)."""
    hg, vg = [fill_nearest(np.where(valid, a, np.nan)) for a in (tmi_hg, tmi_vg)]
    amp = np.hypot(hg, vg).astype(np.float32)
    return {'analytic_amp': amp}

def analytic_ranks(fields, domain):
    acc = np.zeros(next(iter(fields.values())).shape, np.float32)
    for a in fields.values():
        acc += rank01(a, domain)
    return (acc / len(fields)).astype(np.float32)
