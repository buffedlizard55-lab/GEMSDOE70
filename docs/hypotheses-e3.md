# Preregistered experiment E3 — 2026-10-20 (experiment 3 of max 3, final)

Written before the E3 run, after E2 completed as a **negative** deliverable.
E3 is a new fixed hypothesis informed by E2 ablations, validated on untouched
folds. It does not retune E2 on E2 folds. No weekly slot is used.

## What E2 measured (all HOLDOUT-DTI, `gems57-pooled-hide-v2`, seed 30)

11,342 withheld positive pixels. Dotted primary endpoint (45k, exclusion >3 px):

- Joint scarp×strain×cover: 0.0598, 95% CI [0.0437, 0.0762] — **falsified**:
  paired Δ vs matched random +0.0073 [−0.0079, +0.0240] (includes 0) and
  significantly worse than scarp alone (Δ −0.0197 [−0.0340, −0.0058]).
- **Scarp alone: 0.0794 [0.0651, 0.0953]** vs random dotted 0.0525
  [0.0470, 0.0578] and band-19 slope 0.0309. Scarp canary AUC 0.6006 (no
  leakage; all E2 canaries ≤0.61). Cover gate direction was wrong (shallow
  AUC 0.468; shallow-alone DTI worst); strain gate also diluted
  (continuous: scarp 0.0321 > scarp×strain 0.0241 > joint 0.0121).
  Coherence weighting helped (joint > joint-nocoh, paired CI excludes 0).
- Archived H33 reference on the same folds: 0.0043 [0.0035, 0.0052]. Its dots
  were pruned using the full catalogue (including withheld traces) and target
  off-catalogue faults, so catalogue-recovery holdout actively penalises the
  live champion design. **Holdout is therefore a falsification instrument for
  ranking signal, not a live-score predictor.** No E3 live score (including
  any ">0.2778" claim) is asserted; 0.2778 remains user/family-reported, not
  ORGANIZER-CONFIRMED here.

## E3 fixed hypothesis

**DEM scarp curvature alone**: the exact E2 scarp field
(`sqrt(rank(slope)·rank(|profile-curvature|)) · (0.25+0.75·coherence)`,
ranked; detrended elevation band 12 only, catalogue-independent), with the
same rank-ordered 2.8 px dotted emission. Layers beyond band 12 enter only as
controls (band-19 slope; E2 joint as gating-harm control). Named mimic
unchanged: shoreline/terrace riser, road cut. Difference from family lidar
lanes: 100 m official-stack detrended DEM curvature+coherence (not 1 m DEM
unsigned step ridges), no catalogue halo, no Hessian multi-layer consensus.

- **Folds**: `buffered_component_draw` seed **40** (untouched; E1=20, E2=30),
  same buffers/evaluator; bootstrap seed 70040. Feature-alone AUC canaries on
  seed-40 folds first; >0.90 stops.
- **Selection**: budgets {30k, 38k, 45k, 60k} × exclusions {>0, >1, >2, >3 px}
  (60k added because E2 DTI was still rising at the 45k cap — disclosed
  range extension; live-prevalence caveat in the run card). Pick max pooled
  dotted DTI (tie → smaller budget/exclusion); report all 16 cells.
  Exclusion-trend caveat: the 3 px feature collar structurally favours larger
  exclusions on this instrument.
- **Comparators at the selected cell**: matched random dotted (seed 70040),
  band-19-slope dotted, E2-joint dotted. **Promotion gates (all required)**:
  canaries pass; scarp beats random with paired 95% CI excluding 0; scarp
  point estimate beats slope and joint controls; saturation-adjusted
  uniqueness passes (below) on surface and final dots; shared-writer TIFF
  validates on disk. Else verdict negative, no published TIFF.

## Uniqueness: saturation-adjusted like-for-like rule (disclosed)

E2 final dots vs champion H33: forward overlap 0.293, Jaccard 0.0104,
Spearman 0.0127 — distinct. Literal forward-overlap firings came only from
covering fields whose 3 px halos saturate the allowed domain (vendor
`saturation_certificate`, `evidence/saturation_certificates_e2.json`):
lattice-s5 halo covers 99.87% of allowed cells, r14 union 76.21%, r11 greedy
73.66%, dense proba 100% — while H33 covers 15.19%. When halo coverage ≥0.70,
*any* allowed dot set has expected forward overlap ≥0.70 by construction, so
the test cannot detect duplication (E2 lattice Jaccard was 0.0075 despite
overlap 1.0). E3 therefore gates as follows, reporting **all** readings:

- Spearman ≤0.90 vs all 63 hash-verified registry rasters (surface + dots);
- Jaccard ≤0.50 vs all dot fields;
- forward 3 px overlap ≤0.70 vs every **non-saturating** dot field
  (halo coverage of allowed <0.70 by vendor certificate);
- saturating fields are named individually with certificates; for them only
  Spearman + Jaccard gate (reverse overlap diagnostic).

The inherited literal gate still fires on saturating fields; that conflict is
reported, not hidden, and final slot use remains a selector decision
(including the outstanding full 862-raster inventory scan). An upstream
template report proposing halo-coverage classification is filed in
`evidence/upstream_uniqueness_report_e3.md`; `vendor/gems57` is not forked.

## Budget and limits

E3 exhausts the 3-experiment budget. DEM scarps are not verified slip;
holdout transfer to expert-mapped hidden faults is unproven (H33 lesson
above). Mirror data are hash-pinned, not organizer-authenticated. Promotion
means "downloadable candidate for selector review", never slot authorization
or an organizer score.
