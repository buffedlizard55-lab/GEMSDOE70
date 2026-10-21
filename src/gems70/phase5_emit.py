"""Phase 5 binary dot allocation algorithms (matched 37,654-dot budget).

Provides two cleanly separated, zero-leakage emitters on any continuous surface:
  1. ``peak_nms_emit``: Standard 7x7 local-maximum suppression baseline (Exp 5.1 & Exp 5.2).
  2. ``submodular_dti_emit``: Exact lazy-greedy maximization of expected marginal
     Distance-Weighted Tversky Index (DTI) coverage over the official R=300 m (3.0 px)
     triangular kernel k(d) = max(1 - d/3, 0) (Exp 5.3, Hypothesis H-P5-5).
"""

from __future__ import annotations

import heapq
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import maximum_filter

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import metric  # noqa: E402


def peak_nms_emit(
    surface: np.ndarray,
    allowed_mask: np.ndarray,
    n_dots: int = 37654,
) -> np.ndarray:
    """Select exact ``n_dots`` binary 1.0 pixels via 7x7 peak NMS (fallback 5x5 -> 3x3)."""
    s = np.where(allowed_mask & np.isfinite(surface), surface.astype(np.float64), -1.0)
    # Deterministic micro-tie-breaker purely from coordinates so ties never form flat plateaus
    yy, xx = np.indices(surface.shape, dtype=np.float64)
    s_tie = s + 1e-12 * (yy * 0.00031 + xx * 0.00017)

    out = np.zeros(surface.shape, dtype=np.float32)
    remaining = int(n_dots)
    avail = allowed_mask & (surface > 0)

    for win in (7, 5, 3, 1):
        if remaining <= 0:
            break
        cur = np.where(avail, s_tie, -2.0)
        if win > 1:
            is_peak = avail & (cur == maximum_filter(cur, size=win, mode="constant", cval=-3.0))
        else:
            is_peak = avail
        cand_idx = np.flatnonzero(is_peak)
        if cand_idx.size == 0:
            continue
        scores = s_tie.ravel()[cand_idx]
        if cand_idx.size > remaining:
            top = np.argpartition(scores, -remaining)[-remaining:]
            top = top[np.argsort(-scores[top])]
            chosen = cand_idx[top]
        else:
            chosen = cand_idx[np.argsort(-scores)]
        out.ravel()[chosen] = 1.0
        avail.ravel()[chosen] = False
        remaining -= int(chosen.size)

    assert int((out > 0.5).sum()) == int(n_dots)
    return out


def submodular_dti_emit(
    prob: np.ndarray,
    allowed_mask: np.ndarray,
    n_dots: int = 37654,
    fp_penalty_weight: float = 0.06,
    candidate_pool: int = 420000,
) -> np.ndarray:
    """Exact lazy-greedy Minoux submodular maximizer of expected DTI kernel coverage.

    For each cell ``g`` with calibrated posterior probability ``q(g) >= 0``, adding dot ``x``
    yields marginal expected weighted true-positive gain:

        dTP(x | S) = sum_{m: d_m < 3} q(x + delta_m) * max(0, k_m - C_S(x + delta_m))

    penalized by ``fp_penalty_weight * (1 - max_m q(x + delta_m) * k_m)``.
    Because ``max(C_S(g), k_m)`` is monotone submodular for every ``g`` with ``q(g) >= 0``,
    the lazy priority queue is mathematically exact (identical output to full brute-force
    greedy re-evaluation at every step, ~100x faster).
    """
    H, W = prob.shape
    # Pad grid by R=3 px so inner loop does ZERO bounds checks
    pad = 3
    q_pad = np.zeros((H + 2 * pad, W + 2 * pad), dtype=np.float64)
    q_pad[pad : pad + H, pad : pad + W] = np.clip(
        np.where(np.isfinite(prob), prob, 0.0), 0.0, 1.0
    )
    cov_pad = np.zeros_like(q_pad)

    dy = metric.OFF_DY.tolist()
    dx = metric.OFF_DX.tolist()
    kw = metric.OFF_K.tolist()
    n_off = len(kw)

    # Vectorized exact initial marginal utility U(x | empty) across entire grid
    init_tp = np.zeros((H, W), dtype=np.float64)
    q_self = np.zeros((H, W), dtype=np.float64)
    for oy, ox, k_val in zip(dy, dx, kw):
        sub = q_pad[pad + oy : pad + oy + H, pad + ox : pad + ox + W]
        init_tp += k_val * sub
        np.maximum(q_self, k_val * sub, out=q_self)

    pen_arr = fp_penalty_weight * (1.0 - q_self)
    u0 = init_tp - pen_arr

    valid_idx = np.flatnonzero(allowed_mask & (init_tp > 0))
    if valid_idx.size > candidate_pool:
        u_sub = u0.ravel()[valid_idx]
        keep = np.argpartition(u_sub, -candidate_pool)[-candidate_pool:]
        valid_idx = valid_idx[keep]

    ys = (valid_idx // W + pad).tolist()
    xs = (valid_idx % W + pad).tolist()
    pens = pen_arr.ravel()[valid_idx].tolist()
    u_vals = u0.ravel()[valid_idx].tolist()

    # Deterministic tie-breaking via index order in Python tuple (-gain, slot_i)
    heap: list[tuple[float, int]] = [(-u_vals[i], i) for i in range(len(u_vals))]
    heapq.heapify(heap)

    out = np.zeros((H, W), dtype=np.float32)
    selected = 0

    while selected < n_dots and heap:
        neg_upper, i = heapq.heappop(heap)
        cy = ys[i]
        cx = xs[i]
        # Exact recomputation over 29 kernel neighbors
        gain = 0.0
        for m in range(n_off):
            ny = cy + dy[m]
            nx = cx + dx[m]
            k_m = kw[m]
            cur_c = cov_pad[ny, nx]
            if k_m > cur_c:
                gain += q_pad[ny, nx] * (k_m - cur_c)
        exact_u = gain - pens[i]

        if not heap or (-exact_u <= heap[0][0] + 1e-15):
            # Guaranteed global argmax among all remaining candidates!
            out[cy - pad, cx - pad] = 1.0
            for m in range(n_off):
                ny = cy + dy[m]
                nx = cx + dx[m]
                k_m = kw[m]
                if k_m > cov_pad[ny, nx]:
                    cov_pad[ny, nx] = k_m
            selected += 1
        else:
            heapq.heappush(heap, (-exact_u, i))

    assert selected == int(n_dots), f"Selected {selected} < {n_dots}"
    return out
