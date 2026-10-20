# Handoff — 2026-10-20

Read README.md and PROMPT.md first, then reports/review-2026-10-20.md.

## State

**NEGATIVE. DO NOT SUBMIT.** No new TIFF or scientific experiment this review.
The archived H69-D TIFF passes local format checks but fails literal uniqueness.
Do not replace the literal gate with the stratified diagnostic. Do not offer
conditional downloads after a failed gate. The latest radiometric scoring code
is missing from this checkout, phase scans refer to an older artifact, and one
aggregate registry entry failed to compare. Detailed review and fresh validator
receipt are retained in reports/ and evidence/.

## Publication commands

    python scripts/release_gate.py
    python scripts/build_site69.py
    python scripts/build_readme.py

All publication entry points now use scripts/release_gate.py. Gate evidence must
be complete, literal, hash-bound, and include feature-alone canaries, method-source
hashes, a same-evaluator current-best comparison, and both uniqueness phases.
Missing evidence means no download. The new manifest contract is
`evidence/e3_method_manifest.json`: artifact_sha256, source_sha256 (relative path
mapping to digest), feature_names (list). Current archived evidence does not meet
it. Do not fabricate fields to make it pass.

## Next work, in order

1. Resolve actual radiometric implementation and training provenance; verify
   catalogue, footprint, and feature identities against organizer data.
2. Repair tip-search radius and interval-gap logic; obtain measured dip/slip
   metadata instead of treating subparallel strikes as same dip.
3. Resolve registry definition upstream without overriding the user's protocol.
4. Only when stop conditions are resolved, preregister a new experiment using
   untouched blocks. Queue: joint HG/tilt phase across relay connectors, then
   releasing-basin margin asymmetry, then staggered scarp phase coherence.
5. Restore pinned caches; canary each feature; compare pooled DTI to the same
   no-prior pipeline AND the current best, with block-bootstrap confidence.
6. Check surface uniqueness before dot placement, final-dot uniqueness after;
   validate exact bytes, bind all evidence, then regenerate the site.

Tests: 1 strict expected failure documents the known interval-gap bug; it is not
proof of complete geological compliance. The shared template was not changed.
No DrivenData slot is authorized. Negative results are deliverables.
