"""Embed the entire retained user brief behind an accurate, evidence-bound summary."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    d = card['instrument_a_holdout']['candidate']
    dref = card['instrument_a_holdout']['h33_reference']
    b = card['instrument_b_prime_proxy']['candidate']
    bref = card['instrument_b_prime_proxy']['h33_reference']
    ball = card['instrument_b_unrestricted']['candidate']
    ballref = card['instrument_b_unrestricted']['h33_reference']
    u = card['uniqueness_detail']
    delta = card['paired_b_prime_vs_h33']
    head = f'''# GEMSDOE70 — geothermal fault research

## Submission status: **DOWNLOADABLE — NOT PROMOTED**

A unique, format-validated competition TIFF is published:
`docs/downloads/{card['submission_name']}.tif` (sha256 `{card['raster_sha256']}`).
**Download: yes. Submit a weekly slot: not recommended by our evidence** — verdict
`{card['verdict']}` on the pre-registered target-like gate. No weekly slot was used.

- [Evidence site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [How to submit](docs/submission.html)
- [Run card](evidence/run_card.json) · [Uniqueness audit](evidence/phase4/uniqueness.json)
- [Why H33 scored 0.2778](docs/h33-analysis.md) · [Preregistered hypotheses](docs/hypotheses.md)
- [Limitations / next steps](docs/irregularities.md) · [Session handoff](HANDOFF.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md and HANDOFF.md.

## What was measured this session

Three preregistered experiments (plus the archived phase-1 negative) on the pinned 100 m grid,
alpha = 0.2, beta = 0.8, 300 m triangular kernel, pooled terms and a paired 20 km spatial-cluster
bootstrap. Exactly {card['registered_parameters']['dot_count']:,} binary dots are emitted, all
off-catalogue.

| Instrument | Candidate | H33 reference | Result |
|---|---:|---:|---|
| A · shared hide-and-recover catalogue holdout | {d['dti']:.4f} | {dref['dti']:.4f} | candidate wins |
| B′ · SGMC off-catalogue proxy, d ≥ 3 px (pre-registered target-like) | {b['dti']:.4f} | {bref['dti']:.4f} | **H33 wins, delta = {delta['delta']:+.4f} {delta['ci95']}** |
| B · unrestricted SGMC proxy (contains map-duplication band) | {ball['dti']:.4f} | {ballref['dti']:.4f} | candidate wins |

Instrument A is biased against the real task (it rewards dots beside mapped traces). Instrument B
is contaminated at short range: 12.5 % of SGMC-only pixels sit within 2 px of the catalogue and
21.4 % within 3 px. B′ removes that band and is the pre-registered gate; it is negative, so the
artifact is published but not promoted. Nothing here is an organizer-confirmed score.

**Uniqueness (corrected):** {u['registry_rasters_checked']} archived rasters checked; worst mutual
overlap {u['worst_dot_overlap']:.3f} (limit 0.70); worst Spearman {u['worst_spearman_full_footprint']:.3f}
(limit 0.90). Forward-only overlap reaches {u['worst_forward_overlap']:.2f} against a dense lattice
whose halo covers the whole footprint — which is why the two-direction test was adopted.

## Two fixes to the shared tool (reported, not silently forked)

1. Dots are binary (`|value - 1| < 1e-6`), not every positive value; otherwise one continuous
   registry surface blocks every candidate.
2. Duplication requires **mutual** overlap (forward and reverse); three dense lattices whose 3-px
   halos cover 100 % of the footprint would otherwise block every candidate.

Both are in `vendor/gems57/uniqueness.py`; `registry/template_pin.json` records the new hash with
`all_identical: false`; full text in `evidence/upstream_fix_report.md`.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py        # pinned owner mirrors, not organizer auth
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/run_experiment_v4.py   # registered Phase-4 run, regenerates the artifact
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

`scripts/run_experiment_v2.py` and `run_experiment_v3.py` reproduce the two earlier negatives
(receipts in `evidence/phase2/` and `evidence/phase3/`). The phase-1 negative is archived in
`evidence/history/phase1_negative/`.

## Next session

Supervised within-halo ranking trained on the SGMC off-catalogue proxy with leave-one-quadrant-out
(features: 19-band stack, lidar scarp, GeoDAWN radiometrics, catalogue geometry). The geometry-only
approach has been measured to its limit — see `docs/irregularities.md`.

## Complete retained project prompt

Historical statements below are user-supplied requirements and claims, not verified results. No
leaderboard value becomes ORGANIZER-CONFIRMED by being copied into this README. The dedicated
PROJECT_BRIEF.md is the source for this embedded copy.

<details>
<summary>Read the complete supplied project brief before every session</summary>

'''
    e3 = json.loads((ROOT / 'evidence/run_card_e3_amended.json').read_text())
    e3d = e3['holdout_dti']
    e3_block = f'''
## Parallel-session candidate E3 (scarp curvature) — selector must score it on B′ before choosing

A second unique, format-validated TIFF from a parallel session is published:
`docs/downloads/{e3['submission_name']}.tif` (sha256 `{e3['raster_sha256']}`),
note ({len(e3['submission_note'])} chars): `{e3['submission_note']}`.
DEM scarp-curvature ranking, {e3['n_final_dots']:,} dots. Catalogue hide-and-recover
(seed-40) HOLDOUT-DTI {e3d['dti']:.4f} [{e3d['ci95'][0]:.4f}, {e3d['ci95'][1]:.4f}]
({e3d['withheld_positive_pixels']:,} withheld) — promoted to selector on that
instrument, but **not yet scored on instrument B′**, so it does not supersede the
Phase-4 verdict above. Score this exact TIF on B′ first. Evidence:
`evidence/run_card_e3_amended.json` (with erratum; E2 gated variant negative).
Site page: `docs/e3-candidate.html`. No slot used for either candidate.

'''
    tail = '\n</details>\n'
    (ROOT / 'README.md').write_text(head + e3_block + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
