"""Embed the entire retained user brief behind a short, accurate session summary."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def main():
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    d=card['holdout_dti']
    head=f'''# GEMSDOE70 — geothermal fault research

## Submission status: **DO NOT SUBMIT — no eligible TIFF**

The fixed contact-termination experiment failed the literal surface uniqueness gate.
Final dot placement and submission export stopped. **No previous submission was
copied, renamed or advertised as a new prediction. No weekly slot was used.**
The requested unique downloadable competition TIFF is **not fulfilled**; the
protocol's verified dense-prior blocker makes it impossible for any nonempty
candidate to pass its current literal support rule. A negative result is retained
instead of an unsafe download.

- [Research site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [Submission guide](docs/executive-summary.html)
- [Run card](evidence/run_card.json) · [Measured results](evidence/holdout.json)
- [H33 forensic analysis](docs/h33-analysis.md) · [Four preregistered hypotheses](docs/hypotheses.md)
- [Limitations / next steps](docs/irregularities.md) · [Session handoff](HANDOFF.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md and HANDOFF.md.

## What was verified

This checkout originally contained only an eleven-byte README. We restored the
cached numerical stack, sample and mapped faults from pinned owner mirrors;
checksums prove mirror consistency, not organizer authentication. Shared
`evaluate_holdout.py`, `submission_writer.py`, metric, holdout and uniqueness
tools are reused unchanged from the pinned template. Their upstream blob/hash
verification is in [evidence/template_verification.json](evidence/template_verification.json).

One fixed CPU experiment targeted magnetic-edge termination along gravity-supported
basement boundaries. Each raw/derived feature received its own leakage canary and
holdout score. No catalogue-derived predictor was used. Whole connected fault
components were hidden with a feature-context buffer and spatial erosion, visible
faults were masked pixel-exactly, and weighted metric terms were pooled before a
paired spatial-cluster bootstrap.

**HOLDOUT-DTI:** {d['dti']:.6f}, 95% CI [{d['ci95'][0]:.6f}, {d['ci95'][1]:.6f}],
{d['withheld_positive_pixels']:,} withheld positive pixels, evaluator
`{d['evaluator_version']}`. This is the continuous pre-placement surface, not final
dots and not a leaderboard score. It underperforms the random sparse control;
no same-split current-best claim is made. See the full receipt for controls and
paired intervals.

**REGISTRY-MEASUREMENT:** one decisive, SHA-verified continuous prior covers the
whole footprint. Surface Spearman is {card['correlation_overlap_vs_registry']['spearman']:.6f};
three-pixel forward support overlap is 1.0, above the literal 0.70 stop threshold.
The [saturation certificate](evidence/registry_saturation.json) proves this blocks
every nonempty off-catalogue candidate under the inherited support definition.
This is a representation/protocol conflict, not evidence that all geological
methods are identical. No private density exemption was used. Only this witness
was checked: a complete fresh uniqueness clearance is **not** claimed.

The user-reported H33 historical value has **no ORGANIZER-CONFIRMED receipt** here.
Actual bytes show H33 is the previous sparse field with catalogue-near dots deleted.
The site explains conditional metric efficiency without inferring hidden labels or
promising a higher score. Conflicting leaderboard values in the prompt remain
unverified. Official non-GitHub pages failed access here; we do not call that a
verified login redirect.

## Reproduce the workbench

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.lock
bash scripts/download_competition_data.sh  # pinned public owner mirrors, not DrivenData auth
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
```

`run_experiment.py` is the preserved one-experiment implementation; it deliberately
refuses a second attempt when its manifest already exists. Do not delete the
manifest to tune on reported holdout blocks. `build_submission.py` exits with a
clear blocked status, never creates a decoy TIFF. The shared writer's real
TIFF/one-TIFF-ZIP round trip, range rejection and no-overwrite behavior are tested
with temporary synthetic fixtures only. No synthetic fixture is published.

The static Pages site reports evidence; it does not train or generate in-browser.
A fresh reviewed scientific run, resolved protocol, complete two-stage audit and
separate weekly-slot selection are needed before enabling a real artifact link.
[Source-health workflow](.github/workflows/source-health.yml) refreshes availability
as a downloadable Actions artifact; it is not an authenticated live-score feed.

## Concurrent review history

Two parallel reviews merged into main during this session. Their reports, source
notes, bridge fixtures, audit helpers and software tests are retained. The earlier
review-only run card and handoff are archived under
[evidence/history/parallel-review2](evidence/history/parallel-review2/), where their
zero-experiment statements remain historically accurate. The canonical current
card records the one fixed experiment reported here. Legacy publication entry
points now delegate to this evidence-driven site; `make_run_card.py` verifies the
existing card rather than overwrite it with an older schema.

A subsequent concurrent H70-C publication (PRs 4/5) contained explicit
simulated/placeholder holdout values in its source and checked novelty against
only H33. Its source, documents and TIFFs are preserved in
`quarantine/concurrent-h70c` with hash evidence, but removed from site downloads.
Those historical READY / score claims are withdrawn, not endorsed as measurements.
See [the quarantine receipt](evidence/concurrent_h70c_quarantine.json).

## Follow-up publication boundary

Pages is configured for the repository root, not only `docs/`. The root
`.nojekyll` bypass has been removed and `_config.yml` excludes quarantine/data
and internal directories. Site builds now check both the root policy and docs,
including symlink bypasses. An API change to `/docs` was denied (403); no
settings change is claimed. GitHub archives remain public, not redacted.
See [follow-up review](reports/followup-publication-review-20261020.md).

## Own the outcome

Do not use “maximize probability of winning” as permission to hide negatives,
overstate verification, spend unvalidated slots or weaken uniqueness. Honest
negative evidence and clear stop conditions protect future experiments. Next-session
priorities and unmet requirements are explicit in HANDOFF.md and the limitations page.

## Complete retained project prompt

Historical statements below are user-supplied requirements/claims, not verified
current results. No leaderboard value below becomes ORGANIZER-CONFIRMED by being
copied into this README. The dedicated PROJECT_BRIEF.md is the source for this
embedded copy (formatting whitespace normalized from the supplied message).

<details>
<summary>Read the complete supplied project brief before every session</summary>

'''
    (ROOT/'README.md').write_text(head+(ROOT/'PROJECT_BRIEF.md').read_text()+'\n</details>\n')
if __name__=='__main__':main()
