#!/usr/bin/env python3
"""Re-audit immutable P5 TIFF bytes after concurrent main integration.

This is *not* a new experiment, training run, model choice or parameter search.
It verifies the file hash/format and rescans the expanded local registry,
correcting only human-readable registry submission IDs and the number of
quadrants represented in the metadata. Historical scores are not recomputed.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor'), str(ROOT / 'scripts')]

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57 import holdout
from gems57.grid import load_grid
from gems57.validate import validate, assert_submittable
from run_experiment_p5_cover import DATA, E, NAME, registry_surface_scan, sha, dump


def main():
    card_p = E / 'run_card.json'
    scan_p = E / 'surface_registry.json'
    card = json.loads(card_p.read_text())
    first_scan = json.loads(scan_p.read_text())
    f = ROOT / 'docs/downloads' / (NAME + '.tif')
    original_sha = card['raster_sha256']
    if sha(f) != original_sha:
        raise ValueError('P5 TIFF differs from originally scored/written bytes')
    grid = load_grid(DATA)
    with rasterio.open(f) as d:
        arr = d.read(1)
        with rasterio.open(DATA / 'sample_submission.tif') as s:
            if (d.shape, d.crs, d.transform) != (s.shape, s.crs, s.transform):
                raise ValueError('published grid drifted from sample')
    val = validate(f, grid.footprint, grid.catalogue)
    assert_submittable(val)
    if val['sha256'] != original_sha:
        raise ValueError('validation receipt file identity differs')
    scan = registry_surface_scan(arr, grid)
    if (scan['worst_spearman_full_footprint'] is None or
            scan['worst_spearman_full_footprint'] > .90 or
            not scan['literal_positive_support_duplicate'] or
            scan['forward_overlap_3px_if_positive_cells_count_as_dots'] != 1.0 or
            scan['binary_one_dots'] != 0):
        raise ValueError('P5 literal stop or surface result has changed')
    if not np.array_equal(arr[grid.catalogue], np.zeros(int(grid.catalogue.sum()), np.float32)):
        raise ValueError('nonzero on catalogue')

    # Saved P4 holdout used the RTP-valid eroded domain; the run asserts that
    # this equals P5's joint-valid eroded domain. Count actual quadrant pixels.
    with rasterio.open(DATA / 'training_features.tif') as s:
        rtp = s.read(2)
    valid = ndi.binary_erosion(grid.footprint & (rtp > -1e30) & np.isfinite(rtp), iterations=12)
    quad = holdout.quadrant_ids(grid.footprint)
    regions = [ndi.binary_erosion(quad == k, iterations=12) & valid for k in range(4)]
    train_pixels = [sum(int(regions[j].sum()) for j in range(4) if j != k)
                    for k in range(4)]
    prod_pixels = sum(int(r.sum()) for r in regions)
    training = json.loads((E / 'training_receipts.json').read_text())
    if len(training) != 4:
        raise ValueError('not four saved training receipts')
    # A re-verification must not rewrite or pretend to run another scientific
    # experiment. Once corrected, verify all saved measurements and return.
    if all('train_region_pixels' in r and 'independent_train_quadrants' not in r for r in training):
        if ([r['train_region_pixels'] for r in training] != train_pixels
                or card['production_train_receipt'].get('train_region_pixels') != prod_pixels
                or card['method_source_sha256']['scripts/run_experiment_p5_cover.py'] != sha(ROOT / 'scripts/run_experiment_p5_cover.py')):
            raise ValueError('saved training/source metadata differs from immutable TIFF recheck')
        old_count = first_scan['registry_rasters_checked']
        new_count = scan['registry_rasters_checked']
        if new_count < old_count:
            raise ValueError('accessible registry shrank; cannot imply uniqueness from fewer rasters')
        old_by_hash = {(row['sha256'], row['submission']): row for row in first_scan['rows']}
        current_by_hash = {(row['sha256'], row['submission']): row for row in scan['rows']}
        for key, prior in old_by_hash.items():
            current = current_by_hash.get(key)
            if not current or not np.isclose(prior['spearman_full_footprint'],
                                             current['spearman_full_footprint'], atol=1e-10, rtol=0):
                raise ValueError('old registry measurement drifted at ' + str(key))
        if new_count > old_count:
            # Only this metadata may change: no fitting, no scoring, no TIFF write.
            dump(E / f'surface_registry_{old_count}.json', first_scan)
            dump(scan_p, scan)
            corr = card['correlation_overlap_vs_registry']
            corr.update(rasters_checked=new_count,
                        inventory_scope=scan['scope_note'],
                        worst_spearman_full_footprint=scan['worst_spearman_full_footprint'],
                        worst_rho_submission=scan['worst_rho_submission'],
                        forward_overlap_positive_support_lattice=scan['forward_overlap_3px_if_positive_cells_count_as_dots'],
                        positive_support_pixels=scan['continuous_positive_pixels'],
                        binary_one_dots=scan['binary_one_dots'],
                        shared_tool_dot_uniqueness=scan['unique'])
            card['reporting_amendment'] += (f' New concurrent inventory expands scan {old_count}->{new_count}; '
                                            'TIFF and fold scores unchanged.')
            dump(card_p, card)
            amendment_path = E / 'reporting_amendment.json'
            amendment = json.loads(amendment_path.read_text())
            amendment['expanded_inventory'] = dict(from_rasters=old_count, to_rasters=new_count,
                max_rho_after=scan['worst_spearman_full_footprint'],
                literal_positive_support_forward_overlap=scan['forward_overlap_3px_if_positive_cells_count_as_dots'],
                tiff_sha256_unchanged=sha(f), no_retraining=True, no_rescoring=True)
            dump(amendment_path, amendment)
        elif not np.isclose(first_scan['worst_spearman_full_footprint'],
                            scan['worst_spearman_full_footprint'], rtol=0, atol=1e-10):
            raise ValueError('saved P5 registry rho changed without a new raster')
        print(json.dumps({'immutable_tiff_sha256': sha(f),
                          'validated': val['all_checks_passed'],
                          'rasters_checked': new_count,
                          'literal_positive_support_forward_overlap': scan['forward_overlap_3px_if_positive_cells_count_as_dots'],
                          'reporting_metadata_unchanged': new_count == old_count,
                          'scores_recomputed': False}, indent=2))
        return
    if any('independent_train_quadrants' not in r for r in training):
        raise ValueError('partially corrected P5 training metadata: refuse mutation')
    before = {'source_sha256': card['method_source_sha256']['scripts/run_experiment_p5_cover.py'],
              'rasters_checked': first_scan['registry_rasters_checked'],
              'worst_rho': first_scan['worst_spearman_full_footprint'],
              'artifact_sha256': original_sha,
              'training_metadata': [r['independent_train_quadrants'] for r in training]}
    for row, n in zip(training, train_pixels):
        row.pop('independent_train_quadrants')
        row['train_region_pixels'] = n
    card['production_train_receipt'].pop('independent_train_quadrants')
    card['production_train_receipt']['train_region_pixels'] = prod_pixels
    card['correlation_overlap_vs_registry'].update(
        rasters_checked=scan['registry_rasters_checked'],
        inventory_scope=scan['scope_note'],
        worst_spearman_full_footprint=scan['worst_spearman_full_footprint'],
        worst_rho_submission=scan['worst_rho_submission'],
        forward_overlap_positive_support_lattice=scan['forward_overlap_3px_if_positive_cells_count_as_dots'],
        positive_support_pixels=scan['continuous_positive_pixels'],
        binary_one_dots=scan['binary_one_dots'],
        shared_tool_dot_uniqueness=scan['unique'])
    card['method_source_sha256']['scripts/run_experiment_p5_cover.py'] = sha(ROOT / 'scripts/run_experiment_p5_cover.py')
    card['reporting_amendment'] = ('After concurrent main integration: re-read unchanged TIFF; '
                                   'expanded comparison from 66 to current registry; repaired '
                                   'mislabelled training-region metadata, NOT the model or scores.')
    dump(E / 'surface_registry_initial.json', first_scan)
    dump(scan_p, scan)
    dump(E / 'training_receipts.json', training)
    dump(card_p, card)
    dump(E / 'reporting_amendment.json', dict(
        evidence_class='AUDIT-METADATA-CORRECTION',
        what='Immutable TIFF re-read, current-registry re-scan and descriptive metadata repair only',
        original=before,
        new=dict(source_sha256=card['method_source_sha256']['scripts/run_experiment_p5_cover.py'],
                 rasters_checked=scan['registry_rasters_checked'],
                 worst_rho=scan['worst_spearman_full_footprint'],
                 worst_rho_submission=scan['worst_rho_submission'],
                 train_region_pixels=train_pixels,
                 production_train_region_pixels=prod_pixels,
                 artifact_sha256=sha(f)),
        no_retraining=True, no_rescoring=True,
        test_scores_unchanged=True,
        literal_positive_support_duplicate=True,
        weekly_slots_used=0,
    ))
    print(json.dumps({
        'file_sha256_unchanged': sha(f),
        'validated': val['all_checks_passed'],
        'registry_checked': scan['registry_rasters_checked'],
        'max_spearman': scan['worst_spearman_full_footprint'],
        'worst_rho_submission': scan['worst_rho_submission'],
        'positive_support_forward_overlap': scan['forward_overlap_3px_if_positive_cells_count_as_dots'],
        'training_region_pixels': train_pixels}, indent=2))


if __name__ == '__main__':
    main()
