# P5 preregistration — 2026-10-20 (written before feature evaluation)

**One lane only.** The supplied prompt refers to a “single method paragraph below”, but no
such method paragraph was supplied. Provisional lane, for this run only:

> **Cover-conditioned analytic-signal source-edge ranking within the visible-fault halo.**
> A blind basement fault below basin fill can juxtapose rocks of differing magnetization.
> Use the width and amplitude of the GeoDAWN magnetic analytic signal, the local gravity
> edge and sediment-cover depth; learn a ranking against *off-catalogue SGMC proxy faults*
> with leave-one-quadrant-out training, with catalogue distance computed only from faults
> visible to the fold. SGMC is a response, **never** a predictor or spatial mask at export.

This is a hypothesis about fault traces, **not** a geothermal vent / fluid-flow discovery. No
parameter may be adjusted after observing holdout results. The archived P4/H33 rasters are
comparators only and never used as features or copied into a prediction.

## Ranked scientific hypotheses considered *before* implementation

Expected DTI improvement ranks are **qualitative conjectures, not scores**. Novelty refers only
to methods inspected in this repo and the pinned archive, not every private competitor run.

| Rank / cost | Hypothesis; specific layers | Physical transform; why an unmapped fault? | Named non-fault mimic; difference from repo | Data status |
|---|---|---|---|---|
| 1 / medium | **P5 tested:** `tmi_hg` (stack band 3), `tmi_vg` (9), `iso_grav_anom` (13), `depth_to_base_surf` (15), visible-only mapped-fault distance | Analytic-signal amplitude `hypot(HG,VG)` and Gaussian scale ratio (sigma 3 / sigma 1) identify broad source boundaries; gravity gradient and sediment cover help distinguish basement contrasts beneath unmapped alluvium. Supervised **within-halo** ranking rather than a binary edge detector. | **Buried dike / remanent magnetization** or flight-line leveling seam. Earlier E1 used along-tangent magnetic termination; E2 used elevation steps; P4 uses geometry alone; H33 reuses dotted prior. This test uses a scale-width interaction calibrated on held-out independent-map faults, not copied dots. | 19-band SHA-pinned mirror restored. SGMC raster is a pinned owner-derived proxy, not organizer truth. No new external download. |
| 2 / medium-high | `cond_surf` (17), `iso_grav_anom` (13), `depth_to_base_surf` (15) | Signed conductivity / gravity cross-profiles across a basement step; covered fault can displace basement without a scarp. | **Saline groundwater facies boundary**. Signed side-order persistence rather than E1 unsigned gradients or E2 mean shift. | Existing stack; no new data. Not run. |
| 3 / high | GeoDAWN radiometric K/Th/U/TC (owner u8 pack) + 3DEP 1 m LiDAR scarp composite | Spatially persistent K/Th alteration gradient coincident with LiDAR curvature, even where expert mapped trace is absent. | **Primary bedrock chemistry or an old shoreline**; a coincident, multi-sensor halo, not prior single radiometric or LiDAR ridges. | USGS [GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), CC0, and 3DEP named by organizer; SHA-pinned owner derivatives downloaded, **not organizer-authenticated**. Not run. |
| 4 / medium | `deq_n100a15` (10), `ieq_n100a15` (16), `geod_shearrate` (7) | Anisotropic earthquake-density gradient aligned with geodetic shear may mark active faults concealed beneath cover. | **Station-network / interpolation artifact**; anisotropic joint transform rather than scalar earthquake density or existing fault-distance prior. Resolution may be too coarse for 300 m metric. | Existing stack; no new data. Not run. |

These hypotheses are *not* newly confirmed structures. The source basis for the magnetic-contact
mechanism and its counterexample is [USGS OFR 02-98](https://pubs.usgs.gov/of/2002/0098/intro.htm):
analytic signal peaks over isolated magnetic contacts, while derivatives amplify noise and shifts
can arise from model assumptions. [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
warns that survey height and flight specifications vary. The [USGS SGMC release](https://www.usgs.gov/data/state-geologic-map-compilation-sgmc-geodatabase-conterminous-united-states)
is a state-geology **compilation**, not independent verification of the hidden fault labels; the
owner's 100 m raster is not authenticated against its current 2026 revision. The actual
[DrivenData problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
predicts newly identified faults, not vents. Organizer data access is login-walled; mirrors are
used only with disclosed provenance.

## Frozen primary experiment

- Data pins: `training_features.tif` sha256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`,
  `sample_submission.tif` `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc`,
  `existing_faults.tif` `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`;
  `sgmc_faults_100m.tif` `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c`.
  Full feature grid, CRS, transform must match the sample. Source mirror identity ≠ organizer identity.
- Invalid raw values: outside sample finite footprint, `<= -1e30`, `>= 1e30`, nonfinite. Nearest fill
  **from joint raw-valid pixels only**, filter before eroding. `valid` is joint raw-valid eroded 12 px.
- Features: log1p of `abs(tmi_hg)`, log1p of `abs(tmi_vg)`, log1p of analytic amplitude; Gaussian
  analytic-amplitude sigma3 divided by sigma1+1e-3, clipped at 3; log1p of gravity gradient
  magnitude after Gaussian sigma2; log1p of nonnegative basement depth; and visible-fault
  distance clipped to 32 px. All transforms fixed without seeing response labels. Keep the
  unit/raster descriptions as metadata (not independently calibrated physical quantities).
- Prediction domain: `valid & ~visible & 3 <= distance_to_visible <= 32 px` for A and SGMC-LOQO;
  `valid & ~catalogue & 3 <= distance_to_catalogue <= 32 px` for final. No SGMC predictor or
  mask at export. No probabilities on known faults (pixel-exact).
- Training response: SGMC 100 m mapped faults **at least 3 px from visible faults**, in other
  quadrants only; train domain excludes a 12-px quadrant boundary. For each of four folds,
  train `HistGradientBoostingClassifier` with 80 iterations, 15 leaves, min leaf 100,
  learning_rate 0.06, L2 2, max_bins 64, random_state 70501; take all positives up to
  25,000 and up to 5 negatives per positive, sampling seed 70501+fold.
  B′ gets cross-fitted predictions ONLY in its withheld quadrant; production refits on all four
  labelled quadrants. Predicted scores are **rankings, not calibrated probabilities**.
- Convert the ranking to a continuous confidence field by retaining only the top 2% of
  **allowed**-domain ranks (mean-tie percentile), `p = 0.99 * max(rank - 0.98, 0)/0.02`, zero
  elsewhere. For OOF, rank separately *within each held-out quadrant*; for production,
  rank over all allowed cells. Thus OOF support across four quadrants has the same
  approximately 2%-of-allowed mass as production. The final field is **not a binary dot
  placement**; positive-support overlap and binary-dot overlap are both reported, not
  conflated. Score **this exact transform** on A and B′, no tuning after the outcome.
  If its support is insufficient, report a negative.
- Canary: every raw and derived feature (including visible-distance) alone on the A spatial
  holdout. Whole connected fault components hidden by shared `buffered_component_draw`
  (seed 20, buffer 3 px, quadrant boundary 12 px); 200,000 negatives sampled with seed 70501.
  Any `max(AUC,1-AUC)>0.90` ⇒ stop for suspected leakage.
- Metric: shared `gems57.evaluate_holdout`, pooled alpha 0.2 / beta 0.8,
  300 m triangular kernel, pixel-exact visible mask. Paired 20 km block-cluster
  95% percentile CI, 1,000 bootstrap draws seed 70501; `withheld_positive_pixels` and
  evaluator hash in every result. No organizer score is inferred.
- Comparators: **P4 frozen candidate** for B′; H33 reference for B′ (as archived) and
  fully regenerated *visible-only P4* for A. Note frozen H33 is not a fair A comparator
  because its full-catalogue spacing used hidden components. A candidate must exceed
  visible-only P4 on A and H33 on B′ with both paired CI lower bounds above 0,
  not just beat a random control. B′ SGMC is an imperfect stand-in for hidden truth.
- Literal parallel-run uniqueness: calculate **forward** 3-px dot overlap >0.70 and Spearman
  >0.90 (not the inherited mutual-overlap reinterpretation) against hash-pinned registry.
  A hash-verified archived binary lattice is already known to cover all erosion-valid pixels
  within 3 px; reconfirm on raw bytes and **STOP before any binary dot placement if so**.
  A continuous surface can be format-validated for scientific review, but do not call it a
  cleared dot submission or a recommended weekly-slot candidate. Record both readings.
- Budget: one experiment here; <=3 experiments or 2h total. No DrivenData slot used. No
  automatic selection: any future promotion must be separate and check the page's weekly cap.
- File: a *new* TIFF can be published **for review only** after shared writer/validator checks,
  with name containing `DO-NOT-SUBMIT`. Landing page must show `download=yes, submit=no`.
  Do not relabel a research artifact as a winner, score or a dot-unique submission.
