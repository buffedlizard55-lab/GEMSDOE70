"""S3: supervised proxy-trained ranking with H33-matched spacing.

Registered in ``docs/preregistration-s3.md`` before the run. Design rules enforced here:

* SGMC (the proxy truth) is never read by any feature function in this module.
* Catalogue geometry is computed only from the catalogue mask passed in (the full catalogue
  for B'/production, the *visible* catalogue inside each instrument-A fold).
* Features are stored as float16 robust z-scores on the ``valid`` pixel list to fit in 3 GB;
  gradient boosting bins features, so a monotone rescaling does not change the model class.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

from .method import fill_nearest
from . import method_v2 as m2

STACK_NAMES = ('mag_anom', 'rtp', 'tmi_hg', 'geod_2ndinv', 'iso_grav_anom_slope', 'tc',
               'geod_shearrate', 'geod_dilaterate', 'tmi_vg', 'deq_n100a15',
               'iso_grav_anom_vg', 'det_elev', 'iso_grav_anom', 'tmi', 'depth_to_base_surf',
               'ieq_n100a15', 'cond_surf', 'iso_grav_anom_hg', 'det_elev_slope')
GRADIENT_OF = ('rtp', 'iso_grav_anom', 'depth_to_base_surf', 'det_elev', 'cond_surf', 'tmi')
AUX_FILES = ('lidar_scarp_features_u8.tif', 'geodawn_rad_u8.tif', 'geodawn_extensions_u8.tif',
             'topo_10m_derived_100m_u8.tif', 'dem10_chi_100m_u8.tif')
GEOMETRY_NAMES = ('cat_d', 'cat_logd', 'cat_tip_along', 'cat_tip_across', 'cat_density15',
                  'cat_density41', 'cat_host_loglen')

D_MIN = 2.4
NMS_RADIUS = 2.5        # blocks d <= 2.5 px -> minimum spacing 2*sqrt(2) px, H33's measured minimum
DOT_COUNT = 37654
HGB_PARAMS = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=63, min_samples_leaf=200,
                  l2_regularization=1.0, random_state=70)
NEG_RATIO = 6


def robust_z16(values):
    """Median/MAD z-score of a 1-D vector, clipped to +-50, float16; NaN preserved."""
    v = np.asarray(values, np.float64)
    good = np.isfinite(v)
    out = np.full(v.shape, np.nan, np.float16)
    if not good.any():
        return out
    med = np.median(v[good])
    mad = 1.4826 * np.median(np.abs(v[good] - med))
    if not np.isfinite(mad) or mad <= 0:
        mad = max(float(np.std(v[good])), 1e-9)
    out[good] = np.clip((v[good] - med) / mad, -50, 50).astype(np.float16)
    return out


def physics_matrix(features_tif, aux_dir, valid):
    """All catalogue-independent features on ``np.flatnonzero(valid)`` (float16 matrix)."""
    idx = np.flatnonzero(valid)
    cols, names = [], []
    with rasterio.open(features_tif) as src:
        if src.count != len(STACK_NAMES):
            raise ValueError('unexpected band count in training_features.tif')
        for b, name in enumerate(STACK_NAMES, start=1):
            a = src.read(b).astype(np.float32)
            bad = ~np.isfinite(a) | (np.abs(a) > 1e18)
            a[bad] = np.nan
            cols.append(robust_z16(a.ravel()[idx]))
            names.append('stack:' + name)
            if name in GRADIENT_OF:
                f = fill_nearest(np.where(valid & ~bad, a, np.nan)).astype(np.float32)
                gy, gx = np.gradient(ndi.gaussian_filter(f, 2.0))
                cols.append(robust_z16(np.hypot(gy, gx).ravel()[idx]))
                names.append('stack:grad_' + name)
                if name == 'det_elev':
                    m = ndi.uniform_filter(f, 5)
                    s = np.sqrt(np.maximum(ndi.uniform_filter(f * f, 5) - m * m, 0))
                    cols.append(robust_z16(s.ravel()[idx]))
                    names.append('stack:std5_det_elev')
                    del m, s
                del f, gy, gx
            del a, bad
    for fname in AUX_FILES:
        with rasterio.open(Path(aux_dir) / fname) as src:
            for b in range(1, src.count + 1):
                a = src.read(b).ravel()[idx].astype(np.float32)
                a[a == 0] = np.nan          # u8 encoding: 0 = nodata
                cols.append(robust_z16(a))
                names.append(f'aux:{fname.split("_u8")[0]}:{src.descriptions[b - 1] or b}')
    return np.stack(cols, axis=1), names


def geometry_matrix(catalogue, valid):
    """Catalogue-only geometry on ``np.flatnonzero(valid)``; also returns the distance map."""
    cat = np.asarray(catalogue, bool)
    idx = np.flatnonzero(valid)
    d, (iy, ix) = ndi.distance_transform_edt(~cat, return_indices=True)
    comp, n = ndi.label(cat, structure=np.ones((3, 3), bool))
    length = np.bincount(comp.ravel(), minlength=n + 1).astype(np.float64)
    host_len = np.log1p(length[comp[iy, ix]]).ravel()[idx]
    del comp, iy, ix
    u, v = m2.tip_kernels(cat, cat.shape)
    along = np.clip(u, -200, 200).ravel()[idx]
    across = np.clip(np.abs(v), 0, 200).ravel()[idx]
    del u, v
    cf = cat.astype(np.float32)
    dens15 = ndi.uniform_filter(cf, 15).ravel()[idx]
    dens41 = ndi.uniform_filter(cf, 41).ravel()[idx]
    dv = d.ravel()[idx]
    cols = [dv, np.log1p(dv), along, across, dens15, dens41, host_len]
    mat = np.stack([robust_z16(c) if k not in (0, 1) else np.asarray(c, np.float16)
                    for k, c in enumerate(cols)], axis=1)
    # distance kept in raw px (<=~400, float16-exact to 0.25 px) for readability of receipts
    return mat, list(GEOMETRY_NAMES), d.astype(np.float32)


def rank_within(score, groups, mask):
    """Percentile rank (0,1] of ``score`` inside each group id, restricted to ``mask``."""
    out = np.zeros(score.shape, np.float32)
    for gid in np.unique(groups[mask]):
        sel = mask & (groups == gid)
        r = rankdata(score[sel], method='average')
        out[sel] = (r / r.size).astype(np.float32)
    return out


def place(score, allowed, n=DOT_COUNT, radius=NMS_RADIUS):
    dots, picked = m2.place_dots(score, allowed, n=n, radius_px=radius)
    if picked != n:
        raise RuntimeError(f'placed {picked} dots, expected {n}')
    return dots


# ----------------------------- S3-E2: marginal-matched placement -----------------------------
DIST_EDGES_E2 = (2.4, 3, 4, 6, 10, 15, 20, 30, 45, 60, 100, np.inf)


def strata_map(d, slope_u8, domain):
    """Stratum id = distance band (11) x slope class (0 = missing, 1..4 = domain quartiles)."""
    db = np.digitize(d, DIST_EDGES_E2[1:-1])            # 0..10 for d >= 2.4
    s = np.asarray(slope_u8)
    present = domain & (s > 0)
    qs = np.percentile(s[present], [25, 50, 75])
    sc = np.where(s > 0, 1 + np.digitize(s, qs, right=True), 0)
    sid = (db * 5 + sc).astype(np.int16)
    return np.where(domain, sid, -1).astype(np.int16), [float(q) for q in qs]


def quotas_from_reference(sid, ref_dots, n=DOT_COUNT, n_strata=55):
    """Reference counts per stratum (positions discarded), scaled to n by largest remainder."""
    ids = sid[np.asarray(ref_dots, bool) & (sid >= 0)]
    counts = np.bincount(ids, minlength=n_strata).astype(np.float64)
    raw = counts / counts.sum() * n
    q = np.floor(raw).astype(np.int64)
    rem = n - int(q.sum())
    q[np.argsort(-(raw - q), kind='stable')[:rem]] += 1
    return q


def place_quota(score, sid, quota, radius=NMS_RADIUS, order=None):
    """Greedy pass in descending score (or a given order), stratum quotas + NMS radius."""
    h, w = sid.shape
    if order is None:
        flat = np.flatnonzero((sid >= 0) & (score > 0))
        order = flat[np.argsort(score.ravel()[flat], kind='stable')[::-1]]
    left = np.asarray(quota, np.int64).copy()
    r = int(np.ceil(radius))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (yy * yy + xx * xx) <= radius * radius
    blocked = np.zeros((h, w), bool)
    dots = np.zeros((h, w), bool)
    sflat = sid.ravel()
    need = int(left.sum())
    for p in order:
        s = sflat[p]
        if s < 0 or left[s] <= 0:
            continue
        y, x = divmod(int(p), w)
        if blocked[y, x]:
            continue
        dots[y, x] = True
        left[s] -= 1
        need -= 1
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        blocked[y0:y1, x0:x1] |= disk[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)]
        if need == 0:
            break
    return dots, int(left.sum())
