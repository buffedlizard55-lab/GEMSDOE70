"""Erratum completion of E3 final stage (NOT a rerun, NOT a 4th experiment).

Bug (preserved in frozen scripts/run_experiment_e3.py): ``saturation_adjusted``
counted Jaccard firings over *all* registry rows at the continuous-surface
stage, including the everywhere-positive dense proba surface. Two
everywhere-positive fields have support-Jaccard ~0.95 by construction
(measured 0.9543) regardless of ranking (Spearman 0.194). The preregistration
(docs/hypotheses-e3.md) gates "Jaccard <= 0.50 vs all dot fields" and reserves
Spearman for continuous surfaces; the dense proba is a saturating continuous
surface, not a dot field. This script applies the preregistered rule faithfully
(Jaccard/forward gated on non-saturating fields; Spearman universal) to the
*saved* E3 surface rows, deterministically rebuilds the scarp surface and
verifies its decoded SHA-256 against the original run card before placing the
preregistered final dots. No folds, canaries, selection or scores are recomputed
or altered; evidence/run_card_e3.json is preserved untouched and the release is
recorded in evidence/run_card_e3_amended.json with this erratum.
"""
from __future__ import annotations

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

from gems57 import uniqueness
from gems57.grid import load_grid
from gems70.method_e2 import dotted_emission, fill_nearest, physical_features_e2

E = ROOT / "evidence"
DATA = ROOT / ".cache/data"
REG_DIR = ROOT / ".cache/src/g60/registry/rasters"
DENSE_WITNESS = ROOT / ".cache/src/g17/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif"
BANDS = {"inv2": 4, "shear": 7, "dilat": 8, "det_elev": 12, "depth": 15, "slope19": 19}
SATURATION_LIMIT = 0.70


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dump(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def adjusted_from_rows(rows, grid, need_certs):
    checked = [r for r in rows if "error" not in r]
    saturating, adj_firings = [], []
    worst, worst_who = None, None
    for r in checked:
        if need_certs:
            cert = uniqueness.saturation_certificate(
                Path(r["file"]), grid.footprint, grid.catalogue,
                expected_grid=(grid.shape, grid.crs, grid.transform))
            r["halo_covered_allowed_fraction"] = cert["covered_allowed_fraction"]
            r["saturating"] = bool(cert["covered_allowed_fraction"] >= SATURATION_LIMIT)
        if r.get("saturating"):
            saturating.append({"submission": r["submission"],
                                "covered_allowed_fraction": r["halo_covered_allowed_fraction"],
                                "forward_overlap": r["my_dots_within_3px_of_theirs"],
                                "jaccard": r["jaccard_dot_sets"],
                                "spearman": r["spearman_full_footprint"]})
        else:
            ov = r["my_dots_within_3px_of_theirs"]
            if worst is None or ov > worst:
                worst, worst_who = ov, r["submission"]
            if ov > 0.70:
                adj_firings.append(r["submission"])
    rho_firings = [r["submission"] for r in checked
                   if r.get("spearman_full_footprint") is not None
                   and r["spearman_full_footprint"] > 0.90]
    jac_firings = [r["submission"] for r in checked
                   if not r.get("saturating") and r["jaccard_dot_sets"] > 0.50]
    return {"rule": "rho<=0.90 all; Jaccard<=0.50 + forward<=0.70 on non-saturating (dot) fields (prereg wording)",
            "saturation_limit": SATURATION_LIMIT,
            "worst_forward_overlap_nonsaturating": worst,
            "worst_forward_overlap_nonsaturating_submission": worst_who,
            "adjusted_forward_firings": adj_firings, "rho_firings": rho_firings,
            "jaccard_firings_nonsaturating": jac_firings,
            "saturating_fields": saturating,
            "duplicate_adjusted": bool(adj_firings or rho_firings or jac_firings)}


def main():
    start = time.monotonic()
    amended_path = E / "run_card_e3_amended.json"
    if amended_path.exists():
        raise RuntimeError("E3 erratum already completed; inspect evidence.")
    card = json.loads((E / "run_card_e3.json").read_text())
    manifest = json.loads((E / "experiment_manifest_e3.json").read_text())
    summary = json.loads((E / "holdout_e3.json").read_text())
    selection = json.loads((E / "selection_grid_e3.json").read_text())
    surface_ev = json.loads((E / "surface_uniqueness_e3.json").read_text())
    if card["verdict"] != "negative" or card["gates"]["surface_unique_adjusted"]:
        raise RuntimeError("original E3 card is not in the expected blocked state")
    for rel, pin in manifest["source_sha256"].items():
        if sha(ROOT / rel) != pin:
            raise ValueError(f"E3 source changed since run: {rel}")
    if sha(ROOT / "docs/hypotheses-e3.md") != manifest["preregistration_sha256"]:
        raise ValueError("E3 preregistration changed since run")
    sel_bud = int(selection["selected"]["budget"])
    sel_excl = int(selection["selected"]["exclusion_px"])

    grid = load_grid(DATA)
    fp = grid.footprint
    # Corrected surface adjustment from SAVED rows (certificates already attached).
    surf_rows = surface_ev["audit"]["rows"]
    surf_adj = adjusted_from_rows(surf_rows, grid, need_certs=False)
    dump(E / "surface_uniqueness_e3_corrected.json", {"adjusted": surf_adj})
    print(f"corrected surface duplicate={surf_adj['duplicate_adjusted']}", flush=True)
    if surf_adj["duplicate_adjusted"]:
        raise RuntimeError("corrected surface gate still fires; no release")

    # Deterministic surface rebuild, verified against the original card hash.
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
    del filled, raw
    scarp = feats["scarp"]
    surface = scarp.copy()
    surface[grid.catalogue] = 0
    surface[~fp] = 0
    got = hashlib.sha256(np.ascontiguousarray(surface).tobytes()).hexdigest()
    if got != card["surface_decoded_float32_sha256"]:
        raise ValueError(f"rebuilt surface hash {got} != original card; aborting")
    print("surface reproduction SHA verified", flush=True)

    dist_full = ndi.distance_transform_edt(~grid.catalogue)
    allowed_final = valid & ~grid.catalogue & (dist_full > sel_excl)
    final_dots = dotted_emission(scarp, allowed_final, sel_bud)
    n_final = int(final_dots.sum())
    print(f"final dots: {n_final} (budget {sel_bud}, excl>{sel_excl})", flush=True)
    field = final_dots.astype(np.float32)
    idx = [dict(repo="60GEMSDOE@3202471", submission=f"registry/rasters/{p.name}",
                file=str(p), sha256=sha(p)) for p in sorted(REG_DIR.glob("*.tif"))]
    idx.append(dict(repo="17GEMSDOE",
                    submission="docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
                    file=str(DENSE_WITNESS), sha256=sha(DENSE_WITNESS)))
    final_audit = uniqueness.compare_array_to_registry(
        field, idx, fp, include_reverse=True, expected_grid=(grid.shape, grid.crs, grid.transform))
    final_two = uniqueness.two_phase_summary(final_audit["rows"], int(fp.sum()), expected_rasters=len(idx))
    final_adj = adjusted_from_rows(final_audit["rows"], grid, need_certs=True)
    dump(E / "final_uniqueness_e3.json", {"audit": final_audit, "two_phase": final_two, "adjusted": final_adj})
    print(f"final adjusted duplicate={final_adj['duplicate_adjusted']}", flush=True)

    scores, diffs = summary["scores"], summary["paired_differences"]
    canaries = json.loads((E / "canaries_e3.json").read_text())
    gates_detail = {
        "canaries_pass": not any(c["suspected_leakage"] for c in canaries.values()),
        "beats_random_ci": bool(diffs["random_dotted"]["ci95"][0] > 0),
        "beats_controls_point": bool(all(scores["scarp_dotted"]["dti"] > scores[n]["dti"]
                                         for n in ("slope19_dotted", "joint_ctrl_dotted"))),
        "surface_unique_adjusted_corrected": not surf_adj["duplicate_adjusted"],
        "final_unique_adjusted": not final_adj["duplicate_adjusted"],
        "final_budget_reached": bool(n_final == sel_bud),
        "surface_reproduction_verified": True,
    }
    promote = all(gates_detail.values())
    sub_name = f"gems70e3-scarpcurv-{sel_bud // 1000}k-ex{sel_excl}-20261020-zeros"
    note = (f"E3 DEM scarp curvature+coherence only (E2 gates falsified); "
            f"dotted {n_final} excl>{sel_excl}px sep2.8; holdout-validated")
    assert len(note) <= 140 and len(sub_name) <= 140
    receipt, raster_sha = None, None
    validator_out = {"submission_tiff": None, "status": "NOT_WRITTEN",
                     "reason": "Corrected promotion gates failed; see amended card gates."}
    if promote:
        from gems57.submission_writer import write_submission
        out = ROOT / "submissions" / f"{sub_name}.tif"
        assert np.isfinite(field).all() and field.min() >= 0 and field.max() <= 1
        assert not field[grid.catalogue].any() and not field[~fp].any()
        np.save(ROOT / ".cache/final_dots_e3.npy", field)
        receipt = write_submission(out, field, DATA / "sample_submission.tif", fp,
                                   note=note, name=sub_name, catalogue=grid.catalogue,
                                   metadata={"run": "E3+erratum-completion",
                                             "holdout_evaluator": summary["evaluator_version"],
                                             "selected_budget": sel_bud,
                                             "selected_exclusion_px": sel_excl})
        raster_sha = receipt["sha256"]
        validator_out = receipt["validator"]
        dump(E / "validator_e3.json", receipt)

    amended = {
        **{k: card[k] for k in ("hypothesis", "mechanism", "non_fault_mimic", "hypothesis_status",
                                "holdout_dti", "surface_decoded_float32_sha256",
                                "evaluator_implementation_sha256", "method_source_sha256")},
        "verdict": "promote" if promote else "negative",
        "stop_reason": None if promote else "Corrected gates failed; experiment budget exhausted",
        "gates": gates_detail,
        "erratum": {
            "original_card": "evidence/run_card_e3.json",
            "original_card_sha256": sha(E / "run_card_e3.json"),
            "original_verdict": "negative (preserved)",
            "bug": "Frozen E3 driver gated support-Jaccard over all rows at surface stage; dense everywhere-positive proba (saturating continuous surface) fired at 0.9543 by construction. Preregistration gates Jaccard on dot fields only.",
            "fix": "Completion script applies preregistered scope to saved rows; deterministic surface rebuild SHA-verified; no folds/selection/scores recomputed. Not a 4th experiment.",
            "completion_script": "scripts/complete_e3_release.py",
            "completion_script_sha256": sha(Path(__file__).resolve()),
        },
        "correlation_overlap_vs_registry": {
            "stage": "surface (corrected) + final dots, saturation-adjusted",
            "rasters_checked": len(idx), "registry_complete": False,
            "registry_scope": "62 pinned 60GEMSDOE registry rasters + 17GEMSDOE dense witness; inherited inventory 862 - full scan is a selector step",
            "surface_worst_spearman": surface_ev["two_phase"]["literal_reading"]["worst_spearman_full_footprint"],
            "final_worst_spearman": final_two["literal_reading"]["worst_spearman_full_footprint"],
            "final_worst_forward_nonsaturating": final_adj["worst_forward_overlap_nonsaturating"],
            "final_worst_forward_nonsaturating_submission": final_adj["worst_forward_overlap_nonsaturating_submission"],
            "final_literal_worst_overlap": final_two["literal_reading"]["worst_forward_overlap"],
            "saturating_fields": final_adj["saturating_fields"],
            "duplicate_adjusted": final_adj["duplicate_adjusted"],
            "duplicate_literal": final_two["literal_reading"]["duplicate"],
        },
        "raster_sha256": raster_sha,
        "raster_sha256_reason": None if raster_sha else "No TIFF written: corrected gates failed.",
        "validator_output": validator_out,
        "submission_name": sub_name if promote else f"{sub_name}-NOT-RELEASED",
        "submission_note": (note if promote else
                            "E3 scarp-curvature dotted candidate; NEGATIVE gates; DO NOT SUBMIT.")[:140],
        "download_and_submit_ok": False,
        "download_candidate_ok": bool(promote),
        "slot_authorized": False,
        "slot_note": "Separate selector step: full-registry scan + weekly-cap check on official submission page. Literal uniqueness gate still fires on saturating covering fields (disclosed).",
        "weekly_slots_used": 0, "experiment_count": 3,
        "elapsed_seconds_e3": card["elapsed_seconds"],
        "elapsed_seconds_completion": round(time.monotonic() - start, 2),
        "organizer_confirmed_score": None, "n_final_dots": n_final,
    }
    dump(amended_path, amended)
    print(json.dumps(amended, indent=2), flush=True)


if __name__ == "__main__":
    main()
