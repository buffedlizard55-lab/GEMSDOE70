# Literal-protocol review — 2026-10-20

## Decision: DO NOT SUBMIT; archived downloads are for review only

**No new TIFF was generated. No new geological experiment was run. No competition slot was used.**
This is a negative deliverable, not completion of the request for a new protocol-compliant submission.
The supplied prompt has no identifiable single-method lane paragraph; the prior handoff's supervised
within-halo ranking is the deferred lane, not an invented assignment.

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
- **REGISTRY-MEASUREMENT:** all four inventoried final TIFFs (P4, discordance, E2, H2 diagnostic)
  have measured forward overlap **1.0** against this binary witness. P4 Spearman is
  **−0.0004249862**. Each is a duplicate **under the prompt's rule**, not necessarily a copied file.
- All four pass the shared local format validator, including finite [0,1], CRS, shape and transform.
  Format validity does not imply uniqueness, portal acceptance or scientific usefulness.

Receipts: [full fresh audit](downloads/literal_protocol_audit.json),
[current negative run card](downloads/review_run_card.json),
[historical P4 holdout](downloads/instrumentA_holdout.json).
One positive witness suffices to reject. This is not an exhaustive scan of all GEMSDOE sites.

## Research queue: four candidates, ranked before any new implementation

These are **untested conjectures**, ranked qualitatively for expected useful information versus
implementation cost, not projected DTI scores. Novelty is relative to the inspected local methods
(`method.py`, `method2.py`, `method_v2.py`, `strike.py`) and archived experiments, not every other
team's private work. They stay within supervised residual within-halo ranking from the handoff.
No added external source is required; layer identities below come from
`evidence/inherited_band_metadata.json`, not independent validation of survey units or inversions.
The large feature stack has not been restored during this stopped review.

| Priority | Candidate and exact cached layers | Proposed physical signature | Why an unmapped fault is plausible | Named non-fault mimic | Difference from local implementations; cost |
|---|---|---|---|---|---|
| First | Residual cross-sensor ranking: `rtp` (2), `det_elev` (12), `cond_surf` (17), `depth_to_base_surf` (15) | A fold-trained model learns departures from each sensor's local smooth background, conditional on visible-catalogue distance; paired elevation break and magnetic/conductivity gradient evidence | A covered fault may perturb basement and electrical structure while having a weak surface trace | Saline groundwater boundaries and lithologic contacts | Learned residual interactions rather than P4 geometry, C1 prescribed discordance product or E2 oriented step; medium cost, highest qualitative priority |
| Second | Displaced texture patches: `rtp` (2), `mag_anom` (1), `iso_grav_anom` (13) | Opposite-side magnetic texture matches best after a nonzero along-strike offset, with a stable offset across scales and gravity support | Concealed displacement can offset a contact without an exposed scarp | Intrusive margins or independent volcanic flows | Patch phase-correlation displacement, not the prior along-tangent amplitude derivative or E3 depth step; high cost, potentially useful but nonunique |
| Third | Relief-conditioned cross-modal disagreement: `det_elev` (12), `det_elev_slope` (19), `depth_to_base_surf` (15), `rtp` (2) | Supervised basement/magnetic boundary evidence is upweighted only where surface-relief response is unexpectedly weak within a training-fold relief stratum | Sedimentary burial may hide a fault scarp | Depositional onlap or an erosional paleovalley | Explicit conditional residual by relief, not E2's elevation-step product or weak geometric tilt; medium cost, uncertain gain |
| Fourth | Dilation/shear contrast interactions: `geod_dilaterate` (8), `geod_shearrate` (7), `iso_grav_anom` (13), `rtp` (2) | Broad strain context conditions local gravity/magnetic evidence instead of being interpreted as a 100m fault locator | Distributed deformation can include structures absent from a mapped-trace catalogue | Aquifer compaction, broad regional strain or geodetic interpolation | Learned context interaction, not univariate geodetic weighting or catalogue-endpoint relay pairing; low–medium cost, lowest qualitative priority because effective resolution is uncertain |

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
not as HOLDOUT-DTI or an organizer score. The cached E2 D28 HOLDOUT-DTI 0.0919 is an **archived**
reference, not a newly rerun baseline. No promotion without a matched best-baseline comparison,
canaries, both-stage literal uniqueness, format validation and a separate selector decision.
Stop after at most three experiments or two hours. No automatic weekly submission.

## Source/evidence audit and limitations

| Claim | Evidence / official review link | Verification boundary |
|---|---|---|
| The task predicts faults, not a catalogue of geothermal vents | [Official organizer notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb), opening cell | Re-fetched via GitHub API this review; excerpts in `evidence/review/official-reference-excerpts.txt` |
| CPU training is possible, GPU preferred | [Official README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) | Re-fetched; the retained prompt's GPU-required statement is too strong |
| Training-loss weights are 0.2/0.8 | Same notebook, cell 16 | Verified training loss; this notebook excerpt alone does not establish the distance-transform competition scorer |
| Competition format, scoring and current slot cap | [Problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), submission-page cap | Historical fetched quotations in `evidence/official_sources_2026-10-20.json`; these hosts are not in this session's outbound allowlist. No fresh cap or authenticated receipt verified |
| GeoDAWN / INGENIOUS source provenance | [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOE GDR 1391](https://gdr.openei.org/submissions/1391) | Official manual-review links; availability and licensing not re-verified this review. No new external-data-dependent candidate asserted viable |
| Reported H33 performance and leader values | User's brief and historical page captures | No submission-page receipt. Not ORGANIZER-CONFIRMED; conflicting values are not averaged or treated as forecasts |

Hash consistency on an owner mirror is not organizer authentication. The local sample contains known
fault positives, so it is a geometry/footprint template, not hidden validation labels. Earlier snippets
in `docs/hypotheses.md` also mis-indexed detrended elevation (correctly band 12) and seismicity distance
(correctly band 10); the table here uses the recorded metadata and avoids inferring ambiguous units.
`prepare_data.py` is absent, so the retained prompt's advertised command is not a working pipeline.
Data placement is not the single blocker: protocol consistency, proxy validity and independent model
validation remain. No scientific-discovery or leaderboard-improvement claim is established.
