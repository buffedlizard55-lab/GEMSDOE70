#!/usr/bin/env python3
"""Deterministic restoration and SHA-256 verification of public GEMS datasets.

Restores into `.cache/data/` (gitignored) and exposes symlinks in `data/`:
  1. Official DrivenData DOE GEMS competition rasters (derived from open U.S.
     federal datasets: USGS ScienceBase GeoDAWN, Great Basin Geopotential Atlas,
     INGENIOUS DOE GDR-1391, USGS Quaternary Fault & Fold Database).
  2. Open public auxiliary datasets pinned by exact SHA-256 in `.cache/data/external/`:
     - USGS 3DEP 1/3 arc-second (~10 m) seamless DEM multi-scale scarp & chi/ksn
       geomorphic rasters (`topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_i16.tif`)
     - USGS 3DEP 1 m Earth MRI LiDAR scarplet rasters (`lidar_scarp_features_u8.tif`)
     - USGS GeoDAWN airborne gamma-ray spectrometry & upward-continued magnetics
       (`geodawn_rad_u8.tif`, `geodawn_extensions_u8.tif`)
     - USGS State Geologic Map Compilation raw 100 m fault traces (`sgmc_faults_100m.tif`)
     - DOE Geothermal Data Repository Submission 1391 (INGENIOUS) springs/wells,
       2 m temperature probes, paleo-geothermal deposits, volcanic vents, and
       catalogue segment trace attributes (`trace_segments_utm11.csv`).

Uses zero-API-quota `codeload.github.com` tarball streaming first and verifies
every file byte-for-byte against its pinned SHA-256 before acceptance.
"""
from __future__ import annotations

import hashlib
import os
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / ".cache" / "data"
EXT_DIR = DATA_DIR / "external"
PUBLIC_DATA_DIR = ROOT / "data"

CORE_FILES = (
    {
        "name": "training_features.tif",
        "sha256": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
        "repo": "buffedlizard55-lab/19GEMSDOE",
        "repo_path": "inputs/official/training_features.tif",
        "commit": "HEAD",
    },
    {
        "name": "existing_faults.tif",
        "sha256": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
        "repo": "buffedlizard55-lab/19GEMSDOE",
        "repo_path": "inputs/official/existing_faults.tif",
        "commit": "HEAD",
    },
    {
        "name": "sample_submission.tif",
        "sha256": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
        "repo": "buffedlizard55-lab/19GEMSDOE",
        "repo_path": "inputs/official/sample_submission.tif",
        "commit": "HEAD",
    },
)

EXTERNAL_60_COMMIT = "32024716f218d06a94e01464157392119c03cb15"
EXTERNAL_FILES = (
    {
        "name": "topo_10m_derived_100m_u8.tif",
        "sha256": "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/topo_10m_derived_100m_u8.tif",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "topo_10m_derived_100m_u8.manifest.json",
        "sha256": "181d5527ba7ed2990031918a8b6c9d5d94e3998b2daf656de0c33322ca94120a",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/topo_10m_derived_100m_u8.manifest.json",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "dem10_chi_100m_i16.tif",
        "sha256": "8897ba9c30ef1cd7ad5f23c16c6dfd7bb070e7e757f36fd9486eb45edfd973a5",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/dem10_chi_100m_i16.tif",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "dem10_chi_100m.manifest.json",
        "sha256": "187a961ef5da45278c84b25d16296a5f3458da37abff45046d31ed58b9f5af86",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/dem10_chi_100m.manifest.json",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "lidar_scarp_features_u8.tif",
        "sha256": "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/lidar_scarp_features_u8.tif",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "geodawn_rad_u8.tif",
        "sha256": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/geodawn_rad_u8.tif",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "geodawn_extensions_u8.tif",
        "sha256": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/geodawn_extensions_u8.tif",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "sgmc_faults_100m.tif",
        "sha256": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/sgmc_faults_100m.tif",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "gdr_wellspring_in_footprint.csv",
        "sha256": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/gdr_wellspring_in_footprint.csv",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "2m_temperature_probe_INGENIOUS_regional_data.zip",
        "sha256": "1301f70d230058e616ea5d34d1c7a32fabf7d49198172f376c59c89bd652eca3",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/2m_temperature_probe_INGENIOUS_regional_data.zip",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "paleo_geothermal_regional.zip",
        "sha256": "faffcf697f32dbbf6cbb317cd1effb3e305538ce38eb239d72d0c6fa071e91ca",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/paleo_geothermal_regional.zip",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "gdr_volcanic_vents_in_footprint.csv",
        "sha256": "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/gdr_volcanic_vents_in_footprint.csv",
        "commit": EXTERNAL_60_COMMIT,
    },
    {
        "name": "trace_segments_utm11.csv",
        "sha256": "c5edf9df3e0e1413c52784884fc38e5b9ca54627b27c6f8baf7713e908f48513",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "repo_path": "data/external/trace_segments_utm11.csv",
        "commit": EXTERNAL_60_COMMIT,
    },
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stream_from_codeload(repo: str, commit: str, targets: dict[str, tuple[Path, str]]) -> None:
    """Stream multiple files from one pinned GitHub tarball without spending REST API quota."""
    url = f"https://codeload.github.com/{repo}/tar.gz/{commit}"
    req = urllib.request.urlopen(url, timeout=180)
    remaining = set(targets.keys())
    with tarfile.open(fileobj=req, mode="r|gz") as tf:
        for member in tf:
            if not member.isfile():
                continue
            rel = member.name.split("/", 1)[1] if "/" in member.name else member.name
            if rel not in remaining:
                continue
            dst, expected_sha = targets[rel]
            tmp = dst.with_suffix(dst.suffix + ".tmp")
            data = tf.extractfile(member).read()
            tmp.write_bytes(data)
            got = sha256_file(tmp)
            if got != expected_sha:
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"SHA256 mismatch for {rel}: got {got}, expected {expected_sha}")
            tmp.replace(dst)
            remaining.remove(rel)
            print(f"[restored] {dst.name}  sha256={got[:16]}...  ({len(data)} bytes)")
            if not remaining:
                break


def ensure_group(items: tuple[dict, ...], base_dir: Path) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    missing_by_source: dict[tuple[str, str], dict[str, tuple[Path, str]]] = {}
    for spec in items:
        dst = base_dir / spec["name"]
        if dst.exists() and sha256_file(dst) == spec["sha256"]:
            print(f"[verified] {dst.name}  sha256={spec['sha256'][:16]}...")
            continue
        missing_by_source.setdefault((spec["repo"], spec["commit"]), {})[spec["repo_path"]] = (
            dst,
            spec["sha256"],
        )

    for (repo, commit), targets in missing_by_source.items():
        stream_from_codeload(repo, commit, targets)

    for spec in items:
        dst = base_dir / spec["name"]
        if not dst.exists() or sha256_file(dst) != spec["sha256"]:
            raise RuntimeError(f"Failed to restore verified {dst}")


def ensure_public_symlinks() -> None:
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for spec in CORE_FILES:
        src = DATA_DIR / spec["name"]
        link = PUBLIC_DATA_DIR / spec["name"]
        rel_target = os.path.relpath(src, PUBLIC_DATA_DIR)
        if link.is_symlink() or link.exists():
            if link.resolve() == src.resolve():
                continue
            link.unlink()
        link.symlink_to(rel_target)


def main() -> int:
    ensure_group(CORE_FILES, DATA_DIR)
    ensure_group(EXTERNAL_FILES, EXT_DIR)
    ensure_public_symlinks()
    return 0


if __name__ == "__main__":
    sys.exit(main())
