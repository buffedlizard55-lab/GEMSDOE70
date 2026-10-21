# Pre-Registration: Experiment E6 — Multi-Modal Extended-Domain Leave-One-Quadrant-Out (LOQO) Fault Ranker

* **Date (UTC):** 2026-10-20
* **Branch:** `arena/effcd5f7-gemsdoe70`
* **Predecessor lanes:** Phase 4 (`P4`, `B' = 0.0812`), Parallel `E2` (`A = 0.0647`), Parallel `E3` (`A = 0.0943`, `B'` unscored), `H70-A` (`B' = 0.0792`), `E5` (`A = 0.0815`, `B' = 0.0886`, negative on `B'` gate).

## 1. Scientific Diagnosis of Prior Negative Outcomes (`P4` and `E5`)

1. **SGMC vs. QFaults Re-Digitization Buffer Calibration ($r = 1..6\text{ px}$):**
   - Measuring cumulative and shell-wise spatial coincidence between off-catalogue USGS SGMC fault traces (`sgmc_faults_100m.tif`, `78,433` pixels) and the training catalogue (`existing_faults.tif`, `60,988` pixels) inside the competition footprint (`5,167,373` pixels) shows that shell enrichment is `3.83x` at $d \in (0, 1]\text{ px}$, `2.98x` at $d \in (1, 2]\text{ px}$, `1.86x` at $d \in (2, 3]\text{ px}$, `1.40x` at $d \in (3, 4]\text{ px}$, `1.14x` at $d \in (4, 5]\text{ px}$, and `0.97x` (background parity) at $d \in (5, 6]\text{ px}$.
   - Consequently, `Instrument B'` ($d_{\text{cat}} \ge 3.0\text{ px}$, retaining `59,937` valid off-catalogue pixels after boundary erosion) removes the `20.12%` near-trace compilation duplicate band ($d < 3.0\text{ px}$).

2. **Why `P4` (`0.0812`) and `E5` (`0.0886`) Trailed `H33` (`0.0938`) on `Instrument B'`:**
   - **Domain Truncation (`d_min = 2.4 px`, `d_max = 32.0 px`):** Both `P4` and `E5` restricted dot placement to $d_{\text{cat}} \in [2.4, 32.0]\text{ px}$. However, `37.8%` of `Instrument B'` positive pixels lie at $d_{\text{cat}} > 32.0\text{ px}$ (`50th` percentile = `22.80 px`, `75th` percentile = `41.98 px`, `90th` percentile = `63.01 px`), while `H33` spans up to `118.4 px` (`75th` percentile = `42.45 px`, `90th` percentile = `68.01 px`). Furthermore, dots placed in $2.4 \le d_{\text{cat}} < 3.0\text{ px}$ cannot score true positives on `Instrument B'` ($d_{\text{cat}} \ge 3.0\text{ px}$) while still incurring false-positive penalties.
   - **Missing Multi-Modal External Features (`HANDOFF.md` Next Step 1):** `E5` used only the 19-band stack and potential-field gradients, omitting the external 1 m LiDAR scarp steps (`lidar_scarp_features_u8.tif`), 10 m DEM curvature and hillshade lineaments (`topo_10m_derived_100m_u8.tif`), USGS GeoDAWN radiometric ratios (`geodawn_rad_u8.tif`), and the gradient-directional scarp curvature tensor (`dem_slope`, `dem_curv`, `dem_coherence`).

## 2. Registered Hypothesis, Mechanism, and Non-Fault Mimics

* **Hypothesis (`E6`):** A Leave-One-Quadrant-Out (LOQO) gradient-boosted decision tree (`HistGradientBoostingClassifier`) trained on the 28-feature multi-modal stack across the extended off-catalogue domain $d_{\text{cat}} \in [3.0, 96.0]\text{ px}$ and emitted via 7×7 regional coverage stratification (`block = 7 px`, `nms = 5.0 px`, `n = 37,654` binary dots) will beat `H33` on `Instrument B'` with a 95% spatial-cluster bootstrap confidence interval strictly above zero while matching or exceeding `P4` and `H33` on `Instrument A`.
* **Physical Mechanism:** Unmapped Great Basin faults in `d_cat in [3.0, 96.0] px` are jointly expressed as (i) 100 m and 10 m profile curvature and structure-tensor breaklines (`dem_curv`, `dem_coherence`, `curv_prof_absmax`, `hs_lineament`), (ii) 1 m LiDAR scarp steps (`step_max`, `upface_max`, `downface_max`, `cross_max`), (iii) shallow sediment cover and range-front basement steps (`depth_to_base_surf`, `iso_grav_anom`, `rtp`, `cond_surf`), (iv) radiometric potassium-to-thorium enrichment along hydrothermally altered damage zones (`K / (Th + 10)`), and (v) off-fault continuation decay (`d_cat`, `exp(-(d_cat-3)/15)`, `tip_continuation`).
* **Non-Fault Mimics:** Erosional terrace risers, volcanic flow margins, glacial moraines, and lithologic contacts without brittle displacement; mitigated by requiring tree splits across multi-modal subsurface (`iso_grav_anom`, `rtp`, `depth_to_base_surf`, `cond_surf`), radiometric (`K/Th`), and surface scarp features simultaneously, plus 7×7 regional coverage stratification.

## 3. Registered Feature Stack (28 Features)

1. **100 m DEM Scarp-Curvature Tensor (3 features from `det_elev`):** `dem_slope`, `dem_curv`, `dem_coherence`.
2. **Core 19-Band Geophysical, Stress & Cover Stack (8 features):** `rtp` (band 2), `tc` (band 4), `|dilatation_rate|` (band 6), `det_elev` (band 12), `det_elev_slope` (band 13), `depth_to_base_surf` (band 15), `iso_grav_anom` (band 17), `cond_surf` (band 19).
3. **1 m LiDAR Scarp Features (`lidar_scarp_features_u8.tif`, 5 features):** `step_max` (band 3), `upface_max` (band 6), `downface_max` (band 7), `along_std` (band 8), `cross_max` (band 9).
4. **USGS GeoDAWN Radiometrics (`geodawn_rad_u8.tif`, 5 features):** `rad_K` (band 1), `rad_Th` (band 2), `rad_U` (band 3), `rad_TC` (band 4), `rad_K_Th_ratio = rad_K / (rad_Th + 10.0)`.
5. **10 m DEM Derived Lineaments & Curvature (`topo_10m_derived_100m_u8.tif`, 4 features):** `slope_p90` (band 1), `curv_prof_absmax` (band 5), `relief_local` (band 6), `hs_lineament` (band 8).
6. **Catalogue Geometry (`existing_faults.tif` / fold-visible catalogue, 3 features):** `d_cat`, `exp(-(d_cat - 3.0) / 15.0)`, `tip_continuation`.

## 4. Registered Evaluation & Gate Protocol

1. **Leakage Canaries:** Every feature in the 28-feature stack (plus all 44 underlying physical bands) is tested individually on `Instrument A` (11,321 withheld catalogue positives) and `Instrument B'` (59,937 off-catalogue SGMC positives); any physical feature with $\max(\text{AUC}, 1-\text{AUC}) > 0.90$ halts the run.
2. **Spatial Cross-Validation:**
   - **Instrument B′ (`PROXY-DTI`, $d_{\text{cat}} \ge 3.0\text{ px}$):** 4-fold Leave-One-Quadrant-Out (`holdout.quadrant_ids(fp)`). Each fold's `HistGradientBoostingClassifier(max_iter=80, max_depth=5, learning_rate=0.08, min_samples_leaf=80, random_state=705+k)` is trained strictly on the other 3 quadrants (`quad != k`).
   - **Instrument A (`HOLDOUT-DTI`, 11,321 withheld catalogue pixels):** Evaluated on the 4 buffered whole-component folds (`seed=20, buffer_px=3, boundary_px=12`) using strictly fold-visible catalogue geometry (`d_vis`, `tip_vis`) and fold-out-of-quadrant physical trees.
3. **Registered Ablations (at fixed mass `37,654` binary dots):**
   - `candidate`: Full 28-feature LOQO ranker + 7×7 stratification in $d \in [3.0, 96.0]\text{ px}$.
   - `ablation_truncated_d32`: Same 28-feature LOQO ranker restricted to $d \in [2.4, 32.0]\text{ px}$ (isolating the effect of fixing `P4`/`E5` domain truncation).
   - `ablation_no_external`: 11-feature subset (8 core 19-band features + 3 catalogue geometry features, omitting LiDAR, GeoDAWN, 10 m DEM, and scarp curvature) in $d \in [3.0, 96.0]\text{ px}$.
   - `ablation_unstratified_sep28`: Full 28-feature LOQO ranker emitted via unstratified greedy `min_sep = 2.8 px` (`dotted_emission`).
   - `random_control`: 37,654 random off-catalogue dots.
   - `h33_reference`: Archived `H33` (`37,654` dots).
4. **Scientific vs. Literal Uniqueness Gate:**
   - Scientific gates: `gate_a_candidate_ge_h33` ($\text{DTI}_A(\text{cand}) \ge \text{DTI}_A(\text{H33})$) and `gate_b_prime_candidate_gt_h33_significant` (paired $\Delta\text{DTI}_{B'} > 0$ with 95% spatial-cluster bootstrap lower bound $> 0$).
   - Uniqueness gates: Both the amended mutual-overlap gate (`vendor/gems57/uniqueness.py`, $\text{mutual} \le 0.70$, $|\rho| \le 0.90$) and the literal one-way forward-overlap gate (`src/gems70/protocol.py`, $\text{forward} \le 0.70$ against `calib_r13lattice_00904.tif`) are recorded. Under the active repository policy (`AGENTS.md`), any fixed-mass `37,654`-dot artifact has forward overlap $\ge 0.8234 > 0.70$ against the dense binary lattice witness, so `download_ok = true` (for review) and `submit_recommended = false` until the selector authorizes the non-lattice / mutual rule.
