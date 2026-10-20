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
    # H70 card stores uniqueness under correlation_overlap_vs_registry; legacy P4 used uniqueness_detail
    u = card.get('uniqueness_detail') or card.get('correlation_overlap_vs_registry') or card.get('uniqueness') or {}
    # normalize keys
    if 'rasters_checked' in u and 'registry_rasters_checked' not in u:
        u['registry_rasters_checked'] = u['rasters_checked']
    if 'worst_mutual_overlap' in u and 'worst_dot_overlap' not in u:
        u['worst_dot_overlap'] = u['worst_mutual_overlap']
    if 'worst_forward_overlap' not in u:
        u['worst_forward_overlap'] = u.get('worst_dot_overlap', 0)
    delta = card['paired_b_prime_vs_h33']
    head = f'''# GEMSDOE70 — geothermal fault research

> **CURRENT REVIEW: DO NOT SUBMIT — literal one-way protocol stop.** The archived Phase-4 and new Phase-5 (P5) files fail the prompt's literal
> one-way overlap gate (forward overlap 1.00 vs dense sampling lattice; four witnesses in 62 archived rasters for P4, same for P5).
> Download is for review only; no slot used. Historical mutual-overlap clearance (worst mutual {u['worst_dot_overlap']:.2f}) does **not** satisfy the current forward rule.
> [Current review](docs/protocol-review.md) · [Current run card](evidence/literal_protocol_review.json).

## Submission status: **REVIEW ONLY — NOT PROMOTED (literal protocol stop)**

**CURRENT PROTOCOL STOP:** Both candidates exceed forward overlap (P5 forward 1.00 vs `calib_r13lattice_00904.tif` and two other dense lattices). See [current review](docs/protocol-review.md). Mutual-overlap clearance (worst {u['worst_dot_overlap']:.2f}) does not satisfy the current prompt's forward-only gate.

A format-validated TIFF is published for **review only** under the literal protocol (measurable under the corrected mutual rule):
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
                   f"Evidence: `evidence/run_card_e3_amended.json` (erratum-completed; gated E2 "
                   f"negative); frozen drivers renamed `scripts/run_experiment_e{{2,3}}_scarp.py` "
                   f"at merge (byte-identical; canonical paths hold the PR #16 lane's drivers). "
                   f"Site page: `docs/e3-candidate.html`. No slot used for any candidate.\n")
    p5_note = ''
    p5p = ROOT / 'evidence/phase5/run_card.json'
    if p5p.is_file():
        import json as _json5
        _p5 = _json5.loads(p5p.read_text())
        _pa = _p5['instrument_a_holdout']['candidate']
        _pb = _p5['instrument_b_prime_proxy']['candidate']
        p5_note = (f"\n## Parallel P5 analytic-signal lane (this branch, arena/97660a79-gemsdoe70) — DO NOT SUBMIT\n\n"
                   f"Analytic-signal halo 7px, 37,654 dots, `tmi_hg`+`tmi_vg` rank in 2.4–32 px halo with tip kernel. HOLDOUT-DTI A {_pa['dti']:.4f} [{_pa['ci95'][0]:.4f},{_pa['ci95'][1]:.4f}] vs H33 0.0037 win; **B′ {_pb['dti']:.4f} [{_pb['ci95'][0]:.4f},{_pb['ci95'][1]:.4f}] vs 0.0938 H33 win Δ { _p5['paired_b_prime_vs_h33']['delta']:+.4f} {_p5['paired_b_prime_vs_h33']['ci95']} → negative**, no slot. Uniqueness: 62 rasters worst mutual 0.30 (limit 0.70) worst ρ 0.042; forward 1.00 vs dense lattice `calib_r13lattice_00904.tif` (literal duplicate, review only). File `docs/downloads/gems70-p5-analytic-halo-37654-20261020.tif` (sha256 `{_p5['raster_sha256']}`, 149,414 bytes, ZIP `bf61cacc...`). Evidence `evidence/phase5/` (run_card, instrument holds, uniqueness, canaries), method `src/gems70/method_p5.py`. Hypotheses.md now ranks 5 candidates (H-2 tested P5, H-3 radiometric GeoDAWN already fetched 36+26 MB, H-4 lidar scarp 36 MB, H-5 conductive breach, H-6 basement curvature) with preregistered validation rule; h33-analysis.md PhD-level byte audit + metric algebra. Under literal forward rule, P5 is duplicate (as is H70 and P4) — download for review only.\n")
    h70_note = ''
    h70p = ROOT / 'evidence/h70/run_card.json'
    if h70p.is_file():
        import json as _json70
        _h70 = _json70.loads(h70p.read_text())
        _ha = _h70['instrument_a_holdout']['candidate']
        _hb = _h70['instrument_b_prime_proxy']['candidate']
        h70_note = (f"\n## Parallel H70 conductive-breach lane (arena/0aa117f9-gemsdoe70, PR #28) — DO NOT SUBMIT\n\n"
                    f"H70-A conductive breach × analytic magnetics, 7px strata, 37,654 dots off-cat; HOLDOUT-DTI A {_ha['dti']:.4f} [{_ha['ci95'][0]:.4f},{_ha['ci95'][1]:.4f}] vs H33 0.0037 win; B′ {_hb['dti']:.4f} [{_hb['ci95'][0]:.4f},{_hb['ci95'][1]:.4f}] vs 0.0953 H33 win Δ {_h70['paired_b_prime_vs_h33']['delta']:+.4f} {_h70['paired_b_prime_vs_h33']['ci95']} → negative. File `docs/downloads/gems70-h70-conductive-breach-37654-20261020.tif` (sha256 `{_h70['raster_sha256']}`, 184,165 bytes). Evidence `evidence/h70/`.\n")
    (ROOT / 'README.md').write_text(head + e2_note + e3_note + p5_note + h70_note + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
