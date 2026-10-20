# Preregistered hypotheses — 2026-10-20 (P5 update: 2026-10-20)

Written before each experiment. These are geological hypotheses, **not established discoveries or predicted scores**. This checkout originally had no implementation. Novelty is relative to that checkout and inspected GEMSDOE32/60/69 code, not an exhaustive claim across private parallel sessions.

No number here is ORGANIZER-CONFIRMED. All DTI below are HOLDOUT-DTI (gems57-pooled-hide-v2, 11,321 withheld catalogue pixels for A, 59,937 SGMC proxy pixels for B') or user-supplied historical values.

## Lane

The prompt refers to a single method paragraph, but supplies none identifiable as a lane assignment. Provisional narrow lane for Phases 1-4: **magnetic-edge termination at a gravity-supported basement boundary**. P5 remains inside the broader halo-stratification family (coverage-stratified sampling) but tests a catalogue-independent magnetic ranking inside the halo — the shared holdout protocol and mutual-overlap uniqueness gate are unchanged. Lane drift is measured: worst mutual overlap 0.30 (limit 0.70), worst Spearman 0.042 (limit 0.90) — no drift.

## What was measured to date

| Phase | Hypothesis | HOLDOUT-DTI A (11,321 px) | HOLDOUT-DTI B′ (59,937 px) | Verdict |
|-------|------------|---------------------------|---------------------------|---------|
| P1 (archived) | magnetic-edge termination at gravity-basement boundary | 0.0102 | — | negative |
| P2 | geophysically gated continuation prior | 0.0591 vs H33 0.0037, B 0.0432 vs 0.0906 | — | negative |
| P3 | damage-zone intensity × tip kernel (NMS 3.6px) | 0.0873 vs 0.0037, B′ 0.0471 vs 0.0938 | 0.0471 | negative |
| P4 | coverage-stratified halo 7px, weak tilt+tip (current best geometry) | **0.0730** [0.0667,0.0790] vs 0.0037 | **0.0812** [0.0723,0.0900] vs 0.0938 | negative (B′ -0.0126 [-0.0241,-0.0018]) |
| **P5 (this session)** | analytic-signal halo 7px, hg+vg rank + tip (candidate) | **0.0828** [0.0755,0.0895] vs 0.0037 | **0.0766** [0.0687,0.0852] vs 0.0938 | **negative** (B′ -0.0172 [-0.0278,-0.0063]) |
| H33 historical | D28 pruned halo sample (0.2-3km, shells deleted) | 0.0037 | 0.0938 | — |
| Leader claim | organizer leaderboard (js-rendered-unverified, 2026-10-20) | — | 0.4413 user-supplied, **not** organizer-confirmed | — |

P5 beats P4 on Instrument A (0.0828 > 0.0730) but loses on the pre-registered target-like gate B′. Neither instrument is the hidden truth; the gap to the claimed leader (0.44) is information inside the halo, not spacing.

## Five new candidate hypotheses not yet tried (beyond P1-P5)

Each was ranked before touching a weekly slot. Required external data is named and obtainability checked in this sandbox (see below).

| Rank | Hypothesis / specific layer(s) | Physical signature / transform | Why it should catch a fault **missing** from USGS/INGENIOUS catalogue | Named non-fault mimic that could also produce it | Difference from anything already implemented in this repo | Expected HOLDOUT-DTI improvement* | Implementation cost | External data needed (free, official, obtainable?) |
|------|--------------------------------|------------------------------|------------------------------------------------------------------------|--------------------------------------------------|----------------------------------------------------------|-------------------|-------------------|-----------------------------------------------------|
| **1 — tested P5** | **H-2 Analytic-signal ridge amplitude: `tmi_hg` (band 3) + `tmi_vg` (band 9)** | Analytic-signal amplitude `A = sqrt(hg²+vg²)` ridge; total gradient magnitude includes vertical derivative, independent of remanence direction. Edge-detection via amplitude magnitude + rank, not just horizontal gradient. | Buried magnetic-contact faults produce a gradient step in total field even with no topographic scarp and arbitrary magnetization direction; vertical derivative is insensitive to strike-parallel remanence that hides the contact in RTP alone. | Intrusive dike margin or isolated remanent anomaly without slip; cultural magnetic noise | P1-P4 used unsigned RTP horizontal gradient only (`_amp(rtp)` with σ1/σ2) or no magnetics at all (pure geometry P4 halo). P5 adds **vertical derivative** and analytic-signal envelope — a different physical quantity. | Moderate (+0.01 on A predicted; B′ uncertain) | **Low** — cached `.cache/gems_data/training_features.tif` bands 3+9 already present; CPU `hypot` + rank only | **None** — bands 3,9 in restored training_features SHA `4371c82e...` verified in this session (`evidence/data_receipt.json`) |
| 2 | **H-3 Radiometric alteration-edge halo: GeoDAWN `K`,`Th`,`U`,`TC` + ratios `ThK`,`UK`,`UTh` (ext_geodawn_rad_u8 + ext_geodawn_extensions_u8)** | Gradient magnitude of `K/Th` depletion or `U` enrichment; hydrothermal alteration halo edge. Transform: `ratio = K/(Th+eps)`, `edge = |∇ ratio|` (Gaussian σ2) + rank. | Hydrothermal alteration along a fault can be detected as a K-depletion halo even where the fault trace is blind, colluviated, or never mapped; radiometrics see the alteration, not the scarp. | Primary lithologic K/Th variation across volcanic contacts; agricultural K fertilization; flight-line leveling artifact | Repo until P5 used **zero** radiometric data. P4/P5 halo uses no chemistry at all. | Uncertain — potentially high if alteration is present in the area, but lithology noise is large | Medium-high — requires `ext_geodawn_rad_u8.tif` (4 bands) + `ext_geodawn_extensions_u8.tif` (ThK, UK, UTh) — **already fetched** 2026-10-20 to `.cache/gems_data/external/` (36 MB + 26 MB, SHA verified) | USGS GeoDAWN release DOI 10.5066/P93LGLVQ via owner mirror GEMSDOE24 — **obtainable: fetched this session, verified bytes** (see `scripts/fetch_data.py` manifest). No new download needed. |
| 3 | **H-4 Detrended-elevation breakline density: `det_elev` (band 12) + `det_elev_slope` (band 19) + lidar_sc `ex_max`, `step_max`, `lapneg_max`** | Breakline / curvature concentration: second-derivative Laplacian zero-crossings + edge density (Canny) in detrended topography. Transform: `curv = laplacian(det_elev)`, `break = |curv| * relief`, rank. | Blind fault scarps <2 m produce a subtle topographic break without a mapped trace; detrending removes regional tilt so the break emerges. Catalogue misses these because they are below photogeologic resolution. | Depositional fan edges, paleochannels, fluvial terraces, road cuts, plow lines | P1-P5 use no topography at all; lidarscarp bands have never been used in this repo except as a future note. | Low-moderate (+0.005-0.02) | Low — `det_elev` band 12 already in stack + lidar_sc 12-band stack already cached `.cache/gems_data/external/lidar_scarp_features_u8.tif` (36 MB, verified) | None — lidar_sc already present (`fetch_data.py` WANT ext_lidar_scarp_features_u8, SHA verified) |
| 4 | **H-5 Deep-conductive breach at magnetic truncation: `cond_surf` (band 17) × magnetic `rtp` edge** | Cross-cutting conductivity gradient intersecting a truncated magnetic edge: `breach = |∇ cond| * termination` where termination = along-tangent derivative of magnetic amplitude (P1 feature). | Fluid pathway along a buried fault breaches the conductive cover and truncates a magnetic contact — a joint EM/mag signature where neither alone is diagnostic. | Saline groundwater brine boundary, perched aquifer, clay pan | Previous conductivity use (GEMSDOE32) was a conductivity-ridge product, not a **breach at a termination**; no repo has crossed cond with the P1 termination field. | Low (uncertain resolution) | Medium — `cond_surf` band 17 already cached (but low resolution, inversion nonunique) | None — band 17 in training_features |
| 5 | **H-6 Basement-ramp curvature endpoint: `depth_to_base_surf` (band 15) + `iso_grav_anom` (band 13) + `det_elev`** | Along-strike curvature termination: `curv = second derivative of basement depth along gravity tangent`, `endpoint = |curv| * |∇grav|`. Transform: basement gradient with σ3, directional second derivative. | Blind basin-bounding fault displaces basement (basin thickness step) without a surface scarp; gravity supports the ramp, topography does not — the ramp ends where the blind fault ends. | Depositional onlap, erosional paleovalley, bedrock high — all produce curvature without fault slip | P1 used first-derivative basement_normal projection; P3 used distance tilt; none used **second-derivative curvature endpoint** operator. | Low | Medium — bands 15,13,12 already cached | None |

*Expected improvement is qualitative only (no projection is a score). Rank 1 was executed as P5 and measured above; ranks 2-5 are queued.

**Validation rule (enforced this session):** Top candidate (H-2) was validated on the spatially-blocked holdout (whole-component hide, 3 px buffer, 12 px boundary erosion, 20 km block bootstrap) **before** any weekly slot decision. It did not beat the current holdout best on B′ (H33 0.0938 vs P5 0.0766, Δ -0.0172 CI excludes zero), so **no weekly slot was spent** (`weekly_slots_used: 0`). This is the deliverable: a measured negative.

If a future candidate requires external data not in the WANT set, the specific free official source must be named and checked obtainable before proposing viability:
- USGS GeoDAWN airborne magnetic/radiometric: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ, cited in NLR rules footnote 3) — verified present in this session as owner-mirrored `training_features.tif` + external rad/extension tifs.
- USGS SGMC faults (proxy truth): State Geologic Map Compilation via NV Bureau of Mines and Geology county maps — used here as `sgmc_faults_100m.tif` proxy (12.5 % within 2 px of catalogue, 21.4 % within 3 px; contaminated band described).
- Nevada Bureau of Mines county geologic maps: https://pubs.nbmg.unr.edu/ — proposed for a genuinely independent additional-fault set (not yet fetched; would require buffer quantification at 1-6 px as next session).

## Fixed experiment that was run (P5)

- Catalogue-independent: magnetic `tmi_hg`, `tmi_vg` only for ranking; no catalogue-derived predictor for the magnetic rank.
- Halo band: `2.4-32 px` (240 m-3.2 km) from catalogue, same as P4 (measured optimal).
- Intensity: `(0.5+0.5*rank_analytic) * (0.7+0.3*tip)` where tip = `exp(-beyond/25)*exp(-|across|/8)` (same tip kernel as P2-P5).
- Placement: one dot per 7×7-px stratum at stratum maximum, 5-px NMS (two-pass fill if collisions reduce count), 37,654 binary dots off-catalogue.
- Canaries: each raw input and derived feature alone, AUC threshold 0.90 — measured analytic_amp AUC 0.531 (clear), tmi_hg 0.524, tmi_vg 0.518.
- Holdout: `buffered_component_draw` seed 20, whole connected components, four spatial quadrants, 3-px feature collar, 12-px boundary erosion. No catalogue-derived ranking.
- Evaluator: `gems57/evaluate_holdout.py` pooled terms, paired 20 km cluster bootstrap 1000 draws, 95 % CI. Catalogue recovery is not validation on hidden organizer labels.
- Uniqueness: before placement **and** final dots, vs 62 registry rasters, mutual overlap >0.70 and Spearman >0.90 gate — P5 worst mutual 0.30 (calib_h25ctx), worst ρ 0.042 — unique.
- Comparison: ablation (offset-only), random control, H33 reference on same folds.

## Scientific limits

Potential-field inversions are nonunique. Analytic-signal amplitude can reflect remanent magnetization or dike thickness rather than displacement; gravity and basement depth may share inversion priors. A high DTI on withheld catalogue components (Instrument A) rewards placing dots **beside** mapped traces — opposite to the competition task — and therefore cannot be promoted alone. Hydrothermal alteration K/Th patterns can be depositional. This test can falsify a useful ranking but cannot establish a geothermal vent, temperature, permeability, or economic resource. The actual target is new fault traces, as described by the organizer's fault-detection reference U-Net, not a vent catalogue.

## H33 in one sentence

H33 is not a detector: it is a uniform sparse sample of the 0.2-3 km halo around mapped faults with the two closest shells (1 px, √2/2 px) deleted — nine in ten dots >300 m from any mapped trace, median 1.97 km — and its 0.2778 historical score is emission geometry plus halo density, not geological inference. See `h33-analysis.md` for the byte-level audit.
