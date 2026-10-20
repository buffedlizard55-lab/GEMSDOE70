> **Historical parallel-session review.** Retained for provenance. Current status, experiment count and evidence are in [README](../README.md) and [the current run card](../evidence/run_card.json); this document is not a current release authorization.

# Repository review — 2026-10-20 UTC

## Executive decision

**NEGATIVE / BLOCKED — DO NOT SUBMIT. No new TIFF was generated.** The request for
a valid unique TIFF cannot be completed under the simultaneously mandatory
literal duplicate-and-stop protocol. This is an unmet deliverable, not a claimed
success. No file has been renamed, copied, perturbed, or advertised as a new
competition submission. No competition slot was used.

## Checked facts, evidence and irregularities

| ID | Finding | Evidence / action |
|---|---|---|
| IR70-01 | Initial repository contained only an 11-byte README; the full ready-to-train pipeline and named download/prepare scripts in the brief did not exist. There were no previous-session tasks on the initial branch snapshot to resume; a concurrent review later reached main and has been preserved. | Initial `git ls-tree`, base commit `a9bfaa70f1b985f09dc2e79606444ad99a5d449a`. Do not claim data placement is the only blocker. |
| IR70-02 | Required lane method paragraph is absent from the supplied prompt. | Preserved prompt in PROMPT.md and README. No neighboring lane was silently adopted. Research hypotheses are conditional suggestions, not experiments. |
| IR70-03 | Literal forward-overlap rule rejects every nonempty in-footprint candidate because one registry member has strictly positive support everywhere in the sample footprint. | Fresh `evidence/preflight.json`, independently hash-verified witness; not just the neighboring repo's old verdict. Stop before surface placement or final dots. |
| IR70-04 | The inherited registry is not a current exhaustive competition registry. | `registry/inherited_registry_index.json` is a historical owner-repo inventory. Only one witness is fetched for this proof; no complete-scan clearance claimed. A single verified witness suffices for a negative existential test. |
| IR70-05 | No submission-page receipt binds the reported H33 result to its bytes. | Reference site says UNSCORED; source claims registry distinguishes owner reports. USER-REPORTED values remain unverified, not ORGANIZER-CONFIRMED. |
| IR70-06 | Brief lists conflicting leaderboard targets. | Fresh official page was read and recorded as a PUBLIC-LEADERBOARD-OBSERVATION, not an artifact receipt. Do not select a historical target as current by assumption. |
| IR70-07 | Owner mirrors are not organizer-authenticated. | Bridge hashes match pinned shared tools, upstream Git blobs checked. This proves mirror consistency only. |
| IR70-08 | Prior site asserts the user's portal error was caused by a nodata sentinel/NaN. The rejected TIFF and portal implementation are not available. | Diagnosis is not established. Shared writer rejects non-finite/out-of-range model outputs rather than clipping. No acceptance claim for zero-outside exports. |
| IR70-09 | Official format text describes null/NaN outside the footprint/bounds; shared writer deliberately offers only an all-finite export. | Preserve shared bytes and disclose the discrepancy. A zero-outside file may pass local checks, but cannot be called organizer-accepted here. Resolve upstream/with organizer before a positive release. |
| IR70-10 | Prior static-artifact holdouts, calibrated surrogate projections, and current pooled hide-and-recover are not interchangeable. | No reported historical number is imported as the current holdout best. Future incumbents must be rebuilt from visible-only catalogue features on the same folds. |
| IR70-11 | Neighboring GEMSDOE69 handoff says its archived candidate is negative; code/evidence provenance issues were found there. | Preserved handoff for education. No borrowed candidate, result, phase receipt, or clearance is used here. |
| IR70-12 | The shared metric docstring contains an unjustified aside `delta_T <= k_self`; a dot can cover several truth pixels. | Prose limitation logged in vendor/README; implementation is unmodified. Independent oracle tests target the actual equations. Any upstream correction must happen in the template, not a private fork. |
| IR70-14 | Attempt to open an upstream shared-template prose issue was denied by GitHub integration permissions (`Resource not accessible by integration`). | No upstream issue or fix is claimed. Reproducer retained in vendor/README.md and research review; shared bytes remain unchanged. |
| IR70-13 | No full family-wide scientific novelty audit or deep literature survey has been completed. | Main reference page/source, neighboring handoff and inherited registry were inspected. All requested family links are retained in the prompt for later audit. Do not call local novelty global novelty. |

## Proof of the uniqueness conflict

Let `F` be the finite sample-footprint cells. For the fetched registry witness
`W`, the measured support satisfies `{x in F : W(x) > 0} = F`. If a candidate has
any nonempty support `C` contained in `F`, every `c in C` is also on positive
witness support. Its nearest witness point is itself: distance zero. Thus
`count(c in C: distance(c, support(W)) <= 3) / count(C) = 1`, exceeding the
protocol limit. No choice of scientific hypothesis, dot placement, random seed,
float perturbation or file name can make such a candidate pass. An all-zero
raster avoids the denominator only by making a non-prediction; it is not a
scientific discovery submission or an acceptable workaround.

This is a support/registry-definition conflict, **not** evidence that every
possible geological method has the same mechanism. The decision to revise that
protocol or registry is outside this lane. We did not exempt dense rasters,
change the positivity threshold, stratify away failed comparisons, or continue
placing dots after a duplicate.

## Three review passes

### Pass 1 — implementation and factual preflight

Inspected the empty checkout; read official problem/metric/format text and
relevant rules sections; inspected H33 construction and actual artifact bytes
for education; restored shared tools and bridge inputs from a pinned owner
mirror; fetched the registry witness through content-addressed GitHub blobs.
Ran `scripts/audit.py` and measured the universal-support obstruction. Added
research queue, audit tooling, a local validation entry point, and a site that
shows its blocked state before anything else. No model was trained or evaluated.

### Pass 2 — defects and edge cases

Checked upstream tree/blob IDs against the local vendor manifest, rather than
trusting an inherited `all_identical` flag. Added tests for empty footprints,
nonfinite witness cells, dense/sparse support, strict threshold boundaries,
shared-metric soft/binary behavior, exact visible-fault masking, pooled-block
terms, and writer rejection of NaN, infinities and sentinels. Corrected the
unsupported nodata diagnosis and documented the outside-footprint policy conflict.
Added structured CLI failures for missing/wrong-grid files and strict JSON encoding of nonfinite metadata (without changing predictions). Added negative-only release policy: changing a card field cannot create a link.

### Pass 3 — original-request compliance

Added a requirements matrix, full working prompt in README, next-session handoff,
linked official-source table, executive submission guide, real-input hash tests,
full-size shared-writer roundtrip **only in a temporary test directory**, static
link checks, and CI. A temporary test TIFF is not a scientific submission and is
not retained or published. The site never exposes input rasters as predictions.
No success is claimed for unmet generation, training, holdout or novelty tasks.
PR, merge, tests and Pages publication receipts are recorded separately.

## Concurrent upstream review integrated

The first merge attempt for PR #2 failed because main advanced to `4b63eba`,
merging a separate review in PR #1. That work was merged into the assigned
branch (no branch switch). Its dated `docs/review-2026-10-20.md` is preserved
with a historical/supersession banner. Its request to restore the shared tools
is now addressed; the missing lane and scientific validation blockers remain.
Its public-leaderboard “ORGANIZER-CONFIRMED” wording is explicitly corrected
as not meeting the artifact-bound submission-page-receipt requirement.

## Next steps, in order

1. Explicitly resolve the registry definition/literal overlap contradiction and
   supply the single-method lane. Do not silently relax the mandatory rule.
2. Authenticate organizer sample/feature/catalogue identities through authorized
   account downloads; verify current rules, outside-footprint encoding and the
   remaining weekly quota. Never put account credentials in the repo or chat.
3. Restore the pinned feature stack using the inherited fetcher. Verify every
   band identity and missing-data mask, especially ambiguous abbreviations such
   as `tc` and the physical meaning of `depth_to_base_surf` (do not assume
   geological basement when the official page describes a conductive base).
4. Build a same-evaluator visible-only incumbent and preregister an assigned
   candidate on untouched blocks. No current-best comparison can be inferred
   from a leaderboard receipt or previously frozen full-catalogue TIFF.
5. Canary every feature; run pooled spatial holdout with withheld count and
   paired block-bootstrap CI; retain negatives. Remain within experiment/time cap.
6. Surface uniqueness **before** placement; final-dot uniqueness after; write
   through the shared tool; independently reopen exact bytes and bind all
   evidence; pass to the separate selector. Only then enable a TIFF download.
7. If selected, use an authorized account to submit within the available quota;
   save the submission-page receipt and its exact raster SHA-256. Do not call a
   local validator PASS organizer acceptance.

## Limitations

Shell binary-download hosts are restricted to GitHub/npm/PyPI endpoints. The
research-page tool can read some official sources, which does not grant shell
binary access. There is no DrivenData account session here. GPU access is not
needed for the current audits, and the official reference supports CPU-only
training; saying a GPU is a hard requirement would be incorrect. No scientific
training implementation or evaluated candidate currently exists in GEMSDOE70.
GitHub Pages is static hosting: it cannot train a model or generate a large
geophysical raster in the server. The delivered site is a transparent report and
submission guide, **not** a claimed functioning model-generation service.

## Verification receipt

Final local suite: **40 software tests passed**, with one rasterio/affine pending-deprecation warning. This is a software result, not a scientific HOLDOUT-DTI. Shared-writer roundtrip uses a temporary toy point only. The default release command exited 2 as intended; the audit and expected-negative CI mode exit 0 without authorizing submission.
