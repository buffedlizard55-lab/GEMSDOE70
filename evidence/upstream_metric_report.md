# Shared-template prose correction — upstream filing blocked

Target: https://github.com/buffedlizard55-lab/60GEMSDOE/blob/32024716f218d06a94e01464157392119c03cb15/src/gems57/metric.py

Issue creation attempted 2026-10-20 via `gh issue create --repo buffedlizard55-lab/60GEMSDOE`.
Result: `GraphQL: Resource not accessible by integration (createIssue)`; exit code one. **No issue was filed.** GitHub integration needs additional cross-repository permissions. Reconnect GitHub in Arena with access to the template repository before retrying. No password/token was requested or stored.

The docstring says `dT <= k`, but a unit dot at (5,5) and truth cells at (5,5), (5,6) give marginal truth coverage `1 + 2/3` and self-credit `k = 1` under the three-pixel triangular kernel.

The unchanged executable `dti_exact` correctly returns TP=1.6666666666666667, FP=0, FN=0.33333333333333326. Thus this is a mathematical explanatory defect, not an observed scoring error affecting this run. The exact inequality remains `deltaT > alpha * old_DTI * (deltaT + 1 - k)`; the simplified inequality needs the additional condition `deltaT = k`.

Do not privately fork the template metric to repair its prose. Fix this once upstream, then repin the shared source. Regression coverage is retained in tests/test_metric.py.
