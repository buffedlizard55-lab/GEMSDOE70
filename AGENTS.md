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
