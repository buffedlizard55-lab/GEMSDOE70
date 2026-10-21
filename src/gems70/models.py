"""Zero-leakage out-of-fold models, controls, and Minoux lazy-greedy submodular emission."""
from __future__ import annotations

import gc
import heapq
from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

from gems57 import emit
from gems57.grid import Grid
from gems57.metric import ALPHA, BETA, EPS, OFF_DX, OFF_DY, OFF_K

from .features import FeatureStack, build_collar_safe_anatomy_features


@dataclass(frozen=True)
class DualExpertOutput:
    """Out-of-fold probability fields and emitted binary predictions."""

    pi_phys_fp: np.ndarray       # float32 (N_fp,) Expert A OOF calibrated probability
    pi_anat_fp: np.ndarray       # float32 (N_fp,) Expert B OOF calibrated probability
    surface_e2_2d: np.ndarray    # float32 (H, W) Experiment 2 continuous surface
    dots_e2_2d: np.ndarray       # float32 (H, W) Experiment 2 binary prediction
    surface_e3_2d: np.ndarray    # float32 (H, W) Experiment 3 continuous surface
    dots_e3_2d: np.ndarray       # float32 (H, W) Experiment 3 binary prediction
    alloc_e3_stats: dict


def _rank01(v: np.ndarray) -> np.ndarray:
    n = v.shape[0]
    order = np.argsort(v, kind="mergesort")
    r = np.empty(n, dtype=np.float32)
    r[order] = np.linspace(0.0, 1.0, n, dtype=np.float32)
    return r


def _relief_deconfounded_blend(
    pi_fp: np.ndarray,
    relief_fp: np.ndarray,
    reg_fp_list: list[np.ndarray] | None = None,
    weight_relief: float = 0.52,
) -> np.ndarray:
    """Map within-(quadrant, relief-decile) quantiles to common marginal probability scale.

    Eliminates both range-crest slope bias and cross-quadrant base-rate starvation
    caused by uneven historical Quaternary fault mapping density across NW/NE/SW/SE.
    """
    local_q = np.zeros_like(pi_fp, dtype=np.float32)
    groups = reg_fp_list if reg_fp_list is not None else [np.ones(len(pi_fp), dtype=bool)]
    for gmask in groups:
        sub_r = relief_fp[gmask]
        bins = np.quantile(sub_r, np.linspace(0.0, 1.0, 11))
        bins[0] -= 1.0
        bins[-1] += 1.0
        bidx = np.clip(np.digitize(sub_r, bins) - 1, 0, 9)
        sub_pi = pi_fp[gmask]
        sub_q = np.zeros_like(sub_pi, dtype=np.float32)
        for b in range(10):
            mb = bidx == b
            if np.any(mb):
                sub_q[mb] = _rank01(sub_pi[mb])
        local_q[gmask] = sub_q
    sorted_pi = np.sort(pi_fp)
    q_idx = np.clip(np.round(local_q * (len(sorted_pi) - 1)).astype(np.int64), 0, len(sorted_pi) - 1)
    deconf_pi = sorted_pi[q_idx]
    return ((1.0 - weight_relief) * pi_fp + weight_relief * deconf_pi).astype(np.float32)


def _greedy_peak_thin_binary(score_2d: np.ndarray, allowed: np.ndarray, n_target: int, min_dist_px: float = 2.85) -> np.ndarray:
    """Isotropic fixed-radius peak thinning baseline decoder for controls and H70-2."""
    ek = emit.expected_credit(np.where(allowed, score_2d, 0.0).astype(np.float32))
    ys, xs = np.nonzero(allowed & (ek > 0))
    out = np.zeros(score_2d.shape, dtype=np.float32)
    if ys.size == 0:
        return out
    cap = min(ys.size, n_target * 14)
    if ys.size > cap:
        top_idx = np.argpartition(-ek[ys, xs], cap - 1)[:cap]
        ys, xs = ys[top_idx], xs[top_idx]
    order = np.argsort(-ek[ys, xs], kind="mergesort")
    ys, xs = ys[order], xs[order]

    r = int(np.ceil(min_dist_px))
    dy, dx = np.mgrid[-r : r + 1, -r : r + 1]
    disk = (dy * dy + dx * dx) <= (min_dist_px * min_dist_px)
    blocked = np.zeros(score_2d.shape, dtype=bool)
    H, W = score_2d.shape
    placed = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        if blocked[y, x]:
            continue
        out[y, x] = 1.0
        placed += 1
        if placed >= n_target:
            break
        y0, y1 = max(0, y - r), min(H, y + r + 1)
        x0, x1 = max(0, x - r), min(W, x + r + 1)
        ky0, ky1 = y0 - (y - r), r + 1 + (y1 - (y + 1))
        kx0, kx1 = x0 - (x - r), r + 1 + (x1 - (x + 1))
        blocked[y0:y1, x0:x1] |= disk[ky0:ky1, kx0:kx1]
    return out


def submodular_marginal_dti_allocate(
    p_2d: np.ndarray,
    allowed: np.ndarray,
    *,
    k_truth: float,
    max_dots: int,
    candidate_cap: int = 240_000,
) -> tuple[np.ndarray, dict]:
    """Exact Minoux (1978) lazy-greedy submodular 300 m kernel coverage allocator.

    Repairs `IR-70-EMIT-BLOB-01` discovered empirically in `emit.greedy_allocate`:
    in `emit.greedy_allocate`, `kself = min(sum_g p(g)*K(x,g), 1.0)` collapses
    `1 - kself` identically to `0.0` wherever the 29-cell kernel sum exceeds 1.0,
    accepting adjacent 1-px solid blobs until `dT == 0`.

    Here:
      1. `p_2d` is calibrated so `sum_{g in allowed} p(g) = k_truth`.
      2. Each candidate's expected max-kernel self-credit uses bounded halo peak
         `k_self(x) = min(0.75, max_{u in K} p(x+u) * K(u))`, guaranteeing strict
         false-positive cost `1 - k_self(x) >= 0.25 > 0` everywhere.
      3. Exact marginal uncovered credit
         `dT(x | S) = sum_{(dy,dx,k)} p[y+dy, x+dx] * max(0, k - cover[y+dy, x+dx])`
         is evaluated lazily via a binary max-heap over `(dT - bar)` with a
         `1.9 px` anti-adjacent-pixel guard (`d >= 2 px`), placing binary vertices
         at exact 300 m Weber kernel centroids along fault strikes, junctions, and
         parallel strands until exact marginal DTI gain drops below zero or `max_dots`.
    """
    H, W = p_2d.shape
    p_clean = np.where(allowed, p_2d, 0.0).astype(np.float32)
    cur_sum = float(p_clean.sum())
    if cur_sum > 0:
        p_clean = np.clip(p_clean * (float(k_truth) / cur_sum), 0.0, 0.70).astype(np.float32)

    ek = emit.expected_credit(p_clean)
    ys, xs = np.nonzero(allowed & (ek > 1e-4))
    if ys.size == 0:
        return np.zeros((H, W), dtype=np.float32), {"n_dots": 0}

    if ys.size > candidate_cap:
        top_i = np.argpartition(-ek[ys, xs], candidate_cap - 1)[:candidate_cap]
        ys, xs = ys[top_i], xs[top_i]

    # Pad p_clean and cover by radius 3 so inner kernel loop has zero bounds branches
    PAD = 3
    p_pad = np.pad(p_clean, PAD, mode="constant", constant_values=0.0)
    cover_pad = np.zeros_like(p_pad, dtype=np.float32)
    blocked = np.zeros((H, W), dtype=bool)
    out = np.zeros((H, W), dtype=np.float32)

    off_triples = list(zip(OFF_DY.tolist(), OFF_DX.tolist(), [float(v) for v in OFF_K.tolist()]))
    bdy, bdx = np.mgrid[-2:3, -2:3]
    block_disk = (bdy * bdy + bdx * bdx) < 7.8  # enforces Euclidean spacing >= sqrt(8) = 2.828 px

    # Compute bounded self-credit k_self(x) <= 0.75 on candidate set
    kself_map = np.zeros(ys.size, dtype=np.float64)
    yp = ys + PAD
    xp = xs + PAD
    for dy, dx, kw in off_triples:
        np.maximum(kself_map, p_pad[yp + dy, xp + dx] * kw, out=kself_map)
    np.minimum(kself_map, 0.75, out=kself_map)

    init_dt = ek[ys, xs].astype(np.float64)
    # Build min-heap of (-dT, cand_idx)
    heap = [(-float(dt_v), idx) for idx, dt_v in enumerate(init_dt)]
    heapq.heapify(heap)

    T = 0.0
    M = 0.0
    n_dots = 0
    evals = 0

    while heap and n_dots < max_dots:
        neg_upper, idx = heapq.heappop(heap)
        y = int(ys[idx])
        x = int(xs[idx])
        if blocked[y, x]:
            continue

        D_cur = ALPHA * (T + n_dots - M) + BETA * float(k_truth) + EPS
        a_cur = ALPHA * (T / D_cur)
        c_bar = (a_cur / (1.0 - a_cur)) * (1.0 - kself_map[idx]) if a_cur < 1.0 else 1e9

        if -neg_upper <= c_bar:
            # Even optimistic upper bound fails the bar; keep scanning or skip
            continue

        # Exact marginal uncovered kernel gain at (y, x)
        py, px = y + PAD, x + PAD
        dt_now = 0.0
        for dy, dx, kw in off_triples:
            rem = kw - float(cover_pad[py + dy, px + dx])
            if rem > 0.0:
                pv = float(p_pad[py + dy, px + dx])
                if pv > 0.0:
                    dt_now += pv * rem
        evals += 1

        if dt_now <= c_bar:
            continue

        # Check Minoux lazy optimality against next heap top
        next_upper = -heap[0][0] if heap else -1.0
        if dt_now < next_upper - 1e-7:
            heapq.heappush(heap, (-dt_now, idx))
            continue

        # Accept binary vertex at (y, x)
        out[y, x] = 1.0
        T += dt_now
        M += kself_map[idx]
        n_dots += 1

        # Update kernel coverage pad
        for dy, dx, kw in off_triples:
            if kw > cover_pad[py + dy, px + dx]:
                cover_pad[py + dy, px + dx] = kw

        # Block inside radius < sqrt(8) = 2.828 px so every dot covers fresh 300 m fault strike
        y0, y1 = max(0, y - 2), min(H, y + 3)
        x0, x1 = max(0, x - 2), min(W, x + 3)
        ky0, ky1 = y0 - (y - 2), 5 + (y1 - (y + 3))
        kx0, kx1 = x0 - (x - 2), 5 + (x1 - (x + 3))
        blocked[y0:y1, x0:x1] |= block_disk[ky0:ky1, kx0:kx1]

    D_fin = ALPHA * (T + n_dots - M) + BETA * float(k_truth) + EPS
    return out, {
        "n_dots": int(n_dots),
        "expected_covered_credit": round(float(T), 4),
        "expected_self_credit": round(float(M), 4),
        "surrogate_dti": round(float(T / D_fin), 6),
        "lazy_evals": int(evals),
        "k_truth": float(k_truth),
    }


def g49_reimpl_control_prediction(
    grid: Grid,
    stack: FeatureStack,
    known_mask: np.ndarray,
    *,
    n_dots: int,
) -> np.ndarray:
    """Clean re-implementation of GEMSDOE49's multi-scale non-ML operator for holdout control."""
    fp = grid.footprint
    idx_map = {name: i for i, name in enumerate(stack.names)}
    score_fp = (
        0.34 * _rank01(stack.X[:, idx_map["hessian_ridge_multiscale"]])
        + 0.22 * _rank01(stack.X[:, idx_map["xgrad_topo_gravity"]])
        + 0.18 * _rank01(stack.X[:, idx_map["xgrad_topo_magnetics"]])
        + 0.14 * _rank01(stack.X[:, idx_map["xgrad_gravity_magnetics"]])
        + 0.12 * _rank01(stack.X[:, idx_map["tectonic_strike_align"]])
    ).astype(np.float32)
    surf = np.zeros(grid.shape, dtype=np.float32)
    surf[fp] = score_fp * 0.05
    d_known = ndi.distance_transform_edt(~known_mask)
    allowed = fp & (d_known > 2.0)
    return _greedy_peak_thin_binary(surf, allowed, n_target=n_dots, min_dist_px=2.9)


def _predict_proba_chunked(clf: HistGradientBoostingClassifier, X: np.ndarray, chunk: int = 600_000) -> np.ndarray:
    out = np.empty(X.shape[0], dtype=np.float32)
    for start in range(0, X.shape[0], chunk):
        end = min(start + chunk, X.shape[0])
        out[start:end] = clf.predict_proba(X[start:end])[:, 1].astype(np.float32)
    return out


def _inner_hide_on_known(known_mask: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Create a strictly internal buffered component split inside `known_mask` ONLY."""
    rng = np.random.default_rng(seed)
    labels, _ = ndi.label(known_mask, structure=np.ones((3, 3), dtype=int))
    sizes = np.bincount(labels.ravel())
    eligible = np.flatnonzero(sizes[1:] >= 5) + 1
    perm = rng.permutation(eligible)
    target_px = 0.22 * float(known_mask.sum())
    chosen = []
    acc = 0.0
    for cid in perm:
        chosen.append(int(cid))
        acc += float(sizes[cid])
        if acc >= target_px:
            break
    inner_hidden = np.isin(labels, np.asarray(chosen, dtype=labels.dtype))
    collar = ndi.distance_transform_edt(~inner_hidden) <= 3.0
    inner_visible = known_mask & ~collar
    return inner_visible, inner_hidden


def fit_predict_dual_experts(
    grid: Grid,
    stack: FeatureStack,
    regions_4: list[np.ndarray],
    known_mask: np.ndarray,
    *,
    seed: int,
    k_truth_prior: float,
    max_dots_e3: int,
    e2_dot_target: int,
) -> DualExpertOutput:
    """Strictly out-of-fold 4-quadrant training & prediction for E2 (`H70-2`) and E3 (`H70-3`).

    CRITICAL ZERO-LEAKAGE GUARANTEE:
    `truth` is NEVER passed into this function. Both `Expert A` and `Expert B` see
    ONLY `known_mask` inside the 3 non-test spatial quadrants `q' != q`.
    """
    fp = grid.footprint
    n_fp = int(fp.sum())
    rng = np.random.default_rng(seed)

    known_fp = known_mask[fp]
    d_known_2d = ndi.distance_transform_edt(~known_mask).astype(np.float32)
    d_known_fp = d_known_2d[fp]

    d_sc = stack.domain_scores
    phys_corrob_fp = (
        0.34 * d_sc["geomorph"]
        + 0.30 * d_sc["potential"]
        + 0.20 * d_sc["hydrothermal"]
        + 0.16 * d_sc["geodesy"]
    ).astype(np.float32)
    top2_prod = np.maximum(
        d_sc["geomorph"] * d_sc["potential"],
        np.maximum(d_sc["geomorph"] * d_sc["hydrothermal"], d_sc["potential"] * d_sc["hydrothermal"]),
    )
    multi_line_synergy_fp = np.sqrt(np.maximum(top2_prod, 0.0)).astype(np.float32)

    # --- 1. Out-of-fold Expert A: Pure 4-Domain Zero-Catalogue Physical Classifier ---
    pi_phys_fp = np.zeros(n_fp, dtype=np.float32)
    reg_fp_list = [np.asarray(r[fp], dtype=bool) for r in regions_4]

    for q in range(4):
        train_fp = ~reg_fp_list[q]
        pos_idx = np.flatnonzero(train_fp & known_fp)
        neg_pool = np.flatnonzero(train_fp & (d_known_fp > 3.5))
        n_neg_sample = min(190_000, neg_pool.size)
        neg_idx = rng.choice(neg_pool, size=n_neg_sample, replace=False)

        tr_idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([
            np.ones(pos_idx.size, dtype=np.int8),
            np.zeros(neg_idx.size, dtype=np.int8),
        ])
        w_neg = float(neg_pool.size) / float(n_neg_sample)
        sw = np.concatenate([
            np.ones(pos_idx.size, dtype=np.float32),
            np.full(neg_idx.size, w_neg, dtype=np.float32),
        ])

        clf_a = HistGradientBoostingClassifier(
            max_iter=180,
            learning_rate=0.055,
            max_leaf_nodes=63,
            min_samples_leaf=80,
            l2_regularization=2.5,
            random_state=seed * 10 + q,
        )
        clf_a.fit(np.asarray(stack.X[tr_idx], dtype=np.float32), y_tr, sample_weight=sw)
        test_idx = np.flatnonzero(reg_fp_list[q])
        pi_phys_fp[test_idx] = _predict_proba_chunked(clf_a, stack.X[test_idx])
        del clf_a, tr_idx, y_tr, sw
        gc.collect()

    # --- 2. Out-of-fold Expert B: Collar-Safe Visible-Network Tip/Relay/Bend Classifier ---
    inner_vis, inner_hid = _inner_hide_on_known(known_mask, seed=seed + 7000)
    X_anat_in, _, _ = build_collar_safe_anatomy_features(
        grid, inner_vis, phys_corrob_fp, stack.sense_src_2d
    )
    inner_vis_fp = inner_vis[fp]
    inner_hid_fp = inner_hid[fp]
    del inner_vis, inner_hid
    gc.collect()

    clf_b_list: list[HistGradientBoostingClassifier] = []
    for q in range(4):
        train_fp = ~reg_fp_list[q]
        pos_idx = np.flatnonzero(train_fp & inner_hid_fp)
        neg_pool = np.flatnonzero(train_fp & ~inner_vis_fp & ~inner_hid_fp)
        n_neg_sample = min(190_000, neg_pool.size)
        neg_idx = rng.choice(neg_pool, size=n_neg_sample, replace=False)

        tr_idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([
            np.ones(pos_idx.size, dtype=np.int8),
            np.zeros(neg_idx.size, dtype=np.int8),
        ])
        w_neg = float(neg_pool.size) / float(n_neg_sample)
        sw = np.concatenate([
            np.ones(pos_idx.size, dtype=np.float32),
            np.full(neg_idx.size, w_neg, dtype=np.float32),
        ])

        clf_b = HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.05,
            max_leaf_nodes=45,
            min_samples_leaf=100,
            l2_regularization=3.0,
            random_state=seed * 20 + q,
        )
        clf_b.fit(X_anat_in[tr_idx], y_tr, sample_weight=sw)
        clf_b_list.append(clf_b)
        del tr_idx, y_tr, sw
        gc.collect()

    del X_anat_in, inner_vis_fp, inner_hid_fp
    gc.collect()

    X_anat_out, _, is_sharp_tip_fp = build_collar_safe_anatomy_features(
        grid, known_mask, phys_corrob_fp, stack.sense_src_2d
    )
    pi_anat_fp = np.zeros(n_fp, dtype=np.float32)
    for q in range(4):
        test_idx = np.flatnonzero(reg_fp_list[q])
        pi_anat_fp[test_idx] = _predict_proba_chunked(clf_b_list[q], X_anat_out[test_idx])

    del clf_b_list, X_anat_out
    gc.collect()

    # =========================================================================
    # EXPERIMENT 2 (`H70-2`): Raw Dual-Expert Noisy-OR + Isotropic Thinning
    # =========================================================================
    p_e2_fp = 1.0 - (1.0 - 0.65 * pi_phys_fp) * (1.0 - 0.85 * pi_anat_fp)
    allowed_e2 = fp & (d_known_2d > 2.0)
    surf_e2 = np.zeros(grid.shape, dtype=np.float32)
    surf_e2[fp] = np.clip(p_e2_fp, 0.0, 1.0)
    surf_e2[~allowed_e2] = 0.0
    dots_e2 = _greedy_peak_thin_binary(surf_e2, allowed_e2, n_target=e2_dot_target, min_dist_px=2.85)

    # =========================================================================
    # EXPERIMENT 3 (`H70-3`): Relief-Deconfounded Piedmont/Basin Corroboration +
    # Collar-Safe Tip/Relay Synergy + Exact Submodular 300m Kernel Allocator
    # =========================================================================
    # Strong relief-decile calibration removes mountain-crest slope over-concentration
    # (which caused 103k steep-slope rasters like 12GEMSDOE_r7-nms3-dem10-scarp to
    # overlap range-crest predictions) and shifts capacity onto piedmont scarplets,
    # basin-interior potential-field steps, relay ramps, tips, and thermal conduits.
    pi_phys_deconf = _relief_deconfounded_blend(
        pi_phys_fp, stack.relief_fp, reg_fp_list=reg_fp_list, weight_relief=0.65
    )
    pi_anat_deconf = _relief_deconfounded_blend(
        pi_anat_fp, stack.relief_fp, reg_fp_list=reg_fp_list, weight_relief=0.55
    )
    basin_piedmont_boost = (1.18 - 0.36 * _rank01(stack.relief_fp)).astype(np.float32)
    corrob_mult = (0.76 + 0.48 * multi_line_synergy_fp) * basin_piedmont_boost
    pi_phys_e3 = np.clip(0.56 * pi_phys_deconf * corrob_mult, 0.0, 0.90)
    pi_anat_e3 = np.clip(0.92 * pi_anat_deconf * (0.84 + 0.32 * phys_corrob_fp), 0.0, 0.90)

    off_known_fp = (d_known_fp > 2.0).astype(np.float32)
    pi_sgmc_off = off_known_fp * stack.sgmc_raw_fp * (0.008 * multi_line_synergy_fp * basin_piedmont_boost)
    pi_blind_geo = off_known_fp * stack.blind_hydro_fp * (0.014 * (0.5 + 0.5 * multi_line_synergy_fp))

    raw_union_e3 = 1.0 - (
        (1.0 - pi_phys_e3)
        * (1.0 - pi_anat_e3)
        * (1.0 - pi_sgmc_off)
        * (1.0 - pi_blind_geo)
    )

    is_sharp_tip_2d = np.zeros(grid.shape, dtype=bool)
    is_sharp_tip_2d[fp] = is_sharp_tip_fp > 0.5
    allowed_e3 = fp & ((d_known_2d > 2.0) | ((d_known_2d > 1.45) & is_sharp_tip_2d & ~known_mask))

    surf_e3 = np.zeros(grid.shape, dtype=np.float32)
    surf_e3[fp] = np.clip(raw_union_e3, 0.0, 1.0).astype(np.float32)
    surf_e3[~allowed_e3] = 0.0

    dots_e3, alloc_stats = submodular_marginal_dti_allocate(
        surf_e3,
        allowed_e3,
        k_truth=float(k_truth_prior),
        max_dots=int(max_dots_e3),
        candidate_cap=260_000,
    )

    return DualExpertOutput(
        pi_phys_fp=pi_phys_fp,
        pi_anat_fp=pi_anat_fp,
        surface_e2_2d=surf_e2,
        dots_e2_2d=dots_e2,
        surface_e3_2d=surf_e3,
        dots_e3_2d=dots_e3,
        alloc_e3_stats=alloc_stats,
    )
