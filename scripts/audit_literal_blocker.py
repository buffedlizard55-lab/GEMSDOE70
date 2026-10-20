#!/usr/bin/env python3
"""Audit the *user's literal forward* 3 px dot rule on a pinned registry witness.

This is a reporting tool, not a modified evaluator or a waiver. It proves the
sample-footprint coverage and the zero-uncovered-features fact, so no 37,654-dot
submission confined to the valid interior could pass forward overlap <=0.70.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "vendor"), str(ROOT / "src")]
from gems57 import grid, uniqueness

WITNESS = "calib_r13lattice_00904.tif"
WITNESS_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
FEATURE_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"


def digest(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as src:
        for block in iter(lambda: src.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def audit(witness_path: Path, features_path: Path, sample_path: Path):
    if digest(witness_path) != WITNESS_SHA or digest(features_path) != FEATURE_SHA:
        raise ValueError("registry witness or training stack SHA-256 mismatch")
    if digest(sample_path) != grid.SHA256_SAMPLE_SUBMISSION:
        raise ValueError("footprint mirror SHA-256 mismatch")
    with rasterio.open(sample_path) as sample:
        footprint = np.isfinite(sample.read(1))
        ref = (sample.shape, sample.crs, sample.transform)
    with rasterio.open(witness_path) as w:
        if (w.shape, w.crs, w.transform) != ref or w.count != 1:
            raise ValueError("witness is not a 100 m single-band raster on the sample grid")
        dots = uniqueness._dots(w.read(1)) & footprint
    near = uniqueness._near(dots, radius_px=3.0)
    with rasterio.open(features_path) as src:
        if (src.shape, src.crs, src.transform) != ref or src.count != 19:
            raise ValueError("training features mismatch")
        # RTP (band 2) defines the old P4 valid footprint, before the 12px erosion.
        rtp = src.read(2)
    valid = ndi.binary_erosion(footprint & np.isfinite(rtp) & (rtp > -1e30), iterations=12)
    del rtp
    covered = int((near & footprint).sum())
    uncovered = int((~near & footprint).sum())
    valid_covered = int((near & valid).sum())
    valid_uncovered = int((~near & valid).sum())
    return {
        "evidence_class": "REGISTRY-MEASUREMENT / LITERAL-FORWARD-STOP",
        "source_url": f"https://github.com/buffedlizard55-lab/60GEMSDOE/blob/b99591eede63c6d45c8a896255b8cd34824fa00b/registry/rasters/{WITNESS}",
        "file": WITNESS, "sha256": WITNESS_SHA,
        "footprint_sha256": grid.SHA256_SAMPLE_SUBMISSION,
        "features_sha256": FEATURE_SHA,
        "radius_px": 3.0, "positive_definition": "binary dots: finite value within 1e-6 of 1.0",
        "witness_dots": int(dots.sum()),
        "footprint_pixels": int(footprint.sum()),
        "covered_footprint_pixels": covered,
        "uncovered_footprint_pixels": uncovered,
        "covered_footprint_fraction": covered / int(footprint.sum()),
        "feature_valid_pixels_after_12px_erosion": int(valid.sum()),
        "feature_valid_covered_pixels": valid_covered,
        "feature_valid_uncovered_pixels": valid_uncovered,
        "minimum_forward_overlap_for_any_nonempty_dot_field_in_valid":
            1.0 if valid_uncovered == 0 else None,
        "literal_user_gate": "if >70% of *our* dots lie within 3px of one registry raster, log duplicate and STOP",
        "literal_stop_for_any_dot_field_in_valid": valid_covered > 0 and valid_uncovered == 0,
        "mutual_overlap_is_not_a_waiver": True,
        "scope": "One SHA-verified archived witness suffices for a positive stop; does not claim a complete registry scan or organizer file identity.",
    }


def main():
    p = Path("/tmp/60GEMSDOE/registry/rasters") / WITNESS
    result = audit(p, ROOT / ".cache/data/training_features.tif",
                   ROOT / "data/bridge/sample_submission.tif")
    dest = ROOT / "evidence/p5/literal_blocker.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
