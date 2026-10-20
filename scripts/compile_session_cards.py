"""Compile protocol section-5 session cards from run evidence (packaging only).

This is NOT an experiment: it scores nothing, tunes nothing, and spends no
budget. It re-derives the deterministic experiment-2 dots (asserting the
run-time pool/taken counts), measures in-memory array checks, and assembles
the nine protocol fields from committed evidence files. Run cards written by
the experiment scripts are never modified; these session cards cite them.
Requires the reconstructible .cache/data inputs; the committed JSON outputs
stand alone afterwards.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57.grid import load_grid
from gems70.method_exp2 import greedy_dots, physical_scores, skeleton
from restore_data import DATA, PINS, sha


def main():
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError("input pin mismatch: " + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    with rasterio.open(DATA / "training_features.tif") as src:
        vg = src.read(9).astype(np.float32)
        vg[(vg <= -1e30) | ~np.isfinite(vg) | ~fp] = np.nan
    finite = fp & np.isfinite(vg)
    valid = ndi.binary_erosion(finite, iterations=12)
    scores = physical_scores(vg, finite)
    scores["score"] = np.where(valid, scores["score"], 0).astype(np.float32)
    skel = skeleton(scores["score"], valid)
    catdist = ndi.distance_transform_edt(~grid.catalogue)
    dots, emission = greedy_dots(scores["score"], skel, catdist)
    card2 = json.loads((ROOT / "evidence/exp2_run_card.json").read_text())
    assert emission == card2["emission"], "rederived dots differ from run time"
    cand = np.where(dots, 1.0, 0.0).astype(np.float32)
    array_checks = {
        "no_nan_inside_footprint": bool(np.all(np.isfinite(cand[fp]))),
        "all_values_finite": bool(np.all(np.isfinite(cand))),
        "values_in_0_1": bool(np.all((cand >= 0) & (cand <= 1))),
        "shape_matches": bool(cand.shape == fp.shape),
        "zero_on_catalogue": bool(not ((cand > 0) & grid.catalogue).any()),
        "zero_outside_footprint": bool(not ((cand > 0) & ~fp).any()),
        "n_dots": int(dots.sum()),
    }
    assert all(v for k, v in array_checks.items() if k != "n_dots")

    audit = json.loads((ROOT / "evidence/exp2_uniqueness_subset.json").read_text())
    rows = [r for r in audit["rows"] if not r.get("error")]
    rhos = [r["spearman_full_footprint"] for r in rows]
    ovs = [(r["key"], r["overlap_final_dots"]) for r in rows if r.get("sparse")]
    uniq2 = {
        "stage": "final dots (binary 38,000) + surface stage reported in subset file",
        "rasters_checked": len(rows),
        "registry_complete": False,
        "max_abs_spearman": float(max(abs(r) for r in rhos)),
        "max_sparse_overlap": max(ovs, key=lambda kv: kv[1]),
        "overlap_vs_h33": next(v for k, v in ovs if k == "h33"),
        "dense_witness_overlap_reported_not_gated": next(
            r["overlap_final_dots"] for r in audit["rows"] if r["key"] == "g17E_dense"),
        "scope": audit["scope"],
    }
    card3 = json.loads((ROOT / "evidence/exp3_run_card.json").read_text())
    hold3 = json.loads((ROOT / "evidence/exp3_holdout.json").read_text())
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    session2 = {
        "evidence_class": "SESSION-CARD",
        "protocol_section": 5,
        "compiled_utc": stamp,
        "compiler": "scripts/compile_session_cards.py",
        "hypothesis": card2["hypothesis"],
        "mechanism": card2["mechanism"],
        "non_fault_mimic": card2["non_fault_mimic"],
        "holdout_dti": card2["holdout_dti"],
        "correlation_overlap_vs_registry": uniq2,
        "raster_sha256": None,
        "raster_sha256_reason": "No submission TIFF written (negative verdict).",
        "validator_output": {
            "submission_tiff": None, "status": "NOT_WRITTEN",
            "pre_export_array_checks": array_checks,
            "crs_shape_transform_file_match": None,
            "reason": "Array checks on rederived deterministic dots (verified "
                      "identical to run time); not a TIFF validator receipt.",
        },
        "submission_name": "gems70-vgshallow-h1-B2-38k-NOT-RELEASED",
        "submission_note": "VG-line H1 B2 38k dots; holdout-negative on two seeds; DO NOT SUBMIT.",
        "verdict": "negative",
        "run_card": "evidence/exp2_run_card.json",
    }
    session3 = {
        "evidence_class": "SESSION-CARD",
        "protocol_section": 5,
        "compiled_utc": stamp,
        "compiler": "scripts/compile_session_cards.py",
        "hypothesis": card3["hypothesis"],
        "mechanism": card3["mechanism"],
        "non_fault_mimic": card3["non_fault_mimic"],
        "holdout_dti": {
            "evidence_class": "SGMC-PROXY-DTI",
            "candidate": hold3["scores"]["candidate"],
            "paired_differences_vs_candidate": hold3["paired_differences"],
            "truth": hold3["truth_provenance"],
        },
        "correlation_overlap_vs_registry": uniq2,
        "correlation_overlap_note": "Same fixed dots as experiment 2; uniqueness "
                                    "measured once and reused.",
        "raster_sha256": None,
        "raster_sha256_reason": "No submission TIFF written (negative verdict).",
        "validator_output": session2["validator_output"],
        "validator_note": "Same fixed dots as experiment 2.",
        "submission_name": "gems70-vgshallow-h1-B2-38k-NOT-RELEASED",
        "submission_note": "VG-line H1 B2 38k dots; SGMC-proxy-negative; DO NOT SUBMIT.",
        "verdict": "negative",
        "run_card": "evidence/exp3_run_card.json",
    }
    assert len(session2["submission_note"]) <= 140
    assert len(session3["submission_note"]) <= 140
    (ROOT / "evidence/session_card_exp2.json").write_text(json.dumps(session2, indent=2) + "\n")
    (ROOT / "evidence/session_card_exp3.json").write_text(json.dumps(session3, indent=2) + "\n")
    print("session cards compiled; both negative; no files renamed or moved.")


if __name__ == "__main__":
    main()
