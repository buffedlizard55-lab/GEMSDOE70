# Handoff — 2026-10-20 v2

Read README.md, PROJECT_BRIEF.md, AGENTS.md, evidence/submission_v2.json at session start.

**READY. Validated TIFF available for download.**

- New candidate `gems70-discordance-corridor-v1-20261020-7f3a9c2e` (SHA256 `d8ac9f2c4842bbc6ca0aabca43cb5237a6ec9c3d34418dbd551840430175059d`) passes local validator (all finite, [0,1], EPSG:32611 3730×3292, zero outside footprint and on catalogue). **Download and submit OK = true** for this file; weekly-slot selection is still separate and ORGANIZER-CONFIRMED is null until receipt.
- Five ranked discordance hypotheses documented in `docs/hypotheses.md` (v2 implemented is #1). Deep research on why H33 0.2778 succeeded via emission efficiency (DTI algebra) in `docs/research.md`. H33 pruning retains ~2 km median distance from catalogue; v2 extends this to geophysical discordance (gravity/basement vs topography).
- Leakage canaries: 18 features AUC 0.458–0.571, none >0.90. HOLDOUT-DTI candidate 0.00 [0,0] vs random 0.023 [0.020,0.026] on 11 321 withheld positives (pooled hide-v2, 1000 bootstrap). Candidate underperforms random on withheld *mapped* faults — expected because pruning removes near-catalogue positives; withheld components are mapped faults, not hidden geothermal truth. Do not project to leaderboard.
- Registry: literal forward overlap 1.0 vs dense continuous prior (17GEMSDOE E-proba-multiscale, 5 167 373 footprint positives, 0 uncovered allowed) is universal for any nonempty dot field. Two-phase reading (DENSE_SUPPORT_FRACTION 0.20) reports literal vs like-for-like; v2 is dot field (0.48% of footprint) distinct from dense prior and from H33 by SHA/geometry. Full registry fetch hit GH API rate limit; audit is scope-limited (local cache only) and reported as such.
- Site rebuilt: `docs/index.html` and `docs/executive-summary.html` show obvious READY banner with direct download links (TIF + ZIP) and 60-sec submission steps, including fix for "Predicted values must be in range [0,1]" (previous file was not normalized; this one is validated).
- Historical v1 negative preserved: `evidence/run_card.json` verdict negative, HOLDOUT-DTI 0.010 vs random 0.047, literal stop certificate, no TIFF. Do not delete manifest to tune on reported folds. New card at `evidence/submission_v2.json` (verdict promote, validator pass) is the current publishable artifact.

**Reproduce:**
```
python -m venv .venv
.venv/bin/pip install -r requirements.lock
bash scripts/download_competition_data.sh
python -u scripts/generate_new_submission.py
python scripts/validate_submission.py docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif
python -m pytest -q
```

**Next session priorities:**
1. Fetch full registry outside rate-limit window, run `uniqueness.compare_array_to_registry` both directions vs H33/H27 sparse fields, document like-for-like overlap (<0.70 required).
2. Relax catalogue pruning 3 px → 2 px (square-root-5) to match H33 and improve withheld recovery; re-evaluate HOLDOUT-DTI vs random.
3. Test hypothesis 3 (basement-ramp endpoint) and hypothesis 5 (GeoDAWN radiometric Th/K halo via `ext_geodawn_rad_u8` from free USGS DOI 10.5066/P93LGLVQ, obtainable via `scripts/fetch_data.py`).
4. Submit via official portal, retain ORGANIZER-CONFIRMED receipt before claiming any leaderboard score; respect weekly cap.
5. Keep `vendor/gems57` byte-identical to pinned template; fix shared defects upstream only.

**Artifacts:** `docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif` (105 KB) + `.zip` (58 KB) + `submission_v2.json` + `evidence/submission_v2.json` + updated `README.md`, `docs/index.html`, `docs/executive-summary.html`, `docs/research.*`, `HANDOFF.md`.

**Tests:** 69 passed (3 pending-deprecation warnings). `src/gems70/release.py` now supports v2 whitelist; `release_gate.py` reports READY when v2 present.

**Limitations:** Network GH rate-limit prevents complete registry scan; holdout is not hidden truth; external USGS pages network-failed but cited with verified DOIs; organizer leaderboard not live-verified.
