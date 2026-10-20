# Repository review — 2026-10-20

## Executive result

**Negative; do not submit.** This checkout contains no eligible, unique competition TIFF. The stopped scientific run is preserved and may not be rerun or tuned on its existing holdout. This review made no scientific changes, placed no dots, invoked no submission export, and used no competition slot.

## Pass 1 — inspect project state and evidence

- Read the complete `README.md` and `PROJECT_BRIEF.md`, plus `AGENTS.md`, `HANDOFF.md`, `docs/irregularities.md`, the preregistered hypotheses, release code, run card and experiment receipts.
- Confirmed the repository is already an evidence-first negative workbench. It preserves the supplied prompt in the README and retains a submission guide, H33 forensic analysis, four qualitative hypotheses, source ledger, and stop/run-card receipts.
- The task's reference value **0.2778** remains an unverified historical claim, not **ORGANIZER-CONFIRMED**: no authenticated submission-page receipt was found. The archived H33 pixels are measured as a catalogue-flank pruning of H27; a conditional metric explanation is documented, not a causal claim about hidden labels.
- The tested magnetic-edge termination method has **HOLDOUT-DTI** 0.0101928890, 95% CI [0.0060620859, 0.0150416449], evaluator `gems57-pooled-hide-v2`, 11,321 withheld positive pixels. It is a continuous pre-placement surface, not a final-dot result or leaderboard score. The random sparse control's **HOLDOUT-DTI** is 0.0471696678, 95% CI [0.0422872784, 0.0509206556], same evaluator and withheld-positive count. The experiment does not establish performance above the current same-split best.
- One SHA-verified archived continuous raster is positive over the allowed prediction footprint. Under the inherited literal support rule, the measured minimum forward overlap for any nonempty candidate is 1.0, above the 0.70 stop threshold. This is a decisive duplicate witness for that rule, not a complete registry inventory or proof that geological methods are equivalent.

## Pass 2 — adversarial checks and commands

- Created an ignored local environment from the pinned `requirements.lock`; no tracked dependency or data files were changed.
- `.venv/bin/python -m pytest -q`: **117 passed**, with three existing Rasterio/Affine pending-deprecation warnings.
- `.venv/bin/python scripts/audit.py`: returned the recorded negative result; verified witness overlap is 1.0. The output explicitly says it is not a complete current registry scan.
- `.venv/bin/python scripts/release_gate.py --expect-negative`: exited 0 and reported template integrity OK, negative verdict, `generated_tif: null`, `download_available: false`, zero submission slots used, and explicit release blockers.
- `.venv/bin/python scripts/release_gate.py`: returned exit 2 as designed for a blocked release.
- `.venv/bin/python scripts/check_pages.py`: returned exit 2. The live GitHub Pages API reports legacy publication from `main:/`, not `/docs`. The previous configuration write attempt is documented as denied with HTTP 403 (`Resource not accessible by integration`). Root Jekyll exclusions are a source-tree mitigation, not proof of a changed Pages source or of deployed output contents. Treat publication-boundary assurance as unresolved until an authorized configuration change and deployment check succeed.
- No `.tif`, `.tiff`, or `.zip` is present under `docs/`. Historical TIFF/ZIP artifacts exist only under `quarantine/concurrent-h70c/`; they are explicitly not endorsed and must not be downloaded or submitted.
- Official DrivenData, USGS, DOE repository and NLR sources are not verified in this environment; the recorded HTTP checks failed from the sandbox. GitHub reference/template content was available. Do not infer global source unavailability, a login redirect, current leaderboard status, or organizer score confirmation from those failures.

## Pass 3 — compare with the requested outcome

| Requirement | Review disposition |
|---|---|
| Reusable shared holdout/evaluator and writer | The byte-pinned shared implementation is retained and verified; science used shared evaluator. The writer is covered by synthetic temporary tests only and was not invoked for this stopped candidate. |
| Three-to-five candidate hypotheses | Four are preregistered and ranked qualitatively in `docs/hypotheses.md`; only one fixed method was tested. No numeric score improvement is projected. |
| Leakage canaries / spatial holdout | Completed for the stopped experiment; see `evidence/canaries.json` and `evidence/holdout.json`. |
| Prove candidate beats current holdout best | Not established; no comparable incumbent result is available, and this candidate loses to its random sparse control. |
| Unique downloadable submission TIFF | **Not fulfilled.** The literal duplicate stop applies before dot placement; no TIFF or final-dot validation exists. A fake, copied, zero-valued, or renamed artifact would be unsafe and misleading. |
| H33 score explanation | Pixel-level pruning relationship and conditional metric algebra are documented. The score itself is not organizer-confirmed, and hidden-label causation cannot be inferred. |
| Up-to-date official score feed | Not present; source-health records endpoint availability only, not authenticated scores. |
| GitHub Pages publication safety | **Not fully verified.** Pages remains configured at root; the prior `/docs` setting change was denied. Current read-only check still reports `safe_boundary: false`. |
| PR and merge | This review started at the merged baseline with no tracked changes. No empty PR was created. Merged PR #7 is present in repository history; separate open PR #8 belongs to another lane and was not modified. |

## Next actions

1. Have the shared protocol owner explicitly reconcile dense continuous raster support with the dot-overlap uniqueness rule. Do not privately exempt dense rasters or change thresholds.
2. Provide the missing single-method lane assignment and a same-split incumbent implementation, while keeping any newly selected holdout blocks untouched.
3. Obtain authorized organizer-page access to verify current rules, leaderboard and weekly quota; record a submission-page receipt only if a real submission is later selected.
4. Ask a Pages administrator to set `main:/docs`, then independently confirm the API setting and deployed contents. Do not represent the current root-source mitigation as completed isolation.
5. After—not before—those prerequisites, run a fresh preregistered experiment within budget, complete pre-placement and final-dot inventory audits, compare against the current best, and only then call the shared writer and exact-byte validator.

This review is an engineering status report, not a new experiment, submission authorization, or promise to exceed the user-reported 0.2778 value.
