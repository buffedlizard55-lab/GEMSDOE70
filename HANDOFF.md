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

## Latest protocol review (arena/4aea4e21-gemsdoe70)
Current prompt's literal forward-overlap rule conflicts with the prior mutual
amendment. P4 has four duplicate witnesses; no new experiment/TIFF generated.
Historical artifact remains downloadable FOR REVIEW ONLY. Release policy now
prevents stale promotion flags bypassing scientific, leakage, and literal overlap
gates. See docs/protocol-review.md and evidence/review-20261020/run_card.json.
Do not resume the earlier next-session plan without a named lane and resolution
of the explicit stop. Official reference README confirms CPU training support.

## Current literal-protocol review (2026-10-20, arena/00dc63c0-gemsdoe70)

Read `reports/literal-protocol-review.md` and `evidence/literal_protocol_review.json`
before interpreting the historical mutual-overlap clearance above. The requested forward-only
rule fails on four archived Phase-4 witnesses (maximum 1.0). Stop; no new experiment or TIFF,
no weekly slot. Frozen scientific receipts are preserved, not reclassified as new measurements.
Site-wide warnings and the README opening supersede old uniqueness claims for this prompt.
Reproduce: `.venv/bin/python scripts/audit_literal_protocol.py`, rebuild site/readme, pytest.
Resolve the protocol contradiction and explicit lane assignment before the supervised next step.

## Parallel-session E3 scarp lane (PR #17)

Independent lane, three frozen experiments: E1 contact-termination (negative, archived), gated
joint scarp×strain×cover (negative), scarp-curvature alone (PROMOTE-to-selector on catalogue
HOLDOUT-DTI 0.0943 [0.0782, 0.1109], seed-40/11,437 withheld). Candidate
`docs/downloads/gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif` (sha256 in
`evidence/run_card_e3_amended.json`). **Not yet scored on instrument B′** — selector's next step.
Frozen drivers live at `scripts/run_experiment_e2_scarp.py` / `run_experiment_e3_scarp.py`
(byte-identical rename; PR #16 owns canonical paths). Do not rerun.

## Current-request review — arena/3169a6c0-gemsdoe70 (2026-10-20)

**Overrides historical uniqueness clearance: DO NOT SUBMIT.** The latest user request explicitly
uses forward overlap, not the inherited mutual criterion. `scripts/audit_current_protocol.py`
reapplies that rule to frozen P4 rows: multiple witnesses fail, including forward overlap 1.00.
This is a historical negative witness, not a refreshed registry scan. No scientific experiment,
new TIFF, fitting, placement or competition upload occurred in this session. All TIFF bytes and
frozen scientific cards are preserved. Fresh local validation confirms P4 finite [0,1] and grid
consistency against cached reference metadata, not organizer acceptance.

- Current JSON: `evidence/current_protocol_review.json` (also published under docs).
- Review / ranked conditional hypotheses: `docs/protocol-review.md`.
- Official reference README retrieved at pinned commit and archived in `evidence/current-review/`;
  CPU-only training is supported (GPU is not a hard requirement).
- Website has a global DO NOT SUBMIT override, archive downloads remain available for review.
- Reconcile explicit lane and uniqueness policy before the old supervised-ranking next step.
- Reproduce: audit_current_protocol.py, build_site.py, build_readme.py, pytest; no data download needed.

Integration: main advanced concurrently with PRs adding a separate E3 scarp artifact and a literal-protocol review. All those frozen receipts, artifacts, tests and drivers were retained. This session's four conditional hypotheses and fresh P4 format card are supplemental (`docs/supplemental-protocol-review.html`), not a replacement for the concurrent review or an authorization of E3.
