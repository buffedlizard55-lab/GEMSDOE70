# Experiment-3 preregistration — 2026-10-20 (SGMC distal-truth rescoring)

Third and final experiment of the protocol budget. No new ranking is trained,
tuned, or emitted here: fixed dot sets from experiment 2 and the public
archives are rescored against an independent off-catalogue proxy truth.

## Motivation (from experiment-2 evidence)

On the shared hide-and-recover holdout, withholding truth that sits ON the
catalogue, every catalogue-avoiding design collapses: H33 reference dots score
0.0037/0.0044 while mass-matched unconstrained random scores 0.047/0.051
(HOLDOUT-DTI, seeds 20/71). The family's best live design (owner-report
0.2778) ranks below random on this instrument, so the instrument cannot
validate distal discovery designs in either direction. Experiment 3 tests the
same fixed dots against faults an independent public map records OFF the
competition catalogue.

## Proxy truth (measured before this preregistration, fixed here)

- Source: `derived_sgmc_faults_100m_u8.tif`, GEMSDOE24 commit
  `07345ea0604953d7efb858d9cfbc21e20c7aca0b`, SHA-256
  `643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0`
  (verified), grid-matched to the competition grid (verified), binary {0,1}.
- Manifest provenance (quoted): "derived from USGS SGMC geologic-map faults
  (proxy only; not used in the factorial)".
- Truth definition (fixed): SGMC-positive pixels with
  distance-to-competition-catalogue > 3 px: **62,122 pixels** (of 83,593
  on-footprint SGMC pixels; only 3,978 sit on the catalogue). Floor: the run
  stops as inconclusive if truth has fewer than 1,000 pixels (satisfied).
- Masked-known: the FULL competition catalogue (organizer-style masking).
- Limit (stated): SGMC maps faults of any age/activity, while the hidden live
  truth presumably emphasizes geothermal-relevant structures; the proxy is
  noisy by construction. Gate A exists to test whether it still ranks live
  designs correctly. SGMC licensing/lineage beyond the quoted manifest note is
  not independently verified here.

## Fixed arms (no new emission)

- `candidate`: experiment-2 dots RECOMPUTED by `src/gems70/method_exp2.py`
  (byte-pinned by the experiment-2 manifest; the run aborts if the pinned SHA
  differs). Deterministic by construction; assert 38,000 dots.
- `h33`, `h27`, `d28`: public archive bytes (SHAs c55bafc4…, 2fc94a38…,
  3e78737f…, grid-verified in experiment 2).
- `random_avoiding`, `random_unconstrained`: fresh mass-matched (38,000)
  controls, `numpy.random.default_rng(70073)` (fixed here); avoiding uses
  catalogue-distance > 2 on the experiment-2 valid domain, unconstrained uses
  the valid domain.
- Domain asymmetry (stated): references span the full footprint while the
  candidate/controls live on the 12 px-eroded valid domain (96.6% of the
  footprint). References are kept byte-intact; the asymmetry slightly favors
  them and is not hidden.

## Fixed scoring

- One whole-footprint evaluation per arm with the shared byte-pinned
  `evaluate_holdout.evaluate`: region = footprint, masked_known = full
  catalogue, truth = SGMC-distal. Bootstrap: shared `pooled_summary`,
  1,000 draws, seed 70073 (fixed here).
- Gate A (instrument validation): H33 beats D28 AND H33 beats
  random_avoiding, both with non-overlapping 95% CIs (reproduces the
  owner-reported live ladder direction D28 0.26 → H33 0.2778 on the proxy).
- Gate B (candidate signal): candidate beats random_avoiding with
  non-overlapping 95% CIs.
- PROMOTE (write the submission via the shared writer, then byte-check)
  if and only if A ∧ B hold, reusing experiment 2's already-measured gates
  (canaries clean, artifact rule passed, rho < 0.90, sparse overlap < 0.70,
  byte-uniqueness vs the 862 index at write time, shared-validator receipt).
  Any failure, or the truth floor failing, yields negative with no file.
- Submission name/note rule from the round-2 preregistration is reused
  (deterministic name `gems70-vgshallow-h1-B2-38k`).

## Budget

Experiment 3 of 3. No further experiments after this run regardless of
outcome. No competition upload and no weekly-slot decision is made here.
