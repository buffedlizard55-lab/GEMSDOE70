#!/usr/bin/env python3
"""Re-audit E2 candidate against all 62 registry rasters under the corrected mutual-overlap rule.

Executes AGENTS.md addendum:
'E2 uniqueness numbers predate the mutual-overlap fix (R1 subset audit). Re-audit E2 under
the corrected rule before comparing uniqueness across lanes.'
Does NOT modify frozen evidence/e2/* files; writes evidence/phase5/e2_uniqueness_62rasters_corrected.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]

import rasterio
from gems57 import uniqueness
from gems57.grid import load_grid
from restore_data import DATA, sha

CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE / 'registry' / 'rasters'
E2_TIF = ROOT / 'docs/downloads/gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif'
OUT = ROOT / 'evidence' / 'phase5' / 'e2_uniqueness_62rasters_corrected.json'


def main():
    grid = load_grid(DATA)
    fp = grid.footprint
    records = []
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count != 1 or (src.height, src.width) != grid.shape:
                continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name,
                            sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index = dict(complete_accessible_scan=True, errors=[], rasters=records)
    audit = uniqueness.compare_to_registry(
        E2_TIF, index, fp, expected_grid=(grid.shape, grid.crs, grid.transform)
    )
    audit['candidate_file'] = str(E2_TIF.relative_to(ROOT))
    audit['candidate_sha256'] = sha(E2_TIF)
    audit['inventory_scope'] = (
        f'{len(records)} single-band 100 m rasters archived in '
        'buffedlizard55-lab/60GEMSDOE registry/rasters; re-audited under corrected '
        'binary-dot (|v-1|<1e-6) and mutual-overlap (min(forward,reverse)>0.70) rule'
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=2, allow_nan=False, default=float) + '\n')
    print(json.dumps({
        'candidate_file': audit['candidate_file'],
        'candidate_sha256': audit['candidate_sha256'],
        'registry_rasters_checked': audit['registry_rasters_checked'],
        'unique': audit['unique'],
        'duplicate_count': audit['duplicate_count'],
        'worst_mutual_overlap': audit['worst_dot_overlap'],
        'worst_overlap_submission': audit['worst_overlap_submission'],
        'worst_forward_overlap': audit['worst_forward_overlap'],
        'worst_forward_submission': audit['worst_forward_submission'],
        'worst_spearman_full_footprint': audit['worst_spearman_full_footprint'],
        'worst_rho_submission': audit['worst_rho_submission'],
        'worst_jaccard_dot_sets': audit['worst_jaccard_dot_sets'],
    }, indent=2))


if __name__ == '__main__':
    main()
