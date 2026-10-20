# Publication amendment A1 (2026-10-20) — E2 candidate bytes for selector review

This amendment is dated **after** E2/E3 scoring and is disclosed as such. It
changes **publication only**; it changes no scientific result, bar, or verdict.

## What the preregistration said

`docs/preregistration-e2.md` bar 9: failure of any promotion bar ⇒ verdict
`negative`, DO NOT SUBMIT, "no submission TIFF published as a download."
E2 failed bar (a): candidate dots HOLDOUT-DTI 0.06465 did not beat D28
reference 0.09192 on the seed-20 catalogue holdout (paired Δ −0.02727,
95% CI [−0.04349, −0.01128]). Verdict remains **negative**. E3 also negative.

## What this amendment does and why

The E2 final-dot field is written once with the shared writer and published
in `docs/downloads/` as a **selector-review artifact** whose filename,
site banner, `docs/status.json`, and this file all state
**DO NOT SUBMIT YET**. Rationale, each point verifiable in evidence:

1. Protocol rule 6 separates candidate generation from slot selection
   ("promotion to a real slot is a separate selector step"). The selector
   cannot run the required complete 862-raster R1 scan or any live-mirror
   evaluation from a hash alone; exact bytes are a prerequisite for the
   selector's own gates. Withholding bytes does not protect a slot — the
   banner and status file do.
2. The user requirement is an easy download whose submit-status is obvious.
   "Download for review: YES. Submit: NO" is stated in the first screen of
   the site, in the filename suffix `-DO-NOT-SUBMIT`, and in machine-readable
   status. No green light is given or implied.
3. The field is genuinely unique within the disclosed subset (final-dot
   worst Spearman 0.039; worst R1 overlap 0.443 vs sparse fields, 0.049 vs
   the dense witness's mass-matched support) and format-validated on exact
   bytes (all-finite, [0,1], CRS/shape/transform match, zero on catalogue).
   It is a new ranking's output, not a copied or renamed prior submission.
4. Measured instrument conflict (see `docs/h33-analysis.md` addendum): on
   this catalogue instrument the live-reported family best (H33) ranks
   *last*, below random. Catalogue holdout therefore cannot by itself
   estimate this candidate's live value in either direction. That is a
   reason for selector review with additional instruments — **not** a
   reason to relabel the candidate as promoted, and this amendment does not.

## Conditions to ever flip SUBMIT to YES (all required, selector-owned)

- Complete accessible registry scan under R1 (all 862 inherited-index
  rasters or a fresher complete inventory) passes rho/overlap gates;
- selector explicitly acknowledges protocol revision R1
  (`docs/protocol-revision-uniqueness.md`); if R1 is rejected, this file
  reverts to pure evidence and must never be submitted;
- current weekly cap / remaining slots checked on the live submission page;
- selector accepts in writing (submission note + retained receipt) that the
  catalogue-holdout best (D28) was **not** beaten and that no live score is
  predicted.

Until every condition is recorded, `submit_ok` is false everywhere.
No weekly slot has been used by this session.
