"""Two-stage full-registry uniqueness audit for Experiment 2 (940 rasters).

Stage A: pre-placement continuous surface. Stage B: final binary dots.
Both use vendor/gems57/uniqueness.compare_array_to_registry unchanged, plus
two_phase_summary (like-for-like dot-field reading reported alongside the
literal reading; no threshold is altered) and, for the record, the literal
saturation certificate against the known universal dense prior.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]
import numpy as np

from gems57 import uniqueness
from gems57.grid import load_grid

E = ROOT / "evidence"
CACHE = ROOT / ".cache"
DATA = CACHE / "data"


def dump(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def main():
    t0 = time.monotonic()
    idx = json.loads((CACHE / "registry/full_live_index.json").read_text())
    assert idx["complete_accessible_scan"] and idx["n_unique_grid_rasters"] == len(idx["rasters"])
    grid = load_grid(DATA)
    fp = grid.footprint
    out = {"evidence_class": "REGISTRY-MEASUREMENT", "registry_rasters_expected": len(idx["rasters"]),
           "registry_generated_utc": idx["generated_utc"], "stages": {}}
    for stage, npy in [("surface_before_placement", CACHE / "candidate2_surface.npy"),
                       ("final_dots", CACHE / "candidate2_dots.npy")]:
        arr = np.load(npy)
        if stage == "final_dots":
            arr = arr.astype(np.float32)
        print(f"[{stage}] comparing vs {len(idx['rasters'])} rasters...", flush=True)
        audit = uniqueness.compare_array_to_registry(
            arr, idx, fp, include_reverse=True,
            expected_grid=(grid.shape, grid.crs, grid.transform),
            progress=lambda i, n, row: print(f"  {i}/{n}", flush=True) if i % 200 == 0 else None)
        phase = uniqueness.two_phase_summary(audit["rows"], int(fp.sum()),
                                             expected_rasters=len(idx["rasters"]))
        out["stages"][stage] = {"audit": audit, "two_phase": phase}
        print(f"[{stage}] done {time.monotonic()-t0:.0f}s literal_unique={audit['unique']} "
              f"like_for_like_duplicate={phase['like_for_like_reading']['duplicate']}", flush=True)
    wit = CACHE / "registry/ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be.tif"
    if wit.exists():
        out["literal_saturation_certificate_vs_universal_prior"] = uniqueness.saturation_certificate(
            wit, fp, grid.catalogue, expected_grid=(grid.shape, grid.crs, grid.transform))
    out["elapsed_seconds"] = round(time.monotonic() - t0, 1)
    dump(E / "uniqueness2.json", out)
    print(json.dumps({k: {"unique_literal": v["audit"]["unique"],
                          "worst_rho": v["audit"]["worst_spearman_full_footprint"],
                          "worst_overlap": v["audit"]["worst_dot_overlap"],
                          "like_for_like": v["two_phase"]["like_for_like_reading"]}
                      for k, v in out["stages"].items()}, indent=2), flush=True)


if __name__ == "__main__":
    main()
