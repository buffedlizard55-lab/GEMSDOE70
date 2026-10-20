#!/usr/bin/env python3
"""P5: LOQO supervised within-halo analytic-signal ranking (one frozen experiment).

Source of truth: docs/preregistration-p5.md. Uses the pinned shared holdout,
evaluator, uniqueness measurement and writer. The user's *literal* forward-dot
rule blocks binary placement on the full feature-valid interior; a continuous
research TIFF, if written, is not a promoted submission. No weekly slot used.
"""
from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor"), str(ROOT / "scripts")]

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness, submission_writer
from gems57.grid import load_grid
from gems70 import phase5
from restore_data import DATA, PINS, sha
from run_experiment_v4 import intensity as p4_intensity, stratified_dots as p4_dots, cropped
from audit_literal_blocker import audit as audit_blocker, WITNESS, WITNESS_SHA

E = ROOT / "evidence" / "p5"
REG = Path("/tmp/60GEMSDOE/registry/rasters")
SGMC = Path("/tmp/60GEMSDOE/data/external/sgmc_faults_100m.tif")
SGMC_SHA = "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c"
H33 = Path("/tmp/60GEMSDOE/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
H33_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
P4 = ROOT / "docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif"
P4_SHA = "0fd1ad9ef58c9bbe0ed1781d36a31f76424db11930502623153dd69581ab35e7"
NAME = "gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT"
NOTE = ("P5 magnetic width and cover, SGMC LOQO proxy; continuous review map. "
        "Literal dot overlap blocks promotion; DO NOT SUBMIT")
assert len(NOTE) <= 140
SEED = 70501
MAX_SECONDS = 7200


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False, default=float) + "\n")
    tmp.replace(path)


def as_record(path: Path, *, source=None):
    # records_from_index reads sources[0] as the human-facing submission ID.
    # Always put the *filename* first; a repository URL is provenance, not an ID.
    links = [path.name]
    if source:
        links.append(source.rstrip("/") + "/" + path.name)
    return dict(repo_first=path.name.split("__")[0], submission=path.name,
                sources=links, cache_file=str(path), sha256=sha(path))


def canaries(raw, features, dist, folds, valid, seed=SEED):
    """Feature-alone AUC on exactly the shared masked catalogue holdout domain."""
    truth = np.zeros(valid.shape, bool)
    active = np.zeros(valid.shape, bool)
    for fold in folds:
        truth |= valid & fold["truth"]
        active |= valid & fold["region"] & ~fold["masked_known"]
    pos = np.flatnonzero(truth)
    neg_all = np.flatnonzero(active & ~truth)
    neg = np.random.default_rng(seed).choice(neg_all, min(len(neg_all), 200000), replace=False)
    ids = np.r_[pos, neg]
    labels = np.r_[np.ones(len(pos), dtype=np.int8), np.zeros(len(neg), dtype=np.int8)]
    out = {}
    for k, a in {**{f"raw_{k}": a for k, a in raw.items()},
                 **features, "visible_distance_clipped": np.minimum(dist, 32.0)}.items():
        values = a.ravel()[ids]
        if not np.isfinite(values).all():
            raise ValueError("nonfinite canary feature: " + k)
        auc = float(roc_auc_score(labels, values))
        out[k] = dict(evidence_class="LEAKAGE-CANARY", auc=auc,
                      inverse_auc=1 - auc, suspected_leakage=max(auc, 1 - auc) > .90,
                      withheld_positive_pixels=len(pos), negative_sample_pixels=len(neg),
                      fold_split="buffered-whole-components-loqo-v2 (seed 20)")
    return out


def fitted_model(features, dist, allowed, train_region, truth, fold_index):
    """SGMC is a response; *never* enters design(). Purge quadrant boundaries."""
    train = allowed & train_region
    pos = np.flatnonzero(train & truth)
    neg = np.flatnonzero(train & ~truth)
    rng = np.random.default_rng(SEED + fold_index)
    if len(pos) < 100 or len(neg) < 500:
        raise ValueError("insufficient training labels in safe quadrant domain")
    if len(pos) > 25000:
        pos = rng.choice(pos, 25000, replace=False)
    neg = rng.choice(neg, min(len(neg), 5 * len(pos)), replace=False)
    ids = np.r_[pos, neg]
    y = np.r_[np.ones(len(pos), np.int8), np.zeros(len(neg), np.int8)]
    order = rng.permutation(len(ids))
    model = HistGradientBoostingClassifier(
        max_iter=80, max_leaf_nodes=15, min_samples_leaf=100,
        learning_rate=.06, l2_regularization=2., max_bins=64, random_state=SEED)
    model.fit(phase5.design(features, dist, ids[order]), y[order])
    return model, dict(positives_sampled=len(pos), negatives_sampled=len(neg),
                       fold_index=fold_index, seed=SEED + fold_index,
                       train_region_pixels=int(train_region.sum()))


def predict_rank(model, features, dist, region):
    ids = np.flatnonzero(region)
    out = np.zeros(region.shape, np.float32)
    for chunk in np.array_split(ids, max(1, int(np.ceil(len(ids) / 300000)))):
        out.ravel()[chunk] = model.predict_proba(phase5.design(features, dist, chunk))[:, 1]
    return phase5.rank_surface(out, region)


def feature_stack(grid):
    raw = {}
    fp = grid.footprint
    with rasterio.open(DATA / "training_features.tif") as src:
        if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform) or src.count != 19:
            raise ValueError("feature grid/count does not match sample")
        desc = [src.descriptions[i - 1] for i in phase5.BANDS.values()]
        for name, band in phase5.BANDS.items():
            if not src.descriptions[band - 1].startswith(name + " -"):
                raise ValueError(f"band {band} is not {name}: {src.descriptions[band - 1]}")
            raw[name] = src.read(band).astype(np.float32)
    valid0 = phase5.feature_valid(raw, fp)
    valid = ndi.binary_erosion(valid0, iterations=12)
    if not valid.any():
        raise ValueError("no joint-valid interior")
    fields = phase5.physics(raw, valid0)
    return raw, fields, valid, desc


def registry_surface_scan(surface, grid):
    records = []
    for p in sorted(REG.glob("*.tif")):
        with rasterio.open(p) as ds:
            if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != (grid.shape, grid.crs, grid.transform):
                continue
        records.append(as_record(p, source="https://github.com/buffedlizard55-lab/60GEMSDOE/tree/b99591eede63c6d45c8a896255b8cd34824fa00b/registry/rasters"))
    count_archived = len(records)
    # Refresh against the *current* local publication inventory, not the
    # four artifacts that happened to exist when this lane started. The P5
    # file (if already published) is excluded because it is the candidate.
    inventory = json.loads((ROOT / "registry/published_artifacts.json").read_text())
    for row in inventory["artifacts"]:
        if not row["path"].lower().endswith((".tif", ".tiff")) or row["path"].endswith(NAME + ".tif"):
            continue
        p = ROOT / row["path"]
        if sha(p) != row["sha256"]:
            raise ValueError("locally inventoried raster changed: " + row["path"])
        records.append(as_record(p))
    if count_archived < 60:
        raise ValueError(f"incomplete indexed 60GEMSDOE registry: {count_archived} raster(s)")
    idx = dict(complete_accessible_scan=True, rasters=records, errors=[])
    res = uniqueness.compare_array_to_registry(surface, idx, grid.footprint,
                                                expected_grid=(grid.shape, grid.crs, grid.transform))
    if res["missing_or_invalid"] or res["registry_rasters_checked"] != len(records):
        raise ValueError("incomplete / invalid raster uniqueness comparison")
    # The shared checker is intentionally *not* a clearance for a continuous
    # field (no binary 1.0 cells); report rho and positive-support overlap too.
    with rasterio.open(REG / WITNESS) as ds:
        lattice = uniqueness._dots(ds.read(1))
    positive = surface > 0
    near = uniqueness._near(lattice, radius_px=3.0)
    res["continuous_positive_pixels"] = int(positive.sum())
    res["binary_one_dots"] = int(uniqueness._dots(surface).sum())
    res["forward_overlap_3px_if_positive_cells_count_as_dots"] = (
        float(near[positive].mean()) if positive.any() else None)
    res["literal_positive_support_duplicate"] = bool(positive.any() and near[positive].mean() > .70)
    res["scope_note"] = (f"{count_archived} archived 60GEMSDOE rasters plus "
                         f"{len(records) - count_archived} locally inventoried prior TIFFs; "
                         "external/unindexed/private files not enumerated. Binary-dot checker reports "
                         "zero dots for this continuous field; positive-support overlap is independent.")
    return res


def main():
    start = time.monotonic()
    E.mkdir(parents=True, exist_ok=True)
    prereg_sha = sha(ROOT / "docs/preregistration-p5.md")
    manifest = E / "manifest.json"
    if manifest.is_file() and json.loads(manifest.read_text()).get("preregistration_sha256") != prereg_sha:
        raise RuntimeError("preregistration changed after this experiment began")
    if not manifest.is_file():
        dump(manifest, {"evidence_class": "EXPERIMENT-FROZEN",
                        "preregistration_sha256": prereg_sha, "experiments_attempted": 1,
                        "max_experiments": 3, "max_seconds": MAX_SECONDS,
                        "fixed_source_sha256": {"src/gems70/phase5.py": sha(ROOT / "src/gems70/phase5.py")}})
    if sha(SGMC) != SGMC_SHA or sha(H33) != H33_SHA or sha(P4) != P4_SHA:
        raise ValueError("SGMC/H33/P4 comparator SHA-256 mismatch")
    for name, expected in PINS.items():
        if sha(DATA / name) != expected:
            raise ValueError("restored input pin mismatch: " + name)
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    literal = audit_blocker(REG / WITNESS, DATA / "training_features.tif",
                            ROOT / "data/bridge/sample_submission.tif")
    dump(E / "literal_blocker.json", literal)
    if not literal["literal_stop_for_any_dot_field_in_valid"]:
        raise ValueError("unexpected literal-dot gate change; cannot use preregistered plan")
    print("Literal dot-placement stop confirmed; continuing continuous-surface holdout only.", flush=True)
    raw, features, valid, desc = feature_stack(grid)
    if int(valid.sum()) != literal["feature_valid_pixels_after_12px_erosion"]:
        raise ValueError("feature domain differs from the independently audited witness domain")
    folds, quad = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    visible = folds[0]["visible"]
    if any(not np.array_equal(f["visible"], visible) for f in folds):
        raise ValueError("folds disagree on globally visible catalogue")
    distance = phase5.visible_distance(visible)
    incident = canaries(raw, features, distance, folds, valid)
    dump(E / "canaries.json", incident)
    if any(row["suspected_leakage"] for row in incident.values()):
        dump(E / "stop.json", {"verdict": "negative", "reason": "LEAKAGE CANARY",
                               "preregistration_sha256": prereg_sha, "canaries": incident})
        raise RuntimeError("LEAKAGE CANARY STOP: feature-alone AUC >0.90 or inverse >0.90")
    dump(E / "feature_receipt.json", dict(
        descriptions=desc, features=list(features) + ["visible_distance_clipped"],
        joint_valid_pixels=int(valid.sum()),
        evaluation_split_receipts=[f["receipt"] for f in folds],
        evaluator_version=evaluate_holdout.VERSION,
        caveat="SGMC owner mirror is only a proxy response; labels are not organizer truth."))
    raw.clear(); del raw
    gc.collect()

    with rasterio.open(SGMC) as s:
        if (s.shape, s.crs, s.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError("SGMC proxy grid mismatch")
        sgmc = (s.read(1) > 0) & fp
    with rasterio.open(P4) as s: p4 = s.read(1).astype(np.float32)
    with rasterio.open(H33) as s: h33 = s.read(1).astype(np.float32)
    if not np.isfinite(p4).all() or not np.isfinite(h33).all():
        raise ValueError("reference submission contains nonfinite pixels")
    qregions = [ndi.binary_erosion(quad == k, iterations=12) & valid for k in range(4)]
    allowed = phase5.domain(valid, visible, distance)
    da = ndi.distance_transform_edt(~cat)
    proxy_prime = sgmc & ~cat & (da >= 3.0) & fp
    print("proxy (unscored full mask)", int(proxy_prime.sum()), flush=True)
    training_labels = sgmc & allowed  # full catalogue never used for A catalogue features
    del da
    terms_a = {k: None for k in ("candidate_continuous", "visible_only_p4")}
    terms_b = {k: None for k in ("candidate_continuous", "p4_frozen", "h33_frozen")}
    fold_rows_a = {k: [] for k in terms_a}
    fold_rows_b = {k: [] for k in terms_b}
    oof = np.zeros(grid.shape, np.float32)
    training_receipts = []
    # Concurrent main moved Phase-4's old P4 fold receipt to a new canonical
    # analytic-halo lane. The exact original P4 fold bytes are frozen here;
    # production P4 itself is regenerated from *visible* faults before scoring.
    baseline_path = E / "p4_visible_baseline_folds.json"
    if sha(baseline_path) != "e020d9f2ca79416a5c943bc9938ba46080008fe5bba252a9e120697c11a8b401":
        raise ValueError("P4 visible-only baseline fold receipt changed")
    prior_a = json.loads(baseline_path.read_text())
    for k in range(4):
        if time.monotonic() - start > MAX_SECONDS:
            raise TimeoutError("two-hour experiment budget exceeded")
        train_regions = np.zeros(grid.shape, bool)
        for j in range(4):
            if j != k: train_regions |= qregions[j]
        model, receipt = fitted_model(features, distance, allowed, train_regions,
                                      training_labels, k)
        training_receipts.append(receipt)
        test = qregions[k] & allowed
        field = predict_rank(model, features, distance, test)
        oof += field
        fold_a = folds[k]
        r, t = cropped(fold_a, field, valid)
        terms_a["candidate_continuous"] = t if terms_a["candidate_continuous"] is None else terms_a["candidate_continuous"] + t
        fold_rows_a["candidate_continuous"].append(r)
        # P4 rebuilt from *globally visible* catalogue, not full-catalogue dots.
        p4dots, n = p4_dots(p4_intensity(visible, valid))
        if n != 37654:
            raise ValueError(f"P4 comparator placed only {n} dots")
        p4_a = p4dots.astype(np.float32)
        del p4dots
        r, t = cropped(fold_a, p4_a, valid)
        for term in ("tp", "fp", "fn", "n_truth"):
            if not np.isclose(r[term], prior_a["candidate"][k][term], rtol=1e-6, atol=1e-5):
                raise ValueError(f"regenerated P4 comparator differs at A fold {k}, {term}")
        terms_a["visible_only_p4"] = t if terms_a["visible_only_p4"] is None else terms_a["visible_only_p4"] + t
        fold_rows_a["visible_only_p4"].append(r)
        del p4_a
        # B' is a separate proxy, with the full given catalogue masked exactly;
        # the evaluated candidate is LOQO cross-fitted (never trained on quadrant k).
        fold_b = dict(region=fold_a["region"], truth=proxy_prime & fold_a["region"],
                      visible=cat, masked_known=cat)
        for label, pred in (("candidate_continuous", field), ("p4_frozen", p4),
                            ("h33_frozen", h33)):
            r, t = cropped(fold_b, pred, valid)
            terms_b[label] = t if terms_b[label] is None else terms_b[label] + t
            fold_rows_b[label].append(r)
        print(f"LOQO quadrant {k} A/B' completed", flush=True)
        del field, model
        gc.collect()
    summary_a = evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=SEED,
                                                candidate="candidate_continuous")
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=SEED,
                                                candidate="candidate_continuous")
    summary_a["instrument"] = "A: shared hide-and-recover whole catalogue segments (proxy for known faults)"
    summary_b["instrument"] = "B': LOQO SGMC off-catalogue proxy at least 3 px from mapped catalogue"
    summary_a["comparison_caveat"] = "P4 rebuilt from globally visible context with same split, grid and footprint"
    summary_b["comparison_caveat"] = "The candidate is cross-fitted; frozen P4/H33 did not train on this SGMC proxy; SGMC is not hidden truth"
    dump(E / "instrument_a.json", summary_a)
    dump(E / "instrument_b_prime.json", summary_b)
    dump(E / "folds_a.json", fold_rows_a)
    dump(E / "folds_b_prime.json", fold_rows_b)
    dump(E / "training_receipts.json", training_receipts)
    # No production model may be interpreted as scored on this same SGMC truth.
    dist_full = phase5.visible_distance(cat)
    final_domain = phase5.domain(valid, cat, dist_full)
    model, production_training = fitted_model(features, dist_full, final_domain,
                                             np.logical_or.reduce(qregions), sgmc & final_domain, 4)
    production = predict_rank(model, features, dist_full, final_domain)
    del model, dist_full, features
    gc.collect()
    if np.any(production[cat]) or np.any(production[~fp]):
        raise ValueError("production nonzero on mapped faults or outside footprint")
    # Surface uniqueness (before writer; there is no dot placement). The
    # inherited dot tool's 'unique=false' for no exact 1.0 cells is disclosed.
    scan = registry_surface_scan(production, grid)
    dump(E / "surface_registry.json", scan)
    rho = scan["worst_spearman_full_footprint"]
    if rho is None or rho > .90 or scan["missing_or_invalid"]:
        dump(E / "stop.json", {"verdict": "negative", "reason": "SURFACE REGISTRY STOP",
                               "worst_rho": rho, "n_errors": scan["missing_or_invalid"]})
        raise RuntimeError("SURFACE UNIQUENESS STOP: missing registry or rho > 0.90")
    if int(uniqueness._dots(production).sum()) != 0:
        raise RuntimeError("Unexpected binary dots in continuous review surface: stop")
    # Strict positive-cell reading is >.70; therefore *no* dot field is written.
    if not scan["literal_positive_support_duplicate"]:
        raise ValueError("positive-support reading unexpectedly differs from preregistered blocker")
    out = ROOT / "docs/downloads" / f"{NAME}.tif"
    receipt = submission_writer.write_submission(
        out, production, DATA / "sample_submission.tif", fp,
        note=NOTE, name=NAME, catalogue=cat,
        metadata={"class": "format-validated continuous research TIFF; NOT a cleared dot submission",
                  "literal_forward_dot_stop": True, "evidence": "evidence/p5/run_card.json"})
    val = receipt["validator"]
    paired_a = summary_a["paired_differences"]["visible_only_p4"]
    paired_b = summary_b["paired_differences"]["h33_frozen"]
    gates = dict(
        a_beats_visible_p4_significant=paired_a["delta"] > 0 and paired_a["ci95"][0] > 0,
        b_prime_beats_h33_significant=paired_b["delta"] > 0 and paired_b["ci95"][0] > 0,
        literal_dot_overlap_gate_passed=False,
        no_canary_alarm=True,
        no_surface_rho_alarm=rho <= .90,
        local_format_validated=val["all_checks_passed"],
    )
    card = dict(
        hypothesis="P5 cover-conditioned analytic-signal width ranking, SGMC LOQO cross-fit",
        mechanism="Gaussian-scale magnetic analytic-signal width x gravity gradient x basement cover, trained on SGMC-only proxy faults, restricted 3..32 px off visible catalogue",
        non_fault_mimic="buried volcanic dike or remanence boundary; acquisition-flight leveling seam",
        evidence_class="HOLDOUT-DTI on A, proxy HOLDOUT-DTI on B'; no organizer-confirmed submission receipt",
        hypothesis_source="docs/preregistration-p5.md", preregistration_sha256=prereg_sha,
        holdout_dti={"instrument_a": summary_a["scores"]["candidate_continuous"],
                     "paired_vs_visible_p4": paired_a,
                     "instrument_b_prime_proxy": summary_b["scores"]["candidate_continuous"],
                     "paired_vs_h33": paired_b},
        comparators={"a_visible_only_p4": summary_a["scores"]["visible_only_p4"],
                     "b_prime_h33_frozen": summary_b["scores"]["h33_frozen"],
                     "b_prime_p4_frozen": summary_b["scores"]["p4_frozen"]},
        correlation_overlap_vs_registry={
            "stage": "final continuous production surface; no dot placement by preregistered literal stop",
            "rasters_checked": scan["registry_rasters_checked"],
            "inventory_scope": scan["scope_note"],
            "worst_spearman_full_footprint": rho,
            "worst_rho_submission": scan["worst_rho_submission"],
            "binary_one_dots": scan["binary_one_dots"],
            "forward_overlap_positive_support_lattice": scan["forward_overlap_3px_if_positive_cells_count_as_dots"],
            "literal_3px_forward_gate_passes": False,
            "literal_witness_file": WITNESS, "literal_witness_sha256": WITNESS_SHA,
            "positive_support_pixels": scan["continuous_positive_pixels"],
            "shared_tool_dot_uniqueness": scan["unique"],
            "shared_tool_note": "Shared _dots uses exact-one binary definition, so zero dot overlap here is NOT a forward-overlap clearance.",
        },
        gate_results=gates,
        raster_sha256=receipt["sha256"],
        validator_output=val,
        submission_name=NAME, submission_note=NOTE, note_chars=len(NOTE),
        raster_path="docs/downloads/" + out.name,
        download_ok=bool(val["all_checks_passed"]),
        submit_recommended=False, download_and_submit_ok=False,
        verdict="negative",
        verdict_reason=("The literal forward 3px dot-overlap rule has a hash-verified 100%-interior-cover lattice: "
                        "any dot placement inside the feature-valid domain is a duplicate. This continuous map is "
                        "for review, not a promoted competition submission; holdout gates also require both CIs >0."),
        weekly_slots_used=0, organizer_confirmed_score=None,
        experiment_count=1, elapsed_seconds=round(time.monotonic() - start, 2),
        max_elapsed_seconds=MAX_SECONDS,
        canaries_path="evidence/p5/canaries.json",
        blocker_path="evidence/p5/literal_blocker.json",
        evaluator_implementation_sha256=evaluate_holdout.implementation_hashes(),
        method_source_sha256={p: sha(ROOT / p) for p in
                              ("src/gems70/phase5.py", "scripts/run_experiment_p5_cover.py")},
        production_train_receipt=production_training,
        limitations=["The SGMC map is not the hidden expert truth and may redraw the same faults.",
                     "Training data are pinned owner mirrors, not independently organizer-authenticated.",
                     "No calibrated probabilities, private-test score or organizer acceptance is asserted.",
                     "Positive-support overlap (not exact-one dots) against the lattice is above the user limit; never upload as a cleared dot submission."],
    )
    dump(E / "run_card.json", card)
    print(json.dumps({k: card[k] for k in ("verdict", "raster_sha256", "raster_path",
                                      "holdout_dti", "correlation_overlap_vs_registry", "gate_results")},
                     indent=2), flush=True)


if __name__ == "__main__":
    main()
