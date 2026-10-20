"""Embed the entire retained user brief behind an accurate, evidence-bound summary."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    review = json.loads((ROOT / 'evidence/literal_protocol_review.json').read_text())
    overlap = review['correlation_overlap_vs_registry']
    holdout = review['holdout']
    witnesses = overlap.get('witnesses', [])
    highest = max((row.get('forward_overlap', 0) for row in witnesses), default=None)
    head = f'''# GEMSDOE70 — geothermal fault research

> **CURRENT DECISION: DO NOT DOWNLOAD OR SUBMIT.** The archived Phase-4 candidate fails the
> literal one-way 3-pixel overlap rule: {len(witnesses)} witnesses among {overlap.get('registry_rasters_checked')} accessible registry rasters; maximum forward overlap {highest:.3f}.
> The accessible inventory is not claimed to include private or uncommitted artifacts. All
> previously exposed TIFF/ZIP files are quarantined for audit only. No new candidate was generated;
> no competition slot was used. [Protocol review](reports/literal-protocol-review.md) ·
> [Release-integrity review](reports/review-release-integrity-2026-10-20.md).

## What is and is not established

- **HOLDOUT-DTI** (archived, not rerun): evaluator `{holdout['evaluator_version']}`, {holdout['dti']:.6f},
  95% CI [{holdout['ci95'][0]:.6f}, {holdout['ci95'][1]:.6f}],
  {holdout['withheld_positive_pixels']:,} withheld positives. This is catalogue hide-and-recover,
  not the organizer's hidden-label score.
- **REGISTRY-MEASUREMENT:** the literal candidate-dot overlap rule is exceeded by archived registry
  rasters. This is a protocol stop, not a claim of byte-identical or geologically equivalent fields.
- **ORGANIZER-CONFIRMED score:** none recorded for a local candidate. The user-reported historical
  H33 score is not confirmed by a submission receipt here.
- **Submission file:** none is cleared. Quarantine artifacts are preserved only for audit; local
  format validation cannot waive the uniqueness stop.

The archived H33 audit suggests that pruning near-catalogue prediction mass can improve a
kernel-weighted Tversky objective by reducing redundant truth-cell credit and false-positive mass.
That is a plausible mechanism, not a causal finding about the hidden competition score. H33 is a
fault-prediction artifact; it does not establish geothermal vents, permeability, temperature, or
commercial potential.

## Next steps

Resolve the literal-overlap protocol with the selector before any new experiment; assign one lane;
use cached, hash-pinned features and shared evaluator/writer; run leakage canaries and buffered
spatial holdout; then complete the registry audit before and after placement. Only a candidate
passing every gate may reach the separate slot-selection step.

## Session startup

Read this README, the complete retained prompt below, `AGENTS.md`, and `HANDOFF.md` at the start of
each session. Negative results are deliverables. Do not treat source links or local receipts as
proof of fresh official retrieval or organizer acceptance.

## Complete retained project prompt

Historical statements in the prompt below are user-supplied requirements and claims, not verified
results. Current measurements and release decisions are documented above and in `evidence/`.

<details>
<summary>Read the complete supplied project brief before every session</summary>

'''
    tail = '\n</details>\n'
    (ROOT / 'README.md').write_text(head + (ROOT / 'PROJECT_BRIEF.md').read_text() + tail)


if __name__ == '__main__':
    main()
