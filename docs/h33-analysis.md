# H33 archive: what the bytes show, what the reported 0.2778 cannot prove

**DO NOT SUBMIT the historical H33/P4 field as a new entry.** The 0.2778 associated with `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` is user-supplied historical information. Neither this checkout nor the [GEMSDOE32 site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) contains an authenticated *submission-page receipt* binding that exact TIFF to an organizer score; the source site labels its primary "UNSCORED" and describes a model projection. The [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) cannot identify which filename produced a team's row. **No ORGANIZER-CONFIRMED file-specific value is claimed.**

## Recomputed artifact ancestry (DATA-MEASUREMENT, not a score)

The [byte-pinned audit](downloads/h33_audit.json) compares three archived single-band TIFFs against the sample grid and mapped catalogue. Source paths and SHA-256 digests appear in that receipt; the [H33 historical owner-archive file](https://github.com/buffedlizard55-lab/60GEMSDOE/blob/32024716f218d06a94e01464157392119c03cb15/registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif) is not an organizer account receipt.

| Field | Positive binary pixels | Change, directly measured from TIFF bytes |
|---|---:|---|
| D28 | 44,090 | Earlier Poisson-style dots |
| H27 | 40,199 | No new pixels; exactly 3,891 D28 dots at a 1-pixel distance to mapped faults removed |
| H33 B2 | 37,654 | No new pixels; exactly 2,545 H27 dots at √2 or 2-pixel distance removed |

The H33 mask has zero pixels on mapped faults, minimum catalogue distance √5 pixels, and 5.77% of its dots within 300 m of mapped traces (median distance about 1.96 km). It is a **pruned subset** of prior emissions, not a new geophysical detector. The source page calls the B2 step "flank B=2 prune". These are on-disk relationships, not evidence that a vent, active fault, or novel resource was discovered.

## Causal hypothesis from the official metric — not proof of the live outcome

The [official problem and formula](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) define a distance-weighted Tversky index, α=0.2, β=0.8, triangular kernel to 300 m. For a binary dot set, let **T** be the sum of best kernel coverages over *truth cells*; **S** the prediction mass (dot count); **M** the sum of each dot's nearest-truth kernel credit; and **K** the number of truth cells. Then the published terms imply

`DTI = T / [0.2·(T + S − M) + 0.8·K + ε]`.

`T` saturates per truth cell, but prediction mass `S` grows with every dot. Removing redundant mass can reduce false-positive cost without much reduction of `T`, so catalogue-near pruning **could** account for a higher reported value *if* expert-labeled new faults mostly lie away from those deleted dots. Removing useful dots could instead hurt recall. Without hidden truth and a receipt, this conditional mechanism is not a causal attribution for 0.2778.

The often-quoted marginal bar `k > α × DTI` is valid **only for a nonredundant dot whose added truth credit equals its own nearest-truth credit**. In general, adding a dot with marginal truth credit ΔT and self-credit k helps iff `ΔT > α·DTI·(ΔT + 1 − k)`; one dot may cover several truth cells. Neither unthinned mass nor indiscriminate pruning is guaranteed optimal. Catalogue hide-and-recover rewards proximity to *withheld mapped faults*; the contest's initial private test consists of *new expert-mapped faults*. Do not project a holdout result as an organizer score.

## Can a distinct method beat the historical report?

**Scientifically possible, not established here.** The [dated public leaderboard read](downloads/leaderboard_read.json) showed a top public observation of 0.4413 on 2026-10-20, but it does not identify an H33-file score. The current run has no new held-out candidate, and its three older archived TIFFs fail the user's **forward** registry-overlap rule against a pinned binary lattice ([recomputed stop](downloads/literal_overlap_stop.json)). A new upload or forecast to exceed 0.2778 would be unjustified. Improving discovery likely requires independent, physically corroborated *within-region ranking*, with nuisance-process controls and newly blocked hide-and-recover plus an independent off-catalogue proxy, rather than copying H33 or only moving its dots. Four untested and cost-ranked proposals are [here](hypotheses-next.html). The [executive summary](executive-summary.html) explains why no file is currently cleared.
