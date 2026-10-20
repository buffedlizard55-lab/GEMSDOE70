# Deep research — Great Basin geothermal structural controls & hidden fault detection

> All claims include official verified links for manual review. "Not-retrieved"
> means network access failed in this sandbox, not a login redirect proof.
> Numerical scores are labeled HOLDOUT-DTI (evaluator gems57-pooled-hide-v2,
> 11 321 withheld positives, 95% CI spatial-block bootstrap) or
> ORGANIZER-CONFIRMED (submission-page receipt). No projection is written as a score.

## Question: Why did H33 score 0.2778 and can we beat it?

### What H33 actually is (byte-verified, not a story)

| Artifact | SHA256 (prefix) | Positives | Derivation |
|---|---|---|---|
| D2.8 `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | (see GEMSDOE30) | 44 090 | Early sparse Poisson-disc 300 m off-catalogue field |
| H27 `h27-4-solo-d28-20261004-8acb75e1` | (see GEMSDOE31) | 40 199 | D2.8 minus 3 891 dots within 1 px of catalogue |
| **H33 B2** `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | `c55bafc470054...` | **37 654** | H27 minus 2 545 dots within √2–2 px of catalogue; only 0/1 values; nearest positive ≈224 m (√5 px) from catalogue; median 1.965 km; 5.77% within 300 m |

Source: `evidence/h33_audit.json` (local audit), inherited bundle
`evidence/inherited_h33_submission_bundles.json` (owner archive GEMSDOE32
commit 98901f3), forensic validation `scripts/audit_h33.py`.

H33 is **not a newly trained detector**; it is **pruned prior dots**.
Its "model" is the pruning rule: delete any dot whose distance-to-catalogue ≤2 px.

### Why pruning helped — DTI algebra (verified in `vendor/gems57/metric.py`)

Official metric is distance-weighted Tversky with α=0.2, β=0.8, triangular kernel
R=300 m (3 px): https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
Reference loss uses same α,β: https://github.com/drivendataorg/gems-prize-reference-solution

For binary dots, let:
- `T = Σ_g max_x p(x)·k(d(x,g))` (coverage over truth cells, saturates at 1/truth cell)
- `M = Σ_x max_g k(d(x,g))` (credit per dot)
- `n = |P|`, `K = |G|`
- `D = T + α·(n - M) + β·(K - T)` ; `DTI = T / D`

Adding one dot with self-credit `k` and marginal coverage `dT` (≤k):

```
dDTI > 0  ⇔  dT > α·DTI·(dT + 1 - k)
```

Only when `dT == k` (non-redundant) does this reduce to `k > α·DTI`.
A dot that covers multiple uncovered truth cells has `dT > k`? No, `dT ≤ k` with
equality when it covers only new truth cells. Earlier prose `dT ≤ k` was corrected
in `vendor/gems57/metric.py` docstring; executable arithmetic was already correct.

**Efficiency mechanism**: A new dot near the catalogue but far from hidden truth
has low `k` (distance to hidden truth >R) and `dT ≈ 0` → `dT < α·DTI·(1 - k)` →
DTI decreases. Deleting such dots **raises** DTI even though `n` drops, because
`FP_w = n - M` shrinks. H33's sequential improvements (0.2600 → 0.2708 → 0.2778)
are consistent with removing low-`k` mass.

**Can we beat 0.2778 (or the prompt's 0.3195 / 0.4413 / 0.3774)?**
User-reported leaders conflict and have no ORGANIZER-CONFIRMED receipt here.
Leaderboard https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
was not retrieved this session. We therefore treat 0.2778 as the highest
**byte-verified family artifact**, not a current competition best.

A higher score requires:
1. **Same sparsity** (~37k dots) to keep `n` low, but **better-placed** dots to
   increase `T` per dot (higher `k` and `dT` against hidden truth). Random with
   same `n` needs `k > 0.055` on average; H33's pruning achieved this by
   avoiding catalogue-flanks where hidden truth is apparently not.
2. **Geological plausibility**: hidden faults should be where geophysics says
   cover-buried structure, not where prior sparse heuristics happened to sample.

Discordance corridor is designed for (1)+(2): it biases placement toward
gravity/basement-supported lineaments lacking topographic scarps, which is exactly
where H33's retained dots reside (median 1.965 km from catalogue).

**Caveat**: HOLDOUT-DTI on catalogue-withheld folds (v1: 0.010 vs random 0.047;
v2 candidate: 0.00 vs random 0.023) **cannot** predict hidden-label DTI.
Withheld components are mapped faults; pruning that helps on hidden truth hurts
on withheld mapped faults (they are near-catalogue by definition). Our
holdout is a diagnostic of over-pruning, not a guarantee of leaderboard gain.

## PhD-level hypothesis evaluation (ranked)

See `docs/hypotheses_new.md` for 5 candidates with layers, signatures, mimics,
costs, and expected DTI lift. Top is discordance corridor (implemented); second
is magnetic phase-jump; third basement-ramp tip; fourth conductive breach;
fifth radiometric alteration halo (requires external GeoDAWN radiometrics).

## Literature & data provenance (no hallucinations)

### Official competition & data

| Source | URL | Status | Claim |
|---|---|---|---|
| DOE GEMS competition (DrivenData) | https://www.drivendata.org/competitions/306/competition-doe-gems/ | Verified page exists (search result id1) | Task: predict faults for geothermal in GeoDAWN area, $300k prize, ends 2026-12-03 |
| Problem description | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | Not retrieved this session | Defines DTI α=0.2 β=0.8 R=300 m, 100 m EPSG:32611 |
| Leaderboard | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ | Not retrieved | Manual review target; conflicting user claims not resolved |
| Official rules (NLR) | https://docs.nlr.gov/docs/fy26osti/96647.pdf | Not retrieved | HeroX-linked PDF, see also https://research-hub.nlr.gov/en/publications/geologic-enhanced-mapping-system-gems-prize-official-rules/ |
| Reference solution | https://github.com/drivendataorg/gems-prize-reference-solution | Verified-content | U-Net MC-CV notebook, loss α=0.2 β=0.8, CPU-capable |
| DOE GBCGE INGENIOUS | https://gbcge.org/current-projects/ingenious/ | Claimed by user prompt | Current projects entry (network not verified live) |
| GDR submission 1391 | https://gdr.openei.org/submissions/1391 | Claimed by user prompt | OpenEI repository entry |
| EPSG:32611 | https://epsg.io/32611 | User-supplied | UTM zone 11N |
| Tversky index | https://en.wikipedia.org/wiki/Tversky_index | User-supplied | α,β weighted Jaccard generalization |

### USGS & geothermal science

| Source | URL | Status | What it supports |
|---|---|---|---|
| **USGS GeoDAWN data release** | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and | **Verified** (search id1 DOI 10.5066/P93LGLVQ) | Airborne magnetic & radiometric surveys: 149 030 line-km, 51 857 km², 400 m spacing, Winnemucca/Fallon/Hawthorne/Tonopah blocks, EDCON-PRJ contractor, Glen & Earney 2024 |
| ScienceBase catalog | https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7 | Verified (search id3) | Same DOI, full data files + contractor report |
| DOI landing | https://doi.org/10.5066/P93LGLVQ | Verified via USGS citation | Official DOI for citation |
| **Faulds et al. structural settings** | https://gdr.openei.org/submissions/383 | Verified (search id1) | 32% step-overs/relay ramps, 25% terminations, 22% intersections, 9% accommodation zones, etc.; step-overs most favorable |
| Faulds & Hinz 2015 | https://www.osti.gov/servlets/purl/1724082 | Verified (search id3) | Figure 2 characteristic settings (major fault, bend, tip, step-over, intersection, accommodation zone, displacement transfer) |
| Giddens et al. 2025 Stanford | https://pangea.stanford.edu/ERE/pdf/IGAstandard/SGW/2025/Giddens.pdf | Verified (search id2) | 450+ step-overs inventoried, 2.8–3.5 km avg relay width, overlapping hard-linked geometries favor >120 °C systems |
| Lyell synthesis | https://www.lyellcollection.org/doi/full/10.1144/geoenergy2023-009 | Verified (search id4) | Step-overs 25%, terminations 20%, intersections 18% summary |
| Faulds dataset | https://www.osti.gov/dataexplorer/biblio/dataset/1148722 | Verified (search id5) | Structural inventory hierarchal complexity |
| munimtechnologies baseline | https://github.com/munimtechnologies/gems-fault-mapping | Verified (search id2) | Local DTI metric, CPU baseline, results table |

## Why hidden faults are plausible targets

Great Basin extension creates high-angle normal faults; Quaternary alluvium
often buries scarps while gravity (isostatic anomaly) and basement depth retain
offset. GeoDAWN's 400-m magnetic/radiometric grids at 150–200 m terrain clearance
resolve 100-m-scale lineaments under cover. H33's retained dots are on average
nearly 2 km from mapped faults, indicating hidden truth may be not random
near known faults but in covered basins—exactly where discordance is high.

## What we did not claim

- No geothermal vent, temperature, permeability, or economic resource is claimed.
  Target is fault traces, per organizer's fault-detection notebook.
- No leaderboard score is projected from HOLDOUT-DTI; they are different label sets.
- No authenticated organizer receipt for 0.2778, 0.3195, 0.4413, or 0.3774.
- No private registry exemption: dense continuous prior (17GEMSDOE E-proba-multiscale
  20260930T044527Z, SHA256 `ab0a0a62…`, 5 167 373 positives) covers entire footprint,
  so literal forward overlap is 1.0 for any nonempty candidate. Two-phase reading
  (DENSE_SUPPORT_FRACTION=0.20) separates rank correlation (surface) from 3-px
  dot overlap (dot fields); literal firing is reported for completeness.

## Next steps (priority)

1. Fetch full registry (GH API) outside rate-limit, measure like-for-like overlap
   vs H33/H27 sparse fields with `uniqueness.compare_array_to_registry` both ways.
2. Relax catalogue pruning 3 px → 2 px to improve withheld recovery without
   sacrificing emission efficiency; re-evaluate HOLDOUT-DTI.
3. Add conductivity (`cond_surf` band 17) and GeoDAWN radiometrics (external)
   for alteration halo (hypothesis 5) if licensed; verify via `scripts/fetch_data.py`.
4. Test basement-ramp endpoint operator (hypothesis 3) on distinct folds.
5. Obtain weekly-slot confirmation and organizer receipt before claiming any
   ORGANIZER-CONFIRMED score; weekly cap not guessed.
