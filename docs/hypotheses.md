# Preregistered hypotheses — 2026-10-20

Written before the experiment. These are geological hypotheses, **not established discoveries or predicted scores**. This checkout originally had no implementation. Novelty is relative to that checkout and inspected GEMSDOE32/60/69 code, not an exhaustive claim across private parallel sessions.

## Lane irregularity

The prompt refers to a single method paragraph, but supplies none identifiable as a lane assignment. Provisional narrow lane: **magnetic-edge termination at a gravity-supported basement boundary**. Only the first hypothesis will be tested. The others are research queue items, not extra experiments. Do not silently borrow H33's predictions or reinterpret the literal overlap rule.

| Expected improvement rank (qualitative only) | Hypothesis / layers | Physical signature / mechanism | Why a catalogue omission is plausible | Named non-fault mimic | Difference from inspected implementations | Implementation cost |
|---|---|---|---|---|---|---|
| First | Magnetic contact truncation: cached `rtp`, `iso_grav_anom`, `depth_to_base_surf` | Magnetic gradient changes rapidly **along** a gravity-boundary tangent, while basement gradient has a large normal projection; possible cross-cutting displacement | A buried discontinuity can interrupt a magnetized contact without a visible topographic scarp | Volcanic dike termination or intrusive lithologic contact | H33 uses co-oriented Hessian consensus; H69 uses catalogue-derived relay connectors. This explicitly targets along-boundary edge-amplitude change, not a reused dot field | Low; existing stack, CPU derivatives |
| Second | Magnetic edge phase jump: cached `rtp`, `mag_anom`, gravity anomaly | Compare signed magnetic normal profiles on either side of an along-strike discontinuity, conditioned on a gravity boundary | Cover can obscure a displaced magnetic contact | Remanence change inside a volcanic flow | Signed profile discontinuity rather than Euler depth cluster / unsigned edge magnitude | Medium; existing stack, directional sampling |
| Third | Basement-ramp endpoint: cached basement depth, gravity anomaly, detrended elevation | Along-strike termination of a basement depth ramp where gravity supports the ramp but topography does not | A blind basin fault may displace basement without a scarp | Depositional onlap or erosional paleovalley | Endpoint operator rather than plain basement gradient / scalar cover gating | Medium; existing stack |
| Fourth | Conductive breach at a magnetic termination: cached conductivity, `rtp`, gravity anomaly | Local conductivity gradient crossing a truncated magnetic edge; possible fluid pathway | Alteration along a buried fault may be detectable without surface rupture | Saline groundwater boundary | Cross-cutting breach rather than H32 conductivity-ridge product or H69 radiometric halo | Medium; existing stack, uncertain conductivity resolution |

## Research queue — candidate hypotheses not yet tried

Qualitative ranking only; none is a verified score improvement. Each names layers, the physical signature, why it could catch faults absent from the USGS/INGENIOUS catalogue, a named non-fault mimic, how it differs from implementations already in this repo, expected DTI improvement rank, and implementation cost. External-data entries name the specific free official source and note whether it is obtainable in this sandbox.

| Rank | Hypothesis / layers | Physical signature | Catalogue-omission argument | Named non-fault mimic | Difference from repo implementations | Expected DTI | Cost | External data |
|------|---------------------|--------------------|-----------------------------|-----------------------|--------------------------------------|--------------|------|---------------|
| 1 (tested) | H-1 Stepover-relay dilation propensity: visible catalogue endpoints paired within 1.2 km x RTP edge | Off-catalogue corridor density at endpoint pairs x magnetic gradient magnitude | New cross-faults nucleate in dilational jogs between mapped traces, not on the traces themselves | Volcanic contact endpoints, leveling artifacts | Network/topology endpoint pairing vs the tested lane's along-tangent edge-amplitude truncation | 0.0230 vs random control 0.0472 (negative) | Low | None (cached stack) |
| 2 | H-2 Magnetic analytic-signal ridge amplitude: rtp, tmi_hg, tmi_vg | Analytic-signal amplitude ridge = total gradient magnitude including vertical derivative; buried source edges independent of magnetization direction | Concealed magnetic-contact faults produce no surface rupture or topographic scarp | Remanence/magnetization contrast without slip; dike margins | Repo uses unsigned RTP horizontal gradient only; adds vertical derivative and analytic-signal envelope | Moderate | Medium | None (bands 2, 3, 9 in stack) |
| 3 | H-3 Radiometric alteration-edge halo: GeoDAWN K, Th, total-count (USGS) | Gradient edges of potassium/thorium depletion or uranium enrichment along hydrothermal alteration halos | Hydrothermal alteration can be detectable where the fault trace itself is unmapped or buried | Primary lithologic K/Th variation unrelated to faulting; flight-line artifacts | Repo uses no radiometric data at all | Uncertain (untested) | Medium-high | ext_geodawn_rad_u8 via fetch_data.py WANT set from public owner mirror; obtainability not yet checked in this session |
| 4 | H-4 Detrended elevation breakline density: det_elev, det_elev_slope | Subtle breakline/curvature concentration of blind fault scarps in detrended topography | Blind scarps displace topography without a mapped trace | Depositional/erosional geomorphology (fans, paleochannels); road cuts | Repo's potential-field lane does not use topography | Low-moderate | Low | None (band 11 in stack) |
| 5 | H-5 Earthquake-density corridor: ieq_n100a15, deq_n100a15 | Microseismicity density ridges outlining concealed seismogenic structures | Seismicity can delineate structures with no surface expression in the catalogue | Station-density or template-matching artifacts in the catalog | Repo uses no seismicity data | Low | Low | None (bands 9, 16 in stack) |

Top candidate by expected improvement vs cost: H-1 (tested this session; see evidence/run_card.json). H-2 is the next cheapest to validate on the same holdout split using only cached bands. H-3 requires the radiometric mirror before it can be proposed as viable; its download was not attempted this session because the GitHub secondary rate limit blocked the single witness fetch already in flight.

## Fixed first experiment

No external-data-dependent idea is asserted viable. All named layers are already obtainable in the restored, SHA-pinned owner mirror. Their descriptions are metadata, not independent proof of the precise inversion or units.

- Smooth RTP with Gaussian sigma one pixel; compute magnetic gradient magnitude, then smooth its amplitude with sigma two pixels.
- Smooth gravity anomaly with sigma three pixels; compute its unit normal and tangent.
- Feature `termination`: absolute directional derivative of magnetic edge amplitude along that tangent.
- Feature `gravity_edge`: magnitude of the smoothed gravity gradient.
- Feature `basement_normal`: absolute projection of the sigma-three basement-depth gradient onto the gravity normal.
- Rank each feature with average ties over the finite feature domain (no catalogue input). Candidate field is the geometric mean of these three ranks. Ablation omits termination.
- Continuous evaluation field retains the upper two percent of ranks, linearly rescaled to [0,1]. This is a fixed surface transform, **not final dot placement**, not a calibrated probability.
- Test every raw input and derived feature alone with holdout AUC and HOLDOUT-DTI before interpreting the joint field. AUC > 0.90 stops the run as suspected leakage.
- Shared `buffered_component_draw`: seed twenty, whole connected catalogue components withheld in four spatial quadrants, three-pixel catalogue feature collar and twelve-pixel boundary erosion. No catalogue-derived predictor is used.
- Shared `evaluate_holdout.py`: pool weighted terms; paired physical twenty-kilometre cluster bootstrap, one thousand draws, ninety-five percent interval. Catalogue recovery is not validation on hidden organizer labels.
- Compare ablation and a fixed random sparse control; a compatible current-holdout-best implementation is not available in this checkout. No promotion without that comparison.
- **Before any final dots or submission writing**, compare the candidate surface to a SHA-verified registry witness with the literal shared uniqueness tool. Any positive duplicate witness is sufficient to stop; it is not sufficient to certify uniqueness. Never scan past a stop to search for a loophole.
- At most one scientific experiment planned; never more than three or two hours. No competition upload or weekly slot.

## Scientific limits

Potential-field inversions are nonunique. Magnetic amplitude changes can reflect magnetization rather than displacement; gravity and basement depth may share inversion priors and are not necessarily independent evidence. This test can falsify a useful ranking but cannot establish a geothermal vent, temperature, permeability, or economic resource. The actual target is new fault traces, as described by the organizer's fault-detection reference notebook, not a vent catalogue.

## Phase-5 addendum — preregistered 2026-10-20 (before the run)

Session priority from `HANDOFF.md`: supervised within-halo ranking. This is experiment 5 overall
(in-session 1 of 3; budget 3 experiments / 2 hours). Written before any model was trained.

### H-P5-1 supervised within-halo ranking on the SGMC off-catalogue proxy

* **Hypothesis.** SGMC off-catalogue fault pixels (the B′ population: SGMC ∧ ¬catalogue ∧ footprint
  ∧ d_catalogue ≥ 3 px) are separable from the halo background by a gradient-boosted model over the
  cached 19-band physics stack plus visible-catalogue geometry, and that ranking transfers both to
  catalogue-withheld segments (instrument A) and to spatially held-out quadrants (instrument B′
  leave-one-quadrant-out). This is the "within-halo information" that `docs/h33-analysis.md`
  identifies as the only route past emission geometry.
* **Layers.** All 19 bands of `training_features.tif` (mag_anom, rtp, tmi_hg, geod_2ndinv,
  iso_grav_anom_slope, tc, geod_shearrate, geod_dilaterate, tmi_vg, deq_n100a15, iso_grav_anom_vg,
  det_elev, iso_grav_anom, tmi, depth_to_base_surf, ieq_n100a15, cond_surf, iso_grav_anom_hg,
  det_elev_slope) plus three catalogue-geometry features (d = distance to visible catalogue, u, v =
  along/across-strike tip kernels, all from `method_v2.tip_kernels`). 22 features, no others.
* **Mechanism.** `sklearn.ensemble.HistGradientBoostingClassifier` (random_state 70520,
  max_iter 300, learning_rate 0.06, max_leaf_nodes 31, min_samples_leaf 40, l2 1.0,
  early_stopping True, validation_fraction 0.1). Training rows: all in-band proxy positives
  (measured 38,757) + 150,000 uniform in-band negatives (seed 70521). Allowed domain = the P4 band:
  valid ∧ ¬catalogue ∧ 2.4 ≤ d ≤ 32 px (measured 2,768,584 cells; 63.7 % of B′ truth lies inside it
  — the band caps reachable truth and widening it is deliberately NOT part of this experiment).
  Leave-one-quadrant-out over the shared `holdout.quadrant_ids` split: four models for evaluation,
  one production model trained on all quadrants.
* **Emission.** The measured P4 design, unchanged: one dot per 7×7-px stratum at the stratum
  maximum of the model score, keep the best 37,654 strata, 5-px Euclidean NMS. Fixed mass 37,654
  binary dots, zero on the catalogue, zero outside the footprint.
* **Non-fault mimic (named).** SGMC cartographic generalization: mapper habit and digitization
  conventions (line-work following map-unit contacts, section lines, or scanner artifacts) can be
  learned as if geology. Such structure transfers to the proxy labels but not to organizer truth.
* **Instruments and arms.** A: shared `buffered_component_draw` (seed 20, buffer 3 px, boundary
  12 px), candidate scored with the production model but fold-visible geometry. B′/B: quadrant
  regions eroded 12 px, candidate dots in quadrant k from LOQO model k (full-catalogue geometry,
  matching its training). Arms: candidate, random control (37,654 uniform on valid ∧ ¬visible),
  h33_reference, and p4_reference (the published Phase-4 TIFF, hash-pinned) so the run is compared
  against the current holdout best family, not only H33.
* **Canaries (rule 4).** (i) every feature alone vs instrument-A withheld truth — STOP if any AUC
  > 0.90; (ii) every feature alone vs the proxy labels — reported, because it measures what the
  model can memorize (d is expected to be high: proxy traces hug the catalogue; that is label
  structure, not feature leakage, and is disclosed rather than hidden); (iii) LOQO out-of-fold
  model AUC vs the proxy — STOP if > 0.90.
* **Uniqueness (rule 1).** Surface Spearman vs the 62 archived registry rasters BEFORE placement
  (stop if ρ > 0.90); final dot audit after writing (mutual 3-px overlap > 0.70 or ρ > 0.90 →
  duplicate → negative, no promotion).
* **Gates (verdict `promote` iff ALL hold).** gate A: candidate A-DTI ≥ H33 A-DTI; gate B′: paired
  Δ vs H33 > 0 with 95 % CI lower bound > 0; uniqueness cleared; shared validator all checks pass.
  Any failure → `negative`. Weekly slots remain 0; promotion to a real slot is a separate selector
  step.
* **Registered honesty constraints.** B′/B share the label source with training (LOQO spatial
  split only) — they are PROXY-DTI (LOQO), partially in-sample; instrument A is the only
  label-independent gate, which is why both gates are required. Instrument A itself has a
  contamination channel: SGMC re-draws of withheld catalogue segments that sit ≥ 3 px from the
  catalogue can appear in the training labels and within kernel range of A truth; the run measures
  and discloses the fraction of A-truth pixels within 3 px of proxy pixels. Phase-4 measured the
  supervised-free baseline at A 0.0730 / B′ 0.0812; H33 at A 0.0037 / B′ 0.0938.

### Phase-5 implementation amendment (2026-10-20, before any score was seen)

The registered emission ("one dot per 7×7-px stratum at the stratum maximum, best 37,654 strata,
5-px NMS, fixed mass 37,654") is under-determined for a spiky surface: on the first execution the
model surface allowed only 34,587 block-argmax dots under NMS (the Phase-4 smooth halo never hit
this). The run stopped at the mass invariant before any evaluation. Amendment, fixed before any
DTI was computed: pass 1 stays **byte-identical** to the Phase-4 operator (blocks in score order,
dot at the stratum maximum when NMS-feasible); only if pass 1 places fewer than 37,654 dots does
a second pass place one dot at the best NMS-feasible **positive-score** cell of the
highest-scoring strata that remain empty (positive cells are exactly the allowed-domain cells, so
every dot stays off-catalogue and inside the footprint). One dot per stratum and the fixed mass
are preserved; no threshold, mass or domain changed. Disclosed in the run card as `emission_topup`.
