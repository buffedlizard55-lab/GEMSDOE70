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

## Parallel E2/E3 lane (integrated PR #16, 2026-10-20)
- E2 alluvial-step and E3 depth-step are additional negatives (see `docs/preregistration-e2.md`, `evidence/e2|e3/`). E2 bytes are published for selector review under `docs/publication-amendment-e2.md`; submit remains NO. E2 uniqueness used pre-fix R1 subset definitions — not directly comparable to the corrected 62-raster mutual audit until rerun.
- Bridge `sample_submission.tif` positives are exactly the catalogue (60,988 px), not an all-zero sample; footprint use only. Two-round expanded-label composition and known-fault masking remain unverified from fetched organizer text.

## Session 3 (2026-10-20, branch arena/a0382202) — irregularities and limits

1. **Offline instruments are not calibrated to the live board** (most important). Spearman of
   reported live score vs B′ = −0.28 and vs A = −0.64 over 18 archived files
   (`evidence/s3/proxy_calibration.json`). No offline gate in this repo can currently justify a slot.
2. **Conservative post-hoc veto of S3-E1.** E1's frozen rule returned `promote`; it was overridden
   to `negative` after the calibration diagnostic. The veto can only block, never promote, and both
   the raw card (`evidence/s3/run_card_raw.json`) and final card are published.
3. **E2 design error, disclosed.** The pre-registered "E1 candidate (reference)" arm used the E1
   production file, which is in-sample on B′ (0.4614). It is annotated and used in no gate.
4. **H33 domain count.** 2,438 of H33's 37,654 dots fall outside the scored valid domain (12-px edge
   erosion or d < 2.4 px), so H33 is slightly handicapped on B′ against arms that place all dots
   in-domain. E2 therefore gates on random-within-strata as well.
5. **Name-matched scores.** Seven calibration rows take their live score from the user brief by
   repository file name only; byte identity to the scored upload is not authenticated.
6. **Same-lane siblings.** E1 and E2 have mutual 3-px overlap 0.80 with each other; at most one
   should ever be considered.
7. **Sandbox limits.** No DrivenData login and no network beyond GitHub/PyPI: organizer pages,
   SGMC/USGS originals and the GDR could not be re-fetched; all inputs are SHA-pinned owner mirrors.

### Next session, in priority order

1. **Build a live-calibrated instrument.** Pre-declare a small family of proxy definitions
   (SGMC-only by distance band; catalogue holdout stratified by `qfault_attributes.csv` age/slip
   class; truth subsampled to a fixed size), select the one whose ranking of the 18 scored files
   best matches the live board (leave-one-file-out), then re-test E2 and P4 on it.
2. **Test the opposite terrain hypothesis** (basin-floor LiDAR micro-scarps, `docs/hypotheses.md`
   Session-3 rank 2) only after step 1 exists.
3. **Upstream the two uniqueness fixes** to the shared template (still pending from session 2).
4. **Selector step.** Only a candidate that beats H33 on a live-calibrated instrument should use
   a weekly slot; record any returned score as ORGANIZER-CONFIRMED with the receipt.
