# Source ledger & data inventory

Reviewed 2026-10-20 UTC. “Read” means the returned page text was inspected; it is
not a blanket certification of every linked resource. All performance claims
require their own evidence class. Official sources support the quoted general
facts, not an assertion that an experimental detector will improve DTI.

| Source | What was verified / read | Scope and limitations |
|---|---|---|
| [DrivenData problem / metric / format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Both returned chunks; fault-location target, new expert labels, triangular distance weighting, alpha/beta, float32 GeoTIFF requirements, public/private and expanded labels. | Does not authenticate owner mirrors. Outside-footprint null/NaN text differs from the local all-finite export. |
| [Official September rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Relevant sections 3.1–3.6 in returned chunks 2–3, plus contents/executive summary. GeoTIFF entry, weekly cap, one final selection, code reproducibility and AI disclosure. | Not a full legal/eligibility review; current authenticated remaining quota not accessed. |
| [DrivenData rules page](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) | Links official rules resource. | No competition-account session inferred. |
| [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Public first row read at review date. | PUBLIC-LEADERBOARD-OBSERVATION, not a file-specific submission receipt or current quota. Historical values in the prompt are not automatically current. |
| [Organizer reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) | Pinned README read; CPU-only and GPU training options documented. | Not executed or a substitute for this repository's missing fitted model. |
| [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Release description, terrain-clearance caveat, survey blocks and processing; DOI 10.5066/P93LGLVQ; page marks work CC0. | Binary grids not downloaded here; release metadata do not make a magnetic edge a verified fault. |
| [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) | Hidden-system exploration goal and publications/resources list. | Background context, not hidden competition truth. |
| [GDR regional compilation](https://gdr.openei.org/submissions/1391) | Resource descriptions and links; landing page labels public CC-BY 4.0. | Layer-specific license/coverage and binary access still require checking before use. |
| [H33 reference site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | Landing page read; explicitly says no organizer scores for repository artifacts. Pinned build/validation source inspected. | Owner site, NOT an official competition receipt; no predictions copied as a new submission. |
| [H33 reference source](https://github.com/buffedlizard55-lab/GEMSDOE32/tree/98901f3130e8704f4254f173784589e63f000673) | Method source plus actual historical TIFF inspected for education; bytes/range/count receipt retained. | A historical TIFF's format does not prove its reported score or causal advantage. |
| [Shared template](https://github.com/buffedlizard55-lab/60GEMSDOE/tree/32024716f218d06a94e01464157392119c03cb15/src/gems57) | Local SHA-256 and upstream Git tree/blob matches for all vendored modules. | Shared owner code, not organizer-authenticated. No private edits. |
| [Neighbor handoff](https://github.com/buffedlizard55-lab/GEMSDOE69/blob/ae3b9b513500fbf31660cf0a19bf161483478c67/HANDOFF.md) | Negative/no-submit verdict and inherited registry context read. | Not this repository's assigned lane or current holdout best. |
| [Registry witness](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/main/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif) | Downloaded immutable Git blob and checked SHA-256, alignment, support on sample footprint. | Large binary lives only in ignored cache. One witness proves failure, not exhaustive registry clearance. |

## Inputs actually present and verified

| Input | SHA-256 | Use / provenance |
|---|---|---|
| `sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | Pinned owner mirror; finite values define bridge-relative footprint. Not a prediction download. |
| `existing_faults.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | Public mapped faults, not the hidden expert labels. |
| Dense registry witness (cache only) | `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be` | Positive throughout the sample footprint; literal overlap obstruction. |

Grid measurement from these mirrors: EPSG:32611; height × width 3730 × 3292;
transform `(100, 0, 243350, 0, -100, 4508550)`; 100 m pixels.
These are grid/data measurements, **not performance scores**.

## Not verified or completed

- No authenticated DrivenData binary download, submission-page receipt, quota
  receipt, organizer acceptance, or artifact-specific ORGANIZER-CONFIRMED score.
- No newly trained model, same-evaluator holdout best, feature AUC, or measured
  scientific candidate result. HOLDOUT-DTI and confidence intervals remain null.
- No complete fresh audit of all family sites. The prompt retains the full link
  list; the inherited registry is historical and explicitly scoped.
- No complete scientific-literature survey or externally verified new geothermal
  discovery. Proposed physical signatures remain falsifiable hypotheses.
- No binary retrieval of the GDR paleogeothermal zip or original USGS downloads;
  the shell host policy excludes those domains.

[Reading notes and exact source excerpts](../evidence/sources/official-reading-notes.md)
