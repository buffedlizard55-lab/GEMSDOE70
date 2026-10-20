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
<title>{html.escape(title)} · GEMSDOE70</title><meta name="description" content="Auditable geothermal fault research. Negative result; no competition-ready TIFF.">
<link rel="stylesheet" href="assets/site.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a><span class="edition">RESEARCH WORKBENCH / OCT 2026</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main><footer>Evidence before leaderboard claims. No competition upload performed.
<a href="run-card.json">Machine-readable run card</a> · <a href="sources.html">Provenance</a></footer></body></html>'''


def main():
    assert_no_public_rasters(ROOT)
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    hold=json.loads((ROOT/'evidence/holdout.json').read_text())
    canaries=json.loads((ROOT/'evidence/canaries.json').read_text())
    sources=json.loads((ROOT/'registry/sources.json').read_text())
    health=json.loads((ROOT/'evidence/source_health.json').read_text())
    gate=release_status(ROOT)
    DOCS.mkdir(exist_ok=True)
    downloads=DOCS/'downloads'; downloads.mkdir(exist_ok=True)
    for name in ['run_card.json','holdout.json','holdout_split.json','holdout_folds.json','canaries.json',
                 'surface_uniqueness.json','registry_saturation.json','h33_audit.json','data_receipt.json',
                 'template_verification.json','source_health.json','experiment_manifest.json']:
        shutil.copyfile(ROOT/'evidence'/name,downloads/name)
    shutil.copyfile(ROOT/'evidence/run_card.json',DOCS/'run-card.json')
    (DOCS/'status.json').write_text(json.dumps(gate,indent=2)+'\n')
    (DOCS/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    d=card['holdout_dti']; ci=d['ci95']
    evidence_label=f'HOLDOUT-DTI · {html.escape(d["evaluator_version"])} · {d["withheld_positive_pixels"]:,} withheld positive pixels'
    status='''<section class="stop" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS</div><h1 id="status">Do not submit this run.</h1>
<p>No eligible TIFF is available. The surface failed the literal uniqueness gate, so final dot placement and GeoTIFF export were stopped.</p>
<div class="actions"><button disabled aria-describedby="stop-note">Submission TIFF unavailable</button><a class="button secondary" href="run-card.json" download>Download run card (JSON)</a></div>
<p id="stop-note" class="small">This JSON is evidence, not a competition submission. No previous submission has been renamed or republished.</p></section>'''
    metrics=f'''<div class="metrics"><section><div class="eyebrow">CONTINUOUS SURFACE · HOLDOUT-DTI</div><div class="number">{d['dti']:.5f}</div><p>95% CI [{ci[0]:.5f}, {ci[1]:.5f}]</p></section>
<section><div class="eyebrow">REGISTRY MEASUREMENT</div><div class="number">100%</div><p>Forward overlap with a verified dense prior. Literal gate limit: 70%.</p></section>
<section><div class="eyebrow">COMPETITION ACTIVITY</div><div class="number">No upload</div><p>One fixed experiment. No weekly slot consumed.</p></section></div>'''
    overview=status+f'''<section class="intro"><div class="eyebrow">A NEGATIVE RESULT, FULLY ACCOUNTED FOR</div><h2>Test the geology. Protect the submission.</h2>
<p>We tested whether magnetic contact terminations along gravity-supported basement boundaries could reveal faults hidden beneath cover. The fixed ranking did not establish useful recovery and cannot pass the current literal overlap protocol.</p></section>{metrics}
<p class="caption">{evidence_label}. Confidence interval is a conditional spatial-block bootstrap, not a leaderboard interval. No final dots were evaluated.</p>
<div class="columns"><section class="panel"><h2>Why no download?</h2><p>A prior continuous raster is positive on the whole footprint. With the inherited positive-support definition of “dots,” every nonempty candidate overlaps it. We measured this conflict rather than waive it.</p><a href="results.html">See the stop certificate →</a></section>
<section class="panel"><h2>What about the H33 result?</h2><p>The archived field is an efficient sparse prediction followed by catalogue-flank pruning, not a new trained detector. Its reported historical score has no organizer receipt here.</p><a href="h33-analysis.html">Read the forensic analysis →</a></section></div>
<section><h2>Reproducible, not speculative</h2><p>The numerical stack was restored from pinned mirrors. The shared evaluator and writer remain byte-identical to the template. Every raw input and derived feature received a leakage canary.</p>
<ul><li><a href="hypotheses.html">Four preregistered geological hypotheses</a></li><li><a href="sources.html">Auditable sources and retrieval status</a></li><li><a href="irregularities.html">Limitations and next-session priorities</a></li></ul></section>'''
    (DOCS/'index.html').write_text(frame('Overview',overview))
    guide=status+'''<section><h2>How a future eligible submission works</h2><p><strong>Do not use this negative run.</strong> The workflow below applies only after a fresh candidate passes every scientific and publication gate. This static website reports precomputed evidence; it does not train a model in your browser.</p>
<ol class="steps"><li><strong>Check the readiness banner.</strong> Only a released artifact may receive a TIFF download link. A valid format alone does not mean it is unique or worth a competition slot.</li>
<li><strong>Verify scientific clearance.</strong> Feature canaries, same-split current-best improvement, a complete pre-placement surface audit and final-dot audit must pass. The present experiment fails and stops before the last step.</li>
<li><strong>Package with the shared writer.</strong> A single-band float32 GeoTIFF must match the sample CRS, shape and geotransform. The writer rejects non-finite/out-of-range values rather than silently clipping them; this project also sets outside-footprint values to zero.</li>
<li><strong>Validate exact file bytes.</strong> Reopen the TIFF, verify range, footprint and mapped-fault masking, and record its SHA-256. A ZIP must contain exactly one TIFF. Our shared writer checks that round trip.</li>
<li><strong>Obtain separate slot selection.</strong> Check the current submission page's rules and remaining weekly allowance; it is not known in this sandbox. Local candidate promotion does not authorize an upload.</li>
<li><strong>Upload only the released TIFF or one-TIFF ZIP.</strong> At the official competition site, open New submission, choose the file and copy its short identifying note. A JSON report, HTML page or PDF is not the prediction file.</li>
<li><strong>Keep the organizer receipt.</strong> Only an actual submission-page receipt can establish an ORGANIZER-CONFIRMED score. Save filename, hash, time, note and receipt together.</li></ol>
<h2>About “Predicted values must be in range [0, 1]”</h2><p>The earlier rejected file is not available for forensic inspection here, so its exact fault is unknown. Potential failures include raw unnormalized features, negative nodata sentinels, NaN/Inf or values above one. The shared writer rejects all these before publishing. We do not claim NaN was the cause of your portal error.</p>
<h2>Reference grid — mirror-relative measurement</h2><p>EPSG:32611; 3,730 rows × 3,292 columns; affine transform [100, 0, 243350, 0, -100, 4508550]. These match the SHA-pinned sample mirror, not an independently authenticated new organizer download.</p>
<h2>This run's reserved identity (not a released submission)</h2>'''+f'<p><code>{html.escape(card["submission_name"])}</code></p><p>Note ({len(card["submission_note"])} characters): <code>{html.escape(card["submission_note"])}</code></p>'+'''
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and format</a>. These pages could not be retrieved here; review current requirements before a future upload.</p></section>'''
    (DOCS/'executive-summary.html').write_text(frame('Submission guide',guide))
    rows=''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>HOLDOUT-DTI</td><td>{r["dti"]:.6f}</td><td>[{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}]</td></tr>' for n,r in hold['scores'].items())
    aucrows=''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>{r["auc"]:.6f}</td><td>{"STOP" if r["suspected_leakage"] else "No threshold alarm"}</td></tr>' for n,r in canaries.items())
    delta=hold['paired_differences']['random_control']
    results=f'''<div class="eyebrow">MEASURED RESULTS</div><h1>Evidence, including the failure.</h1><p>{evidence_label}. Continuous pre-placement surfaces only; not final dots.</p>
<div class="table-wrap"><table><caption>Same evaluator, same withheld positives and masks; pooled terms, then bootstrap.</caption><thead><tr><th>Arm</th><th>Evidence class</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Candidate-minus-random HOLDOUT-DTI difference: {delta['delta']:.6f}, 95% paired CI [{delta['ci95'][0]:.6f}, {delta['ci95'][1]:.6f}], with {d['withheld_positive_pixels']:,} withheld positives, evaluator {d['evaluator_version']}. The candidate is materially worse on this instrument. No comparable current-best implementation was available; none is claimed beaten.</p>
<p>The random control uses the same positive-cell count and fixed half-intensity, giving similar—not exactly equal—mass. It is a spatial spread diagnostic, not a tuned submission or proof that random prediction will score well on hidden labels.</p>
<h2>Leakage canaries</h2><p>LEAKAGE-CANARY AUC, not DTI or leaderboard scores. Each feature alone: {d['withheld_positive_pixels']:,} withheld positive pixels and 200,000 sampled negatives. We also checked the inverse ranking. Neither direction exceeded the 0.90 alarm threshold. This does not prove absence of every possible leakage mechanism.</p>
<div class="table-wrap"><table><thead><tr><th>Feature</th><th>AUC</th><th>Result</th></tr></thead><tbody>{aucrows}</tbody></table></div>
<h2>Uniqueness stop certificate</h2><p>REGISTRY-MEASUREMENT: exact surface Spearman correlation with the checked witness is {card['correlation_overlap_vs_registry']['spearman']:.6f}; forward three-pixel support overlap is 1.0. The literal threshold is exceeded.</p>
<p>The witness is positive on all 5,167,373 footprint cells. All 5,106,385 off-catalogue allowed cells are covered by its three-pixel halo; zero are uncovered. One verified counterexample suffices to reject uniqueness, while one comparison can never certify uniqueness. The inherited inventory is historical, not a fresh complete organizer registry.</p>
<p><a href="downloads/surface_uniqueness.json">Surface audit</a> · <a href="downloads/registry_saturation.json">Universal-blocker certificate</a> · <a href="downloads/holdout.json">Full holdout / paired intervals</a> · <a href="downloads/canaries.json">Canaries</a> · <a href="run-card.json">Run card</a></p>
<h2>Validator status: NOT WRITTEN</h2><p>The in-memory surface is finite, in range, correctly shaped, zero outside the footprint and zero on mapped faults. There is no TIFF validator receipt, file SHA-256, or final-dot audit because export and placement were stopped. Surface decoded-array SHA-256 is not a file hash.</p>'''
    (DOCS/'results.html').write_text(frame('Results',results))
    for name,title in [('hypotheses','Hypotheses'),('h33-analysis','H33 analysis'),('irregularities','Limitations')]:
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
    print('Built site. No eligible TIFF; no prediction files published.')

if __name__=='__main__':main()
