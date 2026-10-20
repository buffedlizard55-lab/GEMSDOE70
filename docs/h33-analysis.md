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

## Phase 5 update — how much headroom is left, with the assumptions written out

Two live points from the same family constrain the hidden-truth size. H27 (40,199 dots,
including the 1 px shell) scored **0.2708**; H33 (37,654 dots, the 1 px and sqrt(2)/2 px shells
deleted) scored **0.2778**. If the deleted 2,545 dots carried ~0 kernel credit against the hidden
truth, then `DTI = T/D` with `D = 0.2*(T + n - M) + 0.8*|G|` gives `D2 = 19,690`, `T = 5,470`,
and `0.8*|G| = 6,690 + 0.2*M`. With `M` (dots with non-zero truth credit) of order 1,500, the
implied hidden truth is `|G| ~ 8,700 px` (870 km of new trace) and H33 recalls ~63 % of it.
**This is a back-of-envelope estimate with two assumptions (k = 0 for the deleted shells,
M ~ 1,500); it is not a measurement and must not be quoted as a score.**

The marginal rule for adding a non-redundant dot is `k > alpha * DTI = 0.2 * 0.2778 = 0.056`.
A random dot in the 0.2-3.2 km halo earns roughly 0.1-0.2 expected kernel credit, so H33's
*density* is close to optimal; adding 37,000 more dots raises `T` by less than it raises the
`0.2*(n - M)` term. The open lever is therefore not more dots but **better-ranked dots**: with the
same 37,654 dots, raising `T` from 5,470 to ~8,700 (covering the truth that is already inside the
halo) would put the score near 0.44 — exactly the leader's public value. That is an arithmetic
target, not a result.

Phase 5 acts on this: it keeps H33's halo geometry and dot count and replaces the uniform draw
with an out-of-fold ranker. On the halo surrogate (instrument C) the emission scores 0.1472
against H33's 0.0952 and P4's 0.1177, paired delta +0.0520 [+0.0398, +0.0639]. Whether that
ranking transfers to the hidden truth is the one thing this repository cannot test; the live
receipt is the test.
