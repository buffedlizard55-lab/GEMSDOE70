# Preregistered hypotheses E2 — 2026-10-20 (experiment 2 of max 3)

Written **before** the E2 experiment. Geological hypotheses, not discoveries or
predicted scores. E1 (magnetic-edge termination, HOLDOUT-DTI 0.01019, worse than
its random control 0.04717) is archived in
`evidence/history/e1-contact-termination-20261020/` and is **not** retuned here.
No weekly slot is used by this session; slot selection is a separate step.

## Lane

The supplied prompt contains no identifiable single method paragraph assigning
a lane (same irregularity as E1). Provisional narrow E2 lane, declared here
before any E2 result: **signed DEM scarp curvature gated by geodetic strain
partitioning and shallow basement cover, with rank-ordered minimum-distance
dotted emission**. Only the first-ranked hypothesis below is tested as E2.

## Why the archived champion scored (evidence summary)

Full forensic receipt: `docs/h33-analysis.md` + `evidence/h33_audit.json`
(DATA-MEASUREMENT; the 0.2778 value itself is user/family-reported, **not**
ORGANIZER-CONFIRMED in this session — no submission-page receipt). Measured:
H33 (37,654 binary dots) = H27 minus every dot within 2 px of the catalogue;
nearest dot √5 px (≈224 m) from the catalogue; median distance ≈1.97 km.
Under the official distance-weighted Tversky definition (verified 2026-10-20
against the organizer problem page: α=0.2, β=0.8, triangular kernel R=300 m),
sparse dotting preserves kernel coverage `T` while cutting emitted mass
`S−M`, and flank pruning removes near-pure false-positive mass next to masked
known faults. That emission-efficiency mechanism is conditional algebra, not
causal proof about hidden faults. Beating it therefore requires a **better
ranking and/or better emission**, not a renamed/pruned copy (forbidden, and
checked by the uniqueness gates below).

## Five untried candidate hypotheses (this repo)

"Untried" = not run in GEMSDOE70 (E1 tested only magnetic termination).
Novelty is relative to inspected GEMSDOE70 + vendored `gems57` template code,
not an exhaustive claim over private parallel sessions. All five use only the
SHA-pinned cached 19-band stack (bands below) — **no new external data is
required**, so no obtainability blocker applies. Mirrors are integrity-pinned,
not organizer-authenticated (see Limitations).

| Rank (expected DTI gain ÷ cost) | Hypothesis / layers (1-indexed bands) | Physical signature | Why a catalogue omission is plausible | Named non-fault mimic | Difference from implemented work | Cost |
|---|---|---|---|---|---|---|
| 1st — TEST AS E2 | **Scarp–strain–cover**: detrended elevation (12), geodetic 2nd invariant (4), shear rate (7), dilatation rate (8), depth to basement (15); band 19 slope as control arm | Strike-coherent profile-curvature scarp step in detrended DEM, weighted by structure-tensor coherence, inside actively straining corridors with shallow-to-moderate cover (scarp preserved) | Low-relief alluvial scarps missed by legacy field/air-photo mapping remain as curvature steps; strain gate rejects inactive geomorphic scarps | Lake-shoreline / fluvial terrace riser; road cut | E1 used only RTP/gravity/basement (no DEM, no geodesy). Template anatomy fits catalogue halos, not DEM curvature × strain. Family lidar lanes used unsigned 1 m step ridges without strain/cover interaction; H33 lineage used unsigned multi-layer Hessian consensus + fixed stride. E2 uses signed-geometry curvature + coherence, geodetic gating, cover interaction, rank-ordered min-distance emission | Low–medium; cached stack, CPU |
| 2nd | Tip process-zone with displacement–length deficit: catalogue geometry (visible only) + detrended elevation (12) confirmation | Along-strike tapered extensions at tips of long faults whose length implies unmapped continuation; DEM scarp required | Mapping stops where scarp fades under alluvium; fault continues blind | Drainage lineament beyond a tip | Template fits whole-trace halos; prior tip/stepover analog matching scored well in family reports but overlaps E2 uniqueness risk and rewards continuations the detached holdout discounts | Low; high registry-overlap risk |
| 3rd | Tilt-phase offset: tilt/total curvature (6), TMI gradients (3, 9), gravity HG (18) | Amplitude-normalised magnetic tilt zero-crossing laterally offset where crossed by a gravity lineament (faulted contact) | Buried contact offset with no DEM scarp | Remanence boundary in a volcanic flow | E1 used depth-biased unsigned RTP gradient *amplitude* change; Euler-cluster lanes used point solutions, not phase-continuity breaks | Medium; potential-field blur vs 300 m kernel (E1 canary AUCs 0.52–0.54 warn weak) |
| 4th | Conductive breach: conductivity (17), depth to basement (15), RTP (2) | Narrow conductor *cross-cutting* basement contours (fluid/alteration pathway) vs basin-parallel stratigraphic conductor | Geothermal upflow fault under cover, no rupture | Saline groundwater / playa conductor | Family conductivity products used co-located ridge agreement, not a cross-cutting-angle test | Medium; conductivity resolution likely km-scale |
| 5th | Seismicity-aligned lineament: earthquake distance (10), intensity (16) + DEM curvature (12) | DEM lineaments collinear with directional seismicity fabric (active blind structure) | Seismogenic fault without Quaternary scarp, absent from Qfaults | Volcanic / geothermal-field swarm without through-going fault | No inspected lane uses the earthquake bands as primary gate | Low; 100 km kernels likely too smooth for 300 m localisation |

## Fixed E2 experiment (no post-hoc tuning)

- **Grid/footprint/catalogue**: vendored `gems57.grid.load_grid` on
  `.cache/data` (EPSG:32611, 3730×3292, 100 m). Features from
  `.cache/data/training_features.tif` SHA-256
  `4371c82e…23bc5` (re-verified this session). Nodata sentinel ≤ −1e30 and
  non-finite → invalid; sentinels never emitted.
- **Valid/fill (fixes the E1 boundary-fill limitation)**: valid = footprint ∩
  finite(all used bands). Nearest-finite fill is computed from the *original*
  finite domain, filters run on the filled field, and only then is output
  support eroded by 12 px. Ranks use average ties over eroded valid only.
- **DEM scarp** (catalogue-independent): Gaussian σ=1 detrended elevation →
  gradient slope; profile curvature along the gradient from the Hessian;
  structure-tensor coherence (σ=2 tensor smoothing).
  `scarp = sqrt(rank(slope)·rank(|profcurv|)) · (0.25+0.75·coherence)`, ranked.
- **Strain corridor**: ranks of σ=5-smoothed 2nd invariant, shear rate and
  |dilatation rate|; geometric mean, ranked. **Cover**: `shallow = 1 −
  rank(σ=3 depth-to-basement)`.
- **Joint ranking**: `rank( scarp^0.60 · strain^0.20 · shallow^0.20 )` (ranks
  floored at 1e-6). Fixed ablations: no-strain (0.75/0.25 scarp/shallow),
  no-cover (0.75/0.25 scarp/strain), no-coherence scarp. Control arms: every
  raw band above + band-19 slope, each derived feature alone, and a seeded
  random dotted control with identical budget/exclusion/spacing.
- **Leakage canary first**: every raw and derived feature alone gets holdout
  AUC; any max(AUC, 1−AUC) > 0.90 stops the run as suspected leakage.
- **Holdout (shared tools, untouched seed)**: `buffered_component_draw`
  seed **30** (E1 used 20), whole components, 3 px feature collar, 12 px
  boundary erosion; catalogue-derived masks/distances from *visible* faults
  only; visible faults masked pixel-exactly; pooled DTI via
  `evaluate_holdout` (`gems57-pooled-hide-v2`, α=0.2, β=0.8, R=300 m), 1000-draw
  paired 20 km-cluster bootstrap (seed 70030). Primary endpoint is **dotted**
  HOLDOUT-DTI; continuous top-2% DTI is reported only for E1 continuity.
  The archived H33 dot field is scored on the same folds as a *reference arm
  with declared catalogue-leakage caveat* (its pruning used the full
  catalogue including withheld traces), never as the promotion bar.
- **Emission (fixed rule)**: candidates ordered by joint rank descending;
  accept greedily with minimum separation 2.8 px; allowed = eroded valid,
  off-catalogue, distance-to-catalogue > exclusion. Selection grid budgets
  {20k, 30k, 38k, 45k} × exclusions {>0, >1, >2, >3 px} scored on the holdout;
  pick max pooled dotted DTI (tie → smaller budget, then smaller exclusion).
  All 16 cells are reported. Final dots re-emit the selected cell against the
  *full* catalogue. Values are binary float32 {0,1}, 0 outside footprint and
  on the catalogue (all-finite zeros export; shared writer rejects any
  non-finite/out-of-[0,1] value without repair).
- **Uniqueness (shared `uniqueness` two-phase summary, both readings
  reported)**: Spearman rank correlation on the surface and on final dots vs
  every locally hash-verified registry raster (62 rasters from pinned
  60GEMSDOE `3202471…` + 17GEMSDOE dense witness `ab0a0a62…`); 3 px dot
  overlap gated like-for-like on dot fields (support ≤20% footprint) with the
  inherited thresholds (ρ>0.90 or overlap>0.70 = duplicate → stop). The
  literal reading (dense continuous surfaces count every positive pixel as a
  dot, saturated by construction) is reported for completeness, not used as
  the dot gate — this is the shared template's own `two_phase_summary`
  distinction, disclosed here, not a private fork. Checked on the surface
  before placement and again on final dots. The inherited full inventory
  lists 862 unique grid rasters; only the 63 locally present bytes are
  checked here, so full-inventory certification remains a selector step.
- **Promotion gates (all required, else verdict negative)**: canaries pass;
  selected joint dotted DTI beats the matched random control with paired 95%
  CI excluding 0; beats every single-feature dotted arm point estimate;
  uniqueness like-for-like passes pre- and post-placement; shared-writer TIFF
  validates on disk (no NaN in footprint, values in [0,1], CRS/shape/transform
  match sample, zero on catalogue/outside footprint). Promotion means
  "downloadable candidate for selector review", never slot authorization or
  an organizer score. Every number is labelled HOLDOUT-DTI (evaluator,
  withheld positives, CI) unless copied from an organizer receipt (none here).
- **Budget**: E2 is experiment 2 of ≤3, ≤2 h compute. No competition upload.

## Scientific limits

DEM curvature steps are not verified fault slip; terraces, shorelines and
cultural features mimic scarps. Geodetic strain is a smooth corridor prior,
not trace localisation. Depth-to-basement is an inversion product that may
share priors with gravity/magnetics. Holdout recovery of withheld *catalogue*
components is a surrogate for expert-mapped hidden faults, not the hidden
truth. No geothermal vent, temperature, permeability or resource is claimed;
the competition target is fault traces (organizer problem page, verified
2026-10-20). Official manual-review links: problem/metric/format
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>,
about <https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/>,
data <https://www.drivendata.org/competitions/306/competition-doe-gems/data/>,
leaderboard <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
(JS-rendered; standings unverified here), reference solution
<https://github.com/drivendataorg/gems-prize-reference-solution>, GeoDAWN
<https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>,
INGENIOUS <https://gbcge.org/current-projects/ingenious/> and GDR 1391
<https://gdr.openei.org/submissions/1391>, EPSG:32611 <https://epsg.io/32611>,
challenge report <https://docs.nlr.gov/docs/fy26osti/96647.pdf>.
