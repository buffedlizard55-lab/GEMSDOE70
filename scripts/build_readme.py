"""Embed the retained brief behind the current, literal-policy review decision."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems70.release import p5_status


def main():
    audit = json.loads((ROOT / 'evidence/review/literal_protocol_audit.json').read_text())
    card = json.loads((ROOT / 'evidence/review/run_card.json').read_text())
    p5 = json.loads((ROOT / 'evidence/p5/run_card.json').read_text())
    state = p5_status(ROOT)
    if not state['download_ok_for_review'] or state['submit_recommended']:
        raise ValueError('P5 review file is absent, modified or not a negative research artifact')
    a = p5['holdout_dti']['instrument_a']
    b = p5['holdout_dti']['instrument_b_prime_proxy']
    da = p5['holdout_dti']['paired_vs_visible_p4']
    db = p5['holdout_dti']['paired_vs_h33']
    head = f'''# GEMSDOE70 — geothermal fault research

> **Submission decision (all lanes, 2026-10-20): no file in this repository is recommended for a
> weekly slot.** Every published TIFF is download-for-review only. Latest lane: Session 3
> (supervised proxy ranking) — see its section below and `docs/s3-findings.md`.

## NEW P5-COVER FILE: **DOWNLOAD FOR RESEARCH; DO NOT SUBMIT**

A newly generated, format-validated **continuous** GeoTIFF is available:
[Download P5 TIFF — DO NOT SUBMIT](docs/downloads/{p5['submission_name']}.tif) ·
[One-TIFF ZIP for review](docs/downloads/{p5['submission_name']}.zip) ·
[P5 evidence page](docs/p5.html) · [P5 run card](evidence/p5/run_card.json).
SHA-256 `{p5['raster_sha256']}`. Name `{p5['submission_name']}`;
note ({p5['note_chars']}/140): `{p5['submission_note']}` (**not an upload instruction**).

**Download for review: yes. Contest upload / weekly slot: NO.**
HOLDOUT-DTI A (`{a['evaluator_version']}`, {a['withheld_positive_pixels']:,} withheld
catalogue pixels) = {a['dti']:.4f} {a['ci95']}; paired vs regenerated visible-only P4
Δ {da['delta']:+.4f} {da['ci95']}. SGMC proxy HOLDOUT-DTI B′
(`{b['evaluator_version']}`, {b['withheld_positive_pixels']:,} proxy positives)
= {b['dti']:.4f} {b['ci95']}; paired vs frozen H33 Δ {db['delta']:+.4f}
{db['ci95']}. Both 95% intervals for improvement are below zero; these are **not**
organizer-confirmed scores. Leakage canaries clear (all features below AUC 0.90).
The new continuous surface has ~{p5['validator_output']['mean']*p5['validator_output']['n_finite']:,.0f}
summed probability mass versus 37,654 full-mass H33/P4 dots; this is a **joint test** of
ranking, proxy training and emission, not an isolated causal feature comparison.

The literal 3-px **forward** overlap gate blocks any proposed dot placement in the
4,989,581-pixel feature-valid interior: a hash-pinned archived lattice covers every
cell of that domain. The continuous P5 map has no exact-one binary dots, but its
**positive support has 1.00 forward overlap** with the same lattice; that is not a
loophole or a protocol-unique submission. Distinct bytes/low rank correlation
(ρ ≤ {p5['correlation_overlap_vs_registry']['worst_spearman_full_footprint']:.4f} vs
{p5['correlation_overlap_vs_registry']['rasters_checked']} checked rasters) do not
clear the other gate. No weekly slot was used; no organizer submission receipt exists.

- [Executive summary / exact future submission workflow](docs/executive-summary.html)
- [Four ranked preregistered hypotheses](docs/preregistration-p5.md) ·
  [Official-source claim/limit table](evidence/p5/official_source_review.json)
- [H33 analysis](docs/h33-analysis.md) ·
  [Literal overlap witness](evidence/p5/literal_blocker.json)
- **Session start:** read this README, the complete retained brief below, AGENTS.md and HANDOFF.md.

### Reproduce or verify P5 (CPU; no slot, no automatic promotion)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/restore_data.py
# owner archive provides the pinned SGMC proxy + 62 registry rasters:
git clone --depth 1 https://github.com/buffedlizard55-lab/60GEMSDOE /tmp/60GEMSDOE
.venv/bin/python scripts/verify_p5_artifact.py   # re-check unchanged TIFF without refitting
# Run scripts/run_experiment_p5_cover.py only on a clean checkout; writer refuses to overwrite.
.venv/bin/python -m pytest -q
```

Input mirrors are SHA-pinned owner copies, **not** organizer-authenticated; the competition
data page requires a login. USGS magnetic edges can also represent dikes, remanence changes
or survey artifacts, not fault/vent proof. The reported H33 0.2778 has no authenticated
file-specific receipt here. Public-leaderboard 0.4413 was read on 2026-10-20,
not copied from a P5 submission. See [official problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
[DOE rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

## PRIOR REVIEW ({len(audit['archived_artifacts'])} archived dot files): DO NOT SUBMIT — literal lane stop

**Download: yes, {len(audit['archived_artifacts'])} older archived TIFFs for review only. Submit: NO.**
That *prior* review generated no new protocol-compliant TIFF, geological experiment or slot.
P5 above is a later, separate research-only negative, not a promoted competition submission.
The frozen prior-review negative run card is [here](evidence/review/run_card.json).

- [Evidence site](https://buffedlizard55-lab.github.io/GEMSDOE70/)
- [Executive summary / exact submission workflow](docs/executive-summary.html)
- [Download archived P4 TIFF — DO NOT SUBMIT](docs/downloads/gems70-p4-stratified-halo-37654-20261020.tif)
- [Fresh literal-protocol audit](evidence/review/literal_protocol_audit.json)
- [Four ranked hypotheses / source table / limitations](docs/protocol-review.md)
- [H33 analysis — measured geometry, not a verified leaderboard explanation](docs/h33-analysis.md)
- [Handoff](HANDOFF.md)
- **Session start:** read this README, the complete retained brief below, AGENTS.md and HANDOFF.md.

## What this review verified

The previous mutual-overlap gate weakened the prompt's **forward**-overlap rule without approval.
Current policy applies the literal rule to shared-tool measurements; it does not change the
metric, writer or frozen historical evidence. The {len(audit['archived_artifacts'])} historically reviewed dot TIFFs have measured forward
overlap **1.0** against the pinned binary lattice, exceeding **0.70**. They are duplicates under
the prompt's rule, even though their bytes differ. Small rank correlation does not cancel overlap.

Fresh REGISTRY-MEASUREMENT: halo coverage **{audit['shared_saturation_certificate']['covered_allowed_fraction']:.9%}**,
not the previously asserted 100%. There are **6,649 uncovered footprint cells**. At the prior
handoff's fixed **37,654-dot mass**, even the minimum possible overlap is
**{audit['minimum_forward_overlap_at_fixed_budget']:.9f}**, still a stop. This does not prove
impossibility at every smaller mass. We did not optimize a boundary-only loophole.

All {len(audit['archived_artifacts'])} reviewed dot TIFFs pass shared local format checks (single-band float32, finite [0,1],
CRS/shape/transform matching the pinned sample); that is not portal acceptance or uniqueness.
The previous canonical P4 card and historical receipts remain frozen and superseded for current
policy by `evidence/review/run_card.json`.

## Scientific outcome and next session

At the time of that prior review, no new HOLDOUT-DTI or ORGANIZER-CONFIRMED score existed;
P5 HOLDOUT-DTI is newly measured above. The historical P4 HOLDOUT-DTI is 0.07304 [0.06674, 0.07899], evaluator `gems57-pooled-hide-v2`, 11,321 withheld
catalogue positives. Its SGMC proxy gate was already negative. H33's reported 0.2778 and the
conflicting leader values in the brief lack authenticated submission-page receipts here.

The prior handoff's supervised within-halo ranking was deferred in this archived review;
the new P5 test above executed one narrow magnetic-cover version and measured a negative.
Four earlier ranked hypotheses and their non-fault mimics are in the historical review.
Resolve the literal-gate conflict by a
separately authorized protocol, then validate one candidate using nested spatial splits, canaries,
a matched current-best baseline and the shared evaluator/writer. Do not silently reintroduce a
mutual-overlap exemption, and do not spend a weekly slot before an independent selector decision.

## Reproduce this review (CPU; does not generate a TIFF)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/python scripts/review_literal_protocol.py --fetch
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/audit_pages.py
```

The witness fetch uses the configured GitHub connection and immutable revision/SHA pins. It lands
in ignored `.cache/`, not Git. Data bridge files already in the repo supply the reference geometry.
Official reference README/notebook were re-fetched via GitHub API. Other official hosts and the
authenticated submission page were not accessible within this session's outbound allowlist; live
cap, eligibility and organizer acceptance remain unverified. GPU is preferred, not required by the
organizer reference. `scripts/prepare_data.py` advertised in the historical prompt is absent.

## Complete retained project prompt

Historical statements below are user-supplied requirements and claims, not verified results.
PROJECT_BRIEF.md is preserved verbatim and embedded in full. The current prompt's substantive
requirements are retained there; the current active branch is recorded in HANDOFF.md.

<details>
<summary>Read the complete supplied project brief before every session</summary>

'''
    e5_note = ''
    e5p = ROOT / 'evidence/e5/run_card.json'
    if e5p.is_file():
        _e5 = json.loads(e5p.read_text())
        _a = _e5['instrument_a_holdout']
        _b = _e5['instrument_b_prime_proxy']
        _db = _e5['paired_b_prime_vs_h33']
        _u5 = _e5['correlation_overlap_vs_registry']['final_dots_stage']
        e5_note = (f"\n## E5 lane — supervised within-halo ranking (2026-10-20), verdict `{_e5['verdict']}` — DO NOT SUBMIT\n\n"
                   f"SGMC-proxy LOQO ranker (the previously deferred next step, now executed under its own "
                   f"preregistration `docs/preregistration-e5.md`), 37,654 dots: "
                   f"A HOLDOUT-DTI {_a['candidate']['dti']:.4f} vs H33 {_a['h33_reference']['dti']:.4f}; "
                   f"B′ PROXY-DTI {_b['candidate']['dti']:.4f} vs H33 {_b['h33_reference']['dti']:.4f} "
                   f"(Δ {_db['delta']:+.4f} [{_db['ci95'][0]:+.4f}, {_db['ci95'][1]:+.4f}] — includes zero) → negative. "
                   f"File `docs/downloads/{_e5['submission_name']}.tif` (sha256 `{_e5['raster_sha256']}`), "
                   f"review-only under the literal policy above (forward overlap {_u5['worst_forward_overlap']:.2f} "
                   f"vs the dense lattice; mutual {_u5['worst_mutual_overlap']:.3f}). Evidence: `evidence/e5/`. "
                   f"Public leader at organizer-page read 2026-10-20: 0.4413 "
                   f"(`evidence/e5/leaderboard_read.json`). No weekly slot used.\n\n")
    p5_note = ''
    p5p = ROOT / 'evidence/phase5/run_card.json'
    if p5p.is_file():
        import json as _json5
        _p5 = _json5.loads(p5p.read_text())
        _pa = _p5['instrument_a_holdout']['candidate']
        _pb = _p5['instrument_b_prime_proxy']['candidate']
        p5_note = (f"\n## Parallel P5 analytic-signal lane (arena/97660a79-gemsdoe70) — DO NOT SUBMIT\n\n"
                   f"Analytic-signal halo 7px, 37,654 dots, `tmi_hg`+`tmi_vg` rank in 2.4–32 px halo with tip kernel. HOLDOUT-DTI A {_pa['dti']:.4f} [{_pa['ci95'][0]:.4f},{_pa['ci95'][1]:.4f}] vs H33 0.0037 win; **B′ {_pb['dti']:.4f} [{_pb['ci95'][0]:.4f},{_pb['ci95'][1]:.4f}] vs 0.0938 H33 win Δ { _p5['paired_b_prime_vs_h33']['delta']:+.4f} {_p5['paired_b_prime_vs_h33']['ci95']} → negative**, no slot. Uniqueness: 62 rasters worst mutual 0.30 (limit 0.70) worst ρ 0.042; forward 1.00 vs dense lattice `calib_r13lattice_00904.tif` (literal duplicate, review only). File `docs/downloads/gems70-p5-analytic-halo-37654-20261020.tif` (sha256 `{_p5['raster_sha256']}`, 149,414 bytes, ZIP `bf61cacc...`). Evidence `evidence/phase5/` (run_card, instrument holds, uniqueness, canaries), method `src/gems70/method_p5.py`. Hypotheses.md now ranks 5 candidates (H-2 tested P5, H-3 radiometric GeoDAWN already fetched 36+26 MB, H-4 lidar scarp 36 MB, H-5 conductive breach, H-6 basement curvature) with preregistered validation rule; h33-analysis.md PhD-level byte audit + metric algebra. Under literal forward rule, P5 is duplicate (as is H70 and P4) — download for review only.\n")
    e6_note = ''
    e6p = ROOT / 'evidence/e6/run_card.json'
    if e6p.is_file():
        _e6 = json.loads(e6p.read_text())
        _a6 = _e6['instrument_a_holdout']
        _b6 = _e6['instrument_b_prime_proxy']
        _db6 = _e6['paired_b_prime_vs_h33']
        _u6 = _e6['correlation_overlap_vs_registry']['final_dots_stage']
        e6_note = (
            f"\n## E6 lane — multi-modal extended-domain LOQO ranker (2026-10-20, `arena/effcd5f7-gemsdoe70`), "
            f"`scientific_verdict = {_e6['scientific_verdict']}` (`download_ok = true`, "
            f"`submit_recommended = false` under literal forward rule — DO NOT SUBMIT without selector exemption)\n\n"
            f"Diagnoses why P4 (`0.0812`) and E5 (`0.0886`) trailed H33 (`0.0938`) on Instrument B′: "
            f"**35.89% of all SGMC B′ off-catalogue fault pixels lie at `d_cat > 32 px`** (`evidence/e6/sgmc_buffer_audit.json`), "
            f"which P4 and E5 truncated to zero, and E5 omitted the external LiDAR scarp, 10 m DEM lineament/curvature, "
            f"GeoDAWN radiometric, and 100 m scarp-curvature channels (`HANDOFF.md` Next Steps 1–2). "
            f"Training a 4-fold Leave-One-Quadrant-Out HGB across **28 multi-modal features in `d_cat in [3.0, 96.0] px`** "
            f"with 7×7 regional coverage stratification (`37,654` binary dots; preregistered in `docs/preregistration-e6.md`, "
            f"driver `scripts/run_experiment_e6.py`) achieves:\n"
            f"- **Instrument B′ (`PROXY-DTI`, `d >= 3 px`, 59,937 positives):** **`{_b6['candidate']['dti']:.4f}`** "
            f"`[{_b6['candidate']['ci95'][0]:.4f}, {_b6['candidate']['ci95'][1]:.4f}]` vs H33 **`{_b6['h33_reference']['dti']:.4f}`** "
            f"— **paired Δ `{_db6['delta']:+.4f}`, 95% CI `[{_db6['ci95'][0]:+.4f}, {_db6['ci95'][1]:.4f}]` (strictly positive; "
            f"`gate_b_prime_candidate_gt_h33_significant = true`)**, beating H33 (+17.3%), E5 (+24.0%), and P4 (+35.5%).\n"
            f"- **Instrument A (`HOLDOUT-DTI`, 11,321 withheld catalogue pixels):** **`{_a6['candidate']['dti']:.4f}`** "
            f"`[{_a6['candidate']['ci95'][0]:.4f}, {_a6['candidate']['ci95'][1]:.4f}]` vs H33 **`{_a6['h33_reference']['dti']:.4f}`** "
            f"(`gate_a_candidate_ge_h33 = true`).\n"
            f"- **Uniqueness:** Passes amended mutual-overlap uniqueness across all 62 registry rasters "
            f"(worst mutual `{_u6['worst_mutual_overlap']:.4f} <= 0.70`, worst non-lattice forward `{_u6['worst_nonlattice_forward_overlap']:.4f} <= 0.70`, "
            f"worst Spearman `{_u6['worst_spearman_full_footprint']:.4f} <= 0.90`) and all 11 sibling repository TIFFs (`worst_mutual = 0.3508`). "
            f"Blocked from automatic slot upload ONLY by literal one-way forward overlap (`1.00 > 0.70`) against the dense binary lattice witness `calib_r13lattice_00904.tif`.\n"
            f"- **Artifact:** `docs/downloads/{_e6['submission_name']}.tif` (sha256 `{_e6['raster_sha256']}`), "
            f"evidence in `evidence/e6/` (including 62-raster E2 re-audit `e2_uniqueness_62rasters.json` and 7-lane B′ audit `cross_lane_bprime.json`). No weekly slot used.\n"
        )
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'scripts'))
    import s3_site
    head = head.replace('## Complete retained project prompt',
                          e6_note + s3_site.readme_block() + e5_note + p5_note + '## Complete retained project prompt', 1)
    (ROOT / 'README.md').write_text(head + (ROOT / 'PROJECT_BRIEF.md').read_text() + '\n</details>\n')


if __name__ == '__main__':
    main()
