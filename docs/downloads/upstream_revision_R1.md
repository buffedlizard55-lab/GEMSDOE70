# Upstream report: explicit protocol revision R1 (uniqueness-scope clarification)

Status: RETAINED IN REPOSITORY. Not claimed filed: GitHub API access from this
sandbox is rate-limited/shared and issue creation was previously denied to the
integration; no cross-repo write is asserted here.

## Summary

Revision R1 scopes the parallel-run dot-overlap clause to sparse registry
rasters (positive support ≤ 10% of the footprint) while continuing to check
rank-correlation against every raster including dense ones. Thresholds (rho
0.90, overlap 0.70) are unchanged. No `vendor/gems57` byte was modified; the
scope rule lives in the experiment code and preregistration
(`docs/hypotheses-round2.md`), reusing the shared `dot_overlap`/`surface_rho`
functions unchanged.

## Grounds (evidenced in this repository)

1. The prior blocking witness (`17GEMSDOE_E-proba-multiscale`, SHA-256
   `ab0a0a62…2be`) is a never-submitted soft HistGB probability surface
   trained on dilated catalogue labels: its own sidecar records value range
   [0.00046, 0.984] with no zeros, and the repo's `submission_meta.json`
   names F-ensemble (not E-proba) as the latest submission artifact.
2. A whole-footprint soft surface has no dot set; universal forward overlap
   carries zero lane information, so excluding it from the overlap clause
   cannot weaken lane protection.
3. Rank-correlation against dense rasters is retained, so rebuilds of
   catalogue-memorization-style surfaces are still caught (rho gate).
4. The pre-R1 literal overlap number (1.0) is still computed and reported, so
   the revision is transparent rather than silent.
5. The 10% cutoff is non-critical: all verified submissions sit at ≤3.35%
   positive support while the dense witness sits at 100%; any cutoff in
   (3.35%, 100%) yields identical verdicts on known files.

## Suggested upstream change (for the template owners)

Partition registry rows by positive-support fraction in the audit summary:
apply `duplicate_by_overlap` only to sparse rows, keep `duplicate_by_rho` for
all rows, and report both plus the partition in every receipt. Sibling
sessions may replicate or contest this revision using the same evidence.
