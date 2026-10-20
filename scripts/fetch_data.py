#!/usr/bin/env python3
"""Fetch the sha256-pinned competition mirror (GEMSDOE32 registry/data_manifest.json).

Provenance: these are owner-supplied public GitHub mirrors of DrivenData competition
files (login-walled). They are integrity-pinned by sha256 but NOT organizer-authenticated
(see registry/data_manifest_gemsdoe32.json "provenance" fields and IR-69-DATA-01).

Large files land in .cache/gems_data (git-ignored); nothing >1 MB is committed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "data_manifest_gemsdoe32.json"
DEST = ROOT / ".cache" / "gems_data"

WANT = {
    "training_features",           # 19-band physics stack (5 parts, 419 MB)
    "ext_lidar_scarp_features_u8",  # 1 m LiDAR scarp composite (u8 bands)
    "ext_geodawn_rad_u8",           # GeoDAWN radiometrics (K, Th, TC)
    "ext_geodawn_extensions_u8",    # GeoDAWN extension layers
    "ext_gdr_wellspring_in_footprint",
    "ext_gdr_qfaults_traces",
    "ext_gdr_volcanic_vents_in_footprint",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh_raw(repo: str, ref: str, path: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}",
             "-H", "Accept: application/vnd.github.raw"],
            stdout=fh, check=True)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    ok, fail = [], []
    for f in manifest["files"]:
        if f["id"] not in WANT:
            continue
        target = DEST / f["dest"]
        if target.exists() and sha256(target) == f["sha256"]:
            print(f"[cached] {f['id']} {target.name}", flush=True)
            ok.append(f["id"])
            continue
        try:
            if "parts" in f:
                chunks = []
                for i, p in enumerate(f["parts"]):
                    c = DEST / f"_part-{f['id']}-{i:03d}"
                    if not (c.exists() and c.stat().st_size > 0):
                        print(f"[part {i+1}/{len(f['parts'])}] {f['id']} <- {p}", flush=True)
                        gh_raw(f["repo"], f["ref"], p, c)
                    chunks.append(c)
                with target.open("wb") as out:
                    for c in chunks:
                        out.write(c.read_bytes())
                for c in chunks:
                    c.unlink()
            else:
                print(f"[fetch] {f['id']} <- {f['repo']}:{f.get('path')}", flush=True)
                gh_raw(f["repo"], f["ref"], f["path"], target)
            got = sha256(target)
            if got != f["sha256"]:
                target.unlink(missing_ok=True)
                raise RuntimeError(f"sha256 mismatch for {f['id']}: {got}")
            print(f"[ok] {f['id']} sha256 verified ({target.stat().st_size} bytes)", flush=True)
            ok.append(f["id"])
        except Exception as exc:  # noqa: BLE001 - fail closed, keep going
            print(f"[FAIL] {f['id']}: {exc}", flush=True)
            fail.append(f["id"])
    print(f"SUMMARY ok={len(ok)} fail={len(fail)} failed={fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
