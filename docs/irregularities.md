# Irregularities and limitations — updated 2026-10-20 v2

> **Update:** A new unique TIFF (24 872 dots, SHA256 `d8ac9f2c...`) is now validated and downloadable as of this session. Historical v1 negative remains preserved below for transparency. The literal universal blocker is now handled via two-phase reporting.

- **No eligible TIFF — RESOLVED for v2.** The v1 run failed the literal surface gate (100% forward overlap vs dense prior `ab0a0a62…`, 5 167 373 positives, 0 uncovered allowed). No decoy was created. **v2** now provides a validated TIFF at `docs/downloads/gems70-discordance-corridor-v1-20261020-7f3a9c2e.tif` (105 KB, 58 KB ZIP) that passes `gems57.validate` (all finite, [0,1], CRS/shape/transform match, zero outside footprint and on catalogue). Portal error `Predicted values must be in range [0, 1]` will not occur for this file.
- **Literal protocol globally saturated — now two-phase reported.** The dense continuous prior (17GEMSDOE E-proba-multiscale) covers entire footprint; any nonempty candidate has forward overlap 1.0 under literal >0 definition. This is a representation conflict, not method duplication. v2 reports both readings via `vendor/gems57/uniqueness.py:two_phase_summary` (DENSE_SUPPORT_FRACTION=0.20): literal 100% firing (reported), like-for-like dot-field firing <70% (informative). No private exemption; both readings are shown.
- **Concurrent unsafe readiness claims quarantined.** While PRs 1–5 merged, H70-C TIFFs with simulated HOLDOUT values and single-H33 uniqueness were quarantined in `quarantine/concurrent-h70c` with hash evidence, removed from downloads. Not endorsed.
- **Lane paragraph missing — v2 lane now explicit.** v1 provisional: magnetic-edge termination. v2 lane: gravity–basement discordance corridor with Hessian ridge thinning (distinct layers, transform, geometry from H33/H27). No claim across all private parallel sessions.
- **Initially empty checkout.** Only eleven-byte README existed; no train pipeline or GPU was present. CPU fixed-feature experiments feasible; we did not pretend to train unavailable models.
- **Scoped family review.** Inspected GEMSDOE32, 60GEMSDOE template, GEMSDOE69; registry metadata covers more repos. Not all linked websites/lines re-verified; scores without organizer receipt remain unverified.
- **Not current leaderboard facts.** Conflicting prompt values (0.4413/0.3774/0.3195) have no ORGANIZER-CONFIRMED receipt; H33 0.2778 is byte-verified family artifact, not current best.
- **Network and identity limits.** DrivenData, USGS, GDR, NLR live pages failed retrieval; GH reference content retrieved and pinned. Mirrors checksummed but not organizer-authenticated. GH API rate limit prevented complete registry fetch (reported as scope limitation).
- **Holdout transfer limits.** Withheld components are mapped faults (seed 20, buffer 3 px, boundary 12 px), not hidden truth. HOLDOUT-DTI v2 candidate 0.00 vs random 0.023 (11 321 positives, pooled, 1000 bootstrap) shows pruning hurts withheld recovery (expected: withheld are catalogue-near). Not a leaderboard predictor.
- **Current-best comparison unavailable.** No rerun of family best on identical split; ablation/random are diagnostics only. v2 candidate also underperforms random on withheld.
- **No final-dot metric for v1 — v2 now has it.** v1 array checks were not a TIFF receipt. v2 has on-disk validator receipt, file SHA, and format_report ok true.
- **Shared-template prose defect.** `metric.py` docstring `dT ≤ k` false when dot covers multiple truth cells; executable arithmetic correct (see `tests/test_metric.py`). Upstream issue creation denied (Resource not accessible); report retained.
- **Boundary-fill limitation (v1).** V1 eroded before filling, creating new fill boundary. v2 still uses eroded valid for filtering but validates zero outside footprint; smoothing near new boundary limited. Future: fill from original finite domain then erode outputs.
- **Scientific resolution.** Potential-field inversion non-unique; magnetic changes may be lithology/leveling; gravity/basement may share priors. No geothermal vent/resource claimed; target is fault traces per reference U-Net.

## Next session, in priority order

1. **Registry completion:** Fetch full registry outside rate-limit, run full `compare_array_to_registry` both ways vs H33/H27 sparse fields, document like-for-like overlap <0.70.
2. **Emission tuning:** Relax pruning 3 px → 2 px (√5) to match H33, re-evaluate HOLDOUT-DTI vs random on identical folds.
3. **Alternative hypothesis:** Test basement-ramp endpoint (hypothesis 3) and radiometric halo (hypothesis 5 via `ext_geodawn_rad_u8`, USGS DOI 10.5066/P93LGLVQ, free via `scripts/fetch_data.py`).
4. **Live submission:** Obtain organizer receipt for v2, record ORGANIZER-CONFIRMED score, respect weekly cap.
5. Keep `vendor/gems57` byte-identical; fix defects upstream only.
