#!/usr/bin/env python3
"""Download every grid-matching registry raster in registry/inherited_registry_index.json.

Each file is fetched by Git blob id from its owner repository through the GitHub
API (gh), then SHA-256 verified against the index before it is kept. Files land in
.cache/registry/<sha256>.tif (git-ignored). Nothing is committed.

Evidence class: REGISTRY-MEASUREMENT input acquisition only. Pins prove that the
bytes match the index; they do not authenticate the owner's intent or the organizer.
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "registry" / "inherited_registry_index.json"
DEST = ROOT / ".cache" / "registry"
OWNER = "buffedlizard55-lab"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_one(row: dict) -> tuple[str, str]:
    digest = row["sha256"]
    target = DEST / f"{digest}.tif"
    if target.exists() and sha256(target) == digest:
        return digest, "cached"
    repo = row["sources"][0].split(":", 1)[0]
    tmp = target.with_suffix(".tif.part")
    try:
        with tmp.open("wb") as out:
            subprocess.run(
                ["gh", "api", f"repos/{OWNER}/{repo}/git/blobs/{row['blob']}",
                 "-H", "Accept: application/vnd.github.raw"],
                stdout=out, check=True, timeout=600)
        if sha256(tmp) != digest:
            tmp.unlink(missing_ok=True)
            return digest, "sha-mismatch"
        tmp.replace(target)
        return digest, "ok"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        tmp.unlink(missing_ok=True)
        return digest, f"error: {exc}"


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    rows = json.loads(INDEX.read_text())["rasters"]
    status: dict[str, str] = {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for i, (digest, state) in enumerate(ex.map(fetch_one, rows), 1):
            status[digest] = state
            if i % 50 == 0 or state not in ("ok", "cached"):
                print(f"{i}/{len(rows)} {digest[:12]} {state}", flush=True)
    counts: dict[str, int] = {}
    for state in status.values():
        key = state.split(":")[0]
        counts[key] = counts.get(key, 0) + 1
    print("SUMMARY", json.dumps(counts), flush=True)
    out = ROOT / "evidence" / "registry_fetch.json"
    out.write_text(json.dumps({"expected": len(rows), "states": counts,
                               "failures": {k: v for k, v in status.items()
                                            if v not in ("ok", "cached")}}, indent=2) + "\n")
    return 0 if all(v in ("ok", "cached") for v in status.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
