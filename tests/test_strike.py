"""Guards for candidate C1 (experiment 2): catalogue independence and output scale."""
import numpy as np
from gems70 import strike
from gems70.method import rank01


def _toy(seed=3):
    rng = np.random.default_rng(seed)
    valid = np.ones((120, 140), bool)
    rtp = rng.normal(size=valid.shape).astype(np.float32)
    rtp[40:44, :] += 5.0                       # a magnetic edge
    vis = np.zeros(valid.shape, bool)
    vis[20:100, 60] = True                      # one visible north-south trace
    return rtp, vis, valid


def test_no_catalogue_arm_is_independent_of_visible_traces():
    rtp, vis, valid = _toy()
    other = np.zeros_like(vis)
    other[10:110, 90] = True                    # a different catalogue
    a = strike.combine(strike.features(rtp, vis, valid), valid, 'ablation_no_catalogue')
    b = strike.combine(strike.features(rtp, other, valid), valid, 'ablation_no_catalogue')
    np.testing.assert_array_equal(a, b)


def test_candidate_depends_on_visible_traces():
    rtp, vis, valid = _toy()
    other = np.zeros_like(vis)
    other[10:110, 90] = True
    a = strike.combine(strike.features(rtp, vis, valid), valid, 'candidate')
    b = strike.combine(strike.features(rtp, other, valid), valid, 'candidate')
    assert not np.array_equal(a, b)


def test_outputs_are_finite_in_unit_interval_and_zero_outside_valid():
    rtp, vis, valid = _toy()
    valid[:5] = False
    out = strike.combine(strike.features(rtp, vis, valid), valid, 'candidate')
    assert np.isfinite(out).all()
    assert out.min() >= 0 and out.max() <= 1
    assert not out[~valid].any()


def test_rank01_bounds():
    v = np.array([3.0, 1.0, 2.0, np.nan])
    r = rank01(v, np.isfinite(v))
    assert r[np.isfinite(v)].min() == 0 and r[np.isfinite(v)].max() == 1
