"""Embed the retained brief behind the current, literal-policy review decision."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    audit = json.loads((ROOT / 'evidence/review/literal_protocol_audit.json').read_text())
    card = json.loads((ROOT / 'evidence/review/run_card.json').read_text())
    head = f'''# GEMSDOE70 — geothermal fault research

## CURRENT REVIEW: DO NOT SUBMIT — literal lane stop

**Download: yes, existing archived TIFFs for review only. Submit: NO.**
No new protocol-compliant TIFF was generated in this review; no new geological experiment or
weekly slot was used. This does **not** fulfill the requested new-submission deliverable.
The current negative run card is [here](evidence/review/run_card.json).

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
metric, writer or frozen historical evidence. All six published final TIFFs have measured forward
overlap **1.0** against the pinned binary lattice, exceeding **0.70**. They are duplicates under
the prompt's rule, even though their bytes differ. Small rank correlation does not cancel overlap.

Fresh REGISTRY-MEASUREMENT: halo coverage **{audit['shared_saturation_certificate']['covered_allowed_fraction']:.9%}**,
not the previously asserted 100%. There are **6,649 uncovered footprint cells**. At the prior
handoff's fixed **37,654-dot mass**, even the minimum possible overlap is
**{audit['minimum_forward_overlap_at_fixed_budget']:.9f}**, still a stop. This does not prove
impossibility at every smaller mass. We did not optimize a boundary-only loophole.

All six existing TIFFs pass shared local format checks (single-band float32, finite [0,1],
CRS/shape/transform matching the pinned sample); that is not portal acceptance or uniqueness.
The previous canonical P4 card and historical receipts remain frozen and superseded for current
policy by `evidence/review/run_card.json`.

## Scientific outcome and next session

No new HOLDOUT-DTI or ORGANIZER-CONFIRMED score exists from this review. The historical P4
HOLDOUT-DTI is 0.07304 [0.06674, 0.07899], evaluator `gems57-pooled-hide-v2`, 11,321 withheld
catalogue positives. Its SGMC proxy gate was already negative. H33's reported 0.2778 and the
conflicting leader values in the brief lack authenticated submission-page receipts here.

The prior handoff's supervised within-halo ranking remains deferred. Four ranked, specific
hypotheses and their non-fault mimics are in the review. Resolve the literal-gate conflict by a
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
    (ROOT / 'README.md').write_text(head + (ROOT / 'PROJECT_BRIEF.md').read_text() + '\n</details>\n')


if __name__ == '__main__':
    main()
