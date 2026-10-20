# Limitations and current next steps

## Current blocker: literal forward-overlap stop

**Do not submit the published files.** They remain available for forensic review only.
The fresh [protocol review](protocol-review.html) supersedes prior mutual-overlap promotion logic,
not the frozen experimental measurements. All six archived final TIFFs have forward overlap 1.0
against the hash-verified binary lattice. This exceeds the prompt's 0.70 stop rule even though
rank correlation and mutual overlap are small. No new candidate was generated after the stop.

The inherited assertion that three lattice halos cover 100% of the footprint was not established.
The re-fetched `calib_r13lattice_00904.tif` covers 99.871327%, with 6,649 uncovered cells. This
still blocks the fixed 37,654-dot design (minimum overlap 0.82341849), but does not prove a universal
block at every mass. The archived mutual-rule receipts have not been rewritten to conceal this error.

## Other irregularities

- The current prompt specifies a single-method lane paragraph but supplies none identifiable.
  The previous handoff's supervised within-halo ranking was deferred, not silently replaced.
- No authenticated submission-page score receipt exists. H33's reported 0.2778 is user-supplied;
  historical public leaderboard captures are not receipts for our own submissions. Conflicting
  leader values in the brief are not current verified targets.
- Local format validity is not portal acceptance. All six re-read TIFFs are single-band float32,
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
- Only GitHub, npm and PyPI hosts are allowed for outbound traffic in this session. The organizer
  reference README/notebook were re-fetched on GitHub; other official pages and the current
  authenticated slot cap were not re-verified. No competition slot was spent.

## Next session, in order

1. Read the retained brief, current protocol review and new handoff note first. Do not bypass the
   literal stop by invoking an old generator or a mutual-overlap rule. Resolve any protocol revision
   explicitly before attempting another fixed-mass candidate. A different mass is a new preregistration,
   not an automatic exemption or a reason to target only boundary slivers.
2. Quantify SGMC versus QFaults overlap across buffers and spatial quadrants. Review independent
   official fault data, licensing and obtainability before treating it as new truth.
3. If the protocol permits it, validate the ranked residual within-halo model with train-only
   preprocessing, buffered leave-one-quadrant-out and the shared evaluator. Recompute catalogue
   geometry only from visible faults and test every raw/derived feature alone for leakage.
4. Rerun the current-best baseline on identical folds and mass. Keep HOLDOUT-DTI, SGMC PROXY-DTI
   and any eventual ORGANIZER-CONFIRMED receipt separate. A negative remains a deliverable.
5. Only a separate selector can approve a real weekly slot after all gates and the live cap are
   checked. Save its authenticated submission-page receipt before reporting an organizer score.

## Publication and reproducibility

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
literal decision rule. See the review for sources, four proposed hypotheses and reproducible commands.
