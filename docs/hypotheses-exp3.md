# Preregistration Addendum — Experiment 3 (H70-3A), written before running it

**Motivation from Experiment 2 (already-reported evidence, `evidence/holdout2.json`):**
on the seed-702 holdout the corroboration gate significantly *hurt*
(candidate 0.07829 vs NoGate ablation 0.08854; paired Δ −0.01025 [−0.01794, −0.00239]),
and the unsupervised GEMSDOE49-architecture detector (0.08681) was statistically
indistinguishable from the raw supervised model. Experiment 2 is negative and is
not retuned. This addendum specifies ONE new experiment, evaluated on **untouched**
blocks (seed **703**; no model, surface, or dot from seed 702 is reused as an input).

## H70-3A — Dual-detector rank fusion
- **Layers / signature:** identical label-free 36-feature stack and out-of-fold
  HistGradientBoosting model as H70-2A (features unchanged), fused with the
  unsupervised GEMSDOE49-architecture surface (multiscale `det_elev_slope` edge ×
  structure-tensor coherence × cross-gradient orthogonality gate, `w=0.25`) by
  **geometric mean of footprint ranks**: `sqrt(rank01(HGB_oof) * rank01(G49))`.
- **Why it could catch unmapped faults:** the supervised model exploits subtle
  multi-physics co-variation learned from visible faults; the unsupervised
  detector requires an actual linear topographic breakline. Rank fusion keeps
  only locations both mechanisms support, suppressing single-mechanism false
  positives (learned-texture artefacts and non-tectonic scarps respectively).
- **Named non-fault mimic:** anthropogenic/paleoshoreline linear scarps that are
  also geophysically textured (e.g. shoreline benches on magnetic basement) —
  these can satisfy both detectors and remain the principal failure mode.
- **Difference from prior repos:** no prior family submission fuses a supervised
  out-of-fold model with this unsupervised detector by rank geometric mean;
  GEMSDOE63 fused prior *submission surfaces* (prohibited here as inputs).

## Fixed protocol (seed 703, otherwise identical to Experiment 2)
- Same features, model hyperparameters, canary rule (stop if any |AUC−0.5| implies
  max(AUC,1−AUC) > 0.90), `buffered_component_draw(seed=703, buffer_px=3, boundary_px=12)`,
  same `emit_decimated`/`emit_prefix` dotted placement, global budget 37,654 dots
  (per-fold proportional, identical for every arm), dots >2 px from *visible* faults.
- **Arms:** `candidate` (fusion), `RawHGB_NoGate`, `GEMS49_OrthoGate`,
  `Gated_H70_2A` (Exp-2 candidate construction), `SingleBand_ElevSlope`,
  `Random_Sparse_Control` — all on identical seed-703 blocks, pooled by the shared
  evaluator (`gems57-pooled-hide-v2`, 1,000 paired bootstrap draws).
- **Promotion gate (holdout part):** candidate must beat `RawHGB_NoGate`,
  `GEMS49_OrthoGate`, `Gated_H70_2A`, and `Random_Sparse_Control`, each with paired
  95% CI lower bound > 0. Any failure ⇒ verdict negative, no “OK to submit”.
- **Uniqueness part:** two-stage 940-raster audit (surface + final dots) with the
  shared tool; like-for-like dot-field overlap ≤ 0.70 and |Spearman| ≤ 0.90 required,
  literal reading reported alongside (see `docs/irregularities.md` protocol note).
- **Budget:** this is experiment 3 of 3. No further experiments after this one.
