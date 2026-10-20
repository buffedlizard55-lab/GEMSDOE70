# Preregistration E5 — supervised within-halo ranking (2026-10-20)

Written BEFORE the E5 run. This executes the registered next step from
`HANDOFF.md` / `docs/irregularities.md` ("Supervised within-halo ranking trained
on the SGMC off-catalogue proxy with leave-one-quadrant-out"). One experiment
only (E5-1). Everything else below is a queue, not extra experiments.

## Why H33 scored 0.2778 (user-supplied; no organizer receipt in this repo)

Measured byte anatomy is in `docs/h33-analysis.md`: H33 = D28 Poisson halo dots
minus the 1 px shell (H27) minus the √2/2 px shells — a uniform sparse sample
of the 0.2–3 km halo, median 1.97 km from a trace. Under
DTI = T/(T + 0.2(S−M) + 0.8(N−T)), T saturates per truth cell while S scales
per dot, so spreading beats concentrating, and dots < ~2 px from a mapped
trace buy S for ~no T (known faults are masked pixel-exactly). Most of 0.2778
is therefore emission geometry. Beating it requires ranking *inside* the halo
with information geometry does not contain — which is what E5-1 tests.

## Candidate hypotheses (ranked; only #1 runs)

| Rank | Hypothesis / layers | Physical signature | Why it can catch a catalogue omission | Named non-fault mimic | Difference from repo implementations | Cost |
|---|---|---|---|---|---|---|
| 1 TEST | **E5-1 Supervised within-halo ranking**: 19-band stack + analytic signal + gradient magnitudes (rtp, basement, gravity) + catalogue geometry (d, log d); HGB trained on SGMC off-catalogue proxy (d_cat ≥ 3 px), leave-one-quadrant-out | Learned multivariate combination of magnetic/gravity edges, strain, seismicity, topography, conductivity at known-but-uncatalogued traces | Training positives are literally faults in the Nevada SGMC compilation but absent from the USGS/INGENIOUS catalogue raster — the omission population itself | SGMC compilation/redrawing bias; lithologic contacts with the same potential-field signature | Every prior lane here (P4, E2, E3, H2, phase 1–3) is geometry or single-field rules; none trains on the off-catalogue proxy with spatial LOQO | Medium; cached stack, CPU |
| 2 | E5-2 Analytic-signal ridge standalone: sqrt(tmi_hg² + tmi_vg²) | Source-edge envelope independent of magnetization direction | Buried magnetic-contact faults have no scarp | Dike margins, remanence contrasts | Repo used unsigned RTP horizontal gradient only; in E5-1 it is one feature (canary = ablation reading) | Low |
| 3 | E5-3 GeoDAWN radiometric alteration edges: K/Th/U/TC gradients | Hydrothermal alteration halo edges along fluid pathways | Alteration can outcrop where the trace is unmapped | Primary lithologic K/Th variation; flight-line levelling | No radiometric layer used in this repo yet | Medium-high; needs `ext_geodawn_rad_u8` from the pinned owner mirror via `scripts/fetch_data.py` (obtainability to be checked before proposing as run) |
| 4 | E5-4 LiDAR scarp composite as supervised features | 1 m scarp morphology aggregated to 100 m | Blind scarps displace topography without a mapped trace | Fans, paleochannels, road cuts | Prior lidar lanes (other sites, user-supplied 0.043–0.115) were standalone detectors, not features inside a proxy-trained ranker | Medium; needs `ext_lidar_scarp_features_u8` mirror fetch, check first |
| 5 | E5-5 Seismicity corridors standalone: deq/ieq bands 10/16 | Microseismicity density ridges along active unmapped strands | Active blind faults seismically express before mapping | Geothermal production/injection seismicity; network detection bias | Bands unused standalone here; inside E5-1 as features | Low |

## Frozen design (no tuning after seeing results)

- Grid/instruments identical to P4 (`scripts/run_experiment_v4.py`): evaluator
  `gems57-pooled-hide-v2`, α=0.2, β=0.8, 300 m triangular kernel, pooled terms,
  paired 20 km spatial-cluster bootstrap (1000 draws, seed 70420).
- Features (fixed order): 19 stack bands (nodata→NaN), analytic signal,
  Sobel gradient magnitude of rtp / depth_to_base_surf / iso_grav_anom,
  d_cat, log1p(d_cat). Geometry is context-derived: full catalogue for
  training/production; **visible catalogue only** in each Instrument-A fold.
- Labels: proxy′ = SGMC & ~catalogue & footprint & (d_cat ≥ 3 px).
  Training positives and negatives are both restricted to the eligible band
  (this is within-halo ranking, not whole-map classification).
  Negatives: eligible band, >3 px from any SGMC pixel. Eligible =
  valid (finite rtp & footprint, eroded 12 px) & off-catalogue & 2.4 ≤ d ≤ 32 px.
- LOQO: quadrant ids from shared `holdout.quadrant_ids`. Model k trains on
  quadrants ≠ k, excluding a 12 px dilation of quadrant k. ≤240,000 sampled
  negatives, all positives, balanced sample weights, seed 70501.
- Model: `HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
  max_leaf_nodes=31, min_samples_leaf=40, l2_regularization=1.0,
  early_stopping=False, random_state=70501)`. No hyperparameter search.
- Production surface = out-of-fold assembly (quadrant k scored by model k).
  The published dots are emitted from exactly this evaluated surface.
- Emission identical to P4: one dot per 7×7 stratum at stratum max, 5 px NMS,
  exactly 37,654 binary dots.
- Canaries first: every feature alone, AUC vs Instrument-A withheld positives
  and vs proxy′; AUC > 0.90 on either stops the run as suspected leakage.
- Uniqueness: shared corrected tool on (a) the OOF surface before placement
  and (b) the final dots, vs the 60GEMSDOE registry clone. Spearman > 0.90 or
  mutual 3 px overlap > 0.70 ⇒ duplicate, log and stop.
- Gates identical to P4: **promote** iff not duplicate AND validator passes
  AND Instrument-A candidate ≥ H33 reference AND B′ paired Δ vs H33 > 0 with
  95% CI lower bound > 0. Otherwise **negative**: artifact still published as
  download-for-review with `submit_recommended=false`. No weekly slot is spent
  by this session either way; promotion is a selector decision.
- All scores labelled HOLDOUT-DTI / PROXY-DTI with evaluator version, withheld
  counts and CI. Nothing is ORGANIZER-CONFIRMED without a portal receipt.

## Amendment 1 (2026-10-20, before any DTI was computed)

First execution reached placement and stopped: P4's one-per-7×7-block pass
places only 34,409 of 37,654 dots on the sharper supervised surface (block
argmaxes align along ridges and mutually suppress under 5 px NMS; measured on
the cached OOF surface, no instrument score existed at that point). Emission
is amended to: P4 block pass unchanged, then a deterministic fill pass over
remaining score>0 pixels in descending score order under the same 5 px NMS
until exactly 37,654. Dot count, NMS, strata and all gates are unchanged.

## Named mimic / failure mode

SGMC is a state compilation that partially re-draws QFaults traces and has its
own mapping-effort bias. A model that learns "where SGMC draws lines QFaults
didn't" may learn compilation style, not hidden-truth geology. B′ (d_cat ≥ 3px)
removes the worst redrawing band, but residual bias is exactly why both
instruments are reported and why a B′ win is a gate to a *selector*, not a
score claim.
