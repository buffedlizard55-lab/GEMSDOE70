# Irregularities and limitations

- **No eligible TIFF.** The scientific run failed the literal surface overlap gate. Per the explicit stop rule, final dots were not placed and no submission TIFF/ZIP was written. A cosmetic file, previous submission copy, all-zero decoy or metadata-only rename would not fulfill the request for a unique prediction. The requested downloadable competition artifact remains unmet.
- **Literal protocol is globally saturated.** A newly SHA-verified archived continuous prediction is positive on every footprint cell. Its three-pixel halo covers every allowed off-catalogue cell. Any nonempty candidate necessarily has full forward overlap under the inherited support definition. This is a protocol/representation conflict, not proof of scientific method duplication. It is logged as a duplicate and stops this run nonetheless. No density exemption was applied.
- **Concurrent unsafe readiness claims quarantined.** While this PR was being prepared, other sessions merged H70-C TIFFs and a READY TO SUBMIT site into main. The preserved generation source explicitly says it will “simulate plausible but label as HOLDOUT” and contains placeholder holdout numbers and hardcoded canary claims; these are not accepted as measurements. Its greedy uniqueness check uses only H33, not the universal dense witness. The source, documents and artifacts are retained under `quarantine/concurrent-h70c`, with hashes in `evidence/concurrent_h70c_quarantine.json`, removed from website downloads and not endorsed. This is a separate session's artifact, not an additional experiment run here.
- **Lane paragraph missing.** A provisional single-method lane was declared before the experiment. No uniqueness or geological novelty claim is made across all private parallel sessions.
- **Initially empty checkout.** Only an eleven-byte README existed. Claims that this checkout already had a train/inference pipeline, GPU requirement, or only a data-placement blocker were not true of the checked-out files. A CPU fixed-feature experiment was feasible; we did not pretend to train an unavailable model.
- **Scoped family review.** We inspected source/artifacts from GEMSDOE32, the pinned shared template in 60GEMSDOE, and the latest GEMSDOE69 handoff; inherited registry metadata covers more repositories. We did not independently review every line of every linked website or reauthenticate every historical score.
- **Not current leaderboard facts.** Multiple conflicting leader values in the supplied prompt have no authenticated organizer receipts here. Neither the historical H33 claim nor any projection is labelled ORGANIZER-CONFIRMED. No weekly cap is guessed.
- **Network and identity limits.** Official DrivenData, USGS, GDR and NLR pages failed retrieval here. GitHub-hosted organizer reference content was retrieved and pinned. Public mirrors were restored and checksum-matched, but mirror identity is not independent organizer authentication, license clearance or proof that all files are current.
- **Holdout transfer limits.** Whole mapped connected components are withheld with buffered visible context and spatially eroded quadrants. This is not the hidden organizer truth. No catalogue-derived feature is used. Feature-ranking is an unsupervised whole-footprint transform, not supervised cross-validation. Confidence intervals are conditional spatial-cluster bootstrap intervals, not leaderboard intervals.
- **Current-best comparison unavailable.** Current-best methodology has not been rerun on this identical split. The ablation and random sparse control are diagnostics, not a certificate of beating the family best. The candidate also underperforms the random control.
- **No final-dot metric or file validator result.** Array checks are recorded, not disguised as a validated GeoTIFF receipt. The run card uses null values with reasons for unperformed stages.
- **Shared-template prose defect.** The `metric.py` docstring says marginal truth coverage is bounded by nearest-truth self-credit (`dT <= k`). This is false when a dot covers several truth pixels. Executable arithmetic returns the correct multiple-pixel coverage. An upstream issue-creation attempt was denied by the GitHub integration (`Resource not accessible by integration`); the report is retained in `evidence/upstream_metric_report.md` and is not claimed filed. The byte-pinned template has not been privately modified. Our explanation and regression test use the general inequality without that assumption.
- **Boundary-fill implementation limitation.** The frozen experiment erodes the feature domain before nearest-finite filling, which creates a new fill boundary at that interior mask. Its comment about guarding all filter-boundary effects is too strong: smoothing can still affect pixels near that new boundary. No positive inference is based on this run. Do not alter the source pins or rerun the stopped experiment to repair its result; a future preregistered implementation should fill from the original finite data domain, then apply an output-support erosion after filtering, with a dedicated edge test.
- **Scientific resolution.** The cached basement/gravity layers may share inversion priors; magnetic changes can reflect magnetization, lithology, or leveling residuals. No geothermal vent, resource, or active fault is claimed discovered.

## Next session, in priority order

1. Resolve the literal continuous-surface/dot representation conflict at the shared protocol level. Until then, no nonempty submission can pass. Do not silently change the threshold or registry support definition.
2. Obtain an explicit lane paragraph, official sample/data identity and rule confirmation, and a current-best implementation on a comparable holdout split. Do not request credentials in chat.
3. Use the archived negative evidence to reject the present fixed ranking. A fresh preregistered idea must use untouched evaluation blocks and satisfy the budget; do not tune this experiment on its reported holdout.
4. Verify scientific literature/data licensing from official sources when network access permits. The research queue is not a list of verified discoveries.
5. Only after a successful complete surface audit: place final dots, repeat the complete literal registry audit, invoke the shared writer, validate the exact bytes, bind the receipt/hash and publish a one-click file. Weekly-slot selection remains separate.

## Addendum 2026-10-20 (E2/E3 session)

- **E2/E3 both negative for slot promotion.** E2 (alluvial step) HOLDOUT-DTI
  0.06465 beats random and each ablation but loses to D28 reference 0.09192;
  E3 (depth step) mechanism canary AUC 0.506 (null), candidate 0.05054 driven
  by its basement-edge partner. Frozen bars in `docs/preregistration-e2.md`
  were applied as written. No tuning followed.
- **Publication amendment A1** (`docs/publication-amendment-e2.md`) publishes
  E2 bytes for selector review under DO-NOT-SUBMIT-YET status. This deviates
  from the preregistration's no-publication sentence on publication only;
  verdicts, bars and numbers are unchanged. If the selector rejects the
  amendment or revision R1, the file must never be submitted.
- **Catalogue holdout anti-ranks the live-reported champion** (H33 last,
  below random; see H33 addendum). Do not use catalogue HOLDOUT-DTI alone to
  rank far-field discovery fields for live value in either direction.
- **Bridge sample is the catalogue**, not an all-zero sample (60,988 positives,
  exact support match). Footprint use only.
- **Uniqueness scope is a 7-raster subset** under revision R1, not the complete
  862-raster inherited inventory and not any organizer registry. Complete scan
  + R1 acknowledgment remain selector prerequisites. Upstream issue filing was
  denied by the integration (`Resource not accessible by integration`);
  report retained in `evidence/upstream_uniqueness_report.md`, not claimed filed.
- **Live pages now retrieved:** organizer problem page, about page and public
  leaderboard were fetched 2026-10-20 (leader 0.4413 at read). Data-download
  identity, weekly cap, known-fault masking in scoring, and final-round label
  composition remain unverified from fetched text.
- **E3 valid-mask note:** E3 intersected all four E2 bands for `valid0` to keep
  the identical eroded domain (4,989,581 px, matches E2), although its ranking
  uses only rtp/basement. Conservative and comparability-preserving; recorded
  in `scripts/run_experiment_e3.py`.
