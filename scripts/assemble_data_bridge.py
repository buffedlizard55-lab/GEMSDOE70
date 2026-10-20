#!/usr/bin/env python3
"""
Reassemble training_features.tif from bridge parts (GitHub 100MB limit).

Usage: python scripts/assemble_data_bridge.py
Output: data/training_features.tif (418 MB) SHA 4371c82e...
"""
import pathlib, hashlib, json

bridge = pathlib.Path("data/bridge")
manifest = json.load(open(bridge / "manifest.json"))
parts = manifest["files"][0]["parts"]
out = pathlib.Path("data/training_features.tif")
out.parent.mkdir(parents=True, exist_ok=True)

print(f"Assembling {manifest['files'][0]['name']} from {len(parts)} parts...")
with open(out, "wb") as outf:
    for p in parts:
        part_path = bridge / p["name"]
        print(f"  {p['name']} ({p['bytes']} bytes) SHA {p['sha256'][:8]}...")
        with open(part_path, "rb") as pf:
            outf.write(pf.read())

# Verify SHA
h = hashlib.sha256()
with open(out, "rb") as f:
    for chunk in iter(lambda: f.read(8192*1024), b""):
        h.update(chunk)
sha = h.hexdigest()
expected = manifest["files"][0]["sha256"]
print(f"SHA: {sha}")
print(f"Expected: {expected}")
print("PASS" if sha==expected else "FAIL")
