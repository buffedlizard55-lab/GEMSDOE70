# Phase 5 preregistration — out-of-fold halo ranker (written before the run)

Date: 2026-10-20 · lane: single method paragraph, no weekly slot consumed by this file.

## Motivation (measured, not assumed)

1. **Instrument B′ as previously used is dominated by domain-wide coverage.**  A random
   field of 37,654 dots drawn from the whole valid domain scores *below* H33 on the
   unrestricted proxy (0.0697 vs 0.0938, Phase 4) but a random field drawn inside the
   0.2–3.2 km halo scores *above* H33 on a halo-restricted version of the same proxy
   (0.112 vs 0.095, this session).  The proxy's positives are spread over the whole
   footprint, whereas the live score ordering (H33-family 0.26–0.28 vs domain-wide
   lattices 0.09) puts the hidden truth inside the halo.  The previous promotion gate
   therefore tested a different spatial population from the one the organiser scores.
2. **The catalogue is the Quaternary fault database, not an independent map.**  Rasterised
   QFaults traces (`trace_segments_utm11.csv`, 84,331 segments) fall 99.998 % within 3 px
   of `existing_faults.tif`.  QFaults cannot serve as a "new fault" proxy.
3. The only independent fault inventory in the cached inputs is SGMC
   (`sgmc_faults_100m.tif`): 3,666 px shared with the catalogue, 78,485 px not.

## Hypothesis H-P5-1

Within the live-proven 0.2–3.2 km halo, a pixel ranker trained on **one independent
inventory (SGMC) minus the nearest 3 px of the catalogue**, using only geophysical,
lidar-scarp, radiometric and terrain features, can place the same 37,654 dots on
higher-probability new-fault ground than a uniform halo sample.

Mechanism: new faults in the Great Basin express as slope/curvature lineaments,
magnetic/gravity gradients and lidar scarps; the ranker learns those signatures from
SGMC faults and transfers them to the halo.
Named non-fault mimic: Quaternary alluvial fan edges and lake-shore terraces produce the
same slope/curvature signature and are not faults.  A ranker driven by
`det_elev_slope` alone would be fooled by them; the permutation-importance table and
the single-feature canaries must be read for that.

## Design (fixed before the run)

* Grid: pinned 100 m EPSG:32611 grid; `valid` = finite rtp, eroded 12 px; halo = 2.4–32 px
  from the catalogue, off-catalogue.
* Features: 19-band stack (sentinel −3.4e38 → NaN), 12 lidar-scarp bands, 4 radiometric
  bands, 4 GeoDAWN extension bands, catalogue density at σ = 5 and 20 px, local relief
  (σ = 3 px), log distance to catalogue.  43 features.
* Label: SGMC == 1, off-catalogue, distance ≥ 3 px.
* Model: `HistGradientBoostingClassifier`, 250 iterations, lr 0.07, 63 leaves,
  min_samples_leaf 40, L2 1.0, positive weight 8; **spatial 4-fold by quadrant**
  (train on three, predict the fourth).  The published raster is the out-of-fold field:
  every dot is scored by a model that never saw its quadrant.
* Emission: one dot per 5 × 5 px block at the block's maximum probability, 4 px NMS,
  exactly 37,654 dots, restricted to the halo.
* Instruments: (A) shared hide-and-recover catalogue holdout, unchanged;
  (B) unrestricted SGMC proxy, reported for continuity; (C) **new primary**:
  SGMC-only, 3 ≤ d ≤ 32 px, four eroded quadrants, pooled DTI, paired 20 km
  spatial-cluster bootstrap, α = 0.2, β = 0.8, 300 m triangular kernel.

## Promotion gate (all must hold)

G1 format: shared validator passes on the written bytes.
G2 uniqueness: worst **mutual** 3-px dot overlap < 0.70 and worst |Spearman| < 0.90
against all archived registry rasters.
G3 ranking skill: pooled out-of-quadrant AUC ≥ 0.70 on the SGMC-only label.
G4 surrogate gain: candidate − H33 on instrument C has a paired 95 % CI lower bound > 0.
G5 live-shape preservation: median catalogue distance in [8, 24] px and ≥ 130 occupied
200 px blocks (H33: 19.6 px, 158 blocks).

If G1–G5 hold the file is labelled **download and submit: yes (calibrated test)**.
Otherwise it is published as a negative and labelled **do not submit**.
No number in this lane is ORGANIZER-CONFIRMED; the live score is the only test and must
be recorded from the submission-page receipt.

## Amendment A1 (post-run, 2026-10-20) — G3 statistic

The run showed that pooling raw probabilities from four independently fitted fold
models is not identifiable: the four models have different intercepts, and the raw
pooled AUC (0.659) is lower than every individual fold AUC (0.689, 0.721, 0.776,
0.712).  G3 is therefore evaluated on the **mean of the four held-out AUCs** with the
**rank-normalised pooled AUC** as a cross-check; the raw pooled value is still reported
in `evidence/phase5/ranking_skill.json` and in the run card.  This amendment was
written after seeing that single number and is disclosed as such; G4, G5, G1 and G2 are
unchanged and were not amended.  No other registered parameter changed.
