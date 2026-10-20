#!/usr/bin/env python3
"""Recheck the user's forward-overlap stop against a pinned, binary registry TIFF.

This is a read-only scientific preflight. It does NOT emit, select, or repair a
submission. The shared template supplies the grid, 3-pixel dot comparator and
on-disk GeoTIFF validator; no private scoring or duplicate-detection fork is
introduced. `--check` independently recomputes the committed receipt (CI).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from gems57 import uniqueness  # noqa: E402
from gems57.grid import load_grid, SHA256_EXISTING_FAULTS, SHA256_SAMPLE_SUBMISSION  # noqa: E402
from gems57.validate import validate  # noqa: E402

INDEX = ROOT / 'registry/inherited_registry_index.json'
INVENTORY = ROOT / 'registry/published_artifacts.json'
RECEIPT = ROOT / 'evidence/literal_overlap_stop.json'
LATTICE_SHA = 'b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2'
ARCHIVES = (
    'docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif',
    'docs/downloads/gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif',
    'docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif',
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def get_lattice(index: dict) -> tuple[Path, dict]:
    matches = [r for r in index['rasters'] if r['sha256'] == LATTICE_SHA]
    if len(matches) != 1 or '13GEMSDOE' not in matches[0]['repo_first']:
        raise ValueError('pinned registry witness missing or ambiguous')
    spec = matches[0]
    target = ROOT / '.cache/registry' / f'{LATTICE_SHA}.tif'
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.partial')
        try:
            with temporary.open('wb') as out:
                subprocess.run(['gh', 'api',
                                f"repos/buffedlizard55-lab/{spec['repo_first']}/git/blobs/{spec['blob']}",
                                '-H', 'Accept: application/vnd.github.raw'],
                               stdout=out, check=True, timeout=180)
            if sha(temporary) != LATTICE_SHA or temporary.stat().st_size != spec['bytes']:
                raise ValueError('registry fetch differs from pinned blob: stop')
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    if sha(target) != LATTICE_SHA or target.stat().st_size != spec['bytes']:
        raise ValueError('cached witness differs from registry pin: stop')
    return target, spec


def budget_lower_bound(uncovered: int, budget: int) -> float:
    """Best-case forward overlap if ALL uncovered off-catalogue cells are dots.

    This is an optimistic geometric bound, not a model score or evidence that a
    particular distribution is geologically plausible. Do not use to tune dots.
    """
    if uncovered < 0 or budget < 1:
        raise ValueError('nonnegative uncovered count and positive budget required')
    return max(0, budget - uncovered) / budget


def coverage_stats(covered: np.ndarray, footprint: np.ndarray,
                   catalogue: np.ndarray, budget: int) -> dict:
    covered = np.asarray(covered, bool)
    fp = np.asarray(footprint, bool)
    cat = np.asarray(catalogue, bool)
    if covered.shape != fp.shape or cat.shape != fp.shape or not fp.any():
        raise ValueError('coverage must match a nonempty grid')
    allowed = fp & ~cat
    if not allowed.any():
        raise ValueError('no off-catalogue cells')
    uncovered = int((allowed & ~covered).sum())
    # (budget - uncovered) / budget <= .70 iff 3*budget <= 10*uncovered.
    return {
        'footprint_cells': int(fp.sum()),
        'off_catalogue_cells': int(allowed.sum()),
        'witness_halo_covered_off_catalogue': int((allowed & covered).sum()),
        'witness_halo_uncovered_off_catalogue': uncovered,
        'witness_halo_fraction_off_catalogue': float(covered[allowed].mean()),
        'min_possible_forward_overlap_at_archived_budget': budget_lower_bound(uncovered, budget),
        'largest_budget_not_ruled_out_by_this_witness_alone': (10 * uncovered) // 3,
        'caveat': 'Optimistic bound ignores spacing, geology and other rasters; a smaller budget is not a clearance.',
    }


def audit() -> dict:
    for name, pin in [('sample_submission.tif', SHA256_SAMPLE_SUBMISSION),
                      ('existing_faults.tif', SHA256_EXISTING_FAULTS)]:
        if sha(ROOT / 'data/bridge' / name) != pin:
            raise ValueError('bridge mirror pin mismatch: ' + name)
    g = load_grid(ROOT / 'data/bridge')
    index = json.loads(INDEX.read_text())
    path, spec = get_lattice(index)
    with rasterio.open(path) as ds:
        if (ds.count, ds.dtypes[0], ds.shape, ds.crs, ds.transform) != (
                1, 'float32', g.shape, g.crs, g.transform):
            raise ValueError('pinned lattice is not a single-band float32 on the sample grid')
        lattice = ds.read(1)
    lattice_dots = uniqueness._dots(lattice) & g.footprint
    # Match shared radius/geometry exactly (Euclidean <= 3 px).
    halo = uniqueness._near(lattice_dots)
    archive_pins = {a['path']: a['sha256'] for a in json.loads(INVENTORY.read_text())['artifacts']}
    results = []
    for rel in ARCHIVES:
        target = ROOT / rel
        if rel not in archive_pins or sha(target) != archive_pins[rel]:
            raise ValueError('archived TIFF missing or differs from inventory: ' + rel)
        validator = validate(target, g.footprint, g.catalogue)
        with rasterio.open(target) as ds:
            if (ds.shape, ds.crs, ds.transform) != (g.shape, g.crs, g.transform):
                raise ValueError('archived TIFF grid mismatch: ' + rel)
            prediction = ds.read(1)
        dots = uniqueness._dots(prediction) & g.footprint
        if not dots.any() or int(dots.sum()) != validator['in_footprint_positive_pixels']:
            raise ValueError('archive is not a binary dot field: ' + rel)
        forward = uniqueness.dot_overlap(prediction, lattice)
        # Surface correlation is diagnostic; the forward result alone is a stop.
        rho = uniqueness.surface_rho(prediction, lattice, g.footprint)['spearman_full_footprint']
        if not validator['all_checks_passed']:
            raise ValueError('archived local format check failed: ' + rel)
        results.append({
            'file': rel, 'sha256': validator['sha256'], 'binary_dots': int(dots.sum()),
            'forward_overlap_within_3px': forward,
            'spearman_full_footprint': rho if np.isfinite(rho) else None,
            'duplicate_under_user_rule': bool(forward > uniqueness.OVERLAP_LIMIT or
                                              (np.isfinite(rho) and rho > uniqueness.RHO_LIMIT)),
            'shared_validator': {
                'sha256': validator['sha256'], 'checks': validator['checks'],
                'all_checks_passed': validator['all_checks_passed'],
                'min': validator['min'], 'max': validator['max'], 'n_nan': validator['n_nan'],
                'crs': validator['meta']['crs'], 'shape': validator['meta']['shape'],
                'transform': validator['meta']['transform'],
            },
        })
    historic = results[0]
    stats = coverage_stats(halo, g.footprint, g.catalogue, historic['binary_dots'])
    return {
        'evidence_class': 'REGISTRY-MEASUREMENT + LOCAL-VALIDATOR; not HOLDOUT-DTI or ORGANIZER-CONFIRMED',
        'scope': 'One pinned public owner-registry raster is sufficient to stop the archived files; NOT a complete registry clearance.',
        'registry_index': 'registry/inherited_registry_index.json',
        'registry_index_sha256': sha(INDEX),
        'witness': {
            'repo': spec['repo_first'], 'git_blob': spec['blob'],
            'source': next(s for s in spec['sources'] if s.startswith('13GEMSDOE:')),
            'url': f"https://api.github.com/repos/buffedlizard55-lab/{spec['repo_first']}/git/blobs/{spec['blob']}",
            'sha256': sha(path), 'bytes': path.stat().st_size,
            'binary_dot_count': int(lattice_dots.sum()),
            'grid_match': True, 'dot_rule': 'shared binary 1.0 support',
        },
        'coverage': stats,
        'thresholds': {'rho_gt': uniqueness.RHO_LIMIT, 'forward_overlap_gt': uniqueness.OVERLAP_LIMIT,
                       'radius_px': 3},
        'archive_checks': results,
        'historical_claim_correction': 'The witness does not cover 100% of allowed cells; earlier blanket-universal statements were too strong.',
        'new_surface_checked': False, 'new_final_dots_checked': False,
        'new_raster_generated': False, 'new_holdout_run': False,
        'no_submission_slot_used': True, 'verdict': 'negative',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='recompute and compare to committed evidence')
    args = parser.parse_args()
    result = audit()
    if args.check:
        if not RECEIPT.exists() or json.loads(RECEIPT.read_text()) != result:
            raise ValueError('literal stop receipt stale; rerun audit and review before publishing')
    else:
        RECEIPT.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'witness': result['witness']['sha256'],
                      'coverage': result['coverage'],
                      'archive_stops': {row['file']: row['forward_overlap_within_3px']
                                        for row in result['archive_checks']}}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
