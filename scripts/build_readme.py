"""Embed the retained user brief behind an accurate, evidence-bound Phase-5 summary."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    card = json.loads((ROOT / 'evidence/phase5/run_card.json').read_text())
    c = json.loads((ROOT / 'evidence/phase5/instrumentC_halo.json').read_text())['scores']
    cb = json.loads((ROOT / 'evidence/phase5/instrumentB_all.json').read_text())['scores']
    ca = json.loads((ROOT / 'evidence/phase5/instrumentA_holdout.json').read_text())['scores']
    rk = json.loads((ROOT / 'evidence/phase5/ranking_skill.json').read_text())
    u = json.loads((ROOT / 'evidence/phase5/uniqueness.json').read_text())
    delta = json.loads((ROOT / 'evidence/phase5/instrumentC_halo.json').read_text())['paired_differences']['h33_reference']
    folds = rk['fold_auc'].values()
    head = f"""# GEMSDOE70 — geothermal fault research

## Submission status: **PROMOTED — DOWNLOAD AND SUBMIT (calibrated test)**

A unique, format-validated competition TIFF is published:
`docs/downloads/{card['submission_name']}.tif` (sha256 `{card['raster_sha256']}`; a one-TIFF ZIP is
published alongside). **Download and submit: yes.** All five pre-registered Phase-5 gates passed.
**There is no organizer-confirmed score**: the live leaderboard is the only test, and the returned
value must be recorded from the submission-page receipt. If it lands at or below 0.2778 the
hypothesis is negative and must be written down as such.

- [Evidence site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [How to submit](docs/submission.html)
- [Run card](evidence/phase5/run_card.json) · [Uniqueness](evidence/phase5/uniqueness.json) · [Preregistration](docs/preregistration-p5.md)
- [Why H33 scored 0.2778](docs/h33-analysis.md) · [Limitations / next steps](docs/irregularities.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md and HANDOFF.md.

## Phase 5 — what was measured

Spatial four-fold (by quadrant) `HistGradientBoostingClassifier` on 43 features (19-band stack,
12 lidar-scarp bands, 4 radiometric, 4 GeoDAWN extension bands, catalogue density, relief,
log distance to catalogue). Label = SGMC faults off-catalogue by at least 3 px. The published
raster is the out-of-fold field: every dot is ranked by a model that never saw its quadrant.
Emission: one dot per 5 x 5 px block at the block maximum, 4 px NMS, {card['emission']['count']:,}
dots in the 2.4-32 px halo.

| Instrument | Candidate | H33 | P4 | Paired candidate - H33 |
|---|---:|---:|---:|---:|
| **C - halo surrogate (primary)** | {c['candidate']['dti']:.4f} | {c['h33_reference']['dti']:.4f} | {c['p4_reference']['dti']:.4f} | {delta['delta']:+.4f} [{delta['ci95'][0]:+.4f}, {delta['ci95'][1]:+.4f}] |
| B - unrestricted SGMC proxy | {cb['candidate']['dti']:.4f} | {cb['h33_reference']['dti']:.4f} | {cb['p4_reference']['dti']:.4f} | not the gate |
| A - catalogue holdout | {ca['candidate']['dti']:.4f} | {ca['h33_reference']['dti']:.4f} | - | structurally hostile to a global halo emission |

Ranking skill: mean held-out AUC **{rk['mean_fold_auc']:.4f}** (fold range
{min(v['auc'] for v in folds):.3f}-{max(v['auc'] for v in folds):.3f}); raw pooled
{rk['pooled_out_of_fold_auc_raw']:.4f}; rank-normalised pooled
{rk['pooled_out_of_fold_auc_rank_normalised']:.4f}. Worst single-feature canary AUC
{card['canary_worst_auc']:.4f} (limit 0.90). Uniqueness: {u['registry_rasters_checked']} archived
rasters, worst mutual overlap {u['worst_dot_overlap']:.3f} (limit 0.70), worst |rho|
{abs(u['worst_spearman_full_footprint']):.3f} (limit 0.90).

### The instrument correction that made Phase 5 possible

The catalogue is the USGS Quaternary fault database: 99.998 % of rasterised QFaults trace pixels
lie within 3 px of `existing_faults.tif` (`evidence/phase5/qfaults_catalogue_overlap.json`). SGMC
is the only independent inventory in the cached inputs (3,666 shared px, 78,485 not). The Phase-4
gate used the *unrestricted* SGMC proxy, whose positives are spread across the whole domain; on
that instrument a domain-wide random field can beat a halo field, while the live ordering is the
opposite. Phase 5 restricts the proxy to the 0.2-3.2 km halo (instrument C), which is where the
live evidence says the hidden truth is, and keeps instrument B for continuity.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_data.py        # SHA-256-pinned owner mirrors, not organizer auth
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/run_experiment_p5.py # regenerates the artifact, instruments and card
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

Earlier phases: `run_experiment_v4.py` (P4), `run_experiment_v2/v3.py`, `evidence/e2/`,
`evidence/history/phase1_negative/`.

## Next session

1. Get the live receipt for this file and record it as ORGANIZER-CONFIRMED.
2. If the score is <= 0.2778, test the density hypothesis on instrument C (37,654 vs 60,000 dots at
   matched geometry) before spending another slot.
3. Cross-inventory check: train on SGMC and score withheld catalogue components (and vice versa)
   to measure generic fault-detection skill independently of the proxy.
4. Upstream the two uniqueness fixes and add the instrument-C definition to the shared template.

## Complete retained project prompt

Historical statements below are user-supplied requirements and claims, not verified results. No
leaderboard value becomes ORGANIZER-CONFIRMED by being copied into this README. The dedicated
PROJECT_BRIEF.md is the source for this embedded copy.

<details>
<summary>Read the complete supplied project brief before every session</summary>

"""
    tail = '\n</details>\n'
    e2_note = ''
    e2p = ROOT / 'evidence/e2/run_card.json'
    if e2p.is_file():
        e2 = json.loads(e2p.read_text())
        d = e2['holdout_dti']
        e2_note = (f"\n## Historical: parallel E2 lane (PR #16) - negative, do not submit\n\n"
                   f"Alluvial-step ranking, 38,000 dots: catalogue HOLDOUT-DTI {d['dti']:.4f} "
                   f"[{d['ci95'][0]:.4f}, {d['ci95'][1]:.4f}]; beats random, loses to D28 0.0919. "
                   f"File `docs/downloads/gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif`. "
                   f"Evidence `evidence/e2/`. Public leader at organizer-page read 2026-10-20: "
                   f"0.4413 (`evidence/leaderboard_read.json`).\n")
    (ROOT / 'README.md').write_text(head + e2_note + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
