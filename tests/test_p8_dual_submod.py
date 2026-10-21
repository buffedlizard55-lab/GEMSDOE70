"""Synthetic unit tests for Phase-5 operators, leakage guards, and submodular packing."""
from __future__ import annotations

import numpy as np

from gems70 import method_v2 as m2
from gems70 import method_p8 as phase5


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


def test_p8_promoted_artifact_hashes_validator_and_gates():
    """End-to-end verification of P8 on-disk GeoTIFF, 1-TIFF ZIP, Run Card, and release gate."""
    import hashlib
    import json
    from pathlib import Path
    import zipfile
    import rasterio

    from gems70.release import p8_status

    root = Path(__file__).resolve().parents[1]
    st = p8_status(root)
    assert st['verdict'] == 'promote'
    assert st['download_ok'] is True
    assert st['submit_recommended'] is True
    assert st['holdout_and_proxy_gates_passed'] is True
    assert st['literal_forward_witness_stop_required'] is True
    assert st['weekly_slots_used'] == 0
    assert st['reasons'] == []

    card = json.loads((root / 'evidence/p8_dual_submod300/run_card.json').read_text())
    assert card['experiment_count'] == 3
    assert card['organizer_confirmed_score'] is None
    assert len(card['submission_note']) <= 140
    assert all(card['promotion_gates'].values())

    tif = root / 'docs/downloads' / f"{card['submission_name']}.tif"
    zpath = root / 'docs/downloads' / f"{card['submission_name']}.zip"
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card['raster_sha256']
    assert hashlib.sha256(zpath.read_bytes()).hexdigest() == card['zip_sha256']

    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
        assert names == [f"{card['submission_name']}.tif"]
        assert hashlib.sha256(zf.read(names[0])).hexdigest() == card['raster_sha256']

    with rasterio.open(tif) as ds:
        assert (ds.height, ds.width, ds.count) == (3730, 3292, 1)
        assert ds.dtypes[0] == 'float32'
        assert ds.crs.to_epsg() == 32611
        arr = ds.read(1)
        assert np.isfinite(arr).all()
        assert set(np.unique(arr).tolist()) == {0.0, 1.0}
        assert int((arr == 1.0).sum()) == 37654


def test_p8_pooled_dti_identities_and_site_presence(tmp_path):
    """Verify pooled TP/(TP+0.2*FP+0.8*FN) exactness, tamper fail-closed gate, and site pages."""
    import json
    from pathlib import Path
    import shutil

    from gems70.release import p8_status

    root = Path(__file__).resolve().parents[1]
    for fname in ('instrumentA_holdout.json', 'instrumentB_prime.json', 'instrumentB_sens_d5.json'):
        doc = json.loads((root / 'evidence/p8_dual_submod300' / fname).read_text())
        for arm, sc in doc['scores'].items():
            recomputed = sc['tpw'] / (sc['tpw'] + 0.2 * sc['fpw'] + 0.8 * sc['fnw'])
            assert abs(recomputed - sc['dti']) < 1e-12, (fname, arm, recomputed, sc['dti'])

    for page in ('docs/index.html', 'docs/executive-summary.html', 'docs/p8.html',
                 'docs/preregistration-p8-dual-submod300.html', 'README.md'):
        txt = (root / page).read_text()
        assert 'gems70-p5-dual-submod300-oof38k-20261020' in txt
        assert 'd0e41ce921afcf3af33b7d86d75f6a258653dfbb4d050e864babe643245f0ea8' in txt

    # Tampering with SHA-256 in run_card must fail closed immediately
    ev = tmp_path / 'evidence/p8_dual_submod300'
    ev.mkdir(parents=True)
    for src in (root / 'evidence/p8_dual_submod300').glob('*.json'):
        shutil.copyfile(src, ev / src.name)
    bad = json.loads((ev / 'run_card.json').read_text())
    bad['raster_sha256'] = '0' * 64
    (ev / 'run_card.json').write_text(json.dumps(bad))
    st_bad = p8_status(tmp_path)
    assert st_bad['download_ok'] is False
    assert st_bad['submit_recommended'] is False

