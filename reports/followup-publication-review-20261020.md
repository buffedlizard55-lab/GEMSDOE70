# Follow-up review — 2026-10-20

## Outcome

**NEGATIVE — DO NOT SUBMIT. No new TIFF generated and no competition slot used.**
The inherited stopped run remains immutable. No experiment was rerun, tuned, or
promoted. The requested unique submission remains unmet under the literal protocol.

## Pass 1: inspect and implement

Read the session contract, README, retained project brief, handoff and limitations;
inspected release/site code, hypotheses, H33 analysis, workflows and run card.
Queried the live GitHub Pages API: it reports legacy `main:/` publication. This
means the existing `docs/`-only no-raster guard did not cover the configured site
source. Added a read-only-by-default settings checker. Attempt to restrict the
source via API was denied with HTTP 403, recorded verbatim without claiming an
authentication failure or a successful update.

Implemented repository-level Jekyll exclusions and removed the root `.nojekyll`
marker which would bypass them. Root source guard now prevents unexpected TIFF,
TIFF/ZIP archives and symlinks outside excluded directories. Existing docs guard
also rejects disguised and dangling symlinks. Quarantine hashes are untouched.

## Pass 2: edge-case review

Tested root marker bypass, root TIFF, missing quarantine exclusion, file symlink,
directory symlink, dangling symlink, malformed/unknown remote settings, read-only
check behavior and API failure. Site generation must fail rather than publish an
unexpected file. Internal data remain public in Git history: this is not a privacy
boundary. Pages configuration is not equivalent to a completed remote build.

## Pass 3: requirements review

Rebuilt the evidence-driven site and retained README; checked the negative gate
and full software suite. Existing four ranked hypotheses and H33 forensic analysis
remain linked. Existing whole-component HOLDOUT-DTI and leakage diagnostics are
preserved, not presented as new measurements. No current organizer score, weekly
cap, complete registry clearance, new final-dot score, or valid TIFF is claimed.
The shared evaluator/writer remain byte-pinned and unchanged. The prompt's missing
lane paragraph and saturated literal overlap rule still prevent new science.

Local verification: **86 software tests pass**, with three existing Rasterio/Affine
pending-deprecation warnings. This count is a software test result, not a score.
The exact remote Pages build must be checked after merge. No local Ruby/Jekyll
runtime is available, so a local production Jekyll build was not claimed.

## Next work

1. Resolve the continuous-support vs dot-support rule centrally, without an exemption
   invented by this session; obtain the missing lane assignment.
2. Supply an auditable same-split incumbent and untouched evaluation blocks.
3. Only then preregister a fresh candidate and run canaries, holdout, complete
   surface/final-dot registry checks, shared writer and byte-level validator.
4. Obtain separate weekly-slot selection and an actual organizer receipt.
5. Restrict Pages source to `/docs` when administration permissions permit; use
   `python scripts/check_pages.py` to inspect configuration without changing it.

Manual evidence: [Pages API](https://api.github.com/repos/buffedlizard55-lab/GEMSDOE70/pages),
[evidence card](../evidence/run_card.json), [H33 analysis](../docs/h33-analysis.md),
[publication response](../evidence/pages_publication.json),
[root publication policy](../_config.yml).
