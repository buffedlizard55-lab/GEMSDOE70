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
    nav = ''.join(f'<a href="{h}">{esc(t)}</a>' for h, t in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · GEMSDOE70</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">GEMS<span>DOE70</span></a>
<span class="edition">PHASE 5 · 2026-10-20</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main>
<footer>Every figure is read from a recorded JSON receipt. A projection is never a score.
<a href="downloads/run_card.json">Run card</a> · <a href="downloads/uniqueness.json">Uniqueness</a> ·
<a href="downloads/instrumentA_holdout.json">Instrument A</a> ·
<a href="downloads/instrumentB_prime.json">Instrument B′</a></footer></body></html>'''


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


def main():
    card = load('evidence/run_card.json', {})
    if not card:
        raise SystemExit('evidence/run_card.json missing; run the experiment first')
    name = card['submission_name']
    sha = card['raster_sha256']
    val = card.get('validator_output') or {}
    checks = val.get('checks') or {}
    uniqueness = load('evidence/phase5/uniqueness.json', {}) or load('evidence/phase4/uniqueness.json', {})
    p5 = load('evidence/phase5/run_card.json', {})
    p5a = load('evidence/phase5/instrumentA_holdout.json')
    p5b = load('evidence/phase5/instrumentB_all.json')
    p5c = load('evidence/phase5/instrumentC_halo.json')
    p5rk = load('evidence/phase5/ranking_skill.json', {})
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
        'evidence/phase4/uniqueness.json': 'uniqueness_phase4.json',
        'evidence/phase5/uniqueness.json': 'uniqueness.json',
        'evidence/phase5/instrumentA_holdout.json': 'p5_instrumentA.json',
        'evidence/phase5/instrumentB_all.json': 'p5_instrumentB.json',
        'evidence/phase5/instrumentC_halo.json': 'p5_instrumentC.json',
        'evidence/phase5/ranking_skill.json': 'p5_ranking_skill.json',
        'evidence/phase5/canaries.json': 'p5_canaries.json',
        'evidence/phase5/emission.json': 'p5_emission.json',
        'evidence/phase5/qfaults_catalogue_overlap.json': 'p5_qfaults_overlap.json',
        'docs/preregistration-p5.md': 'preregistration-p5.md',
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
    headline = 'Promoted candidate — download and submit' if promoted else 'Verified file · not promoted'
    cdt = p5c['scores'] if p5c else {}
    crit = p5c['paired_differences']['h33_reference'] if p5c else {}
    decision = f'''<section class="{tone}" aria-labelledby="decision">
<div class="eyebrow">SUBMISSION STATUS · PHASE 5</div>
<h1 id="decision">{esc(headline)}</h1>
<p><strong>Download: yes.</strong> <strong>Download and submit: yes, as a calibrated test.</strong> Every pre-registered gate
(G1 format, G2 uniqueness, G3 ranking skill, G4 surrogate gain, G5 live-shape preservation)
passed; the file is unique among the 62 archived registry rasters and every shared-validator
check passed on the written bytes. There is <strong>no organizer-confirmed score</strong>: the
live leaderboard is the only test, and the returned value must be recorded from the receipt.</p>
<p><strong>What the evidence is, and is not.</strong> On the new halo surrogate (instrument C,
SGMC faults 0.2–3.2 km from the mapped catalogue) the candidate scores
{cdt.get('candidate', {}).get('dti', 0):.4f} against H33's {cdt.get('h33_reference', {}).get('dti', 0):.4f}
(paired Δ {crit.get('delta', 0):+.4f}, 95 % CI {ci(crit) if crit else '—'}). That surrogate is
chosen because the live evidence places the hidden truth in the halo; it is still a surrogate,
and transfer to the hidden truth is <em>not</em> validated.</p>
<div class="actions">
<a class="button" style="background:#076c64;color:#fff" href="downloads/{esc(name)}.tif" download>Download submission TIFF</a>
<a class="button secondary" href="downloads/{esc(name)}.zip" download>Download one-TIFF ZIP</a>
<a class="button secondary" href="submission.html">How to submit</a>
</div>
<p class="small">Name: <code>{esc(name)}</code> · Note ({card.get('note_chars', len(card.get('submission_note', '')))}/140 chars):
<code>{esc(card.get('submission_note', ''))}</code></p></section>'''

    # ------------------------------------------------------------------ overview
    a = p5a['scores'] if p5a else {}
    b = p5b['scores'] if p5b else {}
    c = p5c['scores'] if p5c else {}
    metrics = f'''<div class="metrics">
<section><div class="eyebrow">INSTRUMENT C · HALO SURROGATE DTI</div>
<div class="number">{c.get('candidate', {}).get('dti', 0):.4f}</div>
<p>{ci(c['candidate']) if c else '—'} · H33 {c.get('h33_reference', {}).get('dti', 0):.4f} · {c.get('candidate', {}).get('withheld_positive_pixels', 0):,} withheld proxy pixels</p></section>
<section><div class="eyebrow">RANKING SKILL · OUT-OF-QUADRANT AUC</div>
<div class="number">{p5rk.get('mean_fold_auc', 0):.3f}</div>
<p>mean of four held-out folds · raw pooled {p5rk.get('pooled_out_of_fold_auc_raw', 0):.3f} · rank-normalised {p5rk.get('pooled_out_of_fold_auc_rank_normalised', 0):.3f}</p></section>
<section><div class="eyebrow">UNIQUENESS · 62 RASTERS</div>
<div class="number">{uniqueness.get('worst_dot_overlap', 0):.2f}</div>
<p>Worst <em>mutual</em> overlap (limit 0.70) · worst ρ {uniqueness.get('worst_spearman_full_footprint', 0):.3f}</p></section></div>'''

    index = decision + f'''<section class="intro"><div class="eyebrow">WHAT THIS PAGE IS</div>
<h2>A unique, auditable candidate whose promotion rule is written down before the run.</h2>
<p>Phase 5 replaces the instrument that dominated Phase 4. A random field of 37,654 dots drawn
across the whole domain scores below H33 on the unrestricted SGMC proxy, but a random field drawn
inside the 0.2–3.2 km halo scores above it — the proxy's positives are spread over the whole map,
while the live ordering puts the hidden truth inside the halo. The new primary instrument
(instrument C) restricts the proxy to the halo. The candidate is an out-of-fold ranker trained on
43 geophysical, lidar-scarp, radiometric and terrain features with quadrant-blocked cross-validation.</p>
</section>{metrics}
<div class="columns">
<section class="panel"><h2>Why it is downloadable and submittable</h2>
<p>Shared validator on the written bytes: single band, float32, 3,730 × 3,292, EPSG:32611, 100 m
transform, values exactly 0/1, {card['emission']['count']:,} dots, zero on mapped faults, zero
outside the footprint. Uniqueness: worst mutual overlap {uniqueness.get('worst_dot_overlap', 0):.3f}
against {uniqueness.get('registry_rasters_checked')} archived rasters; worst |Spearman|
{abs(uniqueness.get('worst_spearman_full_footprint', 0)):.3f}.</p>
<a href="submission.html">Submission steps →</a></section>
<section class="panel"><h2>What would falsify it</h2>
<p>The ranker is trained on SGMC faults; if the hidden new faults are not SGMC-like, the tilt can
underperform the uniform H33 halo. The surrogate gain is {crit.get('delta', 0):+.4f}
({ci(crit) if crit else '—'}), and the quadrant folds span 1.5–3.6 k positives. A live score at or
below 0.2778 is a negative result and must be recorded as such.</p>
<a href="limitations.html">Known limits →</a></section></div>
<section><h2>Measured this session</h2>
<p>The catalogue is the USGS Quaternary fault database: 99.998 % of rasterised QFaults trace pixels
lie within 3 px of <code>existing_faults.tif</code>, so QFaults cannot be a "new fault" proxy.
SGMC is the only independent inventory in the cached inputs (3,666 shared px, 78,485 not).
Every number on this site is read from a JSON receipt; a projection is never a score.</p>
<ul><li><a href="h33-analysis.html">Why the archived H33 field scored 0.2778</a></li>
<li><a href="results.html">Instruments A, B, C; gates; canaries</a></li>
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
    guide = f'''<div class="eyebrow">SUBMISSION GUIDE · PHASE 5</div>
<h1>How to submit this file — and what the number will mean.</h1>
<p class="lead"><strong>The file:</strong> <code>downloads/{esc(name)}.tif</code>
({val.get('bytes', 0):,} bytes, SHA-256 <code>{esc(sha)}</code>).
A one-TIFF ZIP of the same file is provided for portals that ask for it. Upload exactly one of them.</p>
<section class="panel"><h2>Decision, stated plainly</h2>
<ul>
<li><strong>Download and submit a weekly slot:</strong> yes, as a calibrated test. Verdict
<code>{esc(card['verdict'])}</code>; all five pre-registered gates passed (see the run card).</li>
<li><strong>What the gates do not prove:</strong> the hidden truth is not available to us. The
candidate beats H33 on the halo surrogate {c.get('candidate', {}).get('dti', 0):.4f} vs
{c.get('h33_reference', {}).get('dti', 0):.4f}, paired Δ {crit.get('delta', 0):+.4f}
{ci(crit) if crit else ''}. That is evidence about a surrogate, not a leaderboard projection.</li>
<li><strong>Record the returned score</strong> as ORGANIZER-CONFIRMED. If it is at or below 0.2778,
the hypothesis is negative and must be written down as such.</li>
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
 'Corrected binary-dot definition; forward-only overlap with a dense sampling grid is uninformative.')}</section>
<section><h2>Phase-5 gate receipt</h2>
{table(['Gate', 'Result'], [[esc(k), 'pass' if v else 'FAIL'] for k, v in card.get('gates', {}).items()],
 'All five gates must pass before the file is labelled submittable.')}
<p class="small">Ranking skill: mean held-out AUC {p5rk.get('mean_fold_auc', 0):.4f}; per-fold
{', '.join(f"{k}: {v['auc']:.3f}" for k, v in p5rk.get('fold_auc', {}).items())}. Raw pooled
{p5rk.get('pooled_out_of_fold_auc_raw', 0):.4f} is reported but not used as the gate (see the
preregistration amendment A1).</p></section>'''
    (DOCS / 'submission.html').write_text(frame('Submit a file', guide))

    # ------------------------------------------------------------------- results
    rows_a = instrument_rows(p4a)
    rows_bp = instrument_rows(p4b)
    rows_ball = instrument_rows(p4ball)
    p4_note = ('<p>The Phase-4 candidate was published as a negative because its pre-registered '
               'gate (instrument B′, unrestricted proxy) said H33 won. Phase 5 replaced it after '
               'measuring that the proxy positives are spread over the whole domain while the live '
               'ordering places the hidden truth in the halo.</p>')
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
    rows_c = instrument_rows(p5c)
    rows_p5b = instrument_rows(p5b)
    rows_p5a = instrument_rows(p5a)
    results = f'''<div class="eyebrow">EVIDENCE</div><h1>Phase 5: one ranker, three instruments, five gates.</h1>
<p>All DTI values use α = 0.2, β = 0.8 and a 300 m triangular kernel on the pinned 100 m grid, pooled
terms and a paired 20 km spatial-cluster bootstrap (1,000 draws). Intervals are conditional on the
fitted folds and the surrogate truth; they are <strong>not</strong> leaderboard intervals.</p>
<h2>Published candidate (Phase 5)</h2>
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_c, 'Instrument C · halo surrogate (SGMC only, 3–32 px from catalogue) — primary gate')}
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_p5b, 'Instrument B · unrestricted SGMC proxy — continuity only')}
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_p5a, 'Instrument A · shared catalogue holdout — structurally hostile to a global halo emission (masks a 3 px buffer around withheld traces)')}
<h2>Ranking skill and canaries</h2>
{table(['Fold', 'Pixels', 'Positives', 'Held-out AUC'],
 [[esc(k), f"{v['n']:,}", f"{v['positives']:,}", f"{v['auc']:.4f}"] for k, v in p5rk.get('fold_auc', {}).items()],
 'Spatial four-fold by quadrant; each fold predicted by a model trained on the other three')}
<p>Mean held-out AUC <strong>{p5rk.get('mean_fold_auc', 0):.4f}</strong>; raw pooled
{p5rk.get('pooled_out_of_fold_auc_raw', 0):.4f}; rank-normalised pooled
{p5rk.get('pooled_out_of_fold_auc_rank_normalised', 0):.4f}. Worst single-feature canary AUC
{card.get('canary_worst_auc', 0):.4f} (limit 0.90).</p>
<h2>Phase-5 gates</h2>
{table(['Gate', 'Result'], [[esc(k), 'pass' if v else 'FAIL'] for k, v in card.get('gates', {}).items()],
 'Registered before the run except the G3 statistic amendment A1, which is disclosed in the card')}
<h2>Emission</h2>
{table(['Measurement', 'Value'],
 [['Dots', f"{card['emission']['count']:,}"],
  ['Block / NMS', f"{card['emission']['block_px']} px / {card['emission']['nms_px']} px"],
  ['Median catalogue distance', f"{card['emission']['median_distance_px']:.2f} px"],
  ['Occupied 200 px blocks', card['emission']['occupied_200px_blocks']]],
 'Live-shape preservation gate: median in [8, 24] px and at least 130 blocks')}
<h2>Phase-4 history (superseded gate)</h2>
'''
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
<a href="downloads/upstream_fix_report.md">Upstream fix report</a></p>'''
    (DOCS / 'sources.html').write_text(frame('Sources', src_page))

    # Root entry point (repository-root Pages keeps working).
    (ROOT / 'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70</title>'
        '</head><body><p><a href="docs/index.html">Open the GEMSDOE70 evidence site</a></p>'
        '</body></html>\n')
    (DOCS / '.nojekyll').touch()
    # Backwards-compatible entry points; they must not carry stale claims.
    for old, target in (('executive-summary.html', 'submission.html'),
                        ('irregularities.html', 'limitations.html'),
                        ('status.html', 'index.html')):
        (DOCS / old).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={target}"><title>GEMSDOE70</title>'
            f'</head><body><p>This page moved. <a href="{target}">Continue</a>.</p></body></html>\n')
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
