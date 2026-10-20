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

## E2/E3 addendum — 2026-10-20 (supersedes "no eligible TIFF" for E1 only)

- **E2 negative (gated scarp).** Scarp×strain×cover joint dotted HOLDOUT-DTI 0.0598 [0.0437, 0.0762] (11,342 withheld, seed 30) failed preregistered gates: paired Δ vs random includes 0 and scarp alone (0.0794) beat it significantly. Cover direction was wrong (shallow AUC 0.468); strain diluted. No E2 TIFF published.
- **E3 candidate released under disclosed adjusted uniqueness.** Scarp-alone dotted HOLDOUT-DTI 0.0943 [0.0782, 0.1109] (11,437 withheld, seed 40), beats random with paired CI excluding 0. Final TIF `gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif` (SHA-256 in run card) is downloadable as a *candidate*; slot use still requires selector completion of the full 862-raster scan (63 checked here, incl. champion: forward 0.342, Jaccard 0.0142, Spearman 0.0198) and weekly-cap verification. Literal forward-overlap still fires on 5 saturating covering fields (halo coverage 0.74–1.00; Jaccards ≤0.041) — certificates in evidence; selector owns the final protocol call.
- **E3 erratum (gating-code bug, science unchanged).** The frozen E3 driver gated support-Jaccard over all rows at surface stage; the everywhere-positive dense proba fired at 0.9543 by construction and blocked placement. `scripts/complete_e3_release.py` applied the preregistered dot-field scope to saved rows, SHA-verified deterministic surface reproduction, then placed dots. Original negative card preserved; amended card carries the erratum. Not a fourth experiment (no new folds/selection).
- **Holdout transfer warning (H33 lesson).** Archived H33 scores HOLDOUT-DTI 0.0043 on E2 folds because its pruning used the full catalogue and it targets off-catalogue faults. Catalogue-recovery holdout therefore cannot predict live ranking; E3 passing it is necessary falsification evidence, not a projected score. No claim to beat 0.2778 (family-reported, no organizer receipt) is made.
- **Selection-edge caveats.** E3 picked the grid-edge cell (60k, >3 px); 45k scored 0.0925 (flattening curve). The 3 px fold collar structurally favours larger exclusions on this instrument, and holdout prevalence (20% hide) may exceed live hidden prevalence, favouring larger budgets. A future session with fresh budget should test a 38–45k scarp variant on new folds rather than retune E3.
- **Official pages now verified.** Problem (p967) and About (p968) retrieved 2026-10-20: metric α=0.2/β=0.8/R=300 m and float32 [0,1] EPSG:32611 format match the shared tools. Leaderboard is JS-rendered; conflicting user-reported leaders (0.3195/0.3774/0.4413) remain unverified. Mirror sample still contradicts the page's "total fault absence" wording (its 60,988 ones sit on the catalogue); it is used only as grid template.
- **Experiment budget exhausted** (E1+E2+E3 = 3). Further science needs a new session preregistration with untouched folds. Highest-value next steps: (1) selector full-registry scan + slot decision with receipt capture; (2) 1 m DEM scarp refinement of E3 dots' corridors (USGS 3DEP, free) as a fresh lane; (3) off-catalogue proxy-truth validation (SGMC/expert-style) to complement catalogue recovery.
