"""Write the E2 selector-review TIFF once, from a from-scratch recomputation.

Recomputes the preregistered E2 ranking + final thinning deterministically
from the pinned inputs and asserts byte-equality with the experiment's cached
final-dot mask before invoking the shared writer. Publication terms:
docs/publication-amendment-e2.md (verdict stays negative; DO NOT SUBMIT YET).
Refuses to overwrite any existing candidate artifact.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57.grid import load_grid
from gems57.submission_writer import write_submission
from gems57.validate import validate
from gems70 import method2
from restore_data import DATA, PINS, sha

E = ROOT / "evidence" / "e2"


def mask_sha(mask_float32):
    return hashlib.sha256(np.ascontiguousarray(mask_float32).tobytes()).hexdigest()


def main():
    card = json.loads((E / "run_card.json").read_text())
    if card["verdict"] != "negative":
        raise RuntimeError("E2 verdict is not the frozen negative; refusing review publication path")
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError("input pin mismatch: " + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    raw = {}
    with rasterio.open(DATA / "training_features.tif") as src:
        for index, name in [(12, "det_elev"), (2, "rtp"), (15, "basement"), (19, "det_elev_slope")]:
            a = src.read(index).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            raw[name] = a
    valid0 = fp.copy()
    for a in raw.values():
        valid0 &= np.isfinite(a)
    valid = ndi.binary_erosion(valid0, iterations=12)
    elev_f = method2.fill_nearest_from(raw["det_elev"], valid0)
    rtp_f = method2.fill_nearest_from(raw["rtp"], valid0)
    base_f = method2.fill_nearest_from(raw["basement"], valid0)
    elev_s = ndi.gaussian_filter(elev_f.astype(np.float64), 1.0)
    axis_index, _ = method2.structure_tensor_normal(rtp_f)
    step_oriented, _ = method2.oriented_step(elev_s, axis_index)
    features = {
        "step_oriented": np.where(valid, step_oriented, 0).astype(np.float32),
        "basement_edge": np.where(valid, method2.gradient_magnitude(base_f, 2.0), 0).astype(np.float32),
    }
    rank = method2.joint_rank(features, valid, ("step_oriented", "basement_edge"))
    dist_cat = ndi.distance_transform_edt(~grid.catalogue)
    mask, n = method2.priority_thin(rank, valid & (dist_cat > 2))
    final = mask.astype(np.float32)
    cached_path = ROOT / ".cache" / "e2_final_dots.npy"
    recomputed = mask_sha(final)
    record = {"recomputed_final_mask_sha256": recomputed, "dots": int(n),
              "cached_mask_present": cached_path.exists()}
    if cached_path.exists():
        cached = np.load(cached_path)
        record["cached_final_mask_sha256"] = mask_sha(cached)
        record["recomputation_matches_experiment"] = bool(np.array_equal(cached, final))
        if not record["recomputation_matches_experiment"]:
            raise RuntimeError("recomputation differs from experiment cache; aborting publication")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "docs" / "downloads" / f"gems70-e2-alluvialstep-38000-{stamp}-zeros-DO-NOT-SUBMIT.tif"
    pred = np.where(fp, final, 0).astype(np.float32)
    pred[grid.catalogue] = 0
    receipt = write_submission(out, pred, DATA / "sample_submission.tif", fp,
                               note=card["submission_note"], name=card["submission_name"],
                               catalogue=grid.catalogue,
                               metadata={"experiment": "E2", "verdict": "negative",
                                         "status": "selector-review only; DO NOT SUBMIT YET; see docs/publication-amendment-e2.md"})
    v = validate(out, fp, grid.catalogue)
    record.update({"file": out.name, "sha256": receipt["sha256"], "bytes": receipt["bytes"],
                   "zip_file": receipt["zip_file"], "zip_sha256": receipt["zip_sha256"],
                   "writer_receipt": receipt, "validate": v,
                   "amendment": "docs/publication-amendment-e2.md",
                   "amendment_sha256": sha(ROOT / "docs/publication-amendment-e2.md"),
                   "download_ok_for_selector_review": bool(v["all_checks_passed"]),
                   "submit_ok": False, "weekly_slots_used": 0,
                   "published_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
    (E / "publication.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"file": out.name, "sha256": receipt["sha256"], "dots": int(n),
                      "validator_pass": v["all_checks_passed"],
                      "recomputation_matches": record.get("recomputation_matches_experiment")}, indent=2))
    if not v["all_checks_passed"]:
        raise RuntimeError("validator failed on written candidate; see evidence/e2/publication.json")


if __name__ == "__main__":
    main()
