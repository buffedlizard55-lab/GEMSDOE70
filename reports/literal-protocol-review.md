# Current literal-protocol review — 2026-10-20 continuation

## Decision: DO NOT SUBMIT; review-only archives

**No new TIFF, geological experiment, holdout score, or competition slot was produced in this continuation.**
The user's request for a new protocol-compliant submission remains unfulfilled. No candidate was
created or placed because the recorded forward-overlap stop fires on prior final TIFFs and no
separate protocol authorization or identifiable method-lane paragraph exists.

### Canonical current records

- Run card: [`evidence/review/run_card.json`](../evidence/review/run_card.json)
- Literal audit: [`evidence/review/literal_protocol_audit.json`](../evidence/review/literal_protocol_audit.json)
- Three-pass record: [`evidence/review/verification-passes.md`](../evidence/review/verification-passes.md)
- Public copies: `docs/downloads/review_run_card.json` and `docs/downloads/literal_protocol_audit.json`
- Source-page and sibling review: [`evidence/web_sources_review_2026-10-20.json`](../evidence/web_sources_review_2026-10-20.json)
- Partial current TIFF inventory: [`evidence/sibling_registry_refresh_20261020.json`](../evidence/sibling_registry_refresh_20261020.json)

The compatibility files `evidence/current_protocol_review.json` and
`evidence/literal_protocol_review.json` preserve historical schemas/measurements. They are not the
canonical current run card and do not authorize a release.

## Stop evidence — measured, not inferred from old mutual-overlap results

The current rule is the supplied **forward** overlap: stop if more than 70% of candidate dots lie
within 3 pixels of one registry raster, or if rank correlation exceeds 0.90. The inherited mutual
rule is not an approved exemption. The pinned binary witness
[`calib_r13lattice_00904.tif`](https://github.com/buffedlizard55-lab/60GEMSDOE/blob/32024716f218d06a94e01464157392119c03cb15/registry/rasters/calib_r13lattice_00904.tif)
has SHA-256 `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2` and 206,895 binary
dots. Its 3-pixel halo covers 5,160,724 of 5,167,373 footprint cells (99.871327%), leaving 6,649
uncovered. At the historical fixed mass of 37,654 dots, even the best possible allocation to those
uncovered cells has minimum forward overlap `1 − 6649/37654 = 0.823418495`, above the stop. This
bound is specific to that mass; it does not prove impossibility for every smaller candidate.

The latest inherited review measured forward overlap 1.0 against this witness for all six published
final TIFFs (P4, discordance, E2, H2 diagnostic, scarp E3, and H70 conductive breach). A low reverse
overlap, low Spearman value, distinct file hash, or old `unique:true` result does not cancel that
forward failure. No new pre-placement surface or final dots were tested.

## Separate format blocker

The official DrivenData problem page states that the output is one float32 GeoTIFF in EPSG:32611 at
100 m with matching bounds and values in [0,1], with null/NaN outside bounds. The shared writer
currently rejects non-finite arrays, writes `nodata=None`, and emits finite zero-valued cells outside
the mapped footprint. Existing archives pass only the shared local single-band/grid/range preflight;
they are **not certified compliant with the complete official format**. No local vendor fork or
shared-writer modification was made. Resolve this upstream or obtain organizer clarification before
any future positive release.

## Current research position

Four hypotheses are ranked in [`docs/protocol-review.md`](../docs/protocol-review.md), with exact
cached band IDs, target signatures, non-fault mimics, qualitative expected HOLDOUT-DTI direction,
cost, and differences from local methods. They are untested and unauthorized, not projected scores.
The first (fold-trained residual cross-sensor ranking) is the highest qualitative information/cost
option, not globally novel: the reviewed sibling pages include multiscale multi-physics and
relief-conditioned methods. No experiment or canary is authorized until protocol and lane are
resolved. Existing historical P4 HOLDOUT-DTI is 0.0730422921, 95% CI [0.0667398770, 0.0789949697],
evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives; it is copied historical evidence, not
recomputed here and not an organizer score.

## Source and registry findings

- The organizer problem, About, public leaderboard, rules PDF, USGS GeoDAWN/SGMC pages, DOE GDR
  1391, and selected literature were retrieved through the Arena web reader. Exact summaries,
  dates, and limits are recorded in `evidence/web_sources_review_2026-10-20.json`.
- On 2026-10-20, the public leaderboard displayed 0.4413, 0.3811, and 0.3788 for its first three
  public rows. These are **PUBLIC-LEADERBOARD-OBSERVATIONS**, not local HOLDOUT-DTI and not
  ORGANIZER-CONFIRMED scores for a named GEMSDOE file; no submission-page receipt was accessed.
- A refresh of the current public default branches for GEMSDOE66–72 found 302 tracked TIFF paths
  matching the grid, 175 unique SHA-256 hashes, 98 hashes in the inherited 862-hash set, and 77
  absent from that set. This partial owner-site scan is **not** the complete family, private, future,
  or organizer registry and clears no candidate.
- Peer-site metrics remain self-reported. GEMSDOE66's LIDAR-05 page/run-card identifiers conflict;
  GEMSDOE68's shared evaluator label hides differing implementation hashes and fold settings;
  GEMSDOE67/69/72 do not expose enough metadata in the retrieved summaries for comparable DTI
  reporting; GEMSDOE71's “ORGANIZER-CONFIRMED” H33 label has no receipt. Full details and links are
  in the source-review JSON.

## Reproduction and continuation

```bash
PYTHONPATH=. .venv/bin/python scripts/refresh_sibling_registry.py \
  --output evidence/sibling_registry_refresh_20261020.json --workers 4 --refresh
.venv/bin/python scripts/review_literal_protocol.py --fetch
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/audit_pages.py
```

The partial sibling refresh uses sparse Git clones and shared binary-dot semantics. Its cached files
stay in ignored `.cache/`; the evidence JSON records exact scope. Full project test/site results for
this continuation are recorded in `evidence/review/verification-passes.md`. The next authorized action
is protocol resolution, not a candidate or slot: preserve the stop, report the shared writer's
format defect upstream, and only then revisit one ranked hypothesis with feature-alone leakage
canaries, matched shared HOLDOUT-DTI, surface-first uniqueness, final-dot uniqueness, and a separate
selector decision.