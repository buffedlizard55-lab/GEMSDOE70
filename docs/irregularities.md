# Limitations, irregularities and next-session work

## Current protocol status — 2026-10-20

The active request requires a stop if any checked registry raster has Spearman > 0.90 **or** more
than 70% of candidate dots within 3 px. The archived Phase-4 final-dot audit has four one-way
witnesses in the 62-raster accessible inventory; maximum forward overlap is 1.00. This is a
REGISTRY-MEASUREMENT, not a competition score, and the inventory is not exhaustive. The historical
mutual-overlap clearance does not satisfy the current prompt.

The archived Phase-4 TIFF is downloadable for review only; **do not submit it**. The current review
generated no new candidate surface or TIFF, ran no experiment, did not recompute holdout, and used no
weekly slot. A surface-stage check was not run and is not claimed to pass. See
`evidence/literal_protocol_review.json` and `reports/literal-protocol-review.md`.

## Archived HOLDOUT-DTI evidence (not organizer scores)

The archived receipts use evaluator `gems57-pooled-hide-v2`; none was recomputed in the current
review. Instrument A withholds catalogue components. Instrument B′ uses SGMC-derived proxy positives,
not organizer hidden truth.

- Instrument A candidate: **HOLDOUT-DTI 0.0730**, 95% CI [0.0667, 0.0790], 11,321 withheld catalogue-positive pixels.
- Instrument B′ candidate: **HOLDOUT-DTI 0.0812**, 95% CI [0.0723, 0.0900], 59,937 withheld proxy-positive pixels.
- Paired B′ candidate-minus-H33 difference: **HOLDOUT-DTI Δ −0.0126**, 95% CI [−0.0241, −0.0018], 59,937 withheld proxy-positive pixels.

The B′ promotion gate was negative. These are internal holdout measurements, not ORGANIZER-CONFIRMED
scores. The user-supplied historical 0.2778 has no submission-page receipt in this repository.

## Historical shared-tool changes and current-rule distinction

The prior Phase-4 work fixed two defects in the pinned `vendor/gems57` uniqueness code and recorded
the modified hashes with `all_identical: false` in `registry/template_pin.json`:

1. Dots are binary (`|value − 1| < 1e-6`), rather than every finite positive raster value.
2. The shared tool's historical duplicate calculation uses mutual overlap, reporting both directions.

The mutual-overlap choice was made after archived dense lattices showed that their 3-px halo covered
the footprint. That is a representation/design concern, not proof that predictions are geologically
identical. However, the active user prompt explicitly specifies a one-way forward-overlap stop. That
stricter literal rule governs this review. No private metric fork or discretionary exemption was
made. Any protocol change must be explicitly authorized and versioned; the shared template changes
still need to be proposed upstream.

## Data, source and novelty limitations

- The feature cache is absent; `data/bridge/` holds only bridge/sample rasters, not the restored
  training stack. No new data bytes were restored or verified in this review.
- The SGMC-derived proxy appears in the pinned manifest but is omitted from
  `scripts/fetch_data.py`'s default `WANT` list. A future restore must explicitly request, hash and
  record it before any proxy experiment.
- The mirrors are GitHub-hosted owner copies, not authenticated organizer downloads or official
  provenance. Official DrivenData, USGS and DOE pages were not freshly fetched because their hosts
  are outside the sandbox allowlist. Manual-review links are on `docs/sources.html` and in the
  current review; no current leaderboard or weekly-cap status is claimed.
- Parallel work overlaps with proposed lanes: GEMSDOE72 describes SGMC off-catalogue emission,
  GEMSDOE66 has CV-retrained relief/scarp artifacts, and GEMSDOE71 describes hydrothermal/thermal
  work. These are sibling-repository claims, not independent scientific verification. Do not call a
  method globally unique without a complete registry and method-level comparison.
- The current report lists three unvalidated cache-based hypotheses. The top proposal was not tested:
  the literal stop is active and no single current method paragraph assigns this session a lane.

## Next-session priorities

1. Resolve the literal one-way protocol conflict with the selector; record any approved change as a
   new protocol version. Do not silently reuse the historical mutual-overlap clearance.
2. Assign one method lane and compare its exact method against this repo and sibling projects before
   touching data or experiment budget. Do not restart the overlapping supervised SGMC lane by
   default.
3. Only after authorization and lane assignment, restore and hash the cached stack and SGMC proxy;
   correct the fetch `WANT` omission in the shared template rather than a private fork.
4. For an authorized method, run each feature-alone leakage canary, then whole-segment spatially
   blocked holdout with a buffer and pixel-exact visible-fault mask. Preserve evaluator, positive
   count and 95% CI on every HOLDOUT-DTI.
5. Check surface uniqueness before placement and final-dot uniqueness after placement; stop on the
   first literal witness. Compare the top candidate to the current best on the identical split.
6. Keep promotion separate: do not use a weekly slot unless a separately cleared candidate beats
   the current HOLDOUT-DTI best and the selector approves it. Record ORGANIZER-CONFIRMED only from a
   submission-page receipt.

## Published artifacts and their status

- `gems70-p4-stratified-halo-37654-20261020.tif`: historical Phase-4 file; format/range receipt is
  archived, but the current literal final-dot gate fails. Review download only; do not submit.
- `gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif`: parallel E2 result,
  selector-review only; a complete current literal uniqueness scan is pending. Do not submit.
- `gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif`: parallel negative artifact with its own
  DO NOT SUBMIT receipt; no current literal clearance is asserted.
- `gems70-stepperamp-relay-diagnostic-BLOCKED-DO-NOT-SUBMIT.tif`: blocked diagnostic only, not a
  candidate submission.

All inventoried files remain hash-pinned in `registry/published_artifacts.json`. A local format pass
never establishes uniqueness, scientific improvement, organizer acceptance, or slot eligibility.

## Official links for manual review

- [DrivenData competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and
  [submission data/format](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391)
- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)

These official pages are included for manual review, not represented as freshly verified in this
sandbox.
