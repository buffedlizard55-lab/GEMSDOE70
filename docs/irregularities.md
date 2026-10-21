# Limitations and current next steps

## Session 3, P5-HGB lane (2026-10-20): the supervised route measured to its ceiling

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

## Lane P8 (`arena/c7049280-gemsdoe70`) — Two new spatial-learning pitfalls discovered & fixed (`IR-P5-1`, `IR-P5-2`)

In executing the 3-experiment progression (`evidence/p8_dual_submod300/`), fold diagnostics uncovered and resolved two general pitfalls for geospatial fault detection:

1. **`IR-P5-1` (Hide-mask / survey-completeness covariate shift from visible-catalogue features)**:
   In Run 1 (`evidence/p8_dual_submod300/run1_v50_run_card.json`), supplying visible-catalogue proximity features (`vis_dist_capped`, `vis_tip_lobe`, `vis_host_len_prox`) to `M_bed` caused trees to learn USGS mapping density rather than fault physics. On Instrument A (where connected components are hidden inside `fold['region']`), `d_vis` jumped inside `fold['region']`, starving all 4 test regions combined to only `9,007 / 37,654` (`23.9%`) of dots in `Exp 5B` (`verdict = negative`). Restricting **both** `M_neo` and `M_bed` strictly to the `38` catalogue-free physical sensor channels completely eliminated this shift.
2. **`IR-P5-2` (Cross-quadrant sample base-rate & regional background level shift)**:
   Holding out NE Nevada (`Quadrant 1`, containing ~48% of SGMC bedrock faults) while keeping `max_neg = 180,000` fixed reduced positive prior log-odds by `-0.46` relative to other folds, starving Quadrant 1 to `1,116 / 37,654` dots under global probability ranking despite strong within-quadrant discrimination (`0.182, 0.165, 0.154` on the other three quadrants). High-pass localizing regional background fields (`x - G_12(x)`) and rank-calibrating predictions strictly within each out-of-fold spatial partition (`rank01_domain`) resolved the imbalance across all 4 quadrants without touching any held-out label (`HOLDOUT-DTI A = 0.11129`, `PROXY-DTI B' = 0.13109`, `PROXY-DTI B'' = 0.11897`).
3. **Upstream verification receipt**: `vendor/gems57/uniqueness.py` (`sha256: 93726c6a...`) was tested directly inside an isolated clone of `buffedlizard55-lab/60GEMSDOE` (`commit 32024716`): **`190 passed, 8 skipped, 0 failed`** (`evidence/p8_dual_submod300/upstream_template_suite.json`, diff in `evidence/p8_dual_submod300/upstream_uniqueness_patch.diff`).
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

## E6 multi-modal extended-domain LOQO lane & completed selector audits (2026-10-20, `arena/effcd5f7-gemsdoe70`)

- **SGMC vs. QFaults buffer calibration ($r = 1\dots 6\text{ px}$, `evidence/e6/sgmc_buffer_audit.json`):**
  Off-catalogue SGMC shell enrichment is `3.83×` in `(0, 1]` px, `2.98×` in `(1, 2]` px, `1.86×` in `(2, 3]` px, `1.40×` in `(3, 4]` px, `1.14×` in `(4, 5]` px, and `0.97×` in `(5, 6]` px; `35.89%` of `SGMC B′` pixels lie at $d_{\text{cat}} > 32\text{ px}$.
- **Experiment E6 (`docs/downloads/gems70-e6-multimodal-extdomain-loqo-37654-20261020.tif`, sha256 `9b4f225f9656b1b3ab106750be431a4053e7ad804fe3bb9e2dac163d49601771`):**
  28-feature LOQO HGB across $d_{\text{cat}} \in [3.0, 96.0]\text{ px}$ with 7×7 regional coverage stratification (`37,654` binary dots) beats `H33` on `Instrument A` (`0.0710 vs 0.0037`) and `Instrument B′` (`0.1100 [0.1058, 0.1133] vs 0.0938 [0.0839, 0.1044]`, paired $\Delta = +0.0162$, 95% CI `[+0.0045, +0.0270]`), passes amended mutual-overlap uniqueness across all 62 registry rasters (`worst_mutual = 0.2960 <= 0.70`, `worst_nonlattice_forward = 0.3526 <= 0.70`, `worst_spearman = 0.0133 <= 0.90`) and all 11 sibling repository TIFFs (`worst_mutual = 0.3508`), and remains review-only (`download_ok = true`, `submit_recommended = false`) under the active literal one-way forward-overlap gate (`1.00 > 0.70` against `calib_r13lattice_00904.tif`) and live-board calibration caution.
- **Full 62-raster E2 uniqueness re-audit (`evidence/e6/e2_uniqueness_62rasters.json`) & 7-lane `Instrument B′` comparison (`evidence/e6/cross_lane_bprime.json`):**
  `E2` has `worst_mutual = 0.2876 <= 0.70` (`unique = true`), `worst_nonlattice_forward = 0.4795 <= 0.70`, `worst_forward = 1.00`. On `Instrument B′`, `E3` (`60,000` dots) scores `0.2137 [0.2002, 0.2261]`; among `37,654`-dot mass-matched candidates, `E6` ranks first at `0.1100 [0.1058, 0.1133]`, ahead of `E2` (`0.1048`), `H33` (`0.0938`), `E5` (`0.0886`), `P4` (`0.0812`), and `H70-A` (`0.0792`).


## P6 dual-horizon LOQO scarp–rad–basement lane & SGMC buffer calibration (`arena/c6a19d32-gemsdoe70`, 2026-10-20)
- Executed handoff priority #1 (`lidar_scarp_features_u8` + `topo_10m_derived_100m_u8` + `geodawn_rad_u8`/`geodawn_extensions_u8` + 19-band stack + visible-catalogue geometry, `evidence/p6_dualhorizon/`) and priority #2 (`1–20 px` SGMC vs QFaults buffer calibration, `evidence/p6_dualhorizon/sgmc_buffer_audit.json`, plus E2 62-raster mutual re-audit `evidence/p6_dualhorizon/e2_mutual_uniqueness.json`).
- Exp 5.3 (`gems70-p5-dualhorizon-37654-20261020.tif`, SHA-256 `bb014897052c478ca2f4690920e4d863fa2a6b810a05a15d8e33e129cc76de84`) clears H33 on Instrument A (`0.0790` vs `0.0037`), Instrument B′ (`0.1440` vs `0.0938`, Δ `+0.0502` `[+0.0339, +0.0663]`), and Instrument B′′ (`d >= 6 px`, `0.1234` vs `0.0850`), as does the unsupervised breakline ablation Exp 5.2 (`A = 0.0774`, `B′ = 0.1201`).
- Verdict remains `negative` (`download_ok = true`, `submit_recommended = false`): paired Instrument A vs P4 CI straddles zero (`[-0.0050, +0.0163]`), `SGMC B′` over-weights steep pre-Quaternary bedrock ranges (`13.42°` median slope vs catalogue `5.55°`), and literal forward overlap vs the dense lattice is `1.00` (worst mutual overlap `0.4230 <= 0.70`, worst Spearman `0.0300 <= 0.90`).

---

## `IR-70-08` — Bedrock-SGMC Proxy Divergence vs Live-Calibrated Quaternary Piedmont `Instrument C_pied` (`2026-10-20`)

- **Finding:** Across all **22** archived submissions with user-recorded live scores (`evidence/instrument_calibration.json`), raw `SGMC \ cat` (`Instrument B'`) includes `~83%` exposed pre-Quaternary bedrock faults (`mean slope 13.42 deg` vs INGENIOUS catalogue `5.55 deg`), causing SGMC-trained models to over-allocate dots into steep mountain ranges at the expense of concealed basin-margin geothermal faults (`P6` achieves `B' = 0.1440` yet `0.0448` on piedmont blind faults; `P8-OOF38k` achieves `B' = 0.1311` yet `0.0842` vs `H33 = 0.0937` on piedmont blind faults).
- **Resolution:** Calibrating `Instrument C_pied` (`SGMC \ cat` restricted to `d_cat > 2.5 px`, `rel10 <= P75_cat`, `slp10 <= P80_cat`, `depth_to_basement >= 250 m`; `Spearman rho = +0.8667, p = 1.82e-07` vs 22 live scores) and reporting **all three complementary instruments side-by-side (`Instrument A`, `Instrument B'`, and `Instrument C_pied`)** ensures human selectors can inspect both zero-SGMC Quaternary piedmont skill (`P9-PiedmontSubmod`: `A = 0.1100`, `B' = 0.1191`, `C_pied = 0.1112` `#1`) and dual-head `SGMC` recall (`P8-OOF38k`: `A = 0.1113` `#1`, `B' = 0.1311`, `C_pied = 0.0842`; `P8-Submodular-54k`: `A = 0.1090`, `B' = 0.1681` `#1`, `C_pied = 0.1001`).
