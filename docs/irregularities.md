# Limitations, irregularities and next-session work

## Session 3 (2026-10-20): the supervised route measured to its ceiling

Experiment 5 (H-P5-1, preregistered in `docs/hypotheses.md`) trained a HistGradientBoosting
classifier on the SGMC off-catalogue proxy (leave-one-quadrant-out) over the 19-band stack plus
visible-catalogue geometry. **Verdict: negative.** The model learns the proxy (out-of-fold AUC
0.641) but the emitted dots score B′ 0.0793 [0.0716, 0.0879] versus H33 0.0938 and P4 0.0812 —
H33 wins the pre-registered gate (Δ −0.0145, CI [−0.0243, −0.0039]) and the candidate is
statistically indistinguishable from the pure-geometry P4 halo (Δ −0.0019, CI [−0.0060,
+0.0024]). **The ceiling is the label source, not the learner.** Two implementation events are
disclosed rather than hidden:

1. **Emission amendment (pre-score).** The registered stratified emission fell 3,067 dots short of
   the fixed 37,654 mass on the spikier model surface (NMS collisions). Pass 2 of
   `method_v5.stratified_dots` tops up from the best NMS-feasible *positive-score* cell of empty
   strata; pass 1 remains byte-identical to Phase-4 (unit-tested). Amendment written into
   `docs/hypotheses.md` before any DTI was computed.
2. **Writer-caught defect.** The first top-up implementation walked onto zero-score cells and
   placed dots **on the mapped catalogue**; the shared writer rejected the artifact
   (`positive prediction mass on the mapped catalogue`) before anything was published. Fixed with a
   regression test (`test_stratified_dots_topup_never_uses_zero_score_cells`). This is the release
   contract working as designed.

**New measured facts:** 31.9 % of instrument-A truth pixels lie within 3 px of proxy pixels (the
SGMC re-draw contamination channel, now quantified); 63.7 % of B′ truth lies inside the 32-px halo
band (the band caps reachable truth); worst feature AUC vs A-truth 0.565 (no leakage canary); the
score surface cleared the 62-raster Spearman pre-check at ρ 0.096 and the final dots at mutual
overlap 0.301 / ρ 0.015.

## Revised next-session priorities (in order)

1. **Independent truth source.** The SGMC proxy is now measured as the bottleneck. Quantify how
   much of SGMC-only support re-draws QFaults (buffer tests 1–6 px), then obtain a genuinely
   independent additional-fault set (Nevada Bureau of Mines county maps, published INGENIOUS trace
   exports) before any further supervised attempt.
2. **Band widening.** 36.3 % of B′ truth lies beyond 32 px from the catalogue. A registered
   experiment widening D_MAX (48/64 px) at fixed mass with the same stratified emission could
   recover out-of-band truth; uniqueness must be re-checked (a wider domain raises exposure to the
   dense lattice rasters).
3. **Mass calibration.** Every fixed-mass family member clusters at B′ 0.08–0.09. A registered
   dot-count sweep (e.g. 25k / 37k / 50k) on the existing surface, scored only on B′ LOQO, would
   measure the mass response without new modelling.
4. **Upstream the two uniqueness fixes** to the shared template and run its suite (still pending
   from session 2).
5. **Selector step unchanged.** No weekly slot has been used by any session of this repository.

## Repository-contract change this session (not a template change)

`src/gems70/release.py` now reads the canonical `evidence/run_card.json` and resolves its phase
receipts through the card's `phase_evidence` mapping (dot count from the card instead of a
hard-coded 37,654). Fail-closed semantics are unchanged and covered by the same tests.

## Two shared-tool defects were found and fixed (session 2)

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
