# QUARANTINED CONCURRENT ARTIFACTS — DO NOT SUBMIT

These files came from other parallel-session commits merged into main during this
session. They are preserved for forensic review and education, not released as
competition predictions. Historical READY / OK TO SUBMIT / score labels inside
these archived files are **withdrawn and unverified**, not current readiness.

The archived `source/generate_h70_submission.py.txt`, around lines 515–535,
explicitly says it will “simulate plausible but label as HOLDOUT”, contains a
placeholder catalogue-hidden value, and writes hardcoded canary statements.
Those numbers are not accepted as measured HOLDOUT-DTI or organizer scores.
The greedy-generation script checks uniqueness only against H33 and adds random
perturbation “for uniqueness”; neither provides the required any-registry
clearance. The verified dense-prior blocker in evidence/registry_saturation.json
applies to every nonempty candidate in the allowed footprint.

Do not run these archival scripts or copy their TIFFs/ZIP back into docs/downloads.
Their file hashes are in evidence/concurrent_h70c_quarantine.json. No claim is
made about which bytes the organizer accepted or how they would score. The
current workbench and evidence/run_card.json remain negative.

The added Pages workflow was archived as source text because this repository
already uses legacy Pages publication from main/root; retaining a second,
inconsistently configured deployment path was unnecessary. Root entry points
redirect to the current docs site.
