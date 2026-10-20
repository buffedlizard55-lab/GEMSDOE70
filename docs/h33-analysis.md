# H33: measured geometry, plausible metric benefit, unproven causation

**The reported leaderboard value 0.2778 is user-supplied, not ORGANIZER-CONFIRMED.**
There is no authenticated submission-page receipt for it in this repository. Conflicting leader
values in the retained brief cannot establish the current leader or predict a new score.

## What the archived bytes show

The historical byte audit (`evidence/h33_audit.json`, linked below) reports:

| Archived raster | Binary dots | Relationship |
|---|---:|---|
| D28 | 44,090 | sparse off-catalogue field |
| H27 | 40,199 | D28 with 3,891 dots at 1 pixel from the catalogue removed; no additions |
| H33 B2 | 37,654 | H27 with 2,545 dots at sqrt(2) or 2 pixels removed; no additions |

H33's median catalogue distance is 1,964.69m; 5.77% of its dots lie within 300m of a mapped
trace. This establishes a sparse halo-sampling geometry and exact subset relationships. It does
**not** establish how much of the reported score comes from geometry, geological information or
properties of hidden labels. Calling H33 a newly learned fault detector is unsupported; calling it
necessarily geology-free is also stronger than the lineage audit alone proves.

## Why the geometry could help

For the shared local DTI implementation,
`DTI = T / (T + 0.2*(S-M) + 0.8*(N-T))`.
Here `T` sums distance-weighted truth coverage, `S` is emitted mass, `M` is nearest-truth credit
at prediction cells, and `N` is truth count. The 300m triangular kernel makes concentrated,
redundant predictions potentially less efficient than well-spaced coverage. Deleting dots that
obtain little hidden-truth credit can reduce false-positive cost. These are plausible explanations
for the user-reported changes, **not a controlled causal explanation of the organizer score**.
Sparse spacing alone does not guarantee improvement: dropping a useful dot can reduce recall.

## What the local comparison actually says

Historical **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`, 11,321 withheld catalogue positives:
P4 0.07304, 95% CI [0.06674, 0.07899], versus H33 0.00370, CI [0.00304, 0.00450].
This measures recovery of hidden catalogue segments, not the organizer's newly mapped faults.
A large win here does not imply a leaderboard win.

The separate historical **SGMC PROXY-DTI** B′ comparison uses 59,937 proxy-positive pixels at
least 3 pixels from the catalogue: P4 0.08116, CI [0.07235, 0.09002], versus H33 0.09377,
CI [0.08375, 0.10403]. Paired delta −0.01261, CI [−0.02407, −0.00180]. This proxy is not a
catalogue holdout or an organizer score. Nearby SGMC/QFaults traces can be re-digitizations;
removing a narrow band does not establish independence.

## Can a new method beat the reported 0.2778?

Possibly, but no current result demonstrates it. The deferred supervised residual-ranking lane
could contribute new information beyond emission geometry. It needs nested spatial validation,
feature-alone canaries, a matched current-best baseline, and the literal uniqueness gates first.
The fresh review found that all published TIFFs fail the current prompt's forward-overlap gate;
no new TIFF was generated after that stop. We will not prune, rename or jitter H33 to call it unique.

- [Historical H33 byte audit](downloads/h33_audit.json)
- [Historical HOLDOUT-DTI receipt, including evaluator/count/CI](downloads/instrumentA_holdout.json)
- [Historical B′ proxy receipt](downloads/instrumentB_prime.json)
- [Current literal-protocol audit and proposed research](protocol-review.html)
- [Organizer fault-detection reference](https://github.com/drivendataorg/gems-prize-reference-solution)

## Session 3 addendum — calibration against the live board (see `docs/s3-findings.md`)

Evidence class: owner/user-reported live scores for 18 archived rasters, re-scored offline here
(`evidence/s3/proxy_calibration.json`, `evidence/s3/terrain_marginals.json`). None is
organizer-confirmed.

* **Neither offline instrument predicts the live ordering.** Spearman(live, B′) = −0.28 and
  Spearman(live, A) = −0.64 (n = 18). The dense lattice `r13` has the best B′ (0.252) and the worst
  live score (0.0904): B′'s proxy truth is large (≈ 60 k px), so it rewards dense coverage that the
  live truth punishes.
* **What the live board did reward, descriptively.** Among ≈ 37–44 k-dot files, the reported live
  score rose as dots within ≈ 2 px of mapped faults were removed (share of dots within 6 px:
  D28 0.300 → H27 0.232 → H33 0.181; scores 0.2600 → 0.2708 → 0.2778). The one file that
  concentrated dots in steep terrain (GEMSDOE49 gate_ortho, 47.5 % in the steepest slope quartile
  versus H33's 19.9 %) scored 0.2376 despite the highest B′ in its size class.
* **Answer to "why H33 is the family best".** It is the best-spaced (2.83 px minimum), terrain-
  neutral sample of the 0.3–8 km band around mapped faults with the nearest shells removed. It
  carries no physical information; its edge over its siblings is emission geometry.
* **Can we beat 0.2778?** Not with evidence available today. Our supervised model concentrates in
  bedrock terrain (the named mimic) and, once terrain and distance are matched to H33, adds no
  significant information on the proxy (E2). Beating H33 needs an instrument that tracks the live
  board first — that is the next session's top task.

## P6 dual-horizon LOQO scarp–rad–basement & SGMC buffer diagnosis (`evidence/p6_dualhorizon/`)

In parallel lane P6 (`arena/c6a19d32-gemsdoe70`, `docs/downloads/gems70-p5-dualhorizon-37654-20261020.tif`), we tested whether expanding the horizon beyond `d_cat <= 32 px` (since `35.9%` of `SGMC B′` pixels and `34.0%` of H33's dots lie at `d_cat > 32 px`) and ranking pixels within `7×7` or `5×5` strata using 10 m 3DEP breaklines + 1 m LiDAR scarps + GeoDAWN radiometric ratios could beat H33 on `Instrument B′`:
- **Exp 5.1 (`H-P5-1`, LOQO supervised `7×7`, `5.0 px` NMS):** `A = 0.0775` `[0.0695, 0.0848]`, `B′ = 0.1250` `[0.1211, 0.1288]` (+33.3% over H33 `0.0938`).
- **Exp 5.2 (`H-P5-2`, unsupervised 10m-3DEP breakline + LiDAR scarp + rad `7×7`, `5.0 px` NMS):** `A = 0.0774` `[0.0698, 0.0849]`, `B′ = 0.1201` `[0.1137, 0.1260]` (+28.1% over H33 with zero SGMC training).
- **Exp 5.3 (`H-P5-3`, submodular dual-horizon `5×5`, `3.2 px` NMS):** `A = 0.0790` `[0.0688, 0.0900]`, `B′ = 0.1440` `[0.1319, 0.1558]` (+53.5% over H33, paired Δ `+0.0502` `[+0.0339, +0.0663]`), `B′′ (d ≥ 6 px) = 0.1234` `[0.1118, 0.1359]` (vs H33 `0.0850`).
- **Why P6 is still held fail-closed (`download_ok = true`, `submit_recommended = false`):** (1) Paired Instrument A gain over P4 (`+0.0059`) has a 95% CI straddling zero (`[-0.0050, +0.0163]`); (2) our `1–20 px` SGMC buffer/slope audit ([receipt](downloads/sgmc_buffer_audit.json)) shows `SGMC B′` sits in steep bedrock ranges (`median slope = 13.42°` vs Quaternary catalogue `5.55°`, where sibling SGMC-promoted submissions `GEMSDOE49 = 0.1304` and `GEMSDOE68 = 0.0680` regressed live); and (3) literal forward overlap against the dense lattice is `1.00` (worst mutual overlap `0.4230 <= 0.70`, worst Spearman `0.0300 <= 0.90`).
