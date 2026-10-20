# Session report — experiments 2–3 (2026-10-20)

Branch: `arena/5ba011ce-gemsdoe70`. All numbers below are HOLDOUT-DTI,
SGMC-proxy DTI, LEAKAGE-CANARY, DATA-MEASUREMENT, or REGISTRY-MEASUREMENT as
labeled. No ORGANIZER-CONFIRMED score exists for any artifact here.

## Pass 1 — review, verification, and implementation

Reviewed the repository: experiment 1 negative (literal-gate stop), H70-C
concurrent publication correctly quarantined (generation source contains
explicit simulated/placeholder holdout values), 117 tests passing at baseline.

Line-by-line verifications performed this session (all match committed
evidence unless noted):

- Core inputs restored via git sparse checkout (GitHub API rate-limited):
  training_features.tif, existing_faults.tif, sample_submission.tif — all
  three SHA-256 pins match.
- H33/H27/D28 forensic audit recomputed from local bytes: every count,
  distance, fraction, SHA, and pruning relation matches
  `evidence/h33_audit.json` exactly.
- 17GEMSDOE E-proba witness SHA matches; its sidecar + `submission_meta.json`
  prove it is a never-submitted catalogue-trained soft probability surface
  (value range [0.00046, 0.984]), with F-ensemble as the actual submission.
- Grid/footprint/catalogue: (3730, 3292), EPSG:32611, 5,167,373 footprint
  pixels, 60,988 catalogue pixels — consistent everywhere.
- 300 m band-smoothness table measured (see preregistration): strain bands
  and ieq carry no fault-scale structure (lag-3 corr ≥ 0.9995); tmi_vg is the
  most textured band (0.6259).
- Registry filename search over 862 unique rasters: no VG-detector lane, six
  strain lanes (including a 0.0000 owner-report), one proba file.
- GeoDAWN report: flight lines N90°E (200/400 m), ties N-S — sets the E-W
  artifact diagnostic used in experiment 2.
- USGS ComCat/FDSN: verified unobtainable (curl exit 35/000; host outside the
  sandbox allowlist) — recorded in `evidence/exp2_netcheck.json`.

Experiments run (budget 3/3, all preregistered before execution):

1. **Exp 2 — VG lineaments** (`docs/hypotheses-round2.md`): dominant-curvature
   Hessian centerlines of TMI vertical gradient (both polarities) OR
   VG-gradient contact ridges, NMS-thinned, 38,000 binary dots, 2 px spacing,
   catalogue-distance > 2 prune. Canaries clean both seeds; E-W 0.081;
   uniqueness subset passed (max sparse overlap 0.369; rho ≤ 0.011). Holdout:
   seed 20: 0.002476 [0.001875, 0.003089]; seed 71: 0.002547 [0.001909,
   0.003178] — tied with avoiding-random both seeds. NEGATIVE.
2. **Exp 3 — SGMC rescoring** (`docs/exp3-prereg.md`): fixed dots vs 62,122
   off-catalogue SGMC pixels. H33 0.095386 [0.084637, 0.106803] >
   H27 0.095295 > D28 0.094174, all above both randoms (avoiding 0.076743
   [0.072924, 0.080846]); candidate 0.075524 [0.061887, 0.088846] ties
   avoiding-random and trails H33 (paired −0.019862, CI excludes 0).
   NEGATIVE. One crash-recovery (missing fold key, no scores observed) is
   documented in `evidence/exp3_rerun_note.json`.

## Pass 2 — review findings and fixes (completed)

- Draft least-|.| eigenvalue channel falsified on synthetics → corrected to
  dominant-curvature responses pre-run (preregistration documents the change).
- Orientation gate moved from noisy skeleton to emitted dots (preregistered).
- Fair controls added: catalogue-avoiding random alongside E1-style random;
  random value 1.0 (matches candidate) instead of E1's 0.5 — stated.
- Cross-domain pooling split by evaluation domain (shared evaluator requires
  identical truth blocks per pool) — stated in receipts.
- Supplementary registry file miss recorded honestly + addendum measured.
- Experiment-2 `exp1_surface` (0.008405) vs committed experiment-1 candidate
  (0.010193): the difference is catalogue masking before scoring (ours masked,
  theirs unmasked, so theirs earns full credit for on-withheld dots; FP mass
  identical at 47611.3). Gate 2 fails against both; verdict unaffected.
  Documented in `docs/irregularities.md`, not rerun (budget exhausted).
- Uniqueness byte-check wording corrected: the 862-SHA comparison applies at
  write time and was never reached; evidence is the 12-raster subset only.
- Protocol section-5 session cards compiled by
  `scripts/compile_session_cards.py` (packaging only, no scoring/tuning):
  `evidence/session_card_exp2.json`, `evidence/session_card_exp3.json`.
  Run cards written by the experiment scripts were not modified.
- Precedence bug caught in the compiler's array checks (`&` vs `>`) before
  running; fixed with explicit parentheses.

## Pass 3 — final compliance check (completed)

- Full suite green (125 passed, 3 pre-existing Rasterio/Affine warnings).
- Site rebuilt; README rebuilt with brief embedded (test-enforced).
- No TIFF/ZIP under docs/, assets/, evidence/; no .tif links on site.
- Preregistration SHAs bind current docs (tests fail on post-hoc edits).
- No weekly slot used; no organizer score claimed; no complete-clearance claim.
- Cross-checks: run cards == holdout receipts; site downloads byte-identical
  to evidence; registry SHA pins verified; implementation re-read for
  correctness (pooling domains, greedy determinism, masking semantics).
- data/bridge input fixtures and quarantine contents are pre-existing
  committed state, excluded from Pages, covered by publication tests.

## Limitations and next steps

1. Uniqueness is partial (12 rasters + 862-SHA byte check). A complete scan
   needs bandwidth outside this sandbox.
2. SGMC proxy is validated for ranking (ladder reproduces) but SGMC maps
   faults of any age — proxy noise remains.
3. Queue hypotheses 2–5 untested; each needs a fresh session, fresh
   preregistration, and untouched blocks. Recommended order: deq-anchored VG
   (H2), gravity-VG (H4); strain-weight (H3) and 100 m scarps (H5) last.
4. Revision R1 needs upstream owner review (report retained, not filed).
5. Slot selection stays with the operator; nothing here authorizes an upload.
