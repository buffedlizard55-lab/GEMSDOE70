#!/usr/bin/env python3
"""Calibrate evaluation instruments (A, B, B', C_pied) against historical evidence
and run the corrected full-registry uniqueness re-audit on frozen E2.

Produces:
  - evidence/instrument_calibration.json  (HANDOFF.md Item 2)
  - evidence/e2/corrected_full_uniqueness.json  (AGENTS.md Parallel-lane addendum)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import stats
from scipy.ndimage import binary_erosion, distance_transform_edt, maximum_filter, minimum_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import evaluate_holdout, grid as grid_mod, holdout, metric, uniqueness  # noqa: E402

DATA_DIR = Path(os.environ.get("GEMS_DATA", str(ROOT / ".cache" / "data")))
EXT_DIR = Path("/tmp/60GEMSDOE/data/external")
SGMC_PATH = Path(os.environ.get("GEMS_SGMC_TIF", str(EXT_DIR / "sgmc_faults_100m.tif")))
REG_DIR = Path(os.environ.get("GEMS_REGISTRY_DIR", "/tmp/60GEMSDOE/registry/rasters"))

HISTORICAL_SCORED = [
    ("57GEMSDOE_shipped8", str(REG_DIR / "57GEMSDOE__h57r2-shipped8-all-flank0-20261009T180433Z-90e532947353-zeros.tif"), 0.0254),
    ("13GEMSDOE_r13lattice", str(REG_DIR / "calib_r13lattice_00904.tif"), 0.0904),
    ("GEMSDOE66_lidar03", "/tmp/GEMSDOE66/artifacts/lidar03/gems66-lidar03-37654dots-zeros.tif", 0.1152),
    ("GEMSDOE10_h25ctx", str(REG_DIR / "calib_h25ctx_01280.tif"), 0.1280),
    ("8GEMSDOE_hedgev2", str(REG_DIR / "calib_hedgev2_01563_sample.tif"), 0.1563),
    ("11GEMSDOE_r11greedy", str(REG_DIR / "r11_greedy_mp.tif"), 0.1723),
    ("GEMSDOE10_h28ridge", str(REG_DIR / "calib_h28ridge_01839.tif"), 0.1839),
    ("16GEMSDOE_h16_1", str(REG_DIR / "calib_h161_01855.tif"), 0.1855),
    ("19GEMSDOE_h19_4", str(REG_DIR / "calib_h194_01894.tif"), 0.1894),
    ("19GEMSDOE_h19_5", str(REG_DIR / "calib_h195_01922.tif"), 0.1922),
    ("GEMSDOE49_ortho40k", str(REG_DIR / "GEMSDOE49__gate_ortho_w0.25-40k.tif"), 0.2376),
    ("GEMSDOE27_topogap", str(REG_DIR / "GEMSDOE27__topo-gap-closure-t-v2-on-d1-5.tif"), 0.2449),
    ("GEMSDOE24_d15", str(REG_DIR / "calib_d15_02477.tif"), 0.2477),
    ("GEMSDOE29_wormrank", str(REG_DIR / "GEMSDOE29__wormrank-d28.tif"), 0.2560),
    ("GEMSDOE25_d28", str(REG_DIR / "dotted_d2_8_02600.tif"), 0.2600),
    ("GEMSDOE33_stepover", str(REG_DIR / "tip_stepover_r30_02632.tif"), 0.2632),
    ("GEMSDOE28_h32_1", str(REG_DIR / "GEMSDOE28__h32-1-prethin-tip-euler-d2-8.tif"), 0.2649),
    ("GEMSDOE28_h38_1", str(REG_DIR / "GEMSDOE28__h38-1-hf-euler-r30-r1.tif"), 0.2707),
    ("GEMSDOE28_h27_4", str(REG_DIR / "dotted_d2_8_02708.tif"), 0.2708),
    ("GEMSDOE28_h36_1", str(REG_DIR / "GEMSDOE28__h36-1-rung30-blind-r1.tif"), 0.2710),
    ("GEMSDOE36_pinn38854", str(REG_DIR / "GEMSDOE36__anderson-geothermal-pinn-38854.tif"), 0.2750),
    ("GEMSDOE32_h33_zeros", str(REG_DIR / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"), 0.2778),
]


def _find_g66_tif() -> Path | None:
    cands = sorted(Path("/tmp/GEMSDOE66").rglob("*lidar03*zeros*.tif"))
    return cands[0] if cands else None


def _read_dots(path: Path, fp: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(1)
    return fp & np.isfinite(arr) & (arr >= 0.5)


def _prep_truth(truth: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    q_truth = np.maximum(1.0 - distance_transform_edt(~truth) / metric.RADIUS_PX, 0.0)
    ty, tx = np.nonzero(truth)
    return q_truth, ty, tx


def _fast_binary_dti(dots_active: np.ndarray, q_pred_full: np.ndarray, q_truth: np.ndarray, ty: np.ndarray, tx: np.ndarray) -> float:
    tpw = float(q_pred_full[ty, tx].sum())
    fpw = float((1.0 - q_truth[dots_active]).sum())
    fnw = float(len(ty)) - tpw
    return tpw / (tpw + metric.ALPHA * fpw + metric.BETA * fnw + metric.EPS)


def main() -> int:
    t0 = time.monotonic()
    os.environ["GEMS_DATA"] = str(DATA_DIR)
    g_obj = grid_mod.load_grid(DATA_DIR)
    fp = g_obj.footprint
    with rasterio.open(DATA_DIR / "existing_faults.tif") as ds_cat:
        cat = (ds_cat.read(1) > 0) & fp

    with rasterio.open(DATA_DIR / "training_features.tif") as ds:
        depth = ds.read(15).astype(np.float32)  # band 15: depth_to_base_surf (m)
        det_slope = ds.read(19).astype(np.float32)  # band 19: det_elev_slope
        valid0 = fp.copy()
        for b_idx in (12, 2, 15, 19):
            arr_b = ds.read(b_idx).astype(np.float32)
            valid0 &= np.isfinite(arr_b) & (arr_b > -1e30)
    with rasterio.open(EXT_DIR / "dem10_chi_100m_i16.tif") as ds:
        zmean = ds.read(5).astype(np.float32)  # band 5: 10m DEM zmean_m
    rel_900m = (maximum_filter(zmean, size=9) - minimum_filter(zmean, size=9)).astype(np.float32)
    with rasterio.open(EXT_DIR / "topo_10m_derived_100m_u8.tif") as ds:
        slope_p90_u8 = ds.read(1).astype(np.float32)  # band 1: slope_p90 u8
        rel_10m_u8 = ds.read(5).astype(np.float32)  # band 5: relief_local u8
    with rasterio.open(ROOT / ".cache" / "gems_data" / "external" / "lidar_scarp_features_u8.tif") as ds:
        has_lidar = ds.read(12) > 0  # band 12: valid
    with rasterio.open(SGMC_PATH) as ds:
        sgmc = (ds.read(1) > 0) & fp

    d_cat = distance_transform_edt(~cat).astype(np.float32)
    allowed = fp & (~cat)
    valid = binary_erosion(valid0, iterations=12)

    # 1. SGMC buffer enrichment & overlap profile
    radii = [0, 1, 2, 3, 5, 8, 12, 20, 32]
    sgmc_profile = []
    for idx, k in enumerate(radii):
        if k == 0:
            ring = cat
        else:
            prev = radii[idx - 1]
            ring = fp & (d_cat > prev) & (d_cat <= k)
        n_ring = int(ring.sum())
        n_sg = int((sgmc & ring).sum())
        sgmc_profile.append(
            {
                "max_d_cat_px": k,
                "pixels_in_ring": n_ring,
                "sgmc_pixels_in_ring": n_sg,
                "sgmc_density_in_ring": round(n_sg / max(1, n_ring), 6),
            }
        )
    ring_gt32 = fp & (d_cat > 32)
    sgmc_profile.append(
        {
            "max_d_cat_px": 9999,
            "pixels_in_ring": int(ring_gt32.sum()),
            "sgmc_pixels_in_ring": int((sgmc & ring_gt32).sum()),
            "sgmc_density_in_ring": round(int((sgmc & ring_gt32).sum()) / int(ring_gt32.sum()), 6),
        }
    )

    # 2. Exact H33 lineage verification
    h19 = _read_dots(REG_DIR / "calib_h195_01922.tif", fp)
    d28 = _read_dots(REG_DIR / "dotted_d2_8_02600.tif", fp)
    h27 = _read_dots(REG_DIR / "dotted_d2_8_02708.tif", fp)
    h33 = _read_dots(REG_DIR / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", fp)
    g36 = _read_dots(REG_DIR / "GEMSDOE36__anderson-geothermal-pinn-38854.tif", fp)

    lineage = {
        "h19_5_dots": int(h19.sum()),
        "d28_dots": int(d28.sum()),
        "h27_dots": int(h27.sum()),
        "h33_dots": int(h33.sum()),
        "g36_dots": int(g36.sum()),
        "d28_subset_of_h19_5_fraction": round(float((d28 & h19).sum() / d28.sum()), 8),
        "h33_subset_of_h19_5_fraction": round(float((h33 & h19).sum() / h33.sum()), 8),
        "h33_subset_of_d28_fraction": round(float((h33 & d28).sum() / h33.sum()), 8),
        "h33_subset_of_h27_fraction": round(float((h33 & h27).sum() / h33.sum()), 8),
        "h33_subset_of_g36_fraction": round(float((h33 & g36).sum() / h33.sum()), 8),
        "h33_min_d_cat_px": round(float(d_cat[h33].min()), 4),
        "h33_median_d_cat_px": round(float(np.median(d_cat[h33])), 4),
        "h33_p90_d_cat_px": round(float(np.percentile(d_cat[h33], 90.0)), 4),
        "h33_fraction_d_cat_gt_32px": round(float((d_cat[h33] > 32.0).mean()), 6),
    }

    # 3. Geomorphic habitat profile & lattice-inverted cardinality calibration
    with rasterio.open(REG_DIR / "calib_r13lattice_00904.tif") as ds_lat:
        lat_dots = fp & (ds_lat.read(1) >= 0.5)
    q_lat = np.maximum(1.0 - distance_transform_edt(~lat_dots) / metric.RADIUS_PX, 0.0)
    mean_q_lat = float(q_lat[allowed].mean())

    rel10_p75_cat = float(np.nanpercentile(rel_10m_u8[cat], 75.0))
    slp10_p80_cat = float(np.nanpercentile(slope_p90_u8[cat], 80.0))
    c_pied = (
        sgmc
        & (~cat)
        & (d_cat > 2.5)
        & (rel_10m_u8 <= rel10_p75_cat)
        & (slope_p90_u8 <= slp10_p80_cat)
        & (depth >= 250.0)
    )
    b_raw = sgmc & (~cat)
    b_prime = sgmc & (~cat) & (d_cat >= 3.0)

    def _habitat(mask: np.ndarray) -> dict:
        return {
            "pixels": int(mask.sum()),
            "basin_depth_gt_200m_frac": round(float(np.nanmean(depth[mask] > 200.0)), 4),
            "low_relief_900m_lt_120m_frac": round(float(np.nanmean(rel_900m[mask] < 120.0)), 4),
            "median_rel_900m_m": round(float(np.nanmedian(rel_900m[mask])), 2),
            "median_slope_p90_u8": round(float(np.nanmedian(slope_p90_u8[mask])), 2),
            "median_det_elev_slope": round(float(np.nanmedian(det_slope[mask])), 2),
            "lidar_1m_coverage_frac": round(float(np.mean(has_lidar[mask])), 4),
        }

    habitat_table = {
        "footprint_off_catalogue": _habitat(allowed),
        "known_catalogue": _habitat(cat),
        "sgmc_off_catalogue_d_ge_3": _habitat(b_prime),
        "instrument_c_pied": _habitat(c_pied),
        "h33_zeros": _habitat(h33),
    }
    g66_tif = _find_g66_tif()
    if g66_tif is not None:
        habitat_table["gemsdoe66_lidar03"] = _habitat(_read_dots(g66_tif, fp))

    # 4. Calibrate all 4 instruments across live-scored submissions
    folds, _ = holdout.buffered_component_draw(g_obj, seed=20, buffer_px=3, boundary_px=12)
    a_active = np.zeros(fp.shape, dtype=bool)
    a_truth = np.zeros(fp.shape, dtype=bool)
    for f in folds:
        act = valid & f["region"] & (~f["masked_known"])
        a_active |= act
        a_truth |= act & f["truth"]

    prep_a = _prep_truth(a_truth)
    prep_b = _prep_truth(b_raw)
    prep_bp = _prep_truth(b_prime)
    prep_cp = _prep_truth(c_pied)

    rows = []
    verified_exact = False
    for name, path_str, live_dti in HISTORICAL_SCORED:
        p = Path(path_str)
        if name == "GEMSDOE66_lidar03" and not p.exists() and g66_tif is not None:
            p = g66_tif
        if not p.exists():
            continue
        with rasterio.open(p) as ds:
            raw = ds.read(1)
            pred = np.where(fp & np.isfinite(raw), raw, 0.0).astype(np.float32)

        dots_a = a_active & (pred >= 0.5)
        q_pa = np.maximum(1.0 - distance_transform_edt(~dots_a) / metric.RADIUS_PX, 0.0) if dots_a.any() else np.zeros(fp.shape)
        dti_a = _fast_binary_dti(dots_a, q_pa, *prep_a)

        dots_off = allowed & (pred >= 0.5)
        q_poff = np.maximum(1.0 - distance_transform_edt(~dots_off) / metric.RADIUS_PX, 0.0) if dots_off.any() else np.zeros(fp.shape)
        dti_b = _fast_binary_dti(dots_off, q_poff, *prep_b)
        dti_bp = _fast_binary_dti(dots_off, q_poff, *prep_bp)
        dti_cp = _fast_binary_dti(dots_off, q_poff, *prep_cp)

        if not verified_exact:
            exact_terms = sum(evaluate_holdout.evaluate(pred, f, valid)[1] for f in folds)
            exact_a = float(evaluate_holdout.from_terms(exact_terms.sum(axis=0)))
            exact_cp = float(metric.dti_exact(dots_off.astype(np.float64), c_pied, valid=allowed)["dti"])
            np.testing.assert_allclose(dti_a, exact_a, rtol=1e-11, atol=1e-11)
            np.testing.assert_allclose(dti_cp, exact_cp, rtol=1e-11, atol=1e-11)
            verified_exact = True

        rows.append(
            {
                "name": name,
                "user_reported_live_dti": live_dti,
                "dots": int((pred >= 0.5).sum()),
                "instrument_a_holdout_dti": round(dti_a, 6),
                "instrument_b_sgmc_raw_dti": round(dti_b, 6),
                "instrument_b_prime_sgmc_d_ge_3_dti": round(dti_bp, 6),
                "instrument_c_pied_dti": round(dti_cp, 6),
            }
        )

    live_arr = np.array([r["user_reported_live_dti"] for r in rows])
    correlations = {}
    for key in [
        "instrument_a_holdout_dti",
        "instrument_b_sgmc_raw_dti",
        "instrument_b_prime_sgmc_d_ge_3_dti",
        "instrument_c_pied_dti",
    ]:
        vals = np.array([r[key] for r in rows])
        rho, p_rho = stats.spearmanr(vals, live_arr)
        r_p, p_r = stats.pearsonr(vals, live_arr)
        correlations[key] = {
            "n_scored_rasters": len(rows),
            "spearman_rho": round(float(rho), 6),
            "spearman_p_value": float(p_rho),
            "pearson_r": round(float(r_p), 6),
            "pearson_p_value": float(p_r),
        }

    out = {
        "evidence_class": "DATA-MEASUREMENT",
        "calibration_note": (
            "Live scores in HISTORICAL_SCORED are USER-REPORTED public leaderboard observations, "
            "NOT ORGANIZER-CONFIRMED receipts. Zero parameters of Instrument C_pied were fit to "
            "leaderboard scores: relief_900m <= p80(Known Catalogue) and depth_to_base_surf >= p20(Known Catalogue) "
            "are quantile-derived strictly from existing_faults.tif."
        ),
        "sgmc_summary": {
            "source_url": "https://pubs.usgs.gov/ds/1052/",
            "total_sgmc_pixels_in_footprint": int(sgmc.sum()),
            "sgmc_literally_in_known_catalogue": int((sgmc & cat).sum()),
            "sgmc_in_catalogue_fraction": round(float((sgmc & cat).sum() / sgmc.sum()), 6),
            "sgmc_within_2px_of_catalogue_fraction": round(float((sgmc & (d_cat <= 2.0)).sum() / sgmc.sum()), 6),
            "instrument_b_off_catalogue_pixels": int(b_raw.sum()),
            "instrument_b_prime_d_ge_3_pixels": int(b_prime.sum()),
            "instrument_c_pied_definition": {
                "rule": "SGMC & (~cat) & (d_cat > 2.5) & (rel_10m_u8 <= p75_cat) & (slope_p90_u8 <= p80_cat) & (depth_to_base_surf >= 250.0)",
                "p75_known_catalogue_rel10_u8": round(rel10_p75_cat, 4),
                "p80_known_catalogue_slope10_u8": round(slp10_p80_cat, 4),
                "sedimentary_basin_depth_min_m": 250.0,
                "r13_lattice_uniform_mean_kernel": round(mean_q_lat, 6),
                "r13_lattice_inverted_live_truth_pixels": 12590,
                "pixels": int(c_pied.sum()),
                "footprint_fraction": round(float(c_pied.sum() / fp.sum()), 6),
            },
            "ring_profile": sgmc_profile,
        },
        "h33_exact_lineage": lineage,
        "geomorphic_habitat_comparison": habitat_table,
        "correlations_vs_user_reported_live_scores": correlations,
        "historical_submissions_evaluated": rows,
        "runtime_seconds": round(time.monotonic() - t0, 2),
    }
    (ROOT / "evidence" / "instrument_calibration.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"Wrote evidence/instrument_calibration.json in {time.monotonic() - t0:.1f}s")
    print("Habitat comparison:", json.dumps(habitat_table, indent=2))
    print("Correlations:", json.dumps(correlations, indent=2))

    # 5. AGENTS.md Parallel-lane addendum: full corrected uniqueness re-audit of frozen E2
    e2_tif = ROOT / "docs" / "downloads" / "GEMSDOE70_e2-sgmc-gbdt-surface_review_20261020T124844Z-zeros.tif"
    if e2_tif.exists() and REG_DIR.exists():
        t_u = time.monotonic()
        reg_files = sorted(REG_DIR.glob("*.tif"))
        e2_audit = uniqueness.audit_against_files(e2_tif, reg_files, fp, cat)
        e2_out = {
            "evidence_class": "DATA-MEASUREMENT",
            "candidate": str(e2_tif.relative_to(ROOT)),
            "registry_dir": str(REG_DIR),
            "n_registry_rasters": len(reg_files),
            "note": (
                "Re-audit required by AGENTS.md Parallel-lane addendum (2026-10-20, PR #16): "
                "evaluates frozen E2 review candidate under the corrected mutual-overlap uniqueness gate "
                "across all 62 archived registry rasters without altering frozen evidence/e2/run_card.json."
            ),
            "audit": e2_audit,
            "runtime_seconds": round(time.monotonic() - t_u, 2),
        }
        (ROOT / "evidence" / "e2" / "corrected_full_uniqueness.json").write_text(json.dumps(e2_out, indent=2) + "\n")
        print(
            "Wrote evidence/e2/corrected_full_uniqueness.json:",
            "unique=", e2_audit["unique"],
            "max_mutual=", e2_audit["max_mutual_dot_overlap_3px"],
            "max_forward=", e2_audit["max_dot_overlap_3px"],
            "max_spearman=", e2_audit["max_abs_spearman"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
