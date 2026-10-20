#!/usr/bin/env python3
"""Refresh the current public sibling TIFF inventory with partial Git clones.

This is a bounded, public-remote alternative to the API-only inherited-registry
fetcher. It fetches no GitHub API blobs: each repository is cloned with
``--filter=blob:none --no-checkout`` and only tracked TIFF paths are checked out.
The default scan covers the user-listed current siblings (GEMSDOE66-72, including
this repository's public default-branch snapshot); pass ``--repo`` explicitly to
control scope. Results and cached binaries are not organizer-authenticated.

Large files live under .cache/sibling_registry (git-ignored). The JSON receipt
records each remote HEAD, tree path, Git blob id, SHA-256, exact grid compatibility,
and binary-dot count under the shared GEMSDOE uniqueness definition.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from pathlib import PurePosixPath
from typing import Iterable
from urllib.parse import quote

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from gems57.uniqueness import _dots  # use the shared binary-dot definition

OWNER = "buffedlizard55-lab"
DEFAULT_REPOS = ("GEMSDOE66", "GEMSDOE67", "GEMSDOE68", "GEMSDOE69", "GEMSDOE70", "GEMSDOE71", "GEMSDOE72")
TIFF_SUFFIXES = {".tif", ".tiff"}
BATCH_SIZE = 80


def _run(args: list[str], *, cwd: Path | None = None, timeout: int = 600) -> bytes:
    result = subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout)
    return result.stdout


def parse_ls_tree_z(raw: bytes) -> list[dict[str, str]]:
    """Parse ``git ls-tree -r -z`` output without losing spaces in paths."""
    files: list[dict[str, str]] = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, path_bytes = entry.split(b"\t", 1)
        mode, object_type, blob = metadata.decode("ascii").split(" ", 2)
        path = os.fsdecode(path_bytes)
        if object_type == "blob" and Path(path).suffix.lower() in TIFF_SUFFIXES:
            files.append({"path": path, "blob": blob, "mode": mode})
    return files


def valid_repo_slug(value: str) -> bool:
    """Accept a single GitHub repository component, never a path or traversal."""
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_regular_file(row: dict[str, str]) -> bool:
    """Only check out regular in-tree files; skip symlinks and unsafe paths."""
    path = PurePosixPath(row["path"])
    return (row["mode"] in {"100644", "100755"}
            and not path.is_absolute()
            and all(part not in {"", ".", ".."} for part in path.parts))


def _json_nodata(value):
    """Represent nonfinite GDAL nodata markers as strings, never invalid JSON floats."""
    if value is None:
        return None
    number = float(value)
    return number if np.isfinite(number) else str(number)


def _clone_or_reuse(repo: str, cache_root: Path, refresh: bool) -> tuple[Path, str]:
    destination = cache_root / repo
    if not (destination / ".git").is_dir():
        destination.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", "--depth", "1", "--filter=blob:none", "--no-checkout",
              f"https://github.com/{OWNER}/{repo}.git", str(destination)], timeout=900)
    elif refresh:
        _run(["git", "fetch", "--depth", "1", "origin"], cwd=destination, timeout=900)
        _run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=destination, timeout=300)
    commit = _run(["git", "rev-parse", "HEAD"], cwd=destination).decode().strip()
    return destination, commit


def _checkout_tiffs(repo_root: Path, rows: list[dict[str, str]]) -> None:
    for start in range(0, len(rows), BATCH_SIZE):
        paths = [row["path"] for row in rows[start:start + BATCH_SIZE]]
        if paths:
            _run(["git", "checkout", "--quiet", "HEAD", "--", *paths], cwd=repo_root,
                 timeout=900)


def scan_repo(repo: str, cache_root: Path, reference: tuple, footprint: np.ndarray,
              refresh: bool) -> dict:
    record: dict = {"repo": repo, "status": "error", "files": []}
    try:
        repo_root, commit = _clone_or_reuse(repo, cache_root, refresh)
        record.update({"status": "scanned", "commit": commit,
                       "source_tree": f"https://github.com/{OWNER}/{repo}/tree/{commit}"})
        tree = parse_ls_tree_z(_run(["git", "ls-tree", "-r", "-z", "HEAD"], cwd=repo_root))
        record["tracked_tiff_paths"] = len(tree)
        checkout_rows = [row for row in tree if _safe_regular_file(row)]
        record["skipped_nonregular_or_unsafe_paths"] = len(tree) - len(checkout_rows)
        _checkout_tiffs(repo_root, checkout_rows)
        matched = 0
        for row in tree:
            source_path = quote(row["path"], safe="/")
            source_url = f"https://github.com/{OWNER}/{repo}/blob/{commit}/{source_path}"
            if not _safe_regular_file(row):
                record["files"].append({"path": row["path"], "git_blob": row["blob"],
                                        "source_url": source_url,
                                        "single_band_grid_match": False,
                                        "binary_dot_count": None,
                                        "skipped_reason": "non-regular blob or unsafe path"})
                continue
            path = repo_root / row["path"]
            item = {"path": row["path"], "git_blob": row["blob"],
                    "source_url": source_url,
                    "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            try:
                with rasterio.open(path) as dataset:
                    item.update({"bands": dataset.count,
                                 "shape": [dataset.height, dataset.width],
                                 "crs": str(dataset.crs),
                                 "transform": list(dataset.transform)[:6],
                                 "dtype": dataset.dtypes[0] if dataset.count else None,
                                 "nodata": _json_nodata(dataset.nodata)})
                    exact_grid = ((dataset.height, dataset.width) == reference[0]
                                  and dataset.crs == reference[1]
                                  and dataset.transform == reference[2]
                                  and dataset.count == 1)
                    item["single_band_grid_match"] = bool(exact_grid)
                    if exact_grid:
                        values = dataset.read(1)
                        dots = _dots(values) & footprint
                        item["binary_dot_count"] = int(dots.sum())
                        matched += 1
                    else:
                        item["binary_dot_count"] = None
            except Exception as exc:  # retain the path and hash even if GDAL cannot open it
                item.update({"single_band_grid_match": False,
                             "binary_dot_count": None,
                             "raster_read_error": f"{type(exc).__name__}: {exc}"})
            record["files"].append(item)
        record["single_band_grid_matches"] = matched
    except Exception as exc:
        record.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return record


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", dest="repos",
                        help="Repository slug to scan; repeatable. Defaults to GEMSDOE66-72.")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache" / "sibling_registry")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "evidence" / "sibling_registry_refresh.json")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--refresh", action="store_true",
                        help="fetch the latest shallow remote HEAD for cached clones before scanning")
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")
    repos = tuple(dict.fromkeys(args.repos or DEFAULT_REPOS))
    if any(not valid_repo_slug(name) for name in repos):
        parser.error("--repo expects a safe owner-local repository slug, not a path")

    grid_path = ROOT / ".cache" / "data" / "sample_submission.tif"
    if not grid_path.is_file():
        grid_path = ROOT / "data" / "bridge" / "sample_submission.tif"
    with rasterio.open(grid_path) as sample:
        footprint = np.isfinite(sample.read(1))
        reference = ((sample.height, sample.width), sample.crs, sample.transform)

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=args.workers) as executor:
        rows = list(executor.map(lambda repo: scan_repo(repo, args.cache_dir, reference,
                                                       footprint, args.refresh), repos))
    all_files = [file for repo in rows for file in repo.get("files", [])]
    grid_files = [file for file in all_files if file.get("single_band_grid_match")]
    out = {
        "evidence_class": "PUBLIC_OWNER_GITHUB_HEAD_SCAN",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "authority_limit": "Owner-repository bytes only; not an organizer registry or official score receipt.",
        "grid_reference": {"path": str(grid_path.relative_to(ROOT)),
                           "shape": list(reference[0]), "crs": str(reference[1]),
                           "transform": list(reference[2])[:6],
                           "footprint_pixels": int(footprint.sum())},
        "scope": {"repositories_requested": list(repos),
                  "repositories_scanned": sum(row.get("status") == "scanned" for row in rows),
                  "repositories_failed": [row["repo"] for row in rows if row.get("status") != "scanned"],
                  "tracked_tiff_paths": sum(row.get("tracked_tiff_paths", 0) for row in rows),
                  "single_band_grid_matches": len(grid_files),
                  "unique_grid_sha256": len({file["sha256"] for file in grid_files}),
                  "matches_in_inherited_862_sha_set": None},
        "repositories": rows,
    }
    inherited = ROOT / "registry" / "inherited_registry_index.json"
    if inherited.is_file():
        expected = {row["sha256"] for row in json.loads(inherited.read_text()).get("rasters", [])}
        found = {file["sha256"] for file in grid_files}
        out["scope"]["inherited_862_unique_sha_count"] = len(expected)
        out["scope"]["matches_in_inherited_862_sha_set"] = len(expected & found)
        out["scope"]["current_grid_hashes_not_in_inherited_index"] = len(found - expected)
    args.output.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(out["scope"], indent=2))
    return 0 if not out["scope"]["repositories_failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
