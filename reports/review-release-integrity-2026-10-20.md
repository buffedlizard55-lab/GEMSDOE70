# Release-integrity review — 2026-10-20

## Decision: STOP — no TIFF is currently cleared to download or submit

This review is a negative result. No competition slot was used. No organizer-confirmed candidate score is available in the checked evidence. The repository contains historical artifact records, but they are not authorization to submit.

### Findings, checked against the checkout

1. `evidence/run_card_v2.json` records a HOLDOUT-DTI of **0.0**, evaluator metadata and 11,321 withheld positive pixels, but its registry measurements are empty/null and its final disposition says `promote` / `download_and_submit_ok: true`. Those fields conflict internally and fail the required uniqueness evidence. They are not accepted as clearance.
2. `evidence/surface_uniqueness.json` explicitly records `complete_accessible_scan: false`, `unique: false`, one checked raster and a forward dot overlap of 1.0. It is an early-stop witness, not a complete registry inventory; under the session's literal rule, it requires stop, not reinterpretation.
3. The generated candidate files in `docs/downloads/` had been linked from the public-facing pages despite the above unresolved gate. Their presence and local format checks do not establish scientific validity, uniqueness, or organizer acceptance.
4. The public pages and README also disagreed about the active artifact and decision. For example, README pointed to the P4 TIFF while `docs/submission.html` named a different P4 file; `evidence/run_card_v2.json` named a third candidate. This release-integrity defect makes prior download instructions unsafe.
5. Historical scores in the supplied prompt, and scores in local receipts without an organizer submission-page receipt, are not treated as ORGANIZER-CONFIRMED. The user-reported 0.2778 H33 result is a reported value; its mechanism can be discussed as a hypothesis, not certified causation.
6. This checkout does not contain the requested shared `evaluate_holdout.py` / `submission_writer.py` by those names. It has vendor and local tooling, but this review did not claim that the exact named upstream tools were used.

### Action taken

All seven previously exposed TIFF/ZIP artifacts have been moved out of the GitHub Pages publication tree into `quarantine/published-downloads-2026-10-20/`. They are preserved for audit, not for download or submission. Public overview and submission instructions now state STOP and link to the review. No scientific experiment was run or promoted; no registry thresholds were relaxed.

### Required next steps

- Resolve the documented protocol conflict between a continuous raster surface scan and binary-dot overlap in a shared, reviewed tool; do not privately change the literal 70% threshold.
- Reconstruct one method lane from the retained supplied prompt; preregister the exact feature, immutable split, evaluator, one candidate and stopping rules.
- Verify official competition data and sample identities. The organizer data page requires authentication per prior recorded observation; owner mirrors are not organizer-authenticated data.
- Evaluate every feature as a leakage canary, then run frozen spatial hide-and-recover holdout with 95% CI. Compare against a same-split incumbent.
- Require a complete, hash-bound registry scan at surface and final-dot stages, with measured rank correlation and overlap for every checked raster.
- Only after every gate passes, generate via the shared writer and validate exact bytes, CRS, dimensions, affine transform, footprint finiteness and [0,1] bounds. Keep promotion to the separate selector step.

## Reproducible review checks and limitations

`git status` was clean before review. The committed `pytest` suite could not run with the system interpreter because `pytest` is not installed (`/usr/bin/python: No module named pytest`). No dependency install was attempted during this review. No current official leaderboard or competition site was newly fetched. This report is based on repository evidence and files, not new scientific source retrieval.

Official manual-review URLs retained by the project: [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOE INGENIOUS repository](https://gdr.openei.org/submissions/1391), [organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).

## Run card

```json
{
  "hypothesis": "No new geological candidate is eligible for promotion in this review; previously exposed artifacts fail release-evidence consistency gates.",
  "mechanism": "Not tested. Review-only action: quarantine publication artifacts until a single preregistered candidate passes the required independent holdout and uniqueness gates.",
  "named_non_fault_mimic": "Not applicable; no candidate surface was evaluated.",
  "holdout_dti": {"evidence_class":"HOLDOUT-DTI","value":null,"ci95":null,"evaluator_version":null,"withheld_positive_pixels":null,"note":"No new holdout run. Historical evidence conflicts; see evidence/run_card_v2.json."},
  "correlation_overlap_vs_registry": {"evidence_class":"REGISTRY-MEASUREMENT","complete_scan":false,"surface_correlation":null,"final_dot_overlap":null,"stop_witness":"evidence/surface_uniqueness.json reports one checked raster and 1.0 forward overlap; not a complete scan."},
  "raster_sha256": null,
  "validator_output": {"no_nan_inside_footprint":null,"values_in_0_1":null,"crs_shape_transform_match":null,"note":"No release TIFF; historical local validator receipts are not uniqueness or scientific clearance."},
  "submission_name": null,
  "submission_note": "No file cleared; do not download or submit quarantined artifacts.",
  "verdict": "negative"
}
```
