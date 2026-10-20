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

## Why that might score well — a metric-based hypothesis

With `DTI = T / (T + 0.2·(S − M) + 0.8·(N − T))`, where `T` sums a triangular kernel over **truth**
cells, `S` sums the emitted mass and `M` sums each dot's nearest-truth credit:

* `T` saturates at 1 per truth cell; `M` and `S` scale with the number of dots. Spreading dots
  across distinct truth therefore beats concentrating them (measured directly this session:
  a 3.6-px-spaced damage-zone field scored 0.047 on the proxy while a 7-px stratified field with
  the same 37,654 dots scored 0.081).
* A dot closer than ~2 px to a mapped fault buys `S` and almost no `T`, under the hypothesis that masking known faults reduces nearby useful credit;
  the hidden-truth spatial distribution is not available for verification. Deleting those
  shells raised the reported live score twice (0.2708 → 0.2778), which is the only live evidence
  available here and is consistent with that algebra.

The audit establishes the emission geometry, not its causal contribution to the reported
result. Neither the hidden-label distribution nor the fraction of performance attributable
to geometry is identified by these experiments.

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
(0.047 → 0.081), and (c) spend one slot on the resulting file. These experiments do not establish a limit on geometry-based methods or identify the
source of any leaderboard gap. No slot is authorized by this suggestion.

## What we will not do

Rescale, jitter, rename or prune H33 and call it a new prediction. H33 is a subset of H27; another
pruned copy would repeat a known result and drift into the same lane, which the protocol forbids.
