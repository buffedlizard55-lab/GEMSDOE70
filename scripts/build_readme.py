#!/usr/bin/env python3
"""Keep the working prompt directly in README as requested."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SUMMARY='''# GEMSDOE70 — evidence-first fault discovery

## Submission status: BLOCKED / DO NOT SUBMIT

**No new submission TIFF was generated.** This highest-priority deliverable is
unmet, not replaced by an old, renamed, randomly perturbed or all-zero file.
No scientific experiment or competition slot was used.

The literal parallel-run protocol is unsatisfiable for any nonempty prediction
inside the sample footprint: a hash-verified registry member is positive at
every footprint pixel. Forward overlap with that member is necessarily 100%,
above the mandatory 70% duplicate-and-stop limit. The required method-lane
paragraph is also absent from the supplied brief. We did not silently revise
either constraint.

**[Open the site](https://buffedlizard55-lab.github.io/GEMSDOE70/)** ·
[Executive submission guide](https://buffedlizard55-lab.github.io/GEMSDOE70/executive-summary.html) ·
[Negative run card](evidence/run_card.json) · [Measured proof](evidence/preflight.json)

### Start every session here

Read this README including the working brief below, [AGENTS.md](AGENTS.md),
[HANDOFF.md](HANDOFF.md), and [the review](reports/review.md). Preserve the user's
literal stop rules. **Maximize P(Win):** protect scarce submission slots.
**Own the Outcome:** publish negative evidence and identify unmet deliverables.

### What was actually delivered

- Audited the initially empty checkout and corrected inherited infrastructure claims.
- Read official competition problem/metric/format text and relevant rules sections;
  stored a [source ledger](reports/sources.md) with explicit evidence limits.
- Inspected H33 method source and prior TIFF bytes **for education only**.
  Its reported result remains USER-REPORTED, not artifact-bound ORGANIZER-CONFIRMED.
- Ranked [four conditional geological hypotheses](reports/research.md) with
  physical signatures, layer names, confounders, and qualitative benefit/cost.
- Reused byte-pinned shared evaluator, writer, metric and registry tools;
  verified upstream Git blobs without editing the shared implementation.
- Added reproducible audit, local format-validator wrapper, negative-only release
  policy, software tests, CI, and a clean static Pages site with no misleading TIFF link.

### Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/audit.py
.venv/bin/python scripts/make_run_card.py
.venv/bin/python scripts/release_gate.py --expect-negative
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q
```

The audit downloads one content-addressed registry witness via `gh` if absent,
checks its SHA-256, and reproduces the negative. Its exit 0 means “audit ran,”
**not** “submission approved.” The release gate without `--expect-negative`
exits 2 and does not authorize publication. Test-generated TIFFs exist only in
pytest temporary directories and are not scientific candidate deliverables.

For a future file's **local format** check only:

```bash
.venv/bin/python scripts/validate_submission.py path/to/candidate.tif --out evidence/validation.json
```

A local format PASS is not novelty clearance, geological validation, slot
approval or organizer acceptance. The shared writer rejects invalid values
without clipping. Its all-finite outside-footprint convention must be reconciled
with official null/NaN guidance before claiming a submit-ready artifact.

### Concurrent prior review preserved

A separate review reached main while this PR was open. Its original dated
[review](docs/review-2026-10-20.md) is preserved with a supersession note. Its
next-step request to restore shared tools is now addressed; lane, protocol,
scientific-validation and organizer-authentication blockers remain. A public
leaderboard observation is not a submission-page-confirmed artifact score.

### Limits and next actions

See the [completion matrix](reports/requirements.md). There is no fitted model,
real-data holdout result, feature AUC, comparable holdout best, current complete
registry scan or submission-page receipt in this repository. The large cached
feature stack was not restored after the preflight stop; the inherited pinned
fetcher is available, not a claimed complete training pipeline. Bridge inputs
are hash-pinned owner mirrors, not independently organizer-authenticated.

Resolve the explicit protocol conflict and assign a lane first. Then authenticate
inputs, restore caches, verify physical band meanings, preregister a same-evaluator
visible-only candidate/incumbent comparison, run canaries and pooled confidence
intervals on untouched blocks, perform surface uniqueness before placement and
final-dot uniqueness afterward, validate exact output bytes, and pass to the
separate selector. No leaderboard improvement is promised.

GitHub Pages is static: this site reports evidence and explains submission; it
does not run scientific training or produce geophysical rasters in the browser.
Source observation dates are shown. No automatic live leaderboard or account
quota feed is claimed. No DrivenData account session is available; shell binary
hosts are restricted. CPU-only training is possible in the official reference;
a GPU can help, but is not a proven hard prerequisite.

## Original working brief

The following preserves the full user-supplied working brief in readable
Markdown (whitespace normalized). Its historical claims are not verified facts;
corrections and blockers above take precedence in our factual reports. It is
also maintained separately in [PROMPT.md](PROMPT.md).

---

'''

if __name__=='__main__':
    (ROOT/'README.md').write_text(SUMMARY+(ROOT/'PROMPT.md').read_text())
