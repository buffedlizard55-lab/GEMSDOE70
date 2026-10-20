# Why the archived H33 field scored 0.2778 — and what it takes to beat it

**Evidence class:** DATA-MEASUREMENT of the archived bytes, plus user-supplied historical scores.
The 0.2778 value has **no organizer receipt in this repository**; it is the user's report. Nothing
below converts it into an ORGANIZER-CONFIRMED score.

## What the file actually is

`evidence/h33_audit.json` recomputes the archived GeoTIFF byte-for-byte:

| Field | Positive pixels | Measured relation to its predecessor |
|---|---:|---|
| D28 (`dotted-d2-8`) | 44,090 | Poisson 300 m dots, minimum catalogue distance 1 px |
| H27 | 40,199 | exactly the 3,891 D28 dots at **1 px** removed |
| H33 B2 | 37,654 | exactly the 2,545 H27 dots at **√2 or 2 px** removed |

So H33 is not a detector. It is a **uniform sparse sample of the 0.2–3 km halo around the mapped
faults, with the two closest shells deleted**. Nine in ten of its dots lie more than 300 m from any
mapped trace (median 1.97 km).

## Why that scores well — the metric algebra

With `DTI = T / (T + 0.2·(S − M) + 0.8·(N − T))`, where `T` sums a triangular kernel over **truth**
cells, `S` sums the emitted mass and `M` sums each dot's nearest-truth credit:

* `T` saturates at 1 per truth cell; `M` and `S` scale with the number of dots. Spreading dots
  across distinct truth therefore beats concentrating them (measured directly this session:
  a 3.6-px-spaced damage-zone field scored 0.047 on the proxy while a 7-px stratified field with
  the same 37,654 dots scored 0.081).
* A dot closer than ~2 px to a mapped fault buys `S` and almost no `T`, because the scorer masks
  known faults pixel-exactly and the hidden truth does not hug the mapped trace. Deleting those
  shells raised the reported live score twice (0.2708 → 0.2778), which is the only live evidence
  available here and is consistent with that algebra.

The consequence: most of H33's 0.2778 is **emission geometry**, not geological inference. The
residual 0.16 to the 0.44 leader requires knowing *where inside the halo* the new traces are.

## Can this be beaten? What the three experiments say

| Arm (37,654 binary dots) | A: catalogue holdout | B: SGMC proxy | B′: proxy ≥ 3 px |
|---|---:|---:|---:|
| H33 (archived reference) | 0.0037 | 0.0906 | 0.0938 |
| Exp 2: offset × tip × geophysics | 0.0591 | 0.0432 | — |
| Exp 3: damage-zone intensity | 0.0873 | 0.1098 | 0.0471 |
| Exp 4: stratified halo, weak tilt | 0.0730 | 0.0948 | 0.0812 |

Readings:

1. **Instrument A is the wrong instrument for this task.** It withholds catalogue segments, so it
   rewards placing dots beside mapped traces — the opposite of what the competition asks. Every
   candidate beats H33 there by 20×, which says nothing about the leaderboard.
2. **Instrument B is contaminated at short range.** 12.5 % of SGMC-only pixels sit within 2 px of
   the catalogue and 21.4 % within 3 px (7.5 % of the domain is that close). Those are largely the
   same traces re-drawn, so B rewards exactly the band the live experiments penalised.
3. **B′ removes that band.** There H33 still wins by 13 % (Δ = −0.0126, 95 % CI [−0.0241, −0.0018]).
   That is the honest negative and the reason this session's candidate is not promoted.

## The defensible route to >0.2778

The remaining headroom is *within-halo ranking*: a supervised model trained on the only population
that resembles the hidden truth has to be built, not invented from geometry. Concretely, the next
session should (a) train on the SGMC-off-catalogue proxy with leave-one-quadrant-out and a proper
featurisation of the 19-band stack plus lidar-scarp and radiometric layers, (b) keep the coverage
stratification that this session measured to be worth +70 % on B′ at fixed mass
(0.047 → 0.081), and (c) spend one slot on the resulting file. Geometry alone has been measured to
its limit here; the leaderboard gap is information, not spacing.

## What we will not do

Rescale, jitter, rename or prune H33 and call it a new prediction. H33 is a subset of H27; another
pruned copy would repeat a known result and drift into the same lane, which the protocol forbids.

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
