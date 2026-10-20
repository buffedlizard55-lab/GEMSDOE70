"""Embed the entire retained user brief behind an accurate session summary."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems70.release import candidate_status  # noqa: E402


def main():
    st = candidate_status(ROOT)
    e2 = json.loads((ROOT / "evidence/e2/run_card.json").read_text())
    d = e2["holdout_dti"]
    head = f'''# GEMSDOE70 — geothermal fault research

## Submission status: **DO NOT SUBMIT YET — unique candidate available for selector review**

**Download for selector review: YES. Submit to DrivenData: NO.** A unique,
format-validated candidate GeoTIFF (new alluvial-step ranking, not a copy of
any prior submission) is published for the separate selector step. Its frozen
promotion bars failed — D28 catalogue-holdout best was not beaten — so no
weekly slot may be spent on it until every selector condition in the guide is
recorded. **No weekly slot was used. No score is claimed.**

- **Candidate:** [`docs/downloads/{st["file"]}`](docs/downloads/{st["file"]}) · SHA-256 `{st["sha256"]}`
- **Name (if selector ever approves):** `{st["submission_name"]}` · **Note:** `{st["submission_note"]}`
- [Research site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [Submission guide](docs/executive-summary.html)
- [E2 run card](evidence/e2/run_card.json) · [E2 holdout](evidence/e2/holdout.json) · [Validator](evidence/e2/validator.json)
- [Preregistration (5 ranked hypotheses, frozen E2/E3)](docs/preregistration-e2.md) · [H33 forensic analysis](docs/h33-analysis.md)
- [Limitations / irregularities](docs/irregularities.md) · [Session handoff](HANDOFF.md)
- **Session start:** read this README, the entire retained brief below, AGENTS.md and HANDOFF.md.

## What was measured (2026-10-20 session)

Two preregistered CPU experiments on the SHA-pinned mirror stack, shared
evaluator `gems57-pooled-hide-v2` (alpha 0.2, beta 0.8, 300 m kernel),
whole-component hide-and-recover, per-feature leakage canaries (all AUC ≤ 0.58,
no alarm), paired 20 km bootstrap. Vendor template byte-identical.

- **E2 alluvial step** (oriented detrended-elevation step × basement edge,
  38,000 thinned dots): **HOLDOUT-DTI {d["dti"]:.5f}**, 95% CI
  [{d["ci95"][0]:.5f}, {d["ci95"][1]:.5f}], {d["withheld_positive_pixels"]:,}
  withheld positives. Beats random (0.04243) and every ablation; ties H19-solid
  at one-third mass; **loses to D28 reference (0.09192)** → negative.
  Uniqueness (7-raster subset, revision R1): worst Spearman 0.039, worst R1
  overlap 0.443; only 797/38,000 pixels coincide exactly with H33.
- **E3 magnetic depth-step:** mechanism AUC 0.506 (null); candidate 0.05054
  carried by its partner feature → negative, no file.
- **E1 contact termination (archived):** 0.01019, worse than random → negative.

**Why H33 (user-reported 0.2778) led the family, and what beating it takes:**
strong H19-5 ranking + kernel-scale thinning + catalogue-flank pruning
(emission efficiency). Measured here on one instrument, that same H33 field
scores HOLDOUT-DTI 0.00370 — *last, below random* — because catalogue
hide-and-recover cannot reward far-field new faults. Never convert catalogue
holdout into a live projection in either direction. Public leader at organizer
page read 2026-10-20: **0.4413** (`evidence/leaderboard_read.json`). The 0.2778
value has no organizer receipt in this repo and is never labelled
ORGANIZER-CONFIRMED. Full derivation: `docs/h33-analysis.md`.

The candidate TIFF is all-finite in [0,1] (min 0, max 1, no nodata tag),
single-band float32, EPSG:32611, 3730×3292 — the local fix for the portal
error “Predicted values must be in range [0, 1]”. Local validation is not
organizer acceptance. Publication terms: `docs/publication-amendment-e2.md`;
dense-surface uniqueness revision: `docs/protocol-revision-uniqueness.md`.

## Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.lock
bash scripts/download_competition_data.sh  # pinned public owner mirrors, not DrivenData auth
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/validate_submission.py docs/downloads/{st["file"]}
```

Experiment scripts refuse reruns (manifests in `evidence/e2|e3/`). Do not
delete manifests to tune on reported folds. `scripts/publish_e2_candidate.py`
recomputes the candidate from scratch and aborts on any mismatch.

## Own the outcome

Maximize P(Win) never licenses hiding negatives, overstating verification, or
spending unvalidated slots. This session's win condition was honest evidence:
a unique candidate with measured limits, an obvious submit status, and a
selector checklist — not a manufactured green light.

## Complete retained project prompt

Historical statements below are user-supplied requirements/claims, not verified
current results. No leaderboard value below becomes ORGANIZER-CONFIRMED by being
copied into this README. The dedicated PROJECT_BRIEF.md is the source for this
embedded copy (formatting whitespace normalized from the supplied message).

<details>
<summary>Read the complete supplied project brief before every session</summary>

'''
    (ROOT / "README.md").write_text(head + (ROOT / "PROJECT_BRIEF.md").read_text() + "\n</details>\n")


if __name__ == "__main__":
    main()
