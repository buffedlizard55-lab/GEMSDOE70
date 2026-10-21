# Current protocol review — 2026-10-20

## Decision: download for review only. DO NOT SUBMIT.

**No new TIFF was generated in this session.** The mandatory duplicate-stop rule takes precedence over generating another candidate after a failed lane check. No experiment, training run, placement or competition upload was performed. No weekly slot was used by this session. This is a negative deliverable, not completion of the requested new unique submission.

[Download existing P4 TIFF for review](downloads/gems70-p4-stratified-halo-37654-20261020.tif) · [Machine-readable current run card](current_protocol_review.json) · [Submission instructions](submission.html)

The existing bytes were freshly re-read: one band, finite everywhere (hence inside the footprint), all values in [0,1], shape/CRS/transform equal to the **cached** reference metadata. SHA-256 equals both the frozen card and registry audit. This is local format validation, not organizer acceptance. No rescaling, copying, jittering or renaming a previous prediction was used to claim a new submission.

## Pass 1 — repository and evidence review

Read the retained README/PROJECT_BRIEF, AGENTS, handoff, irregularities and current evidence. The user instruction says **forward** overlap above 0.70 requires a stop. The inherited code instead uses **mutual** overlap. Those are different gates; an alleged tool fix cannot silently authorize a change to the user's rule. Frozen historical results remain intact but are not a clearance under the current instruction.

The frozen P4 final-dot audit contains multiple failing forward-overlap rows, including `calib_r13lattice_00904.tif` with candidate-to-registry overlap 1.00. Its reverse overlap is about 0.211. This explains the disagreement with the inherited mutual gate, but does not remove the stop. All raw measurements and registry hashes are in [the frozen audit](downloads/uniqueness.json); exact witnesses and validation checks are in [the current card](current_protocol_review.json). This is a reapplication of policy to historical measurements, **not a fresh registry scan**. It is sufficient for a negative, not for a positive uniqueness claim.

The supplied prompt references a "single method paragraph below" but does not identify one. No new lane is silently invented. These two blockers make the supervised within-halo next step in the old handoff unauthorized in this run.

## Pass 2 — scientific interpretation and candidate queue

H33's archived bytes support a sparse halo-sampling explanation, not demonstrated fault physics: [the existing byte audit](downloads/h33_audit.json) documents successive subsets of predecessor dots. Sparse emission can reduce redundant mass while maintaining distance-tolerant coverage. It does **not** prove why a hidden organizer evaluation rewarded it. The historical 0.2778 and the several inconsistent leaderboard values in the prompt are **user-reported, not ORGANIZER-CONFIRMED here**. The apparent headroom is not a forecast. There is no defensible promise that any new method will beat that value.

The following are **conditional, untested hypotheses**, ranked qualitatively by information novelty and cost, not predicted scores. They are queued before implementation, not assigned lanes. They need no new external source if the pinned 19-band owner-mirrored stack is restored and checked. Layer names below are cached metadata, not verification of inversion provenance or physical units. We do not claim these have never been tried by other repositories or private sessions.

| Priority / cost | Hypothesis and specific cached layers | Target transform and physical rationale | Why potentially missing from catalogue / non-fault mimic | Difference from the reviewed implementations |
|---|---|---|---|---|
| First / medium | Cross-field conductive basement boundary: `cond_surf`, `depth_to_base_surf`, `iso_grav_anom` | Multi-scale conductivity-gradient normal aligned with basement-depth-gradient normal; gravity-edge persistence as corroboration | Concealed basin-margin structures may juxtapose conductive fill and basement without a visible scarp. **Mimic:** saline basin-fill or clay boundary without displacement | Conditional conductivity/basement normal agreement, rather than P4 geometry, E2 topographic step, E3 depth step alone, or C1 magnetic continuation |
| Second / medium | Strain partition boundary: `geod_dilaterate`, `geod_shearrate`, `geod_2ndinv`, `depth_to_base_surf` | Neighborhood contrast of dilation relative to shear, restricted to persistent basement boundaries | Broad strain localization may prioritize blind structures not mapped at surface. **Mimic:** hydrologic subsidence or smoothed geodetic inversion artifacts | Joint strain-partition contrast, not catalogue endpoint relay geometry; resolution may be too coarse for the scoring radius |
| Third / medium | Magnetic–gravity edge offset: `rtp`, `iso_grav_anom`, `depth_to_base_surf` | Signed normal offsets between persistent magnetic and gravity edges, conditional on basement step, rather than multiplying amplitudes | A buried offset/contact could be unresolved in surface mapping. **Mimic:** intrusive contact or nonunique density/magnetization geometry | Uses edge **separation** across scale, unlike the reviewed coincident-gradient and along-strike termination transforms |
| Fourth / low-medium | Conductive corridor interruption: `cond_surf`, `det_elev`, `depth_to_base_surf` | Conductivity ridge endpoint/branch persistence, suppressed where aligned solely with detrended drainage curvature | A hydraulic barrier or breach could highlight a concealed cross-structure. **Mimic:** evaporite margin, channel or interpolation seam | Conductivity topology plus drainage negative control, not hydrographic proximity or magnetic tip extrapolation |

These are not vent detections: the competition target is fault mapping. None establishes temperature, permeability, fluid discharge or a geothermal resource. The first candidate must be rejected if the conductivity raster is too smooth, has unreliable provenance, or if individual features trigger the leakage canary.

### Authorized future validation order (not executed)

1. Establish an explicit lane and resolve the forward-vs-mutual policy without weakening the current instruction unilaterally. Refresh the accessible registry, including newly published concurrent runs. Preserve the old negative.
2. Restore and hash-check the template cache. Inspect band units, resolutions, nodata and resampling. Do not call owner mirrors organizer-authenticated inputs.
3. Use shared `evaluate_holdout.py`, whole-component withholding with buffers and visible-only catalogue features. Add an untouched outer spatial fold; reserve any hyperparameter selection for inner folds. Feature-alone AUC above 0.90 (also test inverse AUC) is suspected leakage, not a victory.
4. Evaluate feature-alone HOLDOUT-DTI as well as AUC. Compare candidate and current best on the **same** split, footprint, dot budget and emission policy. Report evaluator version, withheld count and paired spatial-bootstrap confidence intervals. Do not compare incompatible historical point estimates as if they were a new controlled experiment.
5. Check the surface before placement and final dots against every accessible registry raster. A single failure stops. Use shared writer only after passing; re-read output and check exact sample grid, finite footprint and [0,1]. No private evaluator or writer fork.
6. Stop at the experiment/time cap. Promotion is a separate selector step and requires a positive controlled result, registry clearance and verified weekly cap. No portal access or organizer receipt exists in this session.

## Pass 3 — source/access and release review

Freshly retrieved the [official reference README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md), commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`, through the GitHub API. It explicitly supports CPU-only training. The inherited statement "GPU needed" is therefore not a universal requirement; GPUs accelerate that reference approach. The README instructs downloading competition data but does not grant access to restricted labels.

Official links for manual review, **not freshly retrieved or asserted verified in this sandbox**:

- [Organizer problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/): organizer acceptance, current scoring rules and cap require direct verification. Network access here is restricted to GitHub and package registries.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and): original survey provenance; this run makes no new claim about download availability.
- [Competition report supplied by user](https://docs.nlr.gov/docs/fy26osti/96647.pdf): not fetched here; no PDF-specific rule is claimed verified.

No new third-party data is proposed as obtainable on speculation. The existing source-health workflow checks availability, not scientific validity or live scores. Automatic uploading is intentionally absent. Future work should reconcile stale prose (e.g. older "exactly one TIFF" claims despite multiple inventory entries) and carry a single authoritative protocol status into all release paths.

## Reproduce this negative audit

```bash
.venv/bin/python scripts/audit_current_protocol.py
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

The frozen scientific cards, TIFF bytes, shared evaluator and writer are untouched. The new policy report is additive and explicitly overrides inherited uniqueness claims for this request.
