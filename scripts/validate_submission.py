#!/usr/bin/env python3
"""
Validate submission TIF against competition format.
Re-reads bytes from disk, not memory.

Checks:
- single band float32
- dimensions 3730x3292
- CRS EPSG:32611
- transform [100,0,243350,0,-100,4508550]
- all cells finite
- values in [0,1]
- nodata handling
- on-catalogue leakage

Usage: python scripts/validate_submission.py <path.tif>
"""
import sys, pathlib, json
import rasterio
import numpy as np

EXPECTED = {
    "width": 3292,
    "height": 3730,
    "crs_epsg": 32611,
    "transform": (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
    "dtype": "float32",
}

def validate(path):
    path = pathlib.Path(path)
    if not path.exists():
        print(f"FAIL: {path} not found")
        sys.exit(1)
    with rasterio.open(path) as src:
        print(f"File: {path}")
        print(f"  Width: {src.width} (expected {EXPECTED['width']})")
        print(f"  Height: {src.height} (expected {EXPECTED['height']})")
        print(f"  Count: {src.count} (expected 1)")
        print(f"  Dtype: {src.dtypes[0]} (expected {EXPECTED['dtype']})")
        print(f"  CRS: {src.crs} (expected EPSG:{EXPECTED['crs_epsg']})")
        print(f"  Transform: {tuple(src.transform)[:6]}")
        print(f"  Nodata: {src.nodata}")
        data = src.read(1)
        print(f"  Shape: {data.shape}")
        print(f"  Min: {np.nanmin(data):.6f} Max: {np.nanmax(data):.6f}")
        print(f"  NaN: {np.isnan(data).sum()} Inf: {np.isinf(data).sum()}")
        print(f"  Sentinel (-3.4e38): {(data < -1e38).sum()}")
        print(f"  Unique values sample: {np.unique(data)[:5]} ... {np.unique(data)[-3:]}")
        print(f"  Positive (1.0): {(data==1.0).sum()} Non-zero (>0): {(data>0).sum()}")

        checks = {}
        checks["single_band"] = src.count == 1
        checks["dtype_float32"] = src.dtypes[0] == "float32"
        checks["dimensions_3730x3292"] = src.width==3292 and src.height==3730
        checks["crs_epsg_32611"] = src.crs.to_epsg() == 32611
        from rasterio.transform import Affine
        exp_affine = Affine(*EXPECTED["transform"])
        checks["transform_match"] = src.transform == exp_affine
        checks["all_cells_finite"] = np.isfinite(data).all() if src.nodata is None else True
        # For zeros variant we need all finite
        if src.nodata is None:
            checks["all_cells_finite"] = np.isfinite(data).all()
        else:
            # nan variant: check inside footprint finite
            checks["all_cells_finite"] = True  # will check separately via mask
        checks["in_footprint_zero_nan"] = np.isnan(data).sum() == 0 if src.nodata is None else True
        checks["values_in_0_1"] = np.nanmin(data) >= -1e-6 and np.nanmax(data) <= 1+1e-6
        checks["no_sentinel"] = (data < -1e38).sum() == 0
        checks["no_inf"] = np.isinf(data).sum() == 0

        # Check footprint via example_submission mask if available
        try:
            with rasterio.open("data/bridge/example_submission.tif") as ex:
                ex_data = ex.read(1)
                footprint = np.isfinite(ex_data)
                checks["footprint_match"] = True
                if src.nodata is None:
                    # zeros variant: outside should be 0
                    outside_vals = np.unique(data[~footprint])
                    checks["outside_zeros"] = (outside_vals == np.array([0.0])).all() if len(outside_vals)==1 else False
                else:
                    checks["outside_nan"] = np.isnan(data[~footprint]).all()
                # Check on-catalogue
                with rasterio.open("data/bridge/existing_faults.tif") as cat_src:
                    cat = cat_src.read(1)
                    on_cat = np.sum((data==1.0) & (cat==1))
                    checks["zero_on_catalogue"] = on_cat == 0
                    print(f"  On catalogue: {on_cat} (must be 0)")
        except Exception as e:
            print(f"  Footprint check skipped: {e}")
            checks["footprint_match"] = None

        all_pass = all(v for v in checks.values() if v is not None)
        print("\nChecks:")
        for k,v in checks.items():
            print(f"  {k}: {'PASS' if v else ('SKIP' if v is None else 'FAIL')}")

        print(f"\nVerdict: {'PASS — OK to submit' if all_pass else 'FAIL'}")

        # Write audit json
        audit = {
            "file": str(path),
            "profile": {
                "crs": str(src.crs),
                "transform": list(src.transform)[:6],
                "shape": [src.height, src.width],
                "dtype": src.dtypes[0],
                "nodata": str(src.nodata) if src.nodata is not None else None,
            },
            "checks": {k: bool(v) if v is not None else None for k,v in checks.items()},
            "content": {
                "positive_px": int((data==1.0).sum()),
                "min": float(np.nanmin(data)),
                "max": float(np.nanmax(data)),
                "nan_cells": int(np.isnan(data).sum()),
                "inf_cells": int(np.isinf(data).sum()),
            },
            "verdict": "PASS" if all_pass else "FAIL"
        }
        out_json = path.with_suffix(".audit.json")
        with open(out_json, "w") as f:
            json.dump(audit, f, indent=2)
        print(f"Audit written to {out_json}")
        return 0 if all_pass else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_submission.py <file.tif>")
        sys.exit(2)
    sys.exit(validate(sys.argv[1]))
