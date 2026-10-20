"""Deterministic, evidence-driven GitHub Pages site. Negative runs never publish TIFFs.

Every number on the site is read from evidence/*.json at build time. Evidence labels used:
HOLDOUT-DTI (evaluator version, withheld positives, 95% CI), LEAKAGE-CANARY (AUC),
REGISTRY-MEASUREMENT (complete scan of the indexed registry), LOCAL-FORMAT-VALIDATION
(shared validator; not organizer acceptance), ORGANIZER-CONFIRMED (no receipt exists here).
"""
from pathlib import Path
import html
import json
import shutil
import sys

import markdown

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems70.release import release_status, assert_no_public_rasters  # noqa: E402

DOCS = ROOT / 'docs'
EV = ROOT / 'evidence'
OFFICIAL = 'https://www.drivendata.org/competitions/306/competition-doe-gems/'
PROBLEM = OFFICIAL + 'page/967/'
RULES = 'https://www.nlr.gov/docs/fy26osti/96647.pdf'
DOWNLOAD_NAMES = [
    'run_card.json', 'holdout.json', 'holdout_split.json', 'holdout_folds.json', 'canaries.json',
    'surface_uniqueness.json', 'registry_saturation.json', 'h33_audit.json', 'data_receipt.json',
    'template_verification.json', 'source_health.json', 'experiment_manifest.json',
    'c1_holdout.json', 'c1_holdout_folds.json', 'c1_holdout_split.json', 'c1_canaries.json',
    'c1_result.json', 'c1_posthoc_binary_diagnostic.json', 'c1_export_receipt.json',
    'c1_final_validation.json', 'c1_registry_scan.json', 'official_sources_2026-10-20.json', 'c1_run_card.json']


def load(name):
    return json.loads((EV / name).read_text())


def esc(x):
    return html.escape(str(x))


def ci(pair):
    return f'[{pair[0]:.6f}, {pair[1]:.6f}]'


def frame(title, body):
    links = [('index.html', 'Overview'), ('executive-summary.html', 'Submission guide'),
             ('results.html', 'Results'), ('candidates-2026-10-20.html', 'Candidates'),
             ('hypotheses.html', 'Hypotheses'), ('h33-analysis.html', 'H33 analysis'),
             ('sources.html', 'Sources'), ('irregularities.html', 'Limitations')]
    nav = ''.join(f'<a href="{u}">{l}</a>' for u, l in links)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · GEMSDOE70</title><meta name="description" content="Auditable geothermal fault research. Current candidate: DO NOT SUBMIT (not cleared).">
<link rel="stylesheet" href="assets/site.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a><span class="edition">RESEARCH WORKBENCH · OCT 2026</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main>
<footer>DO NOT SUBMIT the generated candidate. No competition upload has been made. Evidence before leaderboard claims.
<a href="run-card.json">Machine-readable run card</a> · <a href="sources.html">Provenance</a></footer></body></html>'''


def main():
    assert_no_public_rasters(ROOT)
    card = load('run_card.json')
    e1 = load('holdout.json')
    e1_canary = load('canaries.json')
    c1 = load('c1_holdout.json')
    c1_result = load('c1_result.json')
    c1_canary = load('c1_canaries.json')
    diag = load('c1_posthoc_binary_diagnostic.json')
    receipt = load('c1_export_receipt.json')
    validation = load('c1_final_validation.json')
    scan = load('c1_registry_scan.json')
    ledger = load('official_sources_2026-10-20.json')
    health = load('source_health.json')
    sources = json.loads((ROOT / 'registry/sources.json').read_text())
    gate = release_status(ROOT)

    DOCS.mkdir(exist_ok=True)
    dl = DOCS / 'downloads'
    dl.mkdir(exist_ok=True)
    for name in DOWNLOAD_NAMES:
        shutil.copyfile(EV / name, dl / name)
    shutil.copyfile(EV / 'c1_run_card.json', DOCS / 'run-card.json')
    (DOCS / 'status.json').write_text(json.dumps(gate, indent=2) + '\n')
    (DOCS / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')

    file_name = Path(receipt['file']).name
    summ = scan['summary']
    dots = [r for r in scan['rows'] if r.get('duplicate_by_overlap') and r.get('representation') == 'dot_field']
    surf = [r for r in scan['rows'] if r.get('duplicate_by_overlap') and r.get('representation') == 'continuous_surface']
    by_repo = {}
    for r in dots:
        by_repo[r['repo']] = by_repo.get(r['repo'], 0) + 1
    top_repos = sorted(by_repo.items(), key=lambda kv: (-kv[1], kv[0]))
    top_text = ', '.join(f'{k} ({v})' for k, v in top_repos[:6])
    rnd = c1['scores']['random_control']
    cand = c1['scores']['candidate']
    noc = c1['scores']['ablation_no_catalogue']
    vs_rnd = c1_result['paired_difference_vs_random']
    vs_noc = c1_result['paired_difference_vs_no_catalogue']
    e1_cand = e1['scores']['candidate']
    e1_rnd = e1['scores']['random_control']
    canary_max_e2 = max(max(v['auc'], 1 - v['auc']) for v in c1_canary.values())
    canary_max_e1 = max(max(v['auc'], 1 - v['auc']) for v in e1_canary.values())
    n_pos = c1['scores']['candidate']['withheld_positive_pixels']
    n_pos_e1 = e1_cand['withheld_positive_pixels']
    check_guard = validation['sample_comparison']['ok'] is True and validation['sample_comparison']['nan_pixels'] == 0

    status = f'''<section class="stop" aria-labelledby="status"><div class="eyebrow">SUBMISSION READINESS · CURRENT CANDIDATE</div>
<h1 id="status">DO NOT SUBMIT. The generated GeoTIFF is not cleared.</h1>
<p>A format-valid file was generated: <code>{esc(file_name)}</code> (LOCAL-FORMAT-VALIDATION). It is <strong>not</strong> OK to download and submit. It fails two measured gates:</p>
<ul><li><strong>Holdout:</strong> HOLDOUT-DTI {cand['dti']:.5f} is below the random sparse control {rnd['dti']:.5f} (paired difference {vs_rnd['delta']:.5f}, 95% CI {ci(vs_rnd['ci95'])}).</li>
<li><strong>Registry:</strong> {len(dots)} sparse dot-field registry rasters exceed the literal 3 px overlap limit of 0.70 (REGISTRY-MEASUREMENT, complete scan of {summ['registry_rasters_checked']} rasters).</li></ul>
<p><strong>Do not submit this run.</strong> Submission TIFF unavailable on this site, because a gate failed.</p>
<div class="actions"><button disabled aria-describedby="stop-note">Download GeoTIFF: blocked, gates not passed</button>
<a class="button secondary" href="downloads/c1_run_card.json" download>Download run card</a>
<a class="button secondary" href="downloads/c1_export_receipt.json" download>Download export receipt (JSON)</a></div>
<p id="stop-note" class="small">The GeoTIFF stays in the git-ignored <code>submissions/</code> folder of the repository workspace, with its status in its file name. It is not published here: repository policy publishes no TIFF or ZIP while a gate fails. Nothing was copied from a previous submission.</p></section>'''

    metrics = f'''<div class="metrics">
<section><div class="eyebrow">C1 CANDIDATE · HOLDOUT-DTI</div><div class="number">{cand['dti']:.5f}</div><p>95% CI {ci(cand['ci95'])} · {n_pos:,} withheld positives · seed 71</p></section>
<section><div class="eyebrow">RANDOM SPARSE CONTROL · HOLDOUT-DTI</div><div class="number">{rnd['dti']:.5f}</div><p>95% CI {ci(rnd['ci95'])} · same withheld positives</p></section>
<section><div class="eyebrow">REGISTRY · LANE COLLISIONS</div><div class="number">{len(dots)}</div><p>sparse dot fields over the 3 px overlap limit, out of {summ['registry_rasters_checked']} indexed rasters (index dated 2026-10-12). Dense surfaces also flagged: {len(surf)}.</p></section></div>'''

    overview = status + f'''<section class="intro"><div class="eyebrow">ANSWER FIRST</div><h2>Can the generated TIF be downloaded and submitted?</h2>
<p><strong>No.</strong> The official steps and the file format are in the <a href="executive-summary.html">submission guide</a>. The guide also says what the verified file does for the “[0, 1]” error and what it does not establish.</p></section>
{metrics}
<p class="caption">HOLDOUT-DTI values are measured on withheld catalogue segments with holdout seed 71 and the shared evaluator <code>{esc(c1['evaluator_version'])}</code>. They are not leaderboard scores. This repository holds no ORGANIZER-CONFIRMED score.</p>
<div class="columns"><section class="panel"><h2>What we tested</h2><p>Candidate C1 (strike-coherent catalogue extrapolation), two ablations and a random control, on a pre-registered design with fresh holdout blocks. It passed the leakage canary. It did not beat the random control, and it did not beat the catalogue-free ablation.</p><a href="results.html">See the measured results →</a></section>
<section class="panel"><h2>What to do next</h2><p>Read the candidate ranking and the limitations. Any new candidate needs fresh, pre-registered holdout validation before a slot is considered.</p><a href="candidates-2026-10-20.html">Read the candidate ranking →</a></section></div>
<section><h2>Reproducible, not speculative</h2><p>Inputs are restored from pinned mirrors and checked by hash. The shared evaluator, the writer and the uniqueness tools are used unchanged (vendor/gems57 is pinned).</p>
<ul><li><a href="hypotheses.html">Preregistered hypotheses</a></li><li><a href="sources.html">Official and other sources, with retrieval status</a></li><li><a href="irregularities.html">Irregularities and limitations</a></li></ul></section>'''
    (DOCS / 'index.html').write_text(frame('Overview', overview))

    guide = status + f'''<div class="eyebrow">EXECUTIVE SUMMARY · HOW TO SUBMIT</div><h1>Making a submission to the GEMS Prize</h1>
<p>Each step cites the official page it comes from. Quotes were copied from pages fetched on 2026-10-20 and are listed in <a href="downloads/official_sources_2026-10-20.json">the source ledger</a>. Anything not checked is marked as such.</p>
<h2>1. The file you upload</h2>
<ol class="steps">
<li><strong>One GeoTIFF with one band, float32.</strong> The problem page requires “a single layer with datatype of 32-bit float (<code>float32</code>)” (<a href="{PROBLEM}">problem page</a>).</li>
<li><strong>Values between 0 and 1.</strong> “with values between 0 and 1 indicating the confidence or probability of fault presence” (<a href="{PROBLEM}">problem page</a>). Our file: minimum {receipt['min']:.1f}, maximum {receipt['max']:.5f}, {receipt['nan_count']} NaN values, {receipt['outside_footprint_positive']} positive values outside the footprint (LOCAL-FORMAT-VALIDATION).</li>
<li><strong>Projection and grid.</strong> EPSG 32611 (UTM zone 11N), 100 m, same bounds as the training data (3,730 rows × 3,292 columns). The validator reports that the transform matches the sample submission (<a href="downloads/c1_final_validation.json">validator output</a>).</li>
<li><strong>Outside the bounds.</strong> The problem page says “data outside the bounds is null or nan.” Our shared writer writes 0 outside the footprint, not NaN. Whether the portal accepts that is not verified. See the <a href="irregularities.html">limitations page</a>.</li>
</ol>
<h2>2. The “Predicted values must be in range [0, 1]” error</h2>
<p>This is the message you reported from the portal. We cannot see your earlier file, so we cannot say which value caused it. Our generated file has no value outside [0, 1] and no NaN, as shown above. Before uploading any file, check it for raw features (for example a nodata value such as −3.4028e38), unnormalized scores, and values above 1.</p>
<h2>3. Name and note</h2>
<p>Our file is named <code>{esc(receipt['name'])}</code> ({receipt['name_chars']} characters). A prepared note is {receipt['note_chars']} characters. The portal’s upload form and its length limits were not visible in this environment, so they are not verified.</p>
<h2>4. Rules that apply</h2>
<ul>
<li><strong>Weekly limit.</strong> “three submissions per week” (rules §3.2; §3.4 says “up to three per week, as specified on the competition website”). <a href="{RULES}">Rules PDF</a>.</li>
<li><strong>One final submission.</strong> “By the submission deadline, you must select only one set of predictions to use as your final submission” (rules §3.4). §3.5 adds that the choice is made “before the end of the competition”. The choice must be made without knowing private scores (§3.6.2).</li>
<li><strong>Deadline.</strong> The competition page gives “Dec. 3, 2026, 11:59 p.m. UTC”. Rules A.1 require posting “by 5:00 p.m. ET on the prize submission deadline date”. On Dec. 3 that is 22:00 UTC, which is earlier. <strong>Plan to the earlier cutoff.</strong> This is a discrepancy to confirm with the organizers.</li>
<li><strong>Generative AI.</strong> You “must indicate in the narrative” the extent of any generative-AI use (rules §3.2). The code and text in this repository were produced with AI-agent assistance. The disclosure must be written and checked by you before any submission.</li>
<li><strong>Eligibility.</strong> An individual must be “a U.S. citizen or permanent resident”; private entities must be “incorporated in and maintain a primary place of business in the United States” (rules §1.3). This is not checked here. Confirm it yourself.</li>
<li><strong>External data.</strong> Allowed only if you hold a license and the data “must be shareable with the challenge organizers” (<a href="{OFFICIAL}">competition page</a>).</li>
</ul>
<h2>5. The upload steps</h2>
<ol class="steps">
<li>Enroll on the <a href="{OFFICIAL}">competition page</a> with the “Compete!” button in the sidebar (step 1 of “How to compete”). The data tab requires a login (checked: redirect to login).</li>
<li>Click “Submit” in the sidebar, then “Make new submission” (step 6 of “How to compete”).</li>
<li>Choose one GeoTIFF file that passes section 1 and enter the note. Keep the portal receipt (score shown and time).</li>
<li>Choose your final submission before the deadline (section 4). Only the portal receipt can be called ORGANIZER-CONFIRMED.</li>
</ol>
<h2>6. Status of the generated file</h2>
<p><strong>DO NOT SUBMIT.</strong> Local file <code>{esc(file_name)}</code>, SHA-256 <code>{esc(receipt['sha256'])}</code>, {receipt['positive_pixels']:,} positive pixels, all cells checked for format. It is not cleared, for the two reasons above. A format-valid file is not an accepted submission.</p>
<p><a href="downloads/c1_export_receipt.json">Export receipt</a> · <a href="downloads/c1_final_validation.json">Validator output</a> · <a href="downloads/c1_registry_scan.json">Registry scan (all 862 rasters)</a> · <a href="downloads/c1_result.json">Holdout verdict</a></p>
<p class="small">Official sources: <a href="{PROBLEM}">problem and format</a> · <a href="{OFFICIAL}">competition</a> · <a href="{RULES}">rules PDF</a>. The leaderboard is rendered by script and was not readable here, so no leaderboard number is stated.</p></section>'''
    (DOCS / 'executive-summary.html').write_text(frame('Submission guide', guide))

    e1_rows = ''.join(
        f'<tr><th scope="row">{esc(n)}</th><td>HOLDOUT-DTI · {esc(e1["evaluator_version"])} · seed 20</td><td>{r["dti"]:.6f}</td><td>{ci(r["ci95"])}</td></tr>'
        for n, r in e1['scores'].items())
    e2_rows = ''.join(
        f'<tr><th scope="row">{esc(n)}</th><td>HOLDOUT-DTI · {esc(c1["evaluator_version"])} · seed 71</td><td>{r["dti"]:.6f}</td><td>{ci(r["ci95"])}</td></tr>'
        for n, r in c1['scores'].items())
    diag_rows = ''.join(
        f'<tr><th scope="row">{esc(n)}</th><td>POST-HOC · binary top 2% · not preregistered</td><td>{r["dti"]:.6f}</td><td>{ci(r["ci95"])}</td></tr>'
        for n, r in diag['scores'].items())
    c1_can = ''.join(
        f'<tr><th scope="row">{esc(n)}</th><td>{v["auc"]:.4f}</td><td>{"STOP: leakage" if v["suspected_leakage"] else "no alarm"}</td></tr>'
        for n, v in c1_canary.items())
    e1_can = ''.join(
        f'<tr><th scope="row">{esc(n)}</th><td>{v["auc"]:.4f}</td><td>{"STOP: leakage" if v["suspected_leakage"] else "no alarm"}</td></tr>'
        for n, v in e1_canary.items())
    results = f'''<div class="eyebrow">MEASURED RESULTS</div><h1>Evidence, including the failures.</h1>
<p>All holdout numbers are on continuous pre-placement surfaces, not final dots, and none is an organizer score.</p>
<h2>Experiment 2 · candidate C1 (pre-registered, holdout seed 71)</h2>
<div class="table-wrap"><table><caption>Same evaluator and withheld blocks for every arm. Pooled terms; paired spatial-cluster bootstrap (159 clusters, 1000 draws, bootstrap seed 71).</caption>
<thead><tr><th>Arm</th><th>Evidence class</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{e2_rows}</tbody></table></div>
<p>C1 minus random control: {vs_rnd['delta']:.5f}, paired 95% CI {ci(vs_rnd['ci95'])}. C1 minus catalogue-free ablation: {vs_noc['delta']:.5f}, paired 95% CI {ci(vs_noc['ci95'])}. Verdict: <strong>negative</strong>. C1 does not beat the random control or the catalogue-free ablation. The leakage canary passed; the largest canary AUC, direction-folded, is {canary_max_e2:.4f} against a 0.90 threshold.</p>
<h2>Post-hoc diagnostic (not preregistered, not a promotion basis)</h2>
<p>The main metric uses a linear upper-2% rescale of C1. To test whether that transform explains the gap, every arm was re-scored with binary top-2% output. The random control still wins under the binary transform, so under this diagnostic the rescaling alone does not explain the gap.</p>
<div class="table-wrap"><table><thead><tr><th>Arm</th><th>Evidence class</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{diag_rows}</tbody></table></div>
<h2>Experiment 1 · magnetic-edge termination (stopped; seed 20)</h2>
<p>Stopped by the registry duplicate gate before final placement (see <a href="downloads/run_card.json">run card</a>). Candidate HOLDOUT-DTI {e1_cand['dti']:.6f} (95% CI {ci(e1_cand['ci95'])}, {n_pos_e1:,} withheld positives); random control {e1_rnd['dti']:.6f}. Verdict: negative.</p>
<div class="table-wrap"><table><thead><tr><th>Arm</th><th>Evidence class</th><th>DTI</th><th>95% CI</th></tr></thead><tbody>{e1_rows}</tbody></table></div>
<h2>Leakage canaries (LEAKAGE-CANARY, AUC of the feature alone)</h2>
<div class="table-wrap"><table><caption>Experiment 2 (C1). Threshold for alarm: AUC above 0.90 in either direction.</caption><thead><tr><th>Feature</th><th>AUC</th><th>Result</th></tr></thead><tbody>{c1_can}</tbody></table></div>
<div class="table-wrap"><table><caption>Experiment 1 (magnetic-edge). Same threshold.</caption><thead><tr><th>Feature</th><th>AUC</th><th>Result</th></tr></thead><tbody>{e1_can}</tbody></table></div>
<h2>Complete registry scan of candidate C1 (REGISTRY-MEASUREMENT)</h2>
<p>Rasters checked: <strong>{summ['registry_rasters_checked']} of {summ['registry_rasters_expected']}</strong>; missing or invalid: {summ['missing_or_invalid']}. Highest rank correlation with any registry raster: {summ['worst_spearman_full_footprint']:.4f} (limit 0.90; none flagged). Highest forward 3 px dot overlap: {summ['worst_dot_overlap']:.4f} (limit 0.70). Flagged: <strong>{len(dots)} sparse dot fields</strong> and {len(surf)} continuous surfaces.</p>
<p>Sparse-field flags by repository: {esc(top_text)}. The JSON lists, for each registry raster, its file hash and both overlap directions.</p>
<p class="small">Caveat: the registry index was generated on 2026-10-12 from a repository scan. Rasters committed after that date are not covered. The literal overlap rule flags any dense raster, so it measures lane collision; it is not a quality test. Its effect on a candidate that is otherwise good is unmeasured.</p>
<p><a href="downloads/c1_registry_scan.json">Full per-raster table (JSON)</a> · <a href="downloads/surface_uniqueness.json">Experiment 1 surface audit</a> · <a href="downloads/registry_saturation.json">Experiment 1 saturation certificate</a></p>
<h2>Local format validation</h2>
<p>LOCAL-FORMAT-VALIDATION (shared validator, not organizer acceptance). Passed for the generated file; the validator output is in <a href="downloads/c1_final_validation.json">c1_final_validation.json</a>. This does not establish novelty or geological accuracy.</p>'''
    (DOCS / 'results.html').write_text(frame('Results', results))

    for name, title in [('hypotheses', 'Hypotheses'), ('h33-analysis', 'H33 analysis'),
                        ('irregularities', 'Limitations'), ('candidates-2026-10-20', 'Candidates')]:
        (DOCS / f'{name}.html').write_text(frame(title, markdown.markdown(
            (DOCS / f'{name}.md').read_text(), extensions=['tables', 'fenced_code'])))

    rows = ''.join(
        f'<tr><th scope="row"><a href="{esc(s["url"])}">{esc(s["id"])}</a></th><td>{esc(s["authority"])}</td>'
        f'<td>{esc(s["status"])}</td><td>{esc(s["claim"])}<br><small>Limit: {esc(s["limit"])}</small></td></tr>'
        for s in sources)
    up = sum(1 for c in health['checks'] if c.get('reachable'))
    srcpage = f'''<div class="eyebrow">PROVENANCE</div><h1>Sources, with what each one can and cannot show.</h1>
<p>A working HTTP page does not verify a scientific claim, a license or a competition result. Each row records the retrieval status and the limit of the claim.</p>
<p>HTTP reachability check at <time>{esc(health['generated_utc'])}</time>: {up} of {len(health['checks'])} endpoints reachable. The leaderboard is JavaScript-rendered and remains <strong>unverified</strong>.</p>
<div class="table-wrap"><table><thead><tr><th>Source</th><th>Authority</th><th>Status</th><th>Claim and limit</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Official-source ledger (2026-10-20)</h2>
<p>Exact quotes for the competition page, the problem page, the rules PDF and the HeroX rules mirror: <a href="downloads/official_sources_2026-10-20.json">official_sources_2026-10-20.json</a>. Known discrepancies are listed inside the ledger.</p>
<h2>Data and implementation receipts</h2>
<p><a href="downloads/data_receipt.json">Input checksums</a> · <a href="downloads/template_verification.json">Shared template verification</a> · <a href="downloads/source_health.json">HTTP health checks</a> · <a href="sources.json">Source ledger (JSON)</a></p>'''
    (DOCS / 'sources.html').write_text(frame('Sources', srcpage))
    (DOCS / '.nojekyll').touch()

    (ROOT / 'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70 · DO NOT SUBMIT</title></head>'
        '<body><h1>GEMSDOE70: DO NOT SUBMIT</h1><p>The generated GeoTIFF is not cleared. '
        '<a href="docs/index.html">Open the research workbench and submission guide</a>.</p></body></html>\n')
    redirects = {'executive-summary': 'executive-summary', 'research': 'hypotheses',
                 'requirements': 'irregularities', 'review': 'irregularities',
                 'run-card': 'results', 'sources': 'sources'}
    for old, target in redirects.items():
        (ROOT / f'{old}.html').write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="refresh" content="0;url=docs/{target}.html"><title>GEMSDOE70 · DO NOT SUBMIT</title></head>'
            f'<body><h1>DO NOT SUBMIT</h1><p>This older entry point now links to the current evidence. '
            f'<a href="docs/{target}.html">Continue to the current workbench</a>.</p></body></html>\n')
    assert check_guard, 'sample comparison failed'
    print('Built site. Candidate not cleared; no TIFF or ZIP published.')


if __name__ == '__main__':
    main()
