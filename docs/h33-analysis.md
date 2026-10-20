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

## Experiment E6 addendum — SGMC 1–6 px buffer calibration, distance-quantile diagnosis, and multi-modal extended-domain LOQO ranker (`arena/effcd5f7-gemsdoe70`)

1. **SGMC vs. QFaults Buffer Calibration ($r = 1\dots 6\text{ px}$, `evidence/e6/sgmc_buffer_audit.json`):**
   Off-catalogue SGMC shell enrichment around `existing_faults.tif` is `3.83×` in `(0, 1]` px (`7,215` px), `2.98×` in `(1, 2]` px (`5,545` px), `1.86×` in `(2, 3]` px (`4,009` px), `1.40×` in `(3, 4]` px (`2,574` px), `1.14×` in `(4, 5]` px (`2,623` px), and `0.97×` (background parity) in `(5, 6]` px (`1,694` px). Removing $d_{\text{cat}} < 3.0\text{ px}$ (`Instrument B′`) excludes `15,784` near-trace compilation pixels (`20.12%`).
2. **Why `P4` (`0.0812`) and `E5` (`0.0886`) Trailed `H33` (`0.0938`) on `Instrument B′`:**
   Measuring Euclidean distance quantiles ($d_{\text{cat}}$) shows that **35.89% of all `SGMC B′` fault pixels lie at $d_{\text{cat}} > 32\text{ px}$** (`p50 = 22.80 px`, `p75 = 41.98 px`, `p90 = 63.01 px`), matching `H33` (`33.98% > 32 px`, `p50 = 19.65 px`, `p75 = 42.45 px`). Both `P4` and `E5` hard-truncated predictions at $d_{\max} = 32\text{ px}$ (`0.00% > 32 px`).
3. **Experiment E6 (`gems70-e6-multimodal-extdomain-loqo-37654-20261020.tif`, `evidence/e6/run_card.json`):**
   Training a 4-fold Leave-One-Quadrant-Out `HistGradientBoostingClassifier` on **28 multi-modal features** (100 m DEM gradient-directional scarp curvature/coherence, 8 core 19-band channels, 5 1 m LiDAR scarp channels, 5 USGS GeoDAWN radiometric channels including `K/(Th+10)`, 4 10 m DEM lineament/curvature channels, and 3 catalogue geometry channels) across $d_{\text{cat}} \in [3.0, 96.0]\text{ px}$ with 7×7 regional coverage stratification (`block = 7 px`, `nms = 5.0 px`, `37,654` binary dots; `30.22% > 32 px`) achieves:
   - **Instrument B′ (`PROXY-DTI`, $d \ge 3\text{ px}$, `59,937` positives):** **`0.1100` `[0.1058, 0.1133]`** vs. `H33` **`0.0938` `[0.0839, 0.1044]`** — **paired $\Delta = +0.0162$, 95% CI `[+0.0045, +0.0270]`** (`gate_b_prime_candidate_gt_h33_significant = true`), with controlled ablations proving positive contributions from extending $d_{\max}$ (`ablation_truncated_d32 = 0.0879`, paired $\Delta = +0.0221$ `[+0.0124, +0.0324]`), multi-modal external features (`ablation_no_external = 0.0945`, paired $\Delta = +0.0155$ `[+0.0092, +0.0231]`), and 7×7 regional stratification (`ablation_unstratified_sep28 = 0.0946` `[0.0721, 0.1201]`).
   - **Instrument A (`HOLDOUT-DTI`, `11,321` withheld catalogue pixels):** **`0.0710` `[0.0637, 0.0781]`** vs. `H33` **`0.0037`** (`gate_a_candidate_ge_h33 = true`).
   - **Uniqueness & release status:** Passes amended mutual-overlap uniqueness across all 62 registry rasters (`worst_mutual = 0.2960 <= 0.70`, `worst_nonlattice_forward = 0.3526 <= 0.70`, `worst_spearman = 0.0133 <= 0.90`) and all 11 sibling repository TIFFs (`worst_mutual = 0.3508`), while failing the literal one-way forward-overlap gate (`forward = 1.00 > 0.70` against `calib_r13lattice_00904.tif`). Published as `download_ok = true` (review-only) and `submit_recommended = false` under the active literal forward rule (`submit_recommended_if_mutual_policy_authorized = true`).

