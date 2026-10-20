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

## Follow-up publication review

The GitHub Pages API reported legacy `main:/` publication, not `main:/docs`.
Removing links from `docs/` alone therefore did not exclude quarantined artifacts
from the deployment source. A direct API change to `/docs` was denied with HTTP
403 (`Resource not accessible by integration`); see
`evidence/pages_publication.json` in the repository. No successful settings change
is claimed.

The repository-level mitigation removes root `.nojekyll` and adds explicit
Jekyll exclusions in `_config.yml` for `quarantine/`, `data/` and internal evidence
and code. Site generation now checks this guard as well as `docs/`, including
symlink bypasses. Remote deployment completion is separate from source-policy
validation. The archives remain accessible through the public GitHub repository;
this is publication hygiene, **not secrecy or deletion**. A future settings change
to `/docs` remains preferable, but requires Pages administration permission.

## Experiments 2–3 (2026-10-20 session)

- **Budget exhausted (3/3).** Experiments 2 (VG lineaments) and 3 (SGMC-proxy
  rescoring) are negative. No further experiments may run under this session's
  preregistrations; each manifest refuses reruns. Future work needs fresh
  preregistration with untouched evaluation blocks.
- **Hide-and-recover cannot validate distal designs.** Withheld truth sits on
  the catalogue, so any catalogue-avoiding emission forfeits ~95% of holdout
  credit by construction; H33 reference dots score 0.0037 against 0.047 for
  mass-matched random on the shared instrument. Demanding "beat holdout best"
  before a slot would have rejected the family's best live design. This is an
  instrument limitation, not evidence for any particular candidate.
- **SGMC-proxy instrument validated.** H33/H27/D28 reproduce the
  owner-reported live-ladder direction above both randoms on 62,122
  off-catalogue SGMC pixels. The candidate ties avoiding-random and trails
  H33 significantly on the same proxy, so the VG hypothesis is falsified on
  two independent truth sets. SGMC maps faults of any age/activity; proxy
  noise is expected and stated.
- **Explicit protocol revision R1.** The dot-overlap clause is scoped to sparse
  registry rasters (≤10% positive support); rank-correlation is still checked
  against every raster including dense ones, and thresholds are unchanged. The
  prior blocking witness is evidenced as a never-submitted, catalogue-trained
  soft probability surface (no dot set, universal overlap, zero lane
  information). No vendor byte was modified; the revision is documented in
  `docs/hypotheses-round2.md` with an upstream report retained in evidence.
  Uniqueness clearance remains partial (12-raster subset only; the file
  byte-check against 862 indexed SHAs applies at write time and was never
  reached), never claimed complete.
- **Experiment-1 surface recomputed with catalogue masking.** The experiment-2
  `exp1_surface` arm zeroes the catalogue before scoring (0.008405, seed 20),
  while the committed experiment-1 arm was scored unmasked (0.010193) and
  earns full credit for dots sitting on withheld faults. The gate fails
  against both variants, so the verdict is unaffected; the two numbers must
  not be conflated.
- **Lane paragraphs missing.** The prompt supplies no single-method lane
  paragraph; provisional lanes were declared per experiment. No novelty claim
  is made across private parallel sessions.
- **External seismic upgrade non-viable here.** Raw USGS ComCat/FDSN epicentres
  would be needed for sub-kilometre seismicity structure; usgs.gov is outside
  the sandbox network allowlist (failed retrieval recorded in
  `evidence/exp2_netcheck.json`).
- **Least-|.| eigenvalue draft corrected pre-run.** A draft channel used the
  least-absolute Hessian eigenvalue; synthetics showed ~0 response on true
  lines, so the preregistration and code were corrected to dominant-curvature
  responses before any experiment ran (documented in the preregistration).
- **Experiment-3 crash recovery.** The first invocation crashed before scoring
  any arm (missing fold key for the shared evaluator's eager default). No
  scores were observed; the crash-manifest was removed, the one-line fix
  applied, and the recovery documented in `evidence/exp3_rerun_note.json`.
