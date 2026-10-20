# GEMSDOE70 — geothermal fault research

## NEW P5-COVER FILE: **DOWNLOAD FOR RESEARCH; DO NOT SUBMIT**

A newly generated, format-validated **continuous** GeoTIFF is available:
[Download P5 TIFF — DO NOT SUBMIT](docs/downloads/gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT.tif) ·
[One-TIFF ZIP for review](docs/downloads/gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT.zip) ·
[P5 evidence page](docs/p5.html) · [P5 run card](evidence/p5/run_card.json).
SHA-256 `30a52f9af75af5e9241e0928cc941a71189cf2e3301d2320460ff70d230c396a`. Name `gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT`;
note (120/140): `P5 magnetic width and cover, SGMC LOQO proxy; continuous review map. Literal dot overlap blocks promotion; DO NOT SUBMIT` (**not an upload instruction**).

**Download for review: yes. Contest upload / weekly slot: NO.**
HOLDOUT-DTI A (`gems57-pooled-hide-v2`, 11,321 withheld
catalogue pixels) = 0.0123 [0.007525362402102077, 0.017652899299874254]; paired vs regenerated visible-only P4
Δ -0.0608 [-0.06869402290922029, -0.05215269960053514]. SGMC proxy HOLDOUT-DTI B′
(`gems57-pooled-hide-v2`, 59,937 proxy positives)
= 0.0254 [0.018528422238356795, 0.033629285104751244]; paired vs frozen H33 Δ -0.0683
[-0.08194331910889527, -0.05446790963256574]. Both 95% intervals for improvement are below zero; these are **not**
organizer-confirmed scores. Leakage canaries clear (all features below AUC 0.90).
The new continuous surface has ~26,987
summed probability mass versus 37,654 full-mass H33/P4 dots; this is a **joint test** of
ranking, proxy training and emission, not an isolated causal feature comparison.

The literal 3-px **forward** overlap gate blocks any proposed dot placement in the
4,989,581-pixel feature-valid interior: a hash-pinned archived lattice covers every
cell of that domain. The continuous P5 map has no exact-one binary dots, but its
**positive support has 1.00 forward overlap** with the same lattice; that is not a
loophole or a protocol-unique submission. Distinct bytes/low rank correlation
(ρ ≤ 0.0232 vs
70 checked rasters) do not
clear the other gate. No weekly slot was used; no organizer submission receipt exists.

- [Executive summary / exact future submission workflow](docs/executive-summary.html)
- [Four ranked preregistered hypotheses](docs/preregistration-p5.md) ·
  [Official-source claim/limit table](evidence/p5/official_source_review.json)
- [H33 analysis](docs/h33-analysis.md) ·
  [Literal overlap witness](evidence/p5/literal_blocker.json)
- **Session start:** read this README, the complete retained brief below, AGENTS.md and HANDOFF.md.

### Reproduce or verify P5 (CPU; no slot, no automatic promotion)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py
# owner archive provides the pinned SGMC proxy + 62 registry rasters:
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/verify_p5_artifact.py   # re-check unchanged TIFF without refitting
# Run scripts/run_experiment_p5_cover.py only on a clean checkout; writer refuses to overwrite.
.venv/bin/python -m pytest -q
```

Input mirrors are SHA-pinned owner copies, **not** organizer-authenticated; the competition
data page requires a login. USGS magnetic edges can also represent dikes, remanence changes
or survey artifacts, not fault/vent proof. The reported H33 0.2778 has no authenticated
file-specific receipt here. Public-leaderboard 0.4413 was read on 2026-10-20,
not copied from a P5 submission. See [official problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
[DOE rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

## PRIOR REVIEW (8 archived dot files): DO NOT SUBMIT — literal lane stop

**Download: yes, 8 older archived TIFFs for review only. Submit: NO.**
That *prior* review generated no new protocol-compliant TIFF, geological experiment or slot.
P5 above is a later, separate research-only negative, not a promoted competition submission.
The frozen prior-review negative run card is [here](evidence/review/run_card.json).

- [Evidence site](https://buffedlizard55-lab.github.io/GEMSDOE70/)
- [Executive summary / exact submission workflow](docs/executive-summary.html)
- [Download archived P4 TIFF — DO NOT SUBMIT](docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif)
- [Fresh literal-protocol audit](evidence/review/literal_protocol_audit.json)
- [Four ranked hypotheses / source table / limitations](docs/protocol-review.md)
- [H33 analysis — measured geometry, not a verified leaderboard explanation](docs/h33-analysis.md)
- [Handoff](HANDOFF.md)
- **Session start:** read this README, the complete retained brief below, AGENTS.md and HANDOFF.md.

## What this review verified

The previous mutual-overlap gate weakened the prompt's **forward**-overlap rule without approval.
Current policy applies the literal rule to shared-tool measurements; it does not change the
metric, writer or frozen historical evidence. The 8 historically reviewed dot TIFFs have measured forward
overlap **1.0** against the pinned binary lattice, exceeding **0.70**. They are duplicates under
the prompt's rule, even though their bytes differ. Small rank correlation does not cancel overlap.

Fresh REGISTRY-MEASUREMENT: halo coverage **99.871327268%**,
not the previously asserted 100%. There are **6,649 uncovered footprint cells**. At the prior
handoff's fixed **37,654-dot mass**, even the minimum possible overlap is
**0.823418495**, still a stop. This does not prove
impossibility at every smaller mass. We did not optimize a boundary-only loophole.

All 8 reviewed dot TIFFs pass shared local format checks (single-band float32, finite [0,1],
CRS/shape/transform matching the pinned sample); that is not portal acceptance or uniqueness.
The previous canonical P4 card and historical receipts remain frozen and superseded for current
policy by `evidence/review/run_card.json`.

## Scientific outcome and next session

At the time of that prior review, no new HOLDOUT-DTI or ORGANIZER-CONFIRMED score existed;
P5 HOLDOUT-DTI is newly measured above. The historical P4 HOLDOUT-DTI is 0.07304 [0.06674, 0.07899], evaluator `gems57-pooled-hide-v2`, 11,321 withheld
catalogue positives. Its SGMC proxy gate was already negative. H33's reported 0.2778 and the
conflicting leader values in the brief lack authenticated submission-page receipts here.

The prior handoff's supervised within-halo ranking was deferred in this archived review;
the new P5 test above executed one narrow magnetic-cover version and measured a negative.
Four earlier ranked hypotheses and their non-fault mimics are in the historical review.
Resolve the literal-gate conflict by a
separately authorized protocol, then validate one candidate using nested spatial splits, canaries,
a matched current-best baseline and the shared evaluator/writer. Do not silently reintroduce a
mutual-overlap exemption, and do not spend a weekly slot before an independent selector decision.

## Reproduce this review (CPU; does not generate a TIFF)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/review_literal_protocol.py --fetch
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/audit_pages.py
```

The witness fetch uses the configured GitHub connection and immutable revision/SHA pins. It lands
in ignored `.cache/`, not Git. Data bridge files already in the repo supply the reference geometry.
Official reference README/notebook were re-fetched via GitHub API. Other official hosts and the
authenticated submission page were not accessible within this session's outbound allowlist; live
cap, eligibility and organizer acceptance remain unverified. GPU is preferred, not required by the
organizer reference. `scripts/prepare_data.py` advertised in the historical prompt is absent.


## E5 lane — supervised within-halo ranking (2026-10-20), verdict `negative` — DO NOT SUBMIT

SGMC-proxy LOQO ranker (the previously deferred next step, now executed under its own preregistration `docs/preregistration-e5.md`), 37,654 dots: A HOLDOUT-DTI 0.0815 vs H33 0.0037; B′ PROXY-DTI 0.0886 vs H33 0.0938 (Δ -0.0051 [-0.0161, +0.0053] — includes zero) → negative. File `docs/downloads/gems70-e5-supervised-loqo-37654-20261020.tif` (sha256 `8b7d67e9c2b0ddb4562b70d5726f76dd4ef84b4b1842bdffc98d017575b97bd2`), review-only under the literal policy above (forward overlap 1.00 vs the dense lattice; mutual 0.308). Evidence: `evidence/e5/`. Public leader at organizer-page read 2026-10-20: 0.4413 (`evidence/e5/leaderboard_read.json`). No weekly slot used.


## Parallel P5 analytic-signal lane (arena/97660a79-gemsdoe70) — DO NOT SUBMIT

Analytic-signal halo 7px, 37,654 dots, `tmi_hg`+`tmi_vg` rank in 2.4–32 px halo with tip kernel. HOLDOUT-DTI A 0.0828 [0.0755,0.0895] vs H33 0.0037 win; **B′ 0.0766 [0.0687,0.0852] vs 0.0938 H33 win Δ -0.0172 [-0.027760492095023067, -0.006296864003715159] → negative**, no slot. Uniqueness: 62 rasters worst mutual 0.30 (limit 0.70) worst ρ 0.042; forward 1.00 vs dense lattice `calib_r13lattice_00904.tif` (literal duplicate, review only). File `docs/downloads/gems70-p5-analytic-halo-37654-20261020.tif` (sha256 `aa3799b2a341a6a5c1a37527e7002c6b22c27d7ea57eb23ab97772926b8f33d4`, 149,414 bytes, ZIP `bf61cacc...`). Evidence `evidence/phase5/` (run_card, instrument holds, uniqueness, canaries), method `src/gems70/method_p5.py`. Hypotheses.md now ranks 5 candidates (H-2 tested P5, H-3 radiometric GeoDAWN already fetched 36+26 MB, H-4 lidar scarp 36 MB, H-5 conductive breach, H-6 basement curvature) with preregistered validation rule; h33-analysis.md PhD-level byte audit + metric algebra. Under literal forward rule, P5 is duplicate (as is H70 and P4) — download for review only.
## Complete retained project prompt

Historical statements below are user-supplied requirements and claims, not verified results.
PROJECT_BRIEF.md is preserved verbatim and embedded in full. The current prompt's substantive
requirements are retained there; the current active branch is recorded in HANDOFF.md.

<details>
<summary>Read the complete supplied project brief before every session</summary>

# User project prompt — retained as supplied

Read this at the beginning of every session. Scores and access statements below are user-supplied claims, not current verified facts. Execution status and verified evidence belong in README.md and evidence/, not by silently rewriting this historical brief.

---

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.3774

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE26/](https://buffedlizard55-lab.github.io/GEMSDOE26/)

dilcond-oof-v1-20261003-47629f496133-nan: 0.1223

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

[https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html)

h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778

....

[https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html)

h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

[https://buffedlizard55-lab.github.io/GEMSDOE37/](https://buffedlizard55-lab.github.io/GEMSDOE37/)

h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193

....

[https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html)

D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763

....

[https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html)

xscale-worm-persistence-20261006T000541Z-nan: 0.0581

....

[https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html)

sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424

....

[https://buffedlizard55-lab.github.io/GEMSDOE45/](https://buffedlizard55-lab.github.io/GEMSDOE45/)

h51-km-faultzone-20261006-zeros: 0.0106

....

[https://buffedlizard55-lab.github.io/GEMSDOE49/](https://buffedlizard55-lab.github.io/GEMSDOE49/)

gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

....

[https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html)

efd28-repro-20261003-1cc7dc534d51-nan: 0.2600

repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041

sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512

wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560

wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532

xfit-c0-habitat-20261003-ca879db0089a-zeros:0.0439

xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros: 0.0356

....

[https://buffedlizard55-lab.github.io/GEMSDOE46/](https://buffedlizard55-lab.github.io/GEMSDOE46/)

r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589

r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843

....

[https://buffedlizard55-lab.github.io/GEMSDOE39/](https://buffedlizard55-lab.github.io/GEMSDOE39/)

h40-e-disc-h40e-30k-zeros: 0.0339

....

[https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html)

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: 0.0397

h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: 0.0984

....

[https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html)

h42-submission-primary: 0.0245

....

[https://buffedlizard55-lab.github.io/GEMSDOE44/docs/](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/)

h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715

....

[https://buffedlizard55-lab.github.io/GEMSDOE47/](https://buffedlizard55-lab.github.io/GEMSDOE47/)

h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430

....

[https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html)

h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296

....

[https://buffedlizard55-lab.github.io/GEMSDOE50/](https://buffedlizard55-lab.github.io/GEMSDOE50/)

h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite: 0.0764

....

[https://buffedlizard55-lab.github.io/GEMSDOE51/](https://buffedlizard55-lab.github.io/GEMSDOE51/)

h53-twostage-20261008T040951Z-9a0b32c871: 0.1047

....

[https://buffedlizard55-lab.github.io/GEMSDOE52/](https://buffedlizard55-lab.github.io/GEMSDOE52/)

h97b-candidate: 0.0856

....

[https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html)

h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros: 0.0159

....

[https://buffedlizard55-lab.github.io/GEMSDOE54/docs/](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/)

h54c-manifest-edge-20261009T025732Z-73454bc5:0.0449

....

[https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html)

tensor_full-n16000-sep3-20261009T211747Z-nan: 0.0290

....

[https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html)

h56-final-dotted-ridge-d2p8-20261009T190421Z:0.0658

....

[https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html)

h57r-joint-strata-38000-20261010T214547Z-00cf5b2066f1-zeros: 0.0254

....

[https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html)

ml-binary-ridge-20261012T000000Z: 0.0180

....

[https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html)

h59j-coherence-consensus-dotted-20261011T043000Z: 0.0499

....

[https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html)

h73-chi-coherent-corridor-12000-20261011T195818Z-zeros: 0.0351

....

[https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html)

h61a-basement-step-20000dots-20261011T012029Z-eb2ae4bb024b-zeros: 0.0009

h61o-vardepth-none-40000dots-20261011T160711Z-28d4fac611ea-zeros-zeros:0.0751

....

[https://buffedlizard55-lab.github.io/62GEMSDOE/](https://buffedlizard55-lab.github.io/62GEMSDOE/)

datum-lahontan-strain-gauge-defensible-440dots-zeros: 0.0000

....

[https://buffedlizard55-lab.github.io/GEMSDOE63/](https://buffedlizard55-lab.github.io/GEMSDOE63/)

cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros: 0.2303

....

[https://buffedlizard55-lab.github.io/GEMSDOE64/](https://buffedlizard55-lab.github.io/GEMSDOE64/)

h64-lidar-scarp-cv-20261011T220000Z:0.0383

....

[https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html)

sar-em-propensity-half-20261011T223500Z-5e4660cd-zeros:0.0431

....

[https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html)

gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros:0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE67/](https://buffedlizard55-lab.github.io/GEMSDOE67/)

h67a-orientip-lane-29447dots-20261012T021226Z-allfinite:0.0356

ovtr-ml-cover-tau3p0-20261012-nan:

....

[https://buffedlizard55-lab.github.io/GEMSDOE68/](https://buffedlizard55-lab.github.io/GEMSDOE68/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE69/](https://buffedlizard55-lab.github.io/GEMSDOE69/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE70/](https://buffedlizard55-lab.github.io/GEMSDOE70/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE71/](https://buffedlizard55-lab.github.io/GEMSDOE71/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE72/](https://buffedlizard55-lab.github.io/GEMSDOE72/)

:

....

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See below for more links and information related to the competition:

[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)

[https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

[https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)

[https://epsg.io/32611](https://epsg.io/32611)

[https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.

Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (verified redirect to login)

See below for links from the above site.  See attached files for links from the above site.

[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (requires login) to data/

See links below for competition data:

[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)

[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)

[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)

[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)

[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.

</details>
