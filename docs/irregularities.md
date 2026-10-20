# Limitations and current next steps

## P5 addendum — new, format-valid research TIFF; competition submit NO

**Download P5 for research:** [TIFF](downloads/gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT.tif)
· [machine-readable negative card](downloads/p5_run_card.json). The preregistered one-lane
magnetic-width LOQO model ran after the older archive review, with one new TIFF and no weekly
slot. Its catalogue HOLDOUT-DTI (`gems57-pooled-hide-v2`, 11,321 withheld positives) was
0.012262 [0.007525, 0.017653] versus visible-only P4 0.073042; SGMC-proxy HOLDOUT-DTI
(same evaluator, 59,937 proxy positives) was 0.025424 [0.018528, 0.033629] versus H33 0.093771.
Neither is an organizer score. The literal forward 3-px stop still applies: the continuous
surface's positive cells are all within 3 px of the hash-pinned lattice. Zero exact-one binary
dots is NOT a waiver. Do not submit P5 or any previous file. The older review card is frozen
and describes what was true *at its own time*, not this later experiment. Read the full
[three-pass P5 review](https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/reports/p5-scientific-review.md).

## Current blocker: literal forward-overlap stop

**Do not submit the published files.** They remain available for forensic review only.
The fresh [protocol review](protocol-review.html) supersedes prior mutual-overlap promotion logic,
not the frozen experimental measurements. All dot TIFFs in that archived review have forward overlap 1.0
against the hash-verified binary lattice. This exceeds the prompt's 0.70 stop rule even though
rank correlation and mutual overlap are small. That prior review generated no new dot candidate;
the separate P5 continuous research map above is also blocked by positive-support overlap.

The inherited assertion that three lattice halos cover 100% of the footprint was not established.
The re-fetched `calib_r13lattice_00904.tif` covers 99.871327%, with 6,649 uncovered cells. This
still blocks the fixed 37,654-dot design (minimum overlap 0.82341849), but does not prove a universal
block at every mass. The archived mutual-rule receipts have not been rewritten to conceal this error.

## Other irregularities

- The current prompt specifies a single-method lane paragraph but supplies none identifiable.
  P5 explicitly declared a **provisional** narrow magnetic-width lane and did not claim an
  assigned slot. The previous handoff's supervised within-halo plan was tested only in this
  restricted form; other feature families remain untested and no promotion was inferred.
- No authenticated submission-page score receipt exists. H33's reported 0.2778 is user-supplied;
  historical public leaderboard captures are not receipts for our own submissions. Conflicting
  leader values in the brief are not current verified targets.
- Local format validity is not portal acceptance. The frozen reviewed TIFFs are single-band float32,
  finite in [0,1], and match the pinned sample's CRS, shape and transform. The rejected upload's
  exact error cannot be diagnosed without its bytes. The footprint-zero policy differs from a
  historical problem-page null/NaN quotation; organizer behavior has not been independently confirmed.
- The owner-mirror sample has 60,988 positive known-fault pixels, not an all-zero reference.
  It supplies grid geometry and footprint only, never hidden validation labels. Owner-mirror hashes
  establish integrity, not organizer authenticity or every license condition.
- Catalogue recovery and SGMC proxy recovery are different populations. SGMC/QFaults re-digitization
  overlap can persist outside a narrow exclusion band. Neither is the organizer's hidden truth.
  A holdout win is not a forecast of leaderboard improvement.
- P4 was already negative on the preregistered B′ proxy gate; E2 did not beat its D28 holdout arm.
  These frozen results stay negative regardless of the uniqueness issue.
- The historical handoff's claim that geometry has reached its limit is not a theorem. Neither
  the remaining leaderboard gap nor a guaranteed route to beating it can be inferred from three
  experiments.
- `scripts/prepare_data.py` from the retained prompt is absent. Data placement is not the sole
  blocker to training/validation. The official reference supports CPU as well as GPU; GPU is
  preferred for speed, not an absolute requirement.
- Only GitHub, npm and PyPI hosts are allowed for shell binary downloads. This P5 session read
  public DrivenData/USGS/GDR/DOE text through the page reader (see the dated
  `evidence/p5/official_source_review.json`), but did **not** obtain organizer-authenticated
  data, an accepted submission receipt, or the current authenticated weekly balance. No
  competition slot was spent. The site links to the live official leaderboard and displays a
  dated snapshot, **not an automatic authenticated live score feed**. The scheduled source-health
  check tests HTTP reachability only; implementing a verifiable auto-refresh remains open.

## Next session, in order

1. Read the retained brief, current protocol review and new handoff note first. Do not bypass the
   literal stop by invoking an old generator or a mutual-overlap rule. Resolve any protocol revision
   explicitly before attempting another fixed-mass candidate. A different mass is a new preregistration,
   not an automatic exemption or a reason to target only boundary slivers.
2. Quantify SGMC versus QFaults overlap across buffers and spatial quadrants. Review independent
   official fault data, licensing and obtainability before treating it as new truth.
3. P5 already tested one LOQO magnetic-width residual and failed both holdouts. If a revised
   protocol permits further experiments, test a geology-conditioned, geometry-preserving
   emission at a **matched mass and spacing** under nested blocked validation; recompute all
   catalogue geometry from visible faults and run every raw/derived feature-alone canary.
   Do not tune the frozen P5 result or relabel this failed continuous map as a dot-unique file.
4. Rerun the current-best baseline on identical folds and mass. Keep HOLDOUT-DTI, SGMC PROXY-DTI
   and any eventual ORGANIZER-CONFIRMED receipt separate. A negative remains a deliverable.
5. Only a separate selector can approve a real weekly slot after all gates and the live cap are
   checked. Save its authenticated submission-page receipt before reporting an organizer score.

## Publication and reproducibility

* `docs/downloads/` contains several independently hash-inventoried review TIFF/ZIP pairs,
  including this P5-cover file and the concurrent E5/P5 analytic lanes. No file is approved
  for a weekly slot; `release.assert_no_public_rasters` rejects unlisted files and symlinks.
* Large inputs (`training_features.tif`, the registry clone) live outside Git; restore commands are
  in the README. Published evidence is small JSON.
* The older dot TIFFs are binary 0/1; P5-cover is a continuous [0,1) review map. All have
  all-finite zeros outside the footprint and no nodata tag. The shared local validator passes;
  organizer acceptance of this policy remains unverified.

## Parallel-session candidate (merged 2026-10-20)

A concurrent branch added `gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif`
(24,872 binary dots, sha256 recorded in `registry/published_artifacts.json`, verdict
`DO NOT SUBMIT` in its own receipts). It is preserved and inventoried but is not the file this
older run card selected; the current landing page now leads with the P5-cover research file,
then the concurrent supervised and dot archives. Both files are hash-pinned by
`release.assert_no_public_rasters`, so neither can be silently replaced. Its narrative pages were
moved to `reports/archive/concurrent-v2/` to avoid two contradictory download instructions in the
published tree.

## Parallel E2/E3 lane (integrated PR #16, 2026-10-20)
- E2 alluvial-step and E3 depth-step are additional negatives (see `docs/preregistration-e2.md`, `evidence/e2|e3/`). E2 bytes are published for selector review under `docs/publication-amendment-e2.md`; submit remains NO. E2 uniqueness used pre-fix R1 subset definitions — not directly comparable to the corrected 62-raster mutual audit until rerun.
- Bridge `sample_submission.tif` positives are exactly the catalogue (60,988 px), not an all-zero sample; footprint use only. Two-round expanded-label composition and known-fault masking remain unverified from fetched organizer text.

## E5 supervised lane (2026-10-20)
- E5 executed the registered next step (SGMC-proxy LOQO ranking) and is a
  measured negative on the frozen B′ gate: Δ −0.0051 [−0.0161, +0.0053] vs H33
  (`evidence/e5/run_card.json`). Artifact published review-only; submit NO.
- Emission Amendment 1: P4's one-per-block pass cannot reach 37,654 dots on a
  sharp supervised surface (34,409 measured). Same-NMS fill added before any
  DTI existed; disclosed in `docs/preregistration-e5.md`. P4 bytes unaffected.
- New information: OOF AUC 0.69–0.78 (real within-halo signal) does not
  convert to B′ DTI above uniform halo sampling at this dot budget — the
  remaining gap to the 0.4413 public leader is not explained by 100 m
  potential-field/topography ranking of the SGMC proxy. Candidate queues:
  radiometric/lidar feature sets (E5-3/E5-4, obtainability unchecked), finer
  (sub-100 m) emission geometry, or a genuinely independent additional-fault
  truth set to replace the SGMC proxy.
- E5 canary context defect (found in review, corrected post-hoc): the primary
  canary table computed `d_cat` against the full catalogue, giving
  Instrument-A AUC 0.0 by construction (A positives are catalogue pixels).
  Prediction-time folds always used visible-only distance; its corrected
  canary AUC is 0.245 (`evidence/e5/canaries_correction.json`). No leakage;
  frozen receipts and artifact unchanged.
All inventoried TIFF/ZIP bytes are preserved; none was renamed or reused as a new submission.
Publication inventory and Pages guards still reject unauthorized rasters or symlinks. Current
review evidence lives in `evidence/review/`; Phase 1–4, E2/E3 and historical cards remain frozen.
The shared metric, evaluator, writer and vendored uniqueness bytes were not modified in this review.
The new policy adapter acts only on existing shared measurements and restores the current prompt's
literal decision rule. P5 uses the same shared evaluator/writer and a separate hash-pinned research
artifact; it did not change the shared metric or its threshold. See the
[scientific review](https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/reports/p5-scientific-review.md)
for new source receipts, a failed controlled test and reproducible commands.

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
