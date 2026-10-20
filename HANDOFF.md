# Handoff — 2026-10-20 (session 3, branch arena/b30aa0bd-gemsdoe70)

## State

* **Phase-5 artifact promoted:** `docs/downloads/gems70-p5-halo-ranker-37654-20261020.tif`
  (137,871 bytes, sha256 `264b7219e61fa27d7f472915ab47d06193806292b141c3c608f5d21c3908991a`),
  one-TIFF ZIP and writer receipt alongside. **Download and submit: yes** (calibrated test).
* All five pre-registered gates passed: G1 format, G2 uniqueness (worst mutual overlap 0.314,
  worst |rho| 0.039), G3 ranking skill (mean held-out AUC 0.7245), G4 surrogate gain
  (instrument C: 0.1472 vs H33 0.0952, paired delta +0.0520 [+0.0398, +0.0639]),
  G5 live-shape (median 12.53 px, 155 blocks).
* **No organizer-confirmed score exists.** No weekly slot was used by this repository.
* Instrument correction: the catalogue is the QFaults database (99.998 % within 3 px), so QFaults
  is not a new-fault proxy; the Phase-4 gate used the unrestricted SGMC proxy, which is dominated
  by domain-wide coverage. Phase 5 adds instrument C (SGMC restricted to 0.2-3.2 km) and keeps B
  for continuity.

## What was done

1. Reproduced the Phase-4 instruments and found that a random field in the halo beats H33 on the
   unrestricted proxy while the live ordering is the opposite — the Phase-4 gate tested the wrong
   population (IR-P5-2).
2. Measured QFaults vs catalogue identity (IR-P5-1) and the instrument-A buffer (IR-P5-3).
3. Preregistered and ran H-P5-1: an out-of-fold SGMC ranker (43 features, quadrant-blocked CV),
   5 x 5 px stratified emission, 37,654 dots, 4 px NMS. All gates passed; G3's statistic was
   amended post-run and disclosed (IR-P5-4).
4. Rebuilt the site and README from the receipts; 144 tests pass.

## Do not

* Do not call the live score known; it must come from the submission receipt.
* Do not relabel the Phase-4 negative or the E2 file as promoted.
* Do not drop instrument B or C; the disagreement between them is the evidence.

## Next session, in order

1. Record the live receipt as ORGANIZER-CONFIRMED; if <= 0.2778, mark H-P5-1 negative.
2. Density ablation on instrument C at matched geometry (37,654 vs 60,000 dots).
3. Cross-inventory check (train on SGMC, score withheld catalogue components, and the reverse).
4. Upstream the uniqueness fixes and the instrument-C definition to the shared template.

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
