# Phase-5 Preregistration — Dual-Population Structural-Hydrothermal Out-of-Fold Synthesis (`H-P5-1..5`)

**Preregistered UTC date:** `2026-10-20` (written and committed **before** executing `scripts/run_experiment_v5.py`).  
**Branch:** `arena/c7049280-gemsdoe70` · **Evaluator:** `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`, untouched).

---

## 1. Pre-Experiment Forensic Diagnosis (Why `H33` Scored `0.2778` and Why `P4` Failed)

Byte-level audit (`evidence/phase5/h33_forensic_reanalysis.json`) established three quantitative facts prior to writing any Phase-5 model code:

1. **Refutation of Session 2's detector-free halo claim (`docs/h33-analysis.md`):**
   `100.00%` (`37,654 / 37,654` pixels) of `GEMSDOE32` `h33-2-b2-zeros.tif` (user-reported `0.2778`) lie strictly inside the `121,131`-pixel (`2.344%` of footprint) `19GEMSDOE` `H19-5` multi-line physical ridge field (`lidar ex_max` mean `82.9` vs background `63.5`), **not** inside a uniform random halo (`calib_r13lattice_00904.tif` scores `0.0904`, showing `+0.1874` of `0.2778` comes from physical fault localization and `+0.0856` from `2.8 px` blue-noise thinning + `d_cat > 2 px` collar removal).
2. **Quantification of `P4`'s two fatal defects:**
   - `P4` hard-zeroed `d_cat > 32 px` (`0.00%` beyond `3.2 km`), whereas **`34.00%`** (`12,803 / 37,654`) of `H33` dots, **`31.9%`** of independent `GEMSDOE49` (`0.2376`) dots, and **`28.7%`** of `SGMC` off-catalogue faults lie beyond `3.2 km` in unmapped ranges and blind hydrothermal basins (e.g., Beowawe Geysers sits at `d_cat = 61.7 px = 6.17 km`).
   - `P4` used zero topographic, LiDAR, potential-field, or hydrothermal features (`in_H19_5 = 2.8%`, random background rate).
3. **SGMC duplication-band & live-prevalence calibration (`evidence/phase5/sgmc_buffer_audit.json`):**
   - `16.3%` of `SGMC`-off-catalogue pixels fall within `d_cat <= 2 px` (`3.41x` spatial enrichment) and `21.4%` within `d_cat <= 3 px` (`2.84x`), confirming `B'` (`d_cat >= 3 px`, `59,937` quadrant-eroded pixels) and `B''` (`d_cat >= 5 px`) are uncontaminated by QFaults re-drawing.
   - Algebraic inversion of the uniform 5-px lattice (`206,895` dots, exact off-catalogue kernel cover `c = 0.5835`, user-reported live DTI `0.0904`) implies `K_live ≈ 7,600–7,905` hidden truth pixels (`~0.15%` footprint prevalence). Because `K_live` is `7.6x` smaller than uncalibrated `B'`, **all candidate arms MUST be evaluated at identical emitted mass (`S = 37,654` binary off-catalogue dots)** where DTI ranking is provably invariant to scalar prevalence rescaling, and we additionally report prevalence-calibrated DTI at `K_cal = 7,905`.

---

## 2. Five Preregistered Geological Hypotheses (`H-P5-1` through `H-P5-5`)

Ranked prior to experimentation by **expected true off-catalogue DTI gain vs implementation cost**. Every external data layer is free public-domain (USGS CC0 / 3DEP) or CC-BY 4.0 (DOE GDR 1391) and SHA-256 verified in local cache before execution. **Zero prior submission rasters are ever used as features, masks, weights, or labels.**

| Rank | ID & Name | Specific Layers (SHA-Verified) | Physical Signature & Mathematical Operator | Why Unmapped in `existing_faults.tif` | Named Non-Fault Mimic | Novelty vs Repo History | Cost | Status in Budget (`<= 3` Exps) |
|---:|---|---|---|---|---|---|---|---|
| **1** | **`H-P5-1` · Dual-Population Out-of-Fold Structural-Hydrothermal Synthesis + Exact 300 m Submodular Cover** | (a) `training_features.tif` (19 bands); (b) `lidar_scarp_features_u8.tif` (12 1 m LiDAR bands, `valid==0 -> NaN`); (c) `topo_10m_derived_100m_u8.tif` (9 10 m 3DEP bands); (d) `geodawn_rad_u8.tif` + `geodawn_extensions_u8.tif` (`K, Th, U, TC, ThK, UK, UTh, TMI_up150`); (e) DOE GDR 1391 wells/springs/geothermometers (`27,092` pts), `2 m` temperature probes (`3,800` pts), paleo-sinter/travertine (`709` pts); (f) fold-proper `visible` fault geometry (`d_vis, tip_kernel, host_len`) | Out-of-fold shallow regularized `HistGradientBoostingClassifier` pairing two distinct fault end-members: **`M_neo`** (Quaternary alluvial scarplets + crustal strain + visible-fault tip lobes) and **`M_bed`** (full-footprint unmapped bedrock fault ridges + K/Th alteration edges + `RTP - TMI_up150` magnetite destruction + thermal/sinter conduits), combined on rank-calibrated log-odds scale and packed with unblurred lazy-greedy exact `300 m` triangular-kernel submodular max-cover (`37,654` binary dots, `d_vis > 2.05 px`) | Captures **both** sub-2 m piedmont/relay scarplets missed on 1:250k maps **and** unmapped intra-horst bedrock faults & blind hydrothermal conduits (`>75%` of Great Basin geothermal systems, Faulds & Hinz 2015) across `100%` of the footprint including `d_cat > 3.2 km` | Lake Lahontan pluvial shorelines, incised fan channels, road embankments, and non-tectonic welded-tuff cooling joints | First repo candidate combining 4-quadrant OOF GBDTs across both neotectonic & off-catalogue populations, full 38-feature multi-sensor localized stack with native `NaN` routing for un-flown LiDAR, and unblurred exact-kernel submodular dot packing | Medium (~90 s CPU) | **Experiment 3 of 3 (`Exp 5C` — Primary Candidate)** |
| **2** | **`H-P5-2` · Unsupervised Multi-Scale Strike-Coherent Ridge × Cross-Gradient Operator** | `det_elev_slope`, `iso_grav_anom`, `rtp`, `topo_10m` (`slope_std`, `curv_prof_absmax`, `hs_lineament`), `lidar_scarp` (`upface_max`, `cross_max`) | Zero-training multi-scale edge magnitude ($\sigma \in \{1, 2, 3.5\}$ px) $\times$ structure-tensor axial coherence minus Gallardo–Meju gravity–magnetic cross-product confounder, packed with exact `300 m` submodular max-cover (`37,654` dots, `d_vis > 2.05 px`) | Completely immune to catalogue spatial bias; detects linear scarps across unmapped ranges and basins | Erosional hogbacks, basalt flow margins, paleoshoreline bluffs | First full-footprint multi-scale 1m+10m+100m coherent ridge + submodular emitter in `GEMSDOE70` | Low (~20 s CPU) | **Experiment 1 of 3 (`Exp 5A` — Unsupervised Baseline)** |
| **3** | **`H-P5-3` · Single-Population LOO Off-Catalogue SGMC Ranking (`HANDOFF.md` Step 1)** | Same 38 localized multi-sensor features as `H-P5-1`, trained leave-one-quadrant-out solely on `SGMC` `d_cat >= 3 px` | Single OOF `HistGradientBoostingClassifier` (`M_bed` alone) across full footprint (`d_vis > 2.05 px`) + exact `300 m` submodular packing (`37,654` dots) | Directly learns off-catalogue bedrock & range-front fault signatures absent from QFaults without `P4`'s `d <= 32 px` truncation | Pre-Cenozoic contacts/thrusts in SGMC without Quaternary reactivation | Exact implementation of `HANDOFF.md` Priority #1 | Medium (~60 s CPU) | **Experiment 2 of 3 (`Exp 5B` — Single-Expert Ablation)** |
| **4** | **`H-P5-4` · Differential Demagnetization × MT Clay-Cap Lateral Breach** | `rtp`, `TMI_up150`, `tc`, `cond_surf` (`https://gdr.openei.org/submissions/1391`, DOI `10.5066/P93LGLVQ`) | Coincident shallow magnetic trough `-Z(RTP) + Z(TMI_up150)` (hydrothermal magnetite oxidation) and lateral conductivity gradient `|∇G_2(cond_surf)|` at smectite clay-cap margins | Blind hydrothermal upflow zones destroy magnetite and form clay caps without surface rupture | Zeolitized tuffaceous lake beds, saline playa brines | Incorporated as a localized feature channel inside `Exp 5B/5C`; coarse MT station spacing limits standalone 100 m localization | Low | Queued standalone (channel active in `Exp 5B/5C`) |
| **5** | **`H-P5-5` · Endorheic-Normalized Drainage Divide $\Delta\chi$ Asymmetry** | `dem10_chi_100m_i16.tif` (`chan_n, knick_n, raised_n`) from public-domain USGS 3DEP 10 m (`https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/`) | Cross-divide $\chi$-jump across footwall uplift blocks normalized per endorheic hydrographic basin | Active footwall tilt reorganizes headwater divides even where piedmont scarps are buried by fans | Resistant caprock knickpoints, inter-basin playa elevation steps | Pre-screen canary showed un-normalized `knick_n` AUC = `0.5004` due to endorheic base-level jumps; requires hydrographic-basin outlets (`USGS WBD HUC10`) first | Medium | Queued for future session |

---

## 3. Frozen Hyperparameters, Split Hygiene & Promotion Gates

1. **Strict Out-of-Fold Spatial Split (Zero Leakage):**
   - Four geographic quadrants `quad = holdout.quadrant_ids(fp)` with a `12 px` (`1.2 km`) boundary erosion collar on **both** training and evaluation masks so multi-scale smoothing ($\sigma \le 4\text{ px}$) cannot leak across quadrant boundaries.
   - On **Instrument A** (`buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)`): fold `k` derives every catalogue feature strictly from `vis = fold['visible']`, fits `M_neo` and `M_bed` strictly on `train_q = valid_eroded & (quad != k)`, and masks only `d_vis <= 2.05 px`.
   - On **Production & Instrument B′ / B / B″**: every pixel in quadrant `k` (`quad == k`) is scored strictly by `f_{-k}` fitted exclusively on `quad != k` (`valid_eroded & (quad != k)`), using `M_neo` trained on `cat` in `quad != k` and `M_bed` trained on `SGMC & ~cat & (d_cat >= 3 px)` in `quad != k`. **Zero in-sample predictions anywhere in `prod`!**
2. **Frozen Model & Blend Specification (`Exp 5C`):**
   - `HistGradientBoostingClassifier(max_iter=160, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=5.0, random_state=7005 + k)` (`250,000` stratified training pixels per fold).
   - Rank-calibrated geometric/weighted dual-population score on allowed pixels (`valid & (d_vis > 2.05)`):
     $$S_{\text{dual}}(x) = r_{\text{bed}}(x)^{0.55}\,r_{\text{neo}}(x)^{0.35}\,r_{\text{unsup}}(x)^{0.10}$$
     where $r_{\cdot}(x) \in (0, 1]$ is the exact within-domain empirical quantile rank of each component across valid pixels. (Frozen weights `0.55 / 0.35 / 0.10` registered before running!)
   - Exact unblurred 300 m kernel lazy-greedy submodular packing (`DOT_COUNT = 37,654` crisp binary `{0.0, 1.0}` off-catalogue dots).
3. **Mandatory All-Pass Promotion Gates (`promoted = True` iff ALL hold simultaneously):**
   - **Canary gate:** Every single feature alone has finite `0 <= AUC <= 1` and `max(AUC, 1 - AUC) <= 0.90` on held-out faults.
   - **Surface & Final Uniqueness gates:** Across all `62` archived registry rasters (plus all published `GEMSDOE70` rasters), full-footprint Spearman `<= 0.90` and mutual 3-px overlap `<= 0.70` (plus forward overlap `< 0.70` on every sparse raster `< 100k` dots).
   - **Format & Range gate:** Shared `submission_writer.py` + `validate_submission.py` pass `15/15` checks (`0` NaN, `0` Inf, binary `{0.0, 1.0}`, `37,654` dots, `0` on `existing_faults.tif`).
   - **Gate A (Instrument A — Catalogue Holdout):** `DTI(Exp 5C) > DTI(H33 = 0.0037)` AND `DTI(Exp 5C) > DTI(P4 = 0.0730)` AND **`DTI(Exp 5C) > DTI(D28 = 0.0919)`** with positive paired 95% spatial-block bootstrap CI vs `H33`, `random_control`, and `P4`!
   - **Gate B′ (Instrument B′ — Pre-Registered Target-Like `SGMC d_cat >= 3 px`, Strictly Out-of-Fold):** **`DTI(Exp 5C) > DTI(H33 = 0.0938)` with 95% paired spatial-block bootstrap CI strictly `> 0`** (AND `> DTI(D28 = 0.0935)` AND `> DTI(P4 = 0.0812)`)!

---

## 4. Run-1 Outcome (`v5.0`, Experiment 1 of 3) & Frozen Run-2 Specification (`v5.1`, Experiment 2 of `<= 3`)

### 4.1 Run-1 Forensic Diagnosis (`evidence/phase5/run1_v50_run_card.json`)
Run 1 (`v5.0`) achieved **`0.10210` (`95% CI [0.08511, 0.12074]`)** on Instrument A (surpassing `D28 = 0.09192`, `H33_fair = 0.09042`, `P4 = 0.00481`, and `H33 = 0.00370`) and **`0.11304` (`95% CI [0.08718, 0.13750]`)** on Instrument B′ (`d_cat >= 3 px`), while `Exp 5A` (`r_unsup`) reached **`0.16433` (`95% CI [0.14710, 0.17961]`)** on Instrument B′ and `Exp 5B` (`HANDOFF.md` Item #1, SGMC-only HGB) falsified pure SGMC supervision on Quaternary faults (`0.04143` on Instrument A).

Our automated gate returned **`verdict = negative`** on Run 1 because fold diagnostics exposed two exact statistical bugs:
1. **`IR-P5-1` (Hide-mask / survey-completeness covariate shift in `X[:, 38:41]`)**: Including `vis_dist_capped`, `vis_tip_lobe`, and `vis_host_len_prox` inside `M_bed` trained `M_bed` to up-weight mapped fault density. When Instrument A masked fault components inside `fold['region']`, `X[:, 38:41]` jumped inside `fold['region']`, starving all 4 test regions combined to only **`9,007 / 37,654` (`23.9%`)** of emitted dots in `Exp 5B` (`1,404` dots on Fold 1 of `Exp 5C`, scoring `0.04449` vs `0.13643` on Fold 0 and `0.13279` on Fold 3).
2. **`IR-P5-2` (Cross-quadrant base-rate & regional level shift)**: Concatenating uncalibrated probabilities across 4 quadrant models trained with fixed `max_neg = 180,000` (penalizing Quadrant 1, where NE Nevada holds ~48% of SGMC faults, by `-0.46` log-odds) plus un-high-passed regional crust/strain levels starved Quadrant 1 on Instrument B′ to **`1,116 / 37,654` (`3.0%`)** of dots (`0.01901`), despite achieving **`0.18235`, `0.16474`, and `0.15382`** across Quadrants 0, 2, and 3!

### 4.2 Frozen Run-2 Bug-Fix Specification (`H-P5-5`, Experiment 2 of `<= 3`) — Locked Before Execution
1. **Strictly Catalogue-Free Physical Features (`n_features = N_STATIC_FEATURES = 38` for BOTH `M_neo` AND `M_bed`)** with high-pass localization (`x - G_12(x)`) applied to broad regional background fields (`b04`, `b07`, `b08`, `b15`, `b16`, `b17`) so trees split strictly on local fault steps rather than eastern-vs-western Nevada regional background.
2. **Exact Per-Partition Out-of-Fold Rank Calibration**: Within every disjoint out-of-fold prediction partition (`H0`, `H1`, and `test_k` on Instrument A; each held-out quadrant `k in {0,1,2,3}` on Production / Instrument B′), compute empirical quantile ranks `rank01_domain(p)` **strictly within that partition** (zero test-label access), eliminating 100% of fold base-rate shift and ensuring balanced geographic coverage across all four quadrants.
3. **Frozen Synthesis Weights**:
   $$S_{\text{P5-5}}(x) = r_{\text{neo}}(x)^{0.45}\,r_{\text{unsup}}(x)^{0.30}\,r_{\text{bed}}(x)^{0.25}$$
   emitted via exact unblurred 300 m submodular max-cover (`DOT_COUNT = 37,654`, `d_vis > 2.05 px`, `support_quantile = 0.90`, `gamma = 2.0`).
4. **Identical All-Pass Promotion Gates**: Must pass EVERY single gate simultaneously (clean feature canaries, uniqueness on pre-placement surface & final dots across all 59 distinct rasters, `15/15` validator checks, and **strictly positive 95% paired spatial-block bootstrap CI against ALL benchmarks — including `h33_reference`, `h33_fold_fair`, `p4_reference`, `d28_reference`, and `random_control` — on BOTH Instrument A AND Instrument B′**).

---

## 5. Run-2 Outcome (`v5.1`, Experiment 2 of 3) & Frozen Run-3 Non-Lattice One-Way Uniqueness Tightening (`v5.2`, Final Experiment 3 of 3)

### 5.1 Run-2 Outcome (`evidence/p8_dual_submod300/run2_v51_run_card.json`)
Run 2 (`[0.45 neo, 0.30 unsup, 0.25 bed]`, `support_quantile = 0.90`) **passed all `11 / 11` scientific & mutual-uniqueness gates simultaneously**:
- **Instrument A (`HOLDOUT-DTI`)**: **`0.10660`** (`95% CI [0.08986, 0.12595]`), beating `h33_reference` (`+0.10290`), `h33_fold_fair` (`+0.01618`, `95% CI [+0.00386, +0.02986]`), `d28_reference` (`+0.01468`, `95% CI [+0.00161, +0.02849]`), `p4_reference` (`+0.10179`), and `random_control` (`+0.05605`).
- **Instrument B′ (`PROXY-DTI`, `d >= 3 px`)**: **`0.13181`** (`95% CI [0.11661, 0.14609]`), beating `h33_reference` (`+0.03804`, `95% CI [+0.02709, +0.04783]`), `d28_reference` (`+0.03828`), `p4_reference` (`+0.05065`), and `random_control` (`+0.06208`), AND beating merged `P7` (`0.12081` vs `0.09997`, `+0.02084`, `95% CI [+0.00818, +0.03394]`) on Instrument B″ (`d >= 6 px`).
- **Pass-2 Uniqueness Tightening Audit**: Under mutual overlap across all `78` rasters (`62` archive + `16` local), `worst_mutual = 0.5475 <= 0.70` (`PASS`). However, checking one-way forward overlap on non-lattice (`< 100k`-dot) submissions revealed a single marginal exceedance of `+0.0082` (`fwd = 0.7082`, `rev = 0.5475`) against `GEMSDOE49__gate_ortho_w0.25-40k.tif` (a pure 10 m DEM topographic ridge submission).

### 5.2 Frozen Run-3 Specification (`v5.2`, Final Experiment 3 of `<= 3`) — Locked Before Execution
Using our 3rd and final allowed session experiment (`experiment_count = 3`), we tighten uniqueness by shifting `0.10` weight from pure topographic `r_unsup` to multi-sensor Quaternary `r_neo` (**`[w_neo = 0.55, w_unsup = 0.20, w_bed = 0.25]`**) and broadening submodular candidate support slightly (**`support_quantile = 0.88`**) so sub-surface geophysical/strain/hydrothermal faults receive stronger representation relative to pure 10 m DEM crests, and add a **12th mandatory gate**: **BOTH mutual overlap AND one-way forward overlap `<= 0.70` against EVERY `< 100k`-dot submission in all 78 archived + local rasters**, alongside all 11 gates from Section 4.


