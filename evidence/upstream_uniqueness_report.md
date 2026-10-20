# Upstream report — template `uniqueness._dots` dense-surface degeneracy

Template: `buffedlizard55-lab/60GEMSDOE` commit
`32024716f218d06a94e01464157392119c03cb15`, file `src/gems57/uniqueness.py`
(vendored byte-identically as `vendor/gems57/uniqueness.py`; not edited here).

## Defect

`_dots(a) = isfinite(a) & (a > 0)` treats every positive cell of a continuous
probability raster as an emitted "dot". The registry contains continuous
surfaces positive on the entire footprint (verified example:
`17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif`, SHA-256
`ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`,
5,167,373/5,167,373 footprint cells positive, min ≈ 0.00046). Its 3-px halo
covers every allowed cell, so `dot_overlap(anything_nonempty, dense) == 1.0`
and every candidate — including the family's shipped H33 champion — is
classified duplicate. The executable arithmetic is internally consistent;
the *definition* conflates ranking surfaces with emitted dot fields.

## Suggested single upstream fix

Define registry dots by support class: sparse fields (≤10% footprint
positive) keep `>0`; dense surfaces use mass-matched top-N support
(N = candidate dot count). Keep Spearman vs dense surfaces literal, and keep
publishing the literal dense overlap as a degenerate diagnostic. Full text:
GEMSDOE70 `docs/protocol-revision-uniqueness.md` (R1). GEMSDOE70 implements R1
only as an additional disclosed measurement layer; the vendored file is
unchanged pending this upstream fix.

## Filing status

Recorded in `evidence/upstream_report_attempt_e2.json` (issue URL or the
exact CLI error). This file alone does not claim an issue was filed.
