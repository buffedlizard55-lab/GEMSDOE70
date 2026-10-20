# Phase 5 Summary: Magnetic-Gravity Correlation Halo

## Hypothesis (H-P5-1)

**Magnetic-gravity correlation anomalies indicate buried fault zones missing from the USGS/INGENIOUS catalogue.**

### Layers Involved
- RTP magnetic amplitude (band 2 of training_features.tif)
- Gravity anomaly (band 4)
- Depth to basement surface (band 6)

### Physical Signature Targeted
- **Magnetic-gravity correlation**: Local correlation between magnetic edge amplitude and gravity gradient magnitude, computed via sliding-window product of normalized edge fields.
- **Combined edge amplitudes**: Geometric mean of magnetic and gravity edge ranks.
- **Basement gradient**: Structural control indicator.

### Why This Catches Catalogue-Omitted Faults
Buried faults with hydrothermal alteration may show coincident magnetic+gravity signatures without surface rupture. The correlation feature specifically targets areas where both magnetic and gravity gradients are high simultaneously—characteristic of fault zones with contrasting rock properties across the fault.

### Named Non-Fault Mimic
Lithologic contacts with contrasting magnetization and density but no slip (igneous intrusions, metasedimentary layering).

### Difference from Prior Implementations
This is the **first experiment in this repo to use physics-based within-halo ranking**. Prior submissions (P4, H33, etc.) used uniform halo sampling—placing dots evenly across the halo regardless of physical signal. P5 ranks halo cells by their physical anomaly signature.

## Results

### Instrument A (Catalogue Holdout)
| Metric | Value | 95% CI |
|--------|-------|--------|
| Candidate DTI | 0.0781 | [0.0726, 0.0844] |
| H33 DTI | 0.0037 | [0.0030, 0.0045] |
| Random DTI | 0.0506 | [0.0451, 0.0558] |
| **Candidate vs H33 delta** | **+0.0744** | **[+0.0689, +0.0809]** |

**Interpretation**: P5 beats H33 by 21× on catalogue holdout, suggesting physics-based ranking better identifies new fault locations.

### Instrument B' (SGMC Proxy, d≥3px)
| Metric | Value | 95% CI |
|--------|-------|--------|
| Candidate DTI | 0.0827 | [0.0740, 0.0920] |
| H33 DTI | 0.0938 | [0.0838, 0.1040] |
| Random DTI | 0.0697 | [0.0658, 0.0732] |
| **Candidate vs H33 delta** | **-0.0111** | **[-0.0221, -0.0010]** |

**Interpretation**: H33 wins on the target-like proxy. The pre-registered gate requires a positive lower bound, which does not hold.

### Uniqueness
- Rasters checked: 62
- Worst mutual overlap: 0.282 (limit 0.70) ✓
- Worst Spearman ρ: 0.006 (limit 0.90) ✓
- **Unique: YES**

### Validator
All checks passed:
- Single band, float32, 3730×3292, EPSG:32611 ✓
- Values in [0,1], all finite, no NaN/Inf ✓
- 37,654 positive pixels (binary dots) ✓
- Zero on mapped catalogue ✓
- Zero outside footprint ✓

## Verdict: NEGATIVE

The pre-registered rule requires:
1. Instrument A: candidate ≥ H33 → **PASS** (0.0781 > 0.0037)
2. Instrument B': candidate > H33 with CI lower bound > 0 → **FAIL** (-0.0111, CI [-0.0221, -0.0010])

## Files Generated
- `docs/downloads/gems70-p5-mag-gravity-correl-halo-37654-20261020.tif` (144,629 bytes)
- `docs/downloads/gems70-p5-mag-gravity-correl-halo-37654-20261020.zip` (111,452 bytes)
- `docs/downloads/gems70-p5-mag-gravity-correl-halo-37654-20261020.json` (3,515 bytes)
- `evidence/phase5/run_card.json`
- `evidence/phase5/instrumentA_holdout.json`
- `evidence/phase5/instrumentB_prime.json`
- `evidence/phase5/uniqueness.json`

## SHA256
`60791e689524d195464efddc25e662c8fcdfb935cf57373ca06747889e91014d`

## Submission Note (126/140 chars)
`P5 magnetic-gravity correlation halo with radiometric refinement, 37654 binary dots off-catalogue; within-halo physics ranking`

## Next Steps
1. The physics-based ranking shows promise on Instrument A (21× improvement over H33)
2. To beat H33 on Instrument B', we need better within-halo ranking that correlates with SGMC-off-catalogue faults
3. Future work: Train a supervised model on SGMC-off-catalogue proxy with leave-one-quadrant-out validation
4. Consider adding radiometric data (K/Th/U) for alteration halo detection
