# Session-2 lane (arena/9a895360) — findings

**Artifact:** `docs/downloads/gems70-fusion-dotted-37654-20261020.tif` — **DO NOT SUBMIT**
(inventoried in `registry/published_artifacts.json`; card: `evidence/s2_run_card.json`).

- **Why 0.2778 (H33):** SHA-verified pruning ladder 44,090 → 40,199 (>1 px) → 37,654
  (>2 px) off-catalogue dots; under α=0.2/β=0.8/300 m DTI, deleting catalogue-hugging
  dots is emission-efficiency gain. No organizer receipt in-repo; nothing claimed beaten.
- **Exp 2 (H70-2A, seed 702):** 36-feature OOF HGB + corroboration gate. Candidate
  HOLDOUT-DTI 0.07829; gate significantly hurt (NoGate 0.08854, Δ −0.01025 CI<0). Negative.
- **Exp 3 (H70-3A, seed 703, untouched):** rank-geomean fusion HGB × GEMSDOE49-architecture
  detector. 0.09161 [0.07489, 0.11106] — best estimate, but paired CIs vs RawHGB
  (+0.0078 [−0.0006, +0.0162]) and vs G49-arch (+0.0090 [−0.0011, +0.0189]) cross zero.
- **Uniqueness (940 rasters):** |ρ| ≤ 0.121, Jaccard ≤ 0.055, yet 0.896 of dots within
  3 px of GEMSDOE49's own dots (> 0.70): fusing with a parent detector is lane drift at
  kernel scale. Literal reading also saturated by continuous/lattice priors.
- **Verdict: negative on both gates; zero slots used.** Preregistrations:
  `docs/s2-hypotheses.md`, `docs/hypotheses-exp3.md`. Method: `src/gems70/method_s2.py`.
  (At run time the method lived at `src/gems70/method2.py`; renamed on merge because
  main's E2/E3 lane owns that path — content unchanged.)
