"""Experiment 3 (preregistered in docs/exp3-prereg.md): SGMC distal rescoring.

Final experiment of the budget. Rescores FIXED dot sets against SGMC faults
off the competition catalogue. Writes a submission only if the instrument
validates (H33 reproduces the live ladder) AND the candidate shows signal.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57 import evaluate_holdout
from gems57.grid import load_grid
from gems57.submission_writer import write_submission
from gems70.method_exp2 import greedy_dots, physical_scores, skeleton
from restore_data import DATA, PINS, sha

E = ROOT / "evidence"
RNG_SEED = 70073
BOOT_SEED = 70073
SUBMISSION_NAME = "gems70-vgshallow-h1-B2-38k"
SGMC_SHA = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def main():
    start = time.monotonic()
    manifest = E / "exp3_manifest.json"
    if manifest.exists():
        raise RuntimeError("Experiment 3 already attempted. Budget exhausted.")
    exp2_manifest = json.loads((E / "exp2_manifest.json").read_text())
    pinned_method = exp2_manifest["source_sha256"]["src/gems70/method_exp2.py"]
    if sha(ROOT / "src/gems70/method_exp2.py") != pinned_method:
        raise ValueError("method_exp2.py changed since experiment 2; dots would differ")
    dump(manifest, {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment_count": 3, "maximum_experiments": 3,
        "maximum_seconds": 7200,
        "preregistration": "docs/exp3-prereg.md",
        "preregistration_sha256": sha(ROOT / "docs/exp3-prereg.md"),
        "source_sha256": {"scripts/run_experiment_exp3.py":
                          sha(ROOT / "scripts/run_experiment_exp3.py")},
        "method_exp2_sha256": pinned_method,
        "rng_seed": RNG_SEED, "bootstrap_seed": BOOT_SEED})

    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError("input pin mismatch: " + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    catdist = ndi.distance_transform_edt(~grid.catalogue)

    sgmc_path = (ROOT / ".cache/mirror-GEMSDOE24/data/external/"
                 "derived_sgmc_faults_100m_u8.tif")
    if sha(sgmc_path) != SGMC_SHA:
        raise ValueError("SGMC pin mismatch")
    with rasterio.open(sgmc_path) as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs,
                                                   grid.transform):
            raise ValueError("SGMC grid mismatch")
        sgmc = src.read(1)
    if set(np.unique(sgmc)) - {0, 1}:
        raise ValueError("SGMC raster is not binary")
    truth = (sgmc > 0) & fp & (catdist > 3)
    print(f"SGMC-distal truth px: {int(truth.sum())}", flush=True)
    if int(truth.sum()) < 1000:
        raise RuntimeError("INCONCLUSIVE: proxy truth below 1,000-pixel floor")

    with rasterio.open(DATA / "training_features.tif") as src:
        vg = src.read(9).astype(np.float32)
        vg[(vg <= -1e30) | ~np.isfinite(vg) | ~fp] = np.nan
    finite_vg = fp & np.isfinite(vg)
    valid = ndi.binary_erosion(finite_vg, iterations=12)
    scores = physical_scores(vg, finite_vg)
    scores["score"] = np.where(valid, scores["score"], 0).astype(np.float32)
    skel = skeleton(scores["score"], valid)
    dots, emission = greedy_dots(scores["score"], skel, catdist)
    print(f"recomputed emission pool: {emission['pool']} taken: {emission['taken']}",
          flush=True)
    if int(dots.sum()) != 38000 or emission["pool"] != 222341:
        raise ValueError("recomputed dots differ from experiment 2")
    candidate = np.where(dots, 1.0, 0.0).astype(np.float32)

    arms = {"candidate": candidate}
    refs = {
        "h33": ".cache/mirror-60GEMSDOE/registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif",
        "h27": ".cache/mirror-60GEMSDOE/registry/rasters/GEMSDOE28__h27-4-r1-solo-d2-8.tif",
        "d28": ".cache/mirror-60GEMSDOE/registry/rasters/GEMSDOE25__dotted-h19-5-d2-8.tif",
    }
    for name, rel in refs.items():
        with rasterio.open(ROOT / rel) as src:
            if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs,
                                                       grid.transform):
                raise ValueError(f"{name} grid mismatch")
            arms[name] = (src.read(1) > 0).astype(np.float32)
    rng = np.random.default_rng(RNG_SEED)
    rand_u = np.zeros(fp.shape, np.float32)
    rand_u.ravel()[rng.choice(np.flatnonzero(valid), 38000, replace=False)] = 1.0
    rand_a = np.zeros(fp.shape, np.float32)
    rand_a.ravel()[rng.choice(np.flatnonzero(valid & (catdist > 2.0)), 38000,
                              replace=False)] = 1.0
    arms["random_unconstrained"] = rand_u
    arms["random_avoiding"] = rand_a

    fold = {"region": fp.copy(), "masked_known": grid.catalogue.copy(),
            "visible": grid.catalogue.copy(),
            "truth": truth, "receipt": {"experiment": 3, "truth": "SGMC-distal"}}
    terms = {}
    for name, arr in arms.items():
        if time.monotonic() - start > 7200:
            raise TimeoutError("two-hour experiment budget exhausted")
        result, term = evaluate_holdout.evaluate(arr, fold, fp)
        terms[name] = term
        print(f"{name}: DTI={result['dti']:.6f} tp={result['tp']:.1f} "
              f"fp={result['fp']:.1f} fn={result['fn']:.1f} "
              f"n={result['n_truth']}", flush=True)
    summary = evaluate_holdout.pooled_summary(terms, draws=1000, seed=BOOT_SEED,
                                              candidate="candidate")
    summary["truth_provenance"] = {
        "source": "GEMSDOE24@07345ea:data/external/derived_sgmc_faults_100m_u8.tif",
        "sha256": SGMC_SHA,
        "definition": "SGMC-positive with catalogue-distance > 3 px",
        "n_truth": int(truth.sum()),
        "masked_known": "full competition catalogue (organizer-style)",
        "caveat": "SGMC maps faults of any age/activity; proxy noise expected. "
                  "Gate A tests whether the proxy ranks the live ladder."}
    summary["interpretation"] = ("SGMC-proxy DTI (single whole-footprint "
                                 "evaluation + spatial-block bootstrap), not "
                                 "organizer-confirmed.")
    dump(E / "exp3_holdout.json", summary)

    def beats(a, b):
        sa, sb = summary["scores"][a], summary["scores"][b]
        return sa["dti"] > sb["dti"] and sa["ci95"][0] > sb["ci95"][1]

    gate_a = beats("h33", "d28") and beats("h33", "random_avoiding")
    gate_b = beats("candidate", "random_avoiding")
    print(f"gateA (H33>D28 and H33>avoiding-random): {gate_a}", flush=True)
    print(f"gateB (candidate>avoiding-random): {gate_b}", flush=True)

    card = {
        "experiment": 3,
        "hypothesis": "Experiment-2 VG dots tested on SGMC distal proxy truth",
        "mechanism": "Fixed-dot rescoring; no new emission",
        "non_fault_mimic": "SGMC inactive-fault traces (proxy noise)",
        "verdict": "negative" if not (gate_a and gate_b) else "promote-pending",
        "gates": {"gateA_instrument": gate_a, "gateB_signal": gate_b},
        "weekly_slots_used": 0,
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "organizer_confirmed_score": None,
    }
    if not (gate_a and gate_b):
        dump(E / "exp3_run_card.json", card)
        print("VERDICT: negative — no submission written", flush=True)
        return

    s = summary["scores"]["candidate"]
    note = (f"VG-line H1 B2 38k; SGMC-proxy DTI {s['dti']:.4f} "
            f"[{s['ci95'][0]:.4f},{s['ci95'][1]:.4f}]; fmt-valid; partial-uniq")
    assert len(note) <= 140, note
    out = ROOT / "docs/downloads" / f"{SUBMISSION_NAME}.tif"
    receipt = write_submission(out, candidate, DATA / "sample_submission.tif",
                               fp, note=note, name=SUBMISSION_NAME,
                               catalogue=grid.catalogue)
    indexed = {r["sha256"] for r in json.loads(
        (ROOT / "registry/inherited_registry_index.json").read_text())["rasters"]}
    if receipt["sha256"] in indexed:
        out.unlink(missing_ok=True)
        out.with_suffix(".zip").unlink(missing_ok=True)
        out.with_suffix(".json").unlink(missing_ok=True)
        card["verdict"] = "negative"
        card["gates"]["gate5_byte_unique"] = False
        dump(E / "exp3_run_card.json", card)
        print("VERDICT: negative — byte duplicate; artifacts removed", flush=True)
        return
    card["verdict"] = "promote"
    card["gates"]["gate5_byte_unique"] = True
    card["raster_sha256"] = receipt["sha256"]
    card["validator_output"] = {
        "submission_tiff": str(out.relative_to(ROOT)),
        "local_validation": receipt["validator"],
        "template_report_ok": receipt["template_report"]["ok"],
        "zip_sha256": receipt["zip_sha256"]}
    card["submission_name"] = SUBMISSION_NAME
    card["submission_note"] = note
    card["download_and_submit_ok"] = (
        "FORMAT-VALID CANDIDATE — download available; organizer acceptance NOT "
        "guaranteed; uniqueness is PARTIAL-subset; slot decision is the "
        "operator's.")
    dump(E / "exp3_run_card.json", card)
    print(f"VERDICT: promote — {out.name} sha256={receipt['sha256']}", flush=True)


if __name__ == "__main__":
    main()
