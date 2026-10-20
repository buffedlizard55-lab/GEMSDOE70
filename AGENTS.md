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

## Current prompt override (2026-10-20, review on arena/4aea4e21-gemsdoe70)
The latest explicit user protocol requires FORWARD overlap > 0.70 to stop.
Earlier mutual-overlap language above describes historical evidence only, not
permission to relax this instruction. Preserve frozen audits. Release authorization
must apply the stricter current rule. See docs/protocol-review.md; no method
paragraph was supplied, no new modeling is authorized by this review.
