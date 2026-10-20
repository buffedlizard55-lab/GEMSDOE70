"""Deterministic evidence-driven Pages site (E1 archived + E2 review candidate + E3).

Submit status is fail-closed: the only public TIFF/ZIP allowed is the
hash-pinned E2 selector-review artifact, bannered DO NOT SUBMIT YET.
"""
from pathlib import Path
import html
import json
import shutil
import sys
import markdown

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems70.release import candidate_status, assert_review_rasters  # noqa: E402

DOCS = ROOT / "docs"


def md(path):
    return markdown.markdown(path.read_text(), extensions=["tables", "fenced_code"])


def frame(title, body, desc="Auditable geothermal fault research. Unique candidate for selector review; DO NOT SUBMIT YET."):
    links = [("index.html", "Overview"), ("executive-summary.html", "Submission guide"),
             ("results.html", "Results"), ("hypotheses.html", "Hypotheses"),
             ("h33-analysis.html", "H33 analysis"), ("sources.html", "Sources"),
             ("irregularities.html", "Limitations")]
    nav = "".join(f'<a href="{url}">{label}</a>' for url, label in links)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · GEMSDOE70</title><meta name="description" content="{html.escape(desc)}">
<link rel="stylesheet" href="assets/site.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a><span class="edition">RESEARCH WORKBENCH / OCT 2026</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main><footer>Evidence before leaderboard claims. No competition upload performed by this repo.
<a href="run-card-e2.json">E2 run card</a> · <a href="sources.html">Provenance</a></footer></body></html>'''


def score_table(hold):
    rows = "".join(
        f'<tr><th scope="row">{html.escape(n)}</th><td>HOLDOUT-DTI</td><td>{r["dti"]:.6f}</td>'
        f'<td>[{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}]</td></tr>'
        for n, r in sorted(hold["scores"].items(), key=lambda kv: -kv[1]["dti"]))
    return f'''<div class="table-wrap"><table><caption>Same evaluator, folds, masks and withheld positives; pooled terms, paired spatial bootstrap.</caption>
<thead><tr><th>Arm</th><th>Evidence class</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{rows}</tbody></table></div>'''


def main():
    assert_review_rasters(ROOT)
    st = candidate_status(ROOT)
    e1 = json.loads((ROOT / "evidence/run_card.json").read_text())
    e2 = json.loads((ROOT / "evidence/e2/run_card.json").read_text())
    e3 = json.loads((ROOT / "evidence/e3/run_card.json").read_text())
    h2 = json.loads((ROOT / "evidence/e2/holdout.json").read_text())
    h3 = json.loads((ROOT / "evidence/e3/holdout.json").read_text())
    c2 = json.loads((ROOT / "evidence/e2/canaries.json").read_text())
    pub = json.loads((ROOT / "evidence/e2/publication.json").read_text())
    lb = json.loads((ROOT / "evidence/leaderboard_read.json").read_text())
    sources = json.loads((ROOT / "registry/sources.json").read_text())
    DOCS.mkdir(exist_ok=True)
    downloads = DOCS / "downloads"
    downloads.mkdir(exist_ok=True)
    for src, dst in [
        ("evidence/run_card.json", "e1_run_card.json"), ("evidence/holdout.json", "e1_holdout.json"),
        ("evidence/canaries.json", "e1_canaries.json"),
        ("evidence/e2/run_card.json", "e2_run_card.json"), ("evidence/e2/holdout.json", "e2_holdout.json"),
        ("evidence/e2/canaries.json", "e2_canaries.json"),
        ("evidence/e2/holdout_confirm_seed21.json", "e2_confirm_seed21.json"),
        ("evidence/e2/surface_uniqueness.json", "e2_surface_uniqueness.json"),
        ("evidence/e2/final_uniqueness.json", "e2_final_uniqueness.json"),
        ("evidence/e2/publication.json", "e2_publication.json"),
        ("evidence/e2/validator.json", "e2_validator.json"),
        ("evidence/e3/run_card.json", "e3_run_card.json"), ("evidence/e3/holdout.json", "e3_holdout.json"),
        ("evidence/e3/canaries.json", "e3_canaries.json"),
        ("evidence/e3/final_uniqueness.json", "e3_final_uniqueness.json"),
        ("evidence/h33_audit.json", "h33_audit.json"), ("evidence/data_receipt.json", "data_receipt.json"),
        ("evidence/leaderboard_read.json", "leaderboard_read.json"),
    ]:
        shutil.copyfile(ROOT / src, downloads / dst)
    shutil.copyfile(ROOT / "evidence/e2/run_card.json", DOCS / "run-card-e2.json")
    shutil.copyfile(ROOT / "evidence/run_card.json", DOCS / "run-card.json")
    # session merged view: frozen E2 card + publication receipt (card itself untouched)
    merged = {**e2, "publication_amendment": "docs/publication-amendment-e2.md",
              "raster_sha256_published": pub["sha256"], "raster_file": pub["file"],
              "validator_output_published": pub["validate"],
              "download_ok_for_selector_review": st["download_ok_for_selector_review"],
              "submit_ok": False}
    (DOCS / "run-card-e2-published.json").write_text(json.dumps(merged, indent=2) + "\n")
    shutil.copyfile(DOCS / "run-card-e2-published.json", downloads / "e2_run_card_published.json")
    (DOCS / "status.json").write_text(json.dumps(st, indent=2) + "\n")
    (DOCS / "sources.json").write_text(json.dumps(sources, indent=2) + "\n")

    f = html.escape(st["file"]); z = html.escape(st["zip_file"])
    name = html.escape(st["submission_name"]); note = html.escape(st["submission_note"])
    d2 = e2["holdout_dti"]; ci = d2["ci95"]
    cand = f'''<section class="stop" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS — READ FIRST</div>
<h1 id="status">DO NOT SUBMIT YET.</h1>
<p><strong>Download for selector review: YES.</strong> A unique candidate GeoTIFF is available below so the selector can run the complete registry scan and slot decision.
<strong>Submit to DrivenData: NO</strong> — promotion bars failed (D28 catalogue-holdout best not beaten). Submitting now would spend a slot on an unpromoted candidate.</p>
<div class="actions"><a class="button" href="downloads/{f}" download>⬇ Download candidate TIFF (review only)</a>
<a class="button secondary" href="downloads/{z}" download>ZIP (single TIFF)</a>
<a class="button secondary" href="run-card-e2-published.json" download>Run card (JSON)</a></div>
<p><strong>File:</strong> <code>{f}</code><br><strong>SHA-256:</strong> <code>{html.escape(st["sha256"] or "")}</code><br>
<strong>Submission name (if selector ever approves):</strong> <code>{name}</code><br>
<strong>Note to paste ({len(st["submission_note"] or "")} characters):</strong> <code>{note}</code></p>
<p class="small">Single band · float32 · EPSG:32611 · 100 m · 3730×3292 · 38,000 dots · every cell finite · values in [0,1] · 0 on catalogue · no nodata tag. Local validator PASS — not organizer acceptance. Exact conditions to flip to “submit” are in the <a href="executive-summary.html">submission guide</a>.</p></section>'''
    metrics = f'''<div class="metrics"><section><div class="eyebrow">E2 DOTS · HOLDOUT-DTI</div><div class="number">{d2["dti"]:.5f}</div><p>95% CI [{ci[0]:.5f}, {ci[1]:.5f}] · beats random, loses to D28 (0.09192)</p></section>
<section><div class="eyebrow">UNIQUENESS (7-RASTER SUBSET, R1)</div><div class="number">ρ ≤ 0.039</div><p>Worst R1 overlap 0.443 (limit 0.70). Complete scan still required.</p></section>
<section><div class="eyebrow">PUBLIC LEADER AT READ 2026-10-20</div><div class="number">0.4413</div><p>Organizer page read; family H33 0.2778 is user-reported, no receipt here.</p></section></div>'''
    overview = cand + f'''<section class="intro"><div class="eyebrow">UNIQUE CANDIDATE, HONEST VERDICT</div><h2>New geology. No borrowed dots.</h2>
<p>E2 ranks blind basin faults by an oriented alluvial elevation step guided by magnetic strike — a lane not used by H33/H19-5 — and shares only 797 exact pixels (2.1%) with H33. It recovers withheld catalogue faults far better than random, but the incumbent dotted ranking still recovers them better, so this session does not promote it. E3 (magnetic depth-step) and archived E1 are also negative. Negative results are deliverables.</p></section>{metrics}
<p class="caption">HOLDOUT-DTI · {html.escape(d2["evaluator_version"])} · {d2["withheld_positive_pixels"]:,} withheld positive pixels · catalogue hide-and-recover, not hidden live faults and not a leaderboard score. On this instrument H33 itself scores 0.00370 (below random) — see why in the <a href="h33-analysis.html">H33 analysis</a> before ranking any far-field field by catalogue recovery alone.</p>
<div class="columns"><section class="panel"><h2>Why download if not submit?</h2><p>Candidate generation and slot selection are separate steps. The selector needs exact bytes for the complete registry scan, R1 acknowledgment and cap check listed in the guide.</p><a href="executive-summary.html">Exact submission steps →</a></section>
<section class="panel"><h2>Why did H33 lead the family?</h2><p>Strong ranking + kernel-scale thinning + catalogue-flank pruning: emission efficiency, not a new detector. The same table shows what beating 0.2778 — and 0.4413 — actually requires.</p><a href="h33-analysis.html">Forensic analysis →</a></section></div>
<section><h2>Reproducible, not speculative</h2><p>Pinned mirror stack, byte-identical shared evaluator/writer, per-feature leakage canaries, paired bootstrap intervals, from-scratch recomputation matched the experiment mask byte-for-byte before writing.</p>
<ul><li><a href="results.html">E1/E2/E3 measured results</a></li><li><a href="hypotheses.html">Ranked hypotheses + frozen E2/E3 preregistration</a></li><li><a href="irregularities.html">Limitations, irregularities, next steps</a></li></ul></section>'''
    (DOCS / "index.html").write_text(frame("Overview", overview))

    guide = f'''<div class="eyebrow">EXECUTIVE SUMMARY</div><h1>How a submission happens — exactly.</h1>
<section class="stop"><h2>Current status: DO NOT SUBMIT YET</h2><p>Download-for-review is YES; submitting is NO until every selector condition below is recorded. This page tells you precisely what “ready” would mean so there is no ambiguity at the portal.</p></section>
<h2>The candidate (selector-review only)</h2>
<p><strong>File:</strong> <code>{f}</code> · <a href="downloads/{f}" download>Download TIFF</a> · <a href="downloads/{z}" download>Download ZIP</a><br>
<strong>SHA-256:</strong> <code>{html.escape(st["sha256"] or "")}</code><br>
<strong>Unique name:</strong> <code>{name}</code><br>
<strong>Note (paste verbatim if ever approved, {len(st["submission_note"] or "")}/140 chars):</strong><br><code>{note}</code></p>
<h2>Selector conditions (all required before any upload)</h2><ol class="steps">
<li><strong>Complete registry scan.</strong> Run R1 uniqueness (rho ≤ 0.90, overlap ≤ 0.70) against the complete accessible inventory (862 inherited-index rasters or fresher), on surface and final dots. This session checked a disclosed 7-raster subset only.</li>
<li><strong>Acknowledge protocol revision R1</strong> for dense continuous registry surfaces (<a href="hypotheses.html">text in preregistration bundle</a>; repo file <code>docs/protocol-revision-uniqueness.md</code>). If R1 is rejected, never submit this file.</li>
<li><strong>Check the live cap.</strong> Open the official submission page, confirm remaining weekly allowance and current rules. This repo does not know your remaining slots and used none.</li>
<li><strong>Accept the holdout result in writing.</strong> E2 did not beat D28 on catalogue holdout; no live score is predicted. Keep that acceptance with the receipt.</li></ol>
<h2>Portal steps (only after all conditions above)</h2><ol class="steps">
<li>Go to the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">official competition</a> → <strong>New submission</strong>.</li>
<li><strong>File to submit:</strong> choose the downloaded <code>.tif</code> above (or the <code>.zip</code> containing that single TIFF). Verify the SHA-256 of your local copy matches this page before uploading.</li>
<li><strong>Note (optional):</strong> paste the note verbatim. It distinguishes this candidate from every prior family file.</li>
<li>Submit once. <strong>Save the organizer receipt</strong> (score, time, filename) — only that receipt can create an ORGANIZER-CONFIRMED score. Report it back with the SHA-256.</li>
<li>Remember the two-round structure: one selected submission is rescored after expert label expansion. Do not assume round-1 flank pruning is free in round 2 (see H33 analysis caveat).</li></ol>
<h2>“Predicted values must be in range [0, 1]” — why this file passes local checks</h2>
<p>That portal error fires when any read value (or a nodata sentinel such as −3.4e38 from the feature stack) lies outside [0,1]. This candidate was written by the shared writer, which <em>rejects</em> non-finite/out-of-range arrays instead of clipping, then re-read from disk: all 12,279,160 cells finite, min 0.0, max 1.0, no NaN/Inf/sentinels, no nodata tag, single-band float32, EPSG:32611, transform [100, 0, 243350, 0, −100, 4508550]. Receipts: <a href="downloads/e2_validator.json">validator</a> · <a href="downloads/e2_publication.json">publication + recomputation match</a>. Local PASS is not organizer acceptance.</p>
<h2>What this site cannot do</h2><p>It does not train in-browser, does not know your slot balance, and does not confirm live scores. Public leader at last read (2026-10-20): 0.4413 — recheck live before deciding.</p>'''
    (DOCS / "executive-summary.html").write_text(frame("Submission guide", guide))

    aucrows = "".join(
        f'<tr><th scope="row">{html.escape(n)}</th><td>{r["auc"]:.4f}</td><td>{"STOP" if r["suspected_leakage"] else "No alarm"}</td></tr>'
        for n, r in c2.items())
    results = f'''<div class="eyebrow">MEASURED RESULTS</div><h1>Evidence, including the failures.</h1>
<h2>E2 — alluvial step (primary, seed-20)</h2><p>HOLDOUT-DTI · {html.escape(d2["evaluator_version"])} · {d2["withheld_positive_pixels"]:,} withheld positives. Candidate dots beat random (paired Δ +0.02222, CI [+0.00786, +0.03721]) and every ablation, tie H19-solid at one-third mass, lose to D28 (Δ −0.02727, CI [−0.04349, −0.01128]). Confirmatory seed-21 candidate 0.06557 (see downloads). Verdict: <strong>negative — DO NOT SUBMIT YET</strong>.</p>{score_table(h2)}
<p>Reference caveat: H33/D28/H19 fields used full-catalogue knowledge; values are same-instrument references, not clean generalization. H33 scoring last here measures instrument mismatch (live new faults vs catalogue pieces), not H33 live quality.</p>
<h2>E2 leakage canaries (AUC, not DTI)</h2><div class="table-wrap"><table><thead><tr><th>Feature alone</th><th>AUC</th><th>Result</th></tr></thead><tbody>{aucrows}</tbody></table></div>
<h2>E3 — magnetic depth-step (contingent)</h2><p>Mechanism canary AUC 0.5062 (null); candidate HOLDOUT-DTI {e3["holdout_dti"]["dti"]:.5f} carried by its basement-edge partner. Negative; no file published.</p>{score_table(h3)}
<h2>E1 — contact termination (archived)</h2><p>Continuous-surface HOLDOUT-DTI {e1["holdout_dti"]["dti"]:.5f}, worse than its random control; stopped at the literal dense-prior gate. Preserved untouched in <a href="downloads/e1_run_card.json">E1 run card</a>.</p>
<h2>Uniqueness + format receipts (E2)</h2><p>Final dots: worst Spearman {e2["correlation_overlap_vs_registry"]["final_worst_spearman"]:.4f}, worst R1 overlap {e2["correlation_overlap_vs_registry"]["final_r1_worst_overlap"]:.4f} (7-raster subset); literal dense overlap 1.0 published as degenerate (R1). Exact shared pixels with H33: 797/38,000. <a href="downloads/e2_final_uniqueness.json">Final audit</a> · <a href="downloads/e2_surface_uniqueness.json">Surface audit</a> · <a href="downloads/e2_validator.json">Validator</a> · <a href="downloads/e2_publication.json">Publication</a></p>'''
    (DOCS / "results.html").write_text(frame("Results", results))

    hyp = md(DOCS / "hypotheses.md") + "<hr>" + md(DOCS / "preregistration-e2.md") + "<hr>" + md(DOCS / "protocol-revision-uniqueness.md") + "<hr>" + md(DOCS / "publication-amendment-e2.md")
    (DOCS / "hypotheses.html").write_text(frame("Hypotheses", hyp))
    (DOCS / "h33-analysis.html").write_text(frame("H33 analysis", md(DOCS / "h33-analysis.md")))
    (DOCS / "irregularities.html").write_text(frame("Limitations", md(DOCS / "irregularities.md")))

    srows = "".join(
        f'<tr><th scope="row"><a href="{html.escape(s["url"])}">{html.escape(s["id"])}</a></th><td>{html.escape(s["authority"])}</td>'
        f'<td>{html.escape(s["status"])}</td><td>{html.escape(s["claim"])}<br><small>{html.escape(s["limit"])}</small></td></tr>'
        for s in sources)
    lbrows = "".join(
        f'<tr><td>{r["rank"]}</td><td>{html.escape(r["participant"])}</td><td>{r["best_public_dw_tversky"]:.4f}</td></tr>'
        for r in lb["top_rows_at_read"])
    srcpage = f'''<div class="eyebrow">AUDITABLE KNOWLEDGE</div><h1>Know what the evidence can say.</h1>
<p>Organizer problem/about/leaderboard pages were fetched 2026-10-20 in this session. Mirror hashes prove consistency, not organizer authentication. No score below is ORGANIZER-CONFIRMED for this repo (no submission receipt).</p>
<h2>Public leaderboard at read (organizer page)</h2><div class="table-wrap"><table><thead><tr><th>Rank</th><th>Participant</th><th>Best public DW-Tversky</th></tr></thead><tbody>{lbrows}</tbody></table></div>
<p><a href="downloads/leaderboard_read.json">Leaderboard read receipt</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Live leaderboard (recheck before deciding)</a></p>
<div class="table-wrap"><table><thead><tr><th>Source</th><th>Authority</th><th>Session status</th><th>Claim and limit</th></tr></thead><tbody>{srows}</tbody></table></div>
<h2>Receipts</h2><p><a href="downloads/data_receipt.json">Input checksums</a> · <a href="downloads/e2_validator.json">Candidate validator</a> · <a href="sources.json">Source ledger</a></p>
<h2>Research note</h2><p>Fault traces are the prediction target — not geothermal vents. A step or depth discontinuity can be a terrace, shoreline, intrusive contact or processing artefact; named mimics travel with every hypothesis. No vent, temperature, permeability or resource claim is made.</p>'''
    (DOCS / "sources.html").write_text(frame("Sources", srcpage))
    (DOCS / ".nojekyll").touch()
    (ROOT / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70</title></head><body>'
        '<h1>GEMSDOE70: DO NOT SUBMIT YET — candidate for selector review</h1>'
        '<p><a href="docs/index.html">Open status, candidate download and submission guide</a>.</p></body></html>\n')
    redirects = {"executive-summary": "executive-summary", "research": "hypotheses",
                 "requirements": "irregularities", "review": "irregularities",
                 "run-card": "results", "sources": "sources"}
    for old, target in redirects.items():
        (ROOT / f"{old}.html").write_text(
            f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="refresh" content="0;url=docs/{target}.html"><title>GEMSDOE70 — DO NOT SUBMIT YET</title></head><body>'
            f'<h1>DO NOT SUBMIT YET</h1><p>Selector-review candidate only. <a href="docs/{target}.html">Continue to current evidence</a>.</p></body></html>\n')
    print("Built site. E2 review candidate linked as DO NOT SUBMIT YET; submit_ok=false.")


if __name__ == "__main__":
    main()
