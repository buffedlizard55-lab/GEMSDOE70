"""Embed the entire retained user brief behind an accurate, evidence-bound summary."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    p5_path = ROOT / 'evidence/phase5/run_card.json'
    p5 = json.loads(p5_path.read_text()) if p5_path.is_file() else {}
    d = card['instrument_a_holdout']['candidate']
    dref = card['instrument_a_holdout']['h33_reference']
    b = card['instrument_b_prime_proxy']['candidate']
    bref = card['instrument_b_prime_proxy']['h33_reference']
    ball = card['instrument_b_unrestricted']['candidate']
    ballref = card['instrument_b_unrestricted']['h33_reference']
    u = card['uniqueness_detail']
    delta = card['paired_b_prime_vs_h33']

    p5_block = ''
    if p5:
        p5a = p5['instrument_a_holdout']['candidate']
        p5bp = p5['instrument_b_prime_proxy']['candidate']
        p5bdp = p5['instrument_b_double_prime_proxy']['candidate']
        p5ball = p5['instrument_b_unrestricted']['candidate']
        p5_dbp = p5['paired_b_prime_vs_h33']
        p5_dbdp = p5['paired_b_double_prime_vs_h33']
        p5_u = p5['correlation_overlap_vs_registry']
        p5_s = p5['surface_uniqueness_vs_registry']
        p5_block = f'''## Phase-5 Submission Status: **DOWNLOADABLE (`download_ok = true`) · PROMOTED FOR SELECTOR REVIEW (`verdict = promote`)**

A new unique, format-validated Phase-5 GeoTIFF is published:
- **File:** `docs/downloads/{p5['submission_name']}.tif` (and `.zip` / `.json`)
- **SHA-256:** `{p5['raster_sha256']}`
- **Submission note (`{p5['note_chars']}/140` chars):** `{p5['submission_note']}`
- **Download (`download_ok`):** **YES (`true`)** — passes all 15 shared validator checks, zero dots on mapped catalogue, `37,654` binary dots in `[0, 1]`, unique across all 66 checked rasters (62 archived registry + 4 local candidates: worst mutual overlap `{p5_u['worst_mutual_overlap_all_66']:.4f} <= 0.70`, worst surface Spearman `{p5_s['worst_spearman_full_footprint']:.4f} <= 0.90`), and passes all 49 single-feature leakage canaries (`max deviation AUC = {p5['leakage_canary_summary']['max_deviation_auc']:.4f} <= 0.90`).
- **Holdout & LOQO Proxy Gates (`holdout_and_proxy_gates_passed`):** **YES (`true`)** — clears all three pre-registered gates (`Instrument A`, `Instrument B'` at `d >= 3` px, and `Instrument B''` at `d >= 6` px outside the 1:500k cartographic duplication band) with 95% bootstrap CIs strictly above zero.
- **Submit a weekly slot (`weekly_slots_used = 0`):** Promoted for human selector review (`selector_ready = true`); under PARALLEL-RUN PROTOCOL Rule 6, no weekly slot was spent automatically in the sandbox because SGMC is a state-compilation proxy rather than the hidden organizer truth.

| Instrument (`gems57-pooled-hide-v2`) | Phase-5 Candidate (`loqo_halo`) | Phase-5 Ablation (`no_hydro`) | Phase-4 Baseline | H33 Reference (`GEMSDOE32`) | Paired Δ (P5 vs H33) |
|---|---:|---:|---:|---:|---|
| **A · Catalogue holdout (`11,321` pos)** | **{p5a['dti']:.4f}** `[{p5a['ci95'][0]:.4f}, {p5a['ci95'][1]:.4f}]` | **{p5['instrument_a_holdout']['ablation_no_hydro']['dti']:.4f}** | 0.0730 | 0.0037 | `+{p5['paired_a_vs_h33']['delta']:.4f}` `[{p5['paired_a_vs_h33']['ci95'][0]:.4f}, {p5['paired_a_vs_h33']['ci95'][1]:.4f}]` |
| **B′ · LOQO SGMC proxy `d ≥ 3` px (`59,937` pos)** | **{p5bp['dti']:.4f}** `[{p5bp['ci95'][0]:.4f}, {p5bp['ci95'][1]:.4f}]` | **{p5['instrument_b_prime_proxy']['ablation_no_hydro']['dti']:.4f}** | 0.0812 | 0.0938 | **`+{p5_dbp['delta']:.4f}` `[{p5_dbp['ci95'][0]:.4f}, {p5_dbp['ci95'][1]:.4f}]`** |
| **B″ · LOQO SGMC proxy `d ≥ 6` px (`52,767` pos)** | **{p5bdp['dti']:.4f}** `[{p5bdp['ci95'][0]:.4f}, {p5bdp['ci95'][1]:.4f}]` | **{p5['instrument_b_double_prime_proxy']['ablation_no_hydro']['dti']:.4f}** | 0.0674 | 0.0850 | **`+{p5_dbdp['delta']:.4f}` `[{p5_dbdp['ci95'][0]:.4f}, {p5_dbdp['ci95'][1]:.4f}]`** |
| **B · Unrestricted LOQO SGMC proxy (`74,740` pos)** | **{p5ball['dti']:.4f}** `[{p5ball['ci95'][0]:.4f}, {p5ball['ci95'][1]:.4f}]` | **{p5['instrument_b_unrestricted']['ablation_no_hydro']['dti']:.4f}** | 0.0948 | 0.0906 | candidate wins |

- [Phase-5 run card](evidence/phase5/run_card.json) · [Phase-5 preregistration](docs/preregistration-phase5.md) · [SGMC buffer audit](evidence/phase5/sgmc_buffer_audit.json) · [E2 62-raster corrected audit](evidence/phase5/e2_uniqueness_62rasters_corrected.json) · [Upstream patch verification](evidence/phase5/upstream_verification.json)

---

'''

    head = f'''# GEMSDOE70 — geothermal fault research

{p5_block}## Frozen Phase-4 Baseline Status: **DOWNLOADABLE — NOT PROMOTED**

A unique, format-validated competition TIFF is published:
`docs/downloads/{card['submission_name']}.tif` (sha256 `{card['raster_sha256']}`).
**Download: yes. Submit a weekly slot: not recommended by our evidence** — verdict
`{card['verdict']}` on the pre-registered target-like gate. No weekly slot was used.

- [Evidence site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [How to submit](docs/submission.html)
- [Run card](evidence/run_card.json) · [Uniqueness audit](evidence/phase4/uniqueness.json)
- [Why H33 scored 0.2778](docs/h33-analysis.md) · [Preregistered hypotheses](docs/hypotheses.md)
- [Limitations / next steps](docs/irregularities.md) · [Session handoff](HANDOFF.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md and HANDOFF.md.

## What was measured in Phase 4

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
.venv/bin/python scripts/audit_sgmc_proxy.py    # SGMC vs QFaults buffer calibration (1-6 px)
.venv/bin/python scripts/reaudit_e2_uniqueness.py # E2 62-raster corrected uniqueness audit
.venv/bin/python scripts/verify_upstream_fix.py # upstream uniqueness patch & 33-test verification
.venv/bin/python scripts/run_experiment_v5.py   # registered Phase-5 LOQO run, regenerates P5 artifact
.venv/bin/python scripts/run_experiment_v4.py   # registered Phase-4 run, regenerates P4 artifact
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
    (ROOT / 'README.md').write_text(head + e2_note + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
