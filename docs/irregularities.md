# Limitations, irregularities and next-session work

## Two shared-tool defects were found and fixed this session

1. **Dot definition.** `uniqueness._dots` counted every finite positive value as a dot, so any
   nonempty candidate "duplicated" the archived continuous surface `E-proba-multiscale`
   (sha256 `ab0a0a62…`, positive on all 5,167,373 footprint cells). Fixed to binary dots
   (`|value − 1| < 1e-6`). Reported in `evidence/upstream_fix_report.md`.
2. **Forward-only overlap.** A duplicate must coincide in both directions. Measuring this session:
   `calib_r13lattice_00904` (206,895 dots), `r11_greedy_mp` (272,853) and
   `calib_hedgev2_01563_sample` (227,507) each have a 3-px halo covering **100 %** of the footprint,
   so forward-only overlap is 1.00 for *any* nonempty candidate. The gate now requires
   `min(forward, reverse) > 0.70`; both directions and Jaccard are always reported, ρ > 0.90 still
   applies to every raster, and no threshold was changed. Three archived submissions — not one —
   triggered the old rule, which is why this is a representation defect rather than duplication.

Both fixes are in `vendor/gems57/uniqueness.py`; `registry/template_pin.json` records the new hash
with `all_identical: false`. They must be proposed upstream to the shared template.

## What is not established

* **No organizer receipt.** 0.2778 and 0.44 are user-supplied historical values. No score on this
  site is ORGANIZER-CONFIRMED. The portal was not reachable from this sandbox.
* **Neither instrument is the hidden truth.** Instrument A withholds catalogue components (measures
  catalogue recovery, biased against the task). Instrument B/B′ uses SGMC faults minus the
  catalogue (an independent state compilation, but partially a re-drawing of the same traces).
  They disagree, and the disagreement is reported rather than averaged.
* **The candidate is not promoted.** On B′, H33 wins by 13 % with a CI excluding zero. The
  pre-registered rule therefore returns `negative`, even though instrument A and unrestricted B
  favour the candidate.
* **Registry scope.** Uniqueness was checked against the 62 single-band 100 m rasters archived in
  `buffedlizard55-lab/60GEMSDOE/registry/rasters`, not against every private or uncommitted file.
  Zero Spearman exceedances (max 0.05) and zero mutual-overlap exceedances were found.
* **Geophysical fields are weak.** Feature-alone AUCs on withheld catalogue segments were
  0.46–0.57. The four-field gate hurt both instruments and was removed after Experiment 2; this is
  recorded, not hidden.

## Next session, in priority order

1. **Supervised within-halo ranking.** Train on the SGMC-off-catalogue proxy with leave-one-quadrant-out;
   features: 19-band stack, lidar-scarp (12 bands), GeoDAWN radiometrics (K/Th/U/TC and ratios),
   catalogue geometry (distance, side, host length, tip position), plus the measured coverage
   stratification. Report A and B′ with the same bootstrap. This is the only path with information
   the geometry does not already contain.
2. **Calibrate the proxy.** Quantify how much of SGMC-only support is a re-drawing of QFaults
   (buffer tests at 1–6 px) and, if possible, obtain a genuinely independent additional-fault set
   (e.g. Nevada Bureau of Mines county maps, published INGENIOUS trace exports).
3. **Upstream the two uniqueness fixes** as a PR to the shared template and re-run its test suite.
4. **Selector step.** If a future candidate clears both gates, promote one slot within the weekly
   cap and record the returned score as ORGANIZER-CONFIRMED.

## Repository-level risks

* `docs/downloads/` now contains exactly one TIFF/ZIP pair, authorised by the run card;
  `release.assert_no_public_rasters` rejects anything else, including symlinks.
* Large inputs (`training_features.tif`, the registry clone) live outside Git; restore commands are
  in the README. Published evidence is small JSON.
* The published TIFF is binary 0/1 with no nodata tag; outside-footprint cells are 0, which the
  shared validator and the sample comparison both accept.

## Parallel-session candidate (merged 2026-10-20)

A concurrent branch added `gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif`
(24,872 binary dots, sha256 recorded in `registry/published_artifacts.json`, verdict
`DO NOT SUBMIT` in its own receipts). It is preserved and inventoried but is not the file this
run card selects; the landing page points only at the P4 artifact. Both files are hash-pinned by
`release.assert_no_public_rasters`, so neither can be silently replaced. Its narrative pages were
moved to `reports/archive/concurrent-v2/` to avoid two contradictory download instructions in the
published tree.
