"""P6 dual-horizon LOQO scarp-rad-basement method, SGMC buffer calibration, and E2 mutual re-audit tests."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems70 import method_dualhorizon as m5
from gems70.release import digest, valid_canary

ROOT = Path(__file__).resolve().parents[1]


def test_dualhorizon_method_synthetics_and_loqo_isolation():
    rng = np.random.default_rng(705)
    shape = (60, 60)
    valid = np.ones(shape, bool)
    valid[:4, :] = False
    cat = np.zeros(shape, bool)
    cat[25, 15:45] = True
    cat[15:45, 30] = True

    det_slope = rng.uniform(0.0, 25.0, shape).astype(np.float32)
    depth_base = rng.uniform(50.0, 2000.0, shape).astype(np.float32)
    iso_grav = rng.normal(0.0, 10.0, shape).astype(np.float32)
    geod_2nd = rng.uniform(0.0, 50.0, shape).astype(np.float32)
    geod_shr = rng.uniform(0.0, 50.0, shape).astype(np.float32)
    tmi_hg = rng.uniform(0.0, 100.0, shape).astype(np.float32)
    lidar_bands = [rng.integers(0, 255, shape, dtype=np.uint8).astype(np.float32) for _ in range(4)]
    topo10_bands = [rng.integers(1, 255, shape, dtype=np.uint8).astype(np.float32) for _ in range(5)]
    rad_bands = [rng.integers(1, 255, shape, dtype=np.uint8).astype(np.float32) for _ in range(4)]
    ext_bands = [rng.integers(1, 255, shape, dtype=np.uint8).astype(np.float32) for _ in range(3)]

    features, names, X = m5.physical_feature_ranks(
        det_slope, depth_base, iso_grav, geod_2nd, geod_shr, tmi_hg,
        lidar_bands, topo10_bands, rad_bands, ext_bands, valid
    )
    assert len(names) == 8
    assert X.shape == (*shape, 8)
    assert np.isfinite(X).all()
    assert not X[~valid].any()

    geom = m5.catalogue_geometry(cat, valid)
    assert geom['envelope'].shape == shape
    assert not geom['envelope'][cat].any()
    assert not geom['envelope'][~valid].any()

    quad = np.zeros(shape, np.int32)
    quad[:30, 30:] = 1
    quad[30:, :30] = 2
    quad[30:, 30:] = 3
    proxy_prime = (geom['d_cat'] >= 3.0) & (det_slope > 15.0) & valid & ~cat

    p_oof_rank, p_oof_raw, models = m5.fit_loqo_ranker(
        X, proxy_prime, quad, valid, cat, geom['d_cat'], seed=42, feature_names=names
    )
    assert len(models) == 4
    assert p_oof_rank.shape == shape
    assert np.isfinite(p_oof_rank).all()
    assert 0.0 <= float(p_oof_rank.min()) <= float(p_oof_rank.max()) <= 1.0

    brk = m5.unsupervised_breakline_rank(features, valid)
    s51 = m5.exp5_1_surface(geom['envelope'], p_oof_rank)
    s52 = m5.exp5_2_surface(geom['envelope'], brk)
    s53 = m5.exp5_3_surface(geom['envelope'], p_oof_rank, geom['allowed_full'])
    for s in (s51, s52, s53):
        assert not s[cat].any()
        assert not s[~valid].any()

    dots, count = m5.stratified_dots(s53, n=25, block=5, nms=3.2)
    assert count == 25
    assert int(dots.sum()) == 25
    assert not (dots & cat).any()


def test_p6_dualhorizon_evidence_and_buffer_calibration_receipts():
    base = ROOT / 'evidence/p6_dualhorizon'
    card = json.loads((base / 'run_card.json').read_text())
    assert card['submission_name'] == 'gems70-p5-dualhorizon-37654-20261020'
    assert card['download_ok'] is True
    assert card['submit_recommended'] is False
    assert card['verdict'] == 'negative'
    assert card['gate_a_candidate_ge_h33'] is True
    assert card['gate_b_prime_candidate_gt_h33_significant'] is True
    assert card['gate_b_double_prime_candidate_gt_h33_significant'] is True
    assert card['gate_unsupervised_ablation_beats_h33_on_b_prime'] is True
    assert card['gate_a_candidate_gt_p4_significant'] is False

    for rel, pin in card['method_source_sha256'].items():
        assert digest(ROOT / rel) == pin

    tif = ROOT / 'docs/downloads' / f"{card['submission_name']}.tif"
    assert digest(tif) == card['raster_sha256']
    with rasterio.open(tif) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert (src.height, src.width) == (3730, 3292)
        assert str(src.crs) == 'EPSG:32611'
    assert set(np.round(np.unique(arr), 6)).issubset({0.0, 1.0})
    assert int((arr > 0).sum()) == 37654

    # Pooled fold arithmetic matches summaries
    for summary_name, folds_name in (
        ('instrumentA_holdout.json', 'instrumentA_folds.json'),
        ('instrumentB_prime.json', 'instrumentB_prime_folds.json'),
    ):
        summary = json.loads((base / summary_name).read_text())
        folds = json.loads((base / folds_name).read_text())
        for arm, rows in folds.items():
            tp = sum(r['tp'] for r in rows)
            fp = sum(r['fp'] for r in rows)
            fn = sum(r['fn'] for r in rows)
            assert summary['scores'][arm]['dti'] == pytest.approx(
                tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12), abs=1e-12
            )

    # All three P6 arms beat H33 and Phase 4 on Instrument B' and B''
    bp = card['instrument_b_prime_proxy']
    assert bp['candidate']['dti'] > bp['exp5_1_sup_7x7']['dti'] > bp['exp5_2_brk_7x7']['dti'] > bp['h33_reference']['dti'] > bp['p4_reference']['dti']
    bpp = card['instrument_b_double_prime_proxy']
    assert bpp['candidate']['dti'] > bpp['exp5_1_sup_7x7']['dti'] > bpp['exp5_2_brk_7x7']['dti'] > bpp['h33_reference']['dti'] > bpp['p4_reference']['dti']

    # Canaries all valid
    canaries = json.loads((base / 'canaries.json').read_text())
    assert len(canaries) == 10
    assert all(valid_canary(c) for c in canaries.values())
    assert all(0.10 <= c['auc_instrument_b_prime'] <= 0.90 for c in canaries.values())

    # SGMC buffer audit monotonic
    buf = json.loads((base / 'sgmc_buffer_audit.json').read_text())
    curve = buf['buffer_enrichment_curve']
    radii = [r['buffer_px'] for r in curve]
    counts = [r['sgmc_pixels_within_buffer'] for r in curve]
    assert radii == sorted(radii)
    assert counts == sorted(counts)
    assert curve[2]['buffer_px'] == 3
    assert curve[2]['sgmc_pixels_d_ge_r'] == 62649
    for row in buf['dti_sensitivity_by_buffer'].values():
        dti = row['dti']
        assert dti['candidate_exp5_3'] > dti['h33_reference']
        assert dti['exp5_1_sup_7x7'] > dti['h33_reference']
        assert dti['exp5_2_brk_7x7'] > dti['h33_reference']

    # Uniqueness receipts (both P6 and E2 62-raster re-audit)
    for rel in ('uniqueness.json', 'e2_mutual_uniqueness.json'):
        u = json.loads((base / rel).read_text())
        assert u['registry_rasters_checked'] == 62
        assert u['unique'] is True
        assert u['duplicate_count'] == 0
        assert u['worst_dot_overlap'] <= 0.70
        assert u['worst_spearman_full_footprint'] <= 0.90
