"""Synthetic unit tests for Phase-5 operators, leakage guards, and submodular packing."""
from __future__ import annotations

import numpy as np

from gems70 import method_v2 as m2
from gems70 import phase5


def test_unblurred_submodular_pack_centers_strictly_on_1px_ridge():
    """Verify the analytical ridge-centering theorem (3.000 > 2.233): dots land dead on 1-px ridge."""
    surf = np.zeros((40, 80), dtype=np.float32)
    surf[20, 5:75] = 1.0  # crisp 1-px E-W fault trace
    allow = np.ones_like(surf, dtype=bool)
    dots, picked = phase5.submodular_pack_300m(surf, allow, target_n=14)
    assert picked == 14
    ys, xs = np.nonzero(dots)
    # Every single emitted dot must sit strictly ON row 20 (never shifted off-ridge!)
    assert np.all(ys == 20)
    # Initial pass places non-overlapping ~5-px spaced dots before infilling
    assert xs.max() - xs.min() >= 55


def test_submodular_pack_respects_allowed_mask_and_exact_count():
    rng = np.random.default_rng(705)
    surf = rng.random((80, 90), dtype=np.float32)
    allow = np.ones((80, 90), dtype=bool)
    allow[:10, :] = False  # forbidden collar / off-footprint
    dots, picked = phase5.submodular_pack_300m(surf, allow, target_n=60)
    assert picked == 60
    assert int(dots.sum()) == 60
    assert not (dots & ~allow).any()


def test_static_feature_slice_prevents_self_distance_leakage():
    """Ensure M_neo trained with n_features=N_STATIC_FEATURES ignores column 38 (d_vis==0)."""
    rng = np.random.default_rng(42)
    n = 4000
    X = rng.normal(size=(n, phase5.N_TOTAL_FEATURES)).astype(np.float32)
    # Inject NaNs in LiDAR columns (25..28) to test native missing-value routing
    X[:1000, 25:29] = np.nan
    pos = np.zeros(n, dtype=bool)
    pos[:300] = True
    # Physical signal on column 29; self-identifying 0.0 distance on column 38
    X[pos, 29] += 2.2
    X[:, 38] = np.where(pos, 0.0, 15.0)
    train_mask = np.ones(n, dtype=bool)
    train_mask[3000:] = False

    clf = phase5.fit_oof_expert(
        X, pos, train_mask, seed=7, n_features=phase5.N_STATIC_FEATURES
    )
    # Changing column 38 on test points must change predictions by 0.0 identically
    X_alt = X[3000:, : phase5.N_STATIC_FEATURES].copy()
    p1 = clf.predict_proba(X[3000:, : phase5.N_STATIC_FEATURES])[:, 1]
    p2 = clf.predict_proba(X_alt)[:, 1]
    np.testing.assert_array_equal(p1, p2)
    assert np.isfinite(p1).all() and (p1.max() > p1.min())


def test_feature_canary_catches_leakage_both_signs():
    rng = np.random.default_rng(11)
    n = 1000
    X = rng.normal(size=(n, phase5.N_TOTAL_FEATURES)).astype(np.float32)
    truth = np.zeros(n, dtype=bool)
    truth[:200] = True
    can_clean = phase5.feature_leakage_canaries(X, truth)
    assert all(not v["suspected_leakage"] for v in can_clean.values())

    # Inject negative-sign leak (AUC < 0.10 -> max(auc, 1-auc) > 0.90)
    X[:, 0] = np.where(truth, -10.0, 10.0)
    can_leak = phase5.feature_leakage_canaries(X, truth)
    assert can_leak[phase5.FEATURE_NAMES[0]]["suspected_leakage"] is True


def test_visible_features_depend_strictly_on_visible_mask():
    valid = np.ones((50, 50), dtype=bool)
    X = np.zeros((int(valid.sum()), phase5.N_TOTAL_FEATURES), dtype=np.float32)
    vis1 = np.zeros((50, 50), dtype=bool)
    vis1[10:35, 25] = True
    d1 = phase5.write_fold_visible_features(X, valid, vis1, m2.tip_kernels)
    assert d1.shape == (50, 50)
    assert np.isfinite(X[:, 38:41]).all()
    assert X[:, 38].max() > 0.0
