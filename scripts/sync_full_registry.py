#!/usr/bin/env python3
"""Synchronize and SHA-256 verify the complete accessible owner raster registry.

Uses zero-rate-limit ``https://codeload.github.com`` streamed tarballs for every
GEMSDOE repository HEAD plus blob-filtered git fetches on ``github.com`` for any
historical non-HEAD commits in ``registry/inherited_registry_index.json``, plus
local quarantined artifacts in ``quarantine/concurrent-h70c``. Zero REST API
requests are consumed.
"""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]

import rasterio
from gems57.grid import TRANSFORM

CACHE_DIR = ROOT / ".cache" / "registry"
OUT_INDEX = CACHE_DIR / "full_live_index.json"

NON_SUBMISSION_BASENAMES = {
    "existing_faults.tif",
    "labels.tif",
    "sample_submission.tif",
    "example_submission.tif",
    "training_features.tif",
    "gems-geodawn-numerical-features.tif",
    "lidar_scarp_features_u8.tif",
    "geodawn_rad_u8.tif",
    "geodawn_extensions_u8.tif",
    "derived_sgmc_faults_100m_u8.tif",
    "derived_gdr_2m_probes_100m_u8.tif",
    "derived_gdr_paleo_100m_u8.tif",
    "derived_gdr_qfaults_v2_100m_u8.tif",
    "derived_gdr_volcanics_100m_u8.tif",
    "qfaults_prior_u8.tif",
    "tiger_road_distance_m.tif",
    "blm_closed_claim_distance_m.tif",
    "acquisition_block_id_100m.tif",
    "template-mask.tif",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_valid_grid_raster(path: Path) -> bool:
    try:
        with rasterio.open(path) as src:
            return (
                src.count == 1
                and src.shape == (3730, 3292)
                and src.crs is not None
                and src.crs.to_epsg() == 32611
                and src.transform == TRANSFORM
            )
    except Exception:
        return False


def candidate_repo_names(base: dict) -> list[str]:
    names = {r["repo"] for r in base.get("repos", [])}
    names.update(r["repo_first"] for r in base.get("rasters", []))
    for i in range(1, 90):
        names.add(f"GEMSDOE{i}")
        names.add(f"{i}GEMSDOE")
    names.update({"GEMSDOE", "MasterSite", "LEARNGEMSDOE"})
    names.discard("GEMSDOE70")
    return sorted(names)


def stream_repo_head(repo: str) -> tuple[str, list[dict], str | None]:
    url = f"https://codeload.github.com/buffedlizard55-lab/{repo}/tar.gz/HEAD"
    found: list[dict] = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "gems70-registry-sync"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            with tarfile.open(fileobj=resp, mode="r|gz") as tf:
                for member in tf:
                    if not member.isfile():
                        continue
                    parts = member.name.split("/", 1)
                    rel = parts[1] if len(parts) > 1 else parts[0]
                    if not rel.lower().endswith((".tif", ".tiff")):
                        continue
                    if Path(rel).name in NON_SUBMISSION_BASENAMES:
                        continue
                    fh = tf.extractfile(member)
                    if fh is None:
                        continue
                    raw = fh.read()
                    digest = sha256_bytes(raw)
                    dest = CACHE_DIR / f"{digest}.tif"
                    if not dest.exists():
                        tmp = CACHE_DIR / f".{digest[:12]}.{repo}.tmp"
                        tmp.write_bytes(raw)
                        tmp.replace(dest)
                    found.append(
                        {
                            "sha256": digest,
                            "repo": repo,
                            "source": f"{repo}:{rel}",
                            "bytes": len(raw),
                        }
                    )
        return repo, found, None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return repo, [], None
        return repo, [], f"{repo}: HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return repo, [], f"{repo}: {str(exc)[:160]}"


def fetch_missing_historical_blobs(missing_by_repo: dict[str, list[dict]]) -> list[str]:
    errors: list[str] = []
    for repo, recs in sorted(missing_by_repo.items()):
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--bare",
                        "--filter=blob:none",
                        f"https://github.com/buffedlizard55-lab/{repo}.git",
                        tmpdir,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=180,
                )
                for rec in recs:
                    blob = rec.get("blob")
                    d = rec["sha256"]
                    if not blob:
                        errors.append(f"{repo}:{d}: missing blob id")
                        continue
                    raw = subprocess.check_output(
                        ["git", "-C", tmpdir, "cat-file", "blob", blob],
                        timeout=120,
                    )
                    got = sha256_bytes(raw)
                    if got != d:
                        errors.append(f"{repo}:{d}: blob sha mismatch {got}")
                        continue
                    dest = CACHE_DIR / f"{d}.tif"
                    dest.write_bytes(raw)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{repo}: git blob recovery failed ({str(exc)[:140]})")
    return errors


def main() -> int:
    t0 = time.monotonic()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Clean any stale temp files from interrupted runs
    for stale in CACHE_DIR.glob("*.tmp"):
        stale.unlink(missing_ok=True)
    for stale in CACHE_DIR.glob("_blob_*.tif"):
        stale.unlink(missing_ok=True)

    base = json.loads((ROOT / "registry" / "inherited_registry_index.json").read_text())
    by_sha: dict[str, dict] = {}
    for rec in base.get("rasters", []):
        digest = rec["sha256"]
        by_sha[digest] = {
            "sha256": digest,
            "blob": rec.get("blob"),
            "repo_first": rec["repo_first"],
            "sources": list(rec["sources"]),
            "bytes": rec.get("bytes"),
        }

    repos = candidate_repo_names(base)
    stream_errors: list[str] = []
    active_repos = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for repo, found, err in ex.map(stream_repo_head, repos):
            if err:
                stream_errors.append(err)
            if found:
                active_repos += 1
            for item in found:
                d = item["sha256"]
                if d in by_sha:
                    if item["source"] not in by_sha[d]["sources"]:
                        by_sha[d]["sources"].append(item["source"])
                else:
                    by_sha[d] = {
                        "sha256": d,
                        "blob": None,
                        "repo_first": item["repo"],
                        "sources": [item["source"]],
                        "bytes": item["bytes"],
                    }

    # Add quarantined concurrent H70-C rasters
    for q_tif in sorted((ROOT / "quarantine").rglob("*.tif")):
        d = sha256_file(q_tif)
        dest = CACHE_DIR / f"{d}.tif"
        if not dest.exists():
            dest.write_bytes(q_tif.read_bytes())
        tag = f"GEMSDOE70:{q_tif.relative_to(ROOT).as_posix()}"
        if d in by_sha:
            if tag not in by_sha[d]["sources"]:
                by_sha[d]["sources"].append(tag)
        else:
            by_sha[d] = {
                "sha256": d,
                "blob": None,
                "repo_first": "GEMSDOE70",
                "sources": [tag],
                "bytes": dest.stat().st_size,
            }

    # Check which historical entries from inherited_registry_index weren't on HEAD
    missing_by_repo: dict[str, list[dict]] = defaultdict(list)
    for d, rec in by_sha.items():
        dest = CACHE_DIR / f"{d}.tif"
        if not (dest.exists() and sha256_file(dest) == d):
            missing_by_repo[rec["repo_first"]].append(rec)

    print(
        f"[sync] Streamed HEADs ({active_repos} active repos with rasters); "
        f"historical non-HEAD blobs to recover via git={sum(len(v) for v in missing_by_repo.values())} "
        f"across {len(missing_by_repo)} repos",
        flush=True,
    )
    git_errors = fetch_missing_historical_blobs(missing_by_repo)

    verified_rasters: list[dict] = []
    skipped_non_grid = 0
    verify_errors: list[str] = []

    def check_entry(rec: dict):
        d = rec["sha256"]
        dest = CACHE_DIR / f"{d}.tif"
        if not dest.exists():
            return ("missing", f"missing {d} ({rec['sources'][0]})", None)
        if sha256_file(dest) != d:
            dest.unlink(missing_ok=True)
            return ("mismatch", f"sha256 mismatch {d}", None)
        if not is_valid_grid_raster(dest):
            dest.unlink(missing_ok=True)
            return ("non_grid", None, None)
        return (
            "ok",
            None,
            {
                "sha256": d,
                "blob": rec.get("blob"),
                "repo_first": rec["repo_first"],
                "sources": sorted(rec["sources"]),
                "bytes": dest.stat().st_size,
                "cache_file": str(dest),
            },
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        for kind, err, item in ex.map(check_entry, by_sha.values()):
            if kind == "non_grid":
                skipped_non_grid += 1
            elif err:
                verify_errors.append(err)
            elif item is not None:
                verified_rasters.append(item)

    verified_rasters.sort(key=lambda r: (r["repo_first"], r["sources"][0], r["sha256"]))
    all_errors = stream_errors + git_errors + verify_errors
    index_doc = {
        "owner": "buffedlizard55-lab",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generated_by": "scripts/sync_full_registry.py",
        "transport": "codeload.github.com streamed tar.gz + git blob-less clone fallback (0 REST API calls)",
        "candidate_repos_probed": len(repos),
        "repos_with_rasters_on_head": active_repos,
        "skipped_non_grid_rasters": skipped_non_grid,
        "errors": all_errors,
        "complete_accessible_scan": len(all_errors) == 0 and len(verified_rasters) > 0,
        "n_unique_grid_rasters": len(verified_rasters),
        "elapsed_seconds": round(time.monotonic() - t0, 2),
        "rasters": verified_rasters,
    }
    OUT_INDEX.write_text(json.dumps(index_doc, indent=2) + "\n")
    print(
        f"[sync] COMPLETE in {index_doc['elapsed_seconds']}s: "
        f"verified_rasters={len(verified_rasters)}, skipped_non_grid={skipped_non_grid}, "
        f"complete={index_doc['complete_accessible_scan']}, errors={len(all_errors)}",
        flush=True,
    )
    if all_errors:
        for e in all_errors[:10]:
            print("  ERROR:", e, flush=True)
    return 0 if index_doc["complete_accessible_scan"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
