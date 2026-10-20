# Preregistration — GEMSDOE70 experiments E2 (primary) and E3 (contingent)

Written 2026-10-20, **before** any E2/E3 feature was scored. E1 (magnetic-edge
termination) is frozen and negative; it is not rerun or tuned. This document is
hashed into the E2 experiment manifest at run time. Any change after first
scoring invalidates the run.

## Lane declaration (protocol rule 1)

The supplied prompt again contains no identifiable single method paragraph.
Declared lane for this session, one method only:

> **Subsurface-strike-guided alluvial step.** A blind basin fault warps young
> cover into a broad, one-sided detrended-elevation step whose strike parallels
> a magnetic basement edge. Rank by the oriented elevation mean-shift across
> the magnetic structure-tensor normal, corroborated by basement-depth edge
> magnitude. No catalogue-derived predictor enters the ranking.

Stay inside this lane. E3 (below) is a separate preregistered fallback lane,
run only under its stated contingency; it is not a blend with E2.

## Candidate hypotheses considered (ranked before implementation)

Qualitative expected-DTI ranking only; no number here is a score.

| Rank | Hypothesis / layers (19-band stack band numbers) | Physical signature | Why a catalogue omission is plausible | Named non-fault mimic | Difference from inspected implementations | Cost / external data |
|---|---|---|---|---|---|---|
| 1 (E2) | Alluvial step: `det_elev` (12), `rtp` (2) strike only, `depth_to_base_surf` (15) | Oriented mean-shift of smoothed detrended elevation sampled ±2 px along the RTP structure-tensor normal; geometric-mean rank with basement gradient magnitude | Basin-interior blind normal faults distribute throw over 200–400 m of fan/basin fill: no sharp scarp for geomorphic mapping, but a persistent one-sided step remains | Terrace riser, paleoshoreline, road grade | H33-A fuses Hessian line magnitudes + orientation order across six physics incl. external LiDAR/radiometrics; H33-B is valley chains; vendor geo uses slope/curvature scalars. None uses an oriented elevation *mean-shift* (asymmetric step) gated by magnetic strike. E1 used along-tangent magnetic-amplitude change, not a topographic step | Low; cached stack only, CPU |
| 2 (E3) | Magnetic source-depth step: `rtp` (2), `depth_to_base_surf` (15) | Cross-edge step (±2 px along tensor normal) of a multi-scale depth index `A3/(A1+eps)` (gradient magnitudes at Gaussian sigma 3 vs 1), rank-fused with basement edge | Vertical throw juxtaposes magnetic basement at two depths under cover with no surface rupture | Intrusive contact with depth change, remanence boundary | Euler lanes cluster isolated deconvolution solutions; this requires a *lateral step in depth index along a continuous edge*, not point clusters. Distinct from E1 termination (along-strike amplitude change) | Low; cached stack only, CPU |
| 3 | Strain-localization kink: `geod_2ndinv` (4), `geod_shearrate` (7), `geod_dilaterate` (8) | Ridge in the gradient of shear/dilatation ratio fields | Actively straining blind faults may localize geodesy before a mapped rupture exists | GPS/InSAR interpolation artefact, volcanic deformation | Vendor geo uses strain as a scalar plane, not a tensor-ratio kink ridge | Low cost but geodetic fields are smooth at km scale; 300 m localization doubtful. Not run this session |
| 4 | Signed magnetic profile jump: `rtp` (2), `mag_anom` (1), `iso_grav_anom` (13) | Discontinuity of signed RTP normal profiles across an along-strike break on a gravity boundary | Cover can hide a displaced magnetic contact | Remanence change inside a volcanic flow | Prior preregistration #2; unsigned termination (E1) already failed (canary AUC ≈ 0.525), so prior is weak. Not run this session | Medium; cached stack only |
| 5 | Sub-km seismicity lineaments: raw epicentres (external) + `deq/ieq` (10, 16) context | Collinear epicentre chains / nodal-plane strike density at ≤1 km scale | Microseismicity can illuminate blind active faults with no surface trace | Quarry blasts, geothermal injection seismicity, location-error streaks | Supplied seismic bands are 100 km aggregates (H33-E notes `ieq` autocorrelation 0.9935 at 3 km lag in GEMSDOE32 source, read 2026-10-20) | **Not viable this session.** Named free official source: USGS ComCat FDSN event service `https://earthquake.usgs.gov/fdsnws/event/1/query`. This sandbox's bash egress allowlist (github/npm/pypi only) cannot download it to a workspace file; no surface is fabricated. Requires a CI/manual fetch step with licence/attribution check before any future claim of viability |

No other external data is required by E2/E3. All E2/E3 layers are in the
SHA-pinned mirror stack (`evidence/data_receipt.json`); mirror consistency is
not organizer authentication.

## E2 frozen specification

Inputs (`.cache/data/training_features.tif`, SHA-pinned): band 12 det_elev,
band 2 rtp, band 15 depth_to_base_surf; canary-only comparators band 19
det_elev_slope. Grid/sample/catalogue from `.cache/data` via shared
`gems57.grid.load_grid`. Vendor code is byte-pinned and unmodified.

1. `valid0 = footprint & finite & |v|<1e18` for every used band.
   Fill non-valid cells by nearest-valid value **from `valid0`** (fixes the E1
   order flaw recorded in `docs/irregularities.md`: E1 eroded before filling).
   Output support `valid = binary_erosion(valid0, 12)` applied **after** all
   filtering. No output outside `valid`.
2. Elevation: `elev_s = gaussian(fill(det_elev), sigma=1)`.
   RTP tensor: gradients of `gaussian(fill(rtp), 1)`; tensor components
   smoothed at sigma=2. Normal angle `a = 0.5*atan2(2*Jxy, Jxx-Jyy)` (gradient
   direction, x = column axis). Coherence
   `sqrt((Jxx-Jyy)^2 + 4*Jxy^2)/(Jxx+Jyy+1e-12)`.
   Quantize `a mod pi` to 4 undirected axes (dy,dx): E–W (0,1), NE–SW (1,1)
   in image coordinates, N–S (1,0), NW–SE (1,-1), by maximum absolute dot
   product with `(sin a, cos a)` in (row, col) coordinates.
3. Step per axis: `|shift(elev_s,+2*axis) - shift(elev_s,-2*axis)|` by array
   slicing (no wraparound; 2-px border invalid, already inside erosion).
   Features: `step_oriented` (axis chosen by RTP tensor), `step_max`
   (maximum over 4 axes, orientation-free control), `coherence`,
   `basement_edge = |grad(gaussian(fill(depth_to_base),2))|`.
4. Candidate ranking: geometric mean of average-tie ranks of
   (`step_oriented`, `basement_edge`) over `valid`, re-ranked to [0,1].
   No catalogue array is read by the ranking code.
5. Holdout: shared `buffered_component_draw(grid, seed=20, buffer_px=3,
   boundary_px=12)` — identical folds/positives to E1 for paired
   comparability — plus a confirmatory `seed=21` draw reported for the
   candidate dots and H33 reference only (never used for tuning).
   Evaluator: shared `gems57.evaluate_holdout` (`gems57-pooled-hide-v2`,
   alpha 0.2, beta 0.8, 300 m triangular kernel), pooled terms, paired
   20 km spatial-cluster bootstrap, 1000 draws, seed 70020.
   Visible faults masked pixel-exactly by the evaluator.
6. Leakage canaries first: every raw used band and every derived feature,
   alone, AUC (and inverse) on withheld positives vs 200,000 sampled
   negatives (seed 70020 sampling as E1). Any `max(AUC,1-AUC) > 0.90` stops
   the run as suspected leakage; no joint interpretation.
7. Dot emission (primary endpoint): priority Poisson-style thinning —
   candidates in descending ranking order from the top 400,000 `valid`
   pixels, accept if no accepted dot within Euclidean distance < 2.8 px,
   until 38,000 dots or pool exhaustion. Binary value 1.0.
   Holdout dots use **no** catalogue exclusion (evaluator masks visible
   faults; dots on withheld truth are the signal). Final submission dots
   additionally require full-catalogue distance > 2 px (disclosed borrowed
   emission hygiene from the H33 lineage, not claimed novel), refilled to
   38,000 by continuing the same priority order.
8. Arms (all HOLDOUT-DTI, same folds/masks): candidate dots; candidate
   continuous upper-2% surface (secondary, E1-comparable); ablations
   `step_oriented` dots, `step_max` dots, `basement_edge` dots (same thin,
   same target N); random binary dots (38,000 uniform `valid` pixels,
   seed 70020, no thinning); reference dot fields scored as-is:
   H33 B2 (37,654 dots, SHA `c55bafc4…`), D2.8 (44,090, SHA `3e78737f…`),
   H19-5 solid (121,131, SHA `ef2ae808…`). Reference caveat: those fields
   were built with full-catalogue knowledge (incl. distance pruning), so
   their holdout values are *reference measurements on this instrument*,
   not clean generalization estimates; pruning near withheld faults can
   only remove their near-truth dots (conservative direction), while any
   catalogue-tuned ranking could favour them. Both directions are stated
   wherever the numbers are used.
9. Promotion bars (all required, candidate **dots**, primary seed-20 draw):
   (a) pooled DTI point estimate exceeds every arm in (8) including H33;
   (b) paired 95% CI for candidate-minus-H33 and candidate-minus-random
   both lie above 0; (c) no canary alarm; (d) uniqueness gates in
   `docs/protocol-revision-uniqueness.md` pass on surface **and** final
   dots within the disclosed subset scope; (e) shared writer + validator
   pass on exact bytes. Failure of any bar ⇒ verdict `negative`,
   **DO NOT SUBMIT**, no submission TIFF published as a download.
   Point-beats-but-CI-crosses-zero ⇒ `negative` (promising is not promoted).
10. Budget: E2 is experiment 1 of this session. Wall-clock cap 2 h for
    E2+E3 combined. No parameter is changed after seeing holdout results.

## E3 frozen specification (contingent)

Run **only if** E2 completes without a canary stop, E2 verdict is negative,
and ≥45 min of budget remains. Identical valid/fill/tensor/holdout/canary/
emission/promotion machinery as E2. Only the ranking differs:
`A1=|grad(gaussian(fill(rtp),1))|`, `A3=|grad(gaussian(fill(rtp),3))|`,
`depth_index=A3/(A1+1e-12)` smoothed sigma=1; `depth_step` = ±2 px mean-shift
of `depth_index` along the RTP tensor normal (same 4-axis machinery);
candidate = geometric-mean rank of (`depth_step`, `basement_edge`).
Ablations: `depth_step` dots, `basement_edge` dots (shared with E2),
random, H33. Same promotion bars. If E2 promotes, E3 is not run.

## What success would and would not mean

Beating H33 on catalogue hide-and-recover does **not** prove a higher live
score: live truth is expert-mapped *new* faults, not withheld catalogue
pieces, and family evidence (GEMSDOE32 site, read 2026-10-20) shows the two
instruments can disagree. Promotion here means only "ready for the separate
selector step + complete registry scan" (protocol rule 6). No projected
leaderboard number will be written as a score. Fault traces are the target;
no geothermal vent, temperature, permeability or resource is claimed.
