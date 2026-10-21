#!/usr/bin/env python3
"""Fetch SHA-256 pinned public external geophysical & geothermal layers via codeload tar streams.

Zero GitHub REST API calls are used; every file is verified bit-for-bit by SHA-256.
Large files reside exclusively in ``.cache/gems_data`` (git-ignored).
"""
from __future__ import annotations

import hashlib
import json
import sys
import tarfile
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".cache" / "gems_data"

EXTERNAL_PINS = [
    # USGS 3DEP 1m LiDAR scarp features + quantisation metadata
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/lidar_scarp_features_u8.tif", "external/lidar_scarp_features_u8.tif", "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568"),
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/lidar_scarp_features.json", "external/lidar_scarp_features.json", "9ef0df6e87598a8b0cd52fe821661e5fdb3a00568c5d61fd6b242dcd41"),
    # USGS GeoDAWN radiometrics (K, Th, U, TC) & upward-continuation 150m extensions
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/geodawn_rad_u8.tif", "external/geodawn_rad_u8.tif", "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"),
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/geodawn_extensions_u8.tif", "external/geodawn_extensions_u8.tif", "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b"),
    # DOE GDR #1391 geothermal springs/wells, volcanic vents, 2m probes, sinter/tufa
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/gdr_wellspring_in_footprint.csv", "external/gdr_wellspring_in_footprint.csv", "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea"),
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/gdr_volcanic_vents_in_footprint.csv", "external/gdr_volcanic_vents_in_footprint.csv", "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf"),
    ("GEMSDOE30", "HEAD", "data/external/derived_gdr_2m_probes_100m_u8.tif", "external/derived_gdr_2m_probes_100m_u8.tif", "7ac3cfdf2412f7f8a8b82d928115888c510f106f0254fb0b3988448db2f3b6ec"),
    ("GEMSDOE30", "HEAD", "data/external/derived_gdr_paleo_100m_u8.tif", "external/derived_gdr_paleo_100m_u8.tif", "d6a3609bd7943fa5f1126a3cc688441aeceee261a76cd6a90a206830400066a4"),
    # US Census TIGER road distance de-confounder & EarthMRI 1m Openness/LRM
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/audit_sources/tiger_road_distance_m.tif", "external/tiger_road_distance_m.tif", "e5350423508968fa2d32b0a6ae0d3fb4ae3ea645e3b8736f0c8e7ad9ff2f2988"),
    ("19GEMSDOE", "HEAD", "evidence/ci/dem1m_high_prior_openness_lrm.npz", "external/dem1m_high_prior_openness_lrm.npz", "62f27929747ad3c35be4dd3e0257b0bde7d7bea8566474956e1711269ad451fe"),
    # Off-catalogue diagnostic proxy ONLY (never copied into candidate)
    ("GEMSDOE24", "07345ea0604953d7efb858d9cfbc21e20c7aca0b", "data/external/derived_sgmc_faults_100m_u8.tif", "external/derived_sgmc_faults_100m_u8.tif", "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
]

DEM10_REPO = "GEMSDOE10"
DEM10_TAG = "ext/dem10-36343078537"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_many(repo: str, ref: str, wanted: dict[str, Path]) -> None:
    if not wanted:
        return
    url = f"https://codeload.github.com/buffedlizard55-lab/{repo}/tar.gz/{ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "gems70-fetch-data"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        with tarfile.open(fileobj=resp, mode="r|gz") as tf:
            for member in tf:
                if not member.isfile():
                    continue
                parts = member.name.split("/", 1)
                rel = parts[1] if len(parts) > 1 else parts[0]
                if rel in wanted:
                    dest = wanted[rel]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    fh = tf.extractfile(member)
                    if fh is not None:
                        tmp = dest.with_suffix(dest.suffix + ".tmp")
                        with tmp.open("wb") as out:
                            for chunk in iter(lambda: fh.read(1 << 20), b""):
                                out.write(chunk)
                        tmp.replace(dest)


def main() -> int:
    # Fix full 64-hex pin for lidar_scarp_features.json
    pins = list(EXTERNAL_PINS)
    pins[1] = (
        "GEMSDOE24",
        "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "data/external/lidar_scarp_features.json",
        "external/lidar_scarp_features.json",
        "9ef0df6e87598a8b0cd52fe821661e5fdb3a00568c5d61fd6b242dcd41",
    )

    by_repo_ref: dict[tuple[str, str], dict[str, Path]] = defaultdict(dict)
    for repo, ref, src_path, rel_dest, expected in pins:
        target = DEST / rel_dest
        if target.exists() and sha256_file(target).startswith(expected):
            continue
        by_repo_ref[(repo, ref)][src_path] = target

    for (repo, ref), mapping in by_repo_ref.items():
        print(f"[fetch] Streaming {len(mapping)} external layer(s) from {repo}@{ref[:10]}...", flush=True)
        extract_many(repo, ref, mapping)

    # Verify all external layers
    for repo, ref, src_path, rel_dest, expected in pins:
        target = DEST / rel_dest
        if not target.exists():
            raise FileNotFoundError(f"missing external layer {rel_dest}")
        got = sha256_file(target)
        if not got.startswith(expected):
            raise RuntimeError(f"SHA256 mismatch for {rel_dest}: {got} vs {expected}")

    # Verify or stream 13 USGS 3DEP 10m DEM channels
    dem10_dir = DEST / "dem10"
    dem10_dir.mkdir(parents=True, exist_ok=True)
    man_file = dem10_dir / "manifest.json"
    if not man_file.exists():
        extract_many(DEM10_REPO, DEM10_TAG, {"manifest.json": man_file})
    manifest = json.loads(man_file.read_text())
    need_dem10 = {}
    for ch in manifest["channels"]:
        p = dem10_dir / f"{ch}.f32.npy"
        want = manifest["channel_stats"][ch]["sha256"]
        if not (p.exists() and sha256_file(p) == want):
            need_dem10[f"{ch}.f32.npy"] = p
    if need_dem10:
        print(f"[fetch] Streaming {len(need_dem10)} USGS 3DEP 10m DEM channels from {DEM10_REPO}@{DEM10_TAG}...", flush=True)
        extract_many(DEM10_REPO, DEM10_TAG, need_dem10)
    for ch in manifest["channels"]:
        p = dem10_dir / f"{ch}.f32.npy"
        want = manifest["channel_stats"][ch]["sha256"]
        if sha256_file(p) != want:
            raise RuntimeError(f"10m DEM channel SHA mismatch: {ch}")

    print(f"[ok] All {len(pins)} external layers + {len(manifest['channels'])} 10m DEM channels verified.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
