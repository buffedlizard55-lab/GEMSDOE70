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
    delta = card['paired_b_prime_vs_h33']
    review = json.loads((ROOT / 'evidence/literal_protocol_review.json').read_text())
    review_gate = review.get('correlation_overlap_vs_registry', {})
    witnesses = review_gate.get('witnesses', [])
    max_forward = max((w['forward_overlap'] for w in witnesses
                       if type(w.get('forward_overlap')) in (int, float)), default=0.0)
    review_only = review_gate.get('stop') is True
    if not review_only:
        raise SystemExit('Literal protocol stop is not active; review the README status before rebuilding it.')
    artifact = card['artifact']
    witness_summary = '; '.join(
        f"`{w.get('submission', 'unnamed raster')}` (forward overlap {w['forward_overlap']:.3f})"
        for w in witnesses if type(w.get('forward_overlap')) in (int, float)
    )
    head = f'''# GEMSDOE70 — geothermal fault research

> **CURRENT STATUS: DO NOT SUBMIT.** The archived Phase-4 final-dot raster fails the literal
> one-way overlap rule: {len(witnesses)} witnesses in {review_gate.get('registry_rasters_checked', 0)}
> accessible registry rasters; maximum forward overlap {max_forward:.2f} (REGISTRY-MEASUREMENT,
> not a competition score). The TIFF is downloadable for review only. No new candidate, surface,
> experiment, or weekly-slot use occurred in this review; no surface pass is claimed.
> [Current review](reports/literal-protocol-review.md) · [JSON run card](evidence/literal_protocol_review.json).

## Archived artifact: **REVIEW DOWNLOAD ONLY — DO NOT SUBMIT**

[Download the archived Phase-4 TIFF for review only]({artifact}) — SHA-256
`{card['raster_sha256']}`. This is an earlier candidate, not a new unique submission. Its local
format/range receipt does not override the current literal uniqueness stop. Do not upload this TIFF
or its ZIP to the competition. `download_ok: true` means bytes are available for review;
`submit_recommended: false` is controlling. No weekly slot was used.

- [Evidence site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [Submission guide and current stop](docs/submission.html)
- [Current review](reports/literal-protocol-review.md) · [Literal-policy JSON card](evidence/literal_protocol_review.json)
- [Archived experiment card](evidence/run_card.json) · [Historical uniqueness receipt](evidence/phase4/uniqueness.json)
- [H33 analysis and verification limits](docs/h33-analysis.md) · [Current research queue and protocol stop](reports/literal-protocol-review.md)
- [Limitations and irregularities](docs/irregularities.md) · [Handoff](HANDOFF.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md, PROJECT_BRIEF.md and HANDOFF.md.

## This review's outcome

No new data was restored, no model or raster was generated, no holdout was recomputed, and no
submission slot was selected. The reviewed archived TIFF is disclosed here solely as a downloadable
review copy. The complete experimental receipts remain frozen and are not new measurements.

## Archived HOLDOUT-DTI evidence (not organizer scores)

Evaluator: `gems57-pooled-hide-v2`. These are copied from archived Phase-4 receipts, not rerun in
this review. Instrument A measures hide-and-recover against withheld catalogue components; B′ uses
an SGMC-derived proxy holdout, not organizer hidden truth. Both are **HOLDOUT-DTI**, not
ORGANIZER-CONFIRMED.

| Evidence | Candidate HOLDOUT-DTI | H33 reference HOLDOUT-DTI |
|---|---|---|
| A · catalogue hide-and-recover; 11,321 withheld positives | {d['dti']:.4f}, 95% CI [{d['ci95'][0]:.4f}, {d['ci95'][1]:.4f}] | {dref['dti']:.4f}, 95% CI [{dref['ci95'][0]:.4f}, {dref['ci95'][1]:.4f}] |
| B′ · SGMC proxy holdout; 59,937 withheld proxy positives (not hidden truth) | {b['dti']:.4f}, 95% CI [{b['ci95'][0]:.4f}, {b['ci95'][1]:.4f}] | {bref['dti']:.4f}, 95% CI [{bref['ci95'][0]:.4f}, {bref['ci95'][1]:.4f}] |

Paired B′ difference versus H33 is **HOLDOUT-DTI** under the same evaluator: Δ {delta['delta']:+.4f},
95% CI [{delta['ci95'][0]:.4f}, {delta['ci95'][1]:.4f}], 59,937 withheld proxy positives. It is
negative; neither instrument approximates the organizer's hidden labels perfectly. No submission
receipt or ORGANIZER-CONFIRMED score is present.

## Literal registry stop

The current prompt's one-way final-dot gate triggers on four recorded witnesses: {witness_summary}.
The accessible scan covers {review_gate.get('registry_rasters_checked', 0)} archived rasters and is not
an organizer-wide or exhaustive inventory. The previous mutual-overlap statistic and its historical
clearance are superseded for this prompt. A new candidate surface was not generated, so the required
surface-stage check was not run and is not claimed to pass. This report stops at the existing final-dot
witness; it does not reinterpret the shared metric or create a private uniqueness exception.

## Ranked geological research queue (unvalidated; not executable yet)

The archived review lists three distinct cache-based hypotheses, ranked qualitatively by expected
holdout improvement per implementation cost: signed magnetic-profile displacement across a gravity
boundary; contact-normal basement asymmetry; and scale-dependent magnetic/gravity edge migration.
Each names layers, target signature, a non-fault mimic, catalogue-omission rationale, and differences
from inspected local methods. They are research proposals only, not claims of global novelty across
private GEMSDOE work. The top idea was **not validated** because the literal stop is active and no
single current lane is assigned. Full comparison and caveats: [ranked research queue](reports/literal-protocol-review.md#ranked-research-queue--not-executable-under-the-current-stop).

## Sources and blockers

Official manual-review links: [DrivenData competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[submission format/data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
[leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/),
[USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
and [organizer reference repository](https://github.com/drivendataorg/gems-prize-reference-solution).
Official competition and USGS pages were not freshly fetched because their hosts are outside the
sandbox allowlist; links are supplied for review, not falsely presented as verified this session.
GitHub owner mirrors are not official provenance. The restored feature cache is absent, the SGMC
proxy is omitted from `scripts/fetch_data.py`'s `WANT` list, and no official-source bytes or current
weekly-cap status were verified.

## Required next steps

1. Obtain an explicit protocol ruling on the one-way overlap stop; record any revision as a new version, not a silent reinterpretation.
2. Assign a single, non-duplicated method lane after comparing GEMSDOE66, GEMSDOE71, GEMSDOE72 and the current repo.
3. Only after both gates are resolved, restore/hash the existing feature stack and SGMC proxy; run feature-alone leakage canaries and whole-segment buffered holdout.
4. For any new method, run surface uniqueness before placement and final-dot uniqueness after placement; stop at the first duplicate witness.
5. Compare the top candidate to the current best on the identical spatially blocked split. Do not select a weekly slot unless a cleared candidate beats the HOLDOUT-DTI baseline.

## Complete retained project prompt

Historical statements below are user-supplied requirements and claims, not verified results. The full text is preserved unchanged and is the starting point for future work.

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
        e2_note = (f"\n## Parallel E2 lane (integrated PR #16) — archived review candidate, DO NOT SUBMIT\n\n"
                   f"Alluvial-step candidate: HOLDOUT-DTI, evaluator `{_d['evaluator_version']}`, "
                   f"{_d['withheld_positive_pixels']:,} withheld-positive pixels, DTI {_d['dti']:.4f}, "
                   f"95% CI [{_d['ci95'][0]:.4f}, {_d['ci95'][1]:.4f}]. This archived result did not beat "
                   f"the D28 catalogue-holdout comparison; it is not an organizer score. "
                   f"File `docs/downloads/gems70-e2-alluvialstep-38000-20261020T221218Z-zeros-DO-NOT-SUBMIT.tif` "
                   f"is selector-review only; its complete current literal uniqueness scan is pending. "
                   f"Evidence: `evidence/e2/`, preregistration `docs/preregistration-e2.md`.\n")
    (ROOT / 'README.md').write_text(head + e2_note + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
