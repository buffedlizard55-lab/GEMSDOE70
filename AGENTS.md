# Session start contract

1. Read README.md and the complete PROJECT_BRIEF.md before any new work.
2. Read HANDOFF.md, evidence/run_card.json and docs/irregularities.md.
3. A candidate artifact may be published without being promoted. Always publish BOTH flags
   (`download_ok`, `submit_recommended`); never describe a non-promoted file as an improvement.
4. `vendor/gems57` is pinned in `registry/template_pin.json`. Two fixes are recorded there with
   `all_identical: false` (binary-dot definition; mutual-overlap duplication). Any further change
   must be justified by measurement, reported in `evidence/upstream_fix_report.md`, and proposed
   upstream — never a private metric or a discretionary exemption.
5. Dots are binary (`|value − 1| < 1e-6`). Duplication requires mutual overlap > 0.70 AND
   Spearman ≤ 0.90 against every checked registry raster; both directions are always reported.
6. Weekly slot selection is separate from candidate generation and is the user's decision. Never
   record a score as ORGANIZER-CONFIRMED without a submission-page receipt.
7. Own the outcome: a measured negative with a reproducible receipt beats a false score, an
   unsupported promotion, or an unsafe download.

## Parallel-lane addendum (2026-10-20, PR #16)
- E2/E3 evidence and cards (`evidence/e2|e3/`) are frozen like Phase 1-4. The E2 review TIFF is inventoried but never promoted; `release.candidate_status().submit_ok` stays False until selector gates in `docs/publication-amendment-e2.md` are recorded.
- E2 uniqueness numbers predate the mutual-overlap fix (R1 subset audit). Re-audit E2 under the corrected rule before comparing uniqueness across lanes.

## Current-request override (2026-10-20, arena/3169a6c0-gemsdoe70)
The user explicitly requires **forward** overlap >0.70 to stop. Historical mutual-overlap
clearances are not sufficient for this request. Read `docs/protocol-review.md` and
`evidence/current_protocol_review.json` first; a P4 final-dot witness requires STOP.
No new lane paragraph was identifiable. Do not generate a new candidate or silently waive the
stop. `gems70.protocol` is a policy adapter over frozen measurements, not a replacement metric.
The shared scientific cards/evaluator/writer remain unchanged. Review-only downloads are allowed;
no slot is authorized. A passing historical subset audit cannot certify current registry coverage.
