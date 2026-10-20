# Irregularities, limitations and remaining work

Status as of 2026-10-20. Current candidate C1: **DO NOT SUBMIT**. Nothing here is ORGANIZER-CONFIRMED.

## Irregularities found in the official material or in this repository

- **Deadline mismatch.** The competition page gives “Dec. 3, 2026, 11:59 p.m. UTC”. Rules A.1 require posting “by 5:00 p.m. ET on the prize submission deadline date”, which is 22:00 UTC on Dec. 3. The earlier cutoff is the safe one. Confirm with the organizers (gemsprize@nlr.gov is listed on the competition page).
- **Sample described as “total fault absence”, but not all-zero.** The problem page calls `sample_submission.tif` a prediction of total absence. The local copy has finite cells exactly {0, 1} with 60,988 ones (measured in an earlier session). Treat the sample as a format template only. Its values are not a model of absence.
- **Outside-footprint convention.** The problem page says data outside the bounds is “null or nan”. The sample uses NaN there. Our shared writer writes 0 outside the footprint (C1 export: `nan_count` 0, `outside_footprint_positive` 0). The validator accepts this locally. Organizer acceptance is not verified.
- **Source checksums are not authentication.** Competition data came from pinned public owner mirrors. The checksums show consistency with each other, not organizer authorship.
- **Leaderboard not readable.** The DrivenData leaderboard is rendered by script. Leader values in the prompt (for example 0.2778 and 0.4413) remain unverified.
- **Data tab requires login.** The data page redirects to login; the official data files were not fetched directly from DrivenData.
- **Generative AI disclosure.** Rules §3.2 require a narrative disclosure. The narrative must be written and checked before any submission.
- **Rules reference.** The DrivenData rules page only links to HeroX, which links to the NLR PDF. We used the PDF (dated SEPTEMBER 2026).

## Registry coverage gaps (must fix before any candidate is cleared)

- **Index age.** `registry/inherited_registry_index.json` was generated 2026-10-12. The complete scan covers the 862 rasters in it and nothing newer.
- **Eleven owner repos are not in the index:** GEMSDOE69 and GEMSDOE73 through GEMSDOE82 (ten of them were created on 2026-10-20). Their rasters were not scanned: the GitHub API rate limit was reached during this session (HTTP 403). This does not change the C1 verdict, which is already negative, but it means the uniqueness claim for any future candidate must include them.
- **Literal overlap rule.** The shared 3 px overlap rule (limit 0.70) flags lane collisions. It is not a quality measure. A random raster can pass it while scoring poorly, and a good raster can fail it. Its effect on a good candidate is unmeasured. Do not exempt or reinterpret it without a revised protocol (AGENTS.md rule 5).

## Scientific limitations

- **C1 is negative on the pre-registered holdout.** HOLDOUT-DTI 0.005570 is below the random sparse control (0.048375) and the catalogue-free ablation (0.009023). The leakage canary passed. The candidate is not promoted, and the holdout seed 71 must not be used for tuning.
- **Post-hoc transform diagnostic.** The binary top-2% test is not preregistered. It does not rescue C1 (random control 0.0622 vs C1 0.0121). It is reported for transparency only.
- **Holdout proxy.** Mapped connected components are a surrogate for previously unmapped faults. The organizer's hidden labels are not available. Confidence intervals are conditional on the fitted folds, catalogue labels and budgets.
- **No current-best comparison.** The current best method has not been rerun on the identical split. Controls are not a certificate of beating the family best.
- **Continuous surfaces, not final dots.** All holdout numbers are for continuous pre-placement surfaces. The final placement step and its full-inventory uniqueness audit have not been done.

## Process limitations

- **Experiment budget.** 2 of 3 experiments used (E1 magnetic-edge termination, E2 C1). The 2-hour budget is nearly exhausted.
- **No weekly slot used.** Submissions are capped at three per week (rules §3.2 and §3.4). Slot selection is a separate step and was not performed.
- **Eligibility not checked.** Rules §1.3 require U.S. citizenship or permanent residence for individuals, and U.S. incorporation for private entities. The user must confirm this.
- **Concurrent sessions.** Other sessions have pushed material into main at various times (for example the quarantined H70-C artifacts). They are not endorsed here. See `evidence/concurrent_h70c_quarantine.json`.

## Remaining work, in order

1. Scan the eleven uncovered owner repos (GEMSDOE69, GEMSDOE73–82) once the API rate limit resets; rerun `scripts/registry_scan.py` against an index that includes them.
2. Resolve the deadline discrepancy with the organizers, and confirm the outside-footprint convention (0 vs NaN) through an official channel.
3. Decide whether to preregister a third experiment on a fresh seed (C2, C5 or C3). Do not tune C1 on seed 71.
4. Write the generative-AI narrative and confirm eligibility before any submission.
5. Only after a candidate passes the holdout gate and the complete registry scan may a file be made downloadable. A separate weekly-slot selection is then required.
