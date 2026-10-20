"""Embed the retained user brief behind an accurate current (E3) summary."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    card = json.loads((ROOT / "evidence/run_card_e3_amended.json").read_text())
    d = card["holdout_dti"]
    name = card["submission_name"]
    ok = card.get("verdict") == "promote" and card.get("download_candidate_ok")
    status = ("**✅ OK TO DOWNLOAD candidate TIF — selector review before upload**"
              if ok else "**DO NOT SUBMIT — no released TIFF**")
    head = f"""# GEMSDOE70 — geothermal fault research

## Submission status: {status}

- **Download (candidate):** [docs/downloads/{name}.tif](docs/downloads/{name}.tif)
  · SHA-256 `{card['raster_sha256']}` · {card['n_final_dots']:,} binary dots, float32, all values in [0, 1]
- **Note to paste ({len(card['submission_note'])} chars):** `{card['submission_note']}`
- **Submit:** uploading is a separate human *selector* step — full-registry scan +
  weekly-cap check first (see [submission guide](docs/executive-summary.html)).
  This project uploaded nothing; **no organizer score exists for this file.**
- [Research site](https://buffedlizard55-lab.github.io/GEMSDOE70/) · [Run card (amended, with erratum)](evidence/run_card_e3_amended.json)
- [Results](docs/results.html) · [H33 forensic analysis](docs/h33-analysis.md) · [Hypotheses E1–E3](docs/hypotheses-e3.md)
- [Limitations / next steps](docs/irregularities.md) · [Session handoff](HANDOFF.md)
- **Session start:** read this README, the retained brief below, AGENTS.md and HANDOFF.md.

## What was done (3 experiments, budget exhausted)

Shared `vendor/gems57` evaluator/writer/validator/uniqueness tools are byte-pinned
and unmodified ([verification](evidence/template_verification.json)). Data were
restored from SHA-pinned public owner mirrors (consistency only, not organizer
authentication). Official problem/about pages were retrieved 2026-10-20 and match
the tools (DTI α=0.2, β=0.8, R=300 m; float32 [0,1], EPSG:32611).

1. **E1 (negative):** magnetic-edge termination — continuous HOLDOUT-DTI 0.0102,
   below random. Archived in `evidence/history/e1-contact-termination-20261020/`.
2. **E2 (negative):** DEM scarp × geodetic strain × shallow-cover — dotted
   HOLDOUT-DTI 0.0598; gates falsified (cover direction wrong).
3. **E3 (promote-to-selector):** DEM scarp curvature alone — **HOLDOUT-DTI:
   {d['dti']:.4f}**, 95% CI [{d['ci95'][0]:.4f}, {d['ci95'][1]:.4f}],
   {d['withheld_positive_pixels']:,} withheld positives, evaluator
   `{d['evaluator_version']}` (seed-40 hide-and-recover; beats matched random
   0.0607 with paired CI excluding 0). Holdout is a falsification gate, **not**
   a predicted leaderboard score — the H33 champion itself scores 0.0043 on
   E2 catalogue-recovery folds. Uniqueness vs H33: forward overlap 0.342,
   Jaccard 0.0142, Spearman 0.0198 (63 hash-verified rasters checked; full
   862-raster scan remains a selector step; literal gate fires vacuously on
   5 saturating covering fields — see Limitations). The family-reported H33
   0.2778 has no organizer receipt here; no "beat it" claim is made.

Why H33 scored: sparse dotted emission + catalogue-flank pruning is
metric-efficient (preserves kernel coverage, cuts penalised mass) — conditional
algebra on top of a multi-layer ranking, detailed in the forensic analysis.
E3 attacks the ranking side with an independent scarp-curvature signal
(AUC ≈0.60–0.61 on two untouched fold sets) and the same efficiency lessons
(binary dots, 2.8 px spacing, off-catalogue, zeros export fixing [0,1] errors).

## Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.lock
bash scripts/download_competition_data.sh  # pinned mirrors (gh); see HANDOFF for git-sparse fallback
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/validate_submission.py docs/downloads/{name}.tif
```

Experiment drivers refuse reruns (manifest guards); do not delete manifests to
tune. `scripts/complete_e3_release.py` is the disclosed erratum completion
(SHA-verified reproduction), not a fourth experiment.

## Own the outcome

Maximize P(Win) by protecting the slot: honest negatives, labelled numbers
(HOLDOUT-DTI vs ORGANIZER-CONFIRMED), and selector discipline beat hopeful
uploads. Next-session priorities are in HANDOFF.md.

## Complete retained project prompt

Historical statements below are user-supplied requirements/claims, not verified
results. No leaderboard value below becomes ORGANIZER-CONFIRMED by copying.

<details>
<summary>Read the complete supplied project brief before every session</summary>

"""
    (ROOT / "README.md").write_text(
        head + (ROOT / "PROJECT_BRIEF.md").read_text() + "\n</details>\n")


if __name__ == "__main__":
    main()
