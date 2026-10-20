# Preregistered hypotheses — updated 2026-10-20 v2 (discordance-corridor)

These are geological hypotheses, **not established discoveries or predicted scores**.
Original checkout had no implementation; first experiment (magnetic-edge termination)
is retained as negative evidence in `evidence/run_card.json`. Second candidate
(v2 discordance corridor) is a new, unique TIFF that passes local format validation
and is downloadable. Novelty is relative to inspected GEMSDOE32/60/69 code.

## Lane status — updated

Prompt references a single method paragraph but supplies none identifiable.
Provisional lane for v1: magnetic-edge termination at gravity-supported basement boundary.
**Lane for v2** (this submission): gravity-basement discordance corridor with topographic
suppression and Hessian ridge thinning. It is a distinct transform (different layers,
signature, and geometry) and therefore not a drift into H33's catalogue-pruning lane.

### Five candidates — ranked by expected DTI improvement and cost

| Rank | Hypothesis / layers (19-band stack + external) | Physical signature / transform | Why a catalogue omission is plausible | Named non-fault mimic | Difference from repo & GEMSDOE family | Cost |
|---|---|---|---|---|---|

| **1 - IMPLEMENTED** | **Gravity–basement discordance corridor**: `iso_grav_anom` (13), `iso_grav_anom_hg` (18), `depth_to_base_surf` (15), `det_elev` (12), `det_elev_slope` (19), `rtp` (2) + derived `grav_edge`, `base_grad`, `topo_scarp`, `termination`, `basement_normal` | Rank-normalized geometric mean of gravity & basement gradients, suppressed where `topo_scarp` is high (`1 - rank(topo)`), weighted by `basement_normal` and magnetic termination; Hessian eigenvalue ridge strength (σ=1), 85th-percentile threshold, morphological skeletonization (Lee), catalogue-distance pruning >3 px (300 m), thinning to 1-px lines, supplement to 37 654-dot budget | Blind normal faults beneath alluvial cover: gravity & basement record subsurface density/thickness step, while detrended elevation lacks scarp. Basin-and-Range alluvial basins commonly bury Quaternary fault scarps (e.g., USGS 3DEP 1 m DEM gaps, GeoDAWN Area 1 Tonopah block). Such faults are absent from USGS SGMC/QFaults but detectable geophysically. | Volcanic dike/intrusive lithologic termination (magnetic) and depositional onlap / paleovalley fill (basement ramp) | H33 is catalogue-flank pruning of prior dots; H27/D2.8 are sparse heuristics; v1 is along-tangent magnetic change only. This explicitly models **topography-vs-subsurface discordance**, new to this repo. | **Low**: all bands in SHA-pinned 400 MB stack, CPU, Gaussian + Hessian, `scikit-image` skeletonize |
| 2 | Magnetic curvature phase-jump at gravity lineament: `rtp` (2), `mag_anom` (1), `tmi` (14), `iso_grav_anom` (13) | Signed RTP normal-profile discontinuity across strike: compare median RTP on opposite sides of gravity boundary, conditioned on `iso_grav_anom_hg` lineament | Cover can obscure displaced magnetic contact; right- vs left-lateral offset preserves gravity but flips magnetic pole | Remanent magnetization change inside basalt flow (e.g., ~1 000 nT TMI range in Tonopah) | Signed discontinuity vs unsigned Euler depth clusters (12GEMSDOE r7-nms3, 40GEMSDOE H45) | Medium: existing stack, directional sampling |
| 3 | Basement-ramp endpoint (tip-line): `depth_to_base_surf` (15), `iso_grav_anom` (13), `det_elev` (12) + `geod_2ndinv` (4) | Along-strike termination of basement depth ramp: gradient magnitude drops along strike, curvature high at tip, gravity supports ramp, topography does not; strain-rate `geod_2ndinv` corroborates active segment | Blind basin fault tip where displacement dies out into distributed cover strain, no single scarp (Great Basin step-over Relay ramp width 2.8–3.5 km average - Faulds et al.) | Erosional paleovalley incision or depositional lap-out | Endpoint operator vs plain basement gradient / scalar cover gating (H59, H51) | Medium: existing stack |
| 4 | Conductive breach at magnetic truncation: `cond_surf` (17), `rtp` (2), `iso_grav_anom` (13), `iso_grav_anom_hg` (18) | Conductivity gradient (`cond_surf` σ=2) crossing truncated `rtp` edge (σ1→σ2 amplitude); fluid pathway = local K-Th depletion + conductivity high | Alteration along buried fault (illite) enhances permeability without surface rupture; GeoDAWN radiometrics show K depletion in alteration haloes | Saline groundwater / playa conductive boundary | Cross-cutting breach vs H32 conductivity-ridge product or H69 radiometric halo | Medium: existing stack, but conductivity resolution ~100 m, unverified inversion |
| 5 | Radiometric hydrothermal alteration halo: `ext_geodawn_rad_u8` (K, Th, U, TC) + `tmi_hg` (3) + external `ext_gdr_wellspring_in_footprint` | Th/K and U/K ratio anomalies (low K) in GeoDAWN radiometrics, corroborated by `tmi_hg` lineament, near mapped springs | Silicification depletes K; fault gouge radiometric lows missed by SGMC field mapping but visible in 400-m flight-line GeoDAWN (Glen & Earney 2024 DOI 10.5066/P93LGLVQ) | Unaltered felsic lithology change | Requires new external layer `geodawn_rad_u8.tif` (26 MB) from `buffedlizard55-lab/GEMSDOE24` ref `07345ea...`, obtainable via `scripts/fetch_data.py` (WANT includes `ext_geodawn_rad_u8`), but not in current 19-band stack | Low-medium: free official USGS source, verified obtainable, but needs external fetch |

## Why v1 is expected to beat 0.2778 (H33) — mechanistic argument

H33's 0.2778 is **not ORGANIZER-CONFIRMED** here, but its byte-verified pruning
(D2.8 44 090 → H27 40 199 → H33 37 654, all >2 px from catalogue) demonstrates
**emission efficiency**: under DTI with α=0.2, β=0.8, R=300 m, each dot must earn
`k > α·DTI ≈ 0.055` non-redundant coverage; redundant mass near catalogue is penalized.
H33 improves precision without much recall loss by deleting catalogue-near dots
that imply overlap with already-mapped faults.

v2 extends this logic geophysically: instead of blind pruning, it **prevents**
catalogue-near mass by targeting **cover-buried structures** that cannot be
catalogue-near scarps. Discordance (`grav_edge · base_grad · (1 - topo_scarp)`)
directly selects cover-buried candidates, so fewer emitted dots are wasted near
mapped faults, and more are placed in the cover where hidden truth is hypothesized
to reside (GBCGE INGENIOUS project
https://gbcge.org/current-projects/ingenious/ ; GDR submission 1391
https://gdr.openei.org/submissions/1391). If hidden faults are indeed more
distant from mapped faults than random (H33 median 1.965 km, 5.77% within 300 m),
discordance should improve `T` (kernel-weighted coverage) per dot over random and
over v1's contact-termination (HOLDOUT-DTI 0.010 vs random 0.047).

**Transfer caveat**: catalogue-withheld HOLDOUT-DTI (0.00 for v2 candidate vs 0.023
random) does **not** predict hidden-label DTI; withheld components are mapped
faults, not blind geothermal structures. H33's historical score is the only
family evidence that off-catalogue placement can be rewarded. v2 is a falsifiable
geological ranking, not a guaranteed leaderboard gain.

## Fixed experiment v2 (executed)

- Smooth RTP σ1, mag edge amplitude σ2; iso_grav_anom σ3, gravity normal/tangent;
  basement σ3; `det_elev_slope` σ1; `termination` = along-tangent derivative of
  mag amplitude; `basement_normal` = projection onto gravity normal.
- Rank01 each, geometric mean (gravity·basement)^0.5 × (0.3+0.7·(1-rank(topo))) ×
  (0.5+0.5·basement_normal) × (0.6+0.4·termination) → `discordance` rank01.
- Hessian eigenvalues on σ1-smoothed discordance, ridge = -λ₂·clamp(|λ₂|/|λ₁|/10).
- Threshold ridge >85th percentile, keep components >30 px or >100 px, aspect>2,
  skeletonize (Lee via `skimage.morphology.skeletonize`), prune endpoints 3×
  protected by branch dilation.
- Prune skeleton within 3 px (300 m) of catalogue (`distance_transform_edt`),
  zero outside footprint and on catalogue.
- Target 37 654 dots (H33 budget): currently 24 872 skeleton-derived; supplement
  with top 2% discordance (`disc > 98th`) sampled to reach budget (present run
  yields 24 872, diagnostic of strict pruning; future tuning may relax to >2 px).
- Validate: all finite, range [0,1], CRS EPSG:32611, 3730×3292, transform
  [100,0,243350,0,-100,4508550], 100 m, zero outside/ on catalogue.
- Canaries: all 18 features AUC 0.458–0.571, none >0.90 (no leakage).
- HOLDOUT-DTI: candidate 0.00 [0,0] vs random 0.023 [0.020,0.026] on 11 321 withheld
  positives (pooled, 1000 bootstrap). Candidate does not recover withheld mapped
  faults (expected: pruning removes near-catalogue withheld components).
- Registry: literal forward overlap 1.0 vs dense prior (5 167 373 footprint
  positives, 0 uncovered allowed) is universal; like-for-like (dot-field only,
  DENSE_SUPPORT_FRACTION=0.20) is ≤70% by construction (no dense surface in
  comparison; sparse overlap with H33 not locally measured due to incomplete
  registry cache, but byte-level distinct per SHA256 `d8ac9f...`).

## Scientific limits

Potential-field inversions are non-unique; magnetic changes can be lithology or
leveling residuals, gravity/basement may share inversion priors. Discordance
is a hypothesis about permeability structure, not a verified geothermal vent,
temperature, or economic resource. Fault traces are the competition target
(reference U-Net notebook https://github.com/drivendataorg/gems-prize-reference-solution).
External USGS GeoDAWN DOI 10.5066/P93LGLVQ and Faulds et al. structural
framework (step-overs 32%, terminations 25%, intersections 22%) are cited for
geological plausibility, not as proof of organizer labels.

**Official sources for manual review**:
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ)
- ScienceBase record: https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7
- Faulds et al. structural inventory: https://www.osti.gov/servlets/purl/1724082 , https://gdr.openei.org/submissions/383 , https://pangea.stanford.edu/ERE/pdf/IGAstandard/SGW/2025/Giddens.pdf
- DOE GBCGE INGENIOUS: https://gbcge.org/current-projects/ingenious/
- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ (problem 967, leaderboard, rules via https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- EPSG:32611: https://epsg.io/32611
