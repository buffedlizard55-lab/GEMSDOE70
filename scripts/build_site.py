"""Evidence-driven GitHub Pages site for the current (E3) run.

Publishes the hash-bound released TIF/ZIP only when the E3 release contract
passes; otherwise publishes no raster and a DO NOT SUBMIT banner. E1/E2
negative history is retained on the results page. Static reporting only:
nothing is trained or generated in the browser.
"""
from pathlib import Path
import hashlib
import html
import json
import os
import shutil
import sys

import markdown

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems70.release_e3 import (  # noqa: E402
    assert_publication_e3, assert_root_guard_e3, digest, release_status_e3,
)

DOCS = ROOT / "docs"
E = ROOT / "evidence"


def md(path):
    return markdown.markdown(Path(path).read_text(), extensions=["tables", "fenced_code"])


def frame(title, body, desc):
    links = [("index.html", "Overview"), ("executive-summary.html", "Submission guide"),
             ("results.html", "Results"), ("hypotheses.html", "Hypotheses"),
             ("h33-analysis.html", "H33 analysis"), ("sources.html", "Sources"),
             ("irregularities.html", "Limitations")]
    nav = "".join(f'<a href="{u}">{t}</a>' for u, t in links)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · GEMSDOE70</title><meta name="description" content="{html.escape(desc)}">
<link rel="stylesheet" href="assets/site.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a><span class="edition">RESEARCH WORKBENCH / OCT 2026</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main><footer>Evidence before leaderboard claims. No competition upload performed by this project.
<a href="run-card.json">Machine-readable run card</a> · <a href="sources.html">Provenance</a></footer></body></html>"""


def publish_released(card):
    """Copy submissions/ artifacts into docs/downloads iff hash-bound to card."""
    name = card["submission_name"]
    downloads = DOCS / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    for suffix, key in ((".tif", "raster_sha256"),):
        src = ROOT / "submissions" / f"{name}{suffix}"
        dst = downloads / f"{name}{suffix}"
        if src.is_file():
            if digest(src) != card[key]:
                raise ValueError("submissions TIFF hash does not match run card")
            if not dst.is_file() or digest(dst) != card[key]:
                shutil.copyfile(src, dst)
                os.chmod(dst, 0o644)
        if not dst.is_file() or digest(dst) != card[key]:
            raise ValueError("released TIFF missing or hash mismatch in docs/downloads")
    receipt = json.loads((E / "validator_e3.json").read_text())
    src = ROOT / "submissions" / f"{name}.zip"
    dst = downloads / f"{name}.zip"
    if src.is_file():
        if digest(src) != receipt["zip_sha256"]:
            raise ValueError("submissions ZIP hash does not match receipt")
        if not dst.is_file() or digest(dst) != receipt["zip_sha256"]:
            shutil.copyfile(src, dst)
            os.chmod(dst, 0o644)
    if not dst.is_file() or digest(dst) != receipt["zip_sha256"]:
        raise ValueError("released ZIP missing or hash mismatch in docs/downloads")


def main():
    card = json.loads((E / "run_card_e3_amended.json").read_text())
    promote = card.get("verdict") == "promote"
    if promote:
        publish_released(card)
    status = assert_publication_e3(ROOT)
    assert_root_guard_e3(ROOT)
    ok = bool(status["download_candidate_ok"])
    hold = json.loads((E / "holdout_e3.json").read_text())
    hold2 = json.loads((E / "holdout_e2.json").read_text())
    can3 = json.loads((E / "canaries_e3.json").read_text())
    uniq = json.loads((E / "final_uniqueness_e3.json").read_text()) if promote else None
    sources = json.loads((ROOT / "registry/sources.json").read_text())
    health = json.loads((E / "source_health.json").read_text())

    downloads = DOCS / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    for name in ["run_card_e3_amended.json", "run_card_e3.json", "run_card_e2.json",
                 "holdout_e3.json", "holdout_folds_e3.json", "holdout_split_e3.json",
                 "canaries_e3.json", "selection_grid_e3.json",
                 "surface_uniqueness_e3.json", "surface_uniqueness_e3_corrected.json",
                 "final_uniqueness_e3.json", "validator_e3.json",
                 "validator_independent_e3.json", "holdout_e2.json",
                 "holdout_continuous_e2.json", "canaries_e2.json",
                 "selection_grid_e2.json", "surface_uniqueness_e2.json",
                 "saturation_certificates_e2.json", "data_receipt_e2.json",
                 "run_card.json", "holdout.json", "canaries.json", "h33_audit.json",
                 "template_verification.json", "source_health.json",
                 "experiment_manifest_e2.json", "experiment_manifest_e3.json"]:
        shutil.copyfile(E / name, downloads / name)
    shutil.copyfile(E / "run_card_e3_amended.json", DOCS / "run-card.json")
    (DOCS / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    (DOCS / "sources.json").write_text(json.dumps(sources, indent=2) + "\n")

    d = card["holdout_dti"]
    ci = d["ci95"]
    ev = (f"HOLDOUT-DTI · {d['evaluator_version']} · "
          f"{d['withheld_positive_pixels']:,} withheld positive pixels")
    corr = card["correlation_overlap_vs_registry"]
    name = card["submission_name"]
    note = card["submission_note"]
    vs_h33, vs_h33_fwd = "", "—"
    if uniq:
        for r in uniq["audit"]["rows"]:
            if r.get("submission", "").endswith("GEMSDOE32__h33-2-b2-zeros.tif"):
                vs_h33_fwd = f"{r['my_dots_within_3px_of_theirs']:.2f}"
                vs_h33 = (f"forward overlap {r['my_dots_within_3px_of_theirs']:.3f}, "
                          f"Jaccard {r['jaccard_dot_sets']:.4f}, "
                          f"Spearman {r['spearman_full_footprint']:.4f}")
    if ok:
        banner = f"""<section class="go" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS — READ FIRST</div>
<h1 id="status">✅ OK to download this candidate TIF.</h1>
<p><strong>Download:</strong> <code>{html.escape(name)}.tif</code> ({card['n_final_dots']:,} dots, float32, all values in [0, 1] — locally validated).
<strong>Submit:</strong> uploading is a human <em>selector</em> decision — complete the two checks in the yellow box on the
<a href="executive-summary.html">submission guide</a> first (full-registry scan + weekly cap). This project has not uploaded anything and no organizer score exists for this file.</p>
<div class="actions"><a class="button primary" href="downloads/{html.escape(name)}.tif" download>⬇ Download submission TIF</a>
<a class="button secondary" href="downloads/{html.escape(name)}.zip" download>⬇ Download one-TIF ZIP</a>
<a class="button secondary" href="run-card.json" download>Download run card (JSON)</a></div>
<p class="small">File name to upload: <code>{html.escape(name)}.tif</code> (or the ZIP containing only it).<br>
Note to paste ({len(note)} characters): <code>{html.escape(note)}</code><br>
SHA-256: <code>{html.escape(str(card['raster_sha256']))}</code></p></section>"""
        desc = "Unique candidate GeoTIFF ready to download. Holdout-validated DEM scarp-curvature faults; selector review before upload."
    else:
        banner = """<section class="stop" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS — READ FIRST</div>
<h1 id="status">⛔ Do not submit. No released TIF.</h1>
<p>Release checks failed; no downloadable prediction is published. See results and limitations.</p>
<div class="actions"><button disabled>Submission TIFF unavailable</button>
<a class="button secondary" href="run-card.json" download>Download run card (JSON)</a></div></section>"""
        desc = "No released submission TIFF. See holdout evidence and limitations."

    metrics = f"""<div class="metrics"><section><div class="eyebrow">E3 DOTTED · HOLDOUT-DTI</div><div class="number">{d['dti']:.4f}</div>
<p>95% CI [{ci[0]:.4f}, {ci[1]:.4f}] · random control {d['random_control_dti']:.4f}</p></section>
<section><div class="eyebrow">UNIQUENESS VS H33 CHAMPION</div><div class="number">{vs_h33_fwd}</div><p>{html.escape(vs_h33)} (gates: overlap ≤0.70, ρ ≤0.90)</p></section>
<section><div class="eyebrow">COMPETITION ACTIVITY</div><div class="number">No upload</div><p>3 experiments (budget exhausted). 0 weekly slots used.</p></section></div>
<p class="caption">{ev}. Spatial-cluster bootstrap CI conditional on catalogue folds — not a leaderboard interval or score. The live champion scores near-zero on this catalogue-recovery instrument (see Results), so holdout falsifies weak rankings but does not predict live DTI.</p>"""

    warn = """<section class="warn"><h2>Before spending a weekly slot (selector checklist)</h2>
<ol><li>Complete the full 862-raster registry uniqueness scan (this session checked 63 hash-verified rasters including the champion lineage; the literal overlap gate still fires vacuously on 5 saturating covering fields — see Limitations).</li>
<li>Check remaining weekly allowance and current rules on the official submission page, and remember one selected submission is rescored in the Final Prize Round.</li></ol>
<p>Then follow the <a href="executive-summary.html">step-by-step submission guide</a>. Keep the organizer receipt with the SHA-256 above — only that receipt can create an ORGANIZER-CONFIRMED score.</p></section>"""

    overview = banner + f"""<section class="intro"><div class="eyebrow">WHAT THIS FILE IS</div><h2>Fresh eyes on old scarps.</h2>
<p>Binary fault-scarp dots from 100 m detrended-elevation curvature (slope × profile curvature × structure-tensor coherence), placed off-catalogue with 2.8 px spacing. Two gated variants (magnetic termination; scarp×strain×cover) were falsified first and are kept as negative deliverables. No previous submission was copied: worst non-saturating registry overlap is {corr['final_worst_forward_nonsaturating']:.3f}.</p></section>{metrics}{warn if ok else ''}
<div class="columns"><section class="panel"><h2>Why did H33 score 0.2778?</h2><p>Forensics show an efficient sparse field plus catalogue-flank pruning — emission efficiency under the distance-weighted Tversky metric, not a new detector. The value is family-reported, with no organizer receipt here.</p><a href="h33-analysis.html">Read the forensic analysis →</a></section>
<section class="panel"><h2>Can this beat it?</h2><p>Unknown until an organizer receipt exists. E3 has independent ranking evidence (AUC ≈0.61 on two untouched fold sets) and a distinct dot field, but catalogue-recovery holdout cannot predict live off-catalogue performance.</p><a href="results.html">See all holdout numbers →</a></section></div>
<section><h2>Audit trail</h2><ul><li><a href="hypotheses.html">Preregistered hypotheses (E1–E3)</a></li><li><a href="sources.html">Official sources &amp; provenance</a></li><li><a href="irregularities.html">Limitations, erratum &amp; next steps</a></li></ul></section>"""
    (DOCS / "index.html").write_text(frame("Overview", overview, desc))

    guide = banner + f"""<section><h2>Exactly how to make the submission</h2>
<ol class="steps">
<li><strong>Download</strong> <code>{html.escape(name)}.tif</code> above (or the ZIP — it contains only that one TIF). Do not upload JSON/HTML evidence files.</li>
<li><strong>(Optional) Verify the bytes:</strong> SHA-256 must equal <code>{html.escape(str(card['raster_sha256']))}</code>. Any other hash is not this candidate.</li>
<li><strong>Selector checks:</strong> full-registry uniqueness scan; weekly allowance + rules on the official page. One chosen submission counts for both prize rounds — choose deliberately.</li>
<li><strong>Open the official New submission form</strong> at <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition 306</a>, choose the TIF (single-band GeoTIFF matching the sample CRS EPSG:32611, shape 3730×3292, transform [100, 0, 243350, 0, −100, 4508550]).</li>
<li><strong>Paste this Note</strong> ({len(note)} of 140 characters): <code>{html.escape(note)}</code></li>
<li><strong>Submit once</strong> and save the organizer receipt (time, filename, note, displayed score) with the SHA-256. Only that receipt is ORGANIZER-CONFIRMED evidence.</li></ol>
<h2>About “Predicted values must be in range [0, 1]”</h2>
<p>This file is binary float32 {{0, 1}} everywhere: 0 NaN, 0 Inf, no nodata sentinels, zeros (not NaN) outside the footprint and on mapped faults. The shared writer rejects any non-finite or out-of-range array instead of clipping, and the on-disk validator re-read these exact bytes (all checks passed — see <a href="downloads/validator_e3.json">receipt</a>). The earlier rejected file is unavailable for forensics, so its exact fault stays unknown; raw unnormalised bands, −3.4e38 sentinels and NaN exports are the usual causes, all excluded here by construction.</p>
<h2>What the numbers mean</h2><p>{ev}: <strong>{d['dti']:.4f}</strong> [95% CI {ci[0]:.4f}–{ci[1]:.4f}]. Holdout recovers withheld <em>catalogue</em> faults; the organizer tests <em>unmapped</em> faults. Treat holdout as a falsification gate passed, never as a predicted leaderboard score.</p></section>"""
    (DOCS / "executive-summary.html").write_text(frame("Submission guide", guide, desc))

    def score_rows(scores):
        return "".join(
            f'<tr><th scope="row">{html.escape(n)}</th><td>HOLDOUT-DTI</td><td>{r["dti"]:.4f}</td>'
            f'<td>[{r["ci95"][0]:.4f}, {r["ci95"][1]:.4f}]</td><td>{r["withheld_positive_pixels"]:,}</td></tr>'
            for n, r in scores.items())

    sat_rows = "".join(
        f'<tr><th scope="row">{html.escape(s["submission"])}</th><td>{s["covered_allowed_fraction"]:.3f}</td>'
        f'<td>{s["forward_overlap"]:.3f}</td><td>{s["jaccard"]:.4f}</td></tr>'
        for s in corr.get("saturating_fields") or [])
    results = banner + f"""<section><h2>E3 — scarp curvature alone (seed 40, primary)</h2>
<p>{ev}. Selected by preregistered max-DTI rule: budget {d['selected_budget']:,}, exclusion &gt;{d['selected_exclusion_px']} px (grid edge; 45k scored 0.0925 — curve flattening, live-prevalence caveat applies). Scarp canary AUC {can3['scarp']['auc']:.4f} (E2 seed-30 replicate 0.6006); no feature exceeded the 0.90 leakage stop.</p>
<div class="table-wrap"><table><thead><tr><th>Arm</th><th>Class</th><th>DTI</th><th>95% CI</th><th>Withheld</th></tr></thead><tbody>{score_rows(hold['scores'])}</tbody></table></div>
<h2>E2 — scarp×strain×cover (seed 30, negative)</h2>
<p>Joint dotted 0.0598 vs scarp-alone 0.0794 vs random 0.0525 (11,342 withheld): strain/cover gating falsified. Archived H33 on the same folds: 0.0043 — its catalogue-based pruning saw the withheld traces and it targets off-catalogue faults, proving this instrument cannot rank live designs.</p>
<div class="table-wrap"><table><thead><tr><th>Arm</th><th>Class</th><th>DTI</th><th>95% CI</th><th>Withheld</th></tr></thead><tbody>{score_rows(hold2['scores'])}</tbody></table></div>
<h2>E1 — magnetic termination (seed 20, negative)</h2><p>Continuous-surface HOLDOUT-DTI 0.0102 [0.0061, 0.0150], 11,321 withheld, below its random control (0.0472). Preserved in <code>evidence/history/e1-contact-termination-20261020/</code>.</p>
<h2>Uniqueness (63 hash-verified registry rasters)</h2>
<p>Vs H33 champion: {html.escape(vs_h33)}. Worst non-saturating forward overlap {corr['final_worst_forward_nonsaturating']:.3f} ({html.escape(str(corr['final_worst_forward_nonsaturating_submission']))}); worst Spearman {corr['final_worst_spearman']:.3f}. Literal gate fires only on saturating covering fields whose 3 px halos cover ≥70% of allowed cells (forward overlap then carries no duplication information; Jaccards ≤0.041):</p>
<div class="table-wrap"><table><thead><tr><th>Saturating field</th><th>Halo coverage</th><th>Forward overlap</th><th>Jaccard</th></tr></thead><tbody>{sat_rows}</tbody></table></div>
<p class="small">Full rows: <a href="downloads/final_uniqueness_e3.json">final_uniqueness_e3.json</a>. Inherited inventory lists 862 rasters; completing that scan is a selector step. No ORGANIZER-CONFIRMED score exists on this site.</p></section>"""
    (DOCS / "results.html").write_text(frame("Results", results, desc))

    hyps = (md(DOCS / "hypotheses-e3.md") + "<hr>" + md(DOCS / "hypotheses-e2.md")
            + "<hr>" + md(DOCS / "hypotheses.md"))
    (DOCS / "hypotheses.html").write_text(frame("Hypotheses", hyps, desc))
    (DOCS / "h33-analysis.html").write_text(frame("H33 analysis", md(DOCS / "h33-analysis.md"), desc))
    (DOCS / "irregularities.html").write_text(frame("Limitations", md(DOCS / "irregularities.md"), desc))

    srows = "".join(
        f'<tr><th scope="row"><a href="{html.escape(s["url"])}">{html.escape(s["id"])}</a></th>'
        f'<td>{html.escape(s["authority"])}</td><td>{html.escape(s["status"])}</td>'
        f'<td>{html.escape(s["claim"])}<br><small>{html.escape(s["limit"])}</small></td></tr>'
        for s in sources)
    srcpage = f"""<div class="eyebrow">AUDITABLE KNOWLEDGE</div><h1>Know what the evidence can say.</h1>
<p>Official problem/about pages were retrieved and verified this session (2026-10-20); the leaderboard renders via JavaScript and standings remain unverified. Mirror hashes prove consistency, not organizer authentication.</p>
<p>Source-health snapshot: <time>{html.escape(str(health.get('generated_utc', 'see file')))}</time> (availability only, not a score feed).</p>
<div class="table-wrap"><table><thead><tr><th>Source</th><th>Authority</th><th>Session status</th><th>Claim and limit</th></tr></thead><tbody>{srows}</tbody></table></div>
<h2>Receipts</h2><p><a href="downloads/validator_e3.json">Writer/validator receipt</a> · <a href="downloads/run_card_e3_amended.json">Amended run card + erratum</a> · <a href="downloads/holdout_e3.json">Holdout E3</a> · <a href="downloads/template_verification.json">Template verification</a> · <a href="sources.json">Source ledger</a></p>"""
    (DOCS / "sources.html").write_text(frame("Sources", srcpage, desc))
    (DOCS / ".nojekyll").touch()

    headline = ("Candidate TIF ready to download — selector review before upload"
                if ok else "DO NOT SUBMIT — no released TIF")
    (ROOT / "index.html").write_text(
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70</title></head>'
        f'<body><h1>GEMSDOE70: {html.escape(headline)}</h1>'
        f'<p><a href="docs/index.html">Open the research workbench and submission status</a>.</p></body></html>\n')
    redirects = {"executive-summary": "executive-summary", "research": "hypotheses",
                 "requirements": "irregularities", "review": "irregularities",
                 "run-card": "results", "sources": "sources"}
    for old, target in redirects.items():
        (ROOT / f"{old}.html").write_text(
            f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="refresh" content="0;url=docs/{target}.html"><title>GEMSDOE70</title></head>'
            f'<body><h1>{html.escape(headline)}</h1><p><a href="docs/{target}.html">Continue to the current workbench</a>.</p></body></html>\n')
    print(f"Built site. download_candidate_ok={ok}; "
          + (f"released {name}.tif sha256={card['raster_sha256']}" if ok else "no raster published"))


if __name__ == "__main__":
    main()
