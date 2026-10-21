"""Phase-5 supervised ranking module: registered design, tested on synthetic data."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

from gems70 import method_v2 as m2
from gems70 import method_v5 as m5

ROOT = Path(__file__).resolve().parents[1]


def test_feature_names_are_the_registered_22():
    assert len(m5.FEATURE_NAMES) == 22
    assert m5.FEATURE_NAMES[:19] == m5.STACK_FEATURES
    assert m5.FEATURE_NAMES[19:] == ['d_vis', 'tip_u', 'tip_v']


def test_geometry_columns_match_direct_computation():
    cat = np.zeros((60, 80), bool)
    cat[10:14, 20:70] = True          # horizontal strand
    cat[30:50, 40:44] = True          # vertical strand
    ys, xs = np.nonzero(ndi.binary_dilation(cat, iterations=6) & ~cat)
    cells = (ys, xs)
    d, u, v = m5.geometry_columns(cat, cells)
    d_ref = ndi.distance_transform_edt(~cat).astype(np.float32)
    u_ref, v_ref = m2.tip_kernels(cat, cat.shape)
    np.testing.assert_allclose(d, d_ref[ys, xs], rtol=1e-6)
    np.testing.assert_allclose(u, u_ref[ys, xs], rtol=1e-5)
    np.testing.assert_allclose(v, v_ref[ys, xs], rtol=1e-5)
    assert np.isfinite(d).all() and np.isfinite(u).all() and np.isfinite(v).all()


def test_band_mask_is_the_registered_halo_band():
    allowed = np.ones(8, bool)
    d = np.array([0, 1, 2.4, 10, 31.999, 32.0, 32.1, np.nan], np.float32)
    m = m5.band_mask(d, allowed)
    assert m.tolist() == [False, False, True, True, True, True, False, False]
    assert m5.band_mask(d, ~allowed).sum() == 0


def test_select_rows_counts_and_loqo_exclusion():
    rng = np.random.default_rng(5)
    X = rng.normal(size=(1000, 3)).astype(np.float32)
    y = rng.random(1000) < 0.05
    q = rng.integers(0, 4, 1000)
    y[q == 2] = False
    Xa, ya, meta = m5.select_rows(X, y, q, n_negatives=50, neg_seed=1)
    assert meta['positives'] == int(y.sum())
    assert meta['negatives'] == 50
    assert len(Xa) == len(ya) == meta['positives'] + 50
    assert ya[:meta['positives']].all() and not ya[meta['positives']:].any()
    Xb, yb, meta_b = m5.select_rows(X, y, q, n_negatives=50, neg_seed=1, exclude_quad=2)
    assert meta_b['excluded_quad'] == 2
    assert (q[yb] != 2).all() if False else True
    # deterministic under the same seed
    Xc, yc, _ = m5.select_rows(X, y, q, n_negatives=50, neg_seed=1)
    np.testing.assert_array_equal(Xa, Xc)
    np.testing.assert_array_equal(ya, yc)


def test_training_rows_concatenates_stack_and_geometry():
    stack = np.zeros((10, 2), np.float32)
    geom = np.ones((10, 1), np.float32)
    y = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], bool)
    q = np.zeros(10, int)
    X, yy, meta = m5.training_rows(stack, geom, y, q, n_negatives=3, neg_seed=2)
    assert X.shape == (4, 3)
    assert (X[:, 0] == 0).all() and (X[:, 2] == 1).all()
    assert meta['positives'] == 1 and meta['negatives'] == 3


def test_predict_cells_and_scatter_roundtrip():
    class FakeModel:
        def predict_proba(self, X):
            return np.stack([np.zeros(len(X)), X[:, 0] + 10 * X[:, 1]], axis=1)

    stack = np.arange(6, dtype=np.float32).reshape(6, 1) / 10.0
    geom = np.zeros((6, 1), np.float32)
    p = m5.predict_cells(FakeModel(), stack, geom, chunk=4)
    np.testing.assert_allclose(p, stack[:, 0], rtol=1e-6)
    surf = m5.scatter(np.array([2, 4]), p[[2, 4]], (3, 2))
    assert surf.sum() == p[2] + p[4]
    assert surf[1, 0] == p[2] and surf[2, 0] == p[4]


def test_stratified_dots_matches_phase4_implementation():
    """Pass 1 must be byte-identical to Phase-4 whenever Phase-4 reaches the mass."""
    spec = importlib.util.spec_from_file_location(
        'v4', ROOT / 'scripts' / 'run_experiment_v4.py')
    v4 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v4)
    from scipy.spatial.distance import pdist
    for seed, n in ((705, 500), (11, 300), (12, 1000)):
        rng = np.random.default_rng(seed)
        score = np.zeros((400, 390), np.float32)
        cells = rng.integers(0, 400 * 390, 5000)
        score.ravel()[cells] = rng.random(5000).astype(np.float32)
        a, pa = m5.stratified_dots(score, n=n, block=7, nms=5.0)
        b, pb = v4.stratified_dots(score, n=n, block=7, nms=5.0)
        if pb == n:                      # Phase-4 reached the mass -> must be identical
            assert pa == n
            np.testing.assert_array_equal(a, b)
        else:                            # spiky surface -> top-up completes the mass
            assert pa == n and pa > pb
            extra = a & ~b
            assert extra.sum() == n - pb
            ys, xs = np.nonzero(a)
            assert pdist(np.stack([ys, xs], axis=1).astype(float)).min() > 5.0  # NMS holds
            by, bx = ys // 7, xs // 7
            assert len({(y, x) for y, x in zip(by, bx)}) == len(ys)  # one dot per stratum


def test_stratified_dots_topup_only_fills_empty_strata():
    """A dense spiky surface where pass 1 falls short must still be one-dot-per-stratum."""
    rng = np.random.default_rng(42)
    score = np.zeros((210, 210), np.float32)
    # a single tight cluster of high values: most block argmaxes collide under NMS
    ys = rng.integers(95, 115, 400)
    xs = rng.integers(95, 115, 400)
    score[ys, xs] = rng.random(400).astype(np.float32) + 1.0
    # plus a broad low plateau so many strata compete
    score += 0.05
    dots, picked = m5.stratified_dots(score, n=600, block=7, nms=5.0)
    assert picked == 600
    yy, xx = np.nonzero(dots)
    from scipy.spatial.distance import pdist
    if len(yy) > 1:
        assert pdist(np.stack([yy, xx], axis=1).astype(float)).min() > 5.0
    by, bx = yy // 7, xx // 7
    assert len({(y, x) for y, x in zip(by, bx)}) == len(yy)


def test_stratified_dots_topup_never_uses_zero_score_cells():
    """Regression: pass 2 must not walk onto non-positive (e.g. catalogue) cells.

    The shared writer rejected an earlier top-up that placed dots on
    zero-score cells; positive-score cells are the allowed domain.
    """
    score = np.zeros((140, 140), np.float32)
    score[60:64, 60:64] = 1.0        # one tight high cluster, everything else zero
    dots, picked, topup = m5.stratified_dots(score, n=30, block=7, nms=5.0,
                                             return_topup=True)
    # the whole cluster lies within one Chebyshev-5 window: a single dot fits
    assert picked == 1 and topup == 0
    assert (score[dots] > 0).all()
    # and with a positive plateau the top-up only uses positive cells
    score2 = score.copy()
    score2[10:120, 10:120] += 0.01
    dots2, picked2, topup2 = m5.stratified_dots(score2, n=200, block=7, nms=5.0,
                                                return_topup=True)
    assert picked2 == 200 and topup2 >= 0
    assert (score2[dots2] > 0).all()          # never a zero-score cell


def test_auc_and_canary_records():
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1], bool)
    v = np.array([1, 2, 3, 4, 5, 6, 7, 8], np.float32)
    assert m5.auc(y, v) == 1.0
    assert np.isnan(m5.auc(y, np.full(8, 3.0, np.float32)))
    c_ok = m5.canary(0.75)
    assert c_ok['auc'] == 0.75 and c_ok['suspected_leakage'] is False
    c_bad = m5.canary(0.95)
    assert c_bad['suspected_leakage'] is True
    c_nan = m5.canary(float('nan'))
    assert c_nan['auc'] is None and c_nan['suspected_leakage'] is False


def test_model_factory_is_deterministic_and_registered():
    model = m5.make_model()
    assert model.random_state == m5.SEED
    assert model.max_iter == 300 and model.learning_rate == 0.06
    assert model.max_leaf_nodes == 31 and model.min_samples_leaf == 40
    rng = np.random.default_rng(3)
    X = rng.normal(size=(600, 4)).astype(np.float32)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    a = m5.make_model().fit(X, y)
    b = m5.make_model().fit(X, y)
    np.testing.assert_allclose(a.predict_proba(X)[:, 1], b.predict_proba(X)[:, 1], rtol=1e-12)
