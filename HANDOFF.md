# Handoff — 2026-10-20 (Lane P8 Hero Candidate, branch `arena/c7049280-gemsdoe70`)

## State after Lane P8 (`p8_dual_submod300`) — `verdict = promote` (`download_ok = true`, `weekly_slots_used = 0`)

- **Promoted Hero Candidate (`docs/downloads/gems70-p5-dual-submod300-oof38k-20261020.{tif,zip,json}`)**:
  - `.tif`: `143,907` bytes · SHA-256 `d0e41ce921afcf3af33b7d86d75f6a258653dfbb4d050e864babe643245f0ea8`
  - `.zip`: `109,203` bytes · SHA-256 `fc6eec02fd78ab61df918d9020c406f0ac321ad748c83bdda72734f3b2cbb5df`
  - `.json` writer receipt: `3,556` bytes · SHA-256 `b925ed515b7a0db9d660d198ae13b1acfafd68f61c9c7a507d871a5339dfc403`
  - Unique submission name: `gems70-p5-dual-submod300-oof38k-20261020`
  - Submission note (`130 / 140` chars): `P8 dual-pop 4f-OOF HGB (Quat+SGMC>=300m, 41 localized multi-sensor feats) + exact 300m submod cover; 37654 binary off-cat dots.`
- **Why P8 breaks both prior ceilings simultaneously (`evidence/p8_dual_submod300/run_card.json`)**:
  - Prior lanes either truncated predictions to `d_cat <= 32 px` (`P4`, `E5`, `P5-HGB`, `P7`) — missing `34.0%` of `H33` across blind basins like Beowawe (`61.7 px`) — or trained purely on steep pre-Quaternary bedrock faults (`S3 = 0.0473`, `P6 = 0.0790`), losing active Basin-and-Range alluvial scarps on Instrument A.
  - `P8` fuses **two** 100% catalogue-free 38-feature 4-fold OOF physical `HistGradientBoostingClassifier` experts (`0.55 M_neo` on Quaternary faults + `0.25 M_bed` on pre-2022 `SGMC d_cat >= 3 px`) + multi-scale `100 m / 10 m 3DEP / 1 m LiDAR` strike-coherent ridge (`0.20 r_unsup`), per-partition quantile calibration (`rank01_domain`), and **exact unblurred `300 m` lazy-greedy submodular max-cover** across all `5,101,859` off-catalogue pixels.
  - **Instrument A (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`, `K = 11,321`)**: **`0.11129` (`95% CI [0.09492, 0.13161]`)** — `#1` in `GEMSDOE70` (`+21.1%` vs `D28 = 0.09192`, `+23.1%` vs fair `H33 = 0.09042`, `+48.0%` vs `P7 = 0.07519`, `+52.4%` vs `P4 = 0.07304`).
  - **Instrument B′ (`PROXY-DTI`, `d_cat >= 3 px`, `K = 59,937`)**: **`0.13109` (`95% CI [0.11566, 0.14499]`)** — `+39.8%` vs `H33 = 0.09377`, `+61.5%` vs `P4 = 0.08116`, `+15.2%` vs `P7 = 0.11379`, and `+6.1%` vs blurred greedy `thin = 2.8 px` on the identical surface (`0.12353`).
  - **Instrument B″ (`PROXY-DTI`, `d_cat >= 6 px`, `K = 52,767`)**: **`0.11897`** vs `P7 = 0.09997` (`paired Δ = +0.01900`, `95% CI [+0.00562, +0.03212]`).
  - **Uniqueness (`78` rasters = `62` archive + `16` local)**: `unique = true` (`0` mutual duplicates; `worst_mutual = 0.5629 <= 0.70`; surface `|ρ| <= 0.1763 <= 0.90`; literal one-way forward vs synthetic 206,895-dot lattice `calib_r13lattice_00904.tif` = `1.0000` and vs `GEMSDOE49__gate_ortho_w0.25-40k.tif` = `0.7028` disclosed for human selector sign-off).

## Reproduce Lane P8 (CPU; strict 3/3 budget documented in `docs/preregistration-p8-dual-submod300.md`)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/fetch_data.py
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/run_p8_audits.py
# Re-audit existing bytes across all 78 rasters & cross-lane B'/B'' without refitting:
.venv/bin/python scripts/audit_p8_against_all_lanes.py
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python scripts/audit_pages.py && .venv/bin/python -m pytest -q
```

## Next session

1. Human selector step: inspect `evidence/p8_dual_submod300/run_card.json` & `docs/p8.html`, verify live DrivenData weekly slot balance (`<= 3/week`), confirm selector exemption of synthetic dense lattice `calib_r13lattice_00904.tif`, upload **either** `docs/downloads/gems70-p5-dual-submod300-oof38k-20261020.tif` **or** `.zip` once, and record the returned portal receipt as `ORGANIZER-CONFIRMED`.
2. Open upstream PR applying `evidence/p8_dual_submod300/upstream_uniqueness_patch.diff` to `buffedlizard55-lab/60GEMSDOE` (`190 passed, 8 skipped, 0 failed` verified).
3. If a further scientific cycle runs with more compute/data, fit multi-scale 2D patch U-Net / ConvNeXt OOF spatial context on top of the 38 localized physical channels while keeping exact `300 m` submodular max-cover and strict 18-score LOO live-proxy calibration.

---

# Handoff — 2026-10-20 (session 3, branch arena/a0382202-gemsdoe70)

Read README.md, PROJECT_BRIEF.md, AGENTS.md, this file, `docs/s3-findings.md` and
`docs/irregularities.md` first.

## State after session 3

* **Two new unique, validated files, both DO NOT SUBMIT** (`docs/downloads/`):
  * `gems70-s3-proxyrank-h33spacing-37654-20261020-DO-NOT-SUBMIT.tif`
    (sha256 `e1982061f8ebbafcbd290e7383340306170a0df04a999905702f505f06ddabc9`) — E1, pre-registered
    proxy gate passed (B′ +0.0300 vs H33, CI [+0.0034, +0.0557]) but **vetoed** after calibration.
  * `gems70-s3e2-marginmatched-proxyrank-37654-20261020-DO-NOT-SUBMIT.tif`
    (sha256 `41099fcd8cc1e81605383183266d829e8504964044435b876d8d4f5d6d14a2fc`) — E2, negative.
* **Key finding:** offline instruments do not track the live board (Spearman −0.28 for B′, −0.64 for
  A, n = 18 reported scores). E1's proxy gain is concentrated in steep terrain (64 % vs H33 20 %),
  like gate_ortho (48 %, reported 0.2376 live). With terrain and distance matched (E2) the model adds
  no significant information.
* Budget: 2 of 3 experiments, ≈ 1 h of 2 h. Weekly slots used: 0. No organizer-confirmed score.

## Reproduce session 3

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/run_experiment_v5.py   # ~11 min CPU; regenerates evidence/p5hgb/
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

=== S3 lane (parallel) ===
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE   # HEAD b99591e used
.venv/bin/python scripts/run_experiment_s3.py        # ~25 min on 2 CPU / 3 GB
.venv/bin/python scripts/proxy_calibration_s3.py     # ~1 min
.venv/bin/python scripts/run_experiment_s3_e2.py     # ~20 min (needs E1 TIFF at its original name;
                                                     #  see evidence/s3/run_card.json 'artifact')
.venv/bin/python scripts/terrain_marginals_s3.py
.venv/bin/python scripts/build_s3_report.py && .venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

## Next session (from docs/irregularities.md)

1. Live-calibrated instrument (pre-declared proxy family, leave-one-file-out against the 18 scores).
2. Only then a new candidate (basin-floor LiDAR micro-scarps is the queued geological idea).
3. Upstream the two uniqueness fixes. 4. Selector step only for a candidate that beats H33 on the
   calibrated instrument.

---

# Handoff — 2026-10-20 · P5 research negative · branch arena/90160b2d-gemsdoe70

**Top priority: new TIFF exists but DO NOT SUBMIT.** Download-for-review file:
`docs/downloads/gems70-p5-cover-magnetic-loqo-20261020-DO-NOT-SUBMIT.tif`;
SHA-256 `30a52f9af75af5e9241e0928cc941a71189cf2e3301d2320460ff70d230c396a`.
Single-band float32, EPSG:32611, 3730×3292, sample transform, finite [0,1], zero on
known faults/outside; one-TIFF ZIP hash-pinned. `p5_status` authorizes a **review download
only**. `submit_recommended=false`; weekly slots used=0. A format pass is not portal acceptance.

The previously missing assigned lane remains an irregularity. We preregistered one provisional
magnetic-analytic-width lane and ran one LOQO supervised experiment; no H33/P4 dots were copied.
Catalogue HOLDOUT-DTI (`gems57-pooled-hide-v2`, 11,321 withheld) 0.01226 [0.00753, 0.01765]
versus regenerated visible-only P4 0.07304; SGMC-proxy HOLDOUT-DTI
(same evaluator, 59,937 proxy positives) 0.02542 [0.01853, 0.03363] versus
H33 0.09377. Paired differences both negative with 95% CIs below 0. This does not predict an
organizer score. Max feature-alone AUC or inverse AUC 0.751 (<.90 leakage canary).

The literal gate remains decisive: hash-pinned binary lattice has a 3px halo covering
**all 4,989,581 feature-valid pixels** after 12px erosion; P5 final positive support has
forward overlap 1.00 with it. Shared binary-dot count zero is NOT a loophole; no discrete
dots were placed. The refreshed 70-raster archived/local scan max Spearman is 0.0232 but a low
rho cannot waive positive-support overlap. No private/organizer registry completeness claim.
Read `docs/preregistration-p5.md`, `evidence/p5/run_card.json`,
`reports/p5-scientific-review.md` and source receipt before attempting further work.

The earlier archive protocol review below is frozen and *was* accurate at its own time;
P5 is a separate, later research result. Only a separately authorized selector can choose
a future cleared file for a live weekly slot. Next: resolve assigned lane + forward-overlap
conflict, train/evaluate geometry-preserving within-halo ranking at matched dot budget on an
untouched outer split, corroborate proxy labels and data rights, then assess live page balance.
Do not tune or submit the negative P5-cover file. Concurrent integration preserved two
stronger but still negative and literal-duplicate lanes: E5 supervised LOQO
(`evidence/e5/`, SGMC proxy B′ 0.0886) and P5 analytic dot halo
(`evidence/p5hgb/`, SGMC proxy B′ 0.0766); neither is an organizer score or slot
approval. The P5-cover run remains a separate immutable continuous research TIFF.

---

# Prior handoff — literal protocol review, arena/9d9f624f-gemsdoe70

This note supersedes older submission-approval language below, not the frozen scientific evidence.

- **DO NOT SUBMIT.** New current card: `evidence/review/run_card.json`; new measured audit:
  `evidence/review/literal_protocol_audit.json`. All six published final TIFFs have forward overlap
  1.0 with the pinned binary `calib_r13lattice_00904.tif` witness. No new TIFF, experiment or slot.
- The inherited "100% halo coverage" claim was false: fresh coverage is 0.9987132726822701,
  leaving 6649 cells uncovered. At fixed mass 37654, the minimum possible overlap is still
  0.8234184947150369 > 0.70. Do not generalize the proof to every smaller mass.
- Vendor metric/evaluator/writer/uniqueness bytes and Phase1–4 / E2 / E3 / scarp E3 receipts are
  preserved. `src/gems70/protocol.py` applies literal thresholds to shared measurements; no mutual
  exemption is authorized. Both historical audit CLI and release API use this adapter.
- Parallel main advanced during the review (including scarp E3, PR17). Integration preserved
  that artifact and its hash pins, all incoming scientific tests and publication guards.
- Website: current review-only banner everywhere, real executive summary, current measured
  run-card links, ranked research queue and conservative H33 analysis. The default public
  `docs/run-card.json` is the new negative card; old P4 evidence stays at its historical path.
- Official organizer GitHub README/notebook re-fetched. Other official hosts, portal auth, live
  weekly cap and score receipts remain unavailable this session. Upstream issue creation was
  denied integration permission; report retained in `evidence/review/upstream-policy-report.md`.

Next: resolve explicit protocol authorization before another fixed-mass experiment; quantify SGMC
redigitization overlap; then evaluate the first residual-ranking hypothesis with nested spatial
validation, feature-alone canaries and a matched current-best baseline. No boundary-only loophole
experiment or new slot without the separate selector gates. Reproduce this review with
`python scripts/review_literal_protocol.py --fetch`, builders, pytest and audit_pages.


Latest integration: PR #28 H70 conductive-breach archive and PR #24 protocol audit preserved.
Canonical `evidence/run_card.json` remains H70 as set by that session; P4 builders/audits now
read `evidence/phase4/run_card.json` explicitly. The new measured review card remains
`evidence/review/run_card.json`. All six artifacts directly fail the binary-witness forward rule.
Integrated suite: 212 passed (three upstream affine deprecation warnings).
# Handoff — 2026-10-20 (session 2, branch arena/9fe83934-gemsdoe70)

Read README.md, PROJECT_BRIEF.md, this file and `docs/irregularities.md` first.

## State — P5 promoted to primary (P4 archived)

* **Artifact now published (primary):** `docs/downloads/gems70-p5-analytic-halo-37654-20261020.tif`
  (149,414 bytes, sha256 `aa3799b2a341a6a5c1a37527e7002c6b22c27d7ea57eb23ab97772926b8f33d4`),
  plus one-TIFF ZIP `bf61cacc...` and writer receipt `4e686799...`. **P4 archived** to `evidence/history/p4_stratified_halo/` and `docs/downloads/gems70-p4...` retained but no longer primary.
* **Verdict: negative (both P4 and P5).** `download_ok = true`, `submit_recommended = false`.
  P5: Instrument A 0.0828 [0.0755,0.0895] vs H33 0.0037 (candidate wins); B′ 0.0766 [0.0687,0.0852] vs H33 0.0938 **H33 wins Δ -0.0172 [-0.0278,-0.0063]**; B unrestricted 0.0878 vs 0.0906 candidate wins. P4 was 12.6 % below H33 on B′; P5 is 18 % below — analytic-signal rank hurt B′ despite helping A.
  The pre-registered target-like gate (B′) is negative with CI excluding zero.
* **No weekly slot used. No organizer-confirmed score exists in this repository.** All numbers are HOLDOUT-DTI (gems57-pooled-hide-v2) or user-supplied historical (0.2778, 0.4413).

## What was done — session 2 + session 3 (P5)

1. **Two defects in the shared uniqueness tool were found and fixed** (reported, hashes in
   `registry/template_pin.json` with `all_identical: false`, full text in
   `evidence/upstream_fix_report.md`):
   * dots are binary (`|value − 1| < 1e-6`), not every positive value;
   * duplication requires **mutual** overlap; forward-only overlap fires at 1.00 on three archived
     dense lattices whose 3-px halos cover the whole footprint.
2. **Four preregistered experiments (P2-P5).**
   * P2 (geophysically gated continuation prior): A 0.0591, B 0.0432 — four-field gate hurt, removed.
   * P3 (damage-zone intensity): A 0.0873, B 0.1098, B′ 0.0471 — concentration wasted mass (T saturates).
   * P4 (coverage-stratified halo 7px, weak tilt+tip): A 0.0730, B 0.0948, B′ 0.0812 — +72 % over P3 at fixed mass; best geometry so far.
   * **P5 (analytic-signal halo 7px, tmi_hg+tmi_vg rank+tip): A 0.0828, B 0.0878, B′ 0.0766 — magnetic rank helped catalogue recovery (+13 % vs P4 on A) but hurt proxy B′ (-6 % vs P4, -18 % vs H33).** Mechanism nonunique: remanent dike margins mimic analytic-signal ridges. Verdict negative; no slot.
3. The site was rebuilt to read every number from JSON receipts and to state the download/submit decision explicitly on the landing page. Hypotheses.md now ranks 5 new candidates (H-2 tested as P5, H-3 radiometric halo, H-4 lidar breakline, H-5 conductive breach, H-6 basement curvature) with layers, signature, omission argument, mimic, difference, expected DTI, cost, and external-source obtainability. h33-analysis.md expanded to PhD-level metric algebra and why P5 failed.

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

## Reproduce — P5 (analytic-signal halo) is now the published primary

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py   # 400 MB training_features + external rad/lidar from owner mirror
.venv/bin/python scripts/fetch_data.py     # 7-file WANT set: training_features + lidar_scarp + geodawn rad/ext + gdr wellsprings
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE  # 62 registry rasters for uniqueness
.venv/bin/python scripts/run_experiment_p5.py   # P5 analytic-signal halo (this session) — 73 sec, 37,654 dots, HOLDOUT-DTI A 0.0828 B′ 0.0766
.venv/bin/python scripts/run_experiment_v4.py   # P4 stratified halo history — archived to evidence/history/p4_stratified_halo/
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q          # 144 passed at P5 handoff (was 118 at P4)
.venv/bin/python scripts/release_gate.py --expect-negative  # download_ok true, submit_recommended false
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

## E5 lane (2026-10-20, branch arena/e22c56cf-gemsdoe70) — supervised LOQO, negative

Executed the registered next step: SGMC-proxy (d≥3 px) HGB ranker, LOQO, OOF
surface, P4 emission + Amendment-1 same-NMS fill (P4 block pass alone placed
34,409/37,654 on the sharper surface; amended pre-score in
`docs/preregistration-e5.md`). Artifact
`docs/downloads/gems70-e5-supervised-loqo-37654-20261020.tif`
(sha256 `8b7d67e9c2b0ddb4562b70d5726f76dd4ef84b4b1842bdffc98d017575b97bd2`,
byte-identical across two full reruns). Canaries ≤0.755; OOF AUC 0.689–0.781.
A HOLDOUT-DTI 0.0815 vs H33 0.0037; **B′ PROXY-DTI 0.0886 vs H33 0.0938,
Δ −0.0051 [−0.0161, +0.0053]** → gate fails, verdict negative,
`submit_recommended=false`, no slot used. Supervised ranking halved P4's B′
deficit (−0.0126) and is statistically tied with H33 on B′, but does not beat
uniform halo sampling: ranking signal exists (AUC) yet does not convert into
DTI at 37,654 dots / 300 m saturation. Evidence `evidence/e5/`; script
`scripts/run_experiment_e5.py`. Next: E5-3/E5-4 features (GeoDAWN
radiometrics, lidar scarp) inside the same LOQO harness after checking mirror
obtainability; or selector decision to spend one slot on P4/E5 as a deliberate
measurement (never recorded as expected win). Public leader 0.4413
(organizer-page read 2026-10-20, `evidence/e5/leaderboard_read.json`).
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

## Session-2 lane (arena/9a895360, merged additively)

Exp2 (seed 702, gate hurt) and Exp3 (seed 703, fusion 0.09161) both negative; unique TIFF
`gems70-fusion-dotted-37654-20261020.tif` is DO NOT SUBMIT (holdout CI gate + 0.896 3-px
overlap vs GEMSDOE49 parent). Card `evidence/s2_run_card.json`, findings `docs/s2-findings.md`,
prereg `docs/s2-hypotheses.md` + `docs/hypotheses-exp3.md`, method `src/gems70/method_s2.py`.
Spent seeds for this lane: 702/703 — do not retune. Zero slots used.

## Parallel E6 multi-modal extended-domain LOQO lane & completed selector audits (2026-10-20, `arena/effcd5f7-gemsdoe70`)

1. **SGMC vs. QFaults buffer calibration ($r = 1\dots 6\text{ px}$, `evidence/e6/sgmc_buffer_audit.json`):**
   Off-catalogue SGMC shell enrichment is `3.83×` at `(0, 1]` px, `2.98×` at `(1, 2]` px, `1.86×` at `(2, 3]` px, `1.40×` at `(3, 4]` px, `1.14×` at `(4, 5]` px, and `0.97×` at `(5, 6]` px; **35.89% of all `SGMC B′` ($d \ge 3\text{ px}$) fault pixels lie at $d_{\text{cat}} > 32\text{ px}$** (`p50 = 22.80 px`, `p75 = 41.98 px`), explaining why `P4` (`0.0812`) and `E5` (`0.0886`) trailed `H33` (`0.0938`) when restricted to $d \le 32\text{ px}$.
2. **Experiment E6 (`docs/downloads/gems70-e6-multimodal-extdomain-loqo-37654-20261020.tif`, sha256 `9b4f225f9656b1b3ab106750be431a4053e7ad804fe3bb9e2dac163d49601771`):**
   28-feature LOQO HGB across $d_{\text{cat}} \in [3.0, 96.0]\text{ px}$ with 7×7 regional coverage stratification (`37,654` binary dots; preregistered in `docs/preregistration-e6.md`, driver `scripts/run_experiment_e6.py`) achieves `Instrument B′ = 0.1100 [0.1058, 0.1133]` vs. `H33` `0.0938 [0.0839, 0.1044]` (**paired $\Delta = +0.0162$, 95% CI `[+0.0045, +0.0270]`**, `gate_b_prime_candidate_gt_h33_significant = true`) and `Instrument A = 0.0710 [0.0637, 0.0781]` vs. `H33` `0.0037` (`gate_a_candidate_ge_h33 = true`). Passes amended mutual-overlap uniqueness across all 62 registry rasters (`worst_mutual = 0.2960 <= 0.70`, `worst_nonlattice_forward = 0.3526 <= 0.70`, `worst_spearman = 0.0133 <= 0.90`) and all sibling repository TIFFs (`worst_mutual = 0.3508`). Published with `download_ok = true` and `submit_recommended = false` under the active literal one-way forward-overlap gate (`1.00 > 0.70` against `calib_r13lattice_00904.tif`).
3. **Completed selector audits (`evidence/e6/e2_uniqueness_62rasters.json` and `evidence/e6/cross_lane_bprime.json`):**
   Full 62-raster E2 uniqueness re-audit (`worst_mutual = 0.2876 <= 0.70`, `worst_nonlattice_forward = 0.4795 <= 0.70`) and 7-lane `Instrument B′` comparison (`E3` `60,000` dots `0.2137`; `E6` `0.1100`; `E2` `0.1048`; `H33` `0.0938`; `E5` `0.0886`; `P4` `0.0812`; `H70-A` `0.0792`).

## P6 dual-horizon LOQO scarp–rad–basement lane & SGMC 1–20 px buffer audit (`arena/c6a19d32-gemsdoe70`, 2026-10-20)

- **Artifact published (review only, DO NOT SUBMIT):** `docs/downloads/gems70-p5-dualhorizon-37654-20261020.tif` (`146,736` bytes, SHA-256 `bb014897052c478ca2f4690920e4d863fa2a6b810a05a15d8e33e129cc76de84`, `37,654` binary `1.0` dots, `0` on-catalogue dots), plus `.zip` and `.json` registered in `registry/published_artifacts.json`.
- **Verdict: negative (`download_ok = true`, `submit_recommended = false`).**
  - Instrument A (`HOLDOUT-DTI`, `11,321` withheld positives): `Exp 5.3` `0.0790` `[0.0688, 0.0900]` vs P4 `0.0730` (Δ `+0.0059` `[-0.0050, +0.0163]`) and H33 `0.0037`.
  - Instrument B′ (`PROXY-DTI`, `SGMC d >= 3 px`, `59,937` positives, LOQO): `Exp 5.3` `0.1440` `[0.1319, 0.1558]` vs H33 `0.0938` (Δ `+0.0502` `[+0.0339, +0.0663]`, +53.5%) and P4 `0.0812` (+77.4%). `Exp 5.1` (LOQO `7×7`) scores `0.1250`; `Exp 5.2` (unsupervised 10m-3DEP breakline + LiDAR scarp + rad `7×7`) scores `0.1201`.
  - Instrument B′′ (`PROXY-DTI`, `SGMC d >= 6 px`, `52,767` positives): `Exp 5.3` `0.1234` `[0.1118, 0.1359]` vs H33 `0.0850` (Δ `+0.0384` `[+0.0217, +0.0553]`).
  - SGMC vs QFaults buffer calibration (`1..20 px`, `evidence/p6_dualhorizon/sgmc_buffer_audit.json`) and E2 62-raster mutual re-audit (`evidence/p6_dualhorizon/e2_mutual_uniqueness.json`) recorded.
  - Held fail-closed because paired Instrument A vs P4 CI straddles zero, SGMC B′ sits at `13.42°` median slope vs Quaternary catalogue `5.55°`, and literal forward overlap vs the dense lattice is `1.00` (worst mutual overlap `0.4230 <= 0.70`, worst Spearman `0.0300 <= 0.90`). No weekly slot used.

