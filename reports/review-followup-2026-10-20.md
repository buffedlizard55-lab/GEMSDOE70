# Follow-up repository review — 2026-10-20

## Executive result: DO NOT SUBMIT

**No eligible unique TIFF was generated. The requested downloadable competition submission remains unmet.** This review does not reset the stopped experiment, invent a lane, change the support definition, tune reported holdout folds, or select a weekly slot. A negative result is the only permissible outcome under the present protocol.

## Pass 1 — repository and release implementation

Read the complete README and PROJECT_BRIEF, session contract, handoff, irregularities, current run card, preregistration, H33 analysis, release implementation, tests and workflows. The repository already contains four ranked hypotheses and a measured stopped experiment. The concurrent H70-C artifact remains quarantined; its placeholder scientific claims are not accepted as evidence.

Fixed a software defect in `scripts/release_gate.py`: `--expect-negative` previously returned success solely for template integrity. It now also requires a negative verdict, explicit false download/submit/slot flags, no generated TIFF, and nonempty blocking reasons. Normal invocation still exits nonzero and never authorizes a submission.

## Pass 2 — malformed evidence and edge cases

Fixed release diagnostics for non-object evidence and nonfinite AUCs. A NaN AUC could previously evade the numeric comparison because comparisons with NaN are false. The current run was blocked regardless; this was a misleading-diagnostic risk, not an observed publication bypass. Canary validation now rejects nonfinite, boolean, missing, string, out-of-range and malformed values, suspected leakage, and either-direction AUC beyond the inherited threshold. Object-shape errors are returned as invalid evidence instead of crashing.

Added regression tests for those cases and each expected-negative CLI condition. No shared template code, experiment source, preregistration, metric, prediction, or scientific receipt was modified.

## Pass 3 — independent blocker recheck and requirements

- Installed the committed dependency lock into an ignored local virtual environment.
- Ran `python scripts/audit.py`: fetched the content-addressed registry witness and reverified its SHA-256, grid and universal support. Output reproduces the committed preflight evidence without changes.
- **REGISTRY-MEASUREMENT:** witness SHA-256: `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`. It has positive support on every allowed footprint pixel; minimum forward overlap for any nonempty allowed candidate is 1.0, exceeding the literal 0.70 stop threshold. This is a decisive failure witness, not a complete registry scan or geological-equivalence proof.
- Rebuilt site and README and reran software tests. Exact final commands/results are in the handoff; these software tests are not scientific scores.
- Verified the pinned organizer reference commit exists via GitHub API: [official reference](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b).
- Queried GitHub Pages configuration: enabled from `main`, repository root, with built status at review time. This does not prove a later deployment contains this PR.

## Scientific conclusion and source boundaries

The [existing H33 audit](../docs/h33-analysis.md) demonstrates that the archived H33 raster is a catalogue-distance pruning of its predecessor, not a wholly new prediction field. Pruning redundant prediction mass can improve the shared distance-weighted Tversky objective if lost truth coverage is sufficiently small. Hidden labels and authenticated submission receipts are unavailable, so this is a conditional metric explanation, not a causal explanation of the user-reported score or a promised improvement. The historical score is unverified, not ORGANIZER-CONFIRMED.

The existing experiment's **HOLDOUT-DTI** is 0.0101928890, CI95 [0.0060620859, 0.0150416449], evaluator `gems57-pooled-hide-v2`, with 11,321 withheld positive pixels, continuous pre-placement surface only. This review did not recompute or tune it. See [full frozen run card](../evidence/run_card.json). It does not establish improvement over the current best.

Official manual-review links: [competition and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem/format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/). These non-GitHub pages were not newly fetched in this review; no new scientific literature or current leaderboard verification is claimed.

## Next session — prerequisites, not automatic promotion

1. Resolve the dense-continuous-raster versus dot-support protocol conflict explicitly in the shared protocol. Do not privately reinterpret it or exclude the witness.
2. Recover the actual single-method lane; a new fixed geological idea needs fresh preregistration and untouched holdout blocks, not a rerun of the negative experiment.
3. Authenticate sample/data identities, official rules and a same-split incumbent implementation. The current holdout best is not independently verified here.
4. Only after all scientific gates pass, perform complete surface and final-dot inventory audits, shared-writer export, exact-byte validation, hash binding and separate weekly-slot selection. Publish a download only then.

No GPU, new external data, or submission slot was used for this software review. Static Pages is a report, not a model-training backend. Network access and organizer-account access remain limited. The explicit stop instruction prevents completing the urgent TIFF request safely; a decoy or quarantined file would not satisfy it.
