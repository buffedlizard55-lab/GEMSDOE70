# Session start contract

1. Read README.md and the complete PROJECT_BRIEF.md before any new work.
2. Read HANDOFF.md, evidence/run_card.json and docs/irregularities.md.
3. Read docs/protocol-review.md and evidence/review/run_card.json. Current policy is literal forward overlap; the inherited mutual rule below is superseded. No new fixed-mass candidate or slot after the recorded stop.
4. A candidate artifact may be published without being promoted. Always publish BOTH flags
   (`download_ok`, `submit_recommended`); never describe a non-promoted file as an improvement.
5. `vendor/gems57` is pinned in `registry/template_pin.json`. Two fixes are recorded there with
   `all_identical: false` (binary-dot definition; mutual-overlap duplication). Any further change
   must be justified by measurement, reported in `evidence/upstream_fix_report.md`, and proposed
   upstream — never a private metric or a discretionary exemption.
6. Dots in the fresh witness are binary. Current duplication stop: forward overlap > 0.70 OR
   Spearman > 0.90. Reverse overlap is diagnostic only; never use it as an exemption. A single
   positive witness rejects; an incomplete scan cannot certify uniqueness.
7. Weekly slot selection is separate from candidate generation and is the user's decision. Never
   record a score as ORGANIZER-CONFIRMED without a submission-page receipt.
8. Own the outcome: a measured negative with a reproducible receipt beats a false score, an
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

## Parallel-session E3 scarp lane (PR #17)

Candidate `gems70e3-scarpcurv-60k-ex3-20261020-zeros` published; catalogue-holdout promotion only;
B′ unscored. Frozen one-shot drivers: `scripts/run_experiment_e2_scarp.py`,
`scripts/run_experiment_e3_scarp.py`, `scripts/complete_e3_release.py` — do not rerun.
`src/gems70/release_e3.py` guards its hash binding (RENAMED_AT_MERGE resolves frozen pins).

## Current-request override (2026-10-20, arena/3169a6c0-gemsdoe70)
The user explicitly requires **forward** overlap >0.70 to stop. Historical mutual-overlap
clearances are not sufficient for this request. Read `docs/protocol-review.md` and
`evidence/current_protocol_review.json` first; a P4 final-dot witness requires STOP.
No new lane paragraph was identifiable. Do not generate a new candidate or silently waive the
stop. `gems70.protocol` is a policy adapter over frozen measurements, not a replacement metric.
The shared scientific cards/evaluator/writer remain unchanged. Review-only downloads are allowed;
no slot is authorized. A passing historical subset audit cannot certify current registry coverage.
