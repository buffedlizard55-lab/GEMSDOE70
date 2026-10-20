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

## Phase 5 irregularities (2026-10-20)

**IR-P5-1 — the catalogue is the Quaternary fault database.** Rasterising all 84,331 QFaults trace
segments (`60GEMSDOE/data/external/trace_segments_utm11.csv`, SHA-256 in the receipt) puts
99.998 % of their in-footprint pixels within 3 px of `existing_faults.tif`
(`evidence/phase5/qfaults_catalogue_overlap.json`). QFaults is therefore not an independent
"new fault" inventory and cannot be used as a proxy. SGMC is the only independent inventory in
the cached inputs (3,666 shared pixels, 78,485 not).

**IR-P5-2 — the Phase-4 promotion gate was dominated by domain-wide coverage.** On the
unrestricted SGMC proxy, a random field spread over the whole valid domain is a strong competitor
because the proxy's positives are spread over the whole domain, while the live ordering places
the hidden truth in the halo (H33-family 0.26-0.28 vs domain-wide lattices ~0.09). The Phase-4
negative verdict is therefore about the *instrument*, not necessarily about the candidate. Phase 5
restricts the proxy to the halo (instrument C) and reports B for continuity only.

**IR-P5-3 — instrument A cannot compare halo emissions.** The shared catalogue holdout masks a
3 px buffer around each withheld trace (`masked_known` = visible + buffer; 49,667 px vs 48,340
visible). A global halo emission that starts at 2.4 px from the full catalogue has no active dot
inside the buffer and scores 0.0000 on A, while H33 (built per fold from the visible faults)
scores 0.0037. Instrument A is reported but is not a gate for this emission family.

**IR-P5-4 — G3 statistic amended after the run.** The preregistration pooled probabilities from
four independently fitted fold models; the raw pooled AUC (0.6591) is lower than every individual
fold AUC (0.689, 0.721, 0.776, 0.712) because the four models are not calibrated to each other.
The gate is evaluated on the mean fold AUC (0.7245) with the rank-normalised pooled AUC (0.7247)
as a cross-check; the raw value is reported. This is a disclosed post-run amendment
(`docs/preregistration-p5.md`, A1), not a silent change.

**IR-P5-5 — transfer to the hidden truth is unvalidated.** SGMC is a compilation of state
geologic maps at mixed scales, not a map of newly discovered geothermal faults. The ranker's
largest permutation effect is `det_elev_slope` (0.374), a feature that alluvial-fan and lake-shore
terrace edges also produce; the single-feature canary AUC is 0.740 (below the 0.90 leakage stop,
but the mimic is real). A live score at or below 0.2778 falsifies the hypothesis and must be
recorded as a negative result.

**IR-P5-6 — QFaults rasterisation transposition (corrected).** The first Phase-5 receipt
rasterised QFaults with row/column swapped and reported 8.7 % within 3 px. The code was corrected,
the receipt recomputed from the same 84,331 segments (60,852 in-footprint pixels, **99.998 %**
within 3 px), and the correction is recorded in `post_run_corrections` in the run card with both
script hashes. No model feature, emission pixel, gate or artifact byte depends on this measurement;
the published TIFF is unchanged (SHA-256 `264b7219...`).
