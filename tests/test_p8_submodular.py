"""Unit and receipt tests for P8 74-feature submodular multi-physics + hydrothermal synthesis."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57 import grid
from gems70 import method_p8_submodular as mp5
from gems70.release import p8_submodular_status, valid_canary

ROOT = Path(__file__).resolve().parents[1]


def test_submodular_dti_dots_spacing_concentration_and_saturation():
    h, w = 64, 64
    prob = np.zeros((h, w), np.float32)
    prob[16, 8:56] = 0.85
    prob[44, 10:54] = 0.70
    prob += 0.01
    allowed = np.ones((h, w), bool)
    allowed[:3, :] = False

    dots18, placed18 = mp5.submodular_dti_dots(prob, allowed, n_dots=18, min_spacing_px=2.5, gamma=1.0)
    assert placed18 == 18 and int(dots18.sum()) == 18
    ys18, _ = np.nonzero(dots18)
    assert ((np.abs(ys18 - 16) <= 1) | (np.abs(ys18 - 44) <= 1)).all()

    dots, placed = mp5.submodular_dti_dots(prob, allowed, n_dots=28, min_spacing_px=2.5, gamma=1.0)
    assert placed == 28 and int(dots.sum()) == 28
    assert not (dots & (~allowed)).any()

    ys, xs = np.nonzero(dots)
    dy = ys[:, None] - ys[None, :]
    dx = xs[:, None] - xs[None, :]
    dist2 = dy * dy + dx * dx
    np.fill_diagonal(dist2, 999)
    assert dist2.min() >= 6.25 - 1e-6
    d_to_dots = ndi.distance_transform_edt(~dots)
    assert d_to_dots[16, 8:56].max() <= 3.0
    assert d_to_dots[44, 10:54].max() <= 3.0


def test_conditioned_surface_enforces_visible_collar_and_unit_bounds():
    base = np.full((40, 40), 0.9, np.float32)
    cat = np.zeros((40, 40), bool)
    cat[20, 10:30] = True
    valid = np.ones((40, 40), bool)
    valid[0, :] = False

    surf = mp5.conditioned_surface(base, cat, valid, d_min=2.5, tip_boost=0.25)
    assert surf.dtype == np.float32
    assert np.isfinite(surf).all()
    assert surf.min() >= 0.0 and surf.max() <= 1.0
    assert surf[~valid].max() == 0.0
    d = ndi.distance_transform_edt(~cat)
    assert surf[d < 2.5].max() == 0.0


def test_feature_canaries_handle_nan_missing_tiles_and_flag_both_tails():
    rng = np.random.default_rng(705)
    fp = np.ones((30, 30), bool)
    n_fp = int(fp.sum())
    pos = np.zeros((30, 30), bool)
    pos[:10, :] = True
    neg = ~pos

    x = rng.normal(size=(n_fp, 3)).astype(np.float16)
    x[::7, 0] = np.float16(np.nan)
    x[:, 1] = np.where(pos[fp], 5.0, -5.0).astype(np.float16)
    x[:, 2] = np.where(pos[fp], -5.0, 5.0).astype(np.float16)

    rep = mp5.run_feature_canaries(x, ['clean_nan', 'leak_hi', 'leak_lo'], fp, pos, neg, seed=1)
    assert rep['clean_nan']['suspected_leakage'] is False
    assert rep['leak_hi']['suspected_leakage'] is True
    assert rep['leak_lo']['suspected_leakage'] is True


def test_oof_dual_model_produces_calibrated_unit_probabilities():
    rng = np.random.default_rng(42)
    h, w = 48, 48
    fp = np.ones((h, w), bool)
    valid = np.ones((h, w), bool)
    quad = np.zeros((h, w), np.int32)
    quad[:24, 24:] = 1
    quad[24:, :24] = 2
    quad[24:, 24:] = 3

    neo = np.zeros((h, w), bool)
    neo[6::12, :] = True
    sgmc = np.zeros((h, w), bool)
    sgmc[:, 8::12] = True

    signal = np.where(neo | sgmc, 2.5, -0.5).ravel()
    X_fp = np.column_stack([
        signal + rng.normal(scale=0.5, size=h * w),
        rng.normal(size=h * w),
    ]).astype(np.float16)

    p_blend, p_neo, p_bed = mp5.fit_predict_oof_dual(
        X_fp, [0, 1], fp, valid, quad, neo, sgmc, neo_weight=0.65, collar_px=2, seed=9,
    )
    for arr in (p_blend, p_neo, p_bed):
        assert arr.shape == (h, w)
        assert np.isfinite(arr).all()
        assert 0.0 <= float(arr.min()) <= float(arr.max()) <= 1.0
    assert float(p_blend[neo].mean()) > float(p_blend[~(neo | sgmc)].mean())


def test_p8_submodular_status_all_78_rasters_and_rank_one_across_all_lanes():
    st = p8_submodular_status(ROOT)
    assert st['verdict'] == 'promote'
    assert st['download_ok'] is True
    assert st['holdout_and_proxy_gates_passed'] is True
    assert st['selector_ready'] is True
    assert st['literal_forward_stop'] is True
    assert st['submit_recommended_automatic'] is False
    assert st['weekly_slots_used'] == 0
    assert st['reasons'] == []

    card = json.loads((ROOT / 'evidence/p8_submodular/run_card.json').read_text())
    can = json.loads((ROOT / 'evidence/p8_submodular/canaries.json').read_text())
    assert len(can) == 74 and all(valid_canary(c) for c in can.values())

    u78 = json.loads((ROOT / 'evidence/p8_submodular/uniqueness_with_all_siblings.json').read_text())
    assert u78['registry_rasters_checked'] == 78
    assert u78['archived_rasters_count'] == 62
    assert u78['local_sibling_rasters_count'] == 16
    assert u78['unique'] is True
    assert u78['duplicate_count'] == 0
    assert u78['worst_dot_overlap'] <= 0.70
    assert u78['worst_sibling_forward_overlap'] <= 0.70

    h2h = json.loads((ROOT / 'evidence/p8_submodular/cross_lane_head_to_head.json').read_text())['lanes']
    p8_e53 = h2h[0]
    for other in h2h[1:]:
        assert p8_e53['instrument_a_dti'] > other['instrument_a_dti'], other['lane']
        assert p8_e53['instrument_b_prime_dti'] > other['instrument_b_prime_dti'], other['lane']

    tif_path = ROOT / 'docs/downloads' / f"{card['submission_name']}.tif"
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == card['raster_sha256']
    g = grid.load_grid(ROOT / 'data/bridge')
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert (src.height, src.width) == (3730, 3292)
        assert str(src.crs) == 'EPSG:32611'
    assert np.isfinite(arr).all()
    assert int((arr > 0.5).sum()) == 54000
    assert int(((arr > 0.5) & g.catalogue).sum()) == 0
    assert int(((arr > 0.5) & ~g.footprint).sum()) == 0


def test_p8_submodular_fails_closed_on_tampered_sha(tmp_path):
    (tmp_path / 'evidence/p8_submodular').mkdir(parents=True)
    card = json.loads((ROOT / 'evidence/p8_submodular/run_card.json').read_text())
    card['raster_sha256'] = '0' * 64
    (tmp_path / 'evidence/p8_submodular/run_card.json').write_text(json.dumps(card))
    st = p8_submodular_status(tmp_path)
    assert st['download_ok'] is False
    assert st['holdout_and_proxy_gates_passed'] is False
    assert st['selector_ready'] is False
