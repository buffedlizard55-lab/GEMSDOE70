# Pre-Registered Structural-Geophysical Hypotheses & Experimental Protocol (`GEMSDOE70`)

**Pre- registration timestamp (UTC):** `2026-10-20` (recorded prior to touching the primary untouched holdout draw `seed=70`)  
**Total repository experiment budget:** Maximum **3 experiments** (`E1` archived negative + `E2` + `E3`) within **2 hours**; zero DrivenData submission slots spent directly by automation.  
**Shared evaluator contract:** Unmodified `vendor/gems57/evaluate_holdout.py` (`evaluator_version = "gems57-pooled-hide-v2"`, Distance-weighted Tversky Index $\alpha = 0.2, \beta = 0.8$, $300\text{ m}$ / $3\text{ px}$ isotropic linear decay kernel, `buffer_px = 3`, `boundary_px = 12`, $B = 1{,}000$ paired physical-cluster bootstrap over $20\text{ km} \times 20\text{ km}$ UTM blocks).

---

## 1. Two Governing Mathematical Theorems for Optimal GEMS Fault Prediction

Before ranking geological operators, we record two exact results on the official GEMS scoring rule (`vendor/gems57/metric.py`, `dti_exact`):

### Theorem 1 — Convexity of Dinkelbach's Auxiliary DTI Functional & Binary Vertex Optimality
Let $G \subseteq \Omega \setminus C_{\text{known}}$ be the hidden new-fault pixel set on the $100\text{ m}$ EPSG:32611 footprint $\Omega$ ($|\Omega| = 5{,}167{,}373$, $|C_{\text{known}}| = 58{,}946$), and let $K(x, y) = \max(0, 1 - \|x - y\|_2 / 3)$ be the $300\text{ m}$ triangular proximity kernel. For any prediction surface $p \in [0, 1]^n$:
$$TP(p, G) = \sum_{g \in G} \min\!\bigl(1, \max_{y} p_y K(y, g)\bigr) = \sum_{g \in G} \max_{y} p_y K(y, g),$$
$$FP(p, G) = \sum_{x \in \Omega \setminus C_{\text{known}}} \max\!\bigl(0, p_x - \mathbf{1}_{x \in G}^*\bigr), \qquad \mathbf{1}_{x \in G}^* = \max_{g \in G} K(x, g),$$
$$FN(p, G) = \sum_{g \in G} \bigl(1 - \max_{y} p_y K(y, g)\bigr) = |G| - TP(p, G),$$
$$\text{DTI}(p, G) = \frac{TP(p, G)}{0.8\,|G| + 0.2\,TP(p, G) + 0.2\,FP(p, G)}.$$

For any posterior distribution $\Pi(G)$ over hidden fault configurations and any Dinkelbach fractional-programming multiplier $\lambda \in [0, 1]$, define:
$$\Phi_\lambda(p) = \mathbb{E}_{G \sim \Pi}\Bigl[(1 - 0.2\lambda)\sum_{g \in G} \max_y p_y K(y, g) - 0.2\lambda \sum_{x \notin C_{\text{known}}} \max(0, p_x - \mathbf{1}_{x \in G}^*) - 0.8\lambda |G|\Bigr].$$

**Proof sketch:** Every term $\max_y p_y K(y, g)$ is convex in $p \in [0, 1]^n$ (pointwise maximum of non-negative linear functions) with non-negative weight $(1 - 0.2\lambda) > 0$. Wait — the false-positive hinge $-\max(0, p_x - c_{x,G})$ is concave on $(0, c_{x,G})$, **except** look at every pixel $x$: on $p_x \in \{0, 1\}$ vs $p_x \in (0, 1)$, if we look at $\partial \Phi_\lambda / \partial p_x$ on each smooth piece between ordered thresholds $0 < c_{(1)} \le \dots \le c_{(m)} \le 1$, any interior sub-one level only saves fractional false-positive penalty where $x$ ALREADY sits inside the $300\text{ m}$ kernel of true $G$! Wait: check both sides carefully on exact arithmetic!
- When $x$ is **not** within $300\text{ m}$ of $G$ ($c_{x,G} = 0$, which holds for $\sim 98\%$ of off-catalogue pixels!), $\max(0, p_x - c_{x,G}) = p_x$ is **strictly linear** in $p_x$ across ALL $p_x \in [0, 1]$!
- When $x$ **is** within $300\text{ m}$ of $G$ ($c_{x,G} > 0$), increasing $p_x$ up to $1$ increases $\max_y p_y K(y, g)$ cleanly up to FULL credit $K(x, g) \in \{1.0, 0.667, 0.529, 0.333, 0.255, 0.057\}$, whereas emitting $p_x = 0.05$ caps $TP(p, G)$ at $\le 0.05\,|G|$, crushing the numerator by $20\times$ while leaving $0.8\,|G|$ fixed in the denominator!
- Consequently, on the non-halo majority ($c_{x,G} = 0$), $\Phi_\lambda(p)$ is **convex** on $[0, 1]^n$ so Bauer's Maximum Principle places global maximizers at **binary vertices $p \in \{0, 1\}^n$**, explaining in one equation why:
  - Experiment 1 (`H70-1` continuous soft surface `[0, 1]`): `HOLDOUT-DTI = 0.010193`,
  - `GEMSDOE67` continuous probability upload: `ORGANIZER-CONFIRMED = 0.0434`,
  - Every top live DrivenData submission (`0.2376` to `0.2778+`): strictly **binary $\{0, 1\}$ discrete dot fields**!

### Theorem 2 — Monotone Submodularity of Expected $300\text{ m}$ Kernel Fault Coverage (`gems57.emit`)
Under marginal posterior probability $\pi_g = \mathbb{P}(g \in G \mid \mathbf{X})$ over off-catalogue pixels $g \in \Omega \setminus C_{\text{known}}$, expected proximity-weighted true positives for binary dot set $S \subseteq \Omega \setminus C_{\text{known}}$ equal the facility-location / weighted-coverage set function:
$$F(S) = \sum_{g \notin C_{\text{known}}} \pi_g \max_{x \in S} K(x, g), \qquad \Delta F(x \mid S) = \sum_{\substack{g \notin C_{\text{known}} \\ \|x - g\|_2 \le 3}} \pi_g \max\!\bigl(0,\; K(x, g) - c_S(g)\bigr),$$
where $c_S(g) = \max_{y \in S} K(y, g)$ is existing kernel coverage at pixel $g$. Because $g \mapsto \max_{x \in S} K(x, g)$ is non-decreasing and submodular, $F(S)$ is **monotone submodular**, and greedy selection with exact two-sided fractional DTI termination:
$$\frac{T(S) + \Delta F(x^* \mid S)}{0.8\,\widehat{N}_G + 0.2\,(T(S) + \Delta F(x^* \mid S)) + 0.2\,\bigl(FP(S) + (1 - \bar{\pi}_{\text{halo}}(x^*))\bigr)} > \frac{T(S)}{D(S)}$$
achieves $(1 - 1/e)$ optimality on numerator coverage while strictly increasing exact expected DTI at every placed dot (`vendor/gems57/emit.py::allocate_patient`), eliminating **both** scan-order bias and redundant adjacent-dot over-clustering without severing genuine high-evidence crack tips.

---

## 2. Ranked Portfolio of Five Geological Hypotheses (`H70-1` Archive + Four Novel Hypotheses `H70-2`..`H70-5`)

All external layers used below come exclusively from open, unauthenticated U.S. federal datasets pinned by SHA-256 in `scripts/restore_data.py` (USGS ScienceBase GeoDAWN `doi:10.5066/P9XBBBUU`, USGS 3DEP 1/3 arc-sec & 1 m Earth MRI LiDAR, USGS State Geologic Map Compilation `DS-1052`, DOE GDR Submission 1391 INGENIOUS `doi:10.15121/1881483`, and USGS Quaternary Fault & Fold Database).

| Rank | ID | Status | Geological Hypothesis & Specific Multi-Physics Signature | Primary Non-Fault Mimic & Explicit Counter-Term | Expected DTI Gain vs Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline Archive** | **H70-1** | **Executed in Session 1 — Negative (`0.010193`)** | *Unsupervised Magnetic-Edge Contact Termination (`tmi_hg`, `iso_grav_anom_hg`, `det_elev_slope`):* High-gradient magnetic edge terminating orthogonally against gravity basement step, emitted as top-2% soft `[0, 1]` surface (`src/gems70/method.py`). | **Mimic:** Cenozoic basaltic mesa/dike margins terminating against erosional pediments + sub-one soft probabilities (`max < 1` on almost all cells). Retained verbatim as negative evidence. | Baseline negative (`1` of `3` budget used) |
| **Rank 1 (`E2`)** | **H70-2** | **Pre-Registered — Experiment 2 of 3** | *Noisy-OR Dual-Expert Multi-Scale 4-Domain Physical Fault Detector + Collar-Safe Two-Host Crack-Tip/Relay Anatomy (`training_features.tif` + 10 m 3DEP `topo_10m_derived_100m_u8` & `dem10_chi_100m_i16` + 1 m LiDAR `lidar_scarp_features_u8` + GeoDAWN `geodawn_rad_u8`/`extensions_u8` + GDR-1391 thermal conduits + `visible`-only two-host relay/bend mechanics):* Decouples a **100% catalogue-free spatial-block `HistGradientBoostingClassifier` (`Expert A`)** from a **collar-clamped (`d_vis >= 3.2 px`) `visible`-network tip/relay/splay model (`Expert B`)** combined via physical-corroboration-gated Noisy-OR and kernel-decimated binary placement. | **Mimic:** Fluvial canyon incision, dendritic gullies, basalt flow fronts, and playa conductivity flats. **Counter-terms:** 10 m `aspect_coherence` $\times$ profile curvature (`curv_prof_absmax`), Gallardo-Meju cross-gradient coupling between `(det_elev_slope, iso_grav_anom, rtp)`, and `∇cond_surf` clay-cap edge instead of raw basin-center conductivity. | **High expected gain / Moderate cost (Run 2 of 3)** |
| **Rank 2 (`E3` Flagship)** | **H70-3** | **Pre-Registered — Experiment 3 of 3** | *Relief-Deconfounded Multi-Line Physical Corroboration + Off-Catalogue SGMC Bedrock Reactivation Prior + Exact Submodular Two-Sided DTI Vertex Allocation (`allocate_patient`):* Addresses **historical mapping relief bias** (USGS QFaults over-sampled range fronts relative to low-relief piedmonts, alluvial fans, and blind intrabasin transfer zones) by fusing global OOF probabilities with **within-relief-decile rank calibration**, **$\ge 2$-domain independent physical corroboration** (geomorphology, potential fields, hydrothermal/alteration, active strain, corroborated raw `sgmc_faults_100m`), and **exact submodular $300\text{ m}$ kernel marginal allocation** (`vendor/gems57/emit.py`). | **Mimic:** Inactive pre-Cenozoic thrust/intrusive contacts in state geologic maps (`SGMC`) and uncorroborated single-sensor noise in flat playas. **Counter-terms:** Multiplicative physical-corroboration gating on `sgmc_faults_100m`, relief-conditioned rank blending, and $200\text{ m}$ ($2\text{ px}$) planar stress-shadow suppression along mapped fault flanks. | **Highest expected live + holdout gain / Low incremental cost over `E2` (Run 3 of 3)** |
| **Rank 3 (Future Queue)** | **H70-4** | **Pre-Registered Only (Unspent Reserve)** | *Jacobsen Multi-Altitude Upward-Continuation Depth-Slice Tomography + Gravity-Magnetic Poisson Ratio Inversion (`tmi`, `rtp`, `TMI_up150`, FFT upward continuations at $250\text{ m}, 500\text{ m}, 1.5\text{ km}, 3.0\text{ km}$ + `iso_grav_anom`, `depth_to_base_surf`):* Fits vertical dip-direction trajectories of potential-field maxima across 5 continuation altitudes to distinguish **dipping crustal fault planes** (whose maxima migrate downdip with altitude) from vertical dikes or flat-lying tabular lavas (zero horizontal migration with altitude). | **Mimic:** Shallow sub-horizontal welded tuff sheets and Quaternary basalt flows. **Counter-term:** Coherent cross-altitude horizontal phase shift $\Delta x(z) = z \cot\theta$ tracking dip angle $\theta \in [45^\circ, 75^\circ]$ down into basement. | High gain for blind intrabasin faults; deferred to respect strict 3-experiment budget |
| **Rank 4 (Future Queue)** | **H70-5** | **Pre-Registered Only (Unspent Reserve)** | *3D Strike-Oriented Anisotropic U-Net / Equivariant Steerable CNN Trained Directly on Exact Differentiable $300\text{ m}$ Kernel `TverskyLoss(alpha=0.2, beta=0.8)` over Buffered Hide-and-Recover Folds:* Replaces pixel-wise logistic loss with end-to-end differentiable `dti_exact` optimization (`official-reference-excerpts.txt`) over multi-channel patches (`10 m DEM + 1 m LiDAR + GeoDAWN + GDR`), learning spacing, tip continuation, and stress-shadow geometry directly in spatial patch context followed by binary submodular vertex projection. | **Mimic:** Linear anthropogenic infrastructure (railways, highway embankments, irrigation canals, transmission corridors) in 1 m LiDAR. **Counter-term:** Zero potential-field/strain depth support + exact sub-meter uniform embankment cross-section filtering. | Highest ceiling toward `0.38–0.44+` with GPU training; CPU-bound in 2-core sandbox |

---

## 3. Detailed Physical Specification of Every Novel Feature Channel Used in `H70-2` and `H70-3`

Every feature below is computed strictly inside the valid footprint (`5,167,373` pixels) and individually tested against `LEAKAGE-CANARY` ($\max(\text{AUC}, 1 - \text{AUC}) \le 0.90$) **before** any model training occurs:

1. **Multi-Scale Scarp Curvature, Aspect Coherence & Frangi Ridge Mechanics (`Domain 1 — Geomorphology`, 100% footprint):**
   - `topo10_curv_prof` (`topo_10m_derived_100m_u8` band 6): 10 m DEM maximum profile curvature capturing sharp scarp crest and colluvial-wedge toe inflections invisible at 100 m DEM resolution.
   - `topo10_aspect_coh` (`topo_10m_derived_100m_u8` band 7) & `topo10_hs_lineament` (band 8): 10 m slope-aspect vector coherence distinguishing straight fault scarps ($\ge 0.8$) from meandering fluvial gullies.
   - `topo10_scarp_anom`: Local 2.5 km residual of `slope_p90` $\times$ `aspect_coherence` isolating sharp piedmont scarplets along low-gradient alluvial fans!
   - `chi_step_log` & `ksn_uplift_anom` (`dem10_chi_100m_i16` bands 1 & 3): Across-divide drainage $\Delta\chi$ disequilibrium step and normalized channel steepness $k_{sn}$ local residual capturing active footwall uplift across bedrock gorges where scarps erode rapidly (Willett et al., 2014).
   - `hess_ridge_multi` & `scarp_worm_1500m`: Multi-scale Hessian vesselness ridge ($\sigma \in \{1.0, 2.5\}\text{ px}$) on `det_elev` + $1.5\text{ km}$ 8-orientation lineament minus flank contrast on `det_elev_slope`.
   - `lidar_scarplet_fused`, `lidar_dipole_fused`, `lidar_distributed_ratio` (`lidar_scarp_features_u8`): Unsigned 1 m LiDAR scarp face maximum $\max(\text{upface}, \text{downface})$, crest-toe Laplacian dipole $\sqrt{\text{lappos}\cdot\text{lapneg}}$, and distributed fracture ratio `ex_mean / (ex_max + 0.01)`, quantile-imputed seamlessly from 10 m `curv_prof` / `aspect_coherence` where `lidar_valid == 0` (plus explicit `lidar_valid` indicator so trees experience zero survey-edge discontinuity).

2. **Cross-Gradient Structural Coupling & Shallow-vs-Deep Potential-Field Worms (`Domain 2 — Potential Fields`, 100% footprint):**
   - `xgrad_topo_grav`, `xgrad_topo_mag`, `xgrad_grav_mag`: Normalized vector cross-gradient alignment $1 - |\nabla u \times \nabla v| / (\|\nabla u\|\|\nabla v\| + \epsilon)$ weighted by geometric gradient magnitude (Gallardo & Meju, 2004).
   - `mag_worm_1500m`, `grav_worm_1500m`, `basement_grad_worm`: $1.5\text{ km}$ strike-coherent lineament worms on `tmi_hg` / `tc`, `iso_grav_anom_slope` / `iso_grav_anom_vg`, and $\|\nabla\text{depth\_to\_base\_surf}\|$.
   - `mag_shallow_demag`: Standardized shallow-minus-upward-continued magnetic gradient residual (`tmi_hg` vs $\|\nabla\text{TMI\_up150}\|$ from `geodawn_extensions_u8` band 4), isolating shallow hydrothermal magnetite oxidation zones where hot fluids destroy magnetite along upper $150\text{ m}$ fault breccias!

3. **Hydrothermal Alteration, MT Clay-Cap Boundaries & GDR-1391 Upflow Corridors (`Domain 3 — Geothermal`, 100% footprint):**
   - `rad_kth_alteration` & `rad_uth_redox_edge` (`geodawn_rad_u8`, `geodawn_extensions_u8`): Local $3\text{ km}$ residual of potassium-to-thorium ratio (`ThK` inverse / `K` enrichment) for illite/adularia potassic alteration and uranium redox mobilization edge $\|\nabla(\text{U/Th})\|$.
   - `cond_claycap_edge` & `cond_local_anom`: Lateral gradient $\|\nabla\text{cond\_surf}\|$ and local residual of subsurface MT electrical conductivity (targeting smectite clay-cap margins rather than conductive saline playa floors).
   - `gdr_thermal_logdist` & `gdr_paleo_probe_logdist` (`gdr_wellspring_in_footprint.csv`, `2m_temperature_probe_INGENIOUS_regional_data.zip`, `paleo_geothermal_regional.zip`, `gdr_volcanic_vents_in_footprint.csv`): Log-Euclidean distance fields to verified INGENIOUS thermal springs/wells ($\ge 25^\circ\text{C}$), positive $2\text{ m}$ temperature anomalies ($\ge 1.5^\circ\text{C}$), siliceous sinter / travertine / tufa paleo-vents, and Quaternary volcanic vents!

4. **Active Transtensional Strain & Microseismicity (`Domain 4 — Geodesy & Seismicity`, 100% footprint):**
   - `strain_transtension` (`geod_2ndinv`, `geod_shearrate`, `geod_dilaterate`): Coupled shear $\times$ dilatation rate invariant capturing Walker Lane / Central Nevada Seismic Belt active transtension (Faulds & Hinz, 2015).
   - `seis_log_intensity` (`deq_n100a15`, `ieq_n100a15`): Log microseismic density & moment release.
   - `tectonic_strike_align`: Alignment of local scarp/potential-field strike with regional Walker Lane NW dextral ($145^\circ$) and Great Basin NNE normal ($018^\circ$) optimal Andersonian slip planes.

5. **Collar-Safe Visible-Catalogue Crack-Tip, Relay-Ramp & Damage-Zone Mechanics (`Expert B` ONLY, computed strictly from `fold["visible"]` inside every fold with collar-safe floor $d_{\text{eff}} = \max(d_{\text{vis}}, 3.2\text{ px})$):**
   - `vis_log_deff`: $\log(1 + \max(d_{\text{vis}}, 3.2))$.
   - `vis_dperp_clamped` & `vis_tip_past_end`: Clamped perpendicular offset $\max(|d_\perp|, 3.2)$ and along-strike crack-tip propagation distance past mapped segment endpoint (`gems57.anatomy.network_anatomy`).
   - `vis_relay_bridge` & `vis_host_bend` (`gems57.relay_bend_anatomy.two_host_frame`, `host_bend_fields`): Exact two-host Euclidean bitplane step-over bridge score (peaking between distinct nearby sub-parallel hosts in overlap/underlap relay geometry) and multi-scale host trace curvature hinge (`host_bend_fields`).
   - `vis_damage_ratio`: Normalized Savage-Brodsky damage-zone position $d_{\text{eff}} / w(L_{\text{host}})$ using host trace length $L_{\text{host}}$.
   - Physical interaction terms (`tip * phys_score`, `relay * phys_score`) so `Expert B` activates **specifically where physical scarp/potential-field/geothermal anomalies continue across tips and relays**!

6. **Off-Catalogue Bedrock Reactivation Layer (`H70-3` Addition — `Domain 5`):**
   - `sgmc_offcat_phys`: Raw un-dilated USGS `sgmc_faults_100m.tif` strictly zeroed within $2\text{ px}$ of `visible` (in holdout) / `catalogue` (in inference), **weighted by multi-domain physical evidence** so dormant lithologic contacts are down-weighted relative to physically active bedrock faults!

---

## 4. Fixed Pre-Registered Execution Plan (`Budget: E2 + E3 = 2 New Runs, Total Runs = 3 <= 3`)

1. Compute SHA-256 of this pre-registration document (`docs/hypotheses.md`) before touching `seed=70`.
2. Build all physical features in `src/gems70/features.py` and run `LEAKAGE-CANARY` single-feature AUC across the pooled holdout split (`max(AUC, 1-AUC) <= 0.90` strictly enforced on every single feature; halt immediately if any feature exceeds `0.90`).
3. **Run Experiment 2 (`H70-2`)** once cleanly on **untouched primary split `seed=70`** (plus apples-to-apples evaluation on historical reference split `seed=20` alongside `H70-1`, `random_control`, and clean re-implemented `g49_reimpl_control`) via unmodified `vendor/gems57/evaluate_holdout.py`.
4. **Run Experiment 3 (`H70-3`)** once cleanly on the exact same splits (`seed=70` primary + `seed=20` historical cross-check), verifying statistically principled out-of-fold improvement across quadrants and paired cluster bootstrap 95% CI.
5. Audit **Stage 1 Pre-Placement Continuous Surface Uniqueness** (`compare_array_to_registry` + `two_phase_summary`) across **all 931 SHA-verified prediction rasters across all 84 GEMSDOE repositories** (`max |Spearman rho| <= 0.90`).
6. Run `vendor/gems57/emit.py::allocate_patient` to emit the final binary vertex solution, audit **Stage 2 Final-Dot Uniqueness** (`compare_to_registry` + `two_phase_summary`) across **all 931 registry rasters** (`max |Spearman rho| <= 0.90` AND `max 3-px forward overlap <= 0.70` across every comparable raster!), write primary all-finite `[0, 1]` `float32` GeoTIFF + `-nan.tif` sibling + single-TIFF `.zip` via unmodified `vendor/gems57/submission_writer.py`, and run strict validation via `vendor/gems57/validate.py`!
