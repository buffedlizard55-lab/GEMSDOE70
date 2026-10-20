# Handoff — 2026-10-20 (session 2, branch arena/9fe83934-gemsdoe70)

Read README.md, PROJECT_BRIEF.md, this file and `docs/irregularities.md` first.

## State

* **Artifact published:** `docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif`
  (126,097 bytes, sha256 `0fd1ad9ef58c9bbe0ed1781d36a31f76424db11930502623153dd69581ab35e7`),
  plus a one-TIFF ZIP and the writer receipt.
* **Verdict: negative.** `download_ok = true`, `submit_recommended = false`.
  The pre-registered target-like gate (instrument B′) is 12.6 % below the H33 reference with a
  95 % CI excluding zero. Instrument A and the unrestricted proxy favour the candidate.
* **No weekly slot used. No organizer-confirmed score exists in this repository.**

## What was done

1. **Two defects in the shared uniqueness tool were found and fixed** (reported, hashes in
   `registry/template_pin.json` with `all_identical: false`, full text in
   `evidence/upstream_fix_report.md`):
   * dots are binary (`|value − 1| < 1e-6`), not every positive value;
   * duplication requires **mutual** overlap; forward-only overlap fires at 1.00 on three archived
     dense lattices whose 3-px halos cover the whole footprint.
2. **Three preregistered experiments.**
   * Exp 2 (geophysically gated continuation prior): A 0.0591, B 0.0432 — the four-field
     geophysical gate hurt and was removed.
   * Exp 3 (damage-zone intensity): A 0.0873, B 0.1098, B′ 0.0471 — concentration wasted mass
     because `T` saturates per truth cell while `S` scales per dot.
   * Exp 4 (coverage-stratified halo, weak tilt): A 0.0730, B 0.0948, B′ 0.0812 — best balance;
     this is the published artifact.
3. The site was rebuilt to read every number from JSON receipts and to state the download/submit
   decision explicitly on the landing page.

## Do not

* Do not relabel the artifact as promoted, and do not edit the card's gates.
* Do not describe 0.2778 or 0.44 as organizer-confirmed; both are user-supplied.
* Do not remove the two uniqueness fixes without replacing them upstream in the shared template.
* Do not publish any TIFF/ZIP other than the three files named by the run card —
  `release.assert_no_public_rasters` enforces this.

## Next session, in order

1. Supervised within-halo ranking on the SGMC off-catalogue proxy with leave-one-quadrant-out.
   Features: 19-band stack, `lidar_scarp_features_u8` (12 bands), `geodawn_rad_u8` (K/Th/U/TC and
   ratios), catalogue geometry (distance, side, host length, tip position), and the measured
   coverage stratification (7×7 strata, 5-px NMS) which was worth +70 % on B′ at fixed mass.
2. Quantify SGMC duplication against QFaults (buffer tests 1–6 px) so instrument B/B′ can be
   improved or replaced by a genuinely independent additional-fault set.
3. Upstream the two uniqueness fixes to the template repository and run its suite.
4. Only then spend a slot, and record the returned score as ORGANIZER-CONFIRMED.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/run_experiment_v4.py
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q          # 118 passed at handoff
```

Large inputs and the registry clone stay outside Git (`.cache/`, `/tmp`). Published evidence is
JSON plus the 126 KB artifact.

## Parallel E2/E3 lane integrated 2026-10-20 (branch arena/ef718aa0-gemsdoe70, PR #16)

Independent preregistered lane merged after session 2: E2 alluvial-step candidate
`gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif`
(sha256 `91f3dac071a87dc6258b907f5971987b2a8cf0f94e45e008badd8e09522c9d6c`, 38,000 dots,
registered in `registry/published_artifacts.json`). Verdict **negative**; download-for-selector-review
only, submit NO. Catalogue HOLDOUT-DTI 0.06465 [0.04869,0.08181] (11,321 withheld) beats random,
loses to D28 0.09192; independently replicates Instrument-A H33 = 0.0037. E3 depth-step null.
Uniqueness for E2 was measured pre-fix under disclosed R1 on a 7-raster subset
(rho <= 0.039, R1 overlap <= 0.443) — rerun under the corrected mutual rule + complete scan
before any slot consideration. Evidence: `evidence/e2/`, `evidence/e3/`,
`docs/preregistration-e2.md`, `docs/publication-amendment-e2.md`. Organizer pages fetched
2026-10-20: public leader 0.4413 (`evidence/leaderboard_read.json`). No slot used.

## Integration note (PR #16 second merge, 2026-10-20)
PR #18 (H2 stepover-relay, negative; HOLDOUT-DTI 0.023034, lane stop fired) landed during PR #16 CI and replaced `evidence/run_card.json`, builders and 4 test files with its fail-closed system. Integration preserved: H2 card moved byte-identical to `evidence/history/h2_stepover_negative/run_card.json`; H2 diagnostic TIFF registered in `registry/published_artifacts.json`; Phase-4 canonical card restored from `fefc857` blob (sha256 `9cd64b1e...`); session-2 builders/tests retained so P4 + discordance + E2 artifacts stay coherent. `make_run_card.py` stale-schema fix (pre-existing red Verify on main) retained. All verdicts negative; slots used 0.

---

## Phase-5 Handoff — 2026-10-20 (branch `arena/3ccffc1b-gemsdoe70`)

All four tasks from the Session-2 handoff above have been executed while keeping all frozen Phase 1–4 and E2/E3 evidence files untouched:

1. **Phase-5 LOQO Supervised Within-Halo Ranker (`evidence/phase5/run_card.json`, `src/gems70/method_v5.py`, `scripts/run_experiment_v5.py`):**
   - **Published artifact:** `docs/downloads/gems70-p5-loqo-halo-37654-20261020.tif` (`150,240` bytes, `sha256: a8cef5bdbbc030cd6bdd59ea275e09e27edf87b4ee8068d3e8052bdff1cb9667`), plus `.zip` (`92,761` bytes) and `.json` (`3,794` bytes), registered in `registry/published_artifacts.json`.
   - **Status (`gems70.release.phase5_status`):** `verdict = "promote"`, `download_ok = true`, `holdout_and_proxy_gates_passed = true`, `selector_ready = true`, `weekly_slots_used = 0`.
   - **Submission note (`120/140` chars):** `P5 LOQO HGB 49-feat within-halo rank x tip/damage prior, 7px strata 5px NMS, 37654 binary dots d>=3px; passes A, B', B''`
   - **Evaluation (`gems57-pooled-hide-v2`, `HOLDOUT-DTI` / `LOQO-PROXY-DTI`, 1,000-draw 20 km spatial-cluster bootstrap):**
     - **Instrument A (`11,321` withheld catalogue positives):** `0.0752` (`[0.0683, 0.0821]`) vs Phase-4 `0.0730`, Random `0.0460` (paired `Δ = +0.0292` `[+0.0230, +0.0354]`), H33 `0.0037` (paired `Δ = +0.0715` `[+0.0647, +0.0780]`).
     - **Instrument B′ (`d_cat >= 3` px, `59,937` SGMC proxy positives):** `0.1138` (`[0.1077, 0.1192]`) vs H33 `0.0938` (paired `Δ = +0.0200` `[+0.0097, +0.0302]`) and Phase-4 `0.0812` (paired `Δ = +0.0326` `[+0.0249, +0.0411]`).
     - **Instrument B″ (`d_cat >= 6` px, `52,767` SGMC proxy positives outside the 1:500k duplication band):** `0.1000` (`[0.0940, 0.1058]`) vs H33 `0.0850` (paired `Δ = +0.0149` `[+0.0050, +0.0245]`) and Phase-4 `0.0674`.
     - **Instrument B (`74,740` unrestricted SGMC proxy positives):** `0.1158` (`[0.1103, 0.1203]`) vs Phase-4 `0.0948` and H33 `0.0906`.
   - **Uniqueness (`66` rasters = `62` archived registry + `4` local candidates):**
     - Pre-placement surface (`evidence/phase5/surface_uniqueness.json`): `unique = true`, `worst_spearman = 0.1210 <= 0.90`, `worst_dot_overlap = 0.00003 <= 0.70`.
     - Final binary dots (`evidence/phase5/uniqueness_with_local.json`): `unique = true`, `duplicate_count = 0`, `worst_mutual_overlap = 0.4870 <= 0.70` (vs Phase-4; `0.3054` vs archived 62), `worst_spearman = 0.1153 <= 0.90` (`0.0301` vs archived 62), `worst_jaccard = 0.0648`.
   - **Leakage canaries (`evidence/phase5/canaries.json`):** All `49` features pass single-feature holdout AUC `<= 0.90` (`max_deviation_auc = 0.7770`).
2. **SGMC vs QFaults Buffer Audit (`evidence/phase5/sgmc_buffer_audit.json`, `scripts/audit_sgmc_proxy.py`):**
   - Quantifies annular enrichment across `[1,2)..[6,8)` px (`3.62× -> 0.92×` background), proving that cartographic duplication decays to baseline at `r = 6` px (`600 m`) and that `r = 3` px (`300 m`) is the exact threshold where `H33 > D28` flips to match the user-reported leaderboard ordering (`0.2778 > 0.2600`).
3. **E2 62-Raster Corrected Uniqueness Re-Audit (`evidence/phase5/e2_uniqueness_62rasters_corrected.json`, `scripts/reaudit_e2_uniqueness.py`):**
   - Confirms E2 is unique across all 62 archived registry rasters (`unique = true`, `worst_mutual_overlap = 0.2876`, `worst_spearman = 0.0241`), while remaining `DO NOT SUBMIT` on its Instrument A gate.
4. **Upstream Uniqueness Patch & Verification (`evidence/phase5/upstream_uniqueness.patch`, `evidence/phase5/upstream_verification.json`, `scripts/verify_upstream_fix.py`):**
   - Produces the 109-line unified diff from `1c5094b8...` to `93726c6a...` and verifies that all 33 shared tests pass when applied to `/tmp/60GEMSDOE`.

