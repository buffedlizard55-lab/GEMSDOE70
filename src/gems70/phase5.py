"""P5 preregistered cover-conditioned analytic-signal ranking; no label reads.

Pre-registration: docs/preregistration-p5.md. GeoDAWN/INGENIOUS names follow
owner-mirror TIFF descriptions; this class does not authenticate those sources.
The only catalogue-derived covariate is a *passed-in visible-only* distance.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

BANDS = {"tmi_hg": 3, "tmi_vg": 9, "iso_grav_anom": 13, "depth_to_base_surf": 15}
FEATURE_NAMES = (
    "log_abs_tmi_hg", "log_abs_tmi_vg", "log_analytic_amplitude",
    "magnetic_width_ratio", "log_gravity_gradient", "log_basement_depth",
)
CUTOFF = 0.98
OUTPUT_MAX = 0.99


def feature_valid(raw: dict[str, np.ndarray], footprint: np.ndarray) -> np.ndarray:
    """Joint raw-valid mask BEFORE nearest-neighbour fill and interior erosion."""
    if set(raw) != set(BANDS) or any(a.shape != footprint.shape for a in raw.values()):
        raise ValueError("all four raw bands on the footprint grid required")
    out = np.asarray(footprint, bool).copy()
    for a in raw.values():
        out &= np.isfinite(a) & (a > -1e30) & (a < 1e30)
    if not out.any():
        raise ValueError("no valid pixels")
    return out


def _fill_joint(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Fill from the *pre-erosion* joint valid raw domain, never from nodata."""
    a = np.asarray(a, np.float32)
    if valid.all():
        return a.copy()
    indexes = ndi.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return a[tuple(indexes)].astype(np.float32, copy=False)


def physics(raw: dict[str, np.ndarray], valid0: np.ndarray) -> dict[str, np.ndarray]:
    """Six fixed geophysical predictors; no catalogue and no SGMC input."""
    hg = _fill_joint(raw["tmi_hg"], valid0)
    vg = _fill_joint(raw["tmi_vg"], valid0)
    grad = np.hypot(hg, vg).astype(np.float32)
    with np.errstate(divide="raise", invalid="raise"):
        width = ndi.gaussian_filter(grad, 3.0) / (
            ndi.gaussian_filter(grad, 1.0) + np.float32(1e-3)
        )
    grav = _fill_joint(raw["iso_grav_anom"], valid0)
    g = ndi.gaussian_filter(grav, 2.0)
    gy, gx = np.gradient(g)
    dep = _fill_joint(raw["depth_to_base_surf"], valid0)
    features = dict(zip(FEATURE_NAMES, (
        np.log1p(np.abs(hg)), np.log1p(np.abs(vg)), np.log1p(grad),
        np.clip(width, 0.0, 3.0),
        np.log1p(np.hypot(gy, gx)), np.log1p(np.maximum(dep, 0.0)),
    )))
    for name, a in features.items():
        features[name] = np.asarray(a, np.float32)
        if not np.isfinite(features[name][valid0]).all():
            raise ValueError("nonfinite geophysical feature: " + name)
    return features


def visible_distance(visible: np.ndarray) -> np.ndarray:
    """Full EDT for the domain; clip to 32 only when gathering model features.

    Clipping before applying the 32-px halo boundary would silently include
    *all* pixels farther than 32 px — a leakage of the emission budget.
    """
    if visible.ndim != 2 or not visible.any():
        raise ValueError("nonempty visible catalogue required")
    return ndi.distance_transform_edt(~np.asarray(visible, bool)).astype(np.float32)


def domain(valid: np.ndarray, visible: np.ndarray, distance: np.ndarray) -> np.ndarray:
    """Clip source ranking to the preregistered 3..32 px off-visible halo."""
    return (np.asarray(valid, bool) & ~np.asarray(visible, bool) &
            (np.asarray(distance) >= 3.0) & (np.asarray(distance) <= 32.0))


def design(features: dict[str, np.ndarray], distance: np.ndarray, ids) -> np.ndarray:
    """Gather model covariates in frozen order without copying the full grid stack."""
    if tuple(features) != FEATURE_NAMES:
        raise ValueError("feature names/order mismatch")
    ids = np.asarray(ids)
    return np.column_stack([features[k].ravel()[ids] for k in FEATURE_NAMES] +
                           [np.minimum(distance.ravel()[ids], 32.0)]).astype(np.float32)


def rank_surface(predicted_scores: np.ndarray, allowed: np.ndarray) -> np.ndarray:
    """Mean-tie percentile rank over *only* allowed cells; 2% upper tail at <1.

    Ties retain their average rank; no implicit random tie break or floating
    point jitter can manufacture a candidate at a class boundary.
    """
    scores = np.asarray(predicted_scores)
    allowed = np.asarray(allowed, bool)
    if scores.shape != allowed.shape or not np.isfinite(scores[allowed]).all():
        raise ValueError("scores/allowed grid mismatch or nonfinite allowed scores")
    n = int(allowed.sum())
    if n <= 50:
        raise ValueError("insufficient allowed pixels")
    rank = rankdata(scores[allowed], method="average") / n
    out = np.zeros(scores.shape, np.float32)
    out[allowed] = (OUTPUT_MAX * np.maximum((rank - CUTOFF) / (1.0 - CUTOFF), 0)).astype(np.float32)
    # No binary-dot cells. Strictly below one by construction, not as a
    # uniqueness exemption; positive-support overlap is reported separately.
    if not np.isfinite(out).all() or (out < 0).any() or (out > OUTPUT_MAX + 1e-6).any():
        raise ValueError("invalid rank transform")
    return out
