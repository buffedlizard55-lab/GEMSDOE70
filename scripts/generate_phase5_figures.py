#!/usr/bin/env python3
"""Generate pure-stdlib lossless PNG spatial map & Retina SVG vector charts
from verified Phase 5 EPSG:32611 rasters and recorded JSON receipts.

Uses ONLY Python standard library + numpy/scipy/rasterio from requirements.lock,
so every figure builds identically in CI without extra packages.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import maximum_filter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"


def write_png_rgb(path: Path, rgb: np.ndarray) -> None:
    """Write uint8 (H, W, 3) array as standard lossless RGB PNG via stdlib zlib."""
    h, w, _ = rgb.shape
    raw_rows = b"".join(b"\x00" + rgb[r].tobytes() for r in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw_rows, level=9)
    png_bytes = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    path.write_bytes(png_bytes)


def build_svg_charts(assets_dir: Path) -> None:
    """Render crisp, zero-overlap Retina SVG charts directly from evidence JSONs."""
    card = json.loads((ROOT / "evidence/phase5/run_card.json").read_text())
    calib = json.loads((ROOT / "evidence/instrument_calibration.json").read_text())
    uniq = json.loads((ROOT / "evidence/phase5/uniqueness.json").read_text())
    p4_a = json.loads((ROOT / "evidence/phase4/instrumentA_holdout.json").read_text())
    p4_bp = json.loads((ROOT / "evidence/phase4/instrumentB_prime.json").read_text())

    # -------------------------------------------------------------------------
    # SVG 1: Live 22-Submission Calibration + 4-Instrument 95% CI Benchmark
    # -------------------------------------------------------------------------
    pts = calib["historical_submissions_evaluated"]
    xs = np.array([p["instrument_c_pied_dti"] for p in pts], dtype=float)
    ys = np.array([p["user_reported_live_dti"] for p in pts], dtype=float)
    m_fit, b_fit = np.polyfit(xs, ys, 1)

    def sx(v: float) -> float:
        return 76.0 + (v / 0.130) * 410.0

    def sy(v: float) -> float:
        return 356.0 - (v / 0.340) * 280.0

    p5_cp = card["instrument_c_pied_proxy"]["candidate"]["dti"]
    p5_cp_lo, p5_cp_hi = card["instrument_c_pied_proxy"]["candidate"]["ci95"]

    svg1 = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 430" role="img" '
        'aria-label="Live Calibration and Multi-Instrument 95% Confidence Interval Benchmark" '
        'style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#ffffff;border:1px solid #e2e8f0;border-radius:10px">',
        '<text x="275" y="30" text-anchor="middle" font-size="14" font-weight="700" fill="#0f172a">'
        'A. Zero-Parameter Calibration vs 22 Live Scores (ρ = +0.867)</text>',
        '<text x="805" y="30" text-anchor="middle" font-size="14" font-weight="700" fill="#0f172a">'
        'B. Phase 5 vs H33 &amp; Phase 4 Across All 4 Primary Instruments</text>',
        # Shaded 95% CI band for Phase 5 C_pied
        f'<rect x="{sx(p5_cp_lo):.1f}" y="66" width="{max(2.0, sx(p5_cp_hi) - sx(p5_cp_lo)):.1f}" height="290" fill="#10b981" fill-opacity="0.11"/>',
        '<rect x="76" y="66" width="415" height="290" fill="none" stroke="#cbd5e1" stroke-width="1"/>',
    ]
    for gy in (0.0, 0.10, 0.20, 0.30):
        yy = sy(gy)
        svg1.append(f'<line x1="76" y1="{yy:.1f}" x2="491" y2="{yy:.1f}" stroke="#e2e8f0" stroke-dasharray="3,3"/>')
        svg1.append(f'<text x="68" y="{yy + 4:.1f}" text-anchor="end" font-size="11" fill="#475569">{gy:.2f}</text>')
    for gx in (0.0, 0.04, 0.08, 0.12):
        xx = sx(gx)
        svg1.append(f'<line x1="{xx:.1f}" y1="66" x2="{xx:.1f}" y2="356" stroke="#e2e8f0" stroke-dasharray="3,3"/>')
        svg1.append(f'<text x="{xx:.1f}" y="373" text-anchor="middle" font-size="11" fill="#475569">{gx:.2f}</text>')

    # Regression line
    svg1.append(
        f'<line x1="{sx(0.0):.1f}" y1="{sy(b_fit):.1f}" x2="{sx(0.125):.1f}" y2="{sy(m_fit * 0.125 + b_fit):.1f}" '
        'stroke="#64748b" stroke-width="1.5" stroke-dasharray="5,4"/>'
    )
    # Phase 5 vertical line
    svg1.append(
        f'<line x1="{sx(p5_cp):.1f}" y1="66" x2="{sx(p5_cp):.1f}" y2="356" stroke="#059669" stroke-width="2.4" stroke-dasharray="6,3"/>'
    )
    svg1.append(
        f'<text x="{sx(p5_cp) - 6:.1f}" y="84" text-anchor="end" font-size="11" font-weight="700" fill="#047857">'
        f'Phase 5 OOF = {p5_cp:.4f}</text>'
    )
    svg1.append(
        f'<text x="{sx(p5_cp) - 6:.1f}" y="98" text-anchor="end" font-size="10.5" fill="#047857">'
        'Beat H33 (+19.1%, 95% CI &gt; 0)</text>'
    )

    for p in pts:
        cx, cy = sx(p["instrument_c_pied_dti"]), sy(p["user_reported_live_dti"])
        fn = p["name"]
        col = "#334155"
        rad = 4.2
        if "H33" in fn or "0.2778" in str(p["user_reported_live_dti"]):
            col, rad = "#0284c7", 6.2
            svg1.append(f'<text x="{cx - 8:.1f}" y="{cy - 8:.1f}" text-anchor="end" font-size="10.5" font-weight="700" fill="#0369a1">H33 (0.2778)</text>')
        elif "H19" in fn or abs(p["user_reported_live_dti"] - 0.1922) < 1e-4:
            col, rad = "#6366f1", 5.5
            svg1.append(f'<text x="{cx - 8:.1f}" y="{cy + 4:.1f}" text-anchor="end" font-size="10" font-weight="600" fill="#4f46e5">H19-5 (0.1922)</text>')
        elif "66" in fn or abs(p["user_reported_live_dti"] - 0.1152) < 1e-4:
            col, rad = "#d97706", 5.5
            svg1.append(f'<text x="{cx + 8:.1f}" y="{cy + 13:.1f}" font-size="10" font-weight="600" fill="#b45309">GEMSDOE66 (0.1152)</text>')
        svg1.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad}" fill="{col}" stroke="#ffffff" stroke-width="1"/>')

    svg1.append('<text x="283" y="400" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1e293b">Instrument C_pied DTI (Quaternary Piedmont SGMC Off-Catalogue)</text>')
    svg1.append('<text x="22" y="211" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1e293b" transform="rotate(-90 22 211)">User-Supplied Public Leaderboard DTI</text>')

    # Panel B: Bar Chart with Error Bars
    svg1.append('<rect x="575" y="66" width="470" height="290" fill="none" stroke="#cbd5e1" stroke-width="1"/>')

    def by(v: float) -> float:
        return 356.0 - (v / 0.205) * 290.0

    for gv in (0.0, 0.05, 0.10, 0.15, 0.20):
        yy = by(gv)
        svg1.append(f'<line x1="575" y1="{yy:.1f}" x2="1045" y2="{yy:.1f}" stroke="#e2e8f0" stroke-dasharray="3,3"/>')
        svg1.append(f'<text x="567" y="{yy + 4:.1f}" text-anchor="end" font-size="11" fill="#475569">{gv:.2f}</text>')

    groups = [
        ("Inst. A", "Hide-Recover", card["instrument_a_holdout"]["h33_reference"]["dti"], p4_a["scores"]["candidate"]["dti"], card["instrument_a_holdout"]["candidate"]),
        ("Inst. A_quad", "4-Quad Blind", card["instrument_a_quad_holdout"]["h19_5_oof_reference"]["dti"], 0.0, card["instrument_a_quad_holdout"]["candidate"]),
        ("Inst. B′", "SGMC d ≥ 3 px", card["instrument_b_prime_proxy"]["h33_reference"]["dti"], p4_bp["scores"]["candidate"]["dti"], card["instrument_b_prime_proxy"]["candidate"]),
        ("Inst. C_pied", "Live Calib.", card["instrument_c_pied_proxy"]["h33_reference"]["dti"], 0.0685, card["instrument_c_pied_proxy"]["candidate"]),
    ]
    for i, (g_top, g_sub, v_ref, v_p4, p5_d) in enumerate(groups):
        gx0 = 602.0 + i * 114.0
        # Ref bar (blue)
        svg1.append(f'<rect x="{gx0:.1f}" y="{by(v_ref):.1f}" width="25" height="{356.0 - by(v_ref):.1f}" fill="#0284c7" rx="2"/>')
        # P4 bar (slate)
        if v_p4 > 0:
            svg1.append(f'<rect x="{gx0 + 28:.1f}" y="{by(v_p4):.1f}" width="25" height="{356.0 - by(v_p4):.1f}" fill="#cbd5e1" stroke="#64748b" stroke-width="0.8" rx="2"/>')
        # P5 bar (emerald) + 95% CI whisker
        vp5 = p5_d["dti"]
        lo5, hi5 = p5_d["ci95"]
        bx5 = gx0 + 56.0
        svg1.append(f'<rect x="{bx5:.1f}" y="{by(vp5):.1f}" width="26" height="{356.0 - by(vp5):.1f}" fill="#059669" rx="2"/>')
        cx5 = bx5 + 13.0
        svg1.append(f'<line x1="{cx5:.1f}" y1="{by(hi5):.1f}" x2="{cx5:.1f}" y2="{by(lo5):.1f}" stroke="#064e3b" stroke-width="1.8"/>')
        svg1.append(f'<line x1="{cx5 - 5:.1f}" y1="{by(hi5):.1f}" x2="{cx5 + 5:.1f}" y2="{by(hi5):.1f}" stroke="#064e3b" stroke-width="1.8"/>')
        svg1.append(f'<line x1="{cx5 - 5:.1f}" y1="{by(lo5):.1f}" x2="{cx5 + 5:.1f}" y2="{by(lo5):.1f}" stroke="#064e3b" stroke-width="1.8"/>')
        svg1.append(f'<text x="{cx5:.1f}" y="{by(hi5) - 6:.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#065f46">{vp5:.4f}</text>')
        svg1.append(f'<text x="{gx0 + 41:.1f}" y="373" text-anchor="middle" font-size="11" font-weight="600" fill="#1e293b">{g_top}</text>')
        svg1.append(f'<text x="{gx0 + 41:.1f}" y="387" text-anchor="middle" font-size="10" fill="#64748b">{g_sub}</text>')

    # Legend inside top of Panel B
    svg1.append('<rect x="587" y="75" width="12" height="10" fill="#0284c7" rx="1"/><text x="604" y="84" font-size="10.5" fill="#1e293b">H33 Incumbent (H19-5 on A_quad)</text>')
    svg1.append('<rect x="795" y="75" width="12" height="10" fill="#cbd5e1" stroke="#64748b"/><text x="812" y="84" font-size="10.5" fill="#1e293b">Phase 4 Baseline</text>')
    svg1.append('<rect x="920" y="75" width="12" height="10" fill="#059669" rx="1"/><text x="937" y="84" font-size="10.5" font-weight="700" fill="#065f46">Phase 5 Promoted</text>')
    svg1.append('</svg>')
    (assets_dir / "phase5_calibration_ablation.svg").write_text("\n".join(svg1) + "\n")

    # -------------------------------------------------------------------------
    # SVG 2: 59-Raster Uniqueness Scatter (Mutual Overlap vs |Spearman rho|)
    # -------------------------------------------------------------------------
    def ux(v: float) -> float:
        return 80.0 + (v / 0.85) * 660.0

    def uy(v: float) -> float:
        return 318.0 - (v / 1.0) * 250.0

    svg2 = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 375" role="img" '
        'aria-label="59-Raster Parallel-Run Uniqueness Audit" '
        'style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#ffffff;border:1px solid #e2e8f0;border-radius:10px">',
        '<text x="410" y="29" text-anchor="middle" font-size="14" font-weight="700" fill="#0f172a">'
        'Parallel-Run Uniqueness Audit Across All 59 Archive &amp; Local Rasters (0 Duplicates)</text>',
        f'<rect x="80" y="{uy(0.90):.1f}" width="{ux(0.70) - 80:.1f}" height="{318.0 - uy(0.90):.1f}" fill="#ecfdf5" fill-opacity="0.7"/>',
        '<rect x="80" y="55" width="660" height="263" fill="none" stroke="#cbd5e1" stroke-width="1"/>',
        f'<line x1="{ux(0.70):.1f}" y1="55" x2="{ux(0.70):.1f}" y2="318" stroke="#dc2626" stroke-width="2" stroke-dasharray="6,4"/>',
        f'<text x="{ux(0.70) - 8:.1f}" y="76" text-anchor="end" font-size="11" font-weight="700" fill="#b91c1c">Mutual Overlap Limit = 0.70</text>',
        f'<line x1="80" y1="{uy(0.90):.1f}" x2="740" y2="{uy(0.90):.1f}" stroke="#7e22ce" stroke-width="2" stroke-dasharray="4,4"/>',
        f'<text x="92" y="{uy(0.90) + 16:.1f}" font-size="11" font-weight="700" fill="#6b21a8">|Spearman ρ| Limit = 0.90 (Pre-placement max |ρ| = 0.1588)</text>',
    ]
    for gx in (0.0, 0.20, 0.40, 0.60, 0.70, 0.80):
        xx = ux(gx)
        svg2.append(f'<text x="{xx:.1f}" y="335" text-anchor="middle" font-size="10.5" fill="#475569">{gx:.2f}</text>')
    for gy in (0.0, 0.30, 0.60, 0.90):
        yy = uy(gy)
        svg2.append(f'<text x="72" y="{yy + 4:.1f}" text-anchor="end" font-size="10.5" fill="#475569">{gy:.2f}</text>')

    for r in uniq["per_submission"]:
        mx = float(r["mutual_overlap"])
        my = abs(float(r["spearman_full_footprint"] or 0.0))
        sub = r["submission"]
        col, rad = "#059669", 4.5
        if "e5eb6e7e-nan" in sub:
            col, rad = "#0284c7", 6.2
            svg2.append(f'<text x="{ux(mx):.1f}" y="{uy(my) - 11:.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#0369a1">H33 (mutual={mx:.3f})</text>')
        elif "h33-h33-2" not in sub and mx > 0.44:
            col, rad = "#047857", 6.0
            svg2.append(f'<text x="{ux(mx):.1f}" y="{uy(my) + 19:.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#065f46">Max: {mx:.4f} (&lt; 0.70)</text>')
        svg2.append(f'<circle cx="{ux(mx):.1f}" cy="{uy(my):.1f}" r="{rad}" fill="{col}" fill-opacity="0.85" stroke="#0f172a" stroke-width="0.7"/>')

    svg2.append('<text x="410" y="360" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1e293b">Two-Direction Mutual 3-px Overlap  min(forward, reverse) Across All 59 Rasters</text>')
    svg2.append('<text x="24" y="186" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1e293b" transform="rotate(-90 24 186)">Full-Footprint |Spearman ρ|</text>')
    svg2.append('</svg>')
    (assets_dir / "phase5_uniqueness_audit.svg").write_text("\n".join(svg2) + "\n")


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    build_svg_charts(ASSETS)

    card = json.loads((ROOT / "evidence/phase5/run_card.json").read_text())
    p5_tif = ROOT / f"docs/downloads/{card['submission_name']}.tif"
    h33_tif = Path("/tmp/60GEMSDOE/registry/rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    ef_tif = ROOT / ".cache/data/existing_faults.tif"

    if p5_tif.is_file() and h33_tif.is_file() and ef_tif.is_file():
        with rasterio.open(ef_tif) as ds:
            ef = ds.read(1)
        fp = ef >= 0
        cat = ef == 1
        with rasterio.open(p5_tif) as ds:
            p5_dots = ds.read(1) > 0.5
        with rasterio.open(h33_tif) as ds:
            h33_dots = ds.read(1) > 0.5

        # Panel Left: 620 x 548 Regional Great Basin Overview (6x downsampled after morphological dilation)
        cat_d = maximum_filter(cat, size=5)[::6, ::6]
        h33_d = maximum_filter(h33_dots, size=6)[::6, ::6]
        p5_d = maximum_filter(p5_dots, size=6)[::6, ::6]
        fp_d = fp[::6, ::6]
        hl, wl = fp_d.shape  # 622 x 549

        left = np.full((hl, wl, 3), 255, dtype=np.uint8)
        left[fp_d] = [241, 245, 249]
        left[cat_d] = [100, 116, 139]
        left[h33_d] = [2, 132, 199]
        left[p5_d] = [5, 150, 105]
        left[h33_d & p5_d] = [234, 88, 12]

        # Draw red zoom indicator box around Central Nevada Piedmont (rows 1050..1672, cols 1200..1822)
        r0, r1, c0, c1 = 1050, 1050 + hl, 1200, 1200 + hl
        br0, br1, bc0, bc1 = r0 // 6, r1 // 6, c0 // 6, c1 // 6
        left[br0:br1, [bc0, bc0 + 1, bc1 - 1, bc1]] = [220, 38, 38]
        left[[br0, br0 + 1, br1 - 1, br1], bc0:bc1] = [220, 38, 38]

        # Panel Right: 622 x 622 exact 100 m native resolution crop of Central Nevada Geothermal Belt
        zoom = np.full((hl, hl, 3), 246, dtype=np.uint8)
        cat_z = maximum_filter(cat[r0:r1, c0:c1], size=2)
        h33_z = maximum_filter(h33_dots[r0:r1, c0:c1], size=3)
        p5_z = maximum_filter(p5_dots[r0:r1, c0:c1], size=3)
        zoom[cat_z] = [71, 85, 105]
        zoom[h33_z] = [2, 132, 199]
        zoom[p5_z] = [5, 150, 105]
        zoom[h33_z & p5_z] = [234, 88, 12]

        # Combine side-by-side with clean white divider
        sep = np.full((hl, 24, 3), 255, dtype=np.uint8)
        canvas = np.concatenate([left, sep, zoom], axis=1)
        write_png_rgb(ASSETS / "phase5_map_comparison.png", canvas)

    print("Generated Retina SVGs + lossless RGB spatial PNG in docs/assets/!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
