# Candidate hypotheses — session 2026-10-20 (pre-registered before validation)

Status labels: these are **geological hypotheses and holdout-validation targets**, not
discoveries and not scores. Every number in this file is either a HOLDOUT-DTI measurement
(evaluator `gems57-pooled-hide-v2`, withheld positives, 95% CI) or a planning estimate
labelled as such. No ORGANIZER-CONFIRMED value exists in this repository.

## Scope rules applied to all candidates

- **Layers:** only bands of `data/bridge`-pinned `training_features.tif` (19 float32 bands,
  nodata -3.4028e38, EPSG:32611, 100 m; band names in `evidence/feature_metadata.json`), and
  the existing catalogue `existing_faults.tif` (mapped USGS/INGENIOUS traces, `catalogue` mask).
- **Catalogue use:** a catalogue-derived feature may use only *visible* traces in holdout
  (`buffered_component_draw` `visible` mask). Final submission may use the full catalogue,
  since the catalogue is training data under the rules (Official Rules §3.3, "training labels").
- **Scoring:** shared `evaluate_holdout.py`, `holdout.py` and `metric.py` (pinned, unmodified).
  DTI alpha 0.2, beta 0.8, 300 m triangular kernel; pooled; paired 20 km cluster bootstrap.
- **Canary:** every feature tested alone, AUC > 0.90 = suspected leakage (stop).

## Candidate ranking (qualitative expected DTI gain × implementation cost)

| Rank | ID | Layers | Physical signature | Why a catalogue omission is plausible | Named non-fault mimic | Overlap risk vs. registry | Cost |
|---|---|---|---|---|---|---|---|
| 1 | **C1 strike-coherent catalogue extrapolation** | visible traces (structure tensor), `rtp` gradient direction, `rtp` gradient magnitude | Magnetic edges whose orientation matches the local strike of visible traces, within ~2 km of them | Faults in Basin-and-Range systems are echelon/parallel; unmapped segments continue visible strike | Dike swarms and lithologic contacts parallel to the fault system | **High** (catalogue-proximity dots are common in the registry) | Low |
| 2 | C2 magnetic phase jump across along-strike discontinuity (prior queue H2) | `rtp`, `mag_anom`, `iso_grav_anom` | Signed magnetic normal-profile discontinuity conditioned on a gravity boundary | A displaced magnetic contact under cover | Remanence change inside a volcanic flow | Medium | Medium |
| 3 | C5 basement-ramp endpoint (prior queue H3) | `depth_to_base_surf`, `iso_grav_anom`, `det_elev` | Along-strike end of a basement-depth ramp supported by gravity | Blind basin-bounding faults can displace basement without a scarp | Onlap or paleovalley margin | Medium | Medium |
| 4 | C3 potassium depletion along visible strike (GeoDAWN radiometrics) | `ext_geodawn_rad` K, Th, TC (if present in cache) | K/TC depletion in fault-zone alteration | Alteration halos can precede surface expression | Lithologic K-enrichment (granite, rhyolite) | Medium | Medium |
| 5 | C4 geodetic shear-strain coherence (`geod_shearrate`, `geod_2ndinv`) | geodetic strain layers | Active shear localisation | Concealed active faults may carry shear | Interpolation of sparse GPS velocity; groundwater subsidence | Low | Low, but **resolution too coarse** for 300 m traces |

Notes:
- Prior queue items (C2, C5) were already preregistered in `docs/hypotheses.md`; they are
  listed here only for the ranking. Only **C1** is validated in this session.
- C4 uses coarse fields (GPS/InSAR interpolation scale). It is ranked last because its
  resolution is probably larger than the 300 m scoring kernel.

## Validated in this session: C1 (pre-registered parameters)

Structure tensor of visible traces: `T = gaussian(visible, sigma=3 px)`; gradient `(gy, gx)`;
`J = gaussian([gx², gy², gx·gy], sigma=10 px)`; trace-normal direction
`theta_n = 0.5·atan2(2·Jxy, Jxx−Jyy)`; coherence `coh = sqrt((Jxx−Jyy)²+4·Jxy²)/(Jxx+Jyy+eps)`.

Magnetic evidence: `M = |∇ gaussian(rtp, 1.5 px)|`; magnetic gradient direction `phi_m`.

Alignment `A = |cos(phi_m − theta_n)|` (magnetic gradient parallel to trace normal ⇒ edge
parallel to strike).

Catalogue proximity `W = exp(−d_visible / 20 px)` (2 km decay).

Candidate field (before output transform) `F = rank(W)·A·rank(M)·coh`, then
`surface = upper_surface(rank(F), valid, cutoff=0.98)` (same output transform as the stopped run,
so results are comparable).

**Arms:** `candidate` (C1); `ablation_no_catalogue` (A·rank(M)·coh, *no visible catalogue at all*);
`ablation_no_alignment` (rank(W)·rank(M)·coh); `random_control` (same positive count, seed fixed).

**Holdout blocks:** `buffered_component_draw(seed=71, buffer_px=3, boundary_px=12)` — a
**fresh seed**, not the seed-20 blocks already reported in `evidence/holdout.json`.

**Pass criteria (pre-registered):**
1. No canary AUC > 0.90 (feature alone).
2. Candidate HOLDOUT-DTI > `ablation_no_catalogue` (otherwise the catalogue is not contributing).
3. Candidate HOLDOUT-DTI > `random_control` (paired CI of difference excludes 0 for "beats").
4. Registry uniqueness gate computed against the **complete** indexed registry (862 rasters)
   before any submission file is declared downloadable.

Failure on (1)–(3) is a negative result and will be recorded as such.
