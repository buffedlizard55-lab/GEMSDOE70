# Session start contract

1. Read README.md and the complete PROJECT_BRIEF.md before any new work.
2. Read HANDOFF.md, evidence/run_card.json and docs/irregularities.md.
3. An archived artifact may be retained for forensic review without promotion; that is
   **not** an eligible new submission download. Always distinguish `download_ok` for an
   eligible new TIFF from `download_for_research_only`. A format pass does not waive a
   scientific or registry stop.
4. `vendor/gems57` is pinned in `registry/template_pin.json`; its inherited
   uniqueness.py already differs from the upstream template (binary-dot definition and
   mutual-overlap gate). **Do not privately modify or treat that difference as protocol
   approval.** A shared-tool correction needs a versioned upstream review; evaluator
   and writer remain pinned unchanged.
5. The user's rule governs: STOP if rank correlation exceeds 0.90 **OR more than
   70% of our dots** are within three pixels of any ONE registry raster's dots.
   Check the surface before placement and the final dot set; the vendored
   mutual-overlap gate is diagnostic, not an exemption. `evidence/literal_overlap_stop.json`
   records a SHA-verified binary-dot witness with forward overlap 1.0 for
   historical P4/E2/discordance. Its halo covers 99.8724%, **not all**, of
   off-catalogue cells. No current new TIFF is cleared.
6. Weekly slot selection is separate from candidate generation and is the user's decision. Never
   record a score as ORGANIZER-CONFIRMED without a submission-page receipt.
7. Own the outcome: a measured negative with a reproducible receipt beats a false score, an
   unsupported promotion, or an unsafe download.

## Parallel-lane addendum (2026-10-20, PR #16)
- E2/E3 evidence and cards (`evidence/e2|e3/`) are frozen like Phase 1-4. The E2 review TIFF is inventoried but never promoted; `release.candidate_status().submit_ok` stays False until selector gates in `docs/publication-amendment-e2.md` are recorded.
- E2's former R1-subset "selector-review" receipt is historical, **not** current permission. A later SHA-pinned binary lattice yields 1.0 forward overlap for its exact final TIFF. E2 is stopped by the user's rule; a complete scan is needed to *clear future, different* surfaces, never to un-stop this measured duplicate.
