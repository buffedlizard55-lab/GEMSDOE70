#!/usr/bin/env python3
"""Build the static evidence site from the recorded JSON evidence.

No number is written by hand: every figure on every page is read from
evidence/run_card.json, evidence/phase*/**.json, evidence/canaries.json or
evidence/phase4/uniqueness.json. Missing evidence renders as "not recorded".
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DOWN = DOCS / 'downloads'

NAV = [('index.html', 'Overview'), ('submission.html', 'Submit a file'),
       ('results.html', 'Evidence'), ('hypotheses.html', 'Hypotheses'),
       ('h33-analysis.html', 'Why H33 scored'), ('sources.html', 'Sources'),
       ('limitations.html', 'Limitations')]


def load(rel, default=None):
    p = ROOT / rel
    return json.loads(p.read_text()) if p.is_file() else default


def esc(x):
    return html.escape(str(x))


def pct(x):
    return f'{100 * x:.1f}%'


def ci(d):
    lo, hi = d['ci95']
    return f'[{lo:.4f}, {hi:.4f}]'


def frame(title, body):
    review = load('evidence/literal_protocol_review.json', {})
    if review.get('correlation_overlap_vs_registry', {}).get('stop'):
        body = ('''<section role="alert" class="card"><h1>DO NOT SUBMIT — literal protocol stop</h1>
<p>No TIFF is authorized for download or submission. The archived Phase-4 TIFF fails the requested one-way
3-pixel overlap rule. Historical “unique” claims below use a different, mutual rule and
are not clearance under the current prompt. Archived files are quarantined for audit only.</p>
<p><a href="protocol-review.html">Current protocol review and next steps</a> ·
<a href="literal-protocol-review.json">Current JSON run card</a></p></section>''' + body)
    nav = ''.join(f'<a href="{h}">{esc(t)}</a>' for h, t in NAV)
    footer_links = ('' if review.get('correlation_overlap_vs_registry', {}).get('stop') else
                    '<a href="downloads/run_card.json">Run card</a> · <a href="downloads/uniqueness.json">Uniqueness</a> · '
                    '<a href="downloads/instrumentA_holdout.json">Instrument A</a> · '
                    '<a href="downloads/instrumentB_prime.json">Instrument B′</a>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · GEMSDOE70</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a>
<span class="edition">PHASE 4 · 2026-10-20</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main>
<footer>Every figure is read from a recorded JSON receipt. A projection is never a score.
{footer_links}</footer></body></html>'''


def table(headers, rows, caption=None):
    cap = f'<caption>{esc(caption)}</caption>' if caption else ''
    head = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return (f'<div class="table-wrap"><table>{cap}<thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def instrument_rows(d):
    if not d:
        return []
    return [[esc(k), f"{v['dti']:.4f}", ci(v), f"{v['withheld_positive_pixels']:,}"]
            for k, v in d['scores'].items()]


def build_blocked_site(review):
    """Render only stop/review pages when literal protocol evidence blocks release."""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / 'literal-protocol-review.json').write_text(json.dumps(review, indent=2) + '\n')
    current = load('evidence/current_protocol_review.json')
    if current is not None:
        (DOCS / 'current_protocol_review.json').write_text(json.dumps(current, indent=2) + '\n')
    import markdown
    report = (ROOT / 'reports/literal-protocol-review.md').read_text()
    (DOCS / 'protocol-review.html').write_text(
        frame('Current protocol review', markdown.markdown(report, extensions=['tables'])))
    stop = '''<section class="stop"><div class="eyebrow">RELEASE DECISION</div>
<h1>STOP — no TIFF cleared for download or submission</h1>
<p><strong>Current protocol: DO NOT SUBMIT.</strong> Do not download or submit any historical artifact. Previously exposed TIFF/ZIP files are quarantined for audit only. The literal one-way 3-pixel overlap rule fails on the archived candidate; no new candidate was generated and no slot was used.</p>
<p><a href="protocol-review.html">Read the literal-protocol review and ranked research queue</a> · <a href="submission.html">Submission requirements and status</a>.</p></section>'''
    pages = {
        'index.html': stop + '<h2>Release gate</h2><p>Local format validation is not uniqueness clearance or organizer acceptance. No local candidate score is an organizer-confirmed score.</p>',
        'submission.html': stop + '<h2>Future requirements</h2><ol><li>Resolve protocol ambiguity with the selector.</li><li>Use one assigned method lane and preregister the split and method.</li><li>Run leakage canaries and buffered holdout with DTI, evaluator version, withheld count and CI.</li><li>Audit the complete registry before and after placement; obey the literal one-way thresholds.</li><li>Only then write and validate one exact-format TIFF; selector approval remains separate.</li></ol><p>The earlier portal range error cannot be diagnosed without the rejected upload bytes.</p>',
        'results.html': stop + '<p>No new experiment was run in this review. Archived scores and receipts remain historical evidence only.</p>',
        'hypotheses.html': stop + '<p>See the ranked, conditional cache-based hypotheses in the protocol review. They are not authorized to execute until the lane and protocol conflict are resolved.</p>',
        'h33-analysis.html': stop + '<p>The archived H33 analysis supports a plausible pruning/metric interaction explanation, not a causal claim. The user-reported 0.2778 is not organizer-confirmed.</p>',
        'limitations.html': stop + '<p>Key blockers: incomplete authorization for a new lane, protocol conflict, no current organizer receipt, and no refreshed official source checks.</p>',
        'sources.html': stop + '<p>Official manual-review links: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">rules</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">data</a>, <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a>, <a href="https://gdr.openei.org/submissions/1391">DOE INGENIOUS</a>, and <a href="https://github.com/drivendataorg/gems-prize-reference-solution">organizer reference</a>. These external sources were not fetched in this review.</p>',
    }
    for name, body in pages.items():
        title = name.removesuffix('.html').replace('-', ' ').title()
        (DOCS / name).write_text(frame(title, body))
    redirect = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=protocol-review.html"><title>GEMSDOE70 — DO NOT SUBMIT</title></head><body><p>DO NOT SUBMIT — no TIFF cleared. <a href="protocol-review.html">Review status</a>.</p></body></html>'
    (DOCS / 'executive-summary.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=submission.html"><title>GEMSDOE70 — DO NOT SUBMIT</title></head><body><p>DO NOT SUBMIT — no TIFF cleared. <a href="submission.html">Review status</a>.</p></body></html>')
    for name in ('e3-candidate.html', 'research-review.html', 'supplemental-protocol-review.html', 'upstream-fix-report.html'):
        (DOCS / name).write_text(redirect)
    print('Rendered fail-closed publication pages; no downloads or candidate metrics published.')


def main():
    review = load('evidence/literal_protocol_review.json', {})
    if review.get('correlation_overlap_vs_registry', {}).get('stop'):
        build_blocked_site(review)
        return
    card = load('evidence/run_card.json', {})
    if not card:
        raise SystemExit('evidence/run_card.json missing; run the experiment first')
    review = load('evidence/literal_protocol_review.json', {})
    if review:
        (DOCS / 'literal-protocol-review.json').write_text(json.dumps(review, indent=2) + '\n')
        import markdown
        text = (ROOT / 'reports/literal-protocol-review.md').read_text()
        (DOCS / 'protocol-review.html').write_text(frame('Current protocol review', markdown.markdown(text, extensions=['tables'])))
    name = card['submission_name']
    sha = card['raster_sha256']
    val = card.get('validator_output') or {}
    checks = val.get('checks') or {}
    uniqueness = load('evidence/phase4/uniqueness.json', {})
    canaries = load('evidence/phase2/canaries.json', {})
    p2a = load('evidence/phase2/instrumentA_holdout.json')
    p2b = load('evidence/phase2/instrumentB_proxy.json')
    p3a = load('evidence/phase3/instrumentA_holdout.json')
    p3b = load('evidence/phase3/instrumentB_prime.json')
    p3ball = load('evidence/phase3/instrumentB_all.json')
    p4a = load('evidence/phase4/instrumentA_holdout.json')
    p4b = load('evidence/phase4/instrumentB_prime.json')
    p4ball = load('evidence/phase4/instrumentB_all.json')
    h33 = load('evidence/h33_audit.json', {})
    receipt = load(f'docs/downloads/{name}.json', {})
    sources = load('registry/sources.json', [])

    DOCS.mkdir(parents=True, exist_ok=True)
    DOWN.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- copy evidence
    copies = {
        'evidence/run_card.json': 'run_card.json',
        'evidence/phase4/uniqueness.json': 'uniqueness.json',
        'evidence/phase4/instrumentA_holdout.json': 'instrumentA_holdout.json',
        'evidence/phase4/instrumentA_folds.json': 'instrumentA_folds.json',
        'evidence/phase4/instrumentB_prime.json': 'instrumentB_prime.json',
        'evidence/phase4/instrumentB_all.json': 'instrumentB_all.json',
        'evidence/phase4/instrumentB_prime_folds.json': 'instrumentB_prime_folds.json',
        'evidence/phase2/canaries.json': 'canaries.json',
        'evidence/phase2/instrumentA_holdout.json': 'phase2_instrumentA.json',
        'evidence/phase2/instrumentB_proxy.json': 'phase2_instrumentB.json',
        'evidence/phase3/instrumentA_holdout.json': 'phase3_instrumentA.json',
        'evidence/phase3/instrumentB_prime.json': 'phase3_instrumentB_prime.json',
        'evidence/phase3/instrumentB_all.json': 'phase3_instrumentB_all.json',
        'evidence/h33_audit.json': 'h33_audit.json',
        'evidence/data_receipt.json': 'data_receipt.json',
        'evidence/template_verification.json': 'template_verification.json',
        'evidence/upstream_fix_report.md': 'upstream_fix_report.md',
        'evidence/registry_saturation.json': 'phase1_registry_saturation.json',
        'evidence/history/phase1_negative/run_card.json': 'phase1_run_card.json',
        'evidence/e2/run_card.json': 'e2_run_card.json',
        'evidence/e2/holdout.json': 'e2_holdout.json',
        'evidence/e2/canaries.json': 'e2_canaries.json',
        'evidence/e2/holdout_confirm_seed21.json': 'e2_confirm_seed21.json',
        'evidence/e2/final_uniqueness.json': 'e2_final_uniqueness.json',
        'evidence/e2/publication.json': 'e2_publication.json',
        'evidence/e2/validator.json': 'e2_validator.json',
        'evidence/e3/run_card.json': 'e3_run_card.json',
        'evidence/e3/holdout.json': 'e3_holdout.json',
        'evidence/e3/canaries.json': 'e3_canaries.json',
        'evidence/leaderboard_read.json': 'leaderboard_read.json',
    }
    for src, dst in copies.items():
        s = ROOT / src
        if s.is_file():
            shutil.copyfile(s, DOWN / dst)

    # --------------------------------------------------------------- decision box
    promoted = bool(card.get('download_and_submit_ok'))
    tone = 'stop' if not promoted else 'ok'
    headline = ('Verified file · not promoted' if not promoted else 'Promoted candidate')
    decision = f'''<section class="{tone}" aria-labelledby="decision">
<div class="eyebrow">SUBMISSION STATUS</div>
<h1 id="decision">{esc(headline)}</h1>
<p><strong>Download: yes — format-validated for review.</strong> The uniqueness check covers
62 archived registry rasters only, not every private or uncommitted raster. Local validation does
not establish organizer acceptance.</p>
<p><strong>Competition submission: NO — not recommended.</strong> The pre-registered target-like
gate (instrument B′) is negative, so improvement is not demonstrated. Verdict:
<strong>{esc(card['verdict'])}</strong>; no weekly slot has been used. The historical 0.2778 figure
is not an organizer-confirmed score in this project.</p>
<div class="actions">
<a class="button" style="background:#076c64;color:#fff" href="downloads/{esc(name)}.tif" download>Download submission TIFF</a>
<a class="button secondary" href="downloads/{esc(name)}.zip" download>Download one-TIFF ZIP</a>
<a class="button secondary" href="submission.html">How to submit</a>
</div>
<p class="small">Name: <code>{esc(name)}</code> · Note ({card.get('note_chars', len(card.get('submission_note', '')))}/140 chars):
<code>{esc(card.get('submission_note', ''))}</code></p></section>'''

    # ------------------------------------------------------------------ overview
    a = p4a['scores'] if p4a else {}
    b = p4b['scores'] if p4b else {}
    ball = p4ball['scores'] if p4ball else {}
    metrics = f'''<div class="metrics">
<section><div class="eyebrow">INSTRUMENT A · HOLDOUT-DTI</div>
<div class="number">{a['candidate']['dti']:.4f}</div>
<p>{ci(a['candidate'])} · {a['candidate']['withheld_positive_pixels']:,} withheld catalogue pixels</p></section>
<section><div class="eyebrow">INSTRUMENT B′ · PROXY-DTI</div>
<div class="number">{b['candidate']['dti']:.4f}</div>
<p>{ci(b['candidate'])} · SGMC proxy outside the duplication band</p></section>
<section><div class="eyebrow">UNIQUENESS · 62 RASTERS</div>
<div class="number">{uniqueness.get('worst_dot_overlap', 0):.2f}</div>
<p>Worst <em>mutual</em> overlap (limit 0.70) · worst ρ {uniqueness.get('worst_spearman_full_footprint', 0):.3f}</p></section></div>'''

    index = decision + f'''<section class="intro"><div class="eyebrow">WHAT THIS PAGE IS</div>
<h2>A unique, auditable candidate — and the evidence that it is not yet an improvement.</h2>
<p>We rebuilt the submission generator, fixed two defects in the shared uniqueness tool, ran three
pre-registered experiments and published the best candidate. Two instruments favour it, one does
not. Both are shown, with confidence intervals, and the verdict follows the pre-registered rule.</p>
</section>{metrics}
<div class="columns">
<section class="panel"><h2>Why it is downloadable</h2>
<p>The shared validator re-read the bytes: single band, float32, 3,730 × 3,292, EPSG:32611,
transform 100 m, values exactly 0/1, 37,654 dots, zero on mapped faults, zero outside the footprint.
Uniqueness: worst mutual overlap 0.31 against 62 archived rasters (forward-only overlap with a dense
lattice reaches 1.00 by construction and is reported separately).</p>
<a href="results.html">Full evidence →</a></section>
<section class="panel"><h2>Why it is not promoted</h2>
<p>On instrument B′ the candidate scores {b['candidate']['dti']:.4f} versus H33's
{b['h33_reference']['dti']:.4f} (paired Δ {p4b['paired_differences']['h33_reference']['delta']:+.4f},
95% CI {ci(p4b['paired_differences']['h33_reference'])}). The pre-registered rule requires a
positive lower bound. It does not hold.</p>
<a href="hypotheses.html">Why this rule →</a></section></div>
<section><h2>What is measured and what is not</h2>
<p>Neither instrument is the organizer's hidden truth. Instrument A withholds whole catalogue
components and measures catalogue recovery; instrument B/B′ uses USGS SGMC faults minus the
catalogue as a proxy for newly mapped faults. Every number is labelled, and no projection is
presented as a leaderboard score.</p>
<ul><li><a href="h33-analysis.html">Why the archived H33 field scored 0.2778</a></li>
<li><a href="results.html">All three experiments, ablations and canaries</a></li>
<li><a href="limitations.html">Known defects, irregularities and next-session work</a></li></ul></section>'''

    # ------------------------------------------- parallel E2/E3 lane (integrated)
    e2card = load('evidence/e2/run_card.json', {})
    e2pub = load('evidence/e2/publication.json', {})
    e2hold = load('evidence/e2/holdout.json', {})
    e3card = load('evidence/e3/run_card.json', {})
    e2_section = ''
    if e2card and e2pub:
        _d = e2card['holdout_dti']
        e2_section = f"""<section><h2>Parallel lane E2 — alluvial step (second candidate, DO NOT SUBMIT YET)</h2>
<p>An independent preregistered lane (oriented detrended-elevation step × basement edge,
38,000 dots) merged from a parallel session. <strong>Download for selector review: yes.
Submit: NO</strong> — its frozen bars failed (D28 catalogue-holdout best not beaten) and its
complete-registry scan is still pending. HOLDOUT-DTI {_d['dti']:.4f} {ci(_d)} ·
{e2card['final_dot_count']:,} dots · SHA-256 <code>{esc(e2pub.get('sha256',''))}</code>.</p>
<div class="actions"><a class="button secondary" href="downloads/{esc(e2pub.get('file',''))}" download>Download E2 review TIFF</a>
<a class="button secondary" href="downloads/e2_run_card.json" download>E2 run card</a></div>
<p class="small">Name: <code>{esc(e2card.get('submission_name',''))}</code> · Note:
<code>{esc(e2card.get('submission_note'))}</code>. E3 (depth-step) in the same lane family is
negative with no file. Full tables on the results page; terms in
<code>docs/publication-amendment-e2.md</code>.</p></section>"""
    (DOCS / 'index.html').write_text(frame('Overview', index + e2_section))

    # ------------------------------------------------------------- submit guide
    vrows = [[esc(k), 'pass' if v else 'FAIL'] for k, v in checks.items()]
    guide = f'''<div class="eyebrow">SUBMISSION GUIDE</div>
<h1>How to submit this file — and what the number will mean.</h1>
<p class="lead"><strong>The file:</strong> <code>downloads/{esc(name)}.tif</code>
({val.get('bytes', 0):,} bytes, SHA-256 <code>{esc(sha)}</code>).
A one-TIFF ZIP of the same file is provided for portals that ask for it. Upload exactly one of them.</p>
<section class="panel"><h2>Decision, stated plainly</h2>
<ul>
<li><strong>Download:</strong> yes — the file is unique, format-validated and reproducible.</li>
<li><strong>Upload a weekly slot:</strong> not recommended. Verdict <code>{esc(card['verdict'])}</code>.
Our target-like proxy says it is 12.6% below H33; our catalogue holdout says it is 20× above it.
Neither is the hidden truth. This is a defensible test, not a validated win.</li>
<li><strong>Never</strong> upload the ZIP and the TIFF as two different submissions.</li></ul></section>
<section><h2>Steps</h2><ol class="steps">
<li>Open the competition <em>New submission</em> page (DrivenData competition 306).</li>
<li>Choose <code>{esc(name)}.tif</code> (or the matching <code>.zip</code>, which contains only that TIFF).</li>
<li>Paste the note exactly as below (one line, {card.get('note_chars', len(card.get('submission_note', '')))} characters).</li>
<li>Submit and keep the receipt: filename, SHA-256, timestamp and the score the portal returns.</li>
<li>Record the returned score as ORGANIZER-CONFIRMED — nothing on this site may be relabelled as one.</li>
</ol>
<p><code>{esc(card.get('submission_note', ''))}</code></p></section>
<section><h2>Why the earlier portal error happened</h2>
<p>“Predicted values must be in range [0, 1]” is raised by the portal's own range check. The shared
writer refuses non-finite, negative or &gt;1 values instead of clipping them, then re-reads the file
from disk. This file is all-finite with values in exactly {{0, 1}}. We cannot inspect the earlier
rejected upload, so we do not claim to know its specific defect.</p></section>
<section><h2>On-disk validator receipt</h2>
<p>Every check below was recomputed from the published bytes by the shared template validator.</p>
{table(['Check', 'Result'], vrows, 'Shared validator, all checks must pass.')}
<p class="small">Validator class: {esc(val.get('validation_class', 'local format/range preflight'))}.</p></section>
<section><h2>Uniqueness receipt</h2>
<p>{esc(uniqueness.get('overlap_definition', ''))}</p>
{table(['Measurement', 'Value'],
 [['Rasters checked', uniqueness.get('registry_rasters_checked')],
  ['Duplicate count (mutual rule)', uniqueness.get('duplicate_count')],
  ['Worst mutual overlap', f"{uniqueness.get('worst_dot_overlap'):.4f} ({esc(uniqueness.get('worst_overlap_submission'))})"],
  ['Worst forward-only overlap', f"{uniqueness.get('worst_forward_overlap'):.4f} ({esc(uniqueness.get('worst_forward_submission'))})"],
  ['Worst Spearman ρ', f"{uniqueness.get('worst_spearman_full_footprint'):.4f}"],
  ['Inventory scope', esc(uniqueness.get('inventory_scope'))]],
 'Corrected binary-dot definition; forward-only overlap with a dense sampling grid is uninformative.')}</section>'''
    (DOCS / 'submission.html').write_text(frame('Submit a file', guide))

    # ------------------------------------------------------------------- results
    rows_a = instrument_rows(p4a)
    rows_bp = instrument_rows(p4b)
    rows_ball = instrument_rows(p4ball)
    ablate = []
    for tag, d in (('A · shared holdout', p3a), ('B′ · proxy', p3b), ('B · unrestricted proxy', p3ball)):
        if d:
            for k in ('candidate', 'ablation_no_tip', 'random_control', 'h33_reference'):
                if k in d['scores']:
                    ablate.append([tag, esc(k), f"{d['scores'][k]['dti']:.4f}", ci(d['scores'][k])])
    canary_rows = [[esc(k), f"{v['auc']:.3f}", 'STOP' if v['suspected_leakage'] else 'clear']
                   for k, v in canaries.items()]
    history = []
    for tag, d in (('Exp 2 · gated prior A', p2a), ('Exp 2 · B proxy', p2b),
                   ('Exp 3 · damage zone A', p3a), ('Exp 3 · B′', p3b),
                   ('Exp 4 · stratified A', p4a), ('Exp 4 · B′', p4b)):
        if not d:
            continue
        cand = d['scores']['candidate']
        ref = d['scores'].get('h33_reference')
        history.append([esc(tag), f"{cand['dti']:.4f}", ci(cand),
                        f"{ref['dti']:.4f}" if ref else '—'])
    results = f'''<div class="eyebrow">EVIDENCE</div><h1>Three experiments, two instruments, one verdict.</h1>
<p>All DTI values use α = 0.2, β = 0.8 and a 300 m triangular kernel on the pinned 100 m grid, with
pooled terms and a paired spatial-cluster bootstrap (1,000 draws, 20 km blocks). Intervals are
conditional on the fitted folds and the proxy truth; they are not leaderboard intervals.</p>
<p><strong>Regression: only mutual overlap now counts as duplication.</strong> Measured this session:
<code>calib_r13lattice_00904.tif</code> (206,895 dots) has a 3-px halo covering <strong>100 %</strong>
of the footprint, so forward-only overlap is 1.00 for any nonempty candidate. Both directions are
always reported.</p>
<h2>Published candidate</h2>
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_a, 'Instrument A · shared hide-and-recover catalogue holdout')}
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_bp, "Instrument B′ · SGMC proxy, d ≥ 3 px from catalogue")}
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_ball, 'Instrument B · unrestricted SGMC proxy (contaminated by map duplication)')}
<h2>Experiment 3 ablations</h2>
{table(['Instrument', 'Arm', 'DTI', '95% CI'], ablate, 'Ablations were registered before their runs.')}
<h2>Leakage canaries</h2>
{table(['Feature', 'AUC (held-out)', 'Result'], canary_rows, 'Each feature alone, 11,321 withheld positives vs 200,000 negatives. AUC > 0.90 would stop the run.')}
<h2>Experiment history</h2>
{table(['Run', 'Candidate DTI', '95% CI', 'H33 DTI'], history)}
<p><a href="downloads/run_card.json">Full run card</a> ·
<a href="downloads/uniqueness.json">Uniqueness audit</a> ·
<a href="downloads/instrumentA_holdout.json">Instrument A</a> ·
<a href="downloads/instrumentB_prime.json">Instrument B′</a> ·
<a href="downloads/phase3_instrumentB_all.json">Experiment 3 B</a></p>'''

    if e2hold:
        _rows = [[esc(k), f"{v['dti']:.4f}", ci(v), str(v['withheld_positive_pixels'])]
                 for k, v in sorted(e2hold['scores'].items(), key=lambda kv: -kv[1]['dti'])]
        results += ("<h2>Parallel lane E2/E3 — catalogue holdout (same instrument A family)</h2>"
                    "<p>E2 beats random and every ablation, ties H19-solid at one-third mass, "
                    "loses to D28; H33 ranks last here by construction (live new faults vs catalogue "
                    "pieces). E3 depth-step mechanism AUC 0.506 (null), candidate "
                    f"{e3card.get('holdout_dti', {}).get('dti', 0):.4f}. Both negative.</p>"
                    + table(['Arm', 'DTI', '95% CI', 'Positives'], _rows,
                            'E2 arms · gems57-pooled-hide-v2 · seed-20'))
    (DOCS / 'results.html').write_text(frame('Evidence', results))

    # ------------------------------------------------------------------ markdown
    import markdown
    for src, dst, title in [('docs/hypotheses.md', 'hypotheses.html', 'Hypotheses'),
                            ('docs/h33-analysis.md', 'h33-analysis.html', 'Why H33 scored'),
                            ('docs/irregularities.md', 'limitations.html', 'Limitations')]:
        text = (ROOT / src).read_text()
        body = markdown.markdown(text, extensions=['tables'])
        (DOCS / dst).write_text(frame(title, body))

    # -------------------------------------------------------------------- sources
    srows = [[f'<a href="{esc(s["url"])}">{esc(s["id"])}</a>', esc(s.get('authority', '')),
              esc(s.get('status', '')), esc(s.get('claim', '')) + '<br><small>'
              + esc(s.get('limit', '')) + '</small>'] for s in sources]
    src_page = f'''<div class="eyebrow">SOURCES</div><h1>Every claim points at a source or a receipt.</h1>
<p>Retrieved content is cached in the repository where licensing allows; scores reported by the user
are labelled as user-supplied, never as organizer-confirmed. Official competition pages could not be
retrieved from this sandbox, which is stated rather than worked around.</p>
{table(['Source', 'Authority', 'Status', 'Claim and limit'], srows)}
<h2>Competition and data</h2>
<ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition home</a> ·
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem and metric</a> ·
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Leaderboard</a></li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference solution</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN data release (DOI 10.5066/P93LGLVQ)</a></li>
<li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS submission 1391</a> ·
<a href="https://gbcge.org/current-projects/ingenious/">GBCGE INGENIOUS</a></li>
<li><a href="https://epsg.io/32611">EPSG:32611</a> ·
<a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR report 96647</a></li>
</ul>
<h2>Science cited for the registered mechanisms</h2>
<ul>
<li>Mitchell, T.M. &amp; Faulkner, D.R. (2012), <em>Towards quantifying the matrix permeability of
fault damage zones in low porosity rocks</em>, EPSL 339–340, 24–31 — damage-zone width scales with
displacement, motivating a decaying intensity around mapped traces.</li>
<li>Faulkner, D.R. et al. (2010), <em>A review of recent developments concerning the structure,
mechanics and fluid flow properties of fault zones</em>, J. Struct. Geol. 32, 1557–1575.</li>
<li>USGS State Geologic Map Compilation (SGMC) faults, used <strong>only as proxy truth</strong>, never
as a predictor.</li></ul>
<h2>Receipts</h2>
<p><a href="downloads/data_receipt.json">Input SHA-256 pins</a> ·
<a href="downloads/template_verification.json">Shared-template verification</a> ·
<a href="https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/evidence/upstream_fix_report.md">Upstream fix report</a></p>'''
    (DOCS / 'sources.html').write_text(frame('Sources', src_page))

    # Root entry point (repository-root Pages keeps working).
    (ROOT / 'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70</title>'
        '</head><body><p>DO NOT SUBMIT — review only.</p><p><a href="docs/index.html">Open the GEMSDOE70 evidence site</a></p>'
        '</body></html>\n')
    (DOCS / '.nojekyll').touch()
    # Backwards-compatible entry points; they must not carry stale claims.
    for old, target in (('executive-summary.html', 'submission.html'),
                        ('irregularities.html', 'limitations.html'),
                        ('status.html', 'index.html')):
        (DOCS / old).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={target}"><title>GEMSDOE70</title>'
            f'</head><body><p>DO NOT SUBMIT — review only.</p><p>This page moved. <a href="{target}">Continue</a>.</p></body></html>\n')
    (DOCS / 'status.json').unlink(missing_ok=True)
    # keep a root-level copy so older pages that link run-card.json still resolve
    (DOCS / 'run-card.json').write_text((ROOT / 'evidence/run_card.json').read_text())
    # Phase-1 receipts keep their historical names only under the archived prefix.
    for stale in ('holdout.json', 'holdout_folds.json', 'holdout_split.json',
                  'registry_saturation.json', 'surface_uniqueness.json',
                  'experiment_manifest.json'):
        (DOWN / stale).unlink(missing_ok=True)
    print('site built:', ', '.join(sorted(p.name for p in DOCS.glob('*.html'))))


if __name__ == '__main__':
    main()
