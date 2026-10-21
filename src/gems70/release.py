"""Fail-closed cryptographic & byte-level release verification gate for GEMSDOE70."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import rasterio


def digest(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_submission_bytes(root: Path, tif_rel: str, zip_rel: str, expected_tif_sha: str, expected_zip_sha: str) -> list[str]:
    """Independently re-open .tif and .zip bytes on disk and verify every competition invariant."""
    reasons: list[str] = []
    tif_path = root / tif_rel
    zip_path = root / zip_rel
    if not tif_path.is_file():
        return [f"Missing promoted GeoTIFF: {tif_rel}"]
    if not zip_path.is_file():
        return [f"Missing promoted ZIP archive: {zip_rel}"]
    if digest(tif_path) != expected_tif_sha:
        reasons.append("GeoTIFF SHA-256 mismatch against run_card.json.")
    if digest(zip_path) != expected_zip_sha:
        reasons.append("ZIP SHA-256 mismatch against run_card.json.")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if names != [tif_path.name]:
            reasons.append(f"ZIP must contain strictly one GeoTIFF named {tif_path.name}, found {names}.")
        else:
            if hashlib.sha256(zf.read(names[0])).hexdigest() != expected_tif_sha:
                reasons.append("GeoTIFF inside ZIP does not byte-match standalone GeoTIFF.")

    sample_path = root / "data/bridge/sample_submission.tif"
    faults_path = root / "data/bridge/existing_faults.tif"
    if not sample_path.is_file() or not faults_path.is_file():
        reasons.append("Missing pinned bridge reference rasters.")
        return reasons

    with rasterio.open(sample_path) as ref_ds, rasterio.open(faults_path) as cat_ds, rasterio.open(tif_path) as sub_ds:
        if sub_ds.count != 1:
            reasons.append(f"GeoTIFF band count {sub_ds.count} != 1.")
        if sub_ds.shape != ref_ds.shape:
            reasons.append(f"GeoTIFF shape {sub_ds.shape} != {ref_ds.shape}.")
        if sub_ds.crs != ref_ds.crs:
            reasons.append(f"GeoTIFF CRS {sub_ds.crs} != {ref_ds.crs}.")
        if sub_ds.transform != ref_ds.transform:
            reasons.append("GeoTIFF affine geotransform mismatch against sample_submission.tif.")
        arr = sub_ds.read(1)
        fp = np.isfinite(ref_ds.read(1))
        cat = cat_ds.read(1) > 0
        if not np.isfinite(arr).all():
            reasons.append("GeoTIFF contains non-finite (NaN/Inf) values.")
        if float(arr.min()) < 0.0 or float(arr.max()) > 1.0:
            reasons.append(f"GeoTIFF values [{arr.min()}, {arr.max()}] outside strict [0, 1] range.")
        if np.any(arr[~fp] != 0.0):
            reasons.append("GeoTIFF has non-zero values outside the study footprint.")
        if np.any(arr[cat] != 0.0):
            reasons.append("GeoTIFF has non-zero mass on mapped public catalogue faults.")
    return reasons


def release_status(root: str | Path, evidence_subdir: str = "evidence") -> dict:
    """Fail-closed cryptographic audit of all scientific, leakage, uniqueness, and GeoTIFF gates."""
    root = Path(root)
    ev = root / evidence_subdir
    reasons: list[str] = []
    try:
        card = json.loads((ev / "run_card.json").read_text())
        holdout = json.loads((ev / "holdout.json").read_text())
        canaries = json.loads((ev / "canaries.json").read_text())
        surf_audit = json.loads((ev / "surface_uniqueness.json").read_text())
        manifest = json.loads((ev / "experiment_manifest.json").read_text())

        if card.get("verdict") != "promote":
            reasons.append("Run verdict is not promote.")
        if card.get("organizer_confirmed_score") is not None:
            reasons.append("Unuploaded local candidate cannot claim an ORGANIZER-CONFIRMED score.")
        if int(card.get("weekly_slots_used", -1)) != 0:
            reasons.append("Unexpected weekly slot count.")
        if int(card.get("experiment_count", 99)) > 3:
            reasons.append("Experiment count exceeded budget limit of 3.")
        if len(card.get("submission_note", "")) > 140 or not card.get("submission_note"):
            reasons.append("Submission note missing or exceeds 140 characters.")

        # Pre-registration and source SHA-256 pins
        prereg_sha = manifest.get("preregistration_sha256")
        if not prereg_sha or prereg_sha != card.get("preregistration_sha256"):
            reasons.append("Pre-registration SHA-256 mismatch between manifest and run card.")
        elif digest(root / "docs/hypotheses.md") != prereg_sha:
            reasons.append("docs/hypotheses.md modified after pre-registration lock.")

        src_pins = card.get("method_source_sha256", {})
        if not src_pins:
            reasons.append("Missing method_source_sha256 pins.")
        for rel, pin in src_pins.items():
            if not (root / rel).is_file() or digest(root / rel) != pin:
                reasons.append(f"Source file changed since experiment: {rel}")

        # Leakage canaries (all features strictly <= 0.90 symmetric AUC)
        if isinstance(canaries, dict) and "seed70_primary" in canaries:
            all_rows = list(canaries["seed70_primary"]) + list(canaries["seed20_historical"])
            if not all_rows or any(
                r.get("leakage_suspect") is not False or max(float(r["auc"]), 1.0 - float(r["auc"])) > 0.90
                for r in all_rows
            ):
                reasons.append("Single-feature leakage canary failed (> 0.90 AUC).")
        else:
            reasons.append("Complete dual-split leakage canary table missing.")

        # Holdout dominance over controls on identical evaluator & split
        scores = holdout.get("scores", {})
        cand_dti = float(scores.get("candidate", {}).get("dti", -1.0))
        for ctrl in ("random_control", "g49_reimpl_control", "experiment1_h70_1", "experiment2_h70_2"):
            if ctrl not in scores or cand_dti <= float(scores[ctrl]["dti"]):
                reasons.append(f"Candidate did not beat control {ctrl} on primary holdout split.")

        # Dual-stage 931-raster registry uniqueness verification
        final_uq_path = ev / "final_uniqueness.json"
        rows_gz_path = ev / "full_931_registry_audit_rows.json.gz"
        if not final_uq_path.is_file() or not rows_gz_path.is_file():
            reasons.append("Missing complete 931-raster Stage-2 uniqueness audit.")
        else:
            final_uq = json.loads(final_uq_path.read_text())
            if surf_audit.get("registry_rasters_checked", 0) < 931 or abs(float(surf_audit["worst_spearman_full_footprint"])) > 0.90:
                reasons.append("Stage-1 pre-placement surface failed 931-raster Spearman <= 0.90 check.")
            if (
                final_uq.get("registry_rasters_checked", 0) < 931
                or not final_uq.get("byte_unique_among_checked")
                or not final_uq.get("pixel_unique_among_checked")
                or abs(float(final_uq["worst_spearman_full_footprint"])) > 0.90
            ):
                reasons.append("Stage-2 final dots failed byte/pixel/Spearman uniqueness check.")
            stage2_rows = json.loads(gzip.open(rows_gz_path, "rt").read())["stage2_final_dot_rows"]
            sparse_overlaps = [float(r["my_dots_within_3px_of_theirs"]) for r in stage2_rows if int(r["their_dots"]) <= 150_000]
            if len(sparse_overlaps) < 700 or max(sparse_overlaps) > 0.70:
                reasons.append("Stage-2 final dots exceeded 0.70 3-px overlap on sparse registry submissions.")

        # Byte-level verification of .tif and .zip deliverables
        paths = card.get("submission_paths", {})
        tif_rel = paths.get("primary_tif", "")
        zip_rel = paths.get("zip", "")
        reasons.extend(
            verify_submission_bytes(
                root,
                tif_rel,
                zip_rel,
                card.get("raster_sha256", ""),
                card.get("zip_sha256", ""),
            )
        )
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        reasons.append("Missing or invalid evidence: " + str(exc))

    ok = len(reasons) == 0
    return {
        "download_and_submit_ok": ok,
        "verdict": "promote" if ok else "negative",
        "reasons": reasons,
        "policy": (
            "All cryptographic, leakage-canary, holdout, 931-raster uniqueness, and [0, 1] GeoTIFF gates passed."
            if ok
            else "Fail-closed gate blocked publication: " + "; ".join(reasons)
        ),
    }


def assert_no_public_rasters(root: str | Path) -> None:
    """Enforce strictly that ONLY the exact cryptographically authorized TIFF/ZIP exist under docs/."""
    root = Path(root)
    docs = root / "docs"
    if not docs.exists():
        return
    status = release_status(root)
    found = sorted(
        p.relative_to(root).as_posix()
        for p in docs.rglob("*")
        if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}
    )
    if not status["download_and_submit_ok"]:
        if found:
            raise ValueError("Stopped or unverified run must not publish TIFF/ZIP artifacts: " + ", ".join(found))
        return
    card = json.loads((root / "evidence/run_card.json").read_text())
    allowed = sorted([
        card["submission_paths"]["primary_tif"],
        card["submission_paths"]["zip"],
    ])
    if found != allowed:
        raise ValueError(f"Unauthorized or mismatched public raster artifacts: found={found}, allowed={allowed}")
