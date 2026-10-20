"""Complete literal uniqueness scan of a candidate GeoTIFF against the indexed registry.

Uses the SHARED comparator (vendor/gems57/uniqueness.py) and its literal thresholds
(Spearman > 0.90 or forward 3 px dot overlap > 0.70). Nothing is exempted or reinterpreted.
Rasters come from .cache/registry (fetched by scripts/fetch_registry_full.py, SHA-verified).

Also records each registry raster's support fraction, so dense continuous surfaces that
make the literal overlap rule degenerate are visible for human review. The scan itself
never clears or blocks a file; it writes evidence only.

Limitation: the index was generated 2026-10-12. Repos changed after that date are NOT
covered unless the index is regenerated (see docs/irregularities.md).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]
import numpy as np
import rasterio

from gems57 import uniqueness
from gems57.grid import load_grid
from restore_data import DATA

INDEX = ROOT / 'registry' / 'inherited_registry_index.json'
CACHE = ROOT / '.cache' / 'registry'


def local_index():
    idx = json.loads(INDEX.read_text())
    rasters = []
    missing = []
    for r in idx['rasters']:
        p = CACHE / f"{r['sha256']}.tif"
        if not p.exists():
            missing.append(r['sha256'])
        rasters.append({**r, 'cache_file': str(p.relative_to(ROOT))})
    return {**idx, 'rasters': rasters, 'complete_accessible_scan': not missing,
            'errors': [f'missing cache for {len(missing)} rasters'] if missing else []}, missing


def main(candidate_tif: str, out_json: str, mine_name: str) -> int:
    grid = load_grid(DATA)
    fp = grid.footprint
    with rasterio.open(candidate_tif) as src:
        if src.count != 1 or src.dtypes[0] != 'float32':
            raise ValueError('candidate must be single-band float32')
        cand = src.read(1).astype(np.float32)
        cand_crs, cand_tf, cand_shape = src.crs, src.transform, src.shape
    cand = np.where(np.isfinite(cand), cand, 0.0).astype(np.float32)
    idx, missing = local_index()
    if missing:
        raise SystemExit(f'registry cache incomplete: {len(missing)} missing')
    expected = (grid.shape, grid.crs, grid.transform)
    audit = uniqueness.compare_array_to_registry(
        cand, idx, fp, include_reverse=True, expected_grid=expected)
    footprint_cells = int(fp.sum())
    # Classify each registry raster by support density (no thresholds changed).
    kinds = {}
    for row in audit['rows']:
        if 'their_dots' in row:
            info = uniqueness.representation_class(row['their_dots'], footprint_cells)
            row['representation'] = info['kind']
            row['their_support_fraction'] = round(info['support_fraction'], 6)
            kinds[info['kind']] = kinds.get(info['kind'], 0) + 1
    my_dots = int(((cand > 0) & fp).sum())
    summary = {k: audit[k] for k in (
        'registry_rasters_expected', 'registry_rasters_checked', 'complete_accessible_scan',
        'missing_or_invalid', 'worst_spearman_full_footprint', 'worst_rho_submission',
        'worst_dot_overlap', 'worst_overlap_submission', 'worst_jaccard_dot_sets',
        'worst_jaccard_submission', 'byte_unique_among_checked', 'pixel_unique_among_checked',
        'duplicate_count', 'unique', 'verdict', 'stop_required')}
    rows = audit['rows']
    dup_overlap = [r for r in rows if r.get('duplicate_by_overlap')]
    dup_rho = [r for r in rows if r.get('duplicate_by_rho')]
    n_dense_dup = sum(1 for r in dup_overlap if r.get('representation') == 'continuous_surface')
    result = {
        'evidence_class': 'REGISTRY-MEASUREMENT',
        'candidate': mine_name,
        'candidate_file_sha256': uniqueness._sha(Path(candidate_tif)),
        'candidate_decoded_sha256': __import__('hashlib').sha256(np.ascontiguousarray(cand).tobytes()).hexdigest(),
        'candidate_grid': {'crs': str(cand_crs), 'shape': list(cand_shape)},
        'my_dots': my_dots,
        'footprint_cells': footprint_cells,
        'index_generated_utc': idx.get('generated_utc'),
        'index_scope': idx.get('scope'),
        'thresholds': {'spearman_gt': uniqueness.RHO_LIMIT, 'overlap_gt': uniqueness.OVERLAP_LIMIT,
                       'jaccard_gt_diagnostic_only': uniqueness.JACCARD_LIMIT},
        'summary': summary,
        'duplicate_by_overlap_count': len(dup_overlap),
        'duplicate_by_overlap_on_continuous_surfaces': n_dense_dup,
        'duplicate_by_overlap_on_dot_fields': len(dup_overlap) - n_dense_dup,
        'duplicate_by_rho_count': len(dup_rho),
        'representation_counts': kinds,
        'rows': rows,
    }
    Path(out_json).write_text(json.dumps(result, indent=2, allow_nan=False, default=float) + '\n')
    print(json.dumps({k: result[k] for k in ('my_dots', 'duplicate_by_overlap_count',
                      'duplicate_by_overlap_on_continuous_surfaces', 'duplicate_by_overlap_on_dot_fields',
                      'duplicate_by_rho_count', 'representation_counts')}, indent=2))
    print(json.dumps(summary, indent=2, default=float))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
