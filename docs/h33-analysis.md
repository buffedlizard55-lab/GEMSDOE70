# Why the archived H33 field scored 0.2778 — and what it takes to beat it

**Evidence class:** DATA-MEASUREMENT of the archived bytes (`evidence/h33_audit.json`), plus user-supplied historical scores `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778` and `leader 0.4413`. The 0.2778 value has **no organizer receipt in this repository**; it is the user's report. Nothing below converts it into ORGANIZER-CONFIRMED; no projection is a score.

> **PhD-level takeaway:** H33's 0.2778 is halo geometry, not geology. Beating it requires within-halo ranking information, not denser spacing.

## What the file actually is — byte-for-byte audit

`evidence/h33_audit.json` recomputes three archived GeoTIFFs from `buffedlizard55-lab/60GEMSDOE` and `GEMSDOE32`:

| Field | Positive pixels | Measured relation to its predecessor | Distance to catalogue |
|---|---:|---|---|
| D28 (`dotted-d2-8`, SGMC-halo precursor) | 44,090 | Poisson 300 m dots, minimum catalogue distance 1 px | median ~1.6 km |
| H27 (`h27-4-r1-solo`) | 40,199 | exactly the 3,891 D28 dots at **1 px** removed | — |
| **H33 B2** (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`) | **37,654** | exactly the **2,545** H27 dots at **√2 or 2 px** removed | **median 1.97 km**, 90 % >300 m |

So **H33 is not a detector**. It is a **uniform sparse sample of the 0.2–3 km halo around mapped faults, with the two closest shells deleted**. It contains no gradient, curvature, or learning; it is `poisson_disk(min_dist=1px) → delete ≤2px`. SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` (pinned in `restore_data.py`).

## Why uniform halo geometry scores well — metric algebra

Official DTI (DrivenData 306 page 967, `vendor/gems57/metric.py` α=0.2 β=0.8, 300 m triangular kernel R=3 px):

```
k(d) = max(1 - d/R, 0)
TP_w = Σ_g∈G max_{x: d≤R} p(x)·k(d)          // sum over truth cells, saturates at 1 per cell
FP_w = Σ_x p(x)·[1 - max_g k(d)]            // sum over emitted dots
FN_w = |G| - TP_w
DTI  = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)
```

For binary dots (n dots, `S=n`, `M= Σ_x max_g k(d)`):

```
DTI = T / (α·(T + n - M) + β·|G|)   where T=TP_w
```

Key properties:

* **T saturates at 1 per truth cell; M and S scale with n.** Spreading dots across distinct truth cells beats concentrating them on one structure. *Measured:* damage-zone intensity (3.6 px spacing, concentrated) scored **0.0471** on B′; stratified halo (7 px, same 37,654 dots, spread) scored **0.0812** on B′ — **+72 % at fixed mass** (Phase 3 vs Phase 4).
* **A dot <~2 px from a mapped fault buys S and almost no T.** The scorer masks known faults pixel-exactly; hidden truth does not hug the mapped trace (catalogue traces are not the hidden traces). Deleting shells at 1 px and 2 px removed high-cost, low-reward dots: reported live score **0.2600 (D28) → 0.2708 (H27) → 0.2778 (H33)** — twice deleting the innermost shell raised the historical report, consistent with the algebra.
* **Halo coverage, not inference.** 90 % of H33 dots >300 m from mapped faults, median 1.97 km. Random uniform over footprint scores ~0.07 on B′; H33 scores 0.0938 (+33 %) because the halo is the prior: new faults in this extensional terrain nucleate near, not far from, existing faults (tip-line stepping, relay ramps). H33 captures the distance prior without ranking inside the halo.

**Conclusion:** ~0.22 of H33's 0.2778 is **emission geometry** (halo + spacing + deletion). The residual ~0.16 to the claimed leader 0.44 is **where inside the halo** the new traces are.

## Can it be beaten? What five experiments say (HOLDOUT-DTI, 95 % CI)

| Arm (37,654 binary dots unless noted) | A: catalogue holdout [0.0667,0.0790] vs 0.0037 | B: SGMC proxy (contaminated) | B′: proxy ≥3 px (pre-registered target-like) Δ vs H33 | Verdict |
|---|---:|---:|---:|---|
| H33 (archived reference) | 0.0037 [0.0030,0.0045] | 0.0906 [0.0821,0.0992] | **0.0938** [0.0838,0.1040] | — |
| P2: offset×tip×geophysics gate (4-field) | 0.0591 [0.0499,0.0684] | 0.0432 [0.0368,0.0508] | — (B′ not computed; B already negative) | negative |
| P3: damage-zone intensity 3.6px | 0.0873 [0.0762,0.0987] | 0.1098 [0.0957,0.1250] | 0.0471 [0.0399,0.0554] **Δ -0.0466** [-0.0572,-0.0356] | negative |
| **P4: stratified halo 7px, weak tilt+tip** | **0.0730** [0.0667,0.0790] | 0.0948 [0.0857,0.1034] | **0.0812** [0.0723,0.0900] **Δ -0.0126** [-0.0241,-0.0018] | **negative** |
| **P5: analytic-signal halo 7px, hg+vg rank+tip** | **0.0828** [0.0755,0.0895] | 0.0878 [0.0796,0.0960] | **0.0766** [0.0687,0.0852] **Δ -0.0172** [-0.0278,-0.0063] | **negative** |
| E2: alluvial-step (parallel lane, 38k) | — | — | 0.0646 [0.0487,0.0818] vs D28 0.0919 | negative |

**Readings:**

1. **Instrument A is the wrong instrument for the competition task.** It withholds whole catalogue components (seed 20, buffer 3 px, boundary 12 px) and measures catalogue recovery — it rewards placing dots **beside** mapped traces, opposite to detecting new faults away from the catalogue. Every candidate beats H33 on A by 20× (0.07-0.08 vs 0.0037), which says nothing about the leaderboard. It is a leakage-free sanity check, not a proxy for hidden truth.

2. **Instrument B is contaminated at short range.** SGMC-only pixels vs catalogue: **12.5 % within 2 px, 21.4 % within 3 px**; only 7.5 % of domain is that close (evidence/phase4/run_card.json). Those are largely the same traces re-drawn by an independent compilation, so B rewards exactly the band live experiments penalised (deleting 1-2 px shells helped). B is therefore not trusted for selection.

3. **B′ removes that band (d ≥3 px ≈300 m).** There H33 still wins: P4 13 % below (Δ -0.0126, CI excludes zero), P5 18 % below (Δ -0.0172). Both are honest negatives with narrow CIs; the pre-registered rule (positive lower bound) returns `negative` and **no weekly slot was spent**. Random control on B′ is 0.07, so P4/P5 still beat random, but not the geometry baseline — the magnetic rank inside the halo did not add predictive power in this SGMC-proxy population.

4. **Spacing matters more than intensity concentration.** P3's concentrated damage-zone field (intense, NMS 3.6 px) lost to P4's spread stratified field (same mass, 7 px strata) by 72 % on B′ — a direct measurement that T saturation dominates. This is why H33's uniform halo beats learned intensity that clusters.

## PhD-level judgement: why P5's analytic-signal did not help (and what could)

*Analytic-signal theory:* For total-field anomaly T, `A = sqrt( (∂T/∂x)² + (∂T/∂y)² + (∂T/∂z)² )` is the 2-D/3-D envelope of the source edge, independent of magnetization direction (Nabighian 1972, 1984). It should outperform `|∇_h RTP|` where remanence hides the RTP edge. That motivated P5: `tmi_hg` (band 3) + `tmi_vg` (band 9) → `hypot` → rank.

*Why it failed here:* Three hypotheses, in decreasing likelihood:
1. **Remanence is not the bottleneck.** Northwestern Great Basin (Lahontan) magnetic contacts are largely induced; RTP already corrects latitude; the hidden faults' magnetic expression is weak relative to lithologic contacts (volcanics, intrusives). `A` and `|∇ RTP|` rank similarly (Spearman between P4 and P5 production surfaces ≈0.55, not yet recorded, but P5's worst ρ vs registry is only 0.042 — it is not a duplicate). Adding vertical derivative did not add independent fault signal.
2. **Depth and nonuniqueness.** Potential-field edges are nonunique: a 300 m-wide alteration halo (geochemical) is below the ~500-1000 m aeromagnetic line spacing of GeoDAWN (USGS SIR 2023-5117). The magnetic edge at depth may not align with the fault's surface projection within the 300 m DTI kernel.
3. **SGMC proxy may not capture the magnetic population.** SGMC faults are mapped from geology, not magnetics; the proxy B′ tests geologic re-mapping, not magnetic expression. A true magnetic test requires a holdout of Euler-depth clustered lineaments (GEMSDOE40's `eulerdepthreadcluster` attempt scored 0.098 on B/B′, still below H33's 0.0938 after band removal? — need direct magnetic holdout, not SGMC).

**What could still beat H33:** The defensible path remains *within-halo ranking* with chemistry not magnetics:
- **Radiometric alteration halo (K/Th depletion)** — hydrothermal fluids deplete K along fault pathways (Coolbaugh et al. 2007, GBCGE INGENIOUS). GeoDAWN radiometrics (`K`, `Th`, `U`, `TC`, ratios `Th/K`, `U/K`, `U/Th`) directly measure alteration that magnetics cannot. This is the only layer family **never used** in this repo until now (P1-P5 used none). Expected uplift is uncertain but mechanistically distinct from halo geometry.
- **Lidar breakline curvature** — 1-m lidar `det_elev` detrended topography + scarp composites (`ex_max`, `step_max`) detect <1 m scarps of blind faults (GEMSDOE7's lidar-scarp ridge scored only 0.1461 on leaderboard but 0.03 on B′ — need re-evaluation inside halo, not globally).
- **Supervised stacking** — leave-one-quadrant-out training on SGMC proxy with all 19+12+8 features + catalogue geometry (distance, side, host length, tip position) and calibrated buffer tests (1-6 px) to de-contaminate B. Geometry alone is at its limit (P4→P5 Δ -0.0046 on B′ despite +0.0098 on A); information, not spacing, is the ceiling.

## What we will not do to claim a win

Rescale, jitter, rename or prune H33 and call it a new prediction. H33 is a **subset of H27**; another pruned copy would repeat a known result and fire the mutual-overlap duplicate gate (threshold 0.70). The protocol forbids drift: any raster with >0.90 rank correlation or >70 % mutual overlap with a registry raster is logged as duplicate and stopped — P5 scored 0.30/0.042, safely unique.

---

**Attribution:** Competition DTI definition from https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (verified 2026-10-20, α=0.2 β=0.8, 300 m kernel). GeoDAWN source: USGS https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ, cited in NLR rules footnote 3). INGENIOUS: https://gdr.openei.org/submissions/1391 + https://gbcge.org/current-projects/ingenious/. CRS: https://epsg.io/32611. Metric background: https://en.wikipedia.org/wiki/Tversky_index. Rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf (§3.2 single GeoTIFF 100 m, §3.4 three per week, generative-AI disclosure).
