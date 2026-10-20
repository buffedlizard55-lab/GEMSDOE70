#!/usr/bin/env python3
"""Descriptive receipt: catalogue-distance and terrain marginals of key dot files (no scoring)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]
import numpy as np, rasterio
from scipy import ndimage as ndi
from gems57.grid import load_grid
from restore_data import DATA, sha
R = Path('/tmp/60GEMSDOE/registry/rasters')
AUX = Path('/tmp/60GEMSDOE/data/external')
FILES = {
    'S3-E1 (this session)': ROOT / 'docs/downloads/gems70-s3-proxyrank-h33spacing-37654-20261020-DO-NOT-SUBMIT.tif',
    'S3-E2 (this session)': ROOT / 'docs/downloads/gems70-s3e2-marginmatched-proxyrank-37654-20261020-DO-NOT-SUBMIT.tif',
    'H33 (reported 0.2778)': R / 'dotted_b2_prune_02778.tif',
    'H27 (reported 0.2708)': R / 'dotted_d2_8_02708.tif',
    'D28 (reported 0.2600)': R / 'dotted_d2_8_02600.tif',
    'gate_ortho (reported 0.2376)': R / 'GEMSDOE49__gate_ortho_w0.25-40k.tif',
    'anderson PINN (reported 0.2750)': R / 'GEMSDOE36__anderson-geothermal-pinn-38854.tif',
    'P4 (session 2, unscored)': ROOT / 'docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif',
}
g = load_grid(DATA); fp, cat = g.footprint, g.catalogue
d = ndi.distance_transform_edt(~cat)
with rasterio.open(AUX / 'topo_10m_derived_100m_u8.tif') as s:
    slope = s.read(1)
q75 = float(np.percentile(slope[fp & (slope > 0)], 75))
rows = []
for k, f in FILES.items():
    with rasterio.open(f) as s:
        a = s.read(1)
    m = np.isfinite(a) & (a > 0.5) & fp
    dd = d[m]
    rows.append(dict(label=k, file=f.name, sha256=sha(f), dots=int(m.sum()),
                     d_px_quantiles_5_25_50_75_95=[float(v) for v in np.percentile(dd, [5, 25, 50, 75, 95])],
                     frac_d_le_6px=float((dd <= 6).mean()), frac_d_le_15px=float((dd <= 15).mean()),
                     frac_steep_top_quartile=float((slope[m] > q75).mean())))
out = dict(evidence_class='DATA-MEASUREMENT (descriptive; live scores are owner/user-reported)',
           steep_definition=f'topo_10m_derived_100m_u8 band 1 (slope_p90) u8 code > {q75} (footprint 75th pct)',
           rows=rows)
(ROOT / 'evidence/s3/terrain_marginals.json').write_text(json.dumps(out, indent=2) + '\n')
for r in rows:
    print(f"{r['label']:32s} steep={r['frac_steep_top_quartile']:.3f} d<=6={r['frac_d_le_6px']:.3f} median_d={r['d_px_quantiles_5_25_50_75_95'][2]:.1f}")
