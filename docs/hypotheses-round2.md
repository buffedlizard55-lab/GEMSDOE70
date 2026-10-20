# Round-2 hypotheses — 2026-10-20 (preregistration for experiment 2)

Five geological hypotheses not tried in this repository. All use ONLY the 19
provided competition bands already restored and SHA-verified in `.cache/data`
(training_features.tif `4371c82e…23bc5`). No new external data is required for
any of them. Ranks are qualitative (no numeric score projections are made).

## Measurements that constrain the ranking (DATA-MEASUREMENT, this session)

300 m-lag (3 px) autocorrelation over the 5,167,373-pixel footprint, per band:

| Band | lag-3 corr | Band | lag-3 corr | Band | lag-3 corr |
|---|---|---|---|---|---|
| tmi_vg (9) | 0.6259 | tmi_hg (3) | 0.8086 | det_elev_slope (19) | 0.8018 |
| tmi (14) | 0.9515 | rtp (2) | 0.9550 | tc (6) | 0.9742 |
| deq_n100a15 (10) | 0.9757 | iso_grav_anom_vg (11) | 0.9821 | det_elev (12) | 0.9914 |
| iso_grav_anom_slope (5) | 0.9912 | mag_anom (1) | 0.9952 | iso_grav_anom_hg (18) | 0.9958 |
| cond_surf (17) | 0.9967 | depth_to_base_surf (15) | 0.9981 | iso_grav_anom (13) | 0.9988 |
| geod_dilaterate (8) | 0.9995 | geod_shearrate (7) | 0.9998 | ieq_n100a15 (16) | 0.9998 |
| geod_2ndinv (4) | 0.9999 | | | | |

Consequences (fixed before any round-2 evaluation):

- Geodetic strain and ieq carry no 300 m structure (lag-3 corr ≥ 0.9995). They
  are rejected as fault-scale localizers. This reproduces the H33-E finding
  (GEMSDOE32 `src/gems32/h33.py`: ieq 0.9935-correlated at 3 km lag) and extends
  it to all three strain bands. Smooth bands may only enter as regional
  allocation weights, never as ridge detectors.
- A dedicated TMI vertical-gradient lineament detector is untried: H33-A uses
  rtp/tmi/mag_anom but no tmi_vg/tmi_hg channel (verified in
  `build_h33a`); GEMSDOE32 derived channels use bands {2,12,13,14,15,17} only
  (verified in `features.py:need`); experiment 1 used rtp/gravity/basement.
- Registry filename search over all 862 unique rasters: zero filenames mention
  vertical-gradient/VG detectors; six mention strain (including 62GEMSDOE's
  440-dot strain submission, owner-report 0.0000), one mentions proba (the
  17GEMSDOE soft intermediate). Strain-as-localizer is both taken and
  negatively evidenced; VG is open.

## The five hypotheses

| Rank | Hypothesis / layers | Physical signature / transform | Why a catalogue omission is plausible | Named non-fault mimic | Difference from implemented work | Cost |
|---|---|---|---|---|---|---|
| First | Shallow magnetic lineaments: `tmi_vg` (band 9) | Sato/Frangi Hessian centerlines of VG accepting both polarities, OR NMS ridge of VG gradient magnitude (contact edges); NMS-thinned; sparse top-k dots with spacing + catalogue-distance prune | VG suppresses deep regional sources, so a fault juxtaposing shallow magnetized volcanics draws a sharp VG line while staying invisible in RTP and leaving no surface scarp under cover | Lava-flow margin, paleochannel magnetic lag, or E-W/N-S survey-leveling residual (checked by orientation diagnostic vs GeoDAWN N90°E flight lines) | No VG detector in H33-A..D, no VG derived channel in champion features, E1 used RTP termination × gravity × basement; H69/H70-C are relay/radiometric lanes | Low: one band, CPU |
| Second | Epicenter-anchored VG lineaments: `deq_n100a15` (10) + `tmi_vg` (9) | Local minima of distance-to-earthquake (epicenters) required to sit on/near a first-hypothesis VG centerline; dots at the anchored intersections | Microseismicity on a blind fault marks what mapping missed; the VG line proves a through-going structure rather than a point source | Quarry blast, volcanic swarm (no quarry map in hand: stated limit) | No family lane uses deq; H33-E declined ieq without testing deq | Medium: minima detection + association |
| Third | Strain-corridor allocation prior: `geod_2ndinv`/`geod_shearrate` (4/7) × first-hypothesis skeleton | Broad 2nd-invariant/shear weights reallocate the fixed dot budget toward high-strain corridors; the skeleton still localizes | Active blind faults concentrate where present-day strain is highest | Aseismic creep, magmatic/hydrologic deformation | Smooth bands used only as weights (never ridges); differs from 62/37/39/51 strain localizers | Low given the first |
| Fourth | Shallow density lineaments: `iso_grav_anom_vg` (11) | Same centerline detector as the first hypothesis applied to gravity VG | Basin-bounding step faults in cover carry a density contrast but no scarp | Buried channel, basement topography | E1 used horizontal gravity gradient magnitude/direction, not the VG band | Low |
| Fifth | 100 m slope-break scarps: `det_elev_slope` (19) | NMS ridge of detrended-elevation slope, thinned centerlines | Subtle or eroded scarps missed at mapping scale | Fluvial terrace, lithologic bench | 100 m competition-grid slope, not external 1 m LiDAR/10 m DEM scarp products; highest lane-collision risk, ranked last | Low |

No hypothesis needs new external data. The H33-E upgrade (raw USGS ComCat/FDSN
epicentres plus nodal-plane strikes) is explicitly NOT proposed here: usgs.gov
is outside this sandbox's network allowlist (verified by allowlist inspection
plus a failed direct retrieval attempt recorded in the experiment log), so
obtainability fails and the idea stays non-viable for this session.

## Provisional lane paragraph (experiment 2)

The supplied prompt contains no identifiable single-method lane paragraph
(continued irregularity IR-LANE-02). Provisional narrow lane for experiment 2:
**shallow-magnetic-contact lineaments from TMI vertical-gradient Hessian
centerlines (both polarities) OR'd with VG-gradient-magnitude contact ridges,
NMS-thinned, sparse top-k binary emission with 2 px spacing and a
catalogue-distance-greater-than-2 px prune.** Only the first hypothesis is
tested. Hypotheses 2–5 are a research queue, not extra experiments.

## Fixed experiment-2 specification (frozen before running)

- Inputs: band 9 (`tmi_vg`); footprint/catalogue geometry only (no catalogue
  values enter any ranking transform).
- Fill NaN by nearest-neighbor from the ORIGINAL finite domain, smooth σ=1,
  then erode the output support by 12 px AFTER filtering (repairs the
  boundary-fill limitation noted against experiment 1).
- Channel A: `|dominant Hessian eigenvalue|` of VG (both polarities:
  linear highs and lows), σ ∈ {1.2, 2.5}, pixel-wise max over scales.
  Synthetic-verified: a 3 px amplitude-5 line scores 1.88 vs 1.02 noise max.
  (An earlier draft used the least-|.| eigenvalue; synthetics showed it
  responds ~0 on true lines, so it was replaced BEFORE any run.)
- Channel B: concave-down-only dominant eigenvalue of `|∇VG|` (contact edges
  are gradmag maxima), same scales. Synthetic-verified: 0.24 on a contact
  step vs 0.01 background.
- Score: `max(rank01(A), rank01(B))` over the valid domain (fixed equal OR).
- Skeleton: 8-connected non-maximum suppression of score, `score > 0`.
- Orientation diagnostic: structure-tensor line direction at the EMITTED DOT
  locations (full-skeleton rose also reported); STOP as artifact-suspect
  (negative) if more than 50% of emitted dots falls within ±10° of E-W
  (GeoDAWN primary flight heading N90°E; Area 1 at 200 m, Area 2 at 400 m
  spacing; ties N-S at 2000 m — see the mirrored GeoDAWN report). Dots are
  the submitted artifact, so the gate binds them, not the noisy skeleton.
- Emission: skeleton ranked by score desc; greedy take with ≥2.0 px spacing
  from taken dots, distance-to-catalogue > 2 px, on-footprint, off-catalogue;
  cap 38,000 binary dots at 1.0, zeros elsewhere (finite everywhere; avoids the
  reported portal range error class).
- Holdout: shared `buffered_component_draw` + `evaluate_holdout` (byte-pinned
  template, unchanged), seeds 20 (comparability with experiment 1) and 71
  (fresh untouched blocks), both fixed here before running.
- Arms per seed: candidate, ablation-A, ablation-B, ablation-no-prune,
  experiment-1 candidate recomputed from `src/gems70/method.py` (same-split
  scientific best), mass-matched random unconstrained (E1 style),
  mass-matched random catalogue-avoiding (fair comparator), H33 dots
  (`c55bafc4…`, reference only).
- Canaries: raw `tmi_vg`, channel A, channel B, combined score — each alone,
  both seeds; `max(AUC, 1−AUC) > 0.90` stops the run as suspected leakage.

## Promotion decision rule (all must hold, else negative with no download)

1. Canaries clean on both seeds.
2. Candidate beats the recomputed experiment-1 surface on seed 20
   (non-overlapping 95% CIs; conservative, stated).
3. Candidate beats mass-matched catalogue-avoiding random on BOTH seeds
   (non-overlapping 95% CIs).
4. E-W artifact rule passes.
5. Candidate file bytes absent from all 862 indexed registry SHAs.
6. Spearman < 0.90 vs every checked raster (dense or sparse).
7. Forward 3 px dot overlap < 0.70 vs every checked SPARSE raster
   (positive support ≤ 10% of footprint; all verified submissions sit ≤ 3.35%,
   so any cutoff in (3.35%, 100%) gives identical verdicts — no tuning).
8. Shared-validator receipt plus single-TIFF ZIP round trip on the exact bytes.

## Explicit protocol revision R1 (scope clarification, not a threshold change)

The 0.90/0.70 thresholds are unchanged and no vendor byte is modified. The
dot-overlap clause is scoped to sparse registry rasters (≤10% positive
support); rank-correlation continues to be checked against every raster
including dense ones. Grounds, all evidenced: (a) the prior blocking witness
is a never-submitted soft HistGB probability surface trained on dilated
catalogue labels (17GEMSDOE sidecar: value range [0.00046, 0.984], no zeros;
`submission_meta.json` names F-ensemble, not E-proba, as latest), so it has no
dot set and cannot discriminate lanes by overlap; (b) excluding it from
overlap cannot weaken lane protection, because universal overlap carries zero
lane information; (c) rho against it is retained, so catalogue-memorization
rebuilds are still caught. The pre-R1 literal overlap number is still computed
and reported for transparency. Upstream report retained in evidence.

## Budget

Experiment 2 of at most 3; experiment compute tracked against the 2-hour
protocol budget. No competition upload and no weekly-slot decision is made
here; slot selection stays a separate step for the operator.

## Fixed randomness and artifact naming (amended before any run)

- All experiment-2 stochastic sampling (canary negative draws, mass-matched
  random controls) uses `numpy.random.default_rng(70071)`.
- Holdout bootstrap draws use the shared evaluator default (`seed=520810`
  inside `pooled_summary` unless overridden to 70071 — fixed here: 70071).
- Deterministic submission name: `gems70-vgshallow-h1-B2-38k` (no timestamp;
  reruns producing identical bytes are caught by the writer's no-overwrite
  rule and the registry byte check). Note template (≤140 chars, filled from
  measurements at write time):
  `VG-line H1 B2 38k dots; holdout-DTI s20 X [lo,hi] s71 Y [lo,hi]; fmt-valid`.
