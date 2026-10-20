"""Embed the entire retained user brief behind an accurate, evidence-bound summary."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    review = json.loads((ROOT / 'evidence/literal_protocol_review.json').read_text())
    e3_literal = review['correlation_overlap_vs_registry']
    p4_literal = review['previous_p4_review']['correlation_overlap_vs_registry']
    e3_witness_count = len(e3_literal['witnesses'])
    e3_worst_overlap = max((r['forward_overlap'] for r in e3_literal['witnesses']), default=0.0)
    d = card['instrument_a_holdout']['candidate']
    dref = card['instrument_a_holdout']['h33_reference']
    b = card['instrument_b_prime_proxy']['candidate']
    bref = card['instrument_b_prime_proxy']['h33_reference']
    ball = card['instrument_b_unrestricted']['candidate']
    ballref = card['instrument_b_unrestricted']['h33_reference']
    u = card['uniqueness_detail']
    delta = card['paired_b_prime_vs_h33']
    head = f'''# GEMSDOE70 — geothermal fault research

> **CURRENT REVIEW: DO NOT SUBMIT EITHER TIFF.** P4 has {len(p4_literal['witnesses'])} literal
> forward-overlap witnesses in 62 archived rasters. The merged parallel E3 candidate has
> {e3_witness_count} witnesses at both surface and final-dot stages (maximum {e3_worst_overlap:.2f});
> its 63 locally checked rasters do not cover the inherited 862-entry inventory. Saturation-adjusted clearance
> does not override the prompt. Existing TIFFs are for review only; this review generated none and
> used no slot. [Current review](docs/protocol-review.md) · [Current JSON run card](evidence/literal_protocol_review.json).

## Submission status: **DOWNLOAD FOR REVIEW ONLY — DO NOT SUBMIT**

**CURRENT PROTOCOL STOP:** The P4 and E3 candidates fail the literal forward-overlap rule. Other
archived review TIFFs are not cleared for this prompt either. P4's historical mutual-overlap
clearance is not current clearance; E3's saturation-adjusted result is also not clearance. No new
TIFF or experiment was generated in this review. The merged E3 lane
reports three experiments and has not been scored on B′. See the [current protocol review](docs/protocol-review.md).

**Download: yes, for inspection only. Submit: no.** The older P4 TIFF remains at
`docs/downloads/{card['submission_name']}.tif` (sha256 `{card['raster_sha256']}`); the merged E3
candidate and its strict re-audit are linked below. No organizer-confirmed score or weekly slot is
reported.

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

Resolve the literal forward-overlap rule with the selector, obtain the complete registry and an
explicit single-lane assignment, then re-check the remaining experiment budget. Do not run another
model, generate a new TIFF, or use a weekly slot while either candidate has a literal witness or the
registry scope is incomplete. E3's B′ score is unreported and its candidate still fails the current
uniqueness rule; these facts do not authorize bypassing the stop.

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
    e3_note = ''
    e3p = ROOT / 'evidence/run_card_e3_amended.json'
    if e3p.is_file():
        import json as _json3
        _e3 = _json3.loads(e3p.read_text())
        _d3 = _e3['holdout_dti']
        e3_note = (f"\n## Parallel E3 scarp lane (PR #17) — selector must score it on B′ before choosing\n\n"
                   f"DEM scarp-curvature ranking, {_e3['n_final_dots']:,} dots: catalogue HOLDOUT-DTI "
                   f"{_d3['dti']:.4f} [{_d3['ci95'][0]:.4f}, {_d3['ci95'][1]:.4f}] "
                   f"({_d3['withheld_positive_pixels']:,} withheld, seed-40) → promote-to-selector on "
                   f"that instrument only; **B′ not yet scored**. File "
                   f"`docs/downloads/{_e3['submission_name']}.tif` (sha256 `{_e3['raster_sha256']}`), "
                   f"note ({len(_e3['submission_note'])} chars): `{_e3['submission_note']}`. "
                   f"Strict current-prompt audit: {len(e3_literal['witnesses'])} forward witnesses in "
                   f"both surface and final-dot checks (worst {e3_worst_overlap:.2f}); the 63 locally "
                   f"checked rasters do not cover the inherited 862-entry inventory. DO NOT SUBMIT; review "
                   f"download only. Evidence: `evidence/run_card_e3_amended.json` (erratum-completed; "
                   f"gated E2 negative); frozen drivers renamed `scripts/run_experiment_e{{2,3}}_scarp.py` "
                   f"at merge (byte-identical; canonical paths hold the PR #16 lane's drivers). "
                   f"Site page: `docs/e3-candidate.html`. No slot used for any candidate.\n")
    (ROOT / 'README.md').write_text(head + e2_note + e3_note + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
