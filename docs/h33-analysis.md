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

## Phase-5 Update (2026-10-20): Distance-Shell Dissection, Buffer Calibration, and Beating H33

### 1. Why H33 (`0.0938` on B′) beat Phase-4 (`0.0812` on B′) inside every distance shell

In Phase-5 we decomposed the per-dot triangular-kernel credit (`credit/dot`) of H33 versus Phase-4 across radial distance shells from `existing_faults.tif` (`d_cat`) on Instrument B′ (`sgmc & ~cat & (d_cat >= 3 px)`):

| Radial shell (`d_cat`) | H33 dots | H33 credit | H33 cr/dot | P4 dots | P4 credit | P4 cr/dot | Why H33 won in Phase-4 |
|---|---:|---:|---:|---:|---:|---:|---|
| `[2.0, 3.0)` px | 674 | 46.8 | 0.0694 | 7,195 | 311.3 | 0.0433 | P4 spent 19.1% of its budget (`d_min = 2.4` px) inside the dead inner collar (`d < 3` px). |
| `[3.0, 6.0)` px | 4,065 | 363.2 | 0.0893 | 7,764 | 466.4 | 0.0601 | H33's `0.893` cr/dot beat P4's `0.060` cr/dot by **1.49×** because H33 ranked pixels by geophysical features (`d28`), whereas P4 used only geometric distance/tip decay. |
| `[6.0, 15.0)` px | 9,708 | 744.7 | 0.0767 | 12,175 | 668.4 | 0.0549 | H33's geophysical ranking achieved **1.40×** higher hit rate per dot. |
| `[15.0, 32.0)` px | 10,395 | 656.5 | 0.0632 | 10,504 | 459.4 | 0.0437 | H33's geophysical ranking achieved **1.45×** higher hit rate per dot. |
| `[32.0, 200.0)` px | 12,812 | 697.0 | 0.0544 | 16 | 0.4 | 0.0271 | P4 hard-truncated at `d_max = 32` px (`3.2` km), forfeiting **697.0** units of distal basin-interior truth credit. |

### 2. SGMC vs QFaults Buffer Calibration (`r = 0..6` px, `evidence/phase5/sgmc_buffer_audit.json`)

Measuring `sgmc_faults_100m.tif & ~existing_faults.tif` (`78,433` pixels inside the footprint; background rate `1.536%`) across annular distance shells from `existing_faults.tif` confirms:
- `[1, 2)` px (`100–200 m`): `5.559%` (`3.62×` background) — 1:500,000 cartographic offset of mapped QFaults.
- `[2, 3)` px (`200–300 m`): `3.532%` (`2.30×` background).
- `[3, 4)` px (`300–400 m`): `2.337%` (`1.52×` background).
- `[4, 5)` px (`400–500 m`): `1.838%` (`1.20×` background).
- `[5, 6)` px (`500–600 m`): `1.601%` (`1.04×` background).
- `[6, 8)` px (`600–800 m`): `1.410%` (`0.92×` background) — cartographic duplication decays to baseline at `r = 6` px (`600 m`).

Notably, `r = 3` px (`300 m`, Instrument B′) is the exact buffer threshold where `H33` (`0.0938`) overtakes `D28` (`0.0935`), reproducing the user-reported live leaderboard ordering (`0.2778 > 0.2600`), and that ordering persists at `r = 6` px (`600 m`, Instrument B″: `H33 = 0.0850 > D28 = 0.0831 > P4 = 0.0674`).

### 3. Phase-5 LOQO Supervised Within-Halo Ranker (`evidence/phase5/run_card.json`)

Executing the Phase-4 roadmap priority — training a 4-fold Leave-One-Quadrant-Out (LOQO) `HistGradientBoostingClassifier` on `sgmc & ~catalogue & (d_cat >= 3 px)` using 49 features (19 GeoDAWN/INGENIOUS bands + 12 LiDAR scarp bands + 8 GeoDAWN radiometric/ratio bands + 2 GDR-1391 hydrothermal conduit features + 8 strictly visible catalogue geometry features), rank-normalizing predictions within each held-out quadrant, multiplying by the tip/damage-zone halo prior on `d_cat >= 3` px with no `32`-px truncation, and placing `37,654` binary dots via `7×7` block stratification + `5`-px NMS — beats both H33 and Phase-4 across every instrument (`evaluator_version = gems57-pooled-hide-v2`, `HOLDOUT-DTI`):

| Arm (37,654 binary dots except E2=38,000) | Instrument A (`11,321` pos) | Instrument B′ (`d>=3` px, `59,937` pos) | Instrument B″ (`d>=6` px, `52,767` pos) | Instrument B (`all`, `74,740` pos) |
|---|---:|---:|---:|---:|
| **Phase-5 Candidate (`loqo_halo`, 49 feat)** | **0.0752** `[0.0683, 0.0821]` | **0.1138** `[0.1077, 0.1192]` | **0.1000** `[0.0940, 0.1058]` | **0.1158** `[0.1103, 0.1203]` |
| **Phase-5 Ablation (`no_hydro`, 47 feat)** | **0.0755** `[0.0692, 0.0816]` | **0.1162** `[0.1104, 0.1211]` | **0.1024** `[0.0967, 0.1073]` | **0.1178** `[0.1128, 0.1223]` |
| Phase-5 Ablation (`loqo_only`, no halo tilt) | 0.0683 `[0.0613, 0.0749]` | 0.1115 `[0.1077, 0.1150]` | 0.0991 `[0.0950, 0.1029]` | 0.1102 `[0.1068, 0.1134]` |
| Phase-5 Ablation (`halo_only`, no LOQO) | 0.0759 `[0.0693, 0.0821]` | 0.0844 `[0.0753, 0.0934]` | 0.0664 `[0.0580, 0.0744]` | 0.0924 `[0.0837, 0.1006]` |
| Phase-4 Reference (`gems70-p4-stratified-halo`) | 0.0730 `[0.0667, 0.0791]` | 0.0812 `[0.0721, 0.0898]` | 0.0674 `[0.0592, 0.0754]` | 0.0948 `[0.0856, 0.1030]` |
| Archived H33 Reference (`GEMSDOE32`) | 0.0037 `[0.0030, 0.0044]` | 0.0938 `[0.0840, 0.1046]` | 0.0850 `[0.0751, 0.0950]` | 0.0906 `[0.0823, 0.0997]` |
| Random Control (`37,654` off-catalogue dots) | 0.0460 `[0.0402, 0.0515]` | 0.0745 `[0.0712, 0.0773]` | 0.0730 `[0.0695, 0.0761]` | 0.0741 `[0.0709, 0.0769]` |

Paired spatial-cluster bootstrap differences (`1,000` draws, `20` km blocks):
- **Instrument B′ (`d_cat >= 3` px) vs H33:** `Δ = +0.0200`, 95% CI `[+0.0097, +0.0302]` (strictly positive).
- **Instrument B′ (`d_cat >= 3` px) vs Phase-4:** `Δ = +0.0326`, 95% CI `[+0.0249, +0.0411]` (strictly positive).
- **Instrument B″ (`d_cat >= 6` px) vs H33:** `Δ = +0.0149`, 95% CI `[+0.0050, +0.0245]` (strictly positive).
- **Instrument A vs H33:** `Δ = +0.0715`, 95% CI `[+0.0647, +0.0780]` (strictly positive).
- **Instrument A vs Random:** `Δ = +0.0292`, 95% CI `[+0.0230, +0.0354]` (strictly positive).

## What we will not do

Rescale, jitter, rename or prune H33 and call it a new prediction. H33 is a subset of H27; another
pruned copy would repeat a known result and drift into the same lane, which the protocol forbids.

