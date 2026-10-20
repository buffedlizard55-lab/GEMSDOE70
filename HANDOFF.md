# Handoff — 2026-10-20 (session 3, branch arena/9fff0647-gemsdoe70)

Read README.md, PROJECT_BRIEF.md, this file and `docs/irregularities.md` first.

## State

* **Artifact published:** `docs/downloads/gems70-p5-halo-rank-hgb-37654-20261020.tif`
  (150,877 bytes, sha256 `0390166b425dc9238bac4c0ec91a2bf013d91b7ae2597cb43d29f98854b06931`),
  plus a one-TIFF ZIP and the writer receipt. **Verdict: negative.** `download_ok = true`,
  `submit_recommended = false`. No weekly slot used; no organizer-confirmed score exists.

## What was done (experiment 5 = session-3 in-session experiment 1 of 3)

1. **Preregistered H-P5-1** (`docs/hypotheses.md` Phase-5 addendum) *before* the run: supervised
   within-halo ranking — HistGradientBoosting over the 19-band stack + visible-catalogue geometry
   (d, tip u, v), trained on the SGMC off-catalogue proxy (d ≥ 3 px) with leave-one-quadrant-out;
   emission = P4 coverage-stratified design at fixed mass 37,654; arms candidate / random / H33 /
   P4; canaries (A-truth, proxy-label disclosure, OOF); surface Spearman pre-check; mutual-overlap
   final audit; both gates.
2. **Result (negative, informative):** A 0.0822 [0.0745, 0.0902] (random 0.0531); B′ LOQO
   0.0793 [0.0716, 0.0879] vs H33 0.0938 (gate fails, Δ −0.0145) and vs P4 0.0812
   (indistinguishable, Δ −0.0019 CI [−0.0060, +0.0024]); OOF AUC 0.641. **The proxy, not the
   learner, is the ceiling.** Canaries clean (worst A-truth feature AUC 0.565). Contamination
   disclosed and measured: 31.9 % of A-truth pixels within 3 px of proxy pixels.
3. **Two implementation events, both disclosed:** the emission top-up amendment (fixed mass under
   NMS collisions; pass 1 byte-identical to P4, unit-tested) and a writer-caught defect (first
   top-up placed dots on catalogue zero-score cells; shared writer rejected it; fixed + regression
   test). See `docs/irregularities.md`.
4. **Repo contract:** `release.py` now resolves the current candidate from the canonical card's
   `phase_evidence` mapping (dot count card-driven); `registry/published_artifacts.json` pins the
   three new files; site/readme regenerated from receipts; tests extended (155 passing at
   handoff).

## Do not

* Do not relabel the P5 artifact as promoted, and do not edit the card's gates.
* Do not describe 0.2778 / 0.44 / 0.3195 as organizer-confirmed (all user-supplied).
* Do not rerun `run_experiment_v5.py` expecting an overwrite — the writer refuses existing files.
* Do not remove the emission amendment or its regression tests.

## Next session, in order

1. Quantify SGMC-vs-QFaults duplication (buffer tests 1–6 px), then pursue an independent truth
   source (NBMG county maps, INGENIOUS trace exports) — the measured bottleneck.
2. Registered band-widening experiment (D_MAX 48/64 px at fixed mass) — 36.3 % of B′ truth lies
   beyond the current 32-px halo.
3. Registered dot-count sweep (25k/37k/50k) on the existing P5 surface, B′ LOQO only.
4. Upstream the two uniqueness fixes to the template and run its suite.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/run_experiment_v5.py   # ~11 min CPU; regenerates evidence/p5hgb/
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

---

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
