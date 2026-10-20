"""Experiment 2 (H70-2A): label-free multi-physics features + corroboration gate.

Every feature here is computed without reading the fault catalogue. The only
catalogue use in the experiment is (a) supervised training labels taken from
each holdout fold's *visible* faults in scripts/run_experiment2.py, and
(b) the final off-catalogue mask (dots only >2 px from mapped faults), which
mirrors the organizer masking rule described in the preregistration.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .method import rank01


def dequant(u8: np.ndarray, xmax: float, mode: str) -> np.ndarray:
    u = np.clip((u8.astype(np.float32) - 1.0) / 254.0, 0.0, 1.0)
    val = (u ** 2) * float(xmax) if mode == "sqrt" else u * float(xmax)
    return np.where(u8 > 0, val, 0.0).astype(np.float32)


def _grad_mag(a: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(a)
    return np.hypot(gy, gx).astype(np.float32)


def _local_anom(a: np.ndarray, size: int = 15) -> np.ndarray:
    return (a - ndi.uniform_filter(a, size=size)).astype(np.float32)


def multiscale_edge(field: np.ndarray, valid: np.ndarray, sigmas=(1.0, 1.5, 2.5, 4.0)) -> np.ndarray:
    acc = np.zeros(field.shape, np.float32)
    for s in sigmas:
        m = _grad_mag(ndi.gaussian_filter(field, s))
        ok = valid & np.isfinite(m)
        if ok.any():
            hi = np.percentile(m[ok], 95.0)
            if hi > 0:
                acc = np.maximum(acc, np.where(ok, np.clip(m / hi, 0, 1), 0))
    return acc


def coherence(field: np.ndarray, valid: np.ndarray, sigma: float = 2.0, win: float = 3.0) -> np.ndarray:
    sm = ndi.gaussian_filter(field, sigma)
    gy, gx = np.gradient(sm)
    ok = valid & np.isfinite(gx)
    jxx = ndi.gaussian_filter(np.where(ok, gx * gx, 0.0), win, mode="nearest")
    jyy = ndi.gaussian_filter(np.where(ok, gy * gy, 0.0), win, mode="nearest")
    jxy = ndi.gaussian_filter(np.where(ok, gx * gy, 0.0), win, mode="nearest")
    den = jxx + jyy
    r = np.where(den > 0, np.hypot(jxx - jyy, 2.0 * jxy) / np.maximum(den, 1e-30), 0.0)
    return np.where(ok, r, 0).astype(np.float32)


def ortho_gate_score(topo_edge: np.ndarray, gravity: np.ndarray, magnetic: np.ndarray,
                     valid: np.ndarray, w: float = 0.25, sigma: float = 2.0) -> np.ndarray:
    """GEMSDOE49-architecture reimplementation: topo edge x coherence, gated by
    magnitude-weighted orthogonality to BOTH potential fields (gate in [1-w, 1])."""
    base = multiscale_edge(topo_edge, valid) * coherence(topo_edge, valid, sigma=2.0, win=3.0)
    # topographic edge direction from the slope field itself
    ty, tx = np.gradient(topo_edge)
    tm = np.hypot(ty, tx)
    orthos = []
    for other in (gravity, magnetic):
        oy, ox = np.gradient(ndi.gaussian_filter(other, sigma))
        om = np.hypot(oy, ox)
        ok = valid & (tm > 0) & (om > 0)
        tn = np.zeros_like(tm); on = np.zeros_like(om)
        if ok.any():
            tn = np.clip(tm / np.percentile(tm[ok], 95), 0, 1)
            on = np.clip(om / np.percentile(om[ok], 95), 0, 1)
        sin = np.where(ok, (tx * oy - ty * ox) / np.maximum(tm * om, 1e-12), 0.0)
        orthos.append(tn * on * sin * sin)
    gate = 1.0 - w * orthos[0] * orthos[1]
    return np.where(valid, base * np.clip(gate, 0, 1), 0).astype(np.float32)


def domain_surfaces(feat: dict[str, np.ndarray], valid: np.ndarray) -> dict[str, np.ndarray]:
    """Unsupervised [0,1] rank surface per physical domain (label-free)."""
    def r(name):
        return rank01(feat[name], valid)
    scarp = np.maximum(np.maximum(r("lid_tect"), r("dem10_onesided3")), r("topo_edge"))
    geophys = np.sqrt(np.maximum(r("mag_edge"), 0) * np.maximum(r("grav_edge"), 0))
    geophys = rank01(geophys, valid)
    hydro = np.maximum(r("kth_anom"), r("thermal_density"))
    return {"scarp": scarp.astype(np.float32), "geophys": geophys, "hydro": hydro.astype(np.float32)}


def corroboration_gate(domains: dict[str, np.ndarray], valid: np.ndarray) -> np.ndarray:
    names = ("scarp", "geophys", "hydro")
    count = np.zeros(valid.shape, np.float32)
    for n in names:
        s = domains[n]
        pos = s[valid & (s > 0)]
        med = float(np.median(pos)) if pos.size else 0.5
        count += (s >= med).astype(np.float32)
    return (0.35 + 0.65 * (count / len(names))).astype(np.float32)


def road_factor(road_dist_m: np.ndarray, valid: np.ndarray) -> np.ndarray:
    return np.where(valid, np.clip(road_dist_m / 300.0, 0.15, 1.0), 0).astype(np.float32)
