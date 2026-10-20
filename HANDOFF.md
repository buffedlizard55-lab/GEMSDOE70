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

## Parallel-session (E2/E3) integration note — 2026-10-20

A second lane ran three frozen experiments on untouched folds: E1 contact-termination (negative,
archived), E2 gated joint scarp×strain×cover (negative — the gates delete scarp signal), E3
scarp-curvature alone (PROMOTE-to-selector on catalogue HOLDOUT-DTI 0.0943 [0.0782, 0.1109],
seed-40/11,437 withheld). Candidate `docs/downloads/gems70e3-scarpcurv-60k-ex3-20261020-zeros.tif`
(sha256 in `evidence/run_card_e3_amended.json`, erratum-completed; original negative card preserved).
**E3 has not been scored on instrument B′** — that scoring is the selector's next step before any
weekly slot is spent on either candidate. Do not rerun the frozen E1/E2/E3 drivers; their manifests
block second runs. The E3 lane's forward-overlap saturation finding independently matches the
mutual-overlap fix landed in `vendor/gems57/uniqueness.py` above.
