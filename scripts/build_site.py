"""Deterministic, evidence-driven GitHub Pages site; negative runs never offer TIFFs.

Covers three stopped experiments: exp1 (contact termination, literal-gate stop),
exp2 (VG lineaments, holdout-negative), exp3 (SGMC-proxy rescoring, negative).
"""
from pathlib import Path
import html
import json
import shutil
import sys
import markdown
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems70.release import release_status, assert_no_public_rasters, assert_root_pages_guard
DOCS = ROOT / 'docs'

NAV = [('index.html', 'Overview'), ('executive-summary.html', 'Submission guide'),
       ('results.html', 'Results'), ('hypotheses.html', 'Hypotheses'),
       ('hypotheses-round2.html', 'Round-2 hypotheses'), ('exp3-prereg.html', 'Exp-3 prereg'),
       ('h33-analysis.html', 'H33 analysis'), ('sources.html', 'Sources'),
       ('irregularities.html', 'Limitations')]


def md(path):
    return markdown.markdown(path.read_text(), extensions=['tables', 'fenced_code'])


def frame(title, body):
    nav = ''.join(f'<a href="{url}">{label}</a>' for url, label in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · GEMSDOE70</title><meta name="description" content="Auditable geothermal fault research. Negative result; no competition-ready TIFF.">
<link rel="stylesheet" href="assets/site.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a><span class="edition">RESEARCH WORKBENCH / OCT 2026</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main><footer>Evidence before leaderboard claims. No competition upload performed.
<a href="run-card.json">Machine-readable run card</a> · <a href="sources.html">Provenance</a></footer></body></html>'''


def main():
    assert_root_pages_guard(ROOT)
    assert_no_public_rasters(ROOT)
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    hold = json.loads((ROOT / 'evidence/holdout.json').read_text())
    canaries = json.loads((ROOT / 'evidence/canaries.json').read_text())
    card2 = json.loads((ROOT / 'evidence/exp2_run_card.json').read_text())
    card3 = json.loads((ROOT / 'evidence/exp3_run_card.json').read_text())
    hold2a = json.loads((ROOT / 'evidence/exp2_holdout_seed20.json').read_text())
    hold2b = json.loads((ROOT / 'evidence/exp2_holdout_seed71.json').read_text())
    hold3 = json.loads((ROOT / 'evidence/exp3_holdout.json').read_text())
    sources = json.loads((ROOT / 'registry/sources.json').read_text())
    health = json.loads((ROOT / 'evidence/source_health.json').read_text())
    gate = release_status(ROOT)
    DOCS.mkdir(exist_ok=True)
    downloads = DOCS / 'downloads'
    downloads.mkdir(exist_ok=True)
    for name in ['run_card.json', 'holdout.json', 'holdout_split.json', 'holdout_folds.json',
                 'canaries.json', 'surface_uniqueness.json', 'registry_saturation.json',
                 'h33_audit.json', 'data_receipt.json', 'template_verification.json',
                 'source_health.json', 'experiment_manifest.json',
                 'exp2_manifest.json', 'exp2_canaries_seed20.json',
                 'exp2_canaries_seed71.json', 'exp2_holdout_seed20.json',
                 'exp2_holdout_seed71.json', 'exp2_holdout_split.json',
                 'exp2_holdout_folds.json', 'exp2_uniqueness_subset.json',
                 'exp2_uniqueness_addendum.json', 'exp2_run_card.json',
                 'exp2_netcheck.json', 'exp3_manifest.json', 'exp3_holdout.json',
                 'exp3_run_card.json', 'exp3_rerun_note.json',
                 'session_card_exp2.json', 'session_card_exp3.json',
                 'concurrent_h70c_quarantine.json',
                 'upstream_revision_R1.md']:
        shutil.copyfile(ROOT / 'evidence' / name, downloads / name)
    shutil.copyfile(ROOT / 'evidence/run_card.json', DOCS / 'run-card.json')
    shutil.copyfile(ROOT / 'evidence/exp2_run_card.json', DOCS / 'exp2-run-card.json')
    shutil.copyfile(ROOT / 'evidence/exp3_run_card.json', DOCS / 'exp3-run-card.json')
    (DOCS / 'status.json').write_text(json.dumps(gate, indent=2) + '\n')
    (DOCS / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')
    session = {
        'evidence_class': 'SESSION-STATUS',
        'download_and_submit_ok': False,
        'runs': [
            {'experiment': 1, 'verdict': card['verdict'],
             'weekly_slots_used': card['weekly_slots_used']},
            {'experiment': 2, 'verdict': card2['verdict'],
             'weekly_slots_used': card2['weekly_slots_used']},
            {'experiment': 3, 'verdict': card3['verdict'],
             'weekly_slots_used': card3['weekly_slots_used']},
        ],
        'experiments_used': 3, 'experiments_max': 3,
        'statement': 'All three budgeted experiments are negative. No TIFF is '
                     'offered. Future work needs a fresh preregistered run.',
    }
    (DOCS / 'session-status.json').write_text(json.dumps(session, indent=2) + '\n')
    d = card['holdout_dti']
    ci = d['ci95']
    evidence_label = f'HOLDOUT-DTI · {html.escape(d["evaluator_version"])} · {d["withheld_positive_pixels"]:,} withheld positive pixels'
    status = '''<section class="stop" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS</div><h1 id="status">Do not submit this run.</h1>
<p>No eligible TIFF is available. All three budgeted experiments are negative, so no competition file is offered for download.</p>
<div class="actions"><button disabled aria-describedby="stop-note">Submission TIFF unavailable</button><a class="button secondary" href="run-card.json" download>Download run card (JSON)</a></div>
<p id="stop-note" class="small">This JSON is evidence, not a competition submission. No previous submission has been renamed or republished. Experiment budget 3/3 used.</p></section>'''
    c2a = hold2a['scores']['candidate']
    c2b = hold2b['scores']['candidate']
    c3 = hold3['scores']['candidate']
    metrics = f'''<div class="metrics"><section><div class="eyebrow">EXP 1 · SURFACE HOLDOUT-DTI</div><div class="number">{d['dti']:.5f}</div><p>95% CI [{ci[0]:.5f}, {ci[1]:.5f}] · negative (literal gate)</p></section>
<section><div class="eyebrow">EXP 2 · FINAL-DOT HOLDOUT-DTI</div><div class="number">{c2a['dti']:.5f}</div><p>seed 20; seed 71: {c2b['dti']:.5f} · negative (no signal)</p></section>
<section><div class="eyebrow">EXP 3 · SGMC-PROXY DTI</div><div class="number">{c3['dti']:.5f}</div><p>95% CI [{c3['ci95'][0]:.5f}, {c3['ci95'][1]:.5f}] · negative (no signal)</p></section></div>'''
    overview = status + f'''<section class="intro"><div class="eyebrow">THREE NEGATIVES, FULLY ACCOUNTED FOR</div><h2>Test the geology. Protect the submission.</h2>
<p>We tested contact termination (exp 1), shallow magnetic lineaments (exp 2), and rescored fixed dots on an independent fault map (exp 3). None established recoverable signal, so no file is offered.</p></section>{metrics}
<p class="caption">{evidence_label}. Intervals are conditional spatial-block bootstraps, not leaderboard intervals.</p>
<div class="columns"><section class="panel"><h2>Why no download?</h2><p>Exp 1 stopped at the literal uniqueness gate; exps 2–3 measured no ranking signal on two independent truth sets. We publish the negative evidence instead of a file.</p><a href="results.html">See the evidence →</a></section>
<section class="panel"><h2>What about the H33 result?</h2><p>The archived field is an efficient sparse prediction followed by catalogue-flank pruning. Our SGMC-proxy measurement independently confirms it recovers off-catalogue faults above chance. Its reported historical score has no organizer receipt here.</p><a href="h33-analysis.html">Read the forensic analysis →</a></section></div>
<section><h2>Reproducible, not speculative</h2><p>The numerical stack was restored from pinned mirrors. The shared evaluator and writer remain byte-identical to the template. Every raw input and derived feature received a leakage canary.</p>
<ul><li><a href="hypotheses.html">Four preregistered geological hypotheses (exp 1)</a></li><li><a href="hypotheses-round2.html">Five round-2 hypotheses (exp 2–3)</a></li><li><a href="sources.html">Auditable sources and retrieval status</a></li><li><a href="irregularities.html">Limitations and next-session priorities</a></li></ul></section>'''
    (DOCS / 'index.html').write_text(frame('Overview', overview))
    guide = status + '''<section><h2>How a future eligible submission works</h2><p><strong>Do not use these negative runs.</strong> The workflow below applies only after a fresh candidate passes every scientific and publication gate. This static website reports precomputed evidence; it does not train a model in your browser.</p>
<ol class="steps"><li><strong>Check the readiness banner.</strong> Only a released artifact may receive a TIFF download link. A valid format alone does not mean it is unique or worth a competition slot.</li>
<li><strong>Verify scientific clearance.</strong> Feature canaries, same-split current-best improvement, a complete pre-placement surface audit and final-dot audit must pass. The present experiments fail and stop before release.</li>
<li><strong>Package with the shared writer.</strong> A single-band float32 GeoTIFF must match the sample CRS, shape and geotransform. The writer rejects non-finite/out-of-range values rather than silently clipping them; this project also sets outside-footprint values to zero.</li>
<li><strong>Validate exact file bytes.</strong> Reopen the TIFF, verify range, footprint and mapped-fault masking, and record its SHA-256. A ZIP must contain exactly one TIFF. Our shared writer checks that round trip.</li>
<li><strong>Obtain separate slot selection.</strong> Check the current submission page's rules and remaining weekly allowance (published limit: three per week; remaining quota is not known in this sandbox). Local candidate promotion does not authorize an upload. Finalists must disclose generative-AI use in the narrative when applicable.</li>
<li><strong>Upload only the released TIFF or one-TIFF ZIP.</strong> At the official competition site, open New submission, choose the file and copy its short identifying note (≤140 characters). A JSON report, HTML page or PDF is not the prediction file.</li>
<li><strong>Keep the organizer receipt.</strong> Only an actual submission-page receipt can establish an ORGANIZER-CONFIRMED score. Save filename, hash, time, note and receipt together.</li></ol>
<h2>About “Predicted values must be in range [0, 1]”</h2><p>The earlier rejected file is not available for forensic inspection here, so its exact fault is unknown. Potential failures include raw unnormalized features, negative nodata sentinels, NaN/Inf or values above one. The shared writer rejects all these before publishing. Finite zeros outside the footprint are portal-safe; NaN inside the footprint would violate range. We do not claim NaN was the cause of your portal error.</p>
<h2>Reference grid — mirror-relative measurement</h2><p>EPSG:32611; 3,730 rows × 3,292 columns; affine transform [100, 0, 243350, 0, -100, 4508550]. These match the SHA-pinned sample mirror, not an independently authenticated new organizer download.</p>
<h2>These runs' reserved identities (not released submissions)</h2>''' + f'<p><code>{html.escape(card["submission_name"])}</code> · <code>{html.escape(card2.get("submission_name", "exp2-no-submission"))}</code> · exp3-no-submission</p>' + '''
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and format</a>. These pages could not be retrieved here; review current requirements before a future upload.</p></section>'''
    (DOCS / 'executive-summary.html').write_text(frame('Submission guide', guide))
    rows = ''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>HOLDOUT-DTI</td><td>{r["dti"]:.6f}</td><td>[{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}]</td></tr>' for n, r in hold['scores'].items())
    aucrows = ''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>{r["auc"]:.6f}</td><td>{"STOP" if r["suspected_leakage"] else "No threshold alarm"}</td></tr>' for n, r in canaries.items())
    delta = hold['paired_differences']['random_control']
    r2a = ''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>{r["dti"]:.6f}</td><td>[{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}]</td></tr>' for n, r in hold2a['scores'].items())
    r2b = ''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>{r["dti"]:.6f}</td><td>[{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}]</td></tr>' for n, r in hold2b['scores'].items())
    r3 = ''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>{r["dti"]:.6f}</td><td>[{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}]</td></tr>' for n, r in hold3['scores'].items())
    d3 = hold3['paired_differences']
    results = f'''<div class="eyebrow">MEASURED RESULTS</div><h1>Evidence, including the failures.</h1>
<h2>Experiment 1 — contact termination (negative, literal gate)</h2><p>{evidence_label}. Continuous pre-placement surfaces only; not final dots.</p>
<div class="table-wrap"><table><caption>Same evaluator, same withheld positives and masks; pooled terms, then bootstrap.</caption><thead><tr><th>Arm</th><th>Evidence class</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Candidate-minus-random HOLDOUT-DTI difference: {delta['delta']:.6f}, 95% paired CI [{delta['ci95'][0]:.6f}, {delta['ci95'][1]:.6f}]. The candidate is materially worse on this instrument.</p>
<h2>Leakage canaries (exp 1)</h2><div class="table-wrap"><table><thead><tr><th>Feature</th><th>AUC</th><th>Result</th></tr></thead><tbody>{aucrows}</tbody></table></div>
<h2>Experiment 2 — VG lineaments (negative, no holdout signal)</h2><p>Final-dot HOLDOUT-DTI, binary 38,000 dots, seeds 20 and 71. The candidate ties the mass-matched catalogue-avoiding random on both seeds and loses to the unpruned ablation, which can reach withheld faults. Canaries clean on both seeds (max AUC 0.533).</p>
<div class="table-wrap"><table><caption>Seed 20 · 11,321 withheld positives.</caption><thead><tr><th>Arm</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{r2a}</tbody></table></div>
<div class="table-wrap"><table><caption>Seed 71 · 11,425 withheld positives.</caption><thead><tr><th>Arm</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{r2b}</tbody></table></div>
<p>Uniqueness subset: max Spearman 0.011 vs 12 checked rasters; max sparse forward overlap 0.369 (17GEMSDOE-A), 0.214 vs H33 — no lane collision among checked. The dense 17GEMSDOE-E soft surface overlaps 1.0 by construction; it is rho-gated only under documented revision R1.</p>
<h2>Experiment 3 — SGMC distal rescoring (negative, no proxy signal)</h2><p>SGMC-proxy DTI on 62,122 off-catalogue SGMC fault pixels, organizer-style masking. H33/H27/D28 reproduce the live-ladder direction above both randoms; the candidate ties avoiding-random and trails H33 significantly (paired −0.0199, CI excludes 0).</p>
<div class="table-wrap"><table><caption>SGMC-distal truth · 62,122 pixels.</caption><thead><tr><th>Arm</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{r3}</tbody></table></div>
<p>Candidate-minus-H33: {d3['h33']['delta']:.6f} [{d3['h33']['ci95'][0]:.6f}, {d3['h33']['ci95'][1]:.6f}]. Candidate-minus-avoiding-random: {d3['random_avoiding']['delta']:.6f} [{d3['random_avoiding']['ci95'][0]:.6f}, {d3['random_avoiding']['ci95'][1]:.6f}].</p>
<p><a href="downloads/holdout.json">Exp-1 holdout</a> · <a href="downloads/exp2_holdout_seed20.json">Exp-2 seed 20</a> · <a href="downloads/exp2_holdout_seed71.json">Exp-2 seed 71</a> · <a href="downloads/exp3_holdout.json">Exp-3 SGMC proxy</a> · <a href="downloads/exp2_uniqueness_subset.json">Uniqueness subset</a> · <a href="run-card.json">Exp-1 card</a> · <a href="exp2-run-card.json">Exp-2 card</a> · <a href="exp3-run-card.json">Exp-3 card</a> · <a href="downloads/session_card_exp2.json">Protocol card exp-2</a> · <a href="downloads/session_card_exp3.json">Protocol card exp-3</a></p>
<h2>Validator status: NOT WRITTEN (all runs)</h2><p>No TIFF was exported by any run, so there is no file SHA-256 or validator receipt. In-memory arrays passed range/finiteness checks where recorded, which is not a submission receipt.</p>'''
    (DOCS / 'results.html').write_text(frame('Results', results))
    for name, title in [('hypotheses', 'Hypotheses'), ('hypotheses-round2', 'Round-2 hypotheses'),
                        ('exp3-prereg', 'Exp-3 prereg'), ('h33-analysis', 'H33 analysis'),
                        ('irregularities', 'Limitations')]:
        (DOCS / f'{name}.html').write_text(frame(title, md(DOCS / f'{name}.md')))
    sourcerows = ''.join(f'<tr><th scope="row"><a href="{html.escape(s["url"])}">{html.escape(s["id"])}</a></th><td>{html.escape(s["authority"])}</td><td>{html.escape(s["status"])}</td><td>{html.escape(s["claim"])}<br><small>{html.escape(s["limit"])}</small></td></tr>' for s in sources)
    srcpage = f'''<div class="eyebrow">AUDITABLE KNOWLEDGE</div><h1>Know what the evidence can say.</h1><p>GitHub reference content was retrieved. Official sites outside this environment's network allowlist were not verified live. A working HTTP endpoint does not verify a scientific claim, a license, or a competition result.</p>
<p>Availability last checked: <time>{html.escape(health['generated_utc'])}</time>. The current leaderboard is <strong>unverified</strong>, not an up-to-date claimed score feed.</p><div class="table-wrap"><table><thead><tr><th>Source</th><th>Authority</th><th>Session status</th><th>Claim and limit</th></tr></thead><tbody>{sourcerows}</tbody></table></div>
<h2>Data and implementation receipts</h2><p><a href="downloads/data_receipt.json">Input checksums</a> · <a href="downloads/template_verification.json">Unmodified shared template verification</a> · <a href="downloads/source_health.json">HTTP health checks</a> · <a href="sources.json">Source ledger</a> · <a href="session-status.json">Session status</a></p>
<h2>Research knowledge</h2><p>Potential-field edge changes are hypotheses about rock-property discontinuities, not verified fault slip. Magnetization changes, intrusive contacts, depositional boundaries and acquisition/leveling residuals are named alternatives. Gravity and basement depth may share inversion assumptions. TMI vertical-gradient lineaments were tested and falsified on two truth sets. No claim of new geothermal vents is made.</p>
<p>The complete original user brief and its historical result list are retained in the repository README and PROJECT_BRIEF.md. The analysis is deliberately scoped: it does not claim that every linked website, score or scientific source has been independently verified.</p>'''
    (DOCS / 'sources.html').write_text(frame('Sources', srcpage))
    (DOCS / '.nojekyll').touch()
    (ROOT / 'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70</title></head><body><h1>GEMSDOE70: DO NOT SUBMIT</h1><p>No eligible TIFF. <a href="docs/index.html">Open the research workbench and submission status</a>.</p></body></html>\n')
    redirects = {'executive-summary': 'executive-summary', 'research': 'hypotheses',
                 'requirements': 'irregularities', 'review': 'irregularities',
                 'run-card': 'results', 'sources': 'sources'}
    for old, target in redirects.items():
        (ROOT / f'{old}.html').write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=docs/{target}.html"><title>GEMSDOE70 — DO NOT SUBMIT</title></head><body><h1>DO NOT SUBMIT</h1><p>This historical entry point now links to the current evidence. <a href="docs/{target}.html">Continue to the current workbench</a>.</p></body></html>\n')
    print('Built site. No eligible TIFF; no prediction files published.')


if __name__ == '__main__':
    main()
