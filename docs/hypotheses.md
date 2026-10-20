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

## Session 3 (2026-10-20, branch arena/a0382202) — candidates, ranking, what was tested

Ranking is qualitative (expected live-DTI gain ÷ cost) and was revised after the instrument
calibration diagnostic (`evidence/s3/proxy_calibration.json`): offline B′ and A **do not** order
archived files the way the live board did (Spearman −0.28 and −0.64, n = 18 owner/user-reported
scores). Any new idea therefore needs an instrument that tracks the board before it can be promoted.

| Rank | Hypothesis / layers | Physical signature | Why it could catch faults missing from the USGS/INGENIOUS catalogue | Named mimic | Difference from repo | Cost | Data |
|---|---|---|---|---|---|---|---|
| tested E1 | S3 supervised proxy ranking: 19-band stack + 6 gradients + 33 LiDAR/topo/chi/radiometric bands + 7 catalogue-geometry, LOQO GBM on SGMC-only faults | learned combination; strongest single features are 10 m-DEM slope/relief (AUC 0.76) | geologic-map faults absent from the Quaternary catalogue | bedrock/map-density bias | first supervised model in this repo trained on an off-catalogue population | medium | in hand |
| tested E2 | Same model, ranking only **within** H33's distance × slope strata | within-stratum ranking | removes terrain/distance confound | lithologic contacts | marginal-matched placement (new) | low | in hand |
| 1 | Live-calibrated instrument: choose, among a small pre-declared family of proxy definitions (SGMC-only by distance band; catalogue holdout by fault age/slip-rate class from `qfault_attributes.csv`), the one whose ranking of the 18 scored archives best matches the live board, then re-test E2 on it | meta-measurement | without it no candidate can be promoted on evidence | over-fitting 18 points | nothing like it exists in the family | low | in hand |
| 2 | Basin-floor LiDAR micro-scarp continuity: `lidar_scarp_features_u8` step_max/downface_max with coh100 strike coherence, restricted to the lowest two slope quartiles | young intrabasin scarps in alluvium | Quaternary catalogues under-sample short, low-relief intrabasin scarps; the opposite terrain to E1's bias | shorelines, canal/road berms | E1 learned bedrock; this explicitly targets low-slope terrain | low | in hand (24.6 % LiDAR gaps) |
| 3 | Thermal-spring/well alignment: `gdr_wellspring_in_footprint.csv` (GDR 1391) points, Hough-style alignment lines through ≥ 3 springs within 20 km | fault-controlled fluid outflow | springs line up on permeable faults that may be unmapped | groundwater discharge at lithologic contacts | no repo method uses spring geometry | medium | in hand (owner mirror of GDR 1391; https://gdr.openei.org/submissions/1391) |
| 4 | Drainage knickpoint lines: `dem10_chi_100m_u8` knick_n aligned across ≥ 3 adjacent catchments | footwall uplift across drainages | blind/young faults deform drainage before scarps are mapped | lithologic knickpoints | by submission name, chi was used before as a corridor score (60GEMSDOE h73), not as cross-catchment alignment | medium | in hand |
| 5 | Radiometric alteration halo at basin margins: GeoDAWN K and Th/K (`geodawn_rad_u8`, `geodawn_extensions_u8`) local anomaly 0.5–3 km from range fronts | hydrothermal K depletion/enrichment along fluid pathways | alteration can mark permeable unmapped faults | primary lithology; flight-line artifacts | by submission name, radiometrics were used before in a scarp fusion (GEMSDOE46 r11f/r12), not as a margin-anomaly operator | medium | in hand (USGS DOI 10.5066/P93LGLVQ) |
