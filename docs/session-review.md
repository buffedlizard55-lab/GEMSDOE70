# Repository review — 20 October 2026

## Decision: DO NOT SUBMIT

**There is no eligible new TIFF to download.** The mandatory duplicate-and-stop protocol still prevents a nonempty candidate from qualifying. Generating an all-zero file, perturbing an archived submission, or publishing the quarantined H70-C file would not meet the request. The requested new submission remains **unfulfilled**, not silently substituted with a software-test raster.

This session performed a repository/publication review, not a new scientific experiment. The measured run card remains unchanged. No competition upload or weekly slot was used.

## Review findings and evidence

| Finding | Verification | Action |
|---|---|---|
| A registered continuous raster has positive support throughout the footprint. | Re-ran `scripts/audit.py`: restored the content-addressed witness, verified its SHA-256 and sample alignment, reproduced the universal-overlap proof. [Witness specification](https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/registry/witness.json), [audit receipt](https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/evidence/preflight.json). | Remain stopped. This is a representation conflict, not proof that every geological method is identical. One witness proves failure; it does not certify a complete registry scan. |
| GitHub Pages was configured for `main:/`, not `/docs`. Root `.nojekyll` made the repository a static publication source, including archived data/quarantine paths regardless of whether links advertised them. | GitHub Pages API returned legacy build, branch `main`, path `/`. [Before-setting receipt](https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/evidence/pages-before-review.json). This establishes exposure risk; the restricted network did not allow a live direct-URL fetch. | Remove the root `.nojekyll` bypass; exclude all nonpublic root content with `_config.yml`. Add an audited public-root policy and a CI build of the actual legacy source. Preserve quarantine bytes in Git for forensic review, not as Pages downloads. |
| Directly changing the Pages source was denied. | GitHub API returned HTTP 403, `Resource not accessible by integration`. [Operation receipt](https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/evidence/pages-settings-attempt.json). | Use the existing legacy-root source with Jekyll exclusions; do not claim the settings were changed. The source change is not an authentication failure or a reason to request credentials. Publication changes require merge and a successful Pages build. |
| Existing publication tests checked `docs/` or advertised links, not the deployed repository-root boundary. | Inspected `tests/test_site.py`, `tests/test_contract.py`, and Pages source settings. | Add tests for unlinked TIFF/ZIP paths, archived text at nonpublic roots, case-insensitive extensions, symlinks, missing banners, and unclassified new root content. A separate CI check inspects the real Jekyll output. |
| H70-C generation source includes simulated holdout and placeholder claims. | Existing SHA-bound quarantine receipt and source text; software tests recheck archival bytes. | Never execute that source or promote its artifacts. File validity alone cannot repair fabricated scientific evidence. |
| The historical H33 result is not tied to an organizer submission receipt here. | Existing byte-level H33 audit and [forensic analysis](h33-analysis.html). | Retain the pruning/coverage-efficiency explanation, not a causal claim or promised score. |

## Scientific conclusion

H33 is an archived sparse field with catalogue-flank points removed, not evidence of a newly trained geological detector. Under distance-weighted Tversky scoring, deleting prediction mass can help **if lost truth coverage is sufficiently small**. Hidden labels are unavailable, so neither the reason for its reported historical score nor an improvement beyond it is established.

The existing magnetic-edge-termination candidate remains a negative: **HOLDOUT-DTI 0.010193, 95% CI [0.006062, 0.015042], evaluator `gems57-pooled-hide-v2`, 11,321 withheld positive pixels**. This is an inherited measured continuous surface result, not recomputed science in this review, final-dot performance, or a leaderboard score. It did not establish an improvement over the current holdout best. [Full receipt](downloads/holdout.json).

The [four ranked preregistered hypotheses](hypotheses.html) already name layers, physical signatures, possible catalogue omissions, non-fault mimics and implementation cost. They remain hypotheses, not confirmed discoveries. This review does **not** claim a fresh set of previously untried methods or run additional hypotheses after a duplicate stop. Uninspected parallel sessions preclude a global novelty claim. The original experiment's preregistration, source pins and results are frozen.

## Three review passes

1. **Inventory and reproduction:** read the retained brief, handoff, scientific receipts and publication code; installed locked dependencies; ran the existing software suite and independently reproduced the blocking witness audit.
2. **Defect correction:** addressed the root-Pages exposure gap without altering shared scientific tools, quarantined bytes, prediction arrays, thresholds, or the stopped run. Regression coverage now checks actual publication boundaries rather than only download links.
3. **Compliance and verification:** rebuilt the evidence site/README deterministically and reran the complete software suite and release gate. The first real Jekyll-output check caught GitHub's automatically injected `assets/css/style.css`; the policy now permits only that exact generated stylesheet and its directories, not arbitrary repository assets. A regression test rejects any additional archived asset. Final combined local suite: **138 software tests passed**, with three existing Rasterio/Affine pending-deprecation warnings. These are software checks, not scientific scores. Verification/deployment outcomes are recorded in [PR #8](https://github.com/buffedlizard55-lab/GEMSDOE70/pull/8) and GitHub checks; this document does not assume a future CI or deployment success.

## Concurrent-main integration

The first merge attempt was rejected because parallel PRs #6 and #7 had advanced main. Merged `f1197da` into the assigned session branch without switching branches. Preserved both reviews, their root-tree/symlink guards, stricter release diagnostics and tests. The Pages output audit complements those source checks; it does not replace or weaken them. The combined suite count above includes all preserved tests. A second integration retained PRs #9–#11 from main `7a2d2ae`, including the unresolved protocol memo and additional malformed-evidence diagnostics. Corrected its checkout-only evidence/handoff links to GitHub URLs, and added actual built-output link checks so excluded repository files cannot masquerade as working site links. No scientific receipt or shared template changed.

## Required next work, in order

1. Resolve the continuous-surface versus dot-support ambiguity **in the shared protocol**, with an explicit version and consistent treatment across all lanes. Do not silently exclude the dense witness or raise thresholds.
2. Obtain the missing assigned method paragraph. Confirm official input identity, current format/rules, outside-footprint encoding and remaining submission allowance. Restricted access is not evidence of a login redirect.
3. Rebuild a visible-only incumbent on comparable, untouched holdout blocks. A frozen full-catalogue submission is not a leakage-safe incumbent. Do not tune the stopped candidate on its disclosed holdout.
4. Preregister a genuinely distinct method, canary every feature, and test within the experiment/time budget. Conduct a complete surface audit before placement, then a complete final-dot audit.
5. Only after scientific clearance, use the pinned shared writer, reopen exact TIFF bytes, validate finite/range/grid constraints, bind the file SHA-256 to its receipts, and expose a one-click download. A separate selector must authorize use of a weekly slot.

## Official and reproducible references

- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): accessible official code; fault detection is the direct task, not verified geothermal-vent discovery.
- [Organizer problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/): manual-review targets, not live-verified receipts in this network.
- [GitHub Pages API](https://docs.github.com/en/rest/pages/pages#update-information-about-a-github-pages-site): official manual-review reference for the denied settings operation.
- [Jekyll configuration](https://jekyllrb.com/docs/configuration/options/): official manual-review reference for exclusions. The actual publication behavior must be verified by building, not by citing this link alone.
- [GitHub's Pages build action, pinned source](https://github.com/actions/jekyll-build-pages/tree/44a6e6beabd48582f863aeeb6cb2151cc1716697): inspected action definition; the CI publication test uses this action.

GitHub-hosted source/data access is available; other research/data hosts are restricted in this environment. No organizer account session, artifact-bound score receipt, current weekly allowance, or permission to change Pages settings is established. No GPU is needed for these audits. The site is a static evidence workbench, not an in-browser trainer. Quarantine exclusion is a publication safeguard, **not secrecy**: archived bytes remain accessible in the public GitHub repository for audit.
