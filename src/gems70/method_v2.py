"""
Discordance-corridor hypothesis for blind normal-fault detection.

Geological target: Blind Basin-and-Range normal faults beneath alluvial cover.
In the Great Basin, ~32% of geothermal systems occupy fault step-overs/relay ramps,
~25% fault terminations, ~22% fault intersections (Faulds et al. 2015 GRC;
Faulds & Hinz 2015; Giddens et al. 2025 Stanford Geothermal Workshop). Many are
blind: Quaternary alluvium buries the scarp while gravity and basement offsets
persist. A fault missing from the USGS SGMC/QFaults catalogue is plausible where
a gravity/b basement lineament exists but detrended topographic scarp does not.

Physical signature:
- Isostatic gravity anomaly (iso_grav_anom) and its horizontal gradient
  (iso_grav_anom_hg) mark lateral density contrast across a basin-bounding fault.
  Source: USGS GeoDAWN compilation (Glen & Earney 2024, DOI 10.5066/P93LGLVQ)
  https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- Depth-to-basement (depth_to_base_surf) gradient marks sedimentary thickness step.
- Detrended elevation slope (det_elev_slope) marks topographic scarp. Discordance
  = gravity/basement structure without topographic expression.
- Reduced-to-pole magnetic anomaly (rtp) and its edge termination along the
  gravity tangent distinguishes fault truncation from intrusive/dike contact
  (magnetic susceptibility vs density). Dike terminations and lithologic contacts
  are the named non-fault mimics (see hypotheses.md).

Layers involved: bands 2 (rtp), 13 (iso_grav_anom), 15 (depth_to_base_surf),
12 (det_elev), 19 (det_elev_slope), 18 (iso_grav_anom_hg), 3 (tmi_hg), 14 (tmi)

Transform: rank-normalized gradient magnitudes, discordance product, Hessian ridge
strength, non-maximum suppression, morphological thinning, catalogue-distance pruning.
This differs from H33 (catalogue-flank pruning of prior dots) and from H70-v1
(contact-termination along gravity normal) by explicitly targeting
topography-vs-subsurface discordance.

Implementation cost: Low (all bands in cached 19-band stack), CPU-only,
100 m grid, Gaussian derivatives, skimage skeletonization.
"""

from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

# reuse helpers from method.py lineage (no catalogue leak)


def rank01(values, valid):
    a = np.asarray(values)
    valid = np.asarray(valid, bool) & np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    n = int(valid.sum())
    if n > 1:
        out[valid] = (rankdata(a[valid], method="average") - 1) / (n - 1)
    return out


def fill_nearest(a):
    good = np.isfinite(a)
    if not good.any():
        raise ValueError("empty finite feature")
    indices = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return a[tuple(indices)]


def _grad_mag(arr, sigma):
    """Gaussian-smoothed gradient magnitude."""
    s = ndi.gaussian_filter(arr, sigma, mode="nearest")
    gy, gx = np.gradient(s)
    return np.hypot(gy, gx)


def physical_features_v2(bands, valid):
    """
    bands: dict with keys rtp, iso_grav_anom, depth_to_base, det_elev, det_elev_slope,
           iso_grav_hg, tmi_hg, tmi, mag_anom etc. as float32 arrays (NaN outside valid)
    valid: bool footprint interior (eroded 12px to guard filter boundaries)
    No catalogue read here.
    """
    # Fill NaN via nearest to avoid edge artifacts before filtering
    filled = {k: fill_nearest(np.where(valid, v, np.nan)) for k, v in bands.items()}

    # Gravity edge: iso_grav_anom gradient (basin scale) + its horizontal gradient band
    # Use both: gradient of iso_grav_anom (sigma 3 = 300 m, matches DTI kernel radius)
    grav_edge = _grad_mag(filled["iso_grav_anom"], sigma=3)
    # Augment with precomputed iso_grav_anom_hg as independent check
    grav_edge = 0.6 * grav_edge + 0.4 * ndi.gaussian_filter(np.abs(filled["iso_grav_hg"]), sigma=2)

    # Basement gradient: depth_to_base_surf step (sigma 3)
    base_grad = _grad_mag(filled["depth_to_base"], sigma=3)

    # Topographic scarp: det_elev_slope (already slope) + gradient of det_elev
    topo_scarp = ndi.gaussian_filter(np.abs(filled["det_elev_slope"]), sigma=1)
    topo_scarp = np.maximum(topo_scarp, _grad_mag(filled["det_elev"], sigma=1))

    # Magnetic edge magnitude (sigma1 gradient, sigma2 amplitude smoothing) - for termination
    rtp = filled["rtp"]
    my, mx = np.gradient(ndi.gaussian_filter(rtp, 1))
    mag_edge_amp = ndi.gaussian_filter(np.hypot(my, mx), 2)
    # Gravity normal/tangent for along-strike derivative
    g_smooth = ndi.gaussian_filter(filled["iso_grav_anom"], 3)
    gy, gx = np.gradient(g_smooth)
    edge = np.hypot(gy, gx)
    ny = np.divide(gy, edge, out=np.zeros_like(gy), where=edge > 0)
    nx = np.divide(gx, edge, out=np.zeros_like(gx), where=edge > 0)
    ay, ax = np.gradient(mag_edge_amp)
    termination = np.abs(-nx * ay + ny * ax)  # along-tangent change

    # Basement normal projection onto gravity normal (validates supported boundary)
    by, bx = np.gradient(ndi.gaussian_filter(filled["depth_to_base"], 3))
    basement_normal = np.abs(ny * by + nx * bx)

    return {
        "grav_edge": np.where(valid, grav_edge, 0).astype(np.float32),
        "base_grad": np.where(valid, base_grad, 0).astype(np.float32),
        "topo_scarp": np.where(valid, topo_scarp, 0).astype(np.float32),
        "termination": np.where(valid, termination, 0).astype(np.float32),
        "basement_normal": np.where(valid, basement_normal, 0).astype(np.float32),
        "mag_edge_amp": np.where(valid, mag_edge_amp, 0).astype(np.float32),
    }


def hessian_ridge_strength(field, valid, sigma=1.0):
    """
    Ridge strength from Hessian eigenvalues (Frangi-like).
    field: smoothed discordance field
    Returns positive ridge measure where structure is line-like and negative curvature.
    """
    # Fill to handle borders
    arr = fill_nearest(np.where(valid, field, np.nan))
    arr = ndi.gaussian_filter(arr, sigma)
    # Second derivatives
    gy, gx = np.gradient(arr)
    gyy, gyx = np.gradient(gy)
    gxy, gxx = np.gradient(gx)
    # Hessian [[gxx, gxy],[gyx, gyy]] ; for each pixel eigenvalues
    # Compute analytically: eig = 0.5*(trace +/- sqrt(trace^2 -4*det))
    trace = gxx + gyy
    det = gxx * gyy - gxy * gyx
    disc = np.maximum(trace*trace - 4*det, 0)
    sqrt_disc = np.sqrt(disc)
    eig1 = 0.5 * (trace + sqrt_disc)
    eig2 = 0.5 * (trace - sqrt_disc)
    # Ridge: one eigenvalue large negative, other small => |eig2| >> |eig1| and eig2<0
    # Use vesselness-like: ridge = -eig2 * (|eig2|/|eig1|)
    # Avoid division by zero
    ridge = np.zeros_like(eig2)
    mask = (eig2 < 0) & valid
    # Normalized anisotropy
    abs_eig1 = np.abs(eig1) + 1e-9
    abs_eig2 = np.abs(eig2) + 1e-9
    anisotropy = abs_eig2 / abs_eig1
    # Ridge strength high when strongly anisotropic and negative
    ridge[mask] = (-eig2[mask]) * np.clip(anisotropy[mask] / 10.0, 0, 1)
    return ridge.astype(np.float32)


def discordance_score(features, valid):
    """
    Geometric mean of ranked gravity/basement edges weighted by topographic suppression.
    Returns rank01 field in [0,1].
    """
    # Rank each
    r_grav = rank01(features["grav_edge"], valid)
    r_base = rank01(features["base_grad"], valid)
    r_topo = rank01(features["topo_scarp"], valid)
    r_term = rank01(features["termination"], valid)

    # Discordance: high where gravity & basement strong, topography weak
    # Use 1 - topo_rank as suppression (avoid division by zero)
    topo_suppress = 1.0 - r_topo  # in [0,1]
    # Combine gravity & basement via geometric mean, then weight by topo suppress
    # Add small epsilon to keep finite
    combined = (r_grav * r_base) ** 0.5 * (0.3 + 0.7 * topo_suppress)
    # Weight by basement_normal (gravity-supported) and termination (fault vs dike)
    r_bn = rank01(features["basement_normal"], valid)
    # Final discordance rank
    disc = rank01(combined * (0.5 + 0.5 * r_bn) * (0.6 + 0.4 * r_term), valid)
    return disc


def skeleton_from_ridge(ridge, valid, percentile=85):
    """
    Threshold ridge strength to top percentile, then skeletonize to 1-px lines.
    Uses skimage.morphology.skeletonize (Lee et al. algorithm).
    """
    from skimage.morphology import skeletonize

    # Must be binary
    thresh = np.percentile(ridge[valid], percentile)
    binary = (ridge > thresh) & valid
    # Remove tiny specks: opening with small disk, then keep elongated.
    # Label components, drop those with <50 pixels or low eccentricity via moments
    labeled, nlab = ndi.label(binary)
    if nlab == 0:
        return np.zeros_like(binary, dtype=bool)
    sizes = np.bincount(labeled.ravel())
    # Filter by size and thinness: keep components >30 px, compute axis lengths via bbox
    keep = np.zeros_like(binary, dtype=bool)
    for lab in range(1, nlab+1):
        if sizes[lab] < 30:
            continue
        # Bounding box aspect ratio as proxy for elongation
        ys, xs = np.where(labeled == lab)
        h = ys.max() - ys.min() + 1
        w = xs.max() - xs.min() + 1
        aspect = max(h, w) / (min(h, w) + 1e-9)
        # Keep if aspect >2 or size >100 (allow moderately compact but not specks)
        if aspect > 2.0 or sizes[lab] > 100:
            keep[labeled == lab] = True

    # Skeletonize remaining thick ridges to 1-px lines
    # skeletonize expects bool, returns bool 1-px skeleton
    skeleton = skeletonize(keep)

    # Prune short spurs (<15 px) by re-labeling skeleton segments?
    # Use sequential pruning: iteratively remove endpoints with 1 neighbor until stable
    # Count neighbors via 3x3 convolution
    skel = skeleton & valid
    # Iterative pruning of endpoints
    for _ in range(3):  # light pruning cycles
        neigh = ndi.convolve(skel.astype(np.uint8), np.ones((3,3), dtype=int), mode="constant") - 1
        endpoints = skel & (neigh == 1)
        # Don't prune if endpoint is junction-adjacent? simple: remove isolated endpoints with no branching nearby
        # Instead, remove endpoints that are spurs shorter than pruning iterations
        # Find branch points
        branch = skel & (neigh > 2)
        # Dilate branch points to protect
        protected = ndi.binary_dilation(branch, structure=np.ones((3,3)))
        removable = endpoints & ~protected
        if not removable.any():
            break
        skel[removable] = False
        # Reconnect after pruning? No, just shrink
    return skel


def dots_from_skeleton(skeleton, valid, catalogue, distance_px=3, target_count=37654, rng_seed=70020):
    """
    Convert skeleton to dots with catalogue-distance pruning and target count control.
    - skeleton: bool 1-px lines
    - catalogue: bool mapped faults
    - distance_px: minimum distance from catalogue (H33 used >2, we use 3 = 300m)
    - target_count: desired dots (H33 B2 = 37654)
    Returns binary prediction (0/1) float32 in [0,1], zero outside footprint and on catalogue.
    """
    # Distance to catalogue
    # Invert catalogue to get distance outside
    cat_dist = ndi.distance_transform_edt(~catalogue)
    # Also distance to footprint edge? Already zero outside valid
    # Prune skeleton near catalogue
    pruned = skeleton & (cat_dist > distance_px) & valid
    # Ensure zero on catalogue (already)
    pruned = pruned & ~catalogue

    # Skeleton already sparse but may have >target_count. If so, subsample along strike
    # to preserve spatial distribution: random sample without replacement, stratified by quadrants
    count = int(pruned.sum())
    if count <= target_count:
        # If too few, dilate slightly to add nearby ridge pixels? Instead, fallback: take additional thresholded discordance points
        # But for now just return pruned (honest count)
        pred = np.zeros(valid.shape, dtype=np.float32)
        pred[pruned] = 1.0
        return pred, count

    # Subsample to target: use deterministic RNG, preserve elongated structures by sampling per component
    rng = np.random.default_rng(rng_seed)
    # Compute per-component quota proportional to length
    labeled, nlab = ndi.label(pruned)
    sizes = np.bincount(labeled.ravel())[1:]  # skip 0
    # Sample indices
    all_y, all_x = np.where(pruned)
    # If many labs, sample proportionally
    # Simpler: uniform random sample across all skeleton pixels (preserves geometry on average)
    keep_idx = rng.choice(count, size=target_count, replace=False)
    sampled = np.zeros_like(pruned)
    sampled[all_y[keep_idx], all_x[keep_idx]] = True

    pred = np.zeros(valid.shape, dtype=np.float32)
    pred[sampled] = 1.0
    return pred, target_count


def upper_surface_ranks(ranks, valid, cutoff=0.95):
    """Legacy continuous surface for holdout comparison (not final dots)."""
    if not 0 <= cutoff < 1:
        raise ValueError("invalid cutoff")
    return np.where(valid, np.maximum(ranks - cutoff, 0) / (1 - cutoff), 0).astype(np.float32)
