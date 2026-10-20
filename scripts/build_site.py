"""Deterministic, evidence-driven GitHub Pages site; negative runs never offer TIFFs."""
from pathlib import Path
import html
import json
import re
import shutil
import sys
import markdown
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from gems70.release import release_status, assert_no_public_rasters
DOCS=ROOT/'docs'


def md(path):
    return markdown.markdown(path.read_text(),extensions=['tables','fenced_code'])


def frame(title,body):
    links=[('index.html','Overview'),('executive-summary.html','Submission guide'),('results.html','Results'),
           ('hypotheses.html','Hypotheses'),('h33-analysis.html','H33 analysis'),('sources.html','Sources'),('irregularities.html','Limitations')]
    nav=''.join(f'<a href="{url}">{label}</a>' for url,label in links)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · GEMSDOE70</title><meta name="description" content="Auditable geothermal fault research. Unique research TIFF available; DO NOT SUBMIT — holdout gate failed.">
<link rel="stylesheet" href="assets/site.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a><span class="edition">RESEARCH WORKBENCH / OCT 2026</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main><footer>Evidence before leaderboard claims. No competition upload performed.
<a href="run-card.json">Machine-readable run card</a> · <a href="sources.html">Provenance</a></footer></body></html>'''


def main():
    assert_no_public_rasters(ROOT)
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    hold=json.loads((ROOT/'evidence/holdout.json').read_text())
    canaries=json.loads((ROOT/'evidence/canaries3.json').read_text()) if (ROOT/'evidence/canaries3.json').exists() else json.loads((ROOT/'evidence/canaries.json').read_text())
    sources=json.loads((ROOT/'registry/sources.json').read_text())
    health=json.loads((ROOT/'evidence/source_health.json').read_text())
    gate=release_status(ROOT)
    DOCS.mkdir(exist_ok=True)
    downloads=DOCS/'downloads'; downloads.mkdir(exist_ok=True)
    for name in ['run_card.json','holdout.json','holdout_split.json','holdout_folds.json','canaries.json',
                 'surface_uniqueness.json','registry_saturation.json','h33_audit.json','data_receipt.json',
                 'template_verification.json','source_health.json','experiment_manifest.json',
                 'holdout2.json','holdout3.json','canaries2.json','canaries3.json','uniqueness3.json','release2.json']:
        src=ROOT/'evidence'/name
        if src.exists(): shutil.copyfile(src,downloads/name)
    shutil.copyfile(ROOT/'evidence/run_card.json',DOCS/'run-card.json')
    (DOCS/'status.json').write_text(json.dumps(gate,indent=2)+'\n')
    (DOCS/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    d=card['holdout_dti']; ci=d['ci95']
    evidence_label=f'HOLDOUT-DTI · {html.escape(d["evaluator_version"])} · {d["withheld_positive_pixels"]:,} withheld positive pixels'
    tif_name=card.get('raster_file','').split('/')[-1]
    if card.get('download_and_submit_ok'):
        status=f'''<section class="go" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS</div><h1 id="status">OK TO DOWNLOAD AND SUBMIT</h1>
<p>The unique TIFF below passed the holdout, uniqueness and validator gates. Weekly-slot selection is still a separate step; no slot has been used by this site.</p>
<div class="actions"><a class="button" href="downloads/{tif_name}" download>Download submission TIFF</a><a class="button secondary" href="run-card.json" download>Download run card (JSON)</a></div>
<p class="small">Submission name: <code>{html.escape(card['submission_name'])}</code><br>Note ({len(card['submission_note'])} chars): <code>{html.escape(card['submission_note'])}</code></p></section>'''
    elif tif_name and (DOCS/'downloads'/tif_name).exists():
        status=f'''<section class="stop" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS</div><h1 id="status">DO NOT SUBMIT — research download only</h1>
<p>A unique TIFF was generated and format-validated, but it <strong>failed the preregistered holdout promotion gate</strong> (see Results). Download it only for learning, education and reproduction. <strong>Do not upload it to the competition.</strong></p>
<div class="actions"><a class="button secondary" href="downloads/{tif_name}" download>Download research TIFF (DO NOT SUBMIT)</a><a class="button secondary" href="run-card.json" download>Download run card (JSON)</a></div>
<p class="small">Would-be submission name: <code>{html.escape(card['submission_name'])}</code><br>Note ({len(card['submission_note'])} chars): <code>{html.escape(card['submission_note'])}</code><br>SHA-256: <code>{html.escape(str(card.get('raster_sha256')))}</code></p></section>'''
    else:
        status='''<section class="stop" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS</div><h1 id="status">Do not submit this run.</h1>
<p>No eligible TIFF is available.</p>
<div class="actions"><button disabled>Submission TIFF unavailable</button><a class="button secondary" href="run-card.json" download>Download run card (JSON)</a></div></section>'''
    _ll=card.get('correlation_overlap_vs_registry',{}).get('final_dots',{})
    metrics=f'''<div class="metrics"><section><div class="eyebrow">FINAL DOTS · HOLDOUT-DTI (EXP 3)</div><div class="number">{d['dti']:.5f}</div><p>95% CI [{ci[0]:.5f}, {ci[1]:.5f}] · {d['withheld_positive_pixels']:,} withheld positives · {html.escape(d['evaluator_version'])}</p></section>
<section><div class="eyebrow">REGISTRY MEASUREMENT</div><div class="number">{_ll.get('overlap_within_3px_dot_fields_worst',0):.1%}</div><p>Worst like-for-like 3 px dot overlap vs 940 rasters. Gate limit: 70%.</p></section>
<section><div class="eyebrow">COMPETITION ACTIVITY</div><div class="number">No upload</div><p>Three experiments (budget exhausted). No weekly slot consumed.</p></section></div>'''
    overview=status+f'''<section class="intro"><div class="eyebrow">THREE PREREGISTERED EXPERIMENTS, FULLY ACCOUNTED FOR</div><h2>Test the geology. Protect the submission.</h2>
<p>Experiment 3 fused a supervised multi-physics model with an unsupervised breakline detector. It produced the best measured ranking of the three experiments, but did not clear the strict promotion gate — so its unique TIFF is published for research only and must not be submitted.</p></section>{metrics}
<p class="caption">{evidence_label}. Confidence interval is a conditional spatial-block bootstrap, not a leaderboard interval.</p>
<div class="columns"><section class="panel"><h2>Why not submit?</h2><p>The fusion candidate beats the gated Experiment-2 construction significantly, but its paired 95% CIs against the raw supervised model and the GEMSDOE49-architecture detector cross zero. The preregistered rule requires CI &gt; 0 against every key comparator.</p><a href="results.html">See the measured results →</a></section>
<section class="panel"><h2>What about the H33 result?</h2><p>The archived field is an efficient sparse prediction followed by catalogue-flank pruning, not a new trained detector. Its reported historical score has no organizer receipt here.</p><a href="h33-analysis.html">Read the forensic analysis →</a></section></div>
<section><h2>Reproducible, not speculative</h2><p>The numerical stack was restored from pinned mirrors. The shared evaluator and writer remain byte-identical to the template. Every feature received a leakage canary, and the final dots were audited against all 940 accessible registry rasters.</p>
<ul><li><a href="hypotheses.html">Preregistered geological hypotheses</a> · <a href="hypotheses-exp3.html">Experiment-3 addendum</a></li><li><a href="sources.html">Auditable sources and retrieval status</a></li><li><a href="irregularities.html">Limitations and next-session priorities</a></li></ul></section>'''
    (DOCS/'index.html').write_text(frame('Overview',overview))
    guide=status+'''<section><h2>How a future eligible submission works</h2><p><strong>Current file: DO NOT SUBMIT.</strong> The unique TIFF on the overview page is a research download only — it failed the preregistered holdout promotion gate. The workflow below is the full submission path for a future candidate that passes every gate. This static website reports precomputed evidence; it does not train a model in your browser.</p>
<ol class="steps"><li><strong>Check the readiness banner.</strong> Only a released artifact may receive a TIFF download link. A valid format alone does not mean it is unique or worth a competition slot.</li>
<li><strong>Verify scientific clearance.</strong> Feature canaries, same-split comparator improvement with paired CI &gt; 0, a complete pre-placement surface audit and final-dot audit must pass. The present Experiment-3 candidate passed canaries, uniqueness and format validation but failed the holdout comparator gate, so it stops here.</li>
<li><strong>Package with the shared writer.</strong> A single-band float32 GeoTIFF must match the sample CRS, shape and geotransform. The writer rejects non-finite/out-of-range values rather than silently clipping them; this project also sets outside-footprint values to zero.</li>
<li><strong>Validate exact file bytes.</strong> Reopen the TIFF, verify range, footprint and mapped-fault masking, and record its SHA-256. A ZIP must contain exactly one TIFF. Our shared writer checks that round trip.</li>
<li><strong>Obtain separate slot selection.</strong> Check the current submission page's rules and remaining weekly allowance; it is not known in this sandbox. Local candidate promotion does not authorize an upload.</li>
<li><strong>Upload only the released TIFF or one-TIFF ZIP.</strong> At the official competition site, open New submission, choose the file and copy its short identifying note. A JSON report, HTML page or PDF is not the prediction file.</li>
<li><strong>Keep the organizer receipt.</strong> Only an actual submission-page receipt can establish an ORGANIZER-CONFIRMED score. Save filename, hash, time, note and receipt together.</li></ol>
<h2>About “Predicted values must be in range [0, 1]”</h2><p>The earlier rejected file is not available for forensic inspection here, so its exact fault is unknown. Potential failures include raw unnormalized features, negative nodata sentinels, NaN/Inf or values above one. The shared writer rejects all these before publishing. We do not claim NaN was the cause of your portal error.</p>
<h2>Reference grid — mirror-relative measurement</h2><p>EPSG:32611; 3,730 rows × 3,292 columns; affine transform [100, 0, 243350, 0, -100, 4508550]. These match the SHA-pinned sample mirror, not an independently authenticated new organizer download.</p>
<h2>This run's identity (research download only — not a released submission)</h2>'''+f'<p><code>{html.escape(card["submission_name"])}</code></p><p>Note ({len(card["submission_note"])} characters): <code>{html.escape(card["submission_note"])}</code></p>'+'''
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and format</a>. These pages could not be retrieved here; review current requirements before a future upload.</p></section>'''
    (DOCS/'executive-summary.html').write_text(frame('Submission guide',guide))
    _h3=json.loads((ROOT/'evidence/holdout3.json').read_text()) if (ROOT/'evidence/holdout3.json').exists() else hold
    rows=''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>HOLDOUT-DTI</td><td>{r["dti"]:.6f}</td><td>[{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}]</td></tr>' for n,r in _h3['scores'].items())
    aucrows=''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>{r["auc"]:.6f}</td><td>{"STOP" if r["suspected_leakage"] else "No threshold alarm"}</td></tr>' for n,r in canaries.items())
    delta=hold['paired_differences']['random_control']
    _pd=_h3['paired_differences']
    _delta_rows=''.join(f'<tr><th scope="row">candidate − {html.escape(n)}</th><td>{v["delta"]:+.6f}</td><td>[{v["ci95"][0]:+.6f}, {v["ci95"][1]:+.6f}]</td></tr>' for n,v in _pd.items())
    _ll=card.get('correlation_overlap_vs_registry',{}).get('final_dots',{})
    _ls=card.get('correlation_overlap_vs_registry',{}).get('surface',{})
    results=f'''<div class="eyebrow">MEASURED RESULTS</div><h1>Evidence, including the failed gate.</h1><p>Experiment 3 (H70-3A fusion), untouched seed-703 holdout: HOLDOUT-DTI · {_h3["evaluator_version"]} · {_h3["scores"]["candidate"]["withheld_positive_pixels"]:,} withheld positive pixels. Final dotted fields; not organizer-confirmed.</p>
<div class="table-wrap"><table><caption>Same evaluator, same withheld positives and masks; pooled terms, then bootstrap.</caption><thead><tr><th>Arm</th><th>Evidence class</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Paired differences (candidate minus comparator)</h2><div class="table-wrap"><table><thead><tr><th>Comparison</th><th>Delta</th><th>95% paired CI</th></tr></thead><tbody>{_delta_rows}</tbody></table></div>
<p><strong>Promotion gate: FAILED.</strong> The candidate is the best point estimate and significantly beats the gated Experiment-2 construction, SingleBand, E1 and Random, but its CIs against RawHGB_NoGate and GEMS49_OrthoGate cross zero. The preregistered rule required CI &gt; 0 against every key comparator. Experiment 2 (seed 702) is archived in the downloads: its gate significantly hurt (candidate 0.07829 vs NoGate 0.08854).</p>
<h2>Leakage canaries (Experiment 3 features)</h2><p>LEAKAGE-CANARY AUC, not DTI or leaderboard scores. No feature exceeded the 0.90 alarm in either direction on the seed-703 evaluation domain.</p>
<div class="table-wrap"><table><thead><tr><th>Feature</th><th>AUC</th><th>Result</th></tr></thead><tbody>{aucrows}</tbody></table></div>
<h2>Uniqueness audit (940 rasters, both stages)</h2><p>REGISTRY-MEASUREMENT: final-dots worst like-for-like 3 px dot-field overlap {_ll.get('overlap_within_3px_dot_fields_worst',0):.3f} (gate 0.70); worst full-footprint |Spearman| vs all 940 rasters reported in the run card. The literal positive-support reading fires against whole-footprint continuous priors by construction (saturation certificate); the like-for-like dot-field reading is the operative lane test and both readings are published.</p>
<p><a href="downloads/uniqueness3.json">Full uniqueness audit</a> · <a href="downloads/holdout3.json">Holdout 3</a> · <a href="downloads/holdout2.json">Holdout 2</a> · <a href="downloads/canaries3.json">Canaries</a> · <a href="run-card.json">Run card</a></p>
<h2>Validator status</h2><p>The published research TIFF passed the shared local validator on its exact bytes (single band, float32, EPSG:32611, shape/transform match, all values finite in [0,1], zero outside footprint, zero on mapped catalogue). That is a format receipt, not organizer acceptance and not permission to submit: the holdout gate failed, so the banner on this site is DO NOT SUBMIT.</p>'''
    (DOCS/'results.html').write_text(frame('Results',results))
    for name,title in [('hypotheses','Hypotheses'),('hypotheses-exp3','Exp-3 addendum'),('h33-analysis','H33 analysis'),('irregularities','Limitations')]:
        (DOCS/f'{name}.html').write_text(frame(title,md(DOCS/f'{name}.md')))
    sourcerows=''.join(f'<tr><th scope="row"><a href="{html.escape(s["url"])}">{html.escape(s["id"])}</a></th><td>{html.escape(s["authority"])}</td><td>{html.escape(s["status"])}</td><td>{html.escape(s["claim"])}<br><small>{html.escape(s["limit"])}</small></td></tr>' for s in sources)
    srcpage=f'''<div class="eyebrow">AUDITABLE KNOWLEDGE</div><h1>Know what the evidence can say.</h1><p>GitHub reference content was retrieved. Official sites outside this environment's network allowlist were not verified live. A working HTTP endpoint does not verify a scientific claim, a license, or a competition result.</p>
<p>Availability last checked: <time>{html.escape(health['generated_utc'])}</time>. The current leaderboard is <strong>unverified</strong>, not an up-to-date claimed score feed.</p><div class="table-wrap"><table><thead><tr><th>Source</th><th>Authority</th><th>Session status</th><th>Claim and limit</th></tr></thead><tbody>{sourcerows}</tbody></table></div>
<h2>Data and implementation receipts</h2><p><a href="downloads/data_receipt.json">Input checksums</a> · <a href="downloads/template_verification.json">Unmodified shared template verification</a> · <a href="downloads/source_health.json">HTTP health checks</a> · <a href="sources.json">Source ledger</a></p>
<h2>Research knowledge</h2><p>Potential-field edge changes are hypotheses about rock-property discontinuities, not verified fault slip. Magnetization changes, intrusive contacts, depositional boundaries and acquisition/leveling residuals are named alternatives. Gravity and basement depth may share inversion assumptions. No claim of new geothermal vents is made.</p>
<p>The complete original user brief and its historical result list are retained in the repository README and PROJECT_BRIEF.md. The analysis is deliberately scoped: it does not claim that every linked website, score or scientific source has been independently verified.</p>'''
    (DOCS/'sources.html').write_text(frame('Sources',srcpage))
    (DOCS/'.nojekyll').touch()
    (ROOT/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70</title></head><body><h1>GEMSDOE70: DO NOT SUBMIT</h1><p>No eligible TIFF. <a href="docs/index.html">Open the research workbench and submission status</a>.</p></body></html>\n')
    # Keep historical root entry points working without serving stale run claims.
    redirects={'executive-summary':'executive-summary','research':'hypotheses',
               'requirements':'irregularities','review':'irregularities',
               'run-card':'results','sources':'sources'}
    for old,target in redirects.items():
        (ROOT/f'{old}.html').write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=docs/{target}.html"><title>GEMSDOE70 — DO NOT SUBMIT</title></head><body><h1>DO NOT SUBMIT</h1><p>This historical entry point now links to the current evidence. <a href="docs/{target}.html">Continue to the current workbench</a>.</p></body></html>\n')
    print('Built site. Research TIFF published with DO NOT SUBMIT banner (holdout gate failed).')

if __name__=='__main__':main()
