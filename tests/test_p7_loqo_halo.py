"""Unit and receipt tests for Phase-5 LOQO within-halo ranker and audits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems57 import grid
from gems70 import method_v5 as m5
from gems70.release import phase5_status, valid_canary

ROOT = Path(__file__).resolve().parents[1]


def test_rank01_vec_bounds_and_monotonicity():
    v = np.array([10.0, 20.0, 15.0, 30.0], dtype=np.float32)
    r = m5.rank01_vec(v)
    assert r.dtype == np.float32
    assert np.isclose(r.min(), 0.0)
    assert np.isclose(r.max(), 1.0)
    assert r[0] < r[2] < r[1] < r[3]
    single = m5.rank01_vec(np.array([5.0], dtype=np.float32))
    assert single.shape == (1,) and np.isclose(single[0], 0.0)


def test_hydrothermal_and_catalogue_geometry_features_synthetic():
    shape = (40, 40)
    valid = np.ones(shape, dtype=bool)
    v_idx = np.flatnonzero(valid)

    # Empty conduit mask and empty catalogue fallback
    h_empty, d_empty = m5.hydrothermal_features(np.zeros(shape, bool), v_idx)
    assert h_empty.shape == (v_idx.size, 2)
    assert np.all(h_empty[:, 1] == 0.0)

    g_empty, d_cat0, tip0 = m5.catalogue_geometry_features(np.zeros(shape, bool), v_idx)
    assert g_empty.shape == (v_idx.size, 8)
    assert np.all(g_empty == 0.0)
    assert np.all(tip0 == 0.0)

    # Non-empty conduit and fault trace
    conduits = np.zeros(shape, bool)
    conduits[20, 20] = True
    h_mat, h_meta = m5.hydrothermal_features(conduits, v_idx)
    assert h_mat.shape == (v_idx.size, 2)
    assert np.isfinite(h_mat).all()
    assert np.isclose(h_meta['hydro_kernel'][20, 20], 1.0)
    assert np.isclose(h_mat[20 * 40 + 20, 0], 0.0)
    assert np.isclose(h_mat[:, 1].max(), 1.0)

    cat_vis = np.zeros(shape, bool)
    cat_vis[10:30, 18] = True
    out_buf = np.empty((v_idx.size, 8), np.float32)
    g_mat, d_cat, tip_k = m5.catalogue_geometry_features(cat_vis, v_idx, out_mat=out_buf)
    assert g_mat is out_buf
    assert np.isfinite(g_mat).all()
    assert np.isclose(d_cat[15, 18], 0.0)
    assert (tip_k >= 0.0).all() and (tip_k <= 1.0).all()


def test_fit_predict_loqo_and_combine_halo_synthetic():
    shape = (32, 32)
    valid = np.ones(shape, bool)
    v_idx = np.flatnonzero(valid)
    n_val = v_idx.size

    rng = np.random.default_rng(70599)
    X = rng.normal(size=(n_val, 6)).astype(np.float32)
    quad = np.zeros(shape, np.int8)
    quad[:16, 16:] = 1
    quad[16:, :16] = 2
    quad[16:, 16:] = 3
    q_val = quad.ravel()[v_idx]
    eq_val = q_val.copy()

    elig = np.ones(n_val, bool)
    y_proxy = (X[:, 0] + 0.5 * X[:, 1] > 0.8) & elig
    rank_grid, diag = m5.fit_predict_loqo(
        X, y_proxy, elig, q_val, eq_val, shape, v_idx, col_indices=[0, 1, 2, 3], seed=70500
    )
    assert rank_grid.shape == shape
    assert len(diag) == 4
    assert (rank_grid >= 0.0).all() and (rank_grid <= 1.0).all()

    cat_vis = np.zeros(shape, bool)
    cat_vis[15, 10:20] = True
    _, d_cat, tip_k = m5.catalogue_geometry_features(cat_vis, v_idx)
    surf = m5.combine_loqo_halo(rank_grid, d_cat, tip_k, cat_vis, valid)
    assert np.all(surf[cat_vis] == 0.0)
    assert np.all(surf[d_cat < 3.0] == 0.0)
    assert (surf >= 0.0).all()

    dots, picked = m5.stratified_dots(surf, n=10, block=4, nms=3.0)
    assert picked == int(dots.sum()) == 10
    assert not (dots & cat_vis).any()


def test_phase5_status_and_artifact_integrity():
    st = phase5_status(ROOT)
    assert st['verdict'] == 'promote'
    assert st['download_ok'] is True
    assert st['holdout_and_proxy_gates_passed'] is True
    assert st['selector_ready'] is True
    assert st['weekly_slots_used'] == 0
    assert st['reasons'] == []

    card = json.loads((ROOT / 'evidence/phase5/run_card.json').read_text())
    assert card['organizer_confirmed_score'] is None
    assert len(card['submission_note']) <= 140
    assert card['note_chars'] == len(card['submission_note'])

    tif_path = ROOT / 'docs/downloads' / f"{card['submission_name']}.tif"
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == card['raster_sha256']
    g = grid.load_grid(ROOT / 'data/bridge')
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert (src.height, src.width) == (3730, 3292)
        assert str(src.crs) == 'EPSG:32611'
    assert np.isfinite(arr).all()
    assert set(np.round(np.unique(arr), 6)).issubset({0.0, 1.0})
    assert int((arr > 0.5).sum()) == 37654
    assert int(((arr > 0.5) & g.catalogue).sum()) == 0
    assert int(((arr > 0.5) & ~g.footprint).sum()) == 0


def test_phase5_canaries_uniqueness_and_audits():
    canaries = json.loads((ROOT / 'evidence/phase5/canaries.json').read_text())
    assert len(canaries) == 49
    assert all(valid_canary(c) for c in canaries.values())

    for fname, expected_n in [
        ('uniqueness.json', 62),
        ('uniqueness_with_local.json', 66),
        ('surface_uniqueness.json', 66),
    ]:
        u = json.loads((ROOT / 'evidence/phase5' / fname).read_text())
        assert u['registry_rasters_checked'] == expected_n
        assert u['unique'] is True
        assert u['duplicate_count'] == 0
        assert u['worst_dot_overlap'] <= 0.70
        assert u['worst_spearman_full_footprint'] <= 0.90

    buf = json.loads((ROOT / 'evidence/phase5/sgmc_buffer_audit.json').read_text())
    assert buf['population_summary']['sgmc_off_catalogue_pixels'] == 78433
    r3 = [row for row in buf['proxy_dti_sensitivity_across_buffers'] if row['min_catalogue_distance_px'] == 3.0][0]
    assert r3['scored_truth_pixels'] == 59937
    assert r3['proxy_dti']['h33_reference'] > r3['proxy_dti']['d28_reference'] > r3['proxy_dti']['p4_stratified_halo']

    e2_u = json.loads((ROOT / 'evidence/phase5/e2_uniqueness_62rasters_corrected.json').read_text())
    assert e2_u['registry_rasters_checked'] == 62
    assert e2_u['unique'] is True
    assert e2_u['duplicate_count'] == 0

    up = json.loads((ROOT / 'evidence/phase5/upstream_verification.json').read_text())
    assert up['other_20_files_identical_to_upstream'] is True
    assert up['pytest_returncode'] == 0
    assert (ROOT / 'evidence/phase5/upstream_uniqueness.patch').is_file()


def test_phase5_status_fails_closed_on_corrupted_card(tmp_path):
    (tmp_path / 'evidence/phase5').mkdir(parents=True)
    card = json.loads((ROOT / 'evidence/phase5/run_card.json').read_text())
    card['raster_sha256'] = '0' * 64
    (tmp_path / 'evidence/phase5/run_card.json').write_text(json.dumps(card))
    st = phase5_status(tmp_path)
    assert st['download_ok'] is False
    assert st['holdout_and_proxy_gates_passed'] is False
    assert st['selector_ready'] is False


def test_all_docs_html_local_links_resolve():
    from html.parser import HTMLParser
    from urllib.parse import unquote, urlsplit

    class LinkChecker(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            if tag in ('a', 'link') and 'href' in d:
                self.links.append(d['href'])

    for p in (ROOT / 'docs').glob('*.html'):
        parser = LinkChecker()
        parser.feed(p.read_text())
        for link in parser.links:
            u = urlsplit(link)
            if u.scheme or u.netloc or not u.path:
                continue
            target = (p.parent / unquote(u.path)).resolve()
            assert target.is_file(), f'Broken local link in {p.name}: {link}'

