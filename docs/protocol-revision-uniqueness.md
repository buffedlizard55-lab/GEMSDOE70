# Protocol revision R1 — dot-overlap definition for continuous registry rasters

Status: **explicit revision proposed by this session (2026-10-20), requiring
selector acknowledgment before any weekly slot is spent.** It does not edit
the byte-pinned shared template (`vendor/gems57/uniqueness.py` is unchanged);
it adds a disclosed measurement layer in this repo's own code and reports the
template's literal numbers alongside. Per protocol rule 2, the underlying
template defect is reported in `evidence/upstream_uniqueness_report.md` for a
single upstream fix; no private fork of the metric or writer is kept.

## The defect (measured, not asserted)

The template defines registry "dots" as every finite pixel `> 0`
(`uniqueness._dots`). The SHA-verified registry raster
`17GEMSDOE:docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif`
(SHA-256 `ab0a0a62…`, re-fetched and re-verified this session) is a
continuous probability surface positive on **all 5,167,373 footprint cells**
(minimum ≈ 0.00046). Under the literal definition its 3-px halo covers every
allowed cell, so **every** nonempty candidate — including the family's own
shipped H33 champion — has forward overlap 1.0 and must "stop as duplicate".
A rule that classifies the champion itself, and every possible nonempty
field, as a duplicate of a probability surface cannot be the intended
meaning of "70% of your dots within 3 px of one registry raster's dots":
continuous surfaces do not have dots until an emission rule is applied.
Left unrevised, the rule makes the user's requirement (a unique candidate)
logically unsatisfiable, which E1 correctly reported as a stop.

## Revision R1 (narrow, anti-copy intent preserved)

For each registry raster, classify by measured support inside the footprint:

- **Sparse / dot field** — positive count ≤ 10% of footprint cells:
  dots = positive pixels, exactly as the literal rule. No change.
- **Dense / continuous surface** — positive count > 10%:
  dots = its **top-N footprint pixels by value**, where N = the candidate's
  own dot count (mass-matched emission-equivalent support). Ties broken by
  stable row-major order. This asks the only well-posed question: "if this
  surface were emitted at your mass, would your dots coincide with its dots?"

Gates (both stages — pre-placement surface and final dots):

1. Spearman rank correlation vs **every** checked registry raster
   (dense included, full footprint, literal template computation) ≤ 0.90.
2. Forward 3-px dot overlap ≤ 0.70 vs every sparse raster (literal) **and**
   vs every dense raster's R1 top-N dots.
3. The literal overlap vs dense rasters is still computed and published
   (expected 1.0); it is labelled `literal_dense_overlap_degenerate`, never
   hidden and never averaged away.
4. Byte/pixel identity vs any checked raster remains an automatic stop.

## Scope honesty

This session checks a disclosed subset (highest-risk lineage + dense witness
+ high-scoring family fields; exact list and SHAs in the E2 evidence), not
all 862 inherited-index rasters and not any organizer registry (none is
public). A subset pass can reject duplication; it cannot certify complete
uniqueness. Promotion therefore means "passes R1 within subset scope;
selector must run the complete accessible scan and acknowledge R1 before
spending a slot." If the selector rejects R1, every candidate from this
session reverts to DO NOT SUBMIT, including any file already downloaded
for review.
