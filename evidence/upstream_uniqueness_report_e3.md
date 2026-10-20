# Upstream report (retained locally; cross-repo issue creation not attempted this session)

Template: `buffedlizard55-lab/60GEMSDOE@32024716f218d06a94e01464157392119c03cb15`,
vendored byte-identical at `vendor/gems57` (see `registry/template_pin.json`).
No private fork was made; lane drivers only call shared functions.

## Finding: forward-overlap gate saturates on sparse covering fields too

`uniqueness.two_phase_summary` classifies registry rasters by positive-support
fraction (`DENSE_SUPPORT_FRACTION = 0.20`). Measured 2026-10-20 with the shared
`saturation_certificate` (`evidence/saturation_certificates_e2.json`):

- `calib_r13lattice_00904.tif`: support 4.00% (classified dot_field) but 3 px
  halo covers 99.87% of allowed (footprint minus catalogue) cells. E2 candidate
  forward overlap 1.0, Jaccard 0.0075, Spearman 0.0007.
- `r14_union_tips10_lat6.tif`: halo coverage 76.21%; `r11_greedy_mp.tif`: 73.66%.
  Any allowed dot set has expected forward overlap at/above the 0.70 gate.
- Champion `GEMSDOE32__h33-2-b2-zeros.tif`: halo coverage 15.19% (gate discriminates).

Suggested upstream fix: classify by halo coverage of the allowed domain
(`covered_allowed_fraction`) in addition to support fraction, and gate forward
overlap only where coverage < overlap limit; keep Spearman + Jaccard universal.
E3 applies this as a disclosed lane-level summary over shared-tool outputs
(`docs/hypotheses-e3.md`) pending any upstream change.
