"""Experiment 2 (preregistered in docs/hypotheses-round2.md): VG lineaments.

Fail-closed: any gate failure raises/stops with no submission written. Refuses
a second run once the manifest exists (no tuning on reported folds).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid
from gems57.submission_writer import write_submission
from gems70.method import joint_field, physical_features, rank01, upper_surface
from gems70.method_exp2 import (ew_fraction, greedy_dots, physical_scores,
                                skeleton, structure_theta)
from restore_data import DATA, PINS, sha

E = ROOT / "evidence"
CACHE = ROOT / ".cache"
SEEDS = (20, 71)
RNG_SEED = 70071
BOOT_SEED = 70071
SUBMISSION_NAME = "gems70-vgshallow-h1-B2-38k"


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def cropped(fold, pred, valid, origin_global):
    y, x = np.nonzero(fold["region"])
    y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
    y1, x1 = min(pred.shape[0], int(y.max()) + 7), min(pred.shape[1], int(x.max()) + 7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k: v[sl] for k, v in fold.items()
           if isinstance(v, np.ndarray) and v.shape == pred.shape}
    return evaluate_holdout.evaluate(pred[sl], sub, valid[sl], origin=(y0, x0),
                                     global_shape=pred.shape)


def load_band(src, index, footprint):
    a = src.read(index).astype(np.float32)
    a[(a <= -1e30) | ~np.isfinite(a) | ~footprint] = np.nan
    return a


def main():
    start = time.monotonic()
    manifest = E / "exp2_manifest.json"
    if manifest.exists():
        raise RuntimeError("Experiment 2 already attempted. No silent reruns/tuning.")
    dump(manifest, {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment_count": 2, "maximum_experiments": 3,
        "maximum_seconds": 7200,
        "preregistration": "docs/hypotheses-round2.md",
        "preregistration_sha256": sha(ROOT / "docs/hypotheses-round2.md"),
        "source_sha256": {p: sha(ROOT / p) for p in
                          ["src/gems70/method_exp2.py",
                           "scripts/run_experiment_exp2.py"]},
        "rng_seed": RNG_SEED, "bootstrap_seed": BOOT_SEED,
        "submission_name": SUBMISSION_NAME})

    def budget():
        if time.monotonic() - start > 7200:
            raise TimeoutError("two-hour experiment budget exhausted")

    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError("input pin mismatch: " + name)
    grid = load_grid(DATA)
    fp = grid.footprint
    catdist = ndi.distance_transform_edt(~grid.catalogue)

    with rasterio.open(DATA / "training_features.tif") as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError("feature grid mismatch")
        vg = load_band(src, 9, fp)
        rtp = load_band(src, 2, fp)
        gravity = load_band(src, 13, fp)
        basement = load_band(src, 15, fp)

    finite_vg = fp & np.isfinite(vg)
    valid = ndi.binary_erosion(finite_vg, iterations=12)
    valid_e1 = fp.copy()
    for a in (rtp, gravity, basement):
        valid_e1 &= np.isfinite(a)
    valid_e1 = ndi.binary_erosion(valid_e1, iterations=12)
    if not valid.any() or not valid_e1.any():
        raise ValueError("no valid interior features")
    domain_delta = int(np.bitwise_xor(valid, valid_e1).sum())
    print(f"valid px: {int(valid.sum())} e1-valid px: {int(valid_e1.sum())} "
          f"delta: {domain_delta}", flush=True)

    scores = physical_scores(vg, finite_vg)
    for key in ("chan_a", "chan_b", "score"):
        scores[key] = np.where(valid, scores[key], 0).astype(np.float32)
    skel = skeleton(scores["score"], valid)
    print(f"skeleton px: {int(skel.sum())}", flush=True)
    theta = structure_theta(scores["smooth"])
    ew_skel = ew_fraction(theta, skel)
    print(f"E-W fraction (skeleton, diagnostic): {ew_skel:.4f}", flush=True)

    dots, emission = greedy_dots(scores["score"], skel, catdist)
    print(f"emission pool: {emission['pool']} taken: {emission['taken']}", flush=True)
    candidate = np.where(dots, 1.0, 0.0).astype(np.float32)
    ew = ew_fraction(theta, dots)
    print(f"E-W fraction (emitted dots, gate): {ew:.4f} (stop if > 0.50)", flush=True)
    if ew > 0.50:
        raise RuntimeError("ARTIFACT STOP: emitted-dot E-W fraction exceeds 0.50")

    # Ablation dot fields share the emission rule on single channels.
    skel_a = skeleton(rank01(scores["chan_a"], valid).astype(np.float32), valid)
    skel_b = skeleton(rank01(scores["chan_b"], valid).astype(np.float32), valid)
    dots_a, _ = greedy_dots(rank01(scores["chan_a"], valid).astype(np.float32),
                            skel_a, catdist)
    dots_b, _ = greedy_dots(rank01(scores["chan_b"], valid).astype(np.float32),
                            skel_b, catdist)
    dots_np, _ = greedy_dots(scores["score"], skel, catdist, prune=-1.0)

    # Experiment-1 surface recomputed from frozen method (same-split best).
    feats_e1 = physical_features(rtp, gravity, basement, valid_e1)
    surf_e1 = upper_surface(joint_field(feats_e1, valid_e1), valid_e1)
    surf_e1[grid.catalogue] = 0

    with rasterio.open(ROOT / ".cache/mirror-60GEMSDOE/registry/rasters/"
                       "GEMSDOE32__h33-2-b2-zeros.tif") as src:
        h33 = (src.read(1) > 0).astype(np.float32)

    rng = np.random.default_rng(RNG_SEED)
    n_mass = int(dots.sum())
    rand_u = np.zeros(fp.shape, np.float32)
    rand_u.ravel()[rng.choice(np.flatnonzero(valid), n_mass, replace=False)] = 1.0
    avoid_pool = np.flatnonzero(valid & (catdist > 2.0))
    rand_a = np.zeros(fp.shape, np.float32)
    rand_a.ravel()[rng.choice(avoid_pool, n_mass, replace=False)] = 1.0

    arms_static = {
        "candidate": (candidate, valid),
        "ablation_A": (np.where(dots_a, 1.0, 0.0).astype(np.float32), valid),
        "ablation_B": (np.where(dots_b, 1.0, 0.0).astype(np.float32), valid),
        "ablation_no_prune": (np.where(dots_np, 1.0, 0.0).astype(np.float32), valid),
        "exp1_surface": (surf_e1, valid_e1),
        "random_unconstrained": (rand_u, valid),
        "random_avoiding": (rand_a, valid),
        "h33_reference": (h33, fp),
    }

    per_seed, fold_details, canary_all, split_all = {}, {}, {}, {}
    for seed in SEEDS:
        budget()
        folds, _ = holdout.buffered_component_draw(grid, seed=seed, buffer_px=3,
                                                   boundary_px=12)
        split_all[seed] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": evaluate_holdout.VERSION,
            "receipts": [f["receipt"] for f in folds],
            "total_withheld_positive_pixels": int(sum((f["truth"] & valid).sum()
                                                     for f in folds)),
            "catalogue_predictors": [],
            "limitation": "Mapped components surrogate for unmapped faults."}
        truth = np.zeros(fp.shape, bool)
        active = np.zeros(fp.shape, bool)
        for fold in folds:
            active |= valid & fold["region"] & ~fold["masked_known"]
            truth |= valid & fold["truth"]
        positives = np.flatnonzero(truth)
        negatives = np.flatnonzero(active & ~truth)
        negatives = rng.choice(negatives, min(200000, len(negatives)), replace=False)
        labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]
        canaries = {}
        for name, arr in (("tmi_vg_raw", vg),
                          ("chan_a", scores["chan_a"]),
                          ("chan_b", scores["chan_b"]),
                          ("score_combined", scores["score"])):
            vals = np.r_[np.asarray(arr, float).ravel()[positives],
                         np.asarray(arr, float).ravel()[negatives]]
            auc = float(roc_auc_score(labels, vals))
            canaries[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc,
                              "inverse_auc": 1 - auc,
                              "withheld_positive_pixels": len(positives),
                              "negative_sample_pixels": len(negatives),
                              "suspected_leakage": bool(max(auc, 1 - auc) > .90)}
        canary_all[seed] = canaries
        dump(E / f"exp2_canaries_seed{seed}.json", canaries)
        if any(c["suspected_leakage"] for c in canaries.values()):
            raise RuntimeError("LEAKAGE CANARY STOP: feature-alone AUC > .90")
        print(f"seed {seed}: canaries clean ({len(positives)} positives)", flush=True)

        terms, fold_results = {}, {}
        for name, (arr, dom) in arms_static.items():
            budget()
            per_fold = [cropped(f, arr, dom, None) for f in folds]
            # pooled_summary requires identical truth counts per block: arms
            # sharing one seed/fold set satisfy this; exp1/h33 use their own
            # domains, so pool them separately below.
            terms[name] = sum(t for _, t in per_fold)
            fold_results[name] = [r for r, _ in per_fold]
            print(f"seed {seed}: {name} evaluated", flush=True)
        fold_details[seed] = fold_results
        # Split pooling by evaluation domain (identical truth blocks required).
        groups = {"main": [n for n, (_, d) in arms_static.items() if d is valid],
                  "exp1": ["exp1_surface"],
                  "h33": ["h33_reference"]}
        pooled = {}
        for gname, members in groups.items():
            if len(members) < 1:
                continue
            cand = "candidate" if "candidate" in members else members[0]
            pooled[gname] = evaluate_holdout.pooled_summary(
                {n: terms[n] for n in members}, draws=1000, seed=BOOT_SEED,
                candidate=cand)
        # Merge group summaries into one receipt; cross-domain DTI values share
        # folds/truth but differ in scored domain (stated, not hidden).
        merged_scores, merged_diff = {}, {}
        for gname, receipt in pooled.items():
            merged_scores.update(receipt["scores"])
            if gname == "main":
                merged_diff = receipt["paired_differences"]
                best = receipt["best_comparable_control"]
                boot = receipt["bootstrap"]
        per_seed[seed] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": evaluate_holdout.VERSION,
            "alpha": 0.2, "beta": 0.8, "triangular_radius_m": 300.0,
            "pooled": True, "scores": merged_scores,
            "best_comparable_control": best,
            "paired_differences_vs_candidate": merged_diff,
            "bootstrap": boot,
            "domain_note": "main arms share exp2 valid domain; exp1_surface "
                           "uses the experiment-1 domain; h33 uses footprint. "
                           "Truth blocks are identical within each group.",
            "interpretation": "Final-dot HOLDOUT-DTI (binary 38k dots except "
                              "where noted), not organizer-confirmed."}
        dump(E / f"exp2_holdout_seed{seed}.json", per_seed[seed])
    folds_clean = {}
    for k in SEEDS:
        folds_clean[str(k)] = {}
        for name in arms_static:
            folds_clean[str(k)][name] = [
                {kk: (float(vv) if isinstance(vv, (float, np.floating)) else
                      (int(vv) if isinstance(vv, (int, np.integer)) else vv))
                 for kk, vv in r.items()}
                for r in fold_details[k][name]]
    dump(E / "exp2_holdout_folds.json", folds_clean)
    dump(E / "exp2_holdout_split.json", {str(k): v for k, v in split_all.items()})

    # ---- promotion gates 1-3 (holdout) ----
    def ci_no_overlap(a, b):
        return a["ci95"][0] > b["ci95"][1] or b["ci95"][0] > a["ci95"][1]

    s20, s71 = per_seed[20], per_seed[71]
    gate2 = (s20["scores"]["candidate"]["dti"] > s20["scores"]["exp1_surface"]["dti"]
             and ci_no_overlap(s20["scores"]["candidate"],
                               s20["scores"]["exp1_surface"]))
    gate3 = all(per_seed[s]["scores"]["candidate"]["dti"]
                > per_seed[s]["scores"]["random_avoiding"]["dti"]
                and ci_no_overlap(per_seed[s]["scores"]["candidate"],
                                  per_seed[s]["scores"]["random_avoiding"])
                for s in SEEDS)
    print(f"gate2 (beat exp1, s20): {gate2}", flush=True)
    print(f"gate3 (beat avoiding-random, both seeds): {gate3}", flush=True)

    # ---- surface + final-dot uniqueness (preregistered subset) ----
    registry_files = {
        "h33": ".cache/mirror-60GEMSDOE/registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif",
        "h27": ".cache/mirror-60GEMSDOE/registry/rasters/GEMSDOE28__h27-4-r1-solo-d2-8.tif",
        "d28": ".cache/mirror-60GEMSDOE/registry/rasters/GEMSDOE25__dotted-h19-5-d2-8.tif",
        "g17F": ".cache/mirror-17GEMSDOE/docs/downloads/17GEMSDOE_F-ensemble-2pct_20260930T050626Z.tif",
        "g17D": ".cache/mirror-17GEMSDOE/docs/downloads/17GEMSDOE_D-supervised-expression_86125863_20260930T034153Z.tif",
        "g17A": ".cache/mirror-17GEMSDOE/docs/downloads/17GEMSDOE_A-verified-01563-support_c5ea501e_20260930T021105Z.tif",
        "h70c": "quarantine/concurrent-h70c/downloads/gemsdoe70_h70c_greedy_B2_38500_zeros.tif",
        "g52h70": ".cache/mirror-GEMSDOE52/docs/downloads/gems52-h70-aonly-cotrain-610px-20261009T055521Z.tif",
        "g17E_dense": ".cache/mirror-17GEMSDOE/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
        "g52h97b_sup": ".cache/mirror-GEMSDOE52/docs/downloads/gems52-h97b-surface-consensus-25400px-20261011T004256Z-450c07e1cca4-zeros.tif",
        "g52h83_sup": ".cache/mirror-GEMSDOE52/docs/downloads/gems52-h83-offcatalogue-cotrain-37654px-e3-20261010T202956Z.tif",
        "g52h60_sup": ".cache/mirror-GEMSDOE52/docs/downloads/gems52-h60-unionmax-37654px-20261010T185134Z-5406fdcdcf46-zeros.tif",
    }
    rows = []
    for key, rel in registry_files.items():
        path = ROOT / rel
        entry = {"key": key, "file": rel,
                 "sha256": sha(path) if path.exists() else None}
        try:
            with rasterio.open(path) as src:
                if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs,
                                                            grid.transform):
                    raise ValueError("grid mismatch")
                theirs = src.read(1).astype(np.float32)
            mine_d = candidate
            sup_frac = float((np.isfinite(theirs) & (theirs > 0) & fp).sum()
                             / fp.sum())
            entry["their_support_fraction"] = sup_frac
            entry["their_dots"] = int((np.isfinite(theirs) & (theirs > 0)).sum())
            entry["sparse"] = bool(sup_frac <= 0.10)
            rho = uniqueness.surface_rho(mine_d, theirs, fp)
            entry["spearman_full_footprint"] = rho["spearman_full_footprint"]
            entry["overlap_final_dots"] = uniqueness.dot_overlap(mine_d, theirs)
            surf_support = (np.isfinite(scores["score"]) & (scores["score"] > 0))
            entry["overlap_surface_stage"] = uniqueness.dot_overlap(
                surf_support.astype(np.float32), theirs)
            entry["duplicate_by_rho"] = bool(
                (rho["spearman_full_footprint"] or 0) > 0.90)
            entry["duplicate_by_overlap_gated"] = bool(
                entry["sparse"] and entry["overlap_final_dots"] > 0.70)
            entry["supplementary"] = key.endswith("_sup")
        except (OSError, ValueError) as exc:
            entry["error"] = str(exc)
        rows.append(entry)
        print(f"uniq {key}: {json.dumps({k: entry.get(k) for k in ('their_dots', 'sparse', 'spearman_full_footprint', 'overlap_final_dots', 'error')})}",
              flush=True)
    gated = [r for r in rows if not r.get("error") and not r.get("supplementary")]
    gate6 = all(not r["duplicate_by_rho"] for r in gated)
    gate7 = all(not r["duplicate_by_overlap_gated"] for r in gated)
    print(f"gate6 (rho<0.90 all): {gate6} | gate7 (overlap<0.70 sparse): {gate7}",
          flush=True)
    dump(E / "exp2_uniqueness_subset.json",
         {"evidence_class": "REGISTRY-MEASUREMENT-PARTIAL",
          "scope": "Preregistered 9-file subset + 3 supplementary; NOT a complete "
                   "862-raster scan. Dense rasters: rho-gated only (revision R1); "
                   "pre-R1 literal overlap reported in overlap_surface_stage.",
          "revision_R1": "docs/hypotheses-round2.md",
          "my_dots": int(dots.sum()), "rows": rows})

    # ---- gate5: byte check vs full 862 index ----
    index = json.loads((ROOT / "registry/inherited_registry_index.json").read_text())
    indexed = {r["sha256"] for r in index["rasters"]}
    print(f"index rasters: {len(indexed)}", flush=True)

    gates = {"gate1_canaries": True, "gate2_beat_exp1": gate2,
             "gate3_beat_random": gate3, "gate4_artifact": True,
             "gate6_rho": gate6, "gate7_overlap": gate7}
    verdict = "promote" if all(gates.values()) else "negative"
    card = {
        "hypothesis": "Shallow magnetic lineaments from TMI vertical gradient",
        "mechanism": "Hessian centerlines of VG (both polarities) OR VG-gradient "
                     "contact ridges; NMS thin; greedy 38k binary dots, 2px "
                     "spacing, catalogue-distance>2 prune",
        "non_fault_mimic": "Lava-flow margin / paleochannel magnetic lag / "
                           "survey-leveling residual (E-W diagnostic passed)",
        "hypothesis_status": "Provisional lane: method paragraph absent from prompt",
        "verdict": verdict if verdict == "negative" else "promote-pending-format",
        "experiment": 2, "seeds": list(SEEDS),
        "holdout_dti": {
            "seed20": s20["scores"]["candidate"],
            "seed71": s71["scores"]["candidate"],
            "paired_differences_vs_candidate_seed20":
                s20["paired_differences_vs_candidate"],
            "paired_differences_vs_candidate_seed71":
                s71["paired_differences_vs_candidate"]},
        "emission": emission, "ew_fraction": ew,
        "ew_fraction_skeleton_diagnostic": ew_skel,
        "gates": gates, "weekly_slots_used": 0,
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "organizer_confirmed_score": None,
    }
    if verdict == "negative":
        card["verdict"] = "negative"
        dump(E / "exp2_run_card.json", card)
        print("VERDICT: negative — no submission written", flush=True)
        return

    # ---- gate8: shared writer on exact bytes (only on full pass) ----
    out = ROOT / "docs/downloads" / f"{SUBMISSION_NAME}.tif"
    note = ("VG-line H1 B2 38k dots; holdout-DTI s20 "
            f"{s20['scores']['candidate']['dti']:.4f} "
            f"[{s20['scores']['candidate']['ci95'][0]:.4f},"
            f"{s20['scores']['candidate']['ci95'][1]:.4f}] s71 "
            f"{s71['scores']['candidate']['dti']:.4f} "
            f"[{s71['scores']['candidate']['ci95'][0]:.4f},"
            f"{s71['scores']['candidate']['ci95'][1]:.4f}]; fmt-valid")
    assert len(note) <= 140, note
    receipt = write_submission(out, candidate, DATA / "sample_submission.tif", fp,
                               note=note, name=SUBMISSION_NAME,
                               catalogue=grid.catalogue)
    file_sha = receipt["sha256"]
    gate5 = file_sha not in indexed
    print(f"gate5 (byte-unique vs {len(indexed)}): {gate5}", flush=True)
    if not gate5:
        out.unlink(missing_ok=True)
        out.with_suffix(".zip").unlink(missing_ok=True)
        out.with_suffix(".json").unlink(missing_ok=True)
        card["verdict"] = "negative"
        card["gates"]["gate5_byte_unique"] = False
        dump(E / "exp2_run_card.json", card)
        print("VERDICT: negative — byte duplicate; artifacts removed", flush=True)
        return
    card["gates"]["gate5_byte_unique"] = True
    card["verdict"] = "promote"
    card["raster_sha256"] = file_sha
    card["validator_output"] = {
        "submission_tiff": str(out.relative_to(ROOT)),
        "local_validation": receipt["validator"],
        "template_report_ok": receipt["template_report"]["ok"],
        "zip_sha256": receipt["zip_sha256"],
    }
    card["submission_name"] = SUBMISSION_NAME
    card["submission_note"] = note
    card["download_and_submit_ok"] = (
        "FORMAT-VALID CANDIDATE — download available; organizer acceptance NOT "
        "guaranteed; uniqueness is PARTIAL-subset (see scope); slot decision is "
        "the operator's.")
    dump(E / "exp2_run_card.json", card)
    print(f"VERDICT: promote — {out.name} sha256={file_sha}", flush=True)


if __name__ == "__main__":
    main()
