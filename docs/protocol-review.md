# Current protocol review — 2026-10-20, after PR #17 merge

## Decision: existing E3 download for review only — DO NOT SUBMIT

**Download E3 for review: yes. Submit E3: no. New TIFF generated in this review: no. Weekly slots used: 0.**
The E3 scarp-curvature TIFF was added by the already-merged parallel PR #17; this review did not
create it. Its lane-specific amended receipt says `promote` under a saturation-adjusted uniqueness
rule, but the current user instruction is stricter and is not satisfied. The literal forward-only
stop wins; do not use the adjusted result to authorize a submission.

The E3 artifact is easy to retrieve from
[`docs/downloads/gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif`](downloads/gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif)
(or the [one-TIFF ZIP](downloads/gems70e3-scarpcurv-60k-ex3-20261020-zeros.zip)) **for inspection only**.
Its SHA-256 is `562a6b48a4a396c9fbabc180b67afd817b21824011482541bc7c9c2f90197d21`.
The current site warning and JSON run card both say **DO NOT SUBMIT**.

## E3 holdout and strict uniqueness re-audit

The merged E3 hypothesis is **DEM scarp curvature alone**: strike-coherent curvature steps in the
100 m detrended-elevation band, with tensor coherence, and rank-ordered 2.8-pixel dotted emission.
Named non-fault mimics are lake-shoreline or fluvial-terrace risers and road cuts.

E3's archived catalogue holdout is **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`,
0.0943224, 95% CI [0.0782398, 0.1109296], 11,437 withheld positives (untouched seed-40 folds).
Its paired **HOLDOUT-DTI** difference from the matched random dotted control is +0.0336652,
95% CI [0.0176636, 0.0491208], with the same 11,437 withheld positives. These are catalogue-recovery
measurements, **not** leaderboard scores or proof of transfer to hidden organizer faults. The E3
receipt says its B′ off-catalogue proxy has not been scored. No score is ORGANIZER-CONFIRMED here.

I re-read the archived surface and final-dot rows using the user's literal rule:
**Spearman > 0.90 OR more than 70% of candidate support within 3 pixels of one registry raster**.
Both stages record five forward-overlap witnesses. The final-dot stage includes four binary-dot
rasters, so the stop is not solely an artifact of comparing to a continuous surface:

| Registry raster | E3 final-dot forward overlap | Outcome |
|---|---:|---|
| `calib_r13lattice_00904.tif` | 1.000000 | stop |
| `r11_greedy_mp.tif` | 0.946783 | stop |
| `r13_lattice_s5_00904.tif` | 1.000000 | stop |
| `r14_union_tips10_lat6.tif` | 0.760400 | stop |
| `17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif` | 1.000000 | stop under the literal receipt; continuous-surface support is also disclosed |

The source E3 pipeline classifies several fields as saturating and applies a Jaccard/saturation
adjustment. That explains why its adjusted gate differs; it does **not** change the requested
one-way threshold. Rank correlation does not exceed 0.90 in these rows, but the overlap arm alone
fires. The surface-stage strict audit also has five witnesses. These are REGISTRY-MEASUREMENTS,
not scores or proof that two geological predictions are identical.

The vendored uniqueness comparator remains different from its pinned template
(`registry/template_pin.json` records `all_identical: false`). This review reinterprets frozen
rows under the user's explicit threshold; it does not treat the patched comparator as authoritative,
and it does not maintain a private replacement. Reconcile any shared-tool change once in the common
template and report it there; do not use that process to weaken the current prompt stop.

The E3 receipts checked 63 locally available rasters and explicitly state that the inherited
862-entry inventory is incomplete. The full registry scope is not certified. For E3, the surface receipt's decoded
float32 hash matches its run card; the final-dot receipt's decoded hash matches a fresh decode of the
published TIFF. The published TIFF's SHA also matches the run card and the fresh local validator.
The separate literal audit is in `evidence/literal_protocol_review.json`.

The older Phase-4 (P4) TIFF is also format-valid for inspection, but its archived full scan has
four forward-overlap witnesses among 62 rasters, including overlap 1.0. Its pre-placement surface
audit is missing. It is **not** a fallback unique submission. The parallel E2 alluvial-step lane is
also not a fallback: its negative catalogue result is HOLDOUT-DTI 0.0646483, 95% CI
[0.0486899, 0.0818097], 11,321 withheld positives, evaluator `gems57-pooled-hide-v2`; it lost to
D28 and its earlier uniqueness evidence covered only a disclosed subset. The P4 and E3 downloads
discussed here are for review only; no artifact in this repo is cleared for a weekly slot under the
current prompt.

## Fresh E3 format check

Fresh local validation of the published E3 bytes passed: one float32 band; EPSG:32611; shape
3730×3292; transform `[100, 0, 243350, 0, -100, 4508550]`; all 12,279,160 cells finite;
zero NaN and infinity; values in [0,1]; 60,000 positive dots; zero positive cells outside the
footprint or on mapped catalogue faults. This is a file-format/range check only, not uniqueness,
scientific validity, B′ performance, organizer acceptance, or slot authorization. Receipt:
`evidence/review-e3-format-validation.json`.

## H33 explanation and evidence boundary

The archived byte audit and metric algebra support a plausible explanation for H33's reported
0.2778: sparse, off-catalogue emission can retain pooled kernel credit while reducing redundant
mass, especially near masked known faults. That is not verified causation. Hidden labels, controlled
organizer ablations, a submission-page receipt, and a fresh live leaderboard read are unavailable.
The 0.2778 value remains **unconfirmed**; user-reported or owner-reported values are not treated as
ORGANIZER-CONFIRMED. Fault prediction also does not demonstrate a geothermal vent, permeability,
fluid temperature, or commercial resource.

## Ranked hypotheses not yet tried in the inspected local methods

Qualitative expected-improvement rank only—not projected DTI. These are not an assigned lane and
must not be run while the literal stop remains unresolved. They differ from the completed E1/E2/E3
methods identified below; novelty across private or uninspected repositories is not claimed.
All use bands in the existing 19-band stack, so no additional external dataset is required. The
full stack is **not** present in this checkout (`.cache/data` is absent); `scripts/restore_data.py`
can reconstruct hash-pinned owner-mirror inputs, but mirror integrity is not organizer
authentication. No restore or experiment was run for this review.

| Rank / expected DTI improvement | Layers | Physical signature | Why a catalogue omission is plausible | Named non-fault mimic | Difference from inspected repo methods | Cost |
|---|---|---|---|---|---|---|
| **1 — highest conditional gain / low compute, high scientific uncertainty** | `geod_dilaterate` (band 8), `geod_2ndinv` (4), `depth_to_base_surf` (15), `iso_grav_anom` (13) | Along-gravity-tangent termination of a basement-depth ramp, weighted by positive dilatation and strain invariant; no DEM scarp required | Basin fill can hide a blind normal fault that offsets a basement ramp and localizes extensional deformation | Sedimentary onlap or paleovalley; transient volcanic inflation | E1 tested magnetic-edge termination; P2 used a scalar geophysical gate with catalogue continuation; E2/E3 tested DEM scarp fields. The strain-gradient/ramp-termination operator itself was not found in those implementations | Low CPU; existing stack. Coarse/smooth strain may erase 300 m-scale localization |
| **2 — high conditional gain / low compute, medium-high confounding** | `cond_surf` (17), `rtp` (2), `iso_grav_anom` (13) | Conductivity gradient crossing, rather than paralleling, a gravity-supported truncated magnetic contact | Buried hydrothermal alteration or a fluid pathway can mark an unmapped fault without a surface trace | Saline basin brine or clay-rich paleolake margin | Existing H32-family conductivity/magnetic products used co-located ridge agreement; this directional cross-contact breach operator was not found in the reviewed E1/E2/E3 code | Low CPU; existing stack. Conductivity resolution and brine confounding are substantial |
| **3 — medium conditional gain / low compute, high confounding** | `tc` (6), `tmi_hg` (3), `tmi_vg` (9), with `rtp` (2) as context | Persistent tilt-derivative zero-contours; a reproducible lateral phase jump or termination at a gravity/contact boundary | A buried displacement may interrupt a weak magnetic contact without a topographic scarp | Gradational lithologic contact or remanence boundary | E1 used unsigned magnetic/tilt amplitude and along-strike termination; H2-like methods used unsigned analytic-signal/ridge strength. Zero-contour persistence/phase continuity is a different transform, not a proven improvement | Low CPU; existing stack. Weak-contact and derivative-noise risk |
| **4 — lower conditional gain / low compute, medium confounding** | `iso_grav_anom_slope` (5), `iso_grav_anom_hg` (18), `det_elev` (12), `det_elev_slope` (19) | Gravity-slope edge with low detrended-elevation slope (a gravity/topography non-correlation guardrail) | A basement fault under alluvium may produce a gravity step without a preserved surface scarp | Erosional pediment or buried paleochannel | E1 used gravity as support for a magnetic edge; E3 used DEM curvature alone. A cross-channel gravity-versus-topography guardrail was not found in those methods | Low CPU; existing stack. Gravity/basement inversion priors are non-independent |

The top-ranked new hypothesis has **not** been evaluated on the spatially blocked holdout. The E3
HOLDOUT-DTI result belongs to a different DEM-scarp hypothesis and cannot validate it. Before any
future run: obtain an explicit single-lane assignment, resolve the one-way uniqueness protocol,
run feature-alone leakage canaries (AUC >0.90 means stop), use whole-segment buffered hide-and-recover
with visible-only catalogue features and exact visible-fault masking, compare against the current
best on identical folds, and require both surface and final-dot uniqueness plus the shared writer
and validator. No weekly slot before those gates.

## Official sources, data availability, and next work

- [Organizer competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
  [format/data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
  and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/):
  linked for manual review; not live-fetched in this sandbox.
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
  DOI `10.5066/P93LGLVQ`: recorded in the repo source manifest; not needed by the four proposals
  above and not re-verified by a live request in this review.
- [DOE GDR INGENIOUS record](https://gdr.openei.org/submissions/1391): a reference to mapped fault
  and spring information, not used as a prediction feature here.
- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution):
  official code mirror, distinct from the organizer's hidden labels and score receipt.

The immediate next action is protocol/selector resolution, not another experiment: the prompt's
forward stop conflicts with the repository's saturation-adjusted interpretation and both existing
candidates have literal witnesses. The 2026-10-20 parallel E3 lane reports 3/3 experiments used;
this review ran zero experiments and used zero slots. Reconcile any protocol change explicitly,
obtain the complete registry and official slot-cap/receipt through authorized channels, then assign
one lane. Do not upload either current TIFF.
