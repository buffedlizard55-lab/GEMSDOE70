"""Build the C1 final surface on the FULL mapped catalogue and write a validated GeoTIFF.

This is a packaging step, not a promotion. The holdout gate (evidence/c1_result.json) was
measured as FAILED, so the file is labelled NOT-CLEARED in its name and receipt. The shared
writer enforces: float32, finite values in [0,1], positive mass only inside the footprint,
zero mass on mapped faults, EPSG:32611 / 100 m / same extent as the sample. It refuses to
overwrite existing outputs.

Output: submissions/ (git-ignored). Receipts: evidence/c1_export_receipt.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]
import numpy as np
from scipy import ndimage as ndi
import rasterio

from gems57 import grid, submission_writer
from gems57.grid import load_grid
from gems70 import strike
from gems70.method import upper_surface
from restore_data import DATA, PINS, sha
from validate_submission import run_validation

NAME = 'gems70-c1-strike-catalogue-NOT-CLEARED-20261020'
NOTE = 'C1 strike-coherent catalogue extrapolation. Holdout below random control. Do not submit.'
OUT = ROOT / 'submissions' / f'{NAME}.tif'
E = ROOT / 'evidence'


def main() -> int:
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError('input pin mismatch: ' + name)
    g = load_grid(DATA)
    fp = g.footprint
    with rasterio.open(DATA / 'training_features.tif') as src:
        hits = [i + 1 for i, d in enumerate(src.descriptions) if d and d.split(' ')[0].split('-')[0].strip() == 'rtp']
        if hits != [2]:
            raise ValueError(f'rtp band not uniquely identified: {hits}')
        rtp = src.read(2).astype(np.float32)
    rtp[(rtp <= -1e30) | ~np.isfinite(rtp) | ~fp] = np.nan
    valid = ndi.binary_erosion(fp & np.isfinite(rtp), iterations=12)
    # FINAL export uses the FULL mapped catalogue (training labels), not the holdout-visible mask.
    feats = strike.features(rtp, g.catalogue, valid)
    surface = upper_surface(strike.combine(feats, valid, 'candidate'), valid)
    surface = np.where(valid & ~g.catalogue, surface, 0.0).astype(np.float32)
    np.save(ROOT / '.cache' / 'c1_final_surface.npy', surface)
    receipt = submission_writer.write_submission(
        OUT, surface, DATA / 'sample_submission.tif', fp, note=NOTE, name=NAME,
        catalogue=g.catalogue, metadata={'method': 'C1 strike-coherent catalogue extrapolation',
                                         'holdout_gate': 'FAILED (evidence/c1_result.json)',
                                         'organizer_confirmed_score': None})
    report = run_validation(OUT)
    (E / 'c1_final_validation.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    out = {
        'evidence_class': 'LOCAL-FORMAT-VALIDATION-NOT-ORGANIZER-ACCEPTANCE',
        'file': str(OUT.relative_to(ROOT)), 'name': NAME, 'note': NOTE,
        'note_chars': len(NOTE), 'name_chars': len(NAME),
        'sha256': receipt['sha256'], 'bytes': receipt['bytes'],
        'zip_file': receipt['zip_file'], 'zip_sha256': receipt['zip_sha256'],
        'positive_pixels': int((surface > 0).sum()),
        'catalogue_positive_pixels': int((surface[g.catalogue] > 0).sum()),
        'outside_footprint_positive': int((surface[~fp] > 0).sum()),
        'min': float(surface[fp].min()), 'max': float(surface[fp].max()),
        'nan_count': int(np.isnan(surface).sum()),
        'download_and_submit_ok': False,
        'reason': 'Holdout gate failed: C1 HOLDOUT-DTI is below the random sparse control (see evidence/c1_result.json).',
        'local_format_pass': report.get('local_format_pass'),
        'validator_errors': report.get('error'),
    }
    (E / 'c1_export_receipt.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    print(json.dumps(out, indent=2, allow_nan=False))
    return 0 if out['local_format_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
