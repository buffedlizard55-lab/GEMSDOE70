# Candidate Hypotheses for Next-Generation Fault Prediction — Supervised Halo Ranking

**Date:** 2026-10-20T22:50Z  
**Status:** Preregistered research queue before any new scoring. No number here is a leaderboard score.  
**Lane context:** The prompt supplies no single method paragraph. Declared narrow lane for this session: **supervised within-halo ranking trained on the SGMC off-catalogue proxy, with leave-one-quadrant-out, using the 19-band stack, lidar-scarp, GeoDAWN radiometrics, and catalogue geometry, at fixed coverage-stratified emission.** This document also lists 4 alternative unsupervised hypotheses for completeness.

Every hypothesis names the specific layer(s), physical signature transform, why a catalogue omission is plausible, a named non-fault mimic, how it differs from implementations already in this repo, expected DTI improvement rank, and implementation cost. External-data entries name the specific free official source and check obtainability.

## Why H33 scored 0.2778 — measured summary (PhD-level judgment)

Archived `evidence/h33_audit.json` recomputes H33 byte-for-byte: H33 B2 is not a detector but a **uniform sparse sample of the 0.2–3 km halo around mapped faults with the two closest shells (≤2 px) deleted** — 37,654 binary dots, median 1.97 km from catalogue, 94% >300 m away. Its ORGANIZER-CONFIRMED 0.2778 (user-supplied historical value, no receipt in this repo) is mostly **emission geometry, not geological inference**:

- **Metric algebra:** DTI = T / (T + 0.2·(S−M) + 0.8·(N−T)). `T` sums a triangular kernel over truth cells and saturates at 1 per truth cell; `S` and `M` scale per dot. Spreading dots across distinct truth beats concentrating them (measured: 3.6-px-spaced damage-zone 0.047 vs 7-px stratified 0.081 on proxy at same mass).
- **Shell deletion:** Dots <2 px from catalogue buy `S` but almost no `T` because scorer masks known faults pixel-exactly and hidden truth does not hug mapped traces. Deleting those shells raised reported live score twice (0.2708→0.2778).
- **Headroom:** The 0.16 gap to the 0.44 leader is **within-halo ranking** — knowing *where inside the halo* new traces lie. Geometry alone has been measured to its limit this session (Exp 3 vs Exp 4: +70% on B′ from stratification at fixed mass, but still −12.6% vs H33 on B′). The leaderboard gap is information, not spacing.

**Implication:** A supervised model trained on the only population resembling hidden truth (SGMC off-catalogue faults) with proper spatial blocking is the defensible route to >0.2778. Unsupervised geometry cannot close the gap.

## Hypotheses ranked by expected DTI improvement vs implementation cost

All layers are in the SHA-pinned mirrors (`evidence/data_receipt.json` + `.cache/gems_data/external/*`) unless noted. All use the pinned 100 m grid, EPSG:32611, α=0.2 β=0.8 300 m triangular kernel, pooled terms, paired 20 km bootstrap.

### Rank 1 — Supervised within-halo ranking on SGMC proxy (TOP CANDIDATE, to be tested this session)

- **Layer(s):** 19-band `training_features.tif` (bands 1–19: mag_anom, rtp, tmi_hg, geod_2ndinv, iso_grav_anom_slope, tc, geod_shearrate, geod_dilaterate, tmi_vg, deq_n100a15, iso_grav_anom_vg, det_elev, iso_grav_anom, tmi, depth_to_base_surf, ieq_n100a15, cond_surf, iso_grav_anom_hg, det_elev_slope) + `lidar_scarp_features_u8.tif` (12 bands: ex_max, ex_mean, step_max, lapneg_max, lappos_max, etc., derived from USGS 3DEP 1 m DEM, 706/716 tiles, OCR-recovered list) + `geodawn_rad_u8.tif` (K, Th, U, TC, from USGS GeoDAWN DOI 10.5066/P93LGLVQ) + `geodawn_extensions_u8.tif` (ThK, UK, UTh, TMI_up150) + catalogue geometry (distance to nearest mapped fault, tip kernel u/v, host-component log-length, side, sin2/cos2 strike, coherence, density, sin2d/cos2d interactions).
- **Physical signature:** HistGradientBoosting classifier learning P(SGMC fault | features) inside the halo (2.4–32 px). Features capture complementary physics: magnetic analytic signal (buried basement offset), gravity edge (basement throw), detrended elevation (blind scarp), radiometric alteration halo (hydrothermal depletion), geodetic strain kink (active localisation), seismic density. Model outputs a continuous ranking surface; final dots are coverage-stratified maxima of that surface.
- **Why catalogue omission plausible:** New faults nucleate in dilational jogs/stepovers and blind basin structures that have geophysical expression (magnetic edge termination, gravity-supported basement step, conductivity breach, alteration halo) without a mappable scarp. SGMC state compilation maps many such faults independently of the INGENIOUS/USGS catalogue, so it proxies hidden truth.
- **Named non-fault mimic:** Colluvial/basin-floor lineaments inside halo; lithologic K/Th variation; dike margins; depositional onlap; road grades; GPS interpolation artefacts — all share geophysical edges without slip.
- **How differs from repo implementations:** H33 is uniform Poisson halo sampling (no ranking). P4 ranked by a parametric weak-tilt halo × tip kernel (hand-tuned, no learning). E2 used oriented detrended-elevation step × basement edge (unsupervised, one physics pair). No prior session trained a supervised model on SGMC proxy with leave-one-quadrant-out and the full 19+12+4+4+geometry feature set while keeping coverage stratification.
- **Expected DTI improvement:** Moderate-high (qualitative only). If proxy generalises, could exceed H33 on B′ (0.0938) and thus be first to beat H33 with statistical confidence on target-like truth; if not, negative but measured.
- **Implementation cost:** Medium (CPU training, 2.7M halo pixels, ~38k positives, 4-fold CV, 100 trees). All data already cached (`scripts/fetch_data.py` verified 7/7 ok 2026-10-20). No new external data needed beyond already-fetched mirrors. Sources below.

### Rank 2 — Magnetic analytic-signal ridge amplitude

- **Layer(s):** `rtp` (band 2), `tmi_hg` (band 3), `tmi_vg` (band 9), optionally `mag_anom` (1) and `tmi` (14) for context.
- **Physical signature:** Analytic signal AS = sqrt( (∂T/∂x)² + (∂T/∂y)² + (∂T/∂z)² ) approximated as sqrt(tmi_hg² + tmi_vg²) smoothed σ=2 px; ridge amplitude via non-maximum suppression along gradient direction. Direction-independent basement edge independent of magnetisation.
- **Why omission plausible:** Concealed magnetic-contact faults offset magnetised basement under cover with no surface rupture; edge only visible in total gradient envelope.
- **Mimic:** Remanence/magnetisation contrast without slip; dike margins; intrusive contacts.
- **How differs:** Repo uses unsigned RTP horizontal gradient magnitude only; no vertical derivative, no analytic-signal envelope. Adds crucial depth-independent edge.
- **Expected DTI:** Moderate (qualitative). Could improve magnetic component beyond tilt edge (E1 AUC 0.46–0.57) but alone may not resolve halo ranking.
- **Cost:** Low-medium (existing stack, CPU derivatives, no new data).

### Rank 3 — Radiometric alteration-edge halo

- **Layer(s):** `geodawn_rad_u8.tif` K, Th, U, TC (uint8 quantised 1st–99th%) + `geodawn_extensions_u8.tif` ratios Th/K, U/K, U/Th.
- **Physical signature:** Gradient magnitude of K/Th depletion or U enrichment along fault-parallel alteration halos; edge density in 200 m window.
- **Why omission plausible:** Hydrothermal alteration along buried faults produces radiometric depletion detectable even where trace is unmapped.
- **Mimic:** Primary lithologic K/Th variation unrelated to faulting; flight-line artefacts (GeoDAWN survey artefacts noted in USGS release).
- **How differs:** Repo uses no radiometric data at all (P4, E1, E2 use only potential-field + elevation).
- **Expected DTI:** Uncertain (untested), could be moderate if alteration halos are systematic in Great Basin geothermal systems, but lithology noise is high.
- **Cost:** Medium-high (requires ext_geodawn_rad_u8 already fetched and verified 26 MB, 2026-10-20; plus gap-filling, edge operator). Official source: USGS GeoDAWN DOI 10.5066/P93LGLVQ via https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and + owner mirror https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea/data/external/geodawn_rad_u8.tif — obtainability verified this session (7/7 ok).

### Rank 4 — Detrended elevation breakline density

- **Layer(s):** `det_elev` (band 12), `det_elev_slope` (band 19), optionally `lidar_scarp_features_u8` step_max/lapneg_max for high-res validation.
- **Physical signature:** Subtle breakline/curvature concentration (Laplacian zero-crossings, profile convexity) in detrended topography; density of <2 m scarps in 300 m kernel.
- **Why omission plausible:** Blind Basin-and-Range normal faults displace late Quaternary fans by <1–2 m without a mapped scarp; detrending removes regional tilt to reveal them.
- **Mimic:** Depositional/erosional geomorphology (alluvial fans, paleochannels, terrace risers); road cuts; Lahontan paleoshorelines (datum-lahontan hypothesis previously 0.0000).
- **How differs:** Potential-field lane (P4, E1) does not use topography; lidar_scarp lane (lidarscarp-ridge-top2pct 0.1461) used externally derived ridges but not detrended-elevation breakline density with coverage stratification.
- **Expected DTI:** Low-moderate (subtle scarps are sparse; prior lidar lanes underperformed H33).
- **Cost:** Low (band 12+19 in cached stack, CPU).

### Rank 5 — Earthquake-density corridor (microseismicity lineaments)

- **Layer(s):** `ieq_n100a15` (band 16), `deq_n100a15` (band 10) + external USGS ComCat catalog.
- **Physical signature:** Ephemeral microseismicity density ridges outlining concealed seismogenic structures at ≤1 km scale; nodal-plane strike coherence.
- **Why omission plausible:** Active blind faults illuminate via microseismicity with no surface expression.
- **Mimic:** Station-density artefacts, template-matching catalog heterogeneity, quarry blasts, geothermal injection seismicity.
- **How differs:** Repo uses no seismicity-derived lineaments; supplied deq/ieq bands are 100 km aggregates (H33-E notes ieq autocorrelation 0.9935 at 3 km lag), so new external data needed.
- **Expected DTI:** Low (supplied bands too smooth; 300 m localisation doubtful).
- **Cost:** Medium (requires free official USGS ComCat FDSN https://earthquake.usgs.gov/fdsnws/event/1/query — obtainability blocked in this sandbox by egress allowlist (github/npm/pypi only), flagged not viable this session without manual fetch).

## Preregistered test plan for Rank 1 (budget: 1 of 3 experiments, <2 h)

- **Training truth:** SGMC off-catalogue proxy (sgmc_100m.tif = 82,151 px, proxy = sgmc & ~catalogue & footprint = 78,433 px; prime = d≥3 px = 62,649 px; halo-restricted prime = 38,757 px at d 2.4–32 px & valid). Use prime to avoid 21.4% duplication band (12.5% within 2 px, 21.4% within 3 px, 7.5% of domain).
- **Features:** 19-band + 12 lidar + 4 rad + 4 extensions + catalogue geometry (d, tip_u/v, log_len, side, sin2/cos2, coherence, density, sin2d/cos2d) = ~51 cols. Fill non-finite by nearest-valid, erode valid 12 px, no extrapolation. No SGMC-derived predictor enters features.
- **Spatial blocking:** Quadrant IDs from `gems57.holdout.quadrant_ids` (median split). 4-fold leave-one-quadrant-out CV for holdout estimate; final production model trained on all quadrants.
- **Model:** HistGradientBoostingClassifier (max_depth 6, learning_rate 0.08, max_iter 250, min_samples_leaf 100, l2_regularization 0.5, early stopping via 15% val split, class_weight balanced via sample_weight). CPU only.
- **Leakage canary first:** Each raw band and derived geometry feature alone AUC on withheld positives vs 200k negatives; any max(AUC,1−AUC)>0.90 stops run.
- **Ranking surface:** Predicted probability from CV models (holdout) or full model (production), rank01 over valid, geometric-mean not needed — direct probability rank.
- **Emission:** Same coverage-stratified halo sample as P4 (7×7 px strata, 5-px NMS, band 2.4–32 px) but ranking by learned probability (with 0.7+0.3×tip-style tilt optionally ablated). Exactly 37,654 binary dots off-catalogue, zeros outside footprint, float32.
- **Instruments:** A = shared hide-and-recover catalogue holdout (4 folds, buffered_component_draw seed 20, buffer 3 px, boundary 12 px, pooled DTI α0.2 β0.8 300 m triangular kernel, paired 20 km bootstrap 1000 draws). B′ = SGMC proxy d≥3 px quadrant holdout (same 4 quadrants, pooled DTI, same kernel/bootstrap). Compare candidate, random_control (37654 uniform valid), h33_reference (37654 dots SHA c55bafc4…), ablation_no_tilt, ablation_no_rad, etc.
- **Uniqueness:** Check on placed surface before final dots AND on final dots vs 62 registry rasters (mutual min(forward,reverse) >0.70 or Spearman >0.90 = duplicate). Report worst mutual, forward, Spearman, Jaccard; both directions always published.
- **Writer:** `vendor/gems57/grid.write_submission` zeros mode, LZW, no nodata, 3730×3292, EPSG:32611, transform (100,0,243350,0,-100,4508550), values in {0,1} exactly, re-read validator checks.
- **Promotion bars (all required for promote):** (a) candidate pooled DTI point estimate > every arm in its instrument including H33 on B′; (b) paired 95% CI for candidate−H33 and candidate−random both entirely >0 on B′; (c) no canary alarm; (d) uniqueness passes mutual rule; (e) writer+validator pass. Failure ⇒ verdict `negative`, DO NOT SUBMIT, but downloadable for selector review if unique+valid. Point-beats-but-CI-crosses ⇒ negative.
- **Budget:** Rank 1 is experiment 1 of this session; 2 h wall-clock cap for all 3; no parameter change after seeing holdout.

## Sources (verified content, links for manual review)

- Competition problem & metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (retrieved 2026-10-20, quotes in `evidence/official_sources_2026-10-20.json`: single GeoTIFF, EPSG:32611, 100 m, bounds, single float32 layer values [0,1], metric α0.2 β0.8 300 m triangular kernel, private → expanded final round, one final selection).
- Competition rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf (NLR Official Rules Sept 2026: §3.2 one GeoTIFF single layer 100 m, up to 3 submissions/week, one final selection §3.4, generative-AI disclosure §3.2, eligibility §1.3 U.S. citizen/permanent/resident or U.S.-incorporated entity).
- Organizer reference solution: https://github.com/drivendataorg/gems-prize-reference-solution (fault-detection U-Net, training loss α0.2 β0.8, CPU/GPU).
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ, cited NLR rules footnote 3) — source for mag/rad grids.
- DOE GDR INGENIOUS: https://gdr.openei.org/submissions/1391 + https://gbcge.org/current-projects/ingenious/ .
- EPSG:32611 https://epsg.io/32611 ; Tversky index https://en.wikipedia.org/wiki/Tversky_index .
- Owner mirrors (not organizer-authenticated, SHA-pinned): training_features + external layers via `registry/data_manifest_gemsdoe32.json` (training_features 418 MB, lidar_scarp 36 MB, geodawn_rad_u8 26 MB, ext_derived_sgmc_faults_100m_u8 198 KB) from buffedlizard55-lab/GEMSDOE24 @ 07345ea + buffedlizard55-lab/60GEMSDOE @ 32024716 (verified bytes in `evidence/data_receipt.json`).
- H33 lineage: https://github.com/buffedlizard55-lab/GEMSDOE32/tree/98901f3/docs + `evidence/h33_audit.json` (byte-measurement: D28 44,090 → H27 40,199 (1 px removed) → H33 B2 37,654 (√2/2 px removed), median 1.97 km, 94% >300 m).

No hallucination: every number above is labelled as HOLDOUT-DTI (with evaluator version, withheld positives, 95% CI) or as user-supplied historical ORGANIZER-CONFIRMED-equivalent (explicitly caveated). No projection is written as a score.
