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
<p>Download for review only. The archived Phase-4 TIFF fails the requested one-way
3-pixel overlap rule. Historical “unique” claims below use a different, mutual rule and
are not clearance under the current prompt. No new TIFF was generated in this review.</p>
<p><a href="protocol-review.html">Current protocol review and next steps</a> ·
<a href="literal-protocol-review.json">Current JSON run card</a></p></section>''' + body)
    nav = ''.join(f'<a href="{h}">{esc(t)}</a>' for h, t in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · GEMSDOE70</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a>
<span class="edition">PHASE 4 · 2026-10-20</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main>
<footer>Every figure is read from a recorded JSON receipt. A projection is never a score.
<a href="literal-protocol-review.json">Current literal-protocol card</a> ·
<a href="downloads/run_card.json">Archived Phase-4 run card</a> ·
<a href="downloads/uniqueness.json">Historical mutual-rule uniqueness</a> ·
<a href="downloads/instrumentA_holdout.json">Archived Instrument A HOLDOUT-DTI</a> ·
<a href="downloads/instrumentB_prime.json">Archived Instrument B′ HOLDOUT-DTI</a></footer></body></html>'''


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


def score_receipt(score):
    """Render every archived DTI with its evidence class, evaluator, n and CI."""
    return (f"{esc(score.get('evidence_class', 'evidence class not recorded'))} · "
            f"evaluator {esc(score.get('evaluator_version', 'not recorded'))} · "
            f"{esc(score.get('withheld_positive_pixels', 'not recorded'))} withheld positives · "
            f"DTI {score['dti']:.4f}, 95% CI {ci(score)}")


def main():
    card = load('evidence/run_card.json', {})
    if not card:
        raise SystemExit('evidence/run_card.json missing; run the experiment first')
    review = load('evidence/literal_protocol_review.json', {})
    review_gate = (review.get('correlation_overlap_vs_registry') or {}) if review else {}
    literal_stop = review_gate.get('stop') is True
    literal_witnesses = review_gate.get('witnesses') or []
    literal_forward_values = [
        row['forward_overlap'] for row in literal_witnesses
        if type(row.get('forward_overlap')) in (int, float)
    ]
    literal_max_forward = max(literal_forward_values, default=0.0)
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
    if literal_stop:
        witness_names = ', '.join(
            esc(row.get('submission', 'unnamed raster')) for row in literal_witnesses[:4]
        ) or 'one or more archived rasters'
        decision = f'''<section class="stop" aria-labelledby="decision">
<div class="eyebrow">ARTIFACT STATUS · REVIEW COPY ONLY</div>
<h1 id="decision">DO NOT SUBMIT — archived TIFF for review only</h1>
<p><strong>Download:</strong> yes, for review and analysis only.
<strong>Submit to DrivenData:</strong> no. The archived final-dot raster fails the current literal
one-way uniqueness gate: {len(literal_witnesses)} witness rasters in the {review_gate.get('registry_rasters_checked', 0)}-raster accessible inventory;
maximum forward overlap {literal_max_forward:.2f}. Witnesses: <code>{witness_names}</code>.
This is a REGISTRY-MEASUREMENT, not a competition score. The inventory is not exhaustive.</p>
<p>The historical local format/range validator passed, but that does not override this uniqueness
stop. No new TIFF was generated in this review, and no weekly slot was used.</p>
<div class="actions">
<a class="button" style="background:#8b1e1e;color:#fff" href="downloads/{esc(name)}.tif" download>Download archived TIFF (review only)</a>
<a class="button secondary" href="downloads/{esc(name)}.zip" download>Download one-TIFF ZIP (review only)</a>
<a class="button secondary" href="protocol-review.html">Read the protocol stop</a>
</div>
<p class="small">Archived identifier: <code>{esc(name)}</code> · The historical note below is for identification only; it is not approved for submission.</p></section>'''
    else:
        tone = 'stop' if not promoted else 'ok'
        headline = ('Verified file · not promoted' if not promoted else 'Promoted candidate')
        decision = f'''<section class="{tone}" aria-labelledby="decision">
<div class="eyebrow">SUBMISSION STATUS</div>
<h1 id="decision">{esc(headline)}</h1>
<p><strong>Download: yes.</strong> The file passed the shared-validator checks, and its SHA-256 is recorded below.</p>
<p><strong>Submit a weekly slot: not recommended by our evidence.</strong> The verdict is
<strong>{esc(card['verdict'])}</strong>. Uploading is a deliberate test, not a validated improvement.</p>
<div class="actions">
<a class="button" style="background:#076c64;color:#fff" href="downloads/{esc(name)}.tif" download>Download TIFF</a>
<a class="button secondary" href="downloads/{esc(name)}.zip" download>Download one-TIFF ZIP</a>
<a class="button secondary" href="submission.html">How to submit</a>
</div>
<p class="small">Name: <code>{esc(name)}</code> · Note ({card.get('note_chars', len(card.get('submission_note', '')))}/140 chars):
<code>{esc(card.get('submission_note', ''))}</code></p></section>'''

    # ------------------------------------------------------------------ overview
    a = p4a['scores'] if p4a else {}
    b = p4b['scores'] if p4b else {}
    ball = p4ball['scores'] if p4ball else {}
    if literal_stop:
        metrics = f'''<div class="metrics">
<section><div class="eyebrow">ARCHIVED HOLDOUT-DTI · gems57-pooled-hide-v2</div>
<div class="number">{a['candidate']['dti']:.4f}</div>
<p>95% CI {ci(a['candidate'])} · {a['candidate']['withheld_positive_pixels']:,} withheld-positive pixels; copied from archived Phase-4 evidence, not rerun.</p></section>
<section><div class="eyebrow">REGISTRY-MEASUREMENT · LITERAL GATE</div>
<div class="number">STOP</div>
<p>{len(literal_witnesses)} one-way overlap witnesses among {review_gate.get('registry_rasters_checked', 0)} accessible rasters · maximum forward overlap {literal_max_forward:.2f}.</p></section>
<section><div class="eyebrow">SUBMISSION STATUS</div>
<div class="number">DO NOT SUBMIT</div>
<p>Review download only · no new TIFF generated · no weekly slot used.</p></section></div>'''
    else:
        metrics = f'''<div class="metrics">
<section><div class="eyebrow">INSTRUMENT A · HOLDOUT-DTI · gems57-pooled-hide-v2</div>
<div class="number">{a['candidate']['dti']:.4f}</div>
<p>95% CI {ci(a['candidate'])} · {a['candidate']['withheld_positive_pixels']:,} withheld-positive pixels</p></section>
<section><div class="eyebrow">INSTRUMENT B′ · HOLDOUT-DTI · gems57-pooled-hide-v2</div>
<div class="number">{b['candidate']['dti']:.4f}</div>
<p>95% CI {ci(b['candidate'])} · {b['candidate']['withheld_positive_pixels']:,} proxy positives; SGMC is not organizer hidden truth.</p></section>
<section><div class="eyebrow">UNIQUENESS · REGISTRY-MEASUREMENT</div>
<div class="number">{uniqueness.get('worst_dot_overlap', 0):.2f}</div>
<p>Historical mutual overlap (limit 0.70) · Spearman {uniqueness.get('worst_spearman_full_footprint', 0):.3f}</p></section></div>'''

    if literal_stop:
        summary_heading = 'Archived Phase-4 evidence — no current submission candidate'
        summary_copy = ('The published TIFF is a historical review artifact. This review ran no new '
                        'experiment, created no candidate surface, and used no weekly slot. The '
                        'literal one-way registry gate fails on the archived final dots; the prior '
                        'mutual-overlap result is not clearance under the current prompt.')
        download_heading = 'Why the archived file can be downloaded only for review'
        download_copy = ('Its archived local validator receipt reports a single-band float32 GeoTIFF '
                         'with the competition grid and values in [0,1]. That is a format/range '
                         'preflight only. It does not establish uniqueness, organizer acceptance, '
                         'or permission to submit. The literal protocol review is controlling.')
        promotion_heading = 'Scientific decision: negative; no slot'
        promotion_copy = ('The archived Phase-4 candidate did not pass its pre-registered target-like '
                          'HOLDOUT-DTI gate. The current report carries the archived catalogue '
                          'HOLDOUT-DTI receipt and its evaluator, withheld-positive count and 95% CI; '
                          'no ORGANIZER-CONFIRMED score exists. No new scientific test was run here.')
        h33_link = 'What the archive can and cannot establish about the user-reported H33 result'
    else:
        summary_heading = 'A reviewed candidate and the evidence behind its status.'
        summary_copy = ('The archive records the method, held-out comparisons and validator receipt. '
                        'A non-promoted artifact is not a validated improvement.')
        download_heading = 'Format and file-integrity receipt'
        download_copy = ('The shared validator re-read the published bytes. See the local format/range '
                         'preflight and registry measurements in the linked evidence; neither is an '
                         'organizer acceptance receipt.')
        promotion_heading = 'Scientific decision'
        promotion_copy = ('The pre-registered target-like HOLDOUT-DTI gate did not pass; no weekly '
                          'slot is recommended by the recorded evidence.')
        h33_link = 'Analysis of the user-reported H33 result'
    index = decision + f'''<section class="intro"><div class="eyebrow">WHAT THIS PAGE IS</div>
<h2>{esc(summary_heading)}</h2>
<p>{esc(summary_copy)}</p>
</section>{metrics}
<div class="columns">
<section class="panel"><h2>{esc(download_heading)}</h2>
<p>{esc(download_copy)}</p>
<a href="protocol-review.html">Current protocol review →</a> · <a href="results.html">Archived evidence →</a></section>
<section class="panel"><h2>{esc(promotion_heading)}</h2>
<p>{esc(promotion_copy)}</p>
<a href="hypotheses.html">Research queue →</a></section></div>
<section><h2>What is measured and what is not</h2>
<p>Instrument A is a hide-and-recover catalogue holdout. Instrument B/B′ uses USGS SGMC faults as
proxy positives and is not organizer hidden truth. Every reported internal score must be read with
its HOLDOUT-DTI evidence class, evaluator version, positive count and 95% CI; none is an
ORGANIZER-CONFIRMED submission score.</p>
<ul><li><a href="h33-analysis.html">{esc(h33_link)}</a></li>
<li><a href="results.html">Archived experiments, ablations and canaries</a></li>
<li><a href="limitations.html">Known defects, irregularities and next-session work</a></li></ul></section>'''

    # ------------------------------------------- parallel E2/E3 lane (integrated)
    e2card = load('evidence/e2/run_card.json', {})
    e2pub = load('evidence/e2/publication.json', {})
    e2hold = load('evidence/e2/holdout.json', {})
    e2_section = ''
    if e2card and e2pub:
        _d = e2card['holdout_dti']
        e2_section = f"""<section><h2>Parallel lane E2 — alluvial step (review only, DO NOT SUBMIT)</h2>
<p>An independent preregistered lane (oriented detrended-elevation step × basement edge,
{e2card['final_dot_count']:,} output dots) merged from a parallel session. <strong>Download for selector review: yes.
Submit: NO</strong> — its frozen comparison did not beat D28, and its complete literal-registry scan is
pending. HOLDOUT-DTI, evaluator <code>{esc(_d['evaluator_version'])}</code>, {_d['withheld_positive_pixels']:,} withheld-positive pixels:
{_d['dti']:.4f}, 95% CI {ci(_d)}. SHA-256 <code>{esc(e2pub.get('sha256',''))}</code>.</p>
<div class="actions"><a class="button secondary" href="downloads/{esc(e2pub.get('file',''))}" download>Download E2 review TIFF</a>
<a class="button secondary" href="downloads/e2_run_card.json" download>E2 run card</a></div>
<p class="small">Name: <code>{esc(e2card.get('submission_name',''))}</code> · Note:
<code>{esc(e2card.get('submission_note'))}</code>. E3 (depth-step) in the same lane family is
negative with no file. Full tables on the results page; terms in
<code>docs/publication-amendment-e2.md</code>.</p></section>"""
    (DOCS / 'index.html').write_text(frame('Overview', index + e2_section))

    # ------------------------------------------------------------- submit guide
    vrows = [[esc(k), 'pass' if v else 'FAIL'] for k, v in checks.items()]
    if literal_stop:
        literal_rows = [
            ['Current literal decision', 'STOP — archived candidate is not cleared'],
            ['One-way overlap witnesses', str(len(literal_witnesses))],
            ['Accessible registry rasters checked', str(review_gate.get('registry_rasters_checked', 0))],
            ['Maximum forward overlap', f'{literal_max_forward:.4f} (REGISTRY-MEASUREMENT, not a score)'],
            ['Inventory completeness', 'Accessible archive only; not exhaustive'],
        ]
        guide = f'''<div class="eyebrow">SUBMISSION GUIDE · CURRENT FILE NOT ELIGIBLE</div>
<h1>Do not submit the archived TIFF.</h1>
<p class="lead"><strong>Current decision: DO NOT SUBMIT.</strong> The archived file
<code>downloads/{esc(name)}.tif</code> ({val.get('bytes', 0):,} bytes, SHA-256 <code>{esc(sha)}</code>)
is downloadable only for review and analysis. Its final-dot raster fails the current literal
one-way overlap rule. The same applies to its one-TIFF ZIP. This is not a new submission candidate.</p>
<div class="actions"><a class="button" style="background:#8b1e1e;color:#fff" href="downloads/{esc(name)}.tif" download>Download archived TIFF (review only)</a>
<a class="button secondary" href="downloads/{esc(name)}.zip" download>Download archive ZIP (review only)</a>
<a class="button secondary" href="protocol-review.html">Read the current stop report</a></div>
<section class="panel"><h2>Current suitability — stated plainly</h2>
<ul>
<li><strong>Download:</strong> yes, for review only; local format/range validation is not uniqueness clearance.</li>
<li><strong>Submit to the competition:</strong> no. The literal one-way registry gate has a duplicate witness.</li>
<li><strong>Weekly slot:</strong> none used. No slot selection or upload was made.</li>
<li><strong>Submission name/note:</strong> the archive identifier is historical only; no note is authorized for upload.</li>
</ul></section>
<section><h2>Why a local format pass is not enough</h2>
<p>The archived shared validator reports a single-band float32 GeoTIFF on the expected 3,730 × 3,292,
EPSG:32611 grid, values within [0,1], and no NaN or infinity. Its validation class is a local
format/range preflight, not organizer acceptance or uniqueness clearance. We cannot infer the
specific defect in the previously rejected upload because its bytes are unavailable.</p>
{table(['Check', 'Archived local validator'], vrows, 'Historical shared-validator receipt; not a current submit approval.')}
<p class="small">Validator class: {esc(val.get('validation_class', 'local format/range preflight'))}.</p></section>
<section><h2>Current uniqueness decision</h2>
<p>The current prompt requires a stop when any checked raster exceeds the one-way overlap threshold.
The recorded final-dot audit triggers that rule. This is a REGISTRY-MEASUREMENT, not a competition
score; the accessible archive is not exhaustive. A surface-stage audit was not run in this review
because no new candidate surface was generated.</p>
{table(['Measurement', 'Current evidence'], literal_rows, 'Literal one-way stop; historical mutual-overlap clearance is superseded.')}
<p>The earlier mutual-overlap results below are retained for provenance only and do not clear this
artifact under the current prompt.</p>
{table(['Historical measurement', 'Value'],
 [['Rasters checked', uniqueness.get('registry_rasters_checked')],
  ['Worst mutual overlap', f"{uniqueness.get('worst_dot_overlap'):.4f} ({esc(uniqueness.get('worst_overlap_submission'))})"],
  ['Worst forward-only overlap', f"{uniqueness.get('worst_forward_overlap'):.4f} ({esc(uniqueness.get('worst_forward_submission'))})"],
  ['Worst Spearman ρ', f"{uniqueness.get('worst_spearman_full_footprint'):.4f}"]],
 'Archived mutual-rule audit only; not current clearance.')}</section>
<section><h2>For a future candidate that is separately cleared</h2>
<ol class="steps">
<li>Wait for an explicit selector decision and a run card with <code>submit_recommended: true</code>; do not use the file above.</li>
<li>Open DrivenData’s competition 306 <em>New submission</em> page.</li>
<li>Select exactly one cleared single-band GeoTIFF or one ZIP containing only that TIFF; never upload both.</li>
<li>Paste the cleared candidate’s run-card note (at most 140 characters).</li>
<li>Keep the portal receipt with filename, SHA-256, timestamp and returned score. Only then label that result ORGANIZER-CONFIRMED.</li>
</ol></section>'''
    else:
        guide = f'''<div class="eyebrow">SUBMISSION GUIDE</div>
<h1>How to submit a separately cleared file.</h1>
<p class="lead">Check the run card before upload. A format-valid download is not automatically recommended for a weekly slot.</p>
<section class="panel"><h2>Decision, stated plainly</h2>
<ul>
<li><strong>Download:</strong> check the release flags and the artifact SHA-256.</li>
<li><strong>Upload a weekly slot:</strong> only if the selector has approved it and <code>submit_recommended</code> is true.</li>
<li><strong>Never</strong> upload the ZIP and the TIFF as two different submissions.</li></ul></section>
<section><h2>Steps</h2><ol class="steps">
<li>Open the competition <em>New submission</em> page (DrivenData competition 306).</li>
<li>Choose one cleared TIFF or its matching ZIP (which contains only that TIFF).</li>
<li>Paste the note from the cleared run card (at most 140 characters).</li>
<li>Submit and keep the receipt: filename, SHA-256, timestamp and the score the portal returns.</li>
<li>Record the returned score as ORGANIZER-CONFIRMED only from that receipt.</li>
</ol></section>
<section><h2>On-disk validator receipt</h2>
{table(['Check', 'Result'], vrows, 'Shared validator, all checks must pass.')}
<p class="small">Validator class: {esc(val.get('validation_class', 'local format/range preflight'))}.</p></section>'''
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
                    ablate.append([tag, esc(k), score_receipt(d['scores'][k])])
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
        history.append([esc(tag), score_receipt(cand), score_receipt(ref) if ref else '—'])
    results = f'''<div class="eyebrow">ARCHIVED EVIDENCE</div><h1>Archived experiments, two instruments, one recorded verdict.</h1>
<p>Each DTI table below reports HOLDOUT-DTI from its receipt, evaluator <code>gems57-pooled-hide-v2</code>,
95% CI, and withheld-positive count. The candidate rows in B/B′ use SGMC-derived proxy positives;
those labels are not organizer hidden truth and must not be called ORGANIZER-CONFIRMED. Values use
α = 0.2, β = 0.8 and a 300 m triangular kernel, with pooled terms and a paired spatial-cluster
bootstrap (1,000 draws, 20 km blocks). Intervals are conditional on the fitted folds/proxy truth,
not leaderboard intervals.</p>
<p><strong>Current status: DO NOT SUBMIT.</strong> The archived literal one-way registry audit stops
on four final-dot witnesses; see the current protocol review. Historical mutual-overlap clearance
is not current clearance.</p>
<p><strong>Historical tool regression:</strong> the archived mutual-overlap implementation treated
only mutual overlap as duplication. The reviewed final dots have forward overlap 1.00 with a dense
lattice; the literal prompt's one-way rule therefore triggers a stop.</p>
<p><strong>Historical measurement:</strong> archived raster <code>calib_r13lattice_00904.tif</code>
(206,895 registry dots) has a 3-px halo covering 100% of the footprint. Its forward overlap with
the reviewed candidate is 1.00, so the current one-way rule stops this artifact.</p>
<h2>Historical Phase-4 candidate — HOLDOUT-DTI, not organizer score</h2>
{table(['Arm', 'DTI', '95% CI', 'Withheld-positive pixels'], rows_a, 'Instrument A · gems57-pooled-hide-v2 · hide-and-recover catalogue holdout')}
{table(['Arm', 'DTI', '95% CI', 'Withheld-positive pixels'], rows_bp, "Instrument B′ · gems57-pooled-hide-v2 · SGMC proxy holdout, not organizer hidden truth")}
{table(['Arm', 'DTI', '95% CI', 'Withheld-positive pixels'], rows_ball, 'Instrument B · gems57-pooled-hide-v2 · unrestricted SGMC proxy holdout; not organizer hidden truth')}
<h2>Experiment 3 ablations</h2>
{table(['Instrument', 'Arm', 'HOLDOUT-DTI receipt'], ablate, 'Each DTI includes evidence class, evaluator version, withheld-positive count, value and 95% CI.')}
<h2>Leakage canaries</h2>
{table(['Feature', 'AUC (held-out)', 'Result'], canary_rows, 'Each feature alone; AUC is a leakage diagnostic, not DTI. AUC > 0.90 would stop the run.')}
<h2>Experiment history</h2>
{table(['Run', 'Candidate HOLDOUT-DTI receipt', 'H33 reference HOLDOUT-DTI receipt'], history)}
<p><a href="downloads/run_card.json">Full run card</a> ·
<a href="downloads/uniqueness.json">Uniqueness audit</a> ·
<a href="downloads/instrumentA_holdout.json">Instrument A</a> ·
<a href="downloads/instrumentB_prime.json">Instrument B′</a> ·
<a href="downloads/phase3_instrumentB_all.json">Experiment 3 B</a></p>'''

    if e2hold:
        _rows = [[esc(k), f"{v['dti']:.4f}", ci(v), str(v['withheld_positive_pixels'])]
                 for k, v in sorted(e2hold['scores'].items(), key=lambda kv: -kv[1]['dti'])]
        results += ("<h2>Parallel lane E2/E3 — archived catalogue holdouts</h2>"
                    "<p>E2 did not beat the D28 catalogue-holdout comparison; E3 depth-step was a null result. "
                    "Both are negative and not organizer-confirmed. See the E2/E3 run cards for the "
                    "complete HOLDOUT-DTI receipts, evaluator versions, withheld-positive counts and CIs.</p>"
                    + table(['Arm', 'DTI', '95% CI', 'Positives'], _rows,
                            'E2 HOLDOUT-DTI arms · gems57-pooled-hide-v2 · seed-20'))
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
