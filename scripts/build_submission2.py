"""Package Experiment 2 final dots with the shared writer (fail-closed).

Writes docs/downloads/<name>.tif + one-TIFF .zip + receipt .json via
vendor/gems57/submission_writer.write_submission (no clipping/repair), then
re-validates the exact bytes with vendor/gems57/validate.validate.
The file is published regardless of verdict so the user has the unique TIFF;
whether it is OK TO SUBMIT is decided by evidence/release2.json, not here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]
import numpy as np

from gems57.grid import load_grid
from gems57.submission_writer import write_submission
from gems57.validate import validate

CACHE = ROOT / ".cache"
DATA = CACHE / "data"
OUT = ROOT / "docs/downloads"
NAME = "gems70-htsas-dotted-37654-20261020"
NOTE = "GEMSDOE70 H70-2A HT-SAS | cross-scale scarp+geophys+hydro HGB, corroboration gate, 37654 dots >2px off-catalogue; see site verdict"


def main():
    grid = load_grid(DATA)
    dots = np.load(CACHE / "candidate2_dots.npy")
    assert dots.shape == grid.shape and dots.sum() == 37654, (dots.shape, dots.sum())
    pred = dots.astype(np.float32)
    assert np.isfinite(pred).all() and pred.min() >= 0 and pred.max() <= 1
    assert not (pred[~grid.footprint] > 0).any()
    assert not (pred[grid.catalogue] > 0).any()
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{NAME}.tif"
    receipt = write_submission(dest, pred, DATA / "sample_submission.tif", grid.footprint,
                               note=NOTE, name=NAME, catalogue=grid.catalogue,
                               metadata={"experiment_id": "H70-2A", "dots": int(dots.sum())})
    check = validate(dest, grid.footprint, grid.catalogue)
    assert check["all_checks_passed"], check["checks"]
    (OUT / f"{NAME}.validator.json").write_text(json.dumps(check, indent=2) + "\n")
    print(json.dumps({"file": dest.name, "sha256": receipt["sha256"], "bytes": receipt["bytes"],
                      "zip": receipt["zip_file"], "zip_sha256": receipt["zip_sha256"],
                      "validator_all_passed": check["all_checks_passed"]}, indent=2))


if __name__ == "__main__":
    main()
