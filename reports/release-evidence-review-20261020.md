# Release-evidence review — 2026-10-20

## Outcome

**NEGATIVE — DO NOT SUBMIT. No eligible new TIFF was generated.** The requested
one-click competition artifact remains unmet, not replaced with a previous,
quarantined, synthetic, empty, or renamed prediction. No new scientific experiment,
final dot placement, training run, competition upload, or weekly slot selection
was performed in this review.

Read the retained prompt in README.md / PROJECT_BRIEF.md and the stopped-run
contract in AGENTS.md before resuming science. The prompt still has no identifiable
single-method lane paragraph. The four preregistered hypotheses remain in
[docs/hypotheses.md](../docs/hypotheses.md); they are not new experiments from this
review and their rejected top candidate must not be tuned on its exposed holdout.

## Pass 1 — inspect and reproduce

Inspected handoff, current run card, site status, release/validator CLIs, shared
registry audit, workflows, and existing tests. Ran `python scripts/audit.py`:
the pinned witness was restored and its hash, grid, registry membership, and
universal support were independently checked again. REGISTRY-MEASUREMENT:
minimum forward overlap is 1.0; the literal rule permits no more than 0.70.
This proves a stop, not full registry clearance or geological equivalence.
The rerun left the committed preflight evidence unchanged.

Verified the organizer reference repository remains accessible through GitHub API:
https://github.com/drivendataorg/gems-prize-reference-solution . This verifies
repository availability only, not present competition rules or any score.
Non-GitHub official sites are outside this sandbox's network allowlist. Neither
the current leaderboard, submission receipts nor weekly allowance is verified.

## Pass 2 — defects and regression fixes

Found two diagnostic defects outside the byte-pinned scientific template:

- `valid_canary` passed arbitrary-size JSON integers to `math.isfinite` before
  range checking. Such integers can raise `OverflowError` rather than yield a
  clean negative. Check the numeric range first; no valid AUC changes behavior.
- A truthy non-boolean `current_best_verified` (including the string `"false"`)
  suppressed the missing-current-best diagnostic. Require literal JSON `true`.
  Publication was already unconditionally blocked for this stopped run; this
  change fixes evidence interpretation, not a demonstrated release bypass.

Added regression tests for both signs of oversized integer and multiple truthy
non-boolean verification claims. Tests use temporary copies of the pinned run
sources and evidence, not new scientific results. No template, feature method,
preregistration, holdout, canary receipt, or archived TIFF was edited.

## Pass 3 — end-to-end requirements check

- `python -m pytest -q`: **124 passed**, three existing Rasterio/Affine warnings.
  This is SOFTWARE-TEST output, not a scientific or competition score.
- `python scripts/release_gate.py --expect-negative`: success means the expected
  **negative** was reproduced; template integrity passes. It authorizes no upload.
- `python scripts/build_site.py` and `python scripts/build_readme.py`: successful;
  no generated tracked content changed and no prediction artifact was published.
- The actual new TIFF validator output and raster SHA-256 remain null because no
  new submission file exists. Array checks must not be presented as file checks.
- The complete prompt remains embedded in README; the executive submission guide
  and site banner correctly state that no eligible download exists.

## H33 interpretation and next-session order

The [existing byte-level H33 analysis](../docs/h33-analysis.md) finds catalogue-near
pruning of an earlier sparse field, not a fundamentally new geological predictor.
Reducing emitted mass while retaining truth coverage can improve the shared
Tversky objective. This is a conditional mechanism, not proof of why hidden
organizer labels yielded a reported result. There is no organizer-confirmed
receipt here; exceeding the user-reported historical score is unproven.

1. Resolve continuous-support versus dot-support semantics once in the shared
   protocol/template, across parallel sessions. No private density exemption.
2. Record an explicit lane and preregister a fresh run on untouched evaluation
   blocks, with a same-split current-best comparator. No rerun of the stopped run.
3. Keep feature-alone canaries, buffered whole-segment recovery, pooled metric,
   confidence intervals and complete surface/final-dot inventory audits mandatory.
4. Only after scientific clearance, use the shared writer and validate the actual
   TIFF bytes against the sample; then a separate selector checks live weekly
   allowance. Format validity is not selection authorization.
5. Review the independent open PR #8's publication-boundary changes separately;
   this review does not merge or certify another session's PR. A GitHub Pages
   build and source configuration are not a verified live direct-URL fetch.
