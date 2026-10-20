# Preregistration S3-E2 — marginal-matched proxy ranking (experiment 2 of ≤ 3)

Committed **before** the run. Written after S3-E1 and the post-hoc calibration diagnostic,
whose results motivate it (all receipts in `evidence/s3/`).

## What E1 and the calibration showed

* E1 (`docs/preregistration-s3.md`) passed its frozen rule on B′: candidate 0.1237 vs H33 0.0938,
  paired Δ +0.0300, 95 % CI [+0.0034, +0.0557].
* Calibration diagnostic (`scripts/proxy_calibration_s3.py`, `evidence/s3/proxy_calibration.json`):
  over 18 archived rasters with owner/user-reported live scores, Spearman(live, B′) = −0.28 and
  Spearman(live, A) = −0.64. **Neither offline instrument orders files the way the live board did.**
* Descriptive: E1 places 63.6 % of dots in the top quartile of 10 m-DEM `slope_p90`; H33 19.9 %;
  GEMSDOE49 `gate_ortho` 47.5 % — and gate_ortho scored 0.2376 live (reported) despite B′ 0.134.
  The B′ gain of E1 is therefore confounded with the named mimic (bedrock / map-density bias).
* E1 is vetoed for submission (conservative, post-hoc veto; never a post-hoc promotion).

## Hypothesis E2

After removing the terrain and distance confounds — by forcing the dot distribution over
(catalogue-distance band × slope quartile) to equal H33's, the live champion's — the proxy-trained
model still ranks unmapped-fault likelihood **within** each stratum better than chance and
better than H33.

## Fixed design (everything not listed is identical to E1)

* Strata: catalogue distance edges `[2.4, 3, 4, 6, 10, 15, 20, 30, 45, 60, 100, ∞)` px ×
  quartiles of `topo_10m_derived_100m_u8` band 1 (`slope_p90`) computed on the domain
  (u8 = 0 treated as its own "missing" class) → 11 × 5 = 55 strata.
* Quota per stratum = number of H33 dots in that stratum among H33 dots inside the domain, scaled
  to 37,654 by largest-remainder rounding. H33 contributes **only counts**, never positions.
* Placement: one greedy pass over pixels in descending model rank; accept a pixel iff its stratum
  quota is unfilled and no accepted dot lies within 2.5 px (same NMS as E1/H33 spacing).
* Model: the E1 candidate feature set and HGB parameters, LOQO out-of-fold for B′; one model on
  all quadrants for production; per-quadrant percentile ranks.
* Arms on B′: E2 candidate; H33; **random-stratified** (uniform random order, same quotas, same
  NMS — isolates within-stratum information); E1 candidate (reference); random.
* Instrument A as in E1, strata recomputed from the visible catalogue in each fold.
* Leakage canary: same features as E1 (receipt `evidence/s3/canaries.json`, no alarm, max 0.768).

## Frozen promotion rule

1. B′: E2 > H33 with paired 95 % CI lower bound > 0.
2. B′: E2 > random-stratified with paired 95 % CI lower bound > 0 (information beyond marginals).
3. A: E2 ≥ H33.
4. Uniqueness (surface ρ ≤ 0.90; final mutual overlap ≤ 0.70, ρ ≤ 0.90) and validator pass.
5. Reported steep-quartile fraction within ±0.03 of H33's (by construction; checked).

All hold ⇒ `promote`. The live-board calibration remains unvalidated, so even a promote is a
**proxy-supported test**, not a predicted score. Otherwise `negative`, file labelled DO NOT SUBMIT.
If E2 is negative the session stops modelling (no experiment 3).
