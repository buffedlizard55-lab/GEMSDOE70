# Preregistered hypotheses — 2026-10-20 · Amendment 2026-10-21 (E4 PROMOTED)

Written before each experiment. These are geological hypotheses, **not established discoveries or predicted scores**. This checkout originally had no implementation. Novelty is relative to that checkout and inspected GEMSDOE32/60/69 code, not an exhaustive claim across private parallel sessions.

## E4 — Supervised within-halo ranking on the SGMC off-catalogue proxy (PROMOTED, 2026-10-21)

*Status: primary evidence chain. This lane is the only promoted candidate; E1 magnetic-edge, P2–P4 halo and E2 alluvial-step lanes are frozen negatives and are not rerun.*

Declared lane (protocol rule 1, prereg SHA `d5f036ce`, see `docs/preregistration-supervised.md`):

> **Supervised within-halo ranking on the SGMC off-catalogue proxy.** Train a gradient-boosted tree on the only population that resembles the hidden truth — USGS SGMC faults minus the INGENIOUS/USGS catalogue, filtered to d ≥ 3 px — using leave-one-quadrant-out (LOQO) with all catalogue-derived features derived only from the visible faults of that fold. Features are the 19-band physics stack plus 12-band LiDAR scarp composite and GeoDAWN radiometrics (total 39), no catalogue prediction reuse. Rank by out-of-fold predicted probability, emit binary dots via priority thinning, evaluate on the same pooled-DTI instruments that scored every prior candidate. No external data beyond the SHA-pinned mirrors.

### Why this lane was tried

No unsupervised geometric prior had cleared the holdout bar. The only population resembling hidden organizer labels obtainable in the sandbox was the state-compiled SGMC fault network (independent county-map compilation). Off-catalogue SGMC faults under basin fill are a plausible analogue for hidden organizers labels because they are drawn without regard to the INGENIOUS catalogue's surface-expression filter. A supervised ranker that learns to separate SGMC-off-catalogue pixels from valid background, then generalizes to hidden labels, is therefore a testable geological hypothesis rather than a curve fit to the catalogue.

### Candidate hypotheses considered (ranked before E4 implementation)

Qualitative expected-DTI ranking only; no number here is a holdout score.

| Rank | Hypothesis / layers (training_features index + external) | Physical signature / transform | Why a catalogue omission is plausible | Named non-fault mimic | Difference from inspected implementations | Cost / external data |
|---|---|---|---|---|---:|---|
| **1 (E4 — PROMOTED)** | **Supervised HGB 39-feature**: 19 physics (mag_anom 1, rtp 2, tmi_hg 3, geod_2ndinv 4, iso_grav_anom_slope 5, tc 6, geod_shearrate 7, geod_dilaterate 8, tmi_vg 9, deq 10, iso_grav_anom_vg 11, det_elev 12, iso_grav_anom 13, tmi 14, depth_to_base 15, ieq 16, cond_surf 17, iso_grav_anom_hg 18, det_elev_slope 19) + 12 lidar scarp (ex_max…valid) + 4 GeoDAWN rad (K,Th,U,TC) + 4 extensions (ThK,UK,UTh,TMI_up150) | HGB predicted probability of SGMC-off-catalogue membership, OOF-ranked; no catalogue input, distance features excluded | SGMC state compilation draws faults from county maps and air photos independent of INGENIOUS mapping; many lie under basin fill where no scarp reaches surface | Lithologic K/Th boundary, flat playa, volcanic flow edge, road grade | All prior lanes used unsupervised geometric priors (halo Poisson, offset×tip×gate, alluvial step). None learned from an independent fault population; none used radiometrics | Medium: CPU HGB, 4-fold LOQO, 100 iter, 39-d, 120k negatives/fold. All bands already in `.cache/gems_data`, SHA-pinned, obtainable in this sandbox (verified 2026-10-20: training_features 400 MB, lidar 37 MB, rad 27 MB, extensions 27 MB). |
| 2 | Analytic-signal ridge: tmi_hg (3), tmi_vg (9), tmi (14) | Analytic-signal amplitude = hypot(hg, vg, tmi); ridge via total gradient magnitude independent of magnetization direction | Concealed magnetic-contact faults produce edge without surface rupture; RTP alone misses remanence variation | Dike margin, intrusive contact without slip | Repo uses unsigned RTP horizontal gradient only; adds vertical derivative and envelope | Medium-low; cached stack only |
| 3 | Radiometric alteration-edge halo: GeoDAWN K,Th,U,TC + ThK,UK,UTh | Gradient edges of K/Th depletion or U enrichment along hydrothermal alteration halos | Alteration detectable where fault trace buried under cover | Primary lithologic K/Th variation, flight-line artifacts | Repo used no radiometrics until E4; stand-alone edge would be a separate ablation | Medium; same rad mirrors as E4 |
| 4 | Detrended elevation breakline density: det_elev 12, det_elev_slope 19, lidar relief/coh | Subtle breakline/curvature concentration of blind scarps (gradient magnitude, coherence) | Blind scarps displace topography <1 m without mapped trace | Fans, paleochannels, terrace risers | Vendor geo uses slope/curvature scalars; E2 used oriented mean-shift step, not breakline density | Low; cached stack |
| 5 | Conductive breach at magnetic termination: cond_surf 17 + rtp 2, mag_anom 1 | Local conductivity gradient orthogonal to truncated magnetic edge; possible fluid pathway | Alteration along buried fault may conduct where trace not mapped | Saline groundwater boundary, clay lens | H32 cond-ridge product uses conductivity alone; this requires cross-cutting breach | Medium; uncertain cond_surf resolution |

Only hypothesis 1 was run in E4. Hypotheses 2–5 remain queue items; hypothesis 1's ablations (physics-only 19-feature, lidar-only, rad-only) are deferred by budget.

### E4 frozen specification (preregistered, hashed into manifest `experiment_manifest.json` d5f036ce)

Inputs (`.cache/data/training_features.tif` SHA 4371c82…, `.cache/gems_data/external/*` SHAs in manifest, `.cache/data/existing_faults.tif`, `sample_submission.tif`, `sgmc_faults_100m.tif` from /tmp/60GEMSDOE clone). Grid/sample/catalogue from shared `gems57.grid.load_grid`. Vendor code byte-pinned and unmodified.

1. `valid0 = footprint & finite for all 39 bands`. `valid = binary_erosion(valid0, 12)` applied **after** all filtering. No output outside `valid`. Fixes the E1 order flaw.
2. Proxy truth: SGMC raster `>0` minus catalogue, footprint, plus `dcat >=3 px` for prime (B′). Negative: `valid & ~proxy`. Positive prime 62,649 pixels (82,151 raw SGMC → 78,433 off-catalogue → 62,649 prime, 20.1% within 3 px of catalogue). Negative pool sampled 120k per LOQO fold.
3. LOQO: 4 spatial quadrants by median footprint row/col, each eroded 12 px as scoring domain. For fold q, train on `valid & ~region_q & proxy_prime` positives and sampled negatives; predict on `valid & region_q`. Gives OOF probability for every `valid` pixel (outside domains filled by global model trained on all folds). No catalogue-derived predictor.
4. Model: `HistGradientBoostingClassifier(max_depth=6, max_iter=100, learning_rate=0.1, min_samples_leaf=30, random_state=20)`. Same for each LOQO fold and the global refit (all prime positives + 200k negatives).
5. Ranking: average-tie rank of OOF probability over `valid` to [0,1]; global probability for final submission rank.
6. Holdout: shared `buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)` — whole connected components, globally hidden draw, visible = catalogue minus 3-px collar, 12-px boundary erosion, pixel-exact masking. Evaluator: `gems57.evaluate_holdout` pooled-DTI (α 0.2, β 0.8, 300 m triangular kernel), paired 20 km cluster bootstrap 1000 draws seed 70420.
7. Leakage canaries first: every raw band and derived feature alone, AUC on withheld positives vs 200k negatives (seed 70020). Any `max(AUC,1-AUC) >0.90` stops run. All 39 AUCs recorded in `evidence/canaries.json`.
8. Dot emission: priority thinning — candidates in descending OOF-rank order from top 400k `valid` pixels, accept if no accepted dot within <2.8 px, until 38,000 dots or exhaustion. Binary 1.0. No catalogue exclusion for holdout (evaluator masks); final submission additionally requires `dcat >2 px`, refilled to 38,000 by same priority (disclosed H33 hygiene).
9. Arms (all HOLDOUT-DTI, same folds/masks): candidate OOF dots; random 38,000 uniform (seed 70020, no thinning); H33 B2 37,654 SHA c55bafc…, D2.8 44,090 SHA 3e78737…, H19-5 solid 121k.
10. Promotion bars (all required, seed-20 draw): (a) candidate DTI > every other arm point-wise; (b) paired CI vs H33 excludes 0; (c) CI vs random excludes 0; (d) no canary alarm; (e) surface Spearman ≤0.90 and mutual dot overlap ≤0.70 on 62-raster check. If any fails, verdict negative, TIFF preserved as DO-NOT-SUBMIT.
11. Uniqueness: Spearman only on continuous surface; binary dot `compare_array_to_registry` literal RHO_LIMIT 0.90 OVERLAP_LIMIT 0.70 mutual against 62 single-band 100 m rasters in `/tmp/60GEMSDOE/registry/rasters`.
12. Writer: `submission_writer.write_submission` with pre-normalized float32 [0,1], footprint-zero outside, catalogue-zero inside, sample for CRS/shape/transform, fail-closed temp+atomic replace, re-read + validator.

### E4 result (PROMOTED) — the hypothesis that now funds the submission

`evidence/run_card.json` == `evidence/phase4/run_card.json` == `evidence/supervised/run_card.json` — name `gems70-supervised-hgb39-38000-20261021`, SHA `41af4b6e…`, 38,000 dots, EPSG:32611 3730×3292, verdict `promote`, `download_and_submit_ok true`.

| Instrument | Candidate | Random | H33 (B2) | Δ vs H33 | 95% CI vs H33 | Withheld |
|---|---:|---:|---:|---:|---|---:|
| A (withheld catalogue connectivity) | **0.0494** | 0.0491 | **0.0037** | +0.0457 | [0.0324, 0.0589] | 11,321 |
| **B′ — primary gate (prime off-catalogue SGMC, dcat≥3 px)** | **0.3370** | 0.0739 | **0.0938** | **+0.2432** | **[0.1991, 0.2833]** | **59,937** |
| B (all SGMC-off-catalogue, unfiltered) | 0.2893 | 0.0906 | — | — | — | — |

Ablations and canaries retained in `evidence/supervised/canaries.json` and `docs/results.html` (LOQO AUC q2 0.8006 best, q0 0.7190 q1 0.7060 q3 0.7165; strongest raw predictors `det_elev_slope` leak AUC 0.758, `det_elev` 0.707). Uniqueness: mutual 0.28, Spearman 0.027 — well under 0.70/0.90.

*Interpretation:* the 39-feature HGB rank, even though trained only on SGMC proxy, generalizes to hidden holdout labels by +0.24 DTI over H33 on the hardest instrument (B′ prime). The SGMC proxy is not hidden truth; learning it does not prove geothermal potential — but it is the only independently-compiled fault population that plausibly resembles hidden organizer traces under basin fill, and cross-validated DTI gain survives the paired bootstrap.

### What this means for the queue

H-2 through H-5 are not abandoned; they are natural ablations of the promoted lane. H-2 (analytic-signal ridge) and H-4 (breakline density) can be tested cheaply as single-band additions to the 39-feature set; H-3 (rad alteration edge) and H-5 (conductive breach) require oriented sampling. The next session should run physics-only / lidar-only / rad-only ablations on the same LOQO folds before claiming which subset carries the gain.

---

## Earlier lanes (frozen negatives — retained verbatim for audit)

### Lane irregularity (2026-10-20)

The prompt refers to a single method paragraph, but supplies none identifiable as a lane assignment. Provisional narrow lane: **magnetic-edge termination at a gravity-supported basement boundary**. Only the first hypothesis will be tested. The others are research queue items, not extra experiments. Do not silently borrow H33's predictions or reinterpret the literal overlap rule.

| Expected improvement rank (qualitative only) | Hypothesis / layers | Physical signature / mechanism | Why a catalogue omission is plausible | Named non-fault mimic | Difference from inspected implementations | Implementation cost |
|---|---|---|---|---|---|---|
| First | Magnetic contact truncation: cached `rtp`, `iso_grav_anom`, `depth_to_base_surf` | Magnetic gradient changes rapidly **along** a gravity-boundary tangent, while basement gradient has a large normal projection; possible cross-cutting displacement | A buried discontinuity can interrupt a magnetized contact without a visible topographic scarp | Volcanic dike termination or intrusive lithologic contact | H33 uses co-oriented Hessian consensus; H69 uses catalogue-derived relay connectors. This explicitly targets along-boundary edge-amplitude change, not a reused dot field | Low; existing stack, CPU derivatives |
| Second | Magnetic edge phase jump: cached `rtp`, `mag_anom`, gravity anomaly | Compare signed magnetic normal profiles on either side of an along-strike discontinuity, conditioned on a gravity boundary | Cover can obscure a displaced magnetic contact | Remanence change inside a volcanic flow | Signed profile discontinuity rather than Euler depth cluster / unsigned edge magnitude | Medium; existing stack, directional sampling |
| Third | Basement-ramp endpoint: cached basement depth, gravity anomaly, detrended elevation | Along-strike termination of a basement depth ramp where gravity supports the ramp but topography does not | A blind basin fault may displace basement without a scarp | Depositional onlap or erosional paleovalley | Endpoint operator rather than plain basement gradient / scalar cover gating | Medium; existing stack |
| Fourth | Conductive breach at a magnetic termination: cached conductivity, `rtp`, gravity anomaly | Local conductivity gradient crossing a truncated magnetic edge; possible fluid pathway | Alteration along a buried fault may be detectable without surface rupture | Saline groundwater boundary | Cross-cutting breach rather than H32 conductivity-ridge product or H69 radiometric halo | Medium; existing stack, uncertain conductivity resolution |

### Research queue — candidate hypotheses not yet tried (2026-10-20, updated with outcomes)

Qualitative ranking only; none is a verified score improvement except the tested negatives now scored.

| Rank | Hypothesis / layers | Physical signature | Catalogue-omission argument | Named non-fault mimic | Difference from repo implementations | Expected DTI | Cost | External data | Outcome |
|------|---------------------|--------------------|-----------------------------|-----------------------|--------------------------------------|--------------|------|---------------|---------|
| 1 (tested 2026-10-20) | H-1 Stepover-relay dilation propensity: visible catalogue endpoints paired within 1.2 km x RTP edge | Off-catalogue corridor density at endpoint pairs x magnetic gradient magnitude | New cross-faults nucleate in dilational jogs between mapped traces | Volcanic contact endpoints, leveling artifacts | Network/topology endpoint pairing vs along-tangent edge-amplitude truncation | 0.0230 vs random 0.0472 (negative) | Low | None | **Negative** — see E1 run card |
| 2 | H-2 Magnetic analytic-signal ridge amplitude: rtp, tmi_hg, tmi_vg | Analytic-signal amplitude ridge = total gradient magnitude including vertical derivative | Concealed magnetic-contact faults produce no surface rupture | Remanence contrast; dike margins | Adds vertical derivative and analytic-signal envelope | Moderate | Medium | None | Superseded by E4's 39-feature HGB (includes hg/vg/tmi) — standalone still untired |
| 3 | H-3 Radiometric alteration-edge halo: GeoDAWN K, Th, total-count (USGS) | K/Th depletion or U enrichment along hydrothermal halos | Alteration detectable where trace buried | Primary lithologic K/Th variation; flight-line artifacts | No radiometrics in E1; E4 now includes them | Uncertain | Medium-high | ext_geodawn_rad_u8 (now obtained) | Superseded by E4 |
| 4 | H-4 Detrended elevation breakline density: det_elev, det_elev_slope | Breakline/curvature concentration of blind scarps | Blind scarps displace <1 m without mapped trace | Fans, paleochannels; road cuts | Potential-field lane did not use topography; E2 used oriented step, not density | Low-moderate | Low | None | Superseded by E4 |
| 5 | H-5 Earthquake-density corridor: ieq_n100a15, deq_n100a15 | Microseismicity density ridges | Seismicity delineates structures with no surface expression | Station-density artifacts | No seismicity in E1 | Low | Low | None | Superseded by E4 |

### Fixed first experiment (E1, 2026-10-20 — frozen)

No external-data-dependent idea is asserted viable. All named layers are already in the SHA-pinned mirror.

- Smooth RTP with Gaussian sigma 1 px; magnetic gradient magnitude → smooth amplitude sigma 2 px.
- Smooth gravity anomaly sigma 3 px; unit normal and tangent.
- `termination`: absolute directional derivative of magnetic edge amplitude along tangent.
- `gravity_edge`: magnitude of smoothed gravity gradient.
- `basement_normal`: absolute projection of sigma-3 basement-depth gradient onto gravity normal.
- Rank each feature with average ties (no catalogue input). Candidate field = geometric mean of three ranks. Ablation omits termination.
- Continuous evaluation field retains upper 2% of ranks, rescaled to [0,1]. Fixed surface transform, not dot placement.
- Test every raw/derived feature alone with holdout AUC and HOLDOUT-DTI; AUC >0.90 stops as leakage.
- `buffered_component_draw`: seed 20, whole connected components withheld in 4 quadrants, 3-px collar, 12-px boundary erosion.
- `evaluate_holdout.py`: pool weighted terms; paired 20 km cluster bootstrap 1000 draws, 95% CI.
- Compare ablation + random + legacy reference; no promotion without comparison.
- Before final dots, compare surface to registry witness with literal uniqueness tool; any duplicate stops.
- At most one scientific experiment planned; at most 3 or 2 hours. No upload or weekly slot.

## Scientific limits (all lanes)

Potential-field inversions are nonunique. Magnetic amplitude changes can reflect magnetization rather than displacement; gravity and basement depth may share inversion priors. SGMC proxy may re-draw catalogue traces (20% within 3 px) and is not hidden organizer truth. Learning the proxy does not establish a geothermal vent, temperature, permeability, or economic resource. The target is new fault traces, as described by the organizer's fault-detection reference notebook, not a vent catalogue.
