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
    p4b = card['instrument_b_prime_proxy'].get('p4_reference')
    ball = card['instrument_b_unrestricted']['candidate']
    ballref = card['instrument_b_unrestricted']['h33_reference']
    u = card['uniqueness_detail']
    delta = card['paired_b_prime_vs_h33']
    dp4 = card['paired_b_prime_vs_p4']
    can = card['canaries']
    promoted = card['verdict'] == 'promote'
    status = 'PROMOTED TO SELECTOR' if promoted else 'DOWNLOADABLE — NOT PROMOTED'
    head = f'''# GEMSDOE70 — geothermal fault research

## Submission status: **{status}**

A unique, format-validated competition TIFF is published:
`docs/downloads/{card['submission_name']}.tif` (sha256 `{card['raster_sha256']}`).
**Download: yes. Submit a weekly slot: {'recommended by our evidence (selector decides)' if promoted else 'not recommended by our evidence'}** — verdict
`{card['verdict']}` on the pre-registered target-like gate. No weekly slot was used.

- [Evidence site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [How to submit](docs/submission.html)
- [Run card](evidence/run_card.json) · [Uniqueness audit](evidence/p5hgb/uniqueness.json)
- [Why H33 scored 0.2778](docs/h33-analysis.md) · [Preregistered hypotheses](docs/hypotheses.md)
- [Limitations / next steps](docs/irregularities.md) · [Session handoff](HANDOFF.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md and HANDOFF.md.

## What was measured this session (session 3, experiment 5)

The handoff's top priority: **supervised within-halo ranking** — HistGradientBoosting over the
19-band physics stack + visible-catalogue geometry, trained on the SGMC off-catalogue proxy with
leave-one-quadrant-out, emitted through the measured P4 coverage-stratified design
({card['registered_parameters']['dot_count']:,} binary dots, all off-catalogue). Preregistered in
`docs/hypotheses.md` (Phase-5 addendum) before the run; canaries, gates and uniqueness receipts in
`evidence/p5hgb/`.

| Instrument | Candidate | H33 reference | P4 reference | Result |
|---|---:|---:|---:|---|
| A · shared hide-and-recover catalogue holdout (label-independent) | {d['dti']:.4f} | {dref['dti']:.4f} | — | beats random 0.0531 |
| B′ · SGMC proxy d ≥ 3 px, LOQO (pre-registered target-like gate) | {b['dti']:.4f} | {bref['dti']:.4f} | {p4b['dti']:.4f} | **H33 wins, Δ {delta['delta']:+.4f} {delta['ci95']}** |
| B · unrestricted SGMC proxy, LOQO | {ball['dti']:.4f} | {ballref['dti']:.4f} | — | H33 wins |

Scientific reading (a deliverable, not a failure to hide): the model learns the proxy
(out-of-fold AUC {can['model_oof_auc_vs_proxy']:.3f}) yet places dots no better than the pure-geometry
halo — statistically indistinguishable from P4 on B′ (Δ {dp4['delta']:+.4f} {dp4['ci95']}). The
SGMC off-catalogue proxy does not contain enough transferable within-halo information for this
feature set; the ceiling is the label source, not the learner. No feature canary fired
(worst A-truth AUC {can['worst_feature_auc_vs_a_truth']:.3f}); disclosure: 31.9 % of A-truth pixels
lie within 3 px of proxy pixels (SGMC re-draws), and B′/B share the training label source.

**Uniqueness (corrected):** {u['registry_rasters_checked']} archived rasters checked on the score
surface before placement (worst ρ {u['surface_precheck']['worst_spearman_full_footprint']:.3f}) and
on the final dots (worst mutual overlap {u['worst_dot_overlap']:.3f}, limit 0.70; worst Spearman
{u['worst_spearman_full_footprint']:.3f}, limit 0.90; {u['duplicate_count']} duplicates).

## Earlier sessions (summaries)

Sessions 1–2 ran four preregistered geometry experiments (all negative on B′; receipts in
`evidence/phase2..4/`), audited why H33 scored 0.2778 (`docs/h33-analysis.md`: emission geometry,
not geology), and fixed two shared-uniqueness defects (binary dots; mutual overlap), reported in
`evidence/upstream_fix_report.md` and pinned in `registry/template_pin.json` with
`all_identical: false`.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py        # pinned owner mirrors, not organizer auth
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/run_experiment_v5.py   # registered Phase-5 run, regenerates the artifact
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

`scripts/run_experiment_v2.py`/`v3.py`/`v4.py` reproduce the earlier negatives; the phase-1
negative is archived in `evidence/history/phase1_negative/`.

## Next session

The proxy ceiling is now measured — see `docs/irregularities.md` for the revised priorities
(independent truth source, band widening, mass calibration), ranked by expected information gain.

## Complete retained project prompt

Historical statements below are user-supplied requirements and claims, not verified results. No
leaderboard value becomes ORGANIZER-CONFIRMED by being copied into this README. The dedicated
PROJECT_BRIEF.md is the source for this embedded copy.

<details>
<summary>Read the complete supplied project brief before every session</summary>

'''
    tail = '\n</details>\n'
    e2_note = ''
    e2p = ROOT / 'evidence/e2/run_card.json'
    if e2p.is_file():
        import json as _json
        _e2 = _json.loads(e2p.read_text())
        _d = _e2['holdout_dti']
        e2_note = (f"\n## Parallel E2 lane (integrated PR #16) — second review candidate, DO NOT SUBMIT YET\n\n"
                   f"Alluvial-step ranking, 38,000 dots: catalogue HOLDOUT-DTI {_d['dti']:.4f} "
                   f"[{_d['ci95'][0]:.4f}, {_d['ci95'][1]:.4f}] (beats random, loses to D28 0.0919) → negative. "
                   f"File `docs/downloads/gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif` "
                   f"(selector-review only; complete corrected uniqueness scan pending). "
                   f"Evidence: `evidence/e2/`, preregistration `docs/preregistration-e2.md`. "
                   f"Public leader at organizer-page read 2026-10-20: 0.4413 (`evidence/leaderboard_read.json`).\n")
    (ROOT / 'README.md').write_text(head + e2_note + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
