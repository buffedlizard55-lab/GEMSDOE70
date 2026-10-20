"""E2 bounded experiment: scarp-strain-cover ranking + dotted emission.

Preregistration: docs/hypotheses-e2.md. Shared evaluator/writer/uniqueness
from vendor/gems57 (byte-pinned, unmodified). Refuses to rerun if the E2
manifest exists. Writes a submission TIFF only if every preregistered gate
passes; otherwise verdict negative and no TIFF is published.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid
from gems70.method_e2 import (
    dotted_emission, fill_nearest, joint_field_e2, physical_features_e2,
    random_dotted, rank01, upper_surface_e2,
)

E = ROOT / "evidence"
DATA = ROOT / ".cache/data"
REG_DIR = ROOT / ".cache/src/g60/registry/rasters"
DENSE_WITNESS = ROOT / ".cache/src/g17/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif"
H33_PATH = REG_DIR / "GEMSDOE32__h33-2-b2-zeros.tif"
PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}
H33_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
DENSE_SHA = "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be"
BANDS = {"inv2": 4, "shear": 7, "dilat": 8, "det_elev": 12, "depth": 15, "slope19": 19}
BUDGETS = (20000, 30000, 38000, 45000)
EXCLUSIONS = (0, 1, 2, 3)


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def cropped_terms(folds, p, valid):
    """Pooled block terms for one full-grid field over all folds (E1 pattern)."""
    total = None
    per_fold = []
    for fold in folds:
        y, x = np.nonzero(fold["region"])
        y0, x0 = max(0, int(y.min()) - 6), max(0, int(x.min()) - 6)
        y1, x1 = min(p.shape[0], int(y.max()) + 7), min(p.shape[1], int(x.max()) + 7)
        sl = np.s_[y0:y1, x0:x1]
        sub = {k: v[sl] for k, v in fold.items()
               if isinstance(v, np.ndarray) and v.shape == p.shape}
        res, terms = evaluate_holdout.evaluate(
            p[sl], sub, valid[sl], origin=(y0, x0), global_shape=p.shape)
        per_fold.append(res)
        total = terms if total is None else total + terms
    return per_fold, total


def registry_index():
    recs = []
    for p in sorted(REG_DIR.glob("*.tif")):
        recs.append(dict(repo="60GEMSDOE@3202471", submission=f"registry/rasters/{p.name}",
                         file=str(p), sha256=sha(p)))
    recs.append(dict(repo="17GEMSDOE", submission="docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
                     file=str(DENSE_WITNESS), sha256=sha(DENSE_WITNESS)))
    return recs


def main():
    start = time.monotonic()

    def budget_check():
        if time.monotonic() - start > 7200:
            raise TimeoutError("two-hour experiment budget exhausted")

    manifest = E / "experiment_manifest_e2.json"
    if manifest.exists():
        raise RuntimeError("E2 already attempted. Inspect evidence; no silent reruns/tuning.")
    dump(manifest, {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment_count": 2, "maximum_experiments": 3, "maximum_seconds": 7200,
        "preregistration": "docs/hypotheses-e2.md",
        "preregistration_sha256": sha(ROOT / "docs/hypotheses-e2.md"),
        "source_sha256": {p: sha(ROOT / p) for p in
                          ["src/gems70/method_e2.py", "scripts/run_experiment_e2.py"]},
    })
    for name, exp in PINS.items():
        if sha(DATA / name) != exp:
            raise ValueError(f"input pin mismatch: {name}")
    if sha(H33_PATH) != H33_SHA or sha(DENSE_WITNESS) != DENSE_SHA:
        raise ValueError("registry witness pin mismatch")
    dump(E / "data_receipt_e2.json", {
        "evidence_class": "DATA-MEASUREMENT",
        "provenance": "Public owner mirrors via git sparse checkout; hash consistency is not organizer authentication",
        "files": {n: {"sha256": sha(DATA / n), "expected": v, "ok": True} for n, v in PINS.items()},
        "h33_reference_sha256": H33_SHA, "dense_witness_sha256": DENSE_SHA,
    })

    grid = load_grid(DATA)
    fp = grid.footprint
    raw = {}
    with rasterio.open(DATA / "training_features.tif") as src:
        if (src.shape, str(src.crs), tuple(src.transform)[:6]) != (
                grid.shape, str(grid.crs), tuple(grid.transform)[:6]):
            raise ValueError("feature grid mismatch")
        dump(E / "feature_metadata_e2.json", {
            "descriptions": list(src.descriptions), "nodata": src.nodata,
            "crs": str(src.crs), "shape": list(src.shape),
            "transform": list(src.transform)[:6], "bands_used_1indexed": BANDS})
        for key, idx in BANDS.items():
            a = src.read(idx).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            raw[key] = a
    valid0 = fp.copy()
    for a in raw.values():
        valid0 &= np.isfinite(a)
    # Fill from ORIGINAL finite domain, then erode output support (E1 fix).
    filled = {k: fill_nearest(raw[k]) for k in ("det_elev", "inv2", "shear", "dilat", "depth")}
    valid = ndi.binary_erosion(valid0, iterations=12)
    if not valid.any():
        raise ValueError("no valid interior features")
    print(f"valid0={int(valid0.sum())} eroded_valid={int(valid.sum())}", flush=True)
    feats = physical_features_e2(filled, valid)
    del filled
    budget_check()
    print("features complete", flush=True)

    joint = joint_field_e2(feats, valid)
    joints = {
        "joint": joint,
        "joint_nostrain": joint_field_e2(feats, valid, 0.75, 0.0, 0.25),
        "joint_nocover": joint_field_e2(feats, valid, 0.75, 0.25, 0.0),
        "joint_nocoh": joint_field_e2(feats, valid, scarp_key="scarp_nocoh"),
    }
    slope19_rank = rank01(np.where(np.isfinite(raw["slope19"]), raw["slope19"], 0), valid)

    folds, _ = holdout.buffered_component_draw(grid, seed=30, buffer_px=3, boundary_px=12)
    dump(E / "holdout_split_e2.json", {
        "evidence_class": "HOLDOUT-DTI", "evaluator_version": evaluate_holdout.VERSION,
        "receipts": [f["receipt"] for f in folds],
        "total_withheld_positive_pixels": int(sum((f["truth"] & valid).sum() for f in folds)),
        "catalogue_predictors": ["fold-visible catalogue mask/distance for emission allowed-mask only; ranking is catalogue-independent"],
        "valid_feature_pixels": int(valid.sum()),
        "seed": 30, "note": "Untouched seed (E1 used 20). Mapped components are a surrogate for hidden expert faults.",
    })

    # --- leakage canaries (every raw + derived feature alone) ---
    truth = np.zeros(fp.shape, bool)
    active = np.zeros(fp.shape, bool)
    for fold in folds:
        active |= valid & fold["region"] & ~fold["masked_known"]
        truth |= valid & fold["truth"]
    positives = np.flatnonzero(truth)
    negatives = np.flatnonzero(active & ~truth)
    rng = np.random.default_rng(70030)
    negatives = rng.choice(negatives, min(200000, len(negatives)), replace=False)
    labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]
    canary_fields = {
        **{f"raw_{k}": v for k, v in raw.items()},
        **feats, **joints, "slope19_rank": slope19_rank,
    }
    canaries = {}
    for name, a in canary_fields.items():
        values = np.r_[a.ravel()[positives], a.ravel()[negatives]]
        if not np.isfinite(values).all():
            raise ValueError(f"canary field {name} non-finite on scored sample")
        auc = float(roc_auc_score(labels, values))
        canaries[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc,
                          "inverse_auc": 1 - auc,
                          "withheld_positive_pixels": int(len(positives)),
                          "negative_sample_pixels": int(len(negatives)),
                          "suspected_leakage": bool(max(auc, 1 - auc) > 0.90)}
    dump(E / "canaries_e2.json", canaries)
    if any(c["suspected_leakage"] for c in canaries.values()):
        raise RuntimeError("LEAKAGE CANARY STOP: AUC > .90; no joint interpretation permitted")
    print("canaries complete", flush=True)

    # --- continuous arms (E1-continuity diagnostic) ---
    cont_defs = {
        "slope19": slope19_rank, "dem_slope": rank01(feats["dem_slope"], valid),
        "dem_curv": rank01(feats["dem_curv"], valid),
        "dem_coherence": feats["dem_coherence"],
        "scarp": feats["scarp"], "strain": feats["strain"], "shallow": feats["shallow"],
        **joints,
    }
    cont_terms, cont_folds = {}, {}
    for name, rank_field in cont_defs.items():
        budget_check()
        arm = upper_surface_e2(rank_field, valid)
        per, terms = cropped_terms(folds, arm, valid)
        cont_terms[name], cont_folds[name] = terms, per
        del arm
        print(f"continuous {name} evaluated", flush=True)
    rnd = np.zeros(fp.shape, np.float32)
    n_top = int((upper_surface_e2(joint, valid) > 0).sum())
    ids = rng.choice(np.flatnonzero(valid), n_top, replace=False)
    rnd.ravel()[ids] = 0.5
    per, terms = cropped_terms(folds, rnd, valid)
    cont_terms["random_iid"], cont_folds["random_iid"] = terms, per
    del rnd
    cont_summary = evaluate_holdout.pooled_summary(cont_terms, draws=1000, seed=70030, candidate="joint")
    cont_summary["interpretation"] = "Continuous top-2% diagnostic HOLDOUT-DTI (E1 continuity), not primary endpoint."
    dump(E / "holdout_continuous_e2.json", cont_summary)
    dump(E / "holdout_continuous_folds_e2.json", cont_folds)
    singles = ["slope19", "dem_slope", "dem_curv", "dem_coherence", "scarp", "strain", "shallow"]
    best_single = max(singles, key=lambda n: cont_summary["scores"][n]["dti"])
    print(f"best single continuous: {best_single}", flush=True)

    # --- dotted selection grid (primary endpoint) ---
    visible = folds[0]["visible"]
    masked_known = folds[0]["masked_known"]
    dist_visible = ndi.distance_transform_edt(~visible)
    grid_rows, dotted_terms_cache = [], {}
    for excl in EXCLUSIONS:
        allowed = valid & ~masked_known & (dist_visible > excl)
        for bud in BUDGETS:
            budget_check()
            dots = dotted_emission(joint, allowed, bud)
            field = dots.astype(np.float32)
            per, terms = cropped_terms(folds, field, valid)
            dti = float(evaluate_holdout.from_terms(terms.sum(axis=0)))
            grid_rows.append({"budget": bud, "exclusion_px": excl,
                              "dots_emitted_global": int(dots.sum()),
                              "pooled_dotted_dti": dti})
            dotted_terms_cache[(bud, excl)] = (terms, per)
            del dots, field
            print(f"dotted budget={bud} excl={excl} DTI={dti:.5f}", flush=True)
    sel = max(grid_rows, key=lambda r: (r["pooled_dotted_dti"], -r["budget"], -r["exclusion_px"]))
    sel_bud, sel_excl = sel["budget"], sel["exclusion_px"]
    if sel["dots_emitted_global"] < sel_bud:
        raise RuntimeError("selected emission truncated by candidate cap; preregistered budget unreachable")
    dump(E / "selection_grid_e2.json", {
        "evidence_class": "HOLDOUT-DTI", "evaluator_version": evaluate_holdout.VERSION,
        "rows": grid_rows, "selected": sel,
        "rule": "max pooled dotted DTI; tie -> smaller budget, then smaller exclusion"})

    # --- dotted comparators at selected cell ---
    allowed_sel = valid & ~masked_known & (dist_visible > sel_excl)
    dotted_terms = {"joint_dotted": dotted_terms_cache[(sel_bud, sel_excl)][0]}
    dotted_folds = {"joint_dotted": dotted_terms_cache[(sel_bud, sel_excl)][1]}
    comp_fields = {"scarp_dotted": feats["scarp"], "slope19_dotted": slope19_rank,
                   "best_single_dotted": cont_defs[best_single]}
    for name, rank_field in comp_fields.items():
        budget_check()
        dots = dotted_emission(rank_field, allowed_sel, sel_bud)
        per, terms = cropped_terms(folds, dots.astype(np.float32), valid)
        dotted_terms[name], dotted_folds[name] = terms, per
        del dots
        print(f"comparator {name} evaluated", flush=True)
    rdots = random_dotted(allowed_sel, sel_bud, seed=70030)
    per, terms = cropped_terms(folds, rdots.astype(np.float32), valid)
    dotted_terms["random_dotted"], dotted_folds["random_dotted"] = terms, per
    del rdots
    with rasterio.open(H33_PATH) as src:
        h33 = src.read(1).astype(np.float32)
    h33 = np.where(np.isfinite(h33), h33, 0)
    per, terms = cropped_terms(folds, h33, valid)
    dotted_terms["h33_reference"], dotted_folds["h33_reference"] = terms, per
    del h33
    dotted_summary = evaluate_holdout.pooled_summary(
        dotted_terms, draws=1000, seed=70030, candidate="joint_dotted")
    dotted_summary["interpretation"] = (
        "Primary dotted HOLDOUT-DTI. h33_reference used the full catalogue when built "
        "(pruning saw withheld traces); reference only, never the promotion bar.")
    dotted_summary["best_single_continuous_name"] = best_single
    dotted_summary["selected_budget"] = sel_bud
    dotted_summary["selected_exclusion_px"] = sel_excl
    dump(E / "holdout_e2.json", dotted_summary)
    dump(E / "holdout_folds_e2.json", dotted_folds)
    print(json.dumps(dotted_summary["scores"], indent=2), flush=True)

    # --- surface uniqueness BEFORE final placement (rho gate) ---
    surface = joint.copy()
    surface[grid.catalogue] = 0
    surface[~fp] = 0
    idx = registry_index()
    print(f"registry rasters to check: {len(idx)}", flush=True)
    surf_audit = uniqueness.compare_array_to_registry(
        surface, idx, fp, include_reverse=True, expected_grid=(grid.shape, grid.crs, grid.transform))
    surf_two = uniqueness.two_phase_summary(surf_audit["rows"], int(fp.sum()),
                                            expected_rasters=len(idx))
    dump(E / "surface_uniqueness_e2.json", {"audit": surf_audit, "two_phase": surf_two})
    surface_rho_dup = surf_two["literal_reading"]["worst_spearman_full_footprint"] is not None and \
        surf_two["literal_reading"]["worst_spearman_full_footprint"] > 0.90
    print(f"surface worst rho={surf_two['literal_reading']['worst_spearman_full_footprint']}", flush=True)

    # --- final dots (only if surface rho passes) ---
    final_audit = final_two = None
    final_dots = None
    n_final = 0
    if not surface_rho_dup:
        dist_full = ndi.distance_transform_edt(~grid.catalogue)
        allowed_final = valid & ~grid.catalogue & (dist_full > sel_excl)
        final_dots = dotted_emission(joint, allowed_final, sel_bud)
        n_final = int(final_dots.sum())
        print(f"final dots: {n_final} (budget {sel_bud})", flush=True)
        final_field = final_dots.astype(np.float32)
        final_audit = uniqueness.compare_array_to_registry(
            final_field, idx, fp, include_reverse=True,
            expected_grid=(grid.shape, grid.crs, grid.transform))
        final_two = uniqueness.two_phase_summary(final_audit["rows"], int(fp.sum()),
                                                 expected_rasters=len(idx))
        dump(E / "final_uniqueness_e2.json", {"audit": final_audit, "two_phase": final_two})
        np.save(ROOT / ".cache/final_dots_e2.npy", final_field)
        print(f"final like-for-like: {final_two['like_for_like_reading']}", flush=True)

    # --- promotion gates ---
    scores = dotted_summary["scores"]
    diffs = dotted_summary["paired_differences"]
    gates_detail = {
        "canaries_pass": not any(c["suspected_leakage"] for c in canaries.values()),
        "beats_random_ci": bool(diffs["random_dotted"]["ci95"][0] > 0),
        "beats_singles_point": bool(all(
            scores["joint_dotted"]["dti"] > scores[n]["dti"]
            for n in ("scarp_dotted", "slope19_dotted", "best_single_dotted"))),
        "surface_rho_pass": not surface_rho_dup,
        "final_unique_pass": bool(final_two and not final_two["like_for_like_reading"]["duplicate"]),
        "final_budget_reached": bool(n_final == sel_bud),
    }
    promote = all(gates_detail.values())
    print(f"gates: {gates_detail} promote={promote}", flush=True)

    # --- writer (only on promote) ---
    receipt = None
    sub_name = f"gems70e2-scarpstrain-{sel_bud // 1000}k-ex{sel_excl}-20261020-zeros"
    note = (f"E2 DEM scarp-curvature x geodetic strain, shallow-cover gate; "
            f"dotted {n_final} excl>{sel_excl}px sep2.8; holdout-validated")
    assert len(note) <= 140 and len(sub_name) <= 140, (len(note), len(sub_name))
    raster_sha = None
    validator_out = {"submission_tiff": None, "status": "NOT_WRITTEN",
                     "reason": "Promotion gates failed; see gates in run card."}
    if promote:
        budget_check()
        from gems57.submission_writer import write_submission
        out = ROOT / "submissions" / f"{sub_name}.tif"
        field = final_dots.astype(np.float32)
        assert np.isfinite(field).all() and field.min() >= 0 and field.max() <= 1
        assert not field[grid.catalogue].any() and not field[~fp].any()
        receipt = write_submission(out, field, DATA / "sample_submission.tif", fp,
                                   note=note, name=sub_name, catalogue=grid.catalogue,
                                   metadata={"run": "E2", "holdout_evaluator": evaluate_holdout.VERSION,
                                             "selected_budget": sel_bud, "selected_exclusion_px": sel_excl})
        raster_sha = receipt["sha256"]
        validator_out = receipt["validator"]
        dump(E / "validator_e2.json", receipt)

    card = {
        "hypothesis": "DEM scarp curvature gated by geodetic strain partitioning and shallow basement cover",
        "mechanism": "Strike-coherent profile-curvature scarp steps (slope x curvature x tensor coherence) weighted by smoothed geodetic strain corridor and inverted depth-to-basement; rank-ordered 2.8px dotted emission off-catalogue",
        "non_fault_mimic": "Lake-shoreline or fluvial terrace riser; road cut",
        "hypothesis_status": "Provisional lane declared in docs/hypotheses-e2.md: prompt supplies no identifiable method paragraph",
        "verdict": "promote" if promote else "negative",
        "stop_reason": None if promote else "promotion gates failed (see gates)",
        "gates": gates_detail,
        "holdout_dti": {**scores["joint_dotted"],
                        "stage": "final dotted emission rule scored on hide-and-recover folds (visible-only masks)",
                        "selected_budget": sel_bud, "selected_exclusion_px": sel_excl,
                        "random_control_dti": scores["random_dotted"]["dti"],
                        "paired_delta_vs_random": diffs["random_dotted"]},
        "continuous_diagnostic_dti": cont_summary["scores"]["joint"],
        "correlation_overlap_vs_registry": {
            "stage": "surface rho pre-placement + final dots",
            "rasters_checked": len(idx), "registry_complete": False,
            "registry_scope": "62 pinned 60GEMSDOE registry rasters + 17GEMSDOE dense witness, hash-verified locally; inherited inventory lists 862 unique rasters - full scan is a selector step",
            "surface_worst_spearman": surf_two["literal_reading"]["worst_spearman_full_footprint"],
            "surface_worst_spearman_submission": surf_two["literal_reading"]["worst_spearman_submission"],
            "final_worst_spearman": (final_two["literal_reading"]["worst_spearman_full_footprint"] if final_two else None),
            "final_worst_dot_overlap_like_for_like": (final_two["like_for_like_reading"]["worst_forward_overlap_dot_fields"] if final_two else None),
            "final_worst_dot_overlap_submission": (final_two["like_for_like_reading"]["worst_forward_overlap_dot_field_submission"] if final_two else None),
            "final_literal_worst_overlap": (final_two["literal_reading"]["worst_forward_overlap"] if final_two else None),
            "duplicate_like_for_like": (final_two["like_for_like_reading"]["duplicate"] if final_two else None),
        },
        "raster_sha256": raster_sha,
        "raster_sha256_reason": None if raster_sha else "No TIFF written: promotion gates failed.",
        "surface_decoded_float32_sha256": hashlib.sha256(np.ascontiguousarray(surface).tobytes()).hexdigest(),
        "validator_output": validator_out,
        "submission_name": sub_name if promote else f"{sub_name}-NOT-RELEASED",
        "submission_note": (note if promote else
                            "E2 scarp-strain-cover dotted candidate; NEGATIVE gates; DO NOT SUBMIT.")[:140],
        "download_and_submit_ok": False,
        "download_candidate_ok": bool(promote),
        "slot_authorized": False,
        "slot_note": "Slot use requires separate selector step incl. full-registry scan + weekly-cap check on official submission page.",
        "weekly_slots_used": 0,
        "experiment_count": 2,
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "organizer_confirmed_score": None,
        "n_final_dots": n_final,
        "evaluator_implementation_sha256": evaluate_holdout.implementation_hashes(),
        "method_source_sha256": {p: sha(ROOT / p) for p in
                                 ["src/gems70/method_e2.py", "scripts/run_experiment_e2.py"]},
    }
    dump(E / "run_card_e2.json", card)
    print(json.dumps(card, indent=2), flush=True)


if __name__ == "__main__":
    main()
