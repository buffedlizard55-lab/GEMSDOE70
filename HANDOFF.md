# Handoff — 2026-10-20 (E2/E3 session)

Read README.md, PROJECT_BRIEF.md, AGENTS.md, docs/preregistration-e2.md first.

**DO NOT SUBMIT YET. Unique candidate exists for selector review; verdict negative.**

Candidate: `docs/downloads/gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif`
SHA-256 `91f3dac071a87dc6258b907f5971987b2a8cf0f94e45e008badd8e09522c9d6c`, 38,000 dots,
name `GEMSDOE70-E2-alluvial-step-38000`. Local validator PASS (all-finite [0,1],
EPSG:32611 3730x3292, 0 on catalogue). No slot used; no organizer score exists.

Two preregistered experiments ran (budget used: 2 of max 3 this session; ~2 min compute each):
E2 alluvial step HOLDOUT-DTI 0.06465 [0.04869,0.08181] (11,321 withheld, gems57-pooled-hide-v2)
beats random/ablations, loses to D28 0.09192 → promotion bars failed. E3 depth-step null
(AUC 0.506) → negative. E1 archived negative unchanged. Do not rerun/tune any of them
(manifests refuse; folds are reported).

Uniqueness: 7-raster subset under explicit revision R1 (docs/protocol-revision-uniqueness.md).
Final dots worst rho 0.039, worst R1 overlap 0.443; literal dense overlap 1.0 published as
degenerate. Complete 862-raster scan + R1 acknowledgment + weekly-cap check + written
acceptance are selector prerequisites (docs/publication-amendment-e2.md, submission guide).
Upstream _dots issue filing denied by integration; report in evidence/, not claimed filed.

Key calibration: on this catalogue instrument H33 (user-reported live 0.2778) scores 0.00370,
below random. Catalogue holdout must not rank far-field fields for live value either way.
Public leader read 2026-10-20: 0.4413 (evidence/leaderboard_read.json). Two-round label
composition and known-fault masking remain unverified — see H33 addendum before any slot.

Next session priorities: (1) selector completes full R1 scan or rejects candidate in writing;
(2) resolve masking/final-round ambiguity from organizer text/forum before spending;
(3) new ranking must raise top-mass credit density (beat D28 on catalogue recovery AND retain
far-field placement) — do not chase holdout with catalogue-hugging supervised fits;
(4) ComCat microseismicity lane needs an out-of-sandbox fetch (named in preregistration).

Commands: venv + requirements.lock; bash scripts/download_competition_data.sh;
.venv/bin/python scripts/build_site.py; scripts/build_readme.py; pytest -q;
scripts/validate_submission.py <candidate.tif>.
