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
