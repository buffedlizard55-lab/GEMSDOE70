#!/usr/bin/env python3
"""Reproduce the negative preflight without generating predictions or using a slot."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor')]
from gems57 import grid, uniqueness


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def check_template():
    manifest = json.loads((ROOT / 'registry/template_pin.json').read_text())
    rows = []
    for item in manifest['files']:
        p = ROOT / 'vendor/gems57' / item['file']
        actual = sha(p) if p.is_file() else None
        rows.append(dict(file=item['file'], sha256=actual, match=actual == item['sha256']))
    return dict(ok=all(r['match'] for r in rows), files=rows,
                template_repo=manifest['template_repo'], template_commit=manifest['template_commit'])


def coverage_report(witness, footprint):
    """Measure support on the exact footprint; do not threshold dense scores away."""
    a, fp = np.asarray(witness), np.asarray(footprint, bool)
    if a.shape != fp.shape or not fp.any():
        raise ValueError('matching nonempty footprint required')
    finite = bool(np.isfinite(a[fp]).all())
    count = int(((a > 0) & fp).sum())
    total = int(fp.sum())
    universal = finite and count == total
    return dict(footprint_pixels=total, positive_footprint_pixels=count,
                finite_inside_footprint=finite, strictly_positive_on_entire_footprint=universal,
                support_fraction=count / total,
                minimum_inside_footprint=float(a[fp].min()) if finite else None,
                maximum_inside_footprint=float(a[fp].max()) if finite else None,
                implied_forward_overlap_for_any_nonempty_in_footprint_candidate=1.0 if universal else None)


def fetch_witness(spec):
    p = ROOT / spec['cache_path']
    if p.is_file() and sha(p) == spec['sha256']:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.partial')
    try:
        with tmp.open('wb') as out:
            subprocess.run(['gh', 'api', f"repos/{spec['repo']}/git/blobs/{spec['git_blob']}",
                            '-H', 'Accept: application/vnd.github.raw'], stdout=out, check=True)
        if sha(tmp) != spec['sha256'] or tmp.stat().st_size != spec['bytes']:
            raise ValueError('registry witness integrity mismatch')
        tmp.replace(p)
    finally:
        tmp.unlink(missing_ok=True)
    return p


def main():
    template = check_template()
    if not template['ok']:
        raise ValueError('shared template byte drift; refusing audit')
    for name, pin in [('sample_submission.tif', grid.SHA256_SAMPLE_SUBMISSION),
                      ('existing_faults.tif', grid.SHA256_EXISTING_FAULTS)]:
        if sha(ROOT / 'data/bridge' / name) != pin:
            raise ValueError(f'{name}: mirror pin mismatch')
    g = grid.load_grid(ROOT / 'data/bridge')
    spec = json.loads((ROOT / 'registry/witness.json').read_text())
    index = json.loads((ROOT / spec['inherited_registry']).read_text())
    member = any(r['sha256'] == spec['sha256'] and r['blob'] == spec['git_blob']
                 for r in index['rasters'])
    if not member:
        raise ValueError('witness is not a member of the recorded registry')
    p = fetch_witness(spec)
    with rasterio.open(p) as ds:
        match = ds.shape == g.shape and ds.crs == g.crs and ds.transform == g.transform
        if ds.count != 1 or not match:
            raise ValueError('registry witness is not aligned to the sample grid')
        coverage = coverage_report(ds.read(1), g.footprint)
    if not coverage['strictly_positive_on_entire_footprint']:
        raise ValueError('universal-overlap proof not established; investigate, do not assume clearance')
    certificate = uniqueness.saturation_certificate(p, g.footprint,
        expected_grid=(g.shape, g.crs, g.transform))
    if not certificate['universal_overlap_blocker']:
        raise ValueError('shared saturation certificate did not establish a stop')
    certificate['witness_file'] = spec['cache_path']
    evidence = dict(shared_saturation_certificate=certificate,
                    evidence_class='REGISTRY-MEASUREMENT', date_utc='2026-10-20',
                    witness=spec, witness_sha256=sha(p), registry_membership_verified=member,
                    grid_match=match, shape=list(g.shape), crs=str(g.crs),
                    transform=list(g.transform)[:6], coverage=coverage,
                    literal_overlap_limit=.70, minimum_forward_overlap=1.0,
                    proof='Every candidate point in the footprint is on positive witness support, so distance=0 <=3 px. Forward overlap=1 for every nonempty candidate.',
                    scope='One verified registry witness suffices to fail the universal any-registry rule. This is NOT a complete current registry scan.',
                    template=template, submission_slots_used=0,
                    stop_required=True, verdict='negative')
    out = ROOT / 'evidence/preflight.json'
    out.write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: evidence[k] for k in ['verdict', 'stop_required', 'minimum_forward_overlap', 'scope']}, indent=2))
    return 0  # Audit successfully reproduced a NEGATIVE; not a release permission.


if __name__ == '__main__':
    raise SystemExit(main())
