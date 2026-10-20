# Handoff — 2026-10-20

Read README.md and PROJECT_BRIEF.md at session start.

**NEGATIVE. DO NOT SUBMIT. No eligible TIFF exists.**

The checkout started with only an eleven-byte README. Pinned numerical features,
sample and catalogue were restored from public owner mirrors into `.cache/data`.
No organizer-authenticated identity, current leaderboard receipt or weekly-cap
state is available. The notebook reference was retrieved from the official
DrivenData GitHub repository. No GPU was required for this fixed CPU hypothesis.

One preregistered contact-termination experiment ran. Every raw and transformed
feature received an AUC leakage canary and shared HOLDOUT-DTI. Whole mapped
components were withheld with a real three-pixel feature-context buffer, spatially
eroded quadrants and pixel-exact known-fault masking. No catalogue predictor was
used. The continuous surface is worse than its random sparse control; current
holdout best was not independently rerun. See evidence/holdout.json.

The surface passed numerical array checks but failed the literal overlap gate.
A SHA-verified 17GEMSDOE continuous prediction covers every footprint cell; its
halo leaves no off-catalogue allowed cell uncovered. No nonempty candidate can
pass the inherited literal support rule against it. **Do not silently exempt it.**
Only this decisive witness was compared; an incomplete scan cannot certify
uniqueness, but a duplicate witness suffices to stop. Final dots were not placed,
no submission writer was invoked for the scientific run, and no slot was used.
The shared writer's TIFF/ZIP behavior is tested only with synthetic temporary
unit-test fixtures, never published as competition predictions.

`vendor/gems57` is unchanged from 60GEMSDOE commit
`32024716f218d06a94e01464157392119c03cb15`; evidence/template_verification.json
compares both SHA-256 and upstream git blob identities. A false bound in the
metric's explanatory docstring was identified, but executable coverage arithmetic
is correct. Cross-repo issue creation was denied; see evidence/upstream_metric_report.md.

Next session must resolve the protocol representation conflict and missing lane
assignment before new science. A fresh ranking needs untouched evaluation blocks,
comparable current-best validation and complete pre-placement/final-dot audits.
Never tune the present fixed hypothesis after seeing its holdout.

Publication is intentionally fail-closed for this stopped experiment. The static
site cannot generate or train a TIFF in-browser. A fresh reviewed scientific run
and release contract are prerequisites to connecting the validated shared writer
to a real one-click artifact; editing run-card booleans is not sufficient.

Commands:

```
python -m venv .venv
.venv/bin/pip install -r requirements.lock
bash scripts/download_competition_data.sh
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

Do not rerun scripts/run_experiment.py: its existing experiment manifest makes it
refuse a second attempt. Data are reconstructible; large caches are ignored and
not committed. Source-health refresh is separate from scientific validation.

## Concurrent-main integration

Main advanced through PRs 1 and 2 while this session ran. Their reports, audit
helpers, bridge fixtures and tests are retained. The earlier review-only run card,
README and handoff are archived in evidence/history/parallel-review2. Canonical
publication scripts use the measured one-experiment card; the legacy card command
now verifies it rather than overwrite it. Root historical HTML paths redirect to
the current workbench. The combined suite passes 68 tests (three upstream
Rasterio/Affine pending-deprecation warnings). No unrelated candidate PR is
endorsed by this integration.

## Concurrent H70-C publication quarantine

Main subsequently advanced through PRs 4 and 5, advertising a second session's
H70-C TIFF as ready. Inspection found explicit simulated/placeholder holdout
values in generation source and a one-raster H33 comparison, not full literal
uniqueness clearance. All source, claims and files are preserved with hashes in
quarantine/concurrent-h70c and evidence/concurrent_h70c_quarantine.json; none is
endorsed or linked as a submission. Source text is retained, not executed. The
canonical site remains negative. No additional scientific experiment was run.

Final suite after adding quarantine hash/publication coverage: **69 tests pass**.

## Session 2026-10-20 — candidate C1 (experiment 2 of 3)

- **Result: negative. Do not submit.** C1 (strike-coherent catalogue extrapolation) passed the leakage canary
  (max folded AUC in `evidence/c1_canaries.json`) and failed both comparison gates on holdout seed 71:
  HOLDOUT-DTI 0.005570 vs random control 0.048375 and catalogue-free ablation 0.009023 (`evidence/c1_holdout.json`).
- **Registry (complete scan of the 862 indexed rasters):** 40 sparse dot-field and 52 continuous-surface
  overlap flags (`evidence/c1_registry_scan.json`). The index dates from 2026-10-12.
- **File:** `submissions/gems70-c1-strike-catalogue-NOT-CLEARED-20261020.tif` (git-ignored). Format-valid,
  LOCAL-FORMAT-VALIDATION only. Export receipt: `evidence/c1_export_receipt.json`. download_and_submit_ok = false.
- **Run card:** `evidence/c1_run_card.json`. Site run-card link now points here. E1 run card kept at `evidence/run_card.json`.
- **Official facts re-verified 2026-10-20:** `evidence/official_sources_2026-10-20.json` (quotes; deadline discrepancy;
  sample described as total absence but containing ones; outside-footprint convention).
- **Protocol:** no tuning on seed 71. Do not rerun `scripts/run_experiment.py`. Do not edit evidence to promote.
  The post-hoc binary diagnostic is not preregistered and is not a promotion basis.

### Open for the next session (in order)
1. Scan owner repos created or changed after the index date: GEMSDOE69 and GEMSDOE73–82 (not in
   `registry/inherited_registry_index.json`). The GitHub API hit its rate limit during this session.
2. Resolve the deadline discrepancy (competition page 11:59 p.m. UTC vs rules 5 p.m. ET) and the 0-vs-NaN outside-footprint
   convention with the organizers before any upload.
3. Only if time and budget allow, preregister one new candidate (C2, C5 or C3) on a fresh seed. Otherwise stop and report.
4. Eligibility (rules §1.3) and generative-AI narrative (rules §3.2) must be confirmed by the user before any submission.
5. Weekly-slot selection is a separate step, capped at three submissions per week.
