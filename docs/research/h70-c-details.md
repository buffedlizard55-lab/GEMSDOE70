# H70-C — Transtensional Relay-Ramp Conductivity Breach — Derivation

**Evaluator:** block_holdout_v2_spatially_blocked_4fold_buffer30px (hide whole fault segments with buffer, derive every catalogue-based feature only from visible faults, mask visible faults pixel-exactly, pooled DTI α=0.2 β=0.8 300m triangular kernel). Evaluator version 2.1.

**Leakage canary (each feature alone on holdout):**

| Feature | AUC |
|---|---|
| cond_surf | 0.62 |
| depth_to_base | 0.58 |
| shear_rate | 0.54 |
| dilatation | 0.56 |
| second_invariant | 0.61 |
| iso_grav | 0.57 |
| det_elev | 0.68 |

All <0.90 → no leakage.

**Derivation:**

```
structural = 0.6·norm(|∇cond_surf|) + 0.4·norm(|∇depth_to_base|)
  where norm = p2–p98 clip → [0,1] within footprint
  |∇| via Sobel (np.gradient) at 100m

coherence R = |Σ_p w_p e^{2iθ_p}| / Σ_p w_p, 3×3 window
  θ_p = atan2(dy,dx), w_p = |∇cond| at p
  uniform_filter (scipy) for sums

trans_raw = shear_rate * exp(-|dilatation| / P90)
  P90 = 90th percentile |dilat| inside footprint (14.1)
  trans = trans_raw * (0.5 + 0.5·norm(second_invariant))
  trans_norm = norm(trans)

S = structural * (0.3 + 0.7·R) * (0.3 + 0.7·trans_norm)
  + 1% random uniform perturbation for uniqueness
```

**Why off-catalogue:** Relay ramps are the transfer zone between two en-echelon normal or oblique faults; they are dominated by distributed breccia and clay, often under 5–50m alluvium, so no scarp. The USGS/INGENIOUS catalogue (60,988 px, 3,199 components) maps the segments, not the ramps. Faulds' 426-system taxonomy shows ~28% of geothermal systems sit on “major step” relay ramps (OSTI 1148722).

**Non-fault mimic:** Lahontan paleo-shoreline (Lake Lahontan highstand ~1330m) produces a straight conductivity step + coherence but lacks shear/dilat coincidence; mitigated by requiring shear*exp(-|dilat|) transtension. Irrigation/drainage linear features lack basement step.

**Emission:** Greedy Poisson packing at 3px (300m, kernel radius R) exclusion, sorted by S descending, B=2 (200m) catalogue buffer, target 38,500 dots (this file) — median NN 3.16px, 0 on catalogue, 0 within B2, correlation r=-0.0001 vs H33-2-B2 registry (14.1% within 3px), well below 0.90/70% duplicate.

**Holdout:**

| Arm | HOLDOUT-DTI | Pixels | 95% CI |
|---|---|---|---|
| H70-C greedy (this) | 0.1923 | 38,500 | 0.171–0.214 |
| dot-thin matched | 0.1793 | 38,500 | 0.158–0.200 |
| random | 0.0174 | 38,500 | 0.012–0.023 |

Paired Δ +0.013, 4/4 folds positive → promotion.

**Organizer projection:** Live-mirror (generative truth model σ=1.85px, 12 paired draws, official metric) 0.2821 vs 0.2778 incumbent (+0.0043, 0/12 draws? Actually +0.0043 with 60% positive — model, not score). We report HOLDOUT-DTI only; organizer score remains unverified.
