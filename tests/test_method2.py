"""Synthetic oracles for the E2/E3 operators (no competition data needed)."""
import numpy as np
from scipy import ndimage as ndi

from gems70 import method2


def test_constant_field_has_no_step():
    a = np.ones((64, 64), np.float32)
    axis, _ = method2.structure_tensor_normal(a)
    oriented, step_max = method2.oriented_step(a, axis)
    assert not step_max.any() and not oriented.any()


def test_tensor_axis_and_step_orientation():
    h = w = 64
    xstep = np.zeros((h, w), np.float32); xstep[:, w // 2:] = 1.0
    ystep = np.zeros((h, w), np.float32); ystep[h // 2:, :] = 1.0
    ax, coh = method2.structure_tensor_normal(xstep)
    assert ax[h // 2, w // 2] == 0  # E-W normal
    assert coh[h // 2, w // 2] > 0.99
    ax2, _ = method2.structure_tensor_normal(ystep)
    assert ax2[h // 2, w // 2] == 2  # N-S normal
    oriented, _ = method2.oriented_step(ndi.gaussian_filter(xstep, 1.0), ax)
    assert oriented[h // 2, w // 2] > 0.5
    assert oriented[h // 2, 5] == 0.0


def test_thin_budget_spacing_determinism():
    rng = np.random.default_rng(0)
    rank = rng.random((100, 100)).astype(np.float32)
    allow = np.ones((100, 100), bool)
    e1, n1 = method2.priority_thin(rank, allow, target_n=50)
    e2, n2 = method2.priority_thin(rank, allow, target_n=50)
    assert n1 == n2 == 50 and np.array_equal(e1, e2)
    assert e1.flat[int(np.argmax(rank))]
    ys, xs = np.nonzero(e1)
    dmin = min(np.hypot(ys[i] - ys[j], xs[i] - xs[j])
               for i in range(len(ys)) for j in range(i + 1, len(ys)))
    assert dmin >= method2.THIN_MIN_DIST_PX


def test_topn_mask_mass():
    v = np.arange(100, dtype=np.float32).reshape(10, 10)
    m = method2.topn_mask(v, np.ones((10, 10), bool), 5)
    assert m.sum() == 5 and m.flat[99] and not m.flat[0]
