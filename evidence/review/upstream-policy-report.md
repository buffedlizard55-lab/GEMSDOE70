## Shared uniqueness policy evidence from GEMSDOE70 review

The current parallel-run user protocol is literal forward overlap > 0.70 OR Spearman > 0.90. GEMSDOE70's inherited vendored tool reports forward overlap but substitutes mutual overlap in its verdict. That substitution is not authorized by the current prompt. We have not changed the shared metric, evaluator, writer or vendor bytes; current release decisions apply the explicit literal policy to the shared measurements.

Fresh pinned binary witness:
- `registry/rasters/calib_r13lattice_00904.tif` at `32024716f218d06a94e01464157392119c03cb15`
- SHA256 `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`
- `saturation_certificate`: 206895 binary dots, 5167373 footprint cells, 6649 uncovered within 3px, coverage 0.9987132726822701.

The earlier GEMSDOE70 narrative that this halo covered 100% was false. At a fixed mass of 37654 dots, the conservative lower bound `1 - 6649/37654 = 0.8234184947150369` still rejects every placement; it does NOT establish a universal blocker at every smaller mass. All five currently inventoried GEMSDOE70 final TIFFs directly re-audit at forward overlap 1.0 against this binary witness (no continuous-support ambiguity).

Please retain literal forward policy as a first-class shared-tool verdict rather than silently treating a dense binary lattice as exempt. Any mutually agreed alternative protocol must be separately authorized and identified; reverse overlap is useful diagnostic evidence but not the present stop rule.

Audit script and receipt will be in GEMSDOE70 branch `arena/9d9f624f-gemsdoe70`: `scripts/review_literal_protocol.py`, `evidence/review/literal_protocol_audit.json`. This is a negative preflight; no new TIFF, model score or submission slot.

Publication attempt: rejected by GitHub integration permissions (createIssue); no issue URL exists.
