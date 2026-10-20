# P5 scientific review and three-pass verification — 2026-10-20

**Outcome:** new GeoTIFF produced, format-valid and byte-distinct, **DO NOT SUBMIT**.
The result is a measured negative on both frozen instruments, not a forecast of a contest score.
The new file is a *continuous review surface*, not a protocol-cleared dot submission.
Run card: [`evidence/p5/run_card.json`](../evidence/p5/run_card.json) · [download for review](../docs/downloads/gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT.tif).

## Pass 1 — hypotheses, scientific mechanism, experiment

The four ranked hypotheses, exact feature band numbers, non-fault mimics, novelty scope,
source links and frozen parameters were written **before** any P5 feature scoring in
[`docs/preregistration-p5.md`](../docs/preregistration-p5.md). Its SHA-256 is stored in the
experiment manifest and card; the frozen file was not changed after the run. Because no
single lane paragraph was supplied, P5 explicitly declared a **provisional** one-lane
magnetic-width mechanism. No other candidate was run; zero weekly slots used.

The target is an *unmapped fault trace*, not a geothermal vent. The
[organizer problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
explicitly distinguishes expert-mapped new faults from the existing public faults. In covered
basins, a fault may juxtapose magnetized bedrock units without a strong surface scarp. The
magnetic analytic-signal amplitude `sqrt(HG² + VG²)` can localize contacts, and its scale-width
ratio may indicate depth/cover differences. Gravity gradient and modelled basement depth provide
context. But this is **not a fault detector by itself**: [USGS OFR 02-98](https://pubs.usgs.gov/of/2002/0098/intro.htm)
warns that contact interpretation depends on assumptions and vertical derivatives amplify noise;
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
warns of variable flight height/specifications. A dike, lithologic contact, magnetic remanence
change, or survey-line artifact is a named null explanation. No predicted pixel proves heat,
permeability or geothermal production.

The P5 model trained *only* on SGMC-mapped faults outside the competition catalogue as a
proxy response, with leave-one-quadrant-out (LOQO) fitting. No SGMC labels entered predictor
columns or the final export mask. Every catalogue-derived feature (visible distance) came from
the globally visible catalogue after whole-component withholding and a 3 px feature collar.
The shared evaluator masked visible faults pixel-exactly. This avoids a simple label leak,
**not** a distribution shift between a state-map compilation and the competition's expert truth.

| Instrument (not a leaderboard score) | P5 | Fixed comparison | Paired difference with 95% CI |
|---|---:|---:|---:|
| Catalogue HOLDOUT-DTI (`gems57-pooled-hide-v2`, 11,321 withheld positives) | 0.012262 [0.007525, 0.017653] | visible-only P4 0.073042 | −0.060780 [−0.068694, −0.052153] |
| **SGMC-proxy** HOLDOUT-DTI (`gems57-pooled-hide-v2`, 59,937 proxy positives) | 0.025424 [0.018528, 0.033629] | archived H33 0.093771 | −0.068347 [−0.081943, −0.054468] |

Both compare pooled DTI terms at α=.2, β=.8, 300 m triangular kernel; paired 20 km spatial-cluster
bootstrap, 1,000 draws, seed 70501. Conditional intervals are *not* public-test intervals.
The P4 A comparator was regenerated from visible-only faults; its fold TP/FP/FN matched its
saved phase-4 receipt exactly. H33 is **not** used as a fair A comparator because it was
built from the full catalogue. `evidence/p5/instrument_*.json` and `folds_*.json` preserve
all terms.

Canaries tested four raw bands and seven derived/cat-distance fields individually:
AUC and inverse AUC range 0.249–0.751; no >0.90 leakage alarm. Most geology-alone
AUCs are near 0.5. This does not prove independence of the truth-generating process.

## Why the new method lost, and what we cannot infer

The observed P5 TIFF has **54,512 positive pixels but only ~26,987 total probability
mass** (continuous mean positive confidence 0.495), versus 37,654 full-mass binary P4/H33
dots. P5 ranks the upper 2% of its own allowed domain, with exact-tie averaging, rather
than sparse coverage-aware 7×7 stratification. Under the official asymmetric DTI formula,
recall credit `TP_w` saturates per truth pixel while predicted mass and false-positive credit
are accumulated per prediction cell. Strong clustering and low mass can simultaneously
leave large parts of truth uncovered and still pay false-positive mass. On the A instrument
P5 yielded TP_w ≈174 versus P4 ≈1,208; on B′ P5 ≈1,344 versus H33 ≈5,213.
This is a **joint test of geophysical ranking, supervised proxy fit, and continuous emission**;
it does **not** isolate whether the magnetic feature, model family, or emission choice caused
the shortfall. It does falsify this *preregistered end-to-end candidate* and is too weak to
justify a leaderboard slot.

The measured H33 file is a subset of H27, itself a subset of D28; it deletes near-catalogue
shells, leaving sparse fault-halo coverage (`evidence/h33_audit.json`). Sparse spreading plus
removal of low-value near-catalogue mass is consistent with the asymmetric metric; it does
not prove why the hidden test rewarded the historical user-reported 0.2778. There is no
file-specific authenticated DrivenData receipt tying that score to bytes. We cannot claim P5
exceeds it or predict a private/public score. A public-leaderboard page read on this date
showed best 0.4413, **a leaderboard snapshot**, not an organizer-confirmed P5 score.

## Pass 2 — literal registry conflict and immutable-byte checks

The prior review found that the inherited shared uniqueness tool silently changed the
user's forward overlap rule into **mutual** overlap. P5 did not treat mutual overlap as a
waiver. A SHA-verified 206,895-dot archived lattice covers 5,160,724 / 5,167,373 footprint
pixels within 3 px, leaving 6,649 boundary pixels; after the registered 12 px feature
erosion it covers **every** one of 4,989,581 valid pixels. Thus any binary dot placed in
that valid interior has 100% forward overlap and must stop before placement. P5 placed
**no final binary dots**. The new continuous field's positive support itself has
**1.00 forward overlap** with that lattice if positive pixels count as dots. The shared
binary-dot checker counts zero exact-one dots; using that observation to claim
`<70%` would be a definitional loophole and is explicitly rejected. Worst full-footprint
Spearman among 68 locally accessible archived/prior TIFFs is 0.023162; a low rho does
not undo the positive-support stop. These 68 are not an exhaustive organizer registry.

The shared `submission_writer.py` wrote a new TIFF/one-TIFF ZIP into distinct paths and
refused all invalid arrays. We independently reopened the bytes and verified:

| Property | Reopened result |
|---|---|
| SHA-256 | `30a52f9af75af5e9241e0928cc941a71189cf2e3301d2320460ff70d230c396a` |
| Band / type | 1 / float32 |
| CRS / shape / transform | EPSG:32611 / 3730×3292 / `(100,0,243350,0,-100,4508550)`; match pinned sample |
| Global range / finiteness | [0, 0.98998183], all finite, 0 NaN in footprint |
| Known faults / outside footprint | zero mass on both |
| ZIP | exactly the TIFF entry; bytes match TIFF |
| Verdict | **negative; download for research only, submit NO** |

Distinct bytes and an all-true local validator are **not** organizer acceptance. The
[organizer page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
requests null/NaN outside bounds, whereas the owner sample contains 60,988 already-positive
pixels and earlier portal range errors prompted the project's all-finite-zero-outside
convention. This conflict remains unresolved without a real authenticated portal receipt;
no claim of accepted submission is made.

After a separate parallel merge to `main`, the old 66-raster scan was recomputed against
68 accessible rasters **without retraining, changing scores, or changing TIFF bytes**.
The metadata-only correction of a misleading registry URL and the training-region count is
recorded in `evidence/p5/reporting_amendment.json`; original scan preserved.

## Pass 3 — publication, source review, next work

The Pages landing page and executive summary now lead with the new file and two independent
flags: **review download yes, competition submit no**. The hash-pinned inventory and root
Pages build policy permit only registered TIFF/ZIP bytes; other data and quarantined prior
files remain excluded. Fresh tests exercise source hashes, grid/range, saved pooled terms,
negative deltas, canaries, literal blocker, ZIP round-trip and tamper fail-closed release.
The earlier archive protocol review is frozen within its own time/scope; P5-cover has
its own run card. The static site has a dedicated evidence page and direct TIFF/ZIP links.

Official text sources with exact claims/limits were read and stored in
`evidence/p5/official_source_review.json`: [DrivenData problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/),
[DOE/NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf),
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
[USGS SGMC](https://www.usgs.gov/data/state-geologic-map-compilation-sgmc-geodatabase-conterminous-united-states),
[USGS magnetic interpretation](https://pubs.usgs.gov/of/2002/0098/intro.htm),
[DOE GDR](https://gdr.openei.org/submissions/1391). The organizer data page redirected
to login; GitHub owner mirrors are hash-verified but not official-origin-authenticated.

**Highest-value next steps, gated:**
1. Obtain an explicit assigned lane and a written decision on the contradictory forward-
   overlap requirement. Never silently substitute mutual overlap. A smaller mass could
   mathematically place some dots in the 6,649 uncovered boundary cells, but that
   boundary-only loophole is geologically unjustified and not a prize strategy.
2. If a legitimate new lane is permitted, test geometry-preserving **within-halo
   geological re-ranking** rather than replacing sparse emission; match P4/H33's
   *probability mass, dot budget and spacing* on the **same** blocked holdout and include
   a truly untouched outer split. Treat SGMC as a weak proxy; investigate independent
   fault traces and origin/rights before importing additional labels.
3. Obtain organizer-authenticated data and a submission-page receipt for any candidate
   cleared by the selector; verify the live weekly balance (rules allow up to three/week),
   do not invent acceptance or private-test score. No automated upload in this repo.
4. Resolve the official outside-bounds null/NaN instruction vs the observed all-finite-zero
   output/portal range behavior by validating on an actual portal receipt **after** a
   scientifically justified, protocol-cleared file exists. Do not burn a slot on formatting
   alone. The site should keep a timestamped source check separate from live score claims.
