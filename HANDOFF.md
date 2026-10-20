# Handoff — 2026-10-20 (Session 2)

Read README.md and PROJECT_BRIEF.md at session start.

**NEGATIVE. DO NOT SUBMIT. A unique research TIFF exists; it failed both gates.**

## What was delivered

- **Unique TIFF (research download only):** `docs/downloads/gems70-fusion-dotted-37654-20261020.tif`
  (+ one-TIFF `.zip` + validator JSON), 37,654 dots >2 px off catalogue, written once by
  `scripts/build_submission3.py` through the shared `vendor/gems57` writer; validator PASS on
  exact bytes; SHA-256 bound in `evidence/run_card.json`. The site banner says
  **DO NOT SUBMIT — research download only** in exactly those terms.
- **Why 0.2778 happened:** H33 = 44,090-dot field pruned to 37,654 by catalogue distance
  (SHA-verified, `evidence/h33_audit.json`); under α=0.2/β=0.8/300 m DTI, deleting
  catalogue-hugging dots is pure emission-efficiency gain. No organizer receipt exists here
  for 0.2778 or any leaderboard value; none is claimed beaten.

## Experiments (3/3 budget exhausted — do not rerun or tune on spent blocks)

| Exp | Design | Holdout (evaluator gems57-pooled-hide-v2) | Verdict |
|---|---|---|---|
| 1 (archived) | Magnetic contact termination, unsupervised | 0.010193 [0.006062, 0.015042], 11,321 px, seed 20 | negative |
| 2 H70-2A | 36-feature OOF HGB + corroboration gate + road factor, dotted | candidate 0.078290 [0.060545, 0.095591], 11,358 px, seed 702; gate hurt (NoGate 0.088542, Δ −0.01025 CI<0) | negative |
| 3 H70-3A | Rank-geomean fusion: raw HGB × GEMSDOE49-architecture detector | candidate 0.091610 [0.074890, 0.111060], 11,520 px, seed 703 (untouched); Δ vs RawHGB +0.00780 [−0.00057, +0.01621], Δ vs G49-arch +0.00895 [−0.00113, +0.01894] | negative (CI gate) |

Canaries passed in every experiment (max feature |AUC−0.5| ≤ 0.125). Exp-2 runner OOM-crashed
twice pre-results at the 3.8 GB ceiling; crashed manifests archived, identical-science rerun.

## Uniqueness (940 SHA-verified rasters, 71 repos + quarantined H70-C)

Final dots: worst |Spearman| 0.121, exact-cell Jaccard ≤ 0.055 — but **0.896 of dots within
3 px of GEMSDOE49's own 40k dots (> 0.70 limit)**: fusion with a parent detector is lane
drift at kernel scale. Literal reading also saturated by continuous/lattice priors (Exp-1
certificate). Both readings published in `evidence/uniqueness3.json`; thresholds unchanged.

## Hard rules for next session

1. Do not submit the Exp-3 TIFF; do not delete experiment manifests to rerun/tune spent seeds (20/702/703).
2. New science needs a fresh preregistration, untouched blocks, and a ranking demonstrably
   >3 px-distinct from parent detector families (checked on the surface before placement).
3. `vendor/gems57` remains byte-identical. Data restore is codeload-based (0 REST calls):
   `bash scripts/download_competition_data.sh`; registry resync: `scripts/sync_full_registry.py`.
4. Weekly-slot selection is a separate step; zero slots used. Only an organizer receipt
   creates an ORGANIZER-CONFIRMED score.

Commands: `bash scripts/download_competition_data.sh` · `.venv/bin/python scripts/build_site.py` ·
`.venv/bin/python scripts/build_readme.py` · `.venv/bin/python -m pytest -q`
