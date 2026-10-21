"""E3 bounded experiment (3 of 3): DEM scarp curvature alone + dotted emission.

Preregistration: docs/hypotheses-e3.md. Reuses E2 scarp code in
src/gems70/method_e2.py and shared vendor/gems57 evaluator/writer/uniqueness
(byte-pinned, unmodified). Refuses to rerun if the E3 manifest exists.
Writes a TIFF only if every preregistered gate passes.
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
    random_dotted, rank01,
)

E = ROOT / "evidence"
DATA = ROOT / ".cache/data"
REG_DIR = ROOT / ".cache/src/g60/registry/rasters"
DENSE_WITNESS = ROOT / ".cache/src/g17/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif"
PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}
BANDS = {"inv2": 4, "shear": 7, "dilat": 8, "det_elev": 12, "depth": 15, "slope19": 19}
BUDGETS = (30000, 38000, 45000, 60000)
EXCLUSIONS = (0, 1, 2, 3)
SATURATION_LIMIT = 0.70


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
    total, per_fold = None, []
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
    recs = [dict(repo="60GEMSDOE@3202471", submission=f"registry/rasters/{p.name}",
                 file=str(p), sha256=sha(p)) for p in sorted(REG_DIR.glob("*.tif"))]
    recs.append(dict(repo="17GEMSDOE",
                     submission="docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
                     file=str(DENSE_WITNESS), sha256=sha(DENSE_WITNESS)))
    return recs


def saturation_adjusted(rows, grid):
    """Classify firings by vendor halo-coverage certificates (see prereg)."""
    checked = [r for r in rows if "error" not in r]
    certs, adjusted_firings, saturating = {}, [], []
    worst_adj, worst_adj_who = None, None
    for r in checked:
        cert = uniqueness.saturation_certificate(
            Path(r["file"]), grid.footprint, grid.catalogue,
            expected_grid=(grid.shape, grid.crs, grid.transform))
        certs[r["submission"]] = cert["covered_allowed_fraction"]
        sat = cert["covered_allowed_fraction"] >= SATURATION_LIMIT
        r["halo_covered_allowed_fraction"] = cert["covered_allowed_fraction"]
        r["saturating"] = bool(sat)
        if sat:
            saturating.append({"submission": r["submission"],
                                "covered_allowed_fraction": cert["covered_allowed_fraction"],
                                "forward_overlap": r["my_dots_within_3px_of_theirs"],
                                "jaccard": r["jaccard_dot_sets"],
                                "spearman": r["spearman_full_footprint"]})
        else:
            ov = r["my_dots_within_3px_of_theirs"]
            if worst_adj is None or ov > worst_adj:
                worst_adj, worst_adj_who = ov, r["submission"]
            if ov > 0.70:
                adjusted_firings.append(r["submission"])
    rho_firings = [r["submission"] for r in checked
                   if r.get("spearman_full_footprint") is not None
                   and r["spearman_full_footprint"] > 0.90]
    jac_firings = [r["submission"] for r in checked if r["jaccard_dot_sets"] > 0.50]
    return {
        "rule": "rho<=0.90 all; Jaccard<=0.50 all; forward<=0.70 where halo coverage<0.70",
        "saturation_limit": SATURATION_LIMIT,
        "worst_forward_overlap_nonsaturating": worst_adj,
        "worst_forward_overlap_nonsaturating_submission": worst_adj_who,
        "adjusted_forward_firings": adjusted_firings,
        "rho_firings": rho_firings, "jaccard_firings": jac_firings,
        "saturating_fields": saturating,
        "duplicate_adjusted": bool(adjusted_firings or rho_firings or jac_firings),
        "certificates": certs,
    }


def main():
    start = time.monotonic()

    def budget_check():
        if time.monotonic() - start > 7200:
            raise TimeoutError("two-hour experiment budget exhausted")

    manifest = E / "experiment_manifest_e3.json"
    if manifest.exists():
        raise RuntimeError("E3 already attempted. Inspect evidence; budget exhausted.")
    dump(manifest, {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment_count": 3, "maximum_experiments": 3, "maximum_seconds": 7200,
        "preregistration": "docs/hypotheses-e3.md",
        "preregistration_sha256": sha(ROOT / "docs/hypotheses-e3.md"),
        "source_sha256": {p: sha(ROOT / p) for p in
                          ["src/gems70/method_e2.py", "scripts/run_experiment_e3.py"]},
    })
    for name, exp in PINS.items():
        if sha(DATA / name) != exp:
            raise ValueError(f"input pin mismatch: {name}")

    grid = load_grid(DATA)
    fp = grid.footprint
    raw = {}
    with rasterio.open(DATA / "training_features.tif") as src:
        for key, idx in BANDS.items():
            a = src.read(idx).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            raw[key] = a
    valid0 = fp.copy()
    for a in raw.values():
        valid0 &= np.isfinite(a)
    filled = {k: fill_nearest(raw[k]) for k in ("det_elev", "inv2", "shear", "dilat", "depth")}
    valid = ndi.binary_erosion(valid0, iterations=12)
    feats = physical_features_e2(filled, valid)
    del filled
    scarp = feats["scarp"]
    joint_ctrl = joint_field_e2(feats, valid)
    slope19_rank = rank01(np.where(np.isfinite(raw["slope19"]), raw["slope19"], 0), valid)
    print("features complete", flush=True)

    folds, _ = holdout.buffered_component_draw(grid, seed=40, buffer_px=3, boundary_px=12)
    dump(E / "holdout_split_e3.json", {
        "evidence_class": "HOLDOUT-DTI", "evaluator_version": evaluate_holdout.VERSION,
        "receipts": [f["receipt"] for f in folds],
        "total_withheld_positive_pixels": int(sum((f["truth"] & valid).sum() for f in folds)),
        "valid_feature_pixels": int(valid.sum()), "seed": 40,
        "note": "Untouched seed (E1=20, E2=30). Ranking catalogue-independent; masks visible-only.",
    })
    truth = np.zeros(fp.shape, bool)
    active = np.zeros(fp.shape, bool)
    for fold in folds:
        active |= valid & fold["region"] & ~fold["masked_known"]
        truth |= valid & fold["truth"]
    positives = np.flatnonzero(truth)
    negatives = np.flatnonzero(active & ~truth)
    rng = np.random.default_rng(70040)
    negatives = rng.choice(negatives, min(200000, len(negatives)), replace=False)
    labels = np.r_[np.ones(len(positives)), np.zeros(len(negatives))]
    canaries = {}
    for name, a in {**{f"raw_{k}": v for k, v in raw.items()}, **feats,
                    "joint_ctrl": joint_ctrl, "slope19_rank": slope19_rank}.items():
        values = np.r_[a.ravel()[positives], a.ravel()[negatives]]
        auc = float(roc_auc_score(labels, values))
        canaries[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc,
                          "inverse_auc": 1 - auc,
                          "withheld_positive_pixels": int(len(positives)),
                          "negative_sample_pixels": int(len(negatives)),
                          "suspected_leakage": bool(max(auc, 1 - auc) > 0.90)}
    dump(E / "canaries_e3.json", canaries)
    if any(c["suspected_leakage"] for c in canaries.values()):
        raise RuntimeError("LEAKAGE CANARY STOP")
    print("canaries complete", flush=True)

    visible, masked_known = folds[0]["visible"], folds[0]["masked_known"]
    dist_visible = ndi.distance_transform_edt(~visible)
    grid_rows, cache = [], {}
    for excl in EXCLUSIONS:
        allowed = valid & ~masked_known & (dist_visible > excl)
        for bud in BUDGETS:
            budget_check()
            dots = dotted_emission(scarp, allowed, bud)
            per, terms = cropped_terms(folds, dots.astype(np.float32), valid)
            dti = float(evaluate_holdout.from_terms(terms.sum(axis=0)))
            grid_rows.append({"budget": bud, "exclusion_px": excl,
                              "dots_emitted_global": int(dots.sum()), "pooled_dotted_dti": dti})
            cache[(bud, excl)] = (terms, per)
            del dots
            print(f"scarp budget={bud} excl={excl} DTI={dti:.5f}", flush=True)
    sel = max(grid_rows, key=lambda r: (r["pooled_dotted_dti"], -r["budget"], -r["exclusion_px"]))
    sel_bud, sel_excl = sel["budget"], sel["exclusion_px"]
    if sel["dots_emitted_global"] < sel_bud:
        raise RuntimeError("selected emission truncated by candidate cap")
    dump(E / "selection_grid_e3.json", {
        "evidence_class": "HOLDOUT-DTI", "evaluator_version": evaluate_holdout.VERSION,
        "rows": grid_rows, "selected": sel,
        "rule": "max pooled dotted DTI; tie -> smaller budget, then smaller exclusion"})

    allowed_sel = valid & ~masked_known & (dist_visible > sel_excl)
    dotted_terms = {"scarp_dotted": cache[(sel_bud, sel_excl)][0]}
    dotted_folds = {"scarp_dotted": cache[(sel_bud, sel_excl)][1]}
    for name, rank_field in (("slope19_dotted", slope19_rank), ("joint_ctrl_dotted", joint_ctrl)):
        dots = dotted_emission(rank_field, allowed_sel, sel_bud)
        per, terms = cropped_terms(folds, dots.astype(np.float32), valid)
        dotted_terms[name], dotted_folds[name] = terms, per
        del dots
        print(f"control {name} evaluated", flush=True)
    rdots = random_dotted(allowed_sel, sel_bud, seed=70040)
    per, terms = cropped_terms(folds, rdots.astype(np.float32), valid)
    dotted_terms["random_dotted"], dotted_folds["random_dotted"] = terms, per
    del rdots
    summary = evaluate_holdout.pooled_summary(dotted_terms, draws=1000, seed=70040,
                                              candidate="scarp_dotted")
    summary["interpretation"] = "Primary dotted HOLDOUT-DTI on untouched seed-40 folds; falsification instrument, not a live-score predictor (see hypotheses-e3 H33 lesson)."
    summary["selected_budget"], summary["selected_exclusion_px"] = sel_bud, sel_excl
    dump(E / "holdout_e3.json", summary)
    dump(E / "holdout_folds_e3.json", dotted_folds)
    print(json.dumps(summary["scores"], indent=2), flush=True)

    idx = registry_index()
    surface = scarp.copy()
    surface[grid.catalogue] = 0
    surface[~fp] = 0
    surf_audit = uniqueness.compare_array_to_registry(
        surface, idx, fp, include_reverse=True, expected_grid=(grid.shape, grid.crs, grid.transform))
    surf_two = uniqueness.two_phase_summary(surf_audit["rows"], int(fp.sum()), expected_rasters=len(idx))
    surf_adj = saturation_adjusted(surf_audit["rows"], grid)
    dump(E / "surface_uniqueness_e3.json", {"audit": surf_audit, "two_phase": surf_two, "adjusted": surf_adj})
    print(f"surface adjusted duplicate={surf_adj['duplicate_adjusted']}", flush=True)

    final_audit = final_two = final_adj = None
    final_dots, n_final = None, 0
    if not surf_adj["duplicate_adjusted"]:
        dist_full = ndi.distance_transform_edt(~grid.catalogue)
        allowed_final = valid & ~grid.catalogue & (dist_full > sel_excl)
        final_dots = dotted_emission(scarp, allowed_final, sel_bud)
        n_final = int(final_dots.sum())
        print(f"final dots: {n_final}", flush=True)
        field = final_dots.astype(np.float32)
        final_audit = uniqueness.compare_array_to_registry(
            field, idx, fp, include_reverse=True, expected_grid=(grid.shape, grid.crs, grid.transform))
        final_two = uniqueness.two_phase_summary(final_audit["rows"], int(fp.sum()), expected_rasters=len(idx))
        final_adj = saturation_adjusted(final_audit["rows"], grid)
        dump(E / "final_uniqueness_e3.json", {"audit": final_audit, "two_phase": final_two, "adjusted": final_adj})
        np.save(ROOT / ".cache/final_dots_e3.npy", field)
        print(f"final adjusted duplicate={final_adj['duplicate_adjusted']}", flush=True)

    scores, diffs = summary["scores"], summary["paired_differences"]
    gates_detail = {
        "canaries_pass": not any(c["suspected_leakage"] for c in canaries.values()),
        "beats_random_ci": bool(diffs["random_dotted"]["ci95"][0] > 0),
        "beats_controls_point": bool(all(scores["scarp_dotted"]["dti"] > scores[n]["dti"]
                                         for n in ("slope19_dotted", "joint_ctrl_dotted"))),
        "surface_unique_adjusted": not surf_adj["duplicate_adjusted"],
        "final_unique_adjusted": bool(final_adj and not final_adj["duplicate_adjusted"]),
        "final_budget_reached": bool(n_final == sel_bud),
    }
    promote = all(gates_detail.values())
    print(f"gates: {gates_detail} promote={promote}", flush=True)

    sub_name = f"gems70e3-scarpcurv-{sel_bud // 1000}k-ex{sel_excl}-20261020-zeros"
    note = (f"E3 DEM scarp curvature+coherence only (E2 gates falsified); "
            f"dotted {n_final} excl>{sel_excl}px sep2.8; holdout-validated")
    assert len(note) <= 140 and len(sub_name) <= 140
    receipt, raster_sha = None, None
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
                                   metadata={"run": "E3", "holdout_evaluator": evaluate_holdout.VERSION,
                                             "selected_budget": sel_bud, "selected_exclusion_px": sel_excl})
        raster_sha = receipt["sha256"]
        validator_out = receipt["validator"]
        dump(E / "validator_e3.json", receipt)

    def worst(rows_key, two):
        return two["literal_reading"][rows_key] if two else None

    card = {
        "hypothesis": "DEM scarp curvature alone (slope x profile-curvature x tensor coherence) localises unmapped fault scarps",
        "mechanism": "Strike-coherent curvature steps in 100m detrended elevation; rank-ordered 2.8px dotted emission off-catalogue; E2 strain/cover gates falsified and removed",
        "non_fault_mimic": "Lake-shoreline or fluvial terrace riser; road cut",
        "hypothesis_status": "Provisional lane in docs/hypotheses-e3.md; E2 negative archived as falsification of gated variant",
        "verdict": "promote" if promote else "negative",
        "stop_reason": None if promote else "promotion gates failed (see gates); experiment budget exhausted",
        "gates": gates_detail,
        "holdout_dti": {**scores["scarp_dotted"],
                        "stage": "dotted emission rule on untouched seed-40 hide-and-recover folds",
                        "selected_budget": sel_bud, "selected_exclusion_px": sel_excl,
                        "random_control_dti": scores["random_dotted"]["dti"],
                        "paired_delta_vs_random": diffs["random_dotted"],
                        "transfer_caveat": "Catalogue-recovery surrogate; H33 live champion scores 0.0043 on E2 folds - holdout falsifies weak rankings but does not predict live DTI."},
        "correlation_overlap_vs_registry": {
            "stage": "surface + final dots, saturation-adjusted (see hypotheses-e3)",
            "rasters_checked": len(idx), "registry_complete": False,
            "registry_scope": "62 pinned 60GEMSDOE registry rasters + 17GEMSDOE dense witness; inherited inventory 862 - full scan is a selector step",
            "surface_worst_spearman": worst("worst_spearman_full_footprint", surf_two),
            "final_worst_spearman": worst("worst_spearman_full_footprint", final_two),
            "final_worst_forward_nonsaturating": (final_adj["worst_forward_overlap_nonsaturating"] if final_adj else None),
            "final_worst_forward_nonsaturating_submission": (final_adj["worst_forward_overlap_nonsaturating_submission"] if final_adj else None),
            "final_literal_worst_overlap": worst("worst_forward_overlap", final_two),
            "saturating_fields": (final_adj["saturating_fields"] if final_adj else None),
            "duplicate_adjusted": (final_adj["duplicate_adjusted"] if final_adj else None),
            "duplicate_literal": (final_two["literal_reading"]["duplicate"] if final_two else None),
        },
        "raster_sha256": raster_sha,
        "raster_sha256_reason": None if raster_sha else "No TIFF written: promotion gates failed.",
        "surface_decoded_float32_sha256": hashlib.sha256(np.ascontiguousarray(surface).tobytes()).hexdigest(),
        "validator_output": validator_out,
        "submission_name": sub_name if promote else f"{sub_name}-NOT-RELEASED",
        "submission_note": (note if promote else
                            "E3 scarp-curvature dotted candidate; NEGATIVE gates; DO NOT SUBMIT.")[:140],
        "download_and_submit_ok": False,
        "download_candidate_ok": bool(promote),
        "slot_authorized": False,
        "slot_note": "Separate selector step: full-registry scan + weekly-cap check on official submission page. Literal uniqueness gate still fires on saturating covering fields (disclosed).",
        "weekly_slots_used": 0, "experiment_count": 3,
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "organizer_confirmed_score": None, "n_final_dots": n_final,
        "evaluator_implementation_sha256": evaluate_holdout.implementation_hashes(),
        "method_source_sha256": {p: sha(ROOT / p) for p in
                                 ["src/gems70/method_e2.py", "scripts/run_experiment_e3.py"]},
    }
    dump(E / "run_card_e3.json", card)
    print(json.dumps(card, indent=2), flush=True)


if __name__ == "__main__":
    main()
