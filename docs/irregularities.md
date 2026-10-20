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

## Phase-5 Execution & Resolution Addendum (2026-10-20)

All four next-session priority items listed above were executed in Phase-5:

1. **Priority 1 — LOQO Supervised Within-Halo Ranker (`evidence/phase5/run_card.json`):**
   `scripts/run_experiment_v5.py` trained a 4-fold Leave-One-Quadrant-Out `HistGradientBoostingClassifier` on `sgmc & ~catalogue & (d_cat >= 3 px)` with 12-px eroded quadrant boundaries across 49 features (39 physical bands + 2 GDR-1391 hydrothermal conduit features + 8 visible catalogue geometry features), combined via quadrant-rank normalization with the tip/damage halo prior (`d_cat >= 3` px, no `32`-px truncation) and `7×7` block stratification + `5`-px NMS (`37,654` binary dots).
   - **Instrument A (`11,321` withheld catalogue positives):** `0.0752` (`[0.0683, 0.0821]`), beating Phase-4 (`0.0730`), Random (`0.0460`), and H33 (`0.0037`).
   - **Instrument B′ (`d_cat >= 3` px, `59,937` SGMC proxy positives):** `0.1138` (`[0.1077, 0.1192]`), beating H33 (`0.0938`, paired `Δ = +0.0200`, 95% CI `[+0.0097, +0.0302]`) and Phase-4 (`0.0812`, paired `Δ = +0.0326`, 95% CI `[+0.0249, +0.0411]`).
   - **Instrument B″ (`d_cat >= 6` px, `52,767` SGMC proxy positives outside the 1:500k duplication band):** `0.1000` (`[0.0940, 0.1058]`), beating H33 (`0.0850`, paired `Δ = +0.0149`, 95% CI `[+0.0050, +0.0245]`).
   - **Ablation finding (hydrothermal spatial clustering):** Because GDR-1391 hot wells (`929` cells) and thermal springs (`377` cells) are concentrated in a handful of drilled geothermal fields, the 47-feature ablation (`ablation_no_hydro`) scores slightly higher across quadrants (`B' = 0.1162`, `B'' = 0.1024`, `A = 0.0755`) than the 49-feature candidate (`B' = 0.1138`, `B'' = 0.1000`, `A = 0.0752`), while both clear every pre-registered gate with 95% CIs strictly above zero.
2. **Priority 2 — SGMC vs QFaults Buffer Calibration (`evidence/phase5/sgmc_buffer_audit.json`):**
   `scripts/audit_sgmc_proxy.py` measured `sgmc & ~catalogue` (`78,433` px) across annular distance shells `1..6` px from `existing_faults.tif`. Enrichment decays from `3.62×` (`[1,2)` px) and `2.30×` (`[2,3)` px) to `1.04×` (`[5,6)` px) and `0.92×` (`[6,8)` px), confirming that `r >= 6` px (`600 m`, Instrument B″) lies completely outside the 1:500,000 cartographic duplication band, while `r = 3` px (`300 m`, Instrument B′) is the exact threshold where `H33 > D28` flips to match the user-reported leaderboard ordering (`0.2778 > 0.2600`).
3. **Priority 3 — E2 Full 62-Raster Re-Audit & Upstream Uniqueness Patch (`evidence/phase5/e2_uniqueness_62rasters_corrected.json`, `evidence/phase5/upstream_verification.json`, `evidence/phase5/upstream_uniqueness.patch`):**
   - `scripts/reaudit_e2_uniqueness.py` audited `gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif` across all 62 archived registry rasters under the corrected binary-dot + mutual-overlap rule (`unique = True`, `duplicate_count = 0`, `worst_mutual_overlap = 0.2876` against `calib_h161_01855.tif`, `worst_spearman = 0.0241`). E2 remains `DO NOT SUBMIT` because its Instrument A promotion bar vs D28 was not met.
   - `scripts/verify_upstream_fix.py` generated the standalone 109-line patch `evidence/phase5/upstream_uniqueness.patch` against `buffedlizard55-lab/60GEMSDOE` (`1c5094b8...` -> `93726c6a...`) and verified that applying it to `/tmp/60GEMSDOE/src/gems57/uniqueness.py` passes all 33 shared-tool tests (`33 passed in 0.88s`).
4. **Priority 4 — Selector Step (`evidence/phase5/run_card.json`):**
   `gems70-p5-loqo-halo-37654-20261020.tif` (`sha256: a8cef5bdbbc030cd6bdd59ea275e09e27edf87b4ee8068d3e8052bdff1cb9667`) passes all validator checks, 66-raster surface and dot uniqueness checks, 49-feature leakage canaries (`max deviation AUC = 0.7770 <= 0.90`), and all three pre-registered evaluation gates (`A`, `B'`, `B''`), earning `verdict = "promote"` (`selector_ready = True`, `weekly_slots_used = 0`). Under PARALLEL-RUN PROTOCOL Rule 6, live portal upload remains gated on human selector sign-off because SGMC is a state-compilation proxy rather than the organizer's hidden truth.

