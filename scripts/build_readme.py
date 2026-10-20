"""Embed the entire retained user brief behind a short, accurate session summary."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def main():
    import sys
    sys.path.insert(0, str(ROOT/'src'))
    c1=json.loads((ROOT/'evidence/c1_holdout.json').read_text())
    res=json.loads((ROOT/'evidence/c1_result.json').read_text())
    rec=json.loads((ROOT/'evidence/c1_export_receipt.json').read_text())
    scan=json.loads((ROOT/'evidence/c1_registry_scan.json').read_text())
    cand=c1['scores']['candidate']; rnd=c1['scores']['random_control']; noc=c1['scores']['ablation_no_catalogue']
    s=scan['summary']
    d_e1=json.loads((ROOT/'evidence/run_card.json').read_text())['holdout_dti']['dti']
    dots=sum(1 for r in scan['rows'] if r.get('duplicate_by_overlap') and r.get('representation')=='dot_field')
    head=f'''# GEMSDOE70 — geothermal fault research

## Submission status: **DO NOT SUBMIT — the generated GeoTIFF is not cleared**

Current candidate **C1** (strike-coherent catalogue extrapolation, pre-registered in
[docs/candidates-2026-10-20.md](docs/candidates-2026-10-20.md)) produced a format-valid,
unique-named single-band float32 GeoTIFF, `submissions/{rec['name']}.tif` (git-ignored,
LOCAL-FORMAT-VALIDATION only). **It is not OK to download or submit.** Two gates fail:

- **Holdout (HOLDOUT-DTI, evaluator `{c1['evaluator_version']}`, holdout seed 71):** C1 {cand['dti']:.5f}
  (95% CI [{cand['ci95'][0]:.5f}, {cand['ci95'][1]:.5f}]) is below the random sparse control
  {rnd['dti']:.5f} and the catalogue-free ablation {noc['dti']:.5f}. Paired difference vs random:
  {res['paired_difference_vs_random']['delta']:.5f}.
- **Registry (REGISTRY-MEASUREMENT, complete scan of {s['registry_rasters_checked']} of {s['registry_rasters_expected']} indexed rasters):**
  {dots} sparse dot-field rasters exceed the literal 3 px overlap limit of 0.70 (worst 1.0, a 13GEMSDOE lattice file).

The leakage canary passed. No tuning on holdout seed 71 was made. No previous submission was copied.

- [Research site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [Submission guide (how to submit)](docs/executive-summary.html)
- [C1 run card](evidence/c1_run_card.json) · [C1 holdout](evidence/c1_holdout.json) · [registry scan](evidence/c1_registry_scan.json)
- [Official-source ledger, verified 2026-10-20](evidence/official_sources_2026-10-20.json) · [Candidate ranking](docs/candidates-2026-10-20.md)
- [Limitations / irregularities](docs/irregularities.md) · [Session handoff](HANDOFF.md)
- [Protocol decision required](docs/protocol-decision.md) · [Latest repository review / Pages safeguards](docs/session-review.md)
- [Follow-up publication review](reports/followup-publication-review-20261020.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md and HANDOFF.md.

## Official facts used (verified 2026-10-20; quotes in the ledger)

- Format: one GeoTIFF, single layer, float32, values between 0 and 1, EPSG 32611, 100 m,
  same bounds; outside bounds “null or nan” (problem page).
- Deadline: competition page “Dec. 3, 2026, 11:59 p.m. UTC”; rules A.1 “5:00 p.m. ET on the prize
  submission deadline date”. Plan to the earlier cutoff. This discrepancy is unresolved.
- Limits: up to three submissions per week; one final submission chosen before the deadline (rules §3.4–3.5).
- Eligibility, generative-AI narrative disclosure and external-data license rules: rules §1.2–1.3, §3.2.
  You must confirm eligibility yourself. Nothing here checks it.
- Upload path: enroll, then Submit → Make new submission (competition page, steps 1 and 6).

## Experiments (budget: 3 experiments or 2 hours; 2 used)

1. **E1, magnetic-edge termination (seed 20):** stopped by the surface-uniqueness gate; no TIFF written.
   HOLDOUT-DTI {d_e1:.6f}, below the random control. Negative.
2. **E2, C1 (seed 71):** described above. Negative. Its post-hoc binary diagnostic is labeled not preregistered and not a promotion basis.

Slot selection (the weekly cap of three) is a separate step. No slot is used.

## Known gaps (not fixed in this session)

- **Registry coverage is incomplete.** The index dates from 2026-10-12. Eleven repos in the
  owner namespace (GEMSDOE69 and GEMSDOE73–GEMSDOE82) are not in it; ten of them were created on 2026-10-20.
  Their rasters were **not** checked, because the GitHub API rate limit was reached during this session.
  This cannot clear C1, but a complete scan is still required before any candidate is cleared.
- Leaderboard numbers are JavaScript-rendered and were not readable. No ORGANIZER-CONFIRMED score exists.
- The shared writer writes 0 outside the footprint, not NaN. Portal acceptance of that is unverified.

## Reproduce the workbench

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.lock
bash scripts/download_competition_data.sh  # pinned public owner mirrors, not DrivenData auth
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python scripts/audit_pages.py
.venv/bin/python -m pytest -q
```

Shared `evaluate_holdout.py`, `submission_writer.py` and the metric are reused unchanged from
vendor/gems57 (pinned; byte identity is recorded in evidence/template_verification.json).
Do not rerun `scripts/run_experiment.py`. Do not tune an experiment after seeing its holdout.

## Publication boundary

Pages is configured to serve the repository root (`main:/`), not only `docs/`. The root
`.nojekyll` bypass was removed, and `_config.yml` excludes quarantine, data, evidence,
code and the local `submissions/` folder. `scripts/audit_pages.py` and the build guards
check the publication boundary, including unlinked artifacts. Remote deployment is a
separate step. The exclusions do not make archived bytes secret; they only keep them out
of the Pages build.

## Own the outcome

Maximizing the probability of winning does not mean hiding negatives, overstating verification
or spending unvalidated slots. A negative result with a clear stop condition is the correct output
here. Next-session priorities are in HANDOFF.md and the limitations page.

## Complete retained project prompt

Historical statements below are user-supplied requirements, not verified current results. No
leaderboard value below becomes ORGANIZER-CONFIRMED by being copied here. PROJECT_BRIEF.md is the
source for this embedded copy (whitespace normalized from the supplied message).

<details>
<summary>Read the complete supplied project brief before every session</summary>

'''
    (ROOT/'README.md').write_text(head+(ROOT/'PROJECT_BRIEF.md').read_text()+'\n</details>\n')
if __name__=='__main__':main()
