"""E3 release contract (fresh run; E1 gate in release.py stays historical).

Fail-closed verification that the downloadable candidate TIFF is exactly the
hash-bound artifact of the amended E3 run card. ``download_candidate_ok``
means the file is format-valid, holdout-gated and uniqueness-checked within
the disclosed scope. It never authorizes a weekly slot: selector review
(full-registry scan + weekly-cap check) remains separate, so
``download_and_submit_ok``/``slot_authorized`` are always False here.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import zipfile

from .release import valid_canary


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _load(root, rel):
    return json.loads((Path(root) / rel).read_text())


def release_status_e3(root):
    root = Path(root)
    reasons, checks = [], {}
    card = None
    try:
        card = _load(root, "evidence/run_card_e3_amended.json")
        original = _load(root, "evidence/run_card_e3.json")
        manifest = _load(root, "evidence/experiment_manifest_e3.json")
        holdout = _load(root, "evidence/holdout_e3.json")
        canaries = _load(root, "evidence/canaries_e3.json")
        receipt = _load(root, "evidence/validator_e3.json")
        final_uniq = _load(root, "evidence/final_uniqueness_e3.json")
        surface_corr = _load(root, "evidence/surface_uniqueness_e3_corrected.json")

        checks["verdict_promote"] = card.get("verdict") == "promote"
        checks["gates_all_true"] = bool(card.get("gates")) and all(card["gates"].values())
        checks["candidate_flag"] = card.get("download_candidate_ok") is True
        checks["no_slots_used"] = card.get("weekly_slots_used") == 0 and card.get("experiment_count") == 3
        checks["original_preserved"] = (
            original.get("verdict") == "negative"
            and digest(root / "evidence/run_card_e3.json") == card["erratum"]["original_card_sha256"])
        checks["sources_pinned"] = all(
            digest(root / rel) == pin for rel, pin in manifest["source_sha256"].items())
        checks["prereg_pinned"] = (
            digest(root / "docs/hypotheses-e3.md") == manifest["preregistration_sha256"])
        checks["completion_pinned"] = (
            digest(root / "scripts/complete_e3_release.py")
            == card["erratum"]["completion_script_sha256"])
        checks["canaries_valid"] = (
            isinstance(canaries, dict) and bool(canaries)
            and all(valid_canary(c) for c in canaries.values()))
        h = card["holdout_dti"]
        s = holdout["scores"]["scarp_dotted"]
        checks["holdout_matches_card"] = (
            h["dti"] == s["dti"] and h["ci95"] == s["ci95"]
            and h["withheld_positive_pixels"] == s["withheld_positive_pixels"]
            and h["evaluator_version"] == holdout["evaluator_version"]
            and h["evidence_class"] == "HOLDOUT-DTI")
        checks["beats_random"] = holdout["paired_differences"]["random_dotted"]["ci95"][0] > 0
        checks["uniqueness_adjusted"] = (
            final_uniq["adjusted"]["duplicate_adjusted"] is False
            and surface_corr["adjusted"]["duplicate_adjusted"] is False)
        name = card["submission_name"]
        note = card["submission_note"]
        checks["name_note_valid"] = (
            isinstance(name, str) and 0 < len(name) <= 140
            and isinstance(note, str) and 0 < len(note) <= 140
            and receipt.get("submission_name") == name and receipt.get("note") == note)
        checks["validator_passed"] = (
            receipt.get("validator", {}).get("all_checks_passed") is True
            and receipt.get("sha256") == card.get("raster_sha256"))
        tif_docs = root / "docs/downloads" / f"{name}.tif"
        tif_sub = root / "submissions" / f"{name}.tif"
        tif = tif_docs if tif_docs.is_file() else tif_sub
        checks["tif_hash_bound"] = tif.is_file() and digest(tif) == card.get("raster_sha256")
        zpath = tif.with_suffix(".zip")
        zip_ok = False
        if zpath.is_file() and digest(zpath) == receipt.get("zip_sha256"):
            with zipfile.ZipFile(zpath) as z:
                zip_ok = z.namelist() == [tif.name] and z.read(tif.name) == tif.read_bytes()
        checks["zip_single_tif_bound"] = zip_ok
        for key, ok in checks.items():
            if not ok:
                reasons.append(f"E3 release check failed: {key}")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile) as exc:
        reasons.append("Missing or invalid E3 evidence: " + str(exc))
    ok = not reasons
    return {
        "download_candidate_ok": ok,
        "download_and_submit_ok": False,
        "slot_authorized": False,
        "verdict": (card or {}).get("verdict", "negative"),
        "submission_name": (card or {}).get("submission_name"),
        "raster_sha256": (card or {}).get("raster_sha256"),
        "checks": checks,
        "reasons": reasons,
        "policy": ("Candidate download requires every check above. Uploading still "
                   "requires separate selector review (full-registry scan, weekly-cap "
                   "check); local validation is not organizer acceptance."),
    }


def released_filenames(root):
    """Exact public raster filenames allowed under docs/downloads (may be empty)."""
    try:
        card = _load(root, "evidence/run_card_e3_amended.json")
        if card.get("verdict") == "promote" and card.get("raster_sha256"):
            name = card["submission_name"]
            return {f"{name}.tif", f"{name}.zip"}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return set()


def assert_publication_e3(root):
    """Docs tree may expose only the hash-bound released TIF/ZIP; no symlinks."""
    root = Path(root)
    allowed = released_filenames(root)
    docs = root / "docs"
    bad = []
    for p in docs.rglob("*"):
        if p.is_symlink():
            bad.append(p.relative_to(root).as_posix())
        elif p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}:
            if not (p.parent == docs / "downloads" and p.name in allowed):
                bad.append(p.relative_to(root).as_posix())
    if bad:
        raise ValueError("Unreleased public raster artifacts: " + ", ".join(sorted(bad)))
    # Released copies, when the run promoted, must be present and hash-bound.
    status = release_status_e3(root)
    if allowed and not status["download_candidate_ok"]:
        raise ValueError("Released filenames present in card but release checks fail: "
                         + "; ".join(status["reasons"]))
    return status


def assert_root_guard_e3(root):
    """Root-Pages guard for the E3 site: like E1 guard, plus released docs files."""
    root = Path(root)
    if (root / ".nojekyll").exists():
        raise ValueError("Root .nojekyll bypasses publication exclusions.")
    config = json.loads((root / "_config.yml").read_text())
    excluded = config.get("exclude", [])
    if (not isinstance(excluded, list) or not all(isinstance(x, str) for x in excluded)
            or not {"quarantine", "data", "submissions"}.issubset(excluded)
            or "docs" in excluded):
        raise ValueError("Invalid root publication exclusions.")
    allowed = released_filenames(root)
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and not (base == root and d in excluded)]
        for name in dirs + files:
            if name.startswith(".") or (base == root and name in excluded):
                continue
            path = base / name
            if path.is_symlink():
                raise ValueError("Unsafe root Pages symlink: " + path.relative_to(root).as_posix())
            if path.is_file() and path.suffix.lower() in {".tif", ".tiff", ".zip"}:
                rel = path.relative_to(root)
                if not (rel.parent.as_posix() == "docs/downloads" and name in allowed):
                    raise ValueError("Unsafe root Pages artifact: " + rel.as_posix())
