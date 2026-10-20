# Current protocol review — 2026-10-20

## Download for review: YES. Submit: NO. New TIFF generated: NO.

The latest prompt requires **forward** dot overlap at most 70%, not mutual overlap.
The immutable Phase-4 audit has four counterexamples: `calib_r13lattice_00904.tif`
(1.0), `r11_greedy_mp.tif` (0.8069262229776385), `r13_lattice_s5_00904.tif`
(1.0), and `r14_union_tips10_lat6.tif` (0.7803686195357731).
These are REGISTRY-MEASUREMENTS, not DTI scores. Dense lattices explain the
failure but do not authorize changing the user's rule. This run logs a duplicate
and stops before any new placement or model experiment. A hash-distinct TIFF is
not necessarily unique under the requested overlap rule.

The supplied prompt says “single method paragraph below” but supplies none.
No lane is silently assigned. Historical mutual-rule evidence is preserved,
not rewritten as though it had used the current protocol. The shared evaluator,
writer, and uniqueness implementation are unchanged in this review. The release
policy additionally enforces the user's literal gate on the recorded rows.

## Why H33 performed well: evidence versus inference

The archived byte audit (`evidence/h33_audit.json`) shows removal of successive
near-catalogue shells from a sparse predecessor, not a newly trained detector.
The triangular-distance metric plausibly rewards sparse coverage and penalizes
redundant emission. But neither that algebra nor a handful of historical submissions
identifies the causal reason for a hidden-label result. Prior prose asserting that
“most” of the result is geometry, that a particular proxy is the hidden truth, or
that geometry is exhausted overstates the evidence. Those are hypotheses, not
verified conclusions. Beating H33 remains possible, not demonstrated here.

The prompt's historical scores and conflicting leaderboard claims lack a
submission-page receipt in this review; none is ORGANIZER-CONFIRMED. No new
leaderboard score or projection is reported. The actual task is fault prediction;
a fault candidate is not evidence of a geothermal vent or a productive reservoir.

## Ranked research backlog (not experiments or an assigned lane)

Expected improvement is qualitative and unvalidated. These combinations were not
found among the reviewed method descriptions; novelty across every external repo
is **not** established. They are not declared viable until data metadata and
availability have been checked in the chosen lane.

| Priority / cost | Hypothesis and specific inputs | Signature and missing-fault rationale | Non-fault mimic / distinction |
|---|---|---|---|
| 1 / medium | Cross-channel displaced marker matching: cached RTP and detrended elevation | Match parallel marker profiles across a candidate discontinuity; consistent lateral displacement could locate an unmapped cross-fault | Drainage capture or depositional truncation; tests signed displacement rather than edge strength or endpoint proximity |
| 2 / medium | Terrain-conditioned radiometric residual: cached GeoDAWN K/Th and detrended elevation | Remove lithology/terrain trends within training blocks, seek narrow residual gradients corroborated by RTP; alteration may reveal concealed conduits | Primary lithology, soil moisture, flight-line leveling; residual anomaly rather than raw ratio concordance |
| 3 / high | Opposed magnetic marker terminations: RTP, horizontal/vertical magnetic derivatives | Pair interrupted magnetic bands with consistent offset and continuation; concealed displacement may have no mapped scarp | Dike termination or remanence; paired marker reconstruction rather than generic analytic-signal ridge |

No new external data is required conceptually for these candidates, but cache
restoration, exact band descriptions, units and provenance are prerequisites.
These are proposals, not verified geological discoveries. Do not run them until
a single lane is assigned and the literal uniqueness stop is resolved explicitly.
No submission slot should be used without beating a preregistered compatible
holdout best, per-feature leakage canaries, and complete surface/final audits.

## Sources and access limitations

- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution):
  README fetched this review and stored in `evidence/review-20261020/`.
  It explicitly supports CPU training; the prompt's “GPU needed” claim is not a
  universal requirement. GPU acceleration can still be desirable.
- [Organizer problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
  [submission/data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
  [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf): manual-review links,
  not freshly verified in this review. Network host restrictions prevent direct access.
- [H33 repository](https://github.com/buffedlizard55-lab/GEMSDOE32): owner research,
  not an organizer receipt. Prior byte audit retained; no new causal validation.

No DrivenData upload or authentication was attempted. Weekly cap is unverified;
this review uses no slots. No exhaustive line-by-line scientific verification of
all linked repositories is claimed.

## Three review passes

1. Reviewed handoff, release policy, immutable audit and existing download inventory;
   found the forward/mutual conflict and stopped modeling.
2. Fixed release authorization: stale promotion flag no longer bypasses failed
   canaries, verdict, scientific gates or literal registry checks. Added mutation tests.
3. Rebuilt the site/README, checked tests and artifact format, and documented
   what remains blocked. Historical TIFF stays downloadable for education only.
