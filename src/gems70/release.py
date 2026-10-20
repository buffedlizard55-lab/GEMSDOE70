"""Publication status, derived from measured evidence (evidence/release2.json).

download_and_submit_ok is True only if the final run card's gates all passed.
A research download may exist while submission is prohibited; the two are
never conflated.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def release_status(root):
    root = Path(root)
    try:
        rel = json.loads((root / "evidence/release2.json").read_text())
        card = json.loads((root / "evidence/run_card.json").read_text())
        ok = bool(rel.get("download_and_submit_ok")) and card.get("verdict") == "promote"
        reasons = list(rel.get("reasons", []))
        if not ok and not reasons:
            reasons.append("Run verdict is not promote.")
        return {"download_and_submit_ok": ok,
                "download_research_ok": bool(rel.get("download_research_ok")),
                "verdict": card.get("verdict"), "reasons": reasons,
                "policy": rel.get("policy", "")}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"download_and_submit_ok": False, "download_research_ok": False,
                "verdict": "negative",
                "reasons": [f"Missing or invalid release evidence: {exc}"],
                "policy": "Fail closed: no release evidence, no submission."}


def assert_no_public_rasters(root):
    """Every published TIFF/ZIP must be exactly the run-card artifact (hash-bound)."""
    root = Path(root)
    docs = root / "docs"
    rasters = [p for p in docs.rglob("*") if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}]
    if not rasters:
        return
    try:
        card = json.loads((root / "evidence/run_card.json").read_text())
        expected = {Path(card["raster_file"]).name}
        zip_name = Path(card["raster_file"]).with_suffix(".zip").name
        expected.add(zip_name)
    except Exception as exc:
        raise ValueError(f"Published rasters without a hash-bound run card: {exc}")
    bad = [p.relative_to(root).as_posix() for p in rasters if p.name not in expected]
    if bad:
        raise ValueError("Unbound published TIFF/ZIP artifacts: " + ", ".join(bad))
    tif = docs / "downloads" / Path(card["raster_file"]).name
    if tif.exists() and digest(tif) != card["raster_sha256"]:
        raise ValueError("Published TIFF hash does not match run card.")
