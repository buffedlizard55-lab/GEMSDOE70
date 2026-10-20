# Input provenance

`bridge/sample_submission.tif` and `bridge/existing_faults.tif` are inputs, NOT
predictions and NOT downloadable submissions. They are copied from owner mirror
GEMSDOE69 commit ae3b9b513500fbf31660cf0a19bf161483478c67, and match the
SHA-256 pins of the shared 60GEMSDOE template. The audit checks both identities.

The sample defines the bridge-relative footprint by finite values. Mirror
integrity is verified; direct organizer-origin identity is NOT authenticated.
Do not interpret the catalogue as private competition truth.

The large cached feature stack is intentionally not committed. The inherited,
unmodified `scripts/fetch_data.py` can restore the SHA-256-pinned feature and
external caches through public owner mirrors into `.cache/gems_data/`:

    .venv/bin/python scripts/fetch_data.py

It is NOT run for this negative preflight: no modeling is authorized by the
missing lane and universal-overlap blocker. No GPU is needed for the audits.
The script's WANT set does not download every manifest entry or a complete
training pipeline. A successful fetch is not evidence of a trained model,
correct band semantics, current licenses, or organizer-authenticated data.
