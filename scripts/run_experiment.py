#!/usr/bin/env python3
"""Execute pre-registered GEMSDOE70 Experiments 2 (H70-2) and 3 (H70-3)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

from gems70.pipeline import run_all


def main() -> int:
    card = run_all(ROOT)
    print(json.dumps({
        "verdict": card["verdict"],
        "submission_name": card["submission_name"],
        "raster_sha256": card["raster_sha256"],
        "zip_sha256": card["zip_sha256"],
        "dots": card["correlation_overlap_vs_registry"]["final_dots"]["my_dots"],
        "seed70_dti": card["holdout"]["dti"],
        "seed70_ci95": card["holdout"]["ci95"],
        "seed20_dti": card["holdout"]["historical_seed20_cross_check"]["dti"],
        "genuine_sparse_worst_overlap": card["correlation_overlap_vs_registry"]["final_dots"]["genuine_sparse_worst_forward_overlap"],
        "genuine_sparse_worst_submission": card["correlation_overlap_vs_registry"]["final_dots"]["genuine_sparse_worst_submission"],
        "worst_spearman": card["correlation_overlap_vs_registry"]["final_dots"]["worst_spearman_full_footprint"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
