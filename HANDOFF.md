# Next session — read before modeling

Read README.md, PROMPT.md, AGENTS.md, reports/review.md, and evidence/run_card.json.

## Current outcome

**NEGATIVE / DO NOT SUBMIT. No new TIFF. No scientific experiment. No slot used.**
The user's highest-priority TIFF deliverable remains **unmet**, because the
literal protocol rejects every nonempty in-footprint candidate. The missing
single-method lane is also a blocker. Do not “fix” this by changing the threshold,
stratifying dense rasters out, renaming a prior TIFF, or changing the run-card verdict.

The obstruction is remeasured, not merely inherited: a member of the historical
registry has positive values at every finite sample-footprint cell. Its byte hash,
Git blob, membership, grid alignment and support were verified. One witness is
sufficient to prove failure of an any-registry rule; no full scan is claimed.

## Reproduce the delivered audit and site

    python -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python scripts/audit.py
    .venv/bin/python scripts/make_run_card.py
    .venv/bin/python scripts/release_gate.py --expect-negative
    .venv/bin/python scripts/build_site.py
    .venv/bin/python -m pytest -q

`audit.py` restores a content-addressed witness from GitHub if absent, checks
its SHA-256 and input pins, then reproduces the universal-overlap proof. The
scientific budget is still unused. The local audit succeeds with exit 0 when it
reproduces a negative; `release_gate.py` without `--expect-negative` exits 2 and
NEVER authorizes a release.

## Resume priorities

1. Explicit protocol resolution and a real method-lane paragraph are required.
2. Confirm organizer data identities, official band semantics, nodata encoding,
   current rules and authenticated weekly quota. No credentials in files/chat.
3. Restore the large feature stack only when a legitimate lane run is possible;
   inherited `scripts/fetch_data.py` is unmodified and uses pinned public mirrors.
4. Build a visible-only same-evaluator incumbent and preregister the assigned
   candidate; all proposed hypotheses are conditional and locally novel only.
5. Feature canaries, pooled buffered whole-segment holdout, paired physical-block
   CI, ordered uniqueness, shared writer, exact-byte validator, separate selector.
6. Replace the negative-only publisher only after a separately reviewed,
   evidence-bound positive gate exists. A run-card field must not enable downloads.

No shared module was edited. Upstream prose issue in metric.py is documented;
any correction must be made once in the shared template, not a private fork.
Official reference README supports CPU-only training; GPU is beneficial, not a
hard requirement. This checkout has no fitted scientific training implementation.
