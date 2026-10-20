# GEMSDOE70 — auditable DOE GEMS fault-discovery workbench

> **Submission status: NOT READY. There is no validated submission GeoTIFF in this repository. Do not download or submit a file from this repository as a competition prediction.** No candidate raster was created because this checkout contains no code, cached feature stack, holdout evaluator, writer, registry rasters, or competition sample raster. Creating a synthetic or copied TIFF would be misleading and could fail the competition format or duplicate another team’s work.

## Start here at every session

Read this README first, then read the dated review at [`docs/review-2026-10-20.md`](docs/review-2026-10-20.md). Treat the review's evidence labels and blockers as binding. Do not represent a projection, proxy holdout result, or another repository's claim as an organizer score. Do not spend a competition submission slot unless an independently re-opened, validated, unique raster beats the preregistered holdout incumbent.

## Project brief

Build an auditable, scientifically defensible workflow for detecting geothermal-relevant geological faults absent from the existing USGS / INGENIOUS catalogue in the DOE GEMS Prize GeoDAWN region. The deliverable, once evidence and data permit it, is a unique, single-band GeoTIFF that is easy to identify and download, plus a unique submission name and a short explanatory note. A higher leaderboard score is a goal, not a result to assume.

The official problem description says the target is faults; it also explains that the known-fault catalogue is incomplete, that the hidden test set contains expert-labelled previously unmapped faults, and that predictions are evaluated with distance-weighted Tversky scoring. The metric uses a 300 m triangular distance kernel, alpha 0.2, and beta 0.8. These specifications are linked under [Official sources](#official-sources); use the current competition rules and submission page as the final authority.

### Core values

- **Maximize P(Win):** Treat scarce weekly submission opportunities as experiments. Prioritize preregistered, spatially blocked validation and uncertainty over attractive but unsupported ideas.
- **Own the Outcome:** Own the evidence from source data through raster bytes and submission receipt. Log failures and negative results; never quietly turn them into success claims.

### Required scientific and engineering safeguards

- Work from the repository's shared cached feature stack, holdout evaluator, and submission writer when they are present; fix shared tools rather than creating private forks.
- Hold out whole fault segments with a buffer. Derive catalogue-based features only from visible faults and mask visible faults pixel-exactly. Use the official metric configuration. Run each feature alone as a leakage canary before trusting a combined model.
- Compare any candidate against registry rasters before placement and on the final dots. Stop and record a duplicate if rank correlation exceeds 0.90 or more than 70% of dots fall within 3 pixels of one registry raster. Never claim uniqueness without those checks.
- Report numerical scores only with their evidence class: **HOLDOUT-DTI** (include evaluator version, withheld-positive count, and 95% CI) or **ORGANIZER-CONFIRMED** (copy from the submission-page receipt). A projection is never a score.
- Preserve negative experiments as deliverables. Stop at the stated experiment/time budget and do not pick a submission; final-slot selection is a separate decision.

### Submission readiness gate

A future downloadable file must be derived from the actual competition template/data and independently re-opened from disk. Before the site calls it ready, verify: one GeoTIFF band; float32; EPSG:32611; exactly the sample's dimensions, bounds, transform and resolution; predictions in `[0, 1]`; and the required outside-footprint null/NaN behavior. Specifically check that no nodata sentinel outside `[0, 1]` leaks into cells that the evaluator treats as predictions. Record SHA-256, validator output, unique filename, and a note no longer than 140 characters. The official competition page is the source of truth for submission-format requirements.

**Current gate result: BLOCKED.** No local sample/template exists to compare against, and no raster is available to validate. Therefore this repository intentionally offers no `.tif` download link and no submission name/note to paste into DrivenData.

## Official sources

- [DOE GEMS Prize — problem description, metric, datasets, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DOE GEMS Prize — current public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — official description of airborne magnetic/radiometric survey products and related lidar.
- [Great Basin Center for Geothermal Energy — INGENIOUS](https://gbcge.org/current-projects/ingenious/) — project description and publication/data-release links.
- [Official reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) — linked by the competition page. Its availability was not established from this checkout during this review.

## Current review

See [`docs/review-2026-10-20.md`](docs/review-2026-10-20.md) for the clean-checkout inventory, score/evidence reconciliation, candidate hypotheses, blockers, irregularities, and the required JSON run card. The next useful work is to make the shared template/data available in this branch, then perform the pre-placement duplicate check and leakage-aware holdout; do not fabricate a GeoTIFF to satisfy the download request.
