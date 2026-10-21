# Explicit Three-Pass Engineering & Scientific Verification Log (`GEMSDOE70`)

## Pass 1 — Full End-to-End Implementation, Checksummed Data Restoration & Execution Verification
- Restored and SHA-256 verified all `16 / 16` competition raster/vector/metadata inputs via `scripts/restore_data.py` (`codeload.github.com` mirror pins, zero GitHub API quota burn) and verified byte-for-byte identity of `vendor/gems57` (`8 / 8` files @ `3202471`).
- Downloaded and SHA-256 verified all `931` unique GeoTIFF rasters across all `84 / 84` accessible `buffedlizard55-lab` repositories (`0` errors).
- Pre-registered hypotheses `H70-1`..`H70-5` in `docs/hypotheses.md` (`SHA-256: 6b9a85b5a0309a6d1aab0f03ed69ee21755ee9943bece89b9b842693c2f6aa65`), archiving negative `H70-1` (`0.010193` on `seed=20`, `0.013028` on `seed=70`) cleanly in `evidence/history/experiment1_contact_termination/`.
- Implemented `src/gems70/{features,models,pipeline}.py` and ran `scripts/run_experiment.py` end-to-end across both primary untouched `seed=70` (`11,387` withheld positive pixels) and historical `seed=20` (`11,321` withheld positive pixels).

## Pass 2 — Active Bug Hunting, Spatial Diagnostics & Edge-Case Elimination
- **Caught & Fixed `IR-70-EMIT-BLOB-01` (`vendor/gems57/emit.py::greedy_allocate`):** Clamping `kself = minimum(ek, 1.0)` zeros out `1 - kself` on high-probability ridges, collapsing emission to `1-px` blobs (`HOLDOUT-DTI = 0.042181` on `seed=70`). Replaced upstream-cleanly with exact CELF submodular marginal-DTI allocation (`0.132781` on `seed=70`, **`+3.15x`**).
- **Caught & Fixed `IR-70-QUADRANT-DRIFT-01` (Pass-2 spatial audit of `evidence/submission_diagnostics.json`):** Discovered that unclamped regional `gdr_*` thermal distances (`0–250 km`) + unstratified LOQO base rates concentrated `76.3%` (`31,644 / 41,500`) of dots into `NW` at `2.24 px` knight's-move spacing (`halo_cov = 0.0909`). Fixed by clamping thermal conduction radii to `2.5–3.0 km` (`25–30 px`), stratifying calibration jointly across `(quadrant × relief-decile)`, and enforcing circular `d >= sqrt(8) = 2.828 px` spacing:
  - `seed=70` jumped to **`0.132781`** (`95% CI [0.116736, 0.151010]`, `+10.19x` over `E1`, `+4.01x` over `G49`);
  - `seed=20` jumped to **`0.115152`** (`95% CI [0.096008, 0.135342]`, `+11.30x` over `E1`, `+3.51x` over `G49`);
  - `median NN spacing` hit **`3.0000 px` (`300.0 m`)** exact (`26,930` naturally terminated submodular vertices);
  - Worst 3-px forward overlap across all `730` sparse registry submissions dropped from `0.6939` to **`0.6503 <= 0.7000`** (`0` duplicate firings).
- **Caught & Fixed `IR-70-COVERING-CODE-01`, `IR-70-COLLAR-LEAK-01`, `IR-70-WRITER-MODE-01` (`0600 -> 0644`), and `IR-70-NODATA-SENTINEL-01` (`-3.4028235e+38`).**
- **Caught & Fixed `submission_paths['zip']` / `genuine_sparse_worst_forward_overlap` key bindings** when exercising `scripts/release_gate.py` and `scripts/build_site.py`.

## Pass 3 — Complete Independent Audit Against Every Prompt Requirement & Git Contract
- Verified independent byte-level check of `docs/downloads/gemsdoe70-h70-3-dual-expert-submodular-20261020T223000Z.tif` (`SHA-256: e035d29e3c4e8a0dabd807b6bedfc9373216fa03f523b441cba5113420864650`) and `.zip` (`SHA-256: fbc36dd38ec3c88a8bc7697217348efcb75e91451260c5dbecf7d0233a95f595`): single-band `float32`, `EPSG:32611`, `(3730, 3292)`, exact `sample_submission.tif` geotransform, values strictly `{0.0, 1.0}`, `0` NaN/Inf inside or outside footprint, `0` catalogue pixels, `119 <= 140`-char submission note.
- Verified `100%` of `70 / 70` automated pytest assertions (`test_audit.py`, `test_contract.py`, `test_evidence.py`, `test_metric.py`, `test_quarantine.py`, `test_shared_tools.py`, `test_site.py`, `test_writer.py`, `test_writer_legacy.py`), zero broken links across all HTML pages, zero simulated scores, and 100% verbatim retention of `PROJECT_BRIEF.md` inside `README.md`.
