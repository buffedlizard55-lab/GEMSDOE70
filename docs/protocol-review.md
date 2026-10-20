# Literal-protocol review — 2026-10-20

## Decision: DO NOT SUBMIT; archived downloads are for review only

**No new TIFF was generated. No new geological experiment was run. No competition slot was used.**
This is a negative deliverable, not completion of the request for a new protocol-compliant submission.
The supplied prompt has no identifiable single-method lane paragraph; the prior handoff's supervised
within-halo ranking is the deferred lane, not an invented or authorized assignment.

Canonical current pointers: `evidence/review/run_card.json` and
`evidence/review/literal_protocol_audit.json`; their public copies are under `docs/downloads/`.
`evidence/current_protocol_review.json` and `evidence/literal_protocol_review.json` are historical
compatibility receipts and do not supersede the canonical current card.

The current prompt explicitly requires a stop when **forward** dot overlap exceeds 70% within
3 pixels, or rank correlation exceeds 0.90. Earlier work changed forward overlap to mutual overlap
without user approval. That change does not satisfy the current prompt. A low reverse overlap or
rank correlation cannot cancel a high forward overlap.

### Fresh measurements, not inherited assertions

Reproduction: `python scripts/review_literal_protocol.py --fetch` (after installing requirements).
The script uses the existing shared `saturation_certificate`, `compare_to_registry`, and `validate`
functions; it does not replace the metric or writer. `src/gems70/protocol.py` applies the user's
literal thresholds to their reported measurements. Vendor bytes and frozen experiments are unchanged.

- Witness: [binary lattice, immutable owner-mirror revision](https://github.com/buffedlizard55-lab/60GEMSDOE/blob/32024716f218d06a94e01464157392119c03cb15/registry/rasters/calib_r13lattice_00904.tif).
- Witness SHA-256: `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`.
- **REGISTRY-MEASUREMENT:** 206,895 binary dots; halo covers 5,160,724 of 5,167,373 footprint cells
  (99.871327%). **6,649 cells remain uncovered.** The earlier claim of 100% coverage is false.
- For the handoff's fixed 37,654-dot design, even placing a dot in every uncovered cell gives
  forward overlap at least `1 − 6649/37654 = 0.82341849`, exceeding 0.70. This rejects every placement
  **at that mass**, before a new surface or final dots are built. It does not prove impossibility
  at every smaller mass. Deliberately predicting only edge slivers would be optimizing the registry
  loophole, not validating the geological hypothesis; no such experiment was attempted.
- **REGISTRY-MEASUREMENT:** all six inventoried final TIFFs (P4, discordance, E2, H2 diagnostic, scarp E3, and H70 conductive breach)
  have measured forward overlap **1.0** against this binary witness. P4 Spearman is
  **−0.0004249862**. Each is a duplicate **under the prompt's rule**, not necessarily a copied file.
- All six pass the shared **local grid/range preflight** (single-band float32, finite [0,1], CRS,
  shape and transform). This is not complete competition-format compliance: the official page says
  values outside the bounds must be null/NaN, while the shared writer currently emits all-finite
  rasters with `nodata=None` and finite zero-valued cells outside the mapped footprint. No upstream
  writer fix or organizer clarification was made here. Do **not** call these archives format-valid
  for upload; this issue is independent of the uniqueness stop.

Receipts: [full fresh audit](downloads/literal_protocol_audit.json),
[current negative run card](downloads/review_run_card.json),
[historical P4 holdout](downloads/instrumentA_holdout.json),
[partial current sibling scan](downloads/sibling_registry_refresh_20261020.json), and
[official/source-page review](downloads/web_sources_review_2026-10-20.json).
One positive witness suffices to reject. The seven-repository scan is not an exhaustive inventory of
all GEMSDOE sites, private submissions, or future/uncommitted rasters.

## Research queue: four candidates, ranked before any new implementation

These are **untested conjectures**, ranked qualitatively for expected useful information versus
implementation cost, not projected DTI scores. The feature cache was re-inspected in this continuation;
no experiment was run. Layer identities come from `evidence/inherited_band_metadata.json`, not
independent validation of survey units, inversion assumptions, or spatial resolution. The stack is an
owner-mirrored input, not a fresh organizer download. Novelty is relative to inspected local methods
(`method.py`, `method2.py`, `method_v2.py`, `strike.py`) and archived experiments, not every parallel
site or private run. The sibling-page review already shows multiscale multi-physics learning and
relief-conditioned methods elsewhere in the family, so no candidate is claimed globally novel.

| Priority | Candidate and exact cached layers | Proposed physical signature | Why an unmapped fault is plausible | Named non-fault mimic | Expected HOLDOUT-DTI direction (qualitative only) | Difference from local implementations; cost |
|---|---|---|---|---|---|---|
| First | Residual cross-sensor ranking: `rtp` (2), `det_elev` (12), `cond_surf` (17), `depth_to_base_surf` (15) | A fold-trained model learns departures from each sensor's local smooth background, conditional on visible-catalogue distance; paired elevation break and magnetic/conductivity gradient evidence | A covered fault may perturb basement and electrical structure while having a weak surface trace | Saline groundwater boundaries and lithologic contacts | Low-to-moderate possible gain if the joint residual is stable; highly uncertain, no score projected | Learned residual interactions rather than P4 geometry, C1 prescribed discordance product or E2 oriented step; medium cost. Not family-new given GEMSDOE68's AutoContext/multi-physics result |
| Second | Displaced texture patches: `rtp` (2), `mag_anom` (1), `iso_grav_anom` (13) | Opposite-side magnetic texture matches best after a nonzero along-strike offset, with a stable offset across scales and gravity support | Concealed displacement can offset a contact without an exposed scarp | Intrusive margins or independent volcanic flows | Low/uncertain; non-unique potential-field textures and high implementation cost | Patch phase-correlation displacement, not the prior along-tangent amplitude derivative or E3 depth step; high cost |
| Third | Relief-conditioned cross-modal disagreement: `det_elev` (12), `det_elev_slope` (19), `depth_to_base_surf` (15), `rtp` (2) | Supervised basement/magnetic boundary evidence is upweighted only where surface-relief response is unexpectedly weak within a training-fold relief stratum | Sedimentary burial may hide a fault scarp | Depositional onlap or an erosional paleovalley | Low-to-moderate but uncertain; explicitly test against acquisition/geologic confounds | Explicit conditional residual by relief, not E2's elevation-step product or weak geometric tilt; medium cost. Related relief stratification appears in GEMSDOE66 |
| Fourth | Dilation/shear contrast interactions: `geod_dilaterate` (8), `geod_shearrate` (7), `iso_grav_anom` (13), `rtp` (2) | Broad strain context conditions local gravity/magnetic evidence instead of being interpreted as a 100m fault locator | Distributed deformation can include structures absent from a mapped-trace catalogue | Aquifer compaction, broad regional strain or geodetic interpolation | Very low/uncertain at the 100 m scoring scale; unlikely to justify a run without a scale audit | Learned context interaction, not univariate geodetic weighting or catalogue-endpoint relay pairing; low–medium cost, lowest qualitative priority because effective resolution is uncertain |

### Validation plan, deferred — not a measured result

Once a separately authorized protocol resolves the literal-gate conflict, test only the first candidate.
Keep the shared evaluator and writer. Freeze the mass, folds, feature list and gates first. Hide whole
fault components with the shared buffer, regenerate catalogue-derived features from visible faults
only, and mask visible faults pixel-exactly. Compute each raw/derived feature-alone AUC **before**
interpreting any joint result; >0.90 is a leakage alarm, including inverse-predictive features as a
conservative diagnostic. All feature fitting, scaling and SGMC proxy labels must exclude the test
quadrant and its buffer. SGMC is proxy training truth, not an inference feature; its overlap with
QFaults must be quantified, not called independent truth.

Evaluate pooled HOLDOUT-DTI (shared evaluator `gems57-pooled-hide-v2`, alpha 0.2, beta 0.8,
300m triangular kernel), withheld-positive count, and paired spatial-bootstrap 95% intervals.
Re-evaluate D28 and the current best on exactly the same folds/mass; compare B′ separately as a proxy,
not as HOLDOUT-DTI or an organizer score. The cached E2 D28 HOLDOUT-DTI is an **archived**
reference in its original run card, not a newly rerun baseline. No promotion without a matched best-baseline comparison,
canaries, both-stage literal uniqueness, format validation and a separate selector decision.
Stop after at most three experiments or two hours. No automatic weekly submission.

## Source/evidence audit and limitations

| Claim | Evidence / official review link | Verification boundary |
|---|---|---|
| Target, incompleteness of mapped faults, metric and file format | [Official DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Retrieved 2026-10-20 via the Arena web reader. Confirms α=0.2, β=0.8, 300 m triangular support and float32/EPSG:32611/100 m/null-outside requirements. It is not an upload or validator receipt. |
| Public reference solution and CPU support | [Organizer reference README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md), [notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb) | README/notebook retrieved through GitHub. Training-loss weights are not independent confirmation of the full competition scorer. |
| Rules and weekly cap | [September 2026 rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Retrieved 2026-10-20; §3.2 states three submissions per week, and §3.4–3.5 requires selecting one. The authenticated account's current remaining quota was not read; no slot was used. A deadline discrepancy is recorded in `evidence/official_sources_2026-10-20.json`. |
| USGS GeoDAWN survey provenance | [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Page retrieved 2026-10-20; it describes 200 m and 400 m nominal line spacing across survey areas and CC0. No source binary was downloaded or matched to the model raster. Acquisition boundaries are a possible mimic, not a demonstrated fault confound in this stack. |
| INGENIOUS / GDR 1391 source provenance | [DOE Geothermal Data Repository, DOI 10.15121/1881483](https://gdr.openei.org/submissions/1391) | Page retrieved 2026-10-20; states public/CC-BY 4.0 and lists multiple geophysical/geologic resources. No archive was downloaded or used. |
| Geologic-map proxy context | [USGS GeMS/SGMC, DOI 10.5066/P1A3DQZK](https://www.usgs.gov/data/geologic-map-schema-gems-version-state-geologic-map-compilation-sgmc-geodatabase-conterminous) | Page retrieved 2026-10-20; 48 state maps at heterogeneous scales with unreconciled boundaries. This does not validate the owner-mirrored raster or make SGMC an independent hidden-fault truth. |
| Structural-process context | [Siler (2023), DOI 10.1144/geoenergy2023-009](https://doi.org/10.1144/geoenergy2023-009); [Mattéo et al. (2021), DOI 10.1029/2020JB021269](https://doi.org/10.1029/2020JB021269) | Retrieved metadata/abstract supports hypotheses about geothermal structural discontinuities and optical/topographic fault mapping, respectively—not direct evidence of local score improvement or a general fault-occurrence map. |
| Current public leaderboard | [Organizer leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | On 2026-10-20 it displayed 0.4413, 0.3811 and 0.3788 for the first three public rows. This is a PUBLIC-LEADERBOARD-OBSERVATION, not HOLDOUT-DTI for this project and not an ORGANIZER-CONFIRMED file receipt. |
| Peer methods and page-reported metrics | [GEMSDOE66–72 owner pages](https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html) | The per-repo findings and exact reporting gaps are in `evidence/web_sources_review_2026-10-20.json`. Owner pages are self-reports, not organizer receipts; run-card/artifact inconsistencies and missing evaluator metadata limit comparison. |
| Historical H33 value | User brief and [GEMSDOE32 owner archive](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | The 0.2778 value is a historical user/owner-reported leaderboard claim, not a HOLDOUT-DTI result; no authenticated submission-page receipt was found. It is not ORGANIZER-CONFIRMED and is not a forecast target. |

A fresh partial Git inventory at `evidence/sibling_registry_refresh_20261020.json` inspected seven
public repositories (GEMSDOE66–72): 302 tracked TIFF paths matched the single-band grid, with 175
unique SHA-256 hashes; 98 hashes occurred in the inherited 862-hash set and 77 did not. This is a
current owner-repository measurement, not an exhaustive family/private/organizer registry and not a
clearance for any new candidate. Hash consistency on owner mirrors is not organizer authentication.

The local sample contains known-fault positives, so it is a geometry/footprint template, not hidden
validation labels. `docs/hypotheses.md` and older preregistrations retain historical plans; the four
rows above are the current ranked queue. `prepare_data.py` is absent, so the retained prompt's
advertised command is not a working pipeline. No scientific-discovery, projected score or
leaderboard-improvement claim is established. Detailed extracted records and limitations are linked
in [the web-source evidence](downloads/web_sources_review_2026-10-20.json).

## Integration and upstream report

The active branch is `arena/2149863c-gemsdoe70`, fast-forwarded to PR #29's main commit
`4b870be`. That merged state preserves the earlier six-artifact literal audit and the single
policy adapter. The canonical current negative card is `evidence/review/run_card.json`; historical
cards, including `evidence/current_protocol_review.json` and `evidence/literal_protocol_review.json`,
remain available but are not current authorization. Review-pass details are maintained in
`evidence/review/verification-passes.md`.

A prior attempt to report a shared-template issue returned
`Resource not accessible by integration (createIssue)`. No issue was posted and no shared-template
code was changed. The finite-only writer/null-outside mismatch remains unresolved upstream; do not
maintain a private fork or claim that existing archives meet the complete official format.
