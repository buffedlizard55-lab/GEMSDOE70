"""Embed the retained user brief after an honest, evidence-bound current status."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    stop = json.loads((ROOT / 'evidence/literal_overlap_stop.json').read_text())
    archived = json.loads((ROOT / 'evidence/phase4/run_card.json').read_text())
    row = stop['archive_checks'][0]
    coverage = stop['coverage']
    lo, hi = archived['instrument_a_holdout']['candidate']['ci95']
    if (card.get('verdict') != 'negative' or card.get('raster_sha256') is not None
            or row['sha256'] != archived['raster_sha256']
            or not row['duplicate_under_user_rule']):
        raise ValueError('Current negative card and literal-stop receipt do not agree')
    summary = f'''# GEMSDOE70 — geological fault-discovery workbench

## DO NOT SUBMIT — no eligible *new* TIFF in this run

**Download a new competition TIFF: NO. Spend a weekly submission slot: NO.**
No new raster was generated or scored on a spatial holdout in this session; the
parallel-run prompt does not supply its promised single-method lane paragraph.
Generating or recommending an arbitrary file would violate the stop rule, not
maximize the probability of a valid win. No portal acceptance or ORGANIZER-CONFIRMED
score is available for this run.

- [Executive summary and exact future submission steps](docs/executive-summary.html) ·
  [Current negative JSON run card](evidence/run_card.json) ·
  [Reproducible forward-overlap stop](evidence/literal_overlap_stop.json)
- [Four ranked, **untested** geological hypotheses](docs/hypotheses-next.md) ·
  [Historical H33 analysis](docs/h33-analysis.md) ·
  [Limitations and next steps](docs/irregularities.md) · [Sources](docs/sources.html)
- [Three independent review passes](evidence/review_passes.md) ·
  [Retraction of misleading historical direct-URL approval JSON](evidence/publication_retractions.json)
  (exact bytes preserved under `evidence/`; one archived split has unresolved merge markers).
- [Public website](https://buffedlizard55-lab.github.io/GEMSDOE70/) (deployment can lag this branch).

**Archived P4 is NOT a new submission:**
[`{archived['submission_name']}.tif`](docs/downloads/{archived['submission_name']}.tif)
(sha256 `{row['sha256']}`) passes the shared *local format* validator, but
**{row['forward_overlap_within_3px']:.0%} of its dots** fall within 3 pixels of the
hash-verified binary registry witness, above the user's 70% forward-overlap
stop. E2 and discordance archive TIFFs also each measure 100% against this one
witness. Their older mutual-overlap exemption is not permission to submit.
Archive downloads are for forensic learning only. The validator checks [0,1],
no NaN inside the sample footprint, one float32 band, EPSG:32611 and exact
shape/transform; it does **not** prove portal acceptance or uniqueness.

The witness covers **{coverage['witness_halo_fraction_off_catalogue']:.4%}** of the
{coverage['off_catalogue_cells']:,} off-catalogue cells within 3 pixels, leaving
**{coverage['witness_halo_uncovered_off_catalogue']:,}** uncovered. Earlier notes
claiming universal 100% coverage were wrong. Even if a future method used all
uncovered cells as dots, a {row['binary_dots']:,}-dot file would have **at least
{coverage['min_possible_forward_overlap_at_archived_budget']:.4%}** overlap with
this single witness. That is an optimistic geometric bound, not a model score;
it does not rule out all smaller budgets or certify any particular file.

## What the historical best teaches (without inventing a score)

[H33 byte audit](evidence/h33_audit.json) finds 37,654 binary dots that are an
exact pruned subset of H27, itself a subset of D28: 2,545 near-catalogue dots
were removed from H27 without adding any. Under the organizer's published
[DTI metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
such thinning *can* lower false-positive mass while retaining truth coverage.
That explains why the user-reported 0.2778 is plausible; it does **not** prove
causation or establish an ORGANIZER-CONFIRMED H33 receipt. A source-site page
itself describes its primary as unscored. The public leaderboard displayed
0.4413 in a dated page read on 2026-10-20
([receipt](evidence/leaderboard_read.json)); this is a public observation, NOT
a file-specific score or a fixed current target. The brief also contains
conflicting historical numbers (0.3774 and 0.3195); do not treat them as current.

The historical Phase-4 **HOLDOUT-DTI** on the mapped catalogue was
{archived['instrument_a_holdout']['candidate']['dti']:.4f},
95% CI [{lo:.4f}, {hi:.4f}],
{archived['instrument_a_holdout']['candidate']['withheld_positive_pixels']:,}
withheld positives (gems57-pooled-hide-v2). It is NOT a new holdout or a
leaderboard estimate. P4's independent SGMC **proxy-DTI** gate was negative
against H33; the [historical P4 card](evidence/phase4/run_card.json) states
its scope. The user requires a new method to beat a *same-split, visible-only*
current best before a weekly slot is considered.

## Reproduce the current negative without generating dots

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/audit_literal_overlap.py --check
.venv/bin/python scripts/make_run_card.py
.venv/bin/python scripts/release_gate.py --expect-negative
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

The witness is fetched through a SHA-pinned public GitHub owner mirror into the
ignored `.cache/` directory if missing. For the *future* science run, the
19-band stack was independently restored into `.cache/data/` with
`.venv/bin/python scripts/restore_data.py` and verified against SHA-256
`4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`;
owner-mirror integrity is not organizer authentication. The DrivenData data tab
redirects to login. The user must verify eligibility, the organizer-format
sample, data-sharing rights, the remaining weekly quota and any eventual
submission-page receipt. No password or token is requested or stored here.

## Own the outcome: next work in order

1. Obtain the missing method-lane assignment and resolve the forward vs mutual
   definition **once upstream** in the shared template. A local exemption or a
   changed filename is not a fix. The repo's vendored uniqueness file already
   differs from its upstream pin; see [upstream report](evidence/upstream_fix_report.md)
   and [new discrepancy report](evidence/literal_overlap_stop.json).
2. Preregister one untried method on untouched blocks; leak-canary each feature;
   rebuild any catalogue features using visible faults only. Compare pooled
   HOLDOUT-DTI and paired 95% CI to a correctly rebuilt same-split incumbent.
3. Scan the full accessible registry on the **surface before placement** and on
   final dots. If either hits rho > 0.90 or forward overlap > 0.70, stop;
   do not write/advertise a candidate. If all gates pass, use the shared
   writer and revalidate exact GeoTIFF bytes with no NaN inside the footprint
   and values in [0,1].
4. Only a separate selector checks live weekly quota (official rules allow up
   to three per week) and chooses one eligible file. Document any organizer
   score only from a submission-page receipt; disclose AI assistance in the
   required narrative.

The source table is a **dated** audit, not a real-time leaderboard feed. The
scheduled source-health workflow tests link availability only; it does not
silently rewrite scientific claims or publish unauthenticated scores. Every
negative result, archive SHA and irregularity is retained for review.

## Complete retained user project brief

Historical claims below are user-supplied, **not** measured or organizer-confirmed
by being copied here. Read the complete text alongside [AGENTS.md](AGENTS.md)
and [HANDOFF.md](HANDOFF.md) at the beginning of each session.

<details>
<summary>Read the retained prompt and the latest user addendum</summary>

'''
    brief = (ROOT / 'PROJECT_BRIEF.md').read_text()
    (ROOT / 'README.md').write_text(summary + brief + '\n</details>\n')


if __name__ == '__main__':
    main()
