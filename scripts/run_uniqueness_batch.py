"""Checkpointed two-stage 940-raster uniqueness audit (shared tool, batched).

Identical measurements to uniqueness.compare_array_to_registry on the full
index; batching only bounds memory and checkpoints rows after every chunk so
an interrupted run loses nothing. Final verdicts come from the shared
summarize_registry_rows / two_phase_summary on the merged rows.
"""
from __future__ import annotations

import argparse
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", required=True)
    ap.add_argument("--dots", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunk", type=int, default=160)
    args = ap.parse_args()
    t0 = time.monotonic()
    idx = json.loads((CACHE / "registry/full_live_index.json").read_text())
    assert idx["complete_accessible_scan"]
    rasters = idx["rasters"]
    grid = load_grid(DATA)
    fp = grid.footprint
    out = {"evidence_class": "REGISTRY-MEASUREMENT", "registry_rasters_expected": len(rasters),
           "registry_generated_utc": idx["generated_utc"], "stages": {}}
    for stage, npy in [("surface_before_placement", args.surface), ("final_dots", args.dots)]:
        arr = np.load(ROOT / npy if not Path(npy).is_absolute() else npy)
        if stage == "final_dots":
            arr = arr.astype(np.float32)
        ckpt = CACHE / f"uniq_rows_{Path(args.out).stem}_{stage}.json"
        rows = json.loads(ckpt.read_text()) if ckpt.exists() else []
        done_shas = {r["sha256"] for r in rows if "sha256" in r}
        meta = None
        todo = [r for r in rasters if r["sha256"] not in done_shas]
        print(f"[{stage}] {len(rows)} checkpointed, {len(todo)} to go", flush=True)
        for i in range(0, len(todo), args.chunk):
            sub = {"rasters": todo[i:i + args.chunk], "complete_accessible_scan": False, "errors": []}
            audit = uniqueness.compare_array_to_registry(
                arr, sub, fp, include_reverse=True,
                expected_grid=(grid.shape, grid.crs, grid.transform))
            rows.extend(audit["rows"])
            meta = {"my_dots": audit["my_dots"], "candidate_decoded_sha256": audit["candidate_decoded_sha256"],
                    "candidate_file_sha256": audit["candidate_file_sha256"],
                    "candidate_rank_variation": audit["candidate_rank_variation"]}
            ckpt.write_text(json.dumps(rows))
            print(f"[{stage}] {len(rows)}/{len(rasters)} ({time.monotonic()-t0:.0f}s)", flush=True)
        audit = uniqueness.summarize_registry_rows(
            rows, registry_rasters_expected=len(rasters), complete_accessible_scan=True,
            source_errors=[], candidate_meta={**meta, "my_file": npy},
            scope="Batched full accessible registry (940 SHA-verified grid rasters, 71 repos + quarantined H70-C); not an organizer registry.")
        phase = uniqueness.two_phase_summary(rows, int(fp.sum()), expected_rasters=len(rasters))
        out["stages"][stage] = {"audit": audit, "two_phase": phase}
        print(f"[{stage}] literal_unique={audit['unique']} like_dup={phase['like_for_like_reading']['duplicate']}", flush=True)
    wit = CACHE / "registry/ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be.tif"
    out["literal_saturation_certificate_vs_universal_prior"] = uniqueness.saturation_certificate(
        wit, fp, grid.catalogue, expected_grid=(grid.shape, grid.crs, grid.transform))
    out["elapsed_seconds"] = round(time.monotonic() - t0, 1)
    (ROOT / args.out).write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print("WROTE", args.out, flush=True)


if __name__ == "__main__":
    main()
