# Handoff — 2026-10-20 (E3 candidate released to selector)

Read README.md and PROJECT_BRIEF.md at session start.

**CANDIDATE READY FOR SELECTOR. Not uploaded. No organizer score.**

- File: `docs/downloads/gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif`
  (+ one-TIF ZIP), SHA-256 in `evidence/run_card_e3_amended.json`.
- Note (107 chars): in run card / site banner. All-finite binary float32 [0,1];
  independent validator PASS (`evidence/validator_independent_e3.json`).
- Evidence: HOLDOUT-DTI 0.0943 [0.0782, 0.1109], 11,437 withheld,
  `gems57-pooled-hide-v2`, seed-40 folds; beats matched random (paired CI
  excludes 0). **Not a live-score prediction** — H33 scores 0.0043 on E2
  catalogue-recovery folds; holdout only falsifies weak rankings.
- Uniqueness: 63 hash-verified rasters; vs H33 forward 0.342 / Jaccard 0.0142 /
  Spearman 0.0198. Literal gate fires on 5 saturating covering fields
  (certificates in evidence). **Selector must complete the 862-raster scan**
  and weekly-cap check before any upload; capture the organizer receipt.

## History (3/3 experiments spent — do not rerun or tune)

E1 magnetic termination (negative, archived `evidence/history/e1-…`);
E2 scarp×strain×cover (negative, gates falsified); E3 scarp alone (promote).
Frozen drivers refuse reruns via manifests. E3 release used the disclosed
erratum completion (`scripts/complete_e3_release.py`, SHA-verified surface
reproduction; original negative card preserved). `vendor/gems57` untouched.

## Data restoration (this sandbox)

`gh` token was invalid and the GitHub contents API rate-limited; data were
restored by git sparse checkout instead (`.cache/src/g0` GEMSDOE@c0c06ac
feature parts → `.cache/data/training_features.tif` SHA `4371c82e…`;
`.cache/src/g60` registry rasters; `.cache/src/g17` dense witness). `.cache/`
is gitignored and reconstructible; committed site copy of the TIF is canonical
for download. `scripts/download_competition_data.sh` (gh path) still works
where gh is authenticated.

## Next session (fresh preregistration + untouched folds required)

1. Selector: full-registry scan → slot decision → upload → file receipt as
   ORGANIZER-CONFIRMED (or record rejection). Never guess the cap.
2. If a new experiment budget is granted: 38–45k scarp variant (E3 picked the
   60k grid edge; curve flattening) and/or USGS 3DEP 1 m refinement inside E3
   corridors; add an off-catalogue proxy-truth instrument alongside catalogue
   recovery. Do not tune E3 on seed-40 folds.
3. Upstream: halo-coverage uniqueness classification report is in
   `evidence/upstream_uniqueness_report_e3.md` (not filed cross-repo).

## Commands

```
python -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/validate_submission.py docs/downloads/gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif
.venv/bin/python scripts/build_submission.py   # status only; exit 0 = candidate intact
```

Pages serves from `main:/` (legacy); `_config.yml` exclusions + E3 guards keep
only the released docs/downloads TIF/ZIP public. Do not restore root `.nojekyll`.
