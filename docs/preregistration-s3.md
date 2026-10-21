# Preregistration S3 — supervised proxy-trained ranking with H33-matched spacing

Committed **before** the run (see git history of this file). Session 3, branch
`arena/a0382202-gemsdoe70`, 2026-10-20. Budget: this is experiment 1 of at most 3 in this
session; no further experiment is pre-specified, so a negative result ends the session's modelling.

## Why this experiment (from measured evidence, not from scores)

1. `docs/h33-analysis.md`: H33 is a uniform Poisson sample (min spacing 2.83 px, measured
   this session from the archived bytes, sha256 `c55bafc4…`) of the 0.2–20 km band around mapped
   faults, with the closest shells removed. It contains no physical information.
2. Measured this session on the restored inputs: inside the valid domain, the rate of SGMC-only
   fault pixels (≥ 3 px from the catalogue, "B′ proxy") is nearly **flat with distance**
   (0.0188 at 3–6 px, 0.013 from 10 to 60 px, 0.011 at 60–100 px). Distance geometry therefore
   cannot be where the remaining headroom is; it has to come from layers that see the ground.
3. The previous session's stated next step was exactly this: supervised within-domain ranking
   trained on the SGMC off-catalogue proxy with leave-one-quadrant-out (HANDOFF.md, item 1).

## Hypothesis

Faults absent from the USGS/INGENIOUS Quaternary catalogue but present in independent geologic
mapping sit where physical layers show structure — LiDAR-derived scarp/step/curvature responses,
10 m-DEM lineament and slope-break statistics, radiometric (K/Th/U) contrasts that mark lithologic
juxtaposition or alteration, magnetic and gravity gradients, conductivity and strain-rate
fields. A model trained on the proxy population can rank pixels **inside** the region H33
samples uniformly, so at identical dot count and identical spacing it should place more dots
within 300 m of unmapped faults.

**Named non-fault mimic:** lithologic contacts and map-compilation density bias (bedrock ranges
are mapped in more detail than alluvial basins, so a model can learn "bedrock" rather than
"fault"). Erosional escarpments and paleoshorelines mimic LiDAR step features.

**Transfer risk (declared):** the hidden truth is expert-mapped faults not in the USGS database;
SGMC is a different compilation. B′ is a proxy, never the organizer's truth.

## Fixed design

* Inputs (all SHA-checked): 19-band `training_features.tif`, `existing_faults.tif`,
  `sample_submission.tif` (restore_data.py pins), and from `buffedlizard55-lab/60GEMSDOE`:
  `lidar_scarp_features_u8.tif` (12 bands), `geodawn_rad_u8.tif` (4), `geodawn_extensions_u8.tif`
  (4), `topo_10m_derived_100m_u8.tif` (9), `dem10_chi_100m_u8.tif` (4), `sgmc_faults_100m.tif`
  (truth only, sha256 `26d142c4…`), H33 (sha256 `c55bafc4…`).
* Domain: `valid` = 12-px eroded finite-feature footprint (as Phase 4), off-catalogue,
  catalogue distance `d ≥ 2.4 px`.
* Label: B′ proxy pixel (`SGMC & ~catalogue & footprint & d ≥ 3`). **SGMC is never a feature.**
* Features: catalogue geometry from the catalogue only (d, log1p d, tip along/across distance,
  catalogue density in 15 px and 41 px windows, host-component log length); the 19 stack bands
  (sentinels → NaN); Gaussian(σ=2 px) gradient magnitudes of rtp, iso_grav_anom,
  depth_to_base_surf, det_elev, cond_surf, tmi; 5-px local std of det_elev; all 33 u8 auxiliary
  bands (0 → missing).
* Model: `HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=63,
  min_samples_leaf=200, l2_regularization=1.0, random_state=70)`; training rows = all label
  positives + 6× random negatives from the training quadrants' 12-px-eroded regions.
* Leave-one-quadrant-out: four models, each predicts only its held-out quadrant (out-of-fold).
  Scores are converted to **percentile ranks within each quadrant region** so all quadrants
  are comparable; production uses one model trained on all four quadrants with the same
  per-quadrant rank transform.
* Placement (identical for candidate and every ablation): greedy non-maximum suppression in
  rank order with exclusion radius 2.5 px (minimum spacing 2√2 px = H33's measured minimum),
  exactly **37,654** binary dots, d ≥ 2.4 px, zero on catalogue and outside footprint.
* Arms on B′ (pooled, paired 20 km spatial-cluster bootstrap, 1,000 draws, seed 70420):
  candidate; H33; random (same domain, same count); P4 published file; ablation
  physics-only (no catalogue geometry); ablation catalogue-geometry-only; placement ablation
  (7×7 stratified, P4 placement on the candidate score). Unrestricted B reported, not gated.
* Instrument A (shared hide-and-recover, seed 20, buffer 3, boundary 12): production model with
  catalogue features recomputed from the visible catalogue in each fold. Diagnostic only.

## Leakage canary

Each feature alone: AUC against the B′ label on a fixed 1,000,000-pixel random sample of the
domain; `max(AUC, 1−AUC) > 0.90` ⇒ suspected leakage ⇒ stop, no artifact.

## Frozen promotion rule (all must hold)

1. No canary alarm.
2. B′: candidate DTI > H33 DTI **and** paired 95 % CI lower bound > 0.
3. A: candidate DTI ≥ H33 DTI.
4. Surface (rank score) Spearman ≤ 0.90 against every checked registry raster, and final dots:
   mutual 3-px overlap ≤ 0.70 and Spearman ≤ 0.90 (shared `vendor/gems57/uniqueness.py`).
5. Shared writer + validator pass (finite, [0,1], CRS/shape/transform match).

If all hold: `verdict = promote`, `download_ok = true`, `submit_recommended = true`. Slot use is
still the user's separate selector decision. Otherwise `verdict = negative` and the file, if
written, is labelled DO NOT SUBMIT. No number is ever presented as an organizer score.
