> **Historical parallel-session review.** Retained for provenance. Current status, experiment count and evidence are in [README](../README.md) and [the current run card](../evidence/run_card.json); this document is not a current release authorization.

# Executive summary & submission guide

## STOP — no approved TIFF is available

**Do not upload an input raster, old reference TIFF, JSON report, HTML page or PDF.**
This session generated **no new submission TIFF** and consumed no competition
submission slot. The status is **NEGATIVE**, not “ready,” “unscored primary,” or
“format valid therefore safe.”

The protocol's literal uniqueness gate cannot be satisfied by a nonempty
in-footprint raster: a verified registry member predicts positive values at
every footprint cell. Every candidate point is at distance zero from that
member, so its forward overlap is universal. The required method-lane paragraph
is also missing. These are blocking conditions, not excuses to copy a prior file.

See [the audit](../evidence/preflight.json), [run card](../evidence/run_card.json)
and [review](review.md). A downloadable scientific artifact is intentionally
absent; the downloadable evidence is a negative result, **not a submission**.

## How a future valid submission must be made

These are instructions for a future **selector-approved** artifact. They are
not permission to upload anything in the current repository.

1. **Resolve gates first.** Supply the method lane and resolve the registry
   definition conflict explicitly. Confirm the current competition rules and
   any remaining weekly allowance in the authenticated submission page.
2. **Prove scientific merit.** Use a visible-only buffered whole-segment
   hide-and-recover holdout; run every feature-alone leakage canary; beat a
   rebuilt current best under the same pooled evaluator, with withheld counts
   and a paired physical-block confidence interval. A projection is not a score.
3. **Prove distinctness in order.** Compare the pre-placement surface to the
   registry; duplicate means stop before placement. Only if it passes, place
   dots and test the final dots. Log inaccessible registry entries as incomplete,
   never as unique. Do not exempt dense rasters without an explicit protocol revision.
4. **Package a normalized prediction through the shared writer.** It must be
   single-band float32, values in `[0,1]`, the template's CRS, shape and transform.
   There must be no NaN inside the footprint. The local all-finite export is
   conservative about range but its zero-outside convention is not verified
   organizer acceptance; reconcile it with the official null/NaN guidance first.
5. **Reopen and verify exact bytes.** Run
   `python scripts/validate_submission.py path/to/new-candidate.tif --out evidence/validation.json`.
   Record the artifact SHA-256 and bind scientific, uniqueness and validator
   evidence to the same method and bytes. A local format PASS does not promote it.
6. **Separate selector decision.** The selector, not this parallel lane, decides
   whether this artifact should use an available weekly slot. No auto-upload
   implementation is present. Do not treat a reserved filename as an artifact.
7. **Download the actual TIFF** from a future enabled artifact link. A ZIP, if
   used, must contain only that one TIFF; no README, reports or extra rasters.
   Compare its SHA-256 with the adjacent receipt.
8. In DrivenData, open competition 306 → **Submit** → **New submission**. Choose
   the exact `.tif` (or single-TIFF `.zip` if currently permitted by the form).
   Paste its unique submission name where the platform permits, and its
   adjacent note of at most 140 characters into **Note (optional)**. Review the
   displayed remaining weekly quota before uploading.
9. After processing, save the submission-page receipt, submission ID, displayed
   metric, timestamp and exact SHA-256. Only that binding warrants the label
   **ORGANIZER-CONFIRMED** for the artifact. Public team leaderboard rows alone
   cannot prove a named file's score. Save any rejection verbatim and retain
   the exact rejected bytes for diagnosis.
10. Before the contest deadline, select only one final submission for both
    rounds, subject to the current official rules. Retain reproducible code,
    data provenance, license attribution and generative-AI-use disclosure.

## Why the previous range error is not diagnosed here

`Predicted values must be in range [0, 1]` is consistent with an invalid numeric
value, including a negative missing-data sentinel, but the rejected file is not
available. It does **not** prove that NaN nodata caused the error. The official
format text itself mentions null/NaN outside the bounds. Our shared writer
rejects nonfinite/out-of-range arrays without silently clipping or replacing
values, and independently reopens the written output. This prevents several
local errors but does not promise portal acceptance.

## Published rules and manual-review links

- [Official problem, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition home](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Rules landing page](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
- [September 2026 official rules PDF, sections 3.1–3.6](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Public leaderboard — not a file-specific receipt](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

The published PDF describes three submissions per week; this project's separate
scientific experiment budget is also three experiments or two hours. They are
different limits. We did not access the account's current remaining quota.

---

## P8 Multi-Agent Synthesis Update (`arena/6db3f66c-gemsdoe70`)

- **All-Time #1 Candidate across all 13 GEMSDOE70 lanes:** `docs/downloads/gems70-p5-submodular-multiphysics-hydro-54000-20261020.tif` (`173,097` bytes, SHA-256 `00e8e1cb6ea34dbe2f6dc0ba3b7cc0d8d18ae2b0aaec11552bfa3ef11f1ea9f2`).
- **Two Separate Decision Flags:**
  1. `download_ok = true` (15/15 shared validator checks pass; `float32`, single band, `EPSG:32611`, `3730 × 3292`, `100 m`, exact `{0.0, 1.0}`, zero NaNs, zero mapped-fault leakage, 74/74 leakage canaries clean with `max(AUC, 1-AUC) = 0.6066 <= 0.90`).
  2. `holdout_and_proxy_gates_passed = true` (**Instrument A `HOLDOUT-DTI = 0.1090 [0.0929, 0.1249]`** — #1 across all 13 lanes, beating `D28` `+0.0170 [+0.0063, +0.0278]`, `Phase 4` `+0.0359`, and `H33` `+0.1053`; **Instrument B′ `OOF-PROXY-DTI = 0.1681 [0.1437, 0.1916]`** — #1 across all 13 lanes, beating `H33` `+0.0743 [+0.0522, +0.0954]` / `+79.3%`, `P6` `0.1440`, `P7` `0.1138`, and `E6` `0.1100`).
  3. `weekly_slots_used = 0` (`submit_recommended = false` automatically under the un-amended literal forward-overlap rule against dense 206,895-dot lattice `calib_r13lattice_00904.tif`; unique across all **78** rasters — 62 archive + 16 sibling TIFFs — under mutual overlap `<= 0.4609` and forward overlap `<= 0.4063` against all 16 sibling TIFFs).
