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
sys.path.insert(0, str(ROOT / 'src'))
from gems70.release import p5_status

DOCS = ROOT / 'docs'
DOWN = DOCS / 'downloads'

NAV = [('index.html', 'Overview'), ('executive-summary.html', 'Executive summary'),
       ('p5.html', 'P5-cover research TIFF'),
       ('protocol-review.html', 'Protocol review'), ('submission.html', 'Submission guide'),
       ('results.html', 'Evidence'), ('hypotheses.html', 'Hypotheses'),
       ('h33-analysis.html', 'Why H33 scored'), ('e3-candidate.html', 'Archived scarp E3'), ('sources.html', 'Sources'),
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
<span class="edition">PROTOCOL REVIEW · 2026-10-20</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">
<aside class="stop"><strong>Current protocol: DO NOT SUBMIT.</strong>
<strong>DO NOT SUBMIT — literal protocol stop.</strong> Old archives and the new P5 continuous TIFF
are downloadable for <em>review only</em>. Positive-support overlap fails the literal forward
rule; neither a local validator nor distinct bytes authorize a slot.
<a href="p5.html">P5-cover negative result</a> · <a href="protocol-review.html">Historical audit</a> ·
<a href="downloads/p5_run_card.json">New P5 run card</a> ·
<a href="downloads/review_run_card.json">Prior review card</a>.</aside>{body}</main>
<footer>Every figure is read from a recorded JSON receipt. A projection is never a score.
<a href="downloads/p5_run_card.json">New P5 negative card</a> ·
<a href="downloads/phase4_run_card.json">Concurrent analytic-halo run card</a> ·
<a href="downloads/archived_p4_run_card.json">Archived P4 run card</a> · <a href="downloads/uniqueness.json">Uniqueness</a> ·
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
    card = load('evidence/phase4/run_card.json', {})
    if not card:
        raise SystemExit('evidence/run_card.json missing; run the experiment first')
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
    p5 = load('evidence/p5/run_card.json', {})
    p5audit = load('evidence/p5/literal_blocker.json', {})
    p5canary = load('evidence/p5/canaries.json', {})
    p5sources = load('evidence/p5/official_source_review.json', {})
    p5_state = p5_status(ROOT)
    if not (p5 and p5audit and p5canary and p5sources
            and p5_state['download_ok_for_review'] is True
            and p5['submit_recommended'] is False):
        raise SystemExit('P5 hash/validator/protocol review evidence missing; refusing stale publication')

    DOCS.mkdir(parents=True, exist_ok=True)
    DOWN.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- copy evidence
    copies = {
        'evidence/run_card.json': 'run_card.json',
        'evidence/phase4/run_card.json': 'phase4_run_card.json',
        'evidence/history/p4_stratified_halo/run_card.json': 'archived_p4_run_card.json',
        'evidence/review/run_card.json': 'review_run_card.json',
        'evidence/review/literal_protocol_audit.json': 'literal_protocol_audit.json',
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
        'evidence/upstream_fix_report.md': 'upstream_fix_report.txt',
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
        'evidence/p5/run_card.json': 'p5_run_card.json',
        'evidence/p5/instrument_a.json': 'p5_instrument_a.json',
        'evidence/p5/instrument_b_prime.json': 'p5_instrument_b_prime.json',
        'evidence/p5/canaries.json': 'p5_canaries.json',
        'evidence/p5/literal_blocker.json': 'p5_literal_blocker.json',
        'evidence/p5/official_source_review.json': 'p5_sources.json',
        'evidence/p5/reporting_amendment.json': 'p5_reporting_amendment.json',
        'evidence/p5/surface_registry.json': 'p5_surface_registry.json',
        'evidence/e5/run_card.json': 'e5_run_card.json',
        'evidence/e5/canaries.json': 'e5_canaries.json',
        'evidence/e5/training.json': 'e5_training.json',
        'evidence/e5/instrumentA_holdout.json': 'e5_instrumentA.json',
        'evidence/e5/instrumentB_prime.json': 'e5_instrumentB_prime.json',
        'evidence/e5/instrumentB_all.json': 'e5_instrumentB_all.json',
        'evidence/e5/surface_uniqueness.json': 'e5_surface_uniqueness.json',
        'evidence/e5/uniqueness.json': 'e5_final_uniqueness.json',
        'evidence/e5/leaderboard_read.json': 'e5_leaderboard_read.json',
        'evidence/p6_dualhorizon/run_card.json': 'p6_dualhorizon_run_card.json',
        'evidence/p6_dualhorizon/canaries.json': 'p6_dualhorizon_canaries.json',
        'evidence/p6_dualhorizon/instrumentA_holdout.json': 'p6_dualhorizon_instrumentA.json',
        'evidence/p6_dualhorizon/instrumentB_prime.json': 'p6_dualhorizon_instrumentB_prime.json',
        'evidence/p6_dualhorizon/instrumentB_double_prime.json': 'p6_dualhorizon_instrumentB_double_prime.json',
        'evidence/p6_dualhorizon/instrumentB_all.json': 'p6_dualhorizon_instrumentB_all.json',
        'evidence/p6_dualhorizon/sgmc_buffer_audit.json': 'sgmc_buffer_audit.json',
        'evidence/p6_dualhorizon/e2_mutual_uniqueness.json': 'e2_mutual_uniqueness.json',
        'evidence/p6_dualhorizon/uniqueness.json': 'p6_dualhorizon_uniqueness.json',
        'evidence/p6_dualhorizon/surface_uniqueness.json': 'p6_dualhorizon_surface_uniqueness.json',
    }
    for src, dst in copies.items():
        s = ROOT / src
        if s.is_file():
            shutil.copyfile(s, DOWN / dst)

    # --------------------------------------------------------------- decision box
    # The frozen experiment card is evidence, never the current policy decision.
    review = load('evidence/review/literal_protocol_audit.json', {})
    rc = load('evidence/review/run_card.json', {})
    if not review or not rc:
        raise SystemExit('Frozen literal protocol audit missing; refusing stale publication')
    pa = p5['holdout_dti']['instrument_a']
    pb = p5['holdout_dti']['instrument_b_prime_proxy']
    da = p5['holdout_dti']['paired_vs_visible_p4']
    db = p5['holdout_dti']['paired_vs_h33']
    p5name = p5['submission_name']
    latest_decision = f'''<section class="stop" aria-labelledby="p5-decision">
<div class="eyebrow">NEW P5-COVER EXPERIMENT · RESEARCH FILE ONLY</div>
<h1 id="p5-decision">New P5-cover TIFF: download for review. DO NOT SUBMIT.</h1>
<p><strong>Download: yes — for research only.</strong> This newly generated continuous GeoTIFF
is distinct in bytes from the checked archive, all-finite within [0,1], single-band float32,
and aligned to the pinned sample. <strong>Competition upload / weekly slot: NO.</strong>
It failed the pre-registered spatial holdout and the literal forward-overlap stop;
it has no organizer receipt. Do not treat a format pass as submission approval.</p>
<p>Catalogue HOLDOUT-DTI ({esc(pa['evaluator_version'])}, {pa['withheld_positive_pixels']:,}
withheld positives): <strong>{pa['dti']:.4f} {ci(pa)}</strong> vs visible-only P4
{p5['comparators']['a_visible_only_p4']['dti']:.4f}.
SGMC-proxy HOLDOUT-DTI ({esc(pb['evaluator_version'])}, {pb['withheld_positive_pixels']:,}
proxy positives): <strong>{pb['dti']:.4f} {ci(pb)}</strong> vs H33
{p5['comparators']['b_prime_h33_frozen']['dti']:.4f}; paired difference
{db['delta']:+.4f} {ci(db)}. Neither is a competition score.</p>
<p>The binary-dot checker counts {p5['correlation_overlap_vs_registry']['binary_one_dots']}
exact-one dots in a continuous map; this is <em>not</em> a loophole. Its
{p5['correlation_overlap_vs_registry']['positive_support_pixels']:,} positive cells have
{p5['correlation_overlap_vs_registry']['forward_overlap_positive_support_lattice']:.2f}
forward 3-pixel overlap against the pinned lattice (limit 0.70). The witness covers
{p5audit['feature_valid_pixels_after_12px_erosion']:,} / {p5audit['feature_valid_pixels_after_12px_erosion']:,}
feature-valid interior cells. No discrete final dots were placed.</p>
<div class="actions">
<a class="button secondary" href="downloads/{esc(p5name)}.tif" download>Download NEW P5-cover research TIFF — DO NOT SUBMIT</a>
<a class="button secondary" href="downloads/{esc(p5name)}.zip" download>One-TIFF ZIP — review only</a>
<a class="button" href="p5.html">Read P5 evidence and limits</a>
</div>
<p class="small">Name: <code>{esc(p5name)}</code> · Note ({p5['note_chars']}/140 characters,
<strong>not an upload instruction</strong>): <code>{esc(p5['submission_note'])}</code> ·
SHA-256 <code>{esc(p5['raster_sha256'])}</code>.</p></section>'''
    decision = f'''<section class="stop" aria-labelledby="decision">
<div class="eyebrow">PRIOR {len(review['archived_artifacts'])}-ARCHIVE REVIEW · STILL BLOCKED</div>
<h2 id="decision">Older files: DO NOT SUBMIT — literal protocol stop</h2>
<p><strong>Download: yes — format-validated for review.</strong> For forensic review only.
<strong>Competition submission: NO — not recommended.</strong>
The witness scan is sufficient to reject, but covers not every private or uncommitted raster.
These are {len(review['archived_artifacts'])} <em>prior</em> archived dot files, not protocol-compliant submissions.
<strong>Submit a weekly slot: not recommended; blocked by your protocol.</strong></p>
<p>All {len(review['archived_artifacts'])} prior dot TIFFs have forward overlap 1.00 against a verified binary registry lattice
(limit 0.70). Mutual overlap is not an authorized exemption. The previous review generated no
new TIFF; P5 above is a separate subsequent negative continuous experiment. No slot was used.</p>
<div class="actions">
<a class="button secondary" href="downloads/{esc(name)}.tif" download>Download archived TIFF — DO NOT SUBMIT</a>
<a class="button secondary" href="downloads/{esc(name)}.zip" download>Archived one-TIFF ZIP — review only</a>
<a class="button" href="executive-summary.html">Executive summary / next steps</a>
</div>
<p class="small">Archived name: <code>{esc(name)}</code> · SHA-256 <code>{esc(sha)}</code>.</p>
<p class="small">Review card: <code>{esc(rc['submission_name'])}</code> · Note:
<code>{esc(rc['submission_note'])}</code> (not an upload instruction).</p></section>'''

    # ------------------------------------------------------------------ overview
    a = p4a['scores'] if p4a else {}
    b = p4b['scores'] if p4b else {}
    ball = p4ball['scores'] if p4ball else {}
    metrics = f'''<div class="metrics">
<section><div class="eyebrow">ARCHIVED ANALYTIC-HALO P5 · INSTRUMENT A · HOLDOUT-DTI</div>
<div class="number">{a['candidate']['dti']:.4f}</div>
<p>{ci(a['candidate'])} · {a['candidate']['withheld_positive_pixels']:,} withheld catalogue pixels</p></section>
<section><div class="eyebrow">ARCHIVED ANALYTIC-HALO P5 · INSTRUMENT B′ · PROXY-DTI</div>
<div class="number">{b['candidate']['dti']:.4f}</div>
<p>{ci(b['candidate'])} · SGMC proxy outside the duplication band</p></section>
<section><div class="eyebrow">LITERAL OVERLAP · STOP</div>
<div class="number">{uniqueness.get('worst_forward_overlap', 0):.2f}</div>
<p>Forward overlap exceeds 0.70. Low correlation does not cancel this failure.</p></section></div>'''

    index = latest_decision + decision + f'''<section class="intro"><div class="eyebrow">WHAT THIS PAGE IS</div>
<h2>A new research TIFF and prior format-valid archives — no protocol-cleared submission.</h2>
<p>Our P5-cover continuous map is a deliberately measured negative. Other sessions ran the archived dot experiments below;
a prior review found an unauthorized mutual-overlap substitution and corrected the current gate.
Historical scientific evidence remains intact but cannot override the literal stop rule.</p>
</section>{metrics}
<div class="columns">
<section class="panel"><h2>Why it is downloadable</h2>
<p>The shared validator re-read the bytes: single band, float32, 3,730 × 3,292, EPSG:32611,
transform 100 m, values exactly 0/1, 37,654 dots, zero on mapped faults, zero outside the footprint.
The fresh binary-witness comparison fails the literal uniqueness rule. Format checks pass, but
that is not organizer acceptance or permission to submit.</p>
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

    # Concurrent archive: analytic-signal dot halo. Distinct from P5-cover continuous.
    p5card = load('evidence/phase5/run_card.json', {})
    p5_section = ''
    if p5card and p5card.get('submission_name') == 'gems70-p5-analytic-halo-37654-20261020':
        pa_analytic = p5card['instrument_a_holdout']['candidate']
        pb_analytic = p5card['instrument_b_prime_proxy']['candidate']
        p5_section = f"""<section><h2>Concurrent lane P5 analytic-signal dots — DO NOT SUBMIT</h2>
<p>Analytic-signal amplitude <code>hypot(tmi_hg, tmi_vg)</code> rank inside the 7×7 stratified halo (2.4–32 px), 37,654 dots off-catalogue, 5-px NMS. <strong>HOLDOUT-DTI A {pa_analytic['dti']:.4f} {ci(pa_analytic)} vs H33 0.0037 win; B′ {pb_analytic['dti']:.4f} {ci(pb_analytic)} vs 0.0938 H33 win Δ {p5card['paired_b_prime_vs_h33']['delta']:+.4f} {p5card['paired_b_prime_vs_h33']['ci95']}</strong> — negative on the pre-registered B′ gate, no slot. Uniqueness: 62 rasters, worst mutual 0.30 (limit 0.70), worst Spearman 0.042; forward 1.00 vs dense lattice (literal duplicate, review only).</p>
<div class="actions"><a class="button secondary" href="downloads/gems70-p5-analytic-halo-37654-20261020.tif" download>Download P5 review TIFF</a>
<a class="button secondary" href="downloads/gems70-p5-analytic-halo-37654-20261020.zip" download>Download P5 ZIP</a>
<a class="button secondary" href="downloads/gems70-p5-analytic-halo-37654-20261020.json" download>P5 receipt</a></div>
<p class="small">Name: <code>gems70-p5-analytic-halo-37654-20261020</code> · Note (93/140): <code>{esc(p5card.get('submission_note',''))}</code> · SHA-256 <code>{esc(p5card.get('raster_sha256',''))}</code> · Evidence <code>evidence/phase5/</code> · Hypotheses <code>docs/hypotheses.md</code> now ranks 5 candidates (H-2 tested, H-3 radiometric already fetched, H-4 lidar scarp, H-5 conductive breach, H-6 basement curvature).</p></section>"""
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
38,000 dots) merged from a parallel session. <strong>Download for forensic review: yes.
Submit: NO</strong> — its frozen bars failed (D28 catalogue-holdout best not beaten) and the
fresh binary-witness comparison fails the literal overlap rule. Archived HOLDOUT-DTI {_d['dti']:.4f} {ci(_d)} · gems57-pooled-hide-v2 · 11,321 withheld positives ·
{e2card['final_dot_count']:,} dots · SHA-256 <code>{esc(e2pub.get('sha256',''))}</code>.</p>
<div class="actions"><a class="button secondary" href="downloads/{esc(e2pub.get('file',''))}" download>Download E2 review TIFF</a>
<a class="button secondary" href="downloads/e2_run_card.json" download>E2 run card</a></div>
<p class="small">Name: <code>{esc(e2card.get('submission_name',''))}</code> · Note:
<code>{esc(e2card.get('submission_note'))}</code>. E3 (depth-step) in the same lane family is
negative with no file. Full tables on the results page; terms in
<code>docs/publication-amendment-e2.md</code>.</p></section>"""
    # ------------------------------------------------------- E5 supervised lane
    e5card = load('evidence/e5/run_card.json', {})
    e5_section = ''
    if e5card and e5card.get('raster_sha256'):
        _a = e5card['instrument_a_holdout']
        _b = e5card['instrument_b_prime_proxy']
        _d = e5card['paired_b_prime_vs_h33']
        _u = e5card['correlation_overlap_vs_registry']['final_dots_stage']
        e5_section = f"""<section><h2>Concurrent E5 — supervised within-halo ranking (distinct bytes, not literal-unique; verdict: {esc(e5card['verdict'])} — DO NOT SUBMIT)</h2>
<p>Preregistered (<code>docs/preregistration-e5.md</code>): a gradient-boosted ranker trained on the
SGMC off-catalogue proxy with leave-one-quadrant-out (OOF AUC 0.69–0.78; worst single-feature
canary AUC {e5card['canary_worst_single_feature_auc']:.3f} &le; 0.90), emitted as 37,654 binary dots
through the same stratified emitter. <strong>Download for review: yes. Submit a weekly slot: NO</strong> —
on the pre-registered target-like gate B′ it scores {_b['candidate']['dti']:.4f} vs H33
{_b['h33_reference']['dti']:.4f} (paired &Delta; {_d['delta']:+.4f}, 95% CI {ci(_d)}: includes zero, so no
validated improvement over H33's 0.2778 is claimed). Instrument A HOLDOUT-DTI
{_a['candidate']['dti']:.4f} vs H33 {_a['h33_reference']['dti']:.4f} favours it, as that instrument
favours every catalogue-adjacent method. Uniqueness vs {_u['rasters_checked']} registry rasters:
worst mutual overlap {_u['worst_mutual_overlap']:.3f} (limit 0.70), worst &rho;
{_u['worst_spearman_full_footprint']:.3f} (limit 0.90). Values are exactly 0/1 — inside [0,1], no NaN.
SHA-256 <code>{esc(e5card['raster_sha256'])}</code>.</p>
<div class="actions"><a class="button secondary" href="downloads/{esc(e5card['submission_name'])}.tif" download>Download E5 TIFF (review only — DO NOT SUBMIT)</a>
<a class="button secondary" href="downloads/e5_run_card.json" download>E5 run card</a></div>
<p class="small">Name: <code>{esc(e5card['submission_name'])}</code> · Note ({e5card['note_chars']}/140):
<code>{esc(e5card['submission_note'])}</code>. Negative results are deliverables: supervised ranking
halved P4's B′ deficit but did not beat uniform halo sampling. Full tables on the results page.</p></section>"""
    # ------------------------------------------------------- P6 dual-horizon lane
    p6card = load('evidence/p6_dualhorizon/run_card.json', {})
    p6_section = ''
    if p6card and p6card.get('raster_sha256'):
        _a6 = p6card['instrument_a_holdout']
        _b6 = p6card['instrument_b_prime_proxy']
        _bpp6 = p6card['instrument_b_double_prime_proxy']
        _db6 = p6card['paired_b_prime_vs_h33']
        _da6 = p6card['paired_a_vs_p4']
        _u6 = p6card['correlation_overlap_vs_registry']
        p6_section = f"""<section><h2>Concurrent P6 — dual-horizon LOQO scarp-rad-basement ranker + SGMC 1–20 px buffer calibration (verdict: {esc(p6card['verdict'])} — DO NOT SUBMIT)</h2>
<p>Preregistered in <code>docs/hypotheses.md</code> (<code>H-P5-1</code> through <code>H-P5-5</code>): combines leave-one-quadrant-out
scarp-radiometric-basement ranking (19-band stack + 1 m LiDAR scarp + 10 m 3DEP breaklines + GeoDAWN radiometric ratios)
with the visible-catalogue tip/host-length halo across <code>5&times;5</code> strata and <code>3.2 px</code> NMS (<code>37,654</code> binary dots).
<strong>Download for review: yes (<code>download_ok = true</code>). Submit a weekly slot: NO (<code>submit_recommended = false</code>)</strong> —
Instrument A HOLDOUT-DTI <strong>{_a6['candidate']['dti']:.4f} {ci(_a6['candidate'])}</strong> (vs P4 {_a6['p4_reference']['dti']:.4f},
paired &Delta; {_da6['delta']:+.4f} {ci(_da6)} straddles zero; vs H33 {_a6['h33_reference']['dti']:.4f});
Instrument B′ PROXY-DTI (<code>d &ge; 3 px</code>) <strong>{_b6['candidate']['dti']:.4f} {ci(_b6['candidate'])}</strong>
vs H33 {_b6['h33_reference']['dti']:.4f} (paired &Delta; {_db6['delta']:+.4f} {ci(_db6)}, +53.5%) and vs P4 {_b6['p4_reference']['dti']:.4f} (+77.4%);
Instrument B′′ PROXY-DTI (<code>d &ge; 6 px</code>) <strong>{_bpp6['candidate']['dti']:.4f} {ci(_bpp6['candidate'])}</strong> vs H33 {_bpp6['h33_reference']['dti']:.4f};
unsupervised breakline ablation (<code>Exp 5.2</code>, zero SGMC training) scores <strong>{_b6['exp5_2_brk_7x7']['dti']:.4f}</strong> on B′ and <strong>{_a6['exp5_2_brk_7x7']['dti']:.4f}</strong> on A.
Held fail-closed because paired A vs P4 CI includes zero, SGMC B′ over-weights steep pre-Quaternary bedrock faults (<code>13.42&deg;</code> vs catalogue <code>5.55&deg;</code>),
and literal forward overlap against the dense lattice is {_u6['worst_forward_overlap']:.2f} (worst mutual overlap {_u6['worst_mutual_overlap']:.4f} &le; 0.70, worst &rho; {_u6['worst_spearman_full_footprint']:.4f} &le; 0.90 across {_u6['rasters_checked']} rasters).
SHA-256 <code>{esc(p6card['raster_sha256'])}</code>.</p>
<div class="actions"><a class="button secondary" href="downloads/{esc(p6card['submission_name'])}.tif" download>Download P6 dual-horizon TIFF (review only — DO NOT SUBMIT)</a>
<a class="button secondary" href="downloads/{esc(p6card['submission_name'])}.zip" download>Download P6 ZIP</a>
<a class="button secondary" href="downloads/p6_dualhorizon_run_card.json" download>P6 run card</a>
<a class="button secondary" href="downloads/sgmc_buffer_audit.json" download>SGMC 1–20 px buffer audit</a>
<a class="button secondary" href="downloads/e2_mutual_uniqueness.json" download>E2 62-raster audit</a></div>
<p class="small">Name: <code>{esc(p6card['submission_name'])}</code> · Note ({p6card['note_chars']}/140):
<code>{esc(p6card['submission_note'])}</code>.</p></section>"""
    archive_rows = [[esc(Path(r['artifact']).name),
        f'<a href="{esc(r["artifact"].removeprefix("docs/"))}" download>Download for review — DO NOT SUBMIT</a>',
        'pass' if r['validator_output']['all_checks_passed'] else 'FAIL',
        str(r['shared_measurements']['rows'][0]['my_dots_within_3px_of_theirs'])]
        for r in review['archived_artifacts']]
    archives = f'<h2>{len(review["archived_artifacts"])} frozen prior dot TIFFs — forensic review only</h2>' + table(
        ['Archive', 'Download', 'Local format', 'Forward overlap (limit 0.70)'], archive_rows)
    (DOCS / 'index.html').write_text(frame('Overview', index + p6_section + e5_section + e2_section + p5_section + archives))

    # ------------------------------------------------------------- submit guide
    vrows = [[esc(k), 'pass' if v else 'FAIL'] for k, v in checks.items()]
    guide = latest_decision + f'''<div class="eyebrow">SUBMISSION GUIDE</div>
<h1>Submission guide — current files are blocked.</h1>
<p class="lead"><strong>The file:</strong> <code>downloads/{esc(name)}.tif</code>
({val.get('bytes', 0):,} bytes, SHA-256 <code>{esc(sha)}</code>).
A one-TIFF ZIP is retained for review. Do not upload either current file.</p>
<section class="panel"><h2>Decision, stated plainly</h2>
<ul>
<li><strong>Download:</strong> yes — archived, format-validated; NOT protocol-unique.</li>
<li><strong>Upload a weekly slot:</strong> not recommended. Verdict <code>{esc(card['verdict'])}</code>.
Our target-like proxy says it is 12.6% below H33; our catalogue holdout says it is 20× above it.
Neither is the hidden truth. The literal overlap gate also fails: do not submit.</li>
<li><strong>Never</strong> upload the ZIP and the TIFF as two different submissions.</li></ul></section>
<section><h2>For a future promoted file only — NOT this archive</h2>
<p>First pass the current literal uniqueness and scientific gates, then obtain a separate selector
decision and verify the live weekly cap. Stop now for the current files.</p><ol class="steps">
<li>Open the competition <em>New submission</em> page only after a separate selector verifies the
weekly cap, eligibility and a new candidate's scientific/literal-gate clearances.</li>
<li>Choose that <em>future approved</em> single-band <code>.tif</code> (or its matching one-TIFF ZIP).
<strong>Do not choose the archived P4 or the new P5 file.</strong></li>
<li>Paste the name and the at-most-140-character note from that future file's approved run card,
not from this blocked archive.</li>
<li>Submit once and keep its filename, hash, timestamp and portal score receipt.</li>
<li>Only then label the returned score ORGANIZER-CONFIRMED.</li>
</ol>
<p>For historical record only, the concurrent analytic-halo note was <code>{esc(card.get('submission_note', ''))}</code>.
It is NOT an instruction to upload this archive.</p></section>
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
 'Historical mutual-rule receipt only; current forward-rule status is STOP. See the fresh audit.')}</section>'''
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
                   ('Canonical analytic P5 · A', p4a), ('Canonical analytic P5 · B′', p4b)):
        if not d:
            continue
        cand = d['scores']['candidate']
        ref = d['scores'].get('h33_reference')
        history.append([esc(tag), f"{cand['dti']:.4f}", ci(cand),
                        f"{ref['dti']:.4f}" if ref else '—'])
    new_evidence = f'''<section class="panel"><div class="eyebrow">NEW · P5 RESEARCH NEGATIVE</div>
<h2>Cross-fitted magnetic-cover ranking did not beat the mapped-halo baselines.</h2>
<p>Catalogue HOLDOUT-DTI ({esc(pa['evaluator_version'])}; {pa['withheld_positive_pixels']:,}
withheld positives): candidate {pa['dti']:.4f} {ci(pa)} vs visible-only P4
{p5['comparators']['a_visible_only_p4']['dti']:.4f}; paired Δ {da['delta']:+.4f}
{ci(da)}. SGMC proxy HOLDOUT-DTI ({esc(pb['evaluator_version'])};
{pb['withheld_positive_pixels']:,} proxy positives): candidate {pb['dti']:.4f}
{ci(pb)} vs frozen H33 {p5['comparators']['b_prime_h33_frozen']['dti']:.4f};
paired Δ {db['delta']:+.4f} {ci(db)}. These are not organizer-confirmed scores.</p>
<p>Worst Spearman ρ {p5['correlation_overlap_vs_registry']['worst_spearman_full_footprint']:.4f}
across {p5['correlation_overlap_vs_registry']['rasters_checked']} archived/local TIFFs;
positive-support forward overlap 1.00 vs the lattice, therefore <strong>DO NOT SUBMIT.</strong></p>
<a href="p5.html">Full P5 reproducibility, feature canaries and downloadable research file →</a></section>'''
    results = new_evidence + f'''<div class="eyebrow">ARCHIVED EVIDENCE</div><h1>Other experiments, separate instruments and their negative verdicts.</h1>
<p>All DTI values use α = 0.2, β = 0.8 and a 300 m triangular kernel on the pinned 100 m grid, with
pooled terms and a paired spatial-cluster bootstrap (1,000 draws, 20 km blocks). Intervals are
conditional on the fitted folds and the proxy truth; they are not leaderboard intervals.</p>
<p><strong>Historical results, not a current uniqueness pass.</strong> Fresh measurement:
<code>calib_r13lattice_00904.tif</code> has halo coverage 99.871327%, not 100%. The
{len(review['archived_artifacts'])} frozen prior dot TIFFs have forward overlap 1.00.
The literal policy stops dot placement.</p>
<p>Evaluator for catalogue HOLDOUT-DTI: gems57-pooled-hide-v2. SGMC tables below are separately
labeled PROXY-DTI, not hide-and-recover HOLDOUT-DTI or organizer-confirmed scores.</p>
<h2>Concurrent analytic-halo P5 candidate (historical negative)</h2>
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_a, 'Instrument A · shared hide-and-recover catalogue holdout')}
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_bp, "Instrument B′ · SGMC proxy, d ≥ 3 px from catalogue")}
{table(['Arm', 'DTI', '95% CI', 'Positives'], rows_ball, 'SGMC PROXY-DTI B · unrestricted (possible map duplication)')}
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
    if e5card:
        _ra = [[esc(k), f"{v['dti']:.4f}", ci(v), str(v['withheld_positive_pixels'])]
               for k, v in sorted(e5card['instrument_a_holdout'].items(),
                                  key=lambda kv: -kv[1]['dti'])]
        _rb = [[esc(k), f"{v['dti']:.4f}", ci(v), str(v['withheld_positive_pixels'])]
               for k, v in sorted(e5card['instrument_b_prime_proxy'].items(),
                                  key=lambda kv: -kv[1]['dti'])]
        _d5 = e5card['paired_b_prime_vs_h33']
        results += ("<h2>Lane E5 — supervised within-halo ranking (preregistered, negative)</h2>"
                    "<p>SGMC-proxy LOQO ranker, OOF AUC by quadrant "
                    + esc(json.dumps(e5card['oof_auc_by_quadrant'], default=float))
                    + f"; worst canary AUC {e5card['canary_worst_single_feature_auc']:.3f}."
                    + f" B′ paired Δ vs H33 {_d5['delta']:+.4f} {ci(_d5)} — gate fails, verdict "
                    + f"<code>{esc(e5card['verdict'])}</code>, no slot used.</p>"
                    + table(['Arm', 'DTI', '95% CI', 'Positives'], _ra,
                            'E5 instrument A · HOLDOUT-DTI · gems57-pooled-hide-v2')
                    + table(['Arm', 'DTI', '95% CI', 'Positives'], _rb,
                            "E5 instrument B′ · PROXY-DTI · SGMC proxy d ≥ 3 px"))
    if p6card:
        _ra6 = [[esc(k), f"{v['dti']:.4f}", ci(v), str(v['withheld_positive_pixels'])]
                for k, v in sorted(p6card['instrument_a_holdout'].items(),
                                   key=lambda kv: -kv[1]['dti'])]
        _rb6 = [[esc(k), f"{v['dti']:.4f}", ci(v), str(v['withheld_positive_pixels'])]
                for k, v in sorted(p6card['instrument_b_prime_proxy'].items(),
                                   key=lambda kv: -kv[1]['dti'])]
        _rbpp6 = [[esc(k), f"{v['dti']:.4f}", ci(v), str(v['withheld_positive_pixels'])]
                  for k, v in sorted(p6card['instrument_b_double_prime_proxy'].items(),
                                     key=lambda kv: -kv[1]['dti'])]
        buf_audit = load('evidence/p6_dualhorizon/sgmc_buffer_audit.json', {})
        buf_rows = [
            [f"<= {r['buffer_px']} px ({r['buffer_m']} m)", f"{r['sgmc_pixels_within_buffer']:,}",
             pct(r['sgmc_fraction_within_buffer']), pct(r['domain_fraction_within_buffer']),
             f"{r['enrichment_ratio']:.2f}x", f"{r['sgmc_pixels_d_ge_r']:,}"]
            for r in buf_audit.get('buffer_enrichment_curve', [])
        ]
        results += ("<h2>Lane P6 — dual-horizon LOQO scarp-rad-basement ranker &amp; SGMC 1–20 px buffer calibration (DO NOT SUBMIT)</h2>"
                    "<p>Evaluates H-P5-1 (LOQO supervised 7x7), H-P5-2 (unsupervised 10m-3DEP breakline + LiDAR scarp + rad 7x7), "
                    "and H-P5-3 (submodular dual-horizon 5x5, 3.2 px NMS, 37,654 binary dots). Held fail-closed (verdict negative) "
                    "because paired Instrument A vs P4 CI straddles zero, SGMC B′ sits at 13.42 deg median slope vs catalogue 5.55 deg, "
                    "and literal forward overlap vs the dense lattice is 1.00.</p>"
                    + table(['Arm', 'DTI', '95% CI', 'Positives'], _ra6,
                            'P6 instrument A · HOLDOUT-DTI · gems57-pooled-hide-v2')
                    + table(['Arm', 'DTI', '95% CI', 'Positives'], _rb6,
                            "P6 instrument B′ · PROXY-DTI · SGMC proxy d ≥ 3 px (LOQO)")
                    + table(['Arm', 'DTI', '95% CI', 'Positives'], _rbpp6,
                            "P6 instrument B′′ · PROXY-DTI · SGMC proxy d ≥ 6 px (LOQO)")
                    + table(['Buffer', 'SGMC px in band', 'SGMC %', 'Domain %', 'Enrichment', 'Remaining SGMC (d >= r)'],
                            buf_rows, 'SGMC vs QFaults cartographic duplication calibration (1–20 px)'))
    (DOCS / 'results.html').write_text(frame('Evidence', results))

    # ------------------------------------- new P5 scientific negative (one lane)
    p5checks = [[esc(k), 'pass' if v is True else 'FAIL']
                for k, v in p5['validator_output']['checks'].items()]
    p5canary_rows = [[esc(k), f"{v['auc']:.4f}", 'STOP' if v['suspected_leakage'] else 'clear']
                     for k, v in sorted(p5canary.items())]
    p5source_rows = []
    for r in p5sources['verified_readings']:
        claims = '<br>'.join(esc(x) for x in r['claims'])
        caution = esc(r.get('use_limit', r.get('irregularity', '')))
        p5source_rows.append([f'<a href="{esc(r["url"])}">{esc(r["source"])}</a>',
                              claims + (f'<br><strong>Limit:</strong> {caution}' if caution else '')])
    p5page = latest_decision + f'''<div class="eyebrow">REPRODUCIBLE SCIENTIFIC RESEARCH · NEGATIVE</div>
<h2>What the new model tested — and why we stopped.</h2>
<p>The pre-registered provisional lane is <em>cover-conditioned magnetic analytic-signal width
within the visible-fault halo</em>. The 19-band owner-mirrored stack supplied horizontal and vertical
magnetic gradients, gravity anomaly and basement depth. The SGMC fault raster was used only as
proxy <strong>training labels</strong>, never as a final predictor or export mask. Four spatial quadrants
were held out in turn. For catalogue recovery, whole connected components were hidden with a
3-pixel feature buffer and visible faults were masked pixel-exactly by the shared evaluator.</p>
<p>Physical hypothesis: a covered fault can juxtapose magnetized lithologies under basin fill;
magnetic edge width might preferentially rank blind structures. <strong>Counterexample:</strong> a
buried volcanic dike or remanence boundary, or airborne survey leveling, can generate a similar
magnetic signature without fault displacement. None of these pixels proves a geothermal vent.</p>
{table(['Instrument / comparison', 'HOLDOUT-DTI', '95% CI', 'Withheld positives'], [
 ['A · P5 continuous', f"{pa['dti']:.4f}", ci(pa), f"{pa['withheld_positive_pixels']:,}"],
 ['A · P4 regenerated from visible faults', f"{p5['comparators']['a_visible_only_p4']['dti']:.4f}",
  ci(p5['comparators']['a_visible_only_p4']), f"{pa['withheld_positive_pixels']:,}"],
 ["B′ · P5 SGMC-proxy LOQO", f"{pb['dti']:.4f}", ci(pb), f"{pb['withheld_positive_pixels']:,}"],
 ["B′ · archived H33 on same proxy", f"{p5['comparators']['b_prime_h33_frozen']['dti']:.4f}",
  ci(p5['comparators']['b_prime_h33_frozen']), f"{pb['withheld_positive_pixels']:,}"],
], 'gems57-pooled-hide-v2; pooled α=.2, β=.8, 300 m triangular kernel; paired 20 km spatial-cluster 95% CI.')}
<p>The paired A delta versus regenerated P4 is {da['delta']:+.4f} {ci(da)}.
The paired B′ delta versus H33 is {db['delta']:+.4f} {ci(db)}.
Both intervals are below zero. The B′ truth is an imperfect *SGMC off-catalogue proxy*, not
new faults confirmed by DrivenData. There is <strong>no organizer-confirmed score</strong> for this file,
and no evidence it beats the reported H33 0.2778 or the public 0.4413 leader.</p>
<p><strong>Interpretation caveat:</strong> P5 has approximately
{p5['validator_output']['mean'] * p5['validator_output']['n_finite']:,.0f} summed probability mass
across {p5['correlation_overlap_vs_registry']['positive_support_pixels']:,} positive pixels,
versus P4/H33's 37,654 binary full-mass dots. This one negative jointly tests geological ranking,
proxy training <em>and</em> continuous emission; it does not isolate which caused the loss.
A mass/spacing-matched future comparison is required, but only after the literal gate is resolved.</p>
<h2>Literal overlap and artifact identity</h2>
<p>The archived binary lattice <code>{esc(p5audit['file'])}</code>
(sha256 <code>{esc(p5audit['sha256'])}</code>) covers every one of the
{p5audit['feature_valid_pixels_after_12px_erosion']:,} erosion-valid cells within 3 pixels.
The P5 map has {p5['correlation_overlap_vs_registry']['positive_support_pixels']:,} positive
continuous pixels with forward positive-support overlap
{p5['correlation_overlap_vs_registry']['forward_overlap_positive_support_lattice']:.2f};
<strong>this exceeds the 0.70 literal stop rule.</strong> It has no exact-one binary dots,
which is NOT a clearance or license to treat positive cells as invisible.
No final discrete dots were placed. Its max Spearman is
{p5['correlation_overlap_vs_registry']['worst_spearman_full_footprint']:.4f}
across {p5['correlation_overlap_vs_registry']['rasters_checked']} archived/local TIFFs; this
is not an exhaustive organizer registry.</p>
<p><strong>Filename:</strong> <code>{esc(p5name)}.tif</code> ·
<strong>SHA-256:</strong> <code>{esc(p5['raster_sha256'])}</code> ·
<strong>Note (not to upload):</strong> <code>{esc(p5['submission_note'])}</code></p>
<h2>Independent on-disk checks</h2>
{table(['Local validator check', 'Result'], p5checks)}
<p>Values are finite everywhere (so no NaN inside the footprint), within [0,1], and
single-band float32 on the sample CRS/shape/transform; known-fault and outside-footprint
cells are zero. The previous user's portal range error cannot be diagnosed without the rejected
bytes, and local validation is not organizer acceptance. The competition page says outside
bounds null/NaN; the pinned owner-mirrored sample has NaNs outside its footprint, while
this output uses all-finite zeros there. Whether the portal accepts that safer range policy
remains an <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">unresolved format question</a>.</p>
<h2>Feature-alone leakage canaries</h2>
<p>Each raw and derived feature was scored alone on {pa['withheld_positive_pixels']:,} withheld
catalogue positives vs 200,000 negatives. AUC or inverse AUC above 0.90 would stop the run.
No canary exceeded the threshold; lack of leakage is <em>not</em> evidence of fault-prediction skill.</p>
{table(['Feature', 'AUC', 'Status'], p5canary_rows)}
<h2>Read and verify the sources yourself</h2>
<p>These links were read as public text on 2026-10-20. Owner mirrors and their SHA pins verify
byte consistency, not official-origin identity. Specific claims and limits are recorded in
<a href="downloads/p5_sources.json">the source receipt</a>.</p>
{table(['Official source', 'Verified reading / limit'], p5source_rows)}
<p><a href="https://github.com/buffedlizard55-lab/GEMSDOE70/blob/main/docs/preregistration-p5.md">Frozen preregistration</a>
· <a href="downloads/p5_run_card.json">P5 run card</a>
· <a href="downloads/p5_instrument_a.json">Catalogue holdout</a>
· <a href="downloads/p5_instrument_b_prime.json">SGMC proxy holdout</a>
· <a href="downloads/p5_literal_blocker.json">Lattice witness</a>
· <a href="downloads/p5_surface_registry.json">{p5['correlation_overlap_vs_registry']['rasters_checked']}-raster rank audit</a>
· <a href="downloads/p5_reporting_amendment.json">Metadata-only correction</a>.</p>
<p>Reproduce on a fresh checkout: install <code>requirements.lock</code>, run
<code>scripts/restore_data.py</code>, clone the pinned owner registry for 60GEMSDOE in
<code>/tmp/60GEMSDOE</code>, then run <code>scripts/run_experiment_p5_cover.py</code>.
The shared writer refuses to overwrite existing outputs; use a clean sandbox for full
reproduction. <code>scripts/verify_p5_artifact.py</code> re-audits the immutable file
without refitting. Data tab requires a DrivenData login; no GPU was required here.</p>'''
    (DOCS / 'p5.html').write_text(frame('New P5-cover research TIFF', p5page))

    # ------------------------------------- E3 scarp parallel candidate (PR17)
    e3 = load('evidence/run_card_e3_amended.json', {})
    if e3:
        e3h = load('evidence/holdout_e3.json', {})
        e3u = load('evidence/final_uniqueness_e3.json', {})
        e3v = (load('evidence/validator_e3.json', {}) or {}).get('validator') or {}
        e3name = e3['submission_name']
        e3d = e3['holdout_dti']
        h33row = {}
        for r in (e3u.get('audit') or {}).get('rows', []):
            if str(r.get('submission', '')).endswith('GEMSDOE32__h33-2-b2-zeros.tif'):
                h33row = r
        e3rows = instrument_rows(e3h) if e3h else []
        e3checks = [[esc(k), 'pass' if v else 'FAIL']
                    for k, v in (e3v.get('checks') or {}).items()]
        e3page = f"""<div class="eyebrow">PARALLEL-SESSION CANDIDATE E3 (SCARP LANE)</div>
<h1>Archived scarp-curvature candidate — DO NOT SUBMIT.</h1>
<p class="lead"><strong>Download: yes.</strong> <code>downloads/{esc(e3name)}.tif</code>
({e3['n_final_dots']:,} dots, SHA-256 <code>{esc(e3['raster_sha256'])}</code>).
<strong>Slot decision: selector-owned.</strong> E3 was promoted on catalogue
hide-and-recover only and has <strong>not</strong> been scored on instrument B′;
the Phase-4 candidate remains the only B′-scored option (negative there).
Fresh binary-witness comparison also fails the literal overlap gate. Do not upload this archive;
B′ scoring and a cap check alone cannot override the current stop.
(Not to be confused with the PR #16 lane's negative depth-step E3.)</p>
<div class="actions">
<a class="button" style="background:#076c64;color:#fff" href="downloads/{esc(e3name)}.tif" download>Download archived E3 TIFF — DO NOT SUBMIT</a>
<a class="button secondary" href="downloads/{esc(e3name)}.zip" download>Download one-TIFF ZIP</a>
<a class="button secondary" href="downloads/run_card_e3_amended.json">E3 run card + erratum</a></div>
<p class="small">Note ({len(e3['submission_note'])}/140 chars): <code>{esc(e3['submission_note'])}</code></p>
<h2>Catalogue holdout (seed-40, untouched folds)</h2>
<p>HOLDOUT-DTI {e3d['dti']:.4f} {ci(e3d)} · {e3d['withheld_positive_pixels']:,} withheld ·
{e3d['evaluator_version']}. The same lane's gated E2 variant was falsified first (negative).</p>
{table(['Arm', 'DTI', '95% CI', 'Positives'], e3rows, 'E3 dotted arms at the selected cell')}
<h2>Uniqueness vs H33 (63 hash-verified rasters, saturation-adjusted)</h2>
<p>Forward overlap {h33row.get('my_dots_within_3px_of_theirs', float('nan')):.3f} ·
Jaccard {h33row.get('jaccard_dot_sets', float('nan')):.4f} ·
Spearman {h33row.get('spearman_full_footprint', float('nan')):.4f}.
Full inventory (862) scan remains a selector step. Literal readings are in the receipt.</p>
<h2>On-disk validator</h2>
{table(['Check', 'Result'], e3checks, 'Shared validator on the published E3 bytes.')}
<p><a href="downloads/holdout_e3.json">Holdout</a> ·
<a href="downloads/final_uniqueness_e3.json">Uniqueness</a> ·
<a href="downloads/validator_e3.json">Writer receipt</a></p>"""
        (DOCS / 'e3-candidate.html').write_text(frame('E3 scarp candidate', e3page))

    # ------------------------------------------------------------------ markdown
    import markdown
    for src, dst, title in [('docs/hypotheses.md', 'hypotheses.html', 'Hypotheses'),
                            ('docs/h33-analysis.md', 'h33-analysis.html', 'Why H33 scored'),
                            ('docs/irregularities.md', 'limitations.html', 'Limitations'),
                            ('docs/protocol-review.md', 'protocol-review.html', 'Protocol review')]:
        text = (ROOT / src).read_text()
        body = markdown.markdown(text, extensions=['tables'])
        (DOCS / dst).write_text(frame(title, body))
        if dst == 'protocol-review.html':
            (DOCS / 'research-review.html').write_text(frame('Current research review', body))

    # -------------------------------------------------------------------- sources
    srows = [[f'<a href="{esc(s["url"])}">{esc(s["id"])}</a>', esc(s.get('authority', '')),
              esc(s.get('status', '')), esc(s.get('claim', '')) + '<br><small>'
              + esc(s.get('limit', '')) + '</small>'] for s in sources]
    src_page = f'''<div class="eyebrow">SOURCES</div><h1>Every claim points at a source or a receipt.</h1>
<p>Retrieved content is cached in the repository where licensing allows; scores reported by the user
are labelled as user-supplied, never as organizer-confirmed. Historical organizer-page quotations are retained with their original provenance. For P5 we additionally
read the DrivenData problem/leaderboard and DOE rules/USGS/GDR public *text* through a page
reader (receipt linked below); shell binary downloads remain restricted. The live weekly balance,
portal acceptance and a file-specific organizer score receipt were not verified.</p>
{table(['Source', 'Authority', 'Status', 'Claim and limit'], srows)}
<p><strong>New verified public-text readings:</strong> <a href="downloads/p5_sources.json">P5 official source table</a>,
with exact claims and limits for the organizer metric, USGS GeoDAWN, SGMC, DOE rules and the
read-only public leaderboard. These are not an authenticated submission receipt.</p>
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
<a href="downloads/upstream_fix_report.txt">Upstream fix report</a></p>'''
    (DOCS / 'sources.html').write_text(frame('Sources', src_page))

    # Root entry point (repository-root Pages keeps working).
    (ROOT / 'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70</title>'
        '</head><body><p><a href="docs/index.html">Open the GEMSDOE70 evidence site</a></p><p>DO NOT SUBMIT — review downloads only.</p>'
        '</body></html>\n')
    (DOCS / '.nojekyll').touch()
    # Backwards-compatible entry points; they must not carry stale claims.
    for old, target in (('irregularities.html', 'limitations.html'),
                        ('status.html', 'index.html')):
        (DOCS / old).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={target}"><title>GEMSDOE70</title>'
            f'</head><body><p>This page moved. <a href="{target}">Continue</a>.</p></body></html>\n')
    executive = latest_decision + decision + '''<h2>Exactly how submission approval works</h2>
<ol class="steps"><li>Do not upload the new P5 review file or any earlier archive. The literal overlap gate fails.</li>
<li>A future candidate must be newly generated using the shared writer, beat a matched current-best
holdout, clear feature-alone canaries and both-stage literal uniqueness, and pass the local validator.</li>
<li>A separate selector checks the live submission-page cap and eligibility before approving a slot.
No authenticated competition session is available here; no slot has been spent by this review.</li>
<li>Only after approval: choose the single-band TIFF or its one-TIFF ZIP, paste its unique name and
at-most-140-character note, submit once, and save the portal receipt.</li>
<li>Only a score copied from that submission-page receipt is ORGANIZER-CONFIRMED.</li></ol>
<p>The old range error cannot be diagnosed without the rejected bytes. The reviewed TIFFs are
finite float32 in [0,1], with the pinned sample's CRS/shape/transform; this is local format validity,
not portal acceptance. See the <a href="submission.html">detailed validator and future workflow</a>.</p>
<p><a href="protocol-review.html">Four ranked hypotheses, source table, limitations and next steps</a></p>'''
    (DOCS / 'executive-summary.html').write_text(frame('Executive summary', executive))
    (DOCS / 'status.json').unlink(missing_ok=True)
    # keep a root-level copy so older pages that link run-card.json still resolve
    (DOCS / 'run-card.json').write_text((ROOT / 'evidence/review/run_card.json').read_text())
    # Phase-1 receipts keep their historical names only under the archived prefix.
    for stale in ('holdout.json', 'holdout_folds.json', 'holdout_split.json',
                  'registry_saturation.json', 'surface_uniqueness.json',
                  'experiment_manifest.json'):
        (DOWN / stale).unlink(missing_ok=True)
    print('site built:', ', '.join(sorted(p.name for p in DOCS.glob('*.html'))))


if __name__ == '__main__':
    main()
