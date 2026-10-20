#!/usr/bin/env python3
"""Build a fail-closed evidence site: archives never become submission buttons.

Scientific values are read from labelled historical receipts; the current
negative run card and independent literal-overlap audit control the banner.
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems70.release import (release_status, assert_no_public_rasters,
                            assert_no_public_release_claims)
DOCS = ROOT / 'docs'
DOWN = DOCS / 'downloads'

NAV = [('index.html', 'Overview'), ('executive-summary.html', 'Executive summary'),
       ('submission.html', 'How to submit'),
       ('results.html', 'Evidence'), ('hypotheses-next.html', 'Next hypotheses'),
       ('hypotheses.html', 'Earlier hypotheses'),
       ('h33-analysis.html', 'H33 archive analysis'), ('sources.html', 'Sources'),
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
<span class="edition">AUDIT UPDATE · 2026-10-20 · DO NOT SUBMIT</span></header>
<nav aria-label="Main">{nav}</nav><main id="main">{body}</main>
<footer>DO NOT SUBMIT this run. Historical results are labelled; no organizer-confirmed receipt exists.
<a href="downloads/run_card.json">Current negative run card</a> ·
<a href="downloads/literal_overlap_stop.json">Recomputed literal stop</a> ·
<a href="downloads/phase4_run_card.json">Historical P4 card</a> ·
<a href="sources.html">Official sources</a></footer></body></html>'''


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
    assert_no_public_rasters(ROOT)
    assert_no_public_release_claims(ROOT)
    current = load('evidence/run_card.json', {})
    card = load('evidence/phase4/run_card.json', {})  # historical, NEVER current
    stop = load('evidence/literal_overlap_stop.json', {})
    status = release_status(ROOT)
    if (not current or not card or not stop or not status['evidence_consistent']
            or status['download_ok'] or status['submit_recommended']
            or status['archive_review'] is None):
        raise SystemExit('Incomplete negative release evidence; refusing to publish a submission link')
    name = card['submission_name']
    sha = card['raster_sha256']
    val = card.get('validator_output') or {}
    checks = val.get('checks') or {}
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
    # Publish the same dated source inventory as the rendered table; otherwise
    # docs/sources.json silently retains an obsolete claim after a rebuild.
    shutil.copyfile(ROOT / 'registry/sources.json', DOCS / 'sources.json')

    # ------------------------------------------------------------- copy evidence
    copies = {
        'evidence/run_card.json': 'run_card.json',
        'evidence/literal_overlap_stop.json': 'literal_overlap_stop.json',
        'evidence/publication_retractions.json': 'publication_retractions.json',
        'evidence/phase4/run_card.json': 'phase4_run_card.json',
        'evidence/inherited_band_metadata.json': 'band_metadata.json',
        # Old mutual-overlap audit says 'promote-to-selector-only'; it is
        # superseded by the current forward stop and stays in private evidence/.
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
        'evidence/history/h2_stepover_negative/run_card.json': 'h2_stepover_run_card.json',
        'evidence/e2/run_card.json': 'e2_run_card.json',
        'evidence/e2/holdout.json': 'e2_holdout.json',
        'evidence/e2/canaries.json': 'e2_canaries.json',
        'evidence/e2/holdout_confirm_seed21.json': 'e2_confirm_seed21.json',
        'evidence/e2/final_uniqueness.json': 'e2_final_uniqueness.json',
        # E2's old selector-review publication receipt is private historical
        # evidence; its affirmative download flag was superseded by the
        # binary-witness forward stop. Do not mirror it to public Pages JSON.
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
    archive_row = stop['archive_checks'][0]
    cover = stop['coverage']
    decision = f'''<section class="stop" aria-labelledby="decision">
<div class="eyebrow">CURRENT SUBMISSION STATUS · NEGATIVE</div>
<h1 id="decision">DO NOT SUBMIT — no eligible new GeoTIFF.</h1>
<p><strong>Download a new submission file: NO.</strong> <strong>Use a weekly slot: NO.</strong>
No new surface, spatial holdout, final dots or TIFF were generated this run. The required
single-method lane paragraph is absent from the prompt. We will not invent a lane or present
an old raster as a new result.</p>
<p>A hash-verified binary registry raster already places <strong>{archive_row['forward_overlap_within_3px']:.0%}
 of the historical P4 dots</strong> within 3 pixels of its dots — above your 70% forward-overlap stop.
The older site's mutual-overlap exception does not override your instruction. Its TIFF passes local
format checks but <strong>is not cleared for a competition upload</strong>.</p>
<div class="actions"><a class="button secondary" href="executive-summary.html">Read the submission decision and steps</a>
<a class="button secondary" href="downloads/run_card.json">Download current negative run card</a></div>
<p class="small">Measured against one verified registry witness, not a complete registry clearance.
No organizer-confirmed score or weekly-slot receipt exists. {esc(current['verdict'])} result;
<a href="downloads/literal_overlap_stop.json">reproducible witness and hashes</a>.</p></section>'''

    # ------------------------------------------------------------------ overview
    a = p4a['scores'] if p4a else {}
    b = p4b['scores'] if p4b else {}
    ball = p4ball['scores'] if p4ball else {}
    metrics = f'''<div class="metrics">
<section><div class="eyebrow">HISTORICAL P4 · HOLDOUT-DTI</div>
<div class="number">{a['candidate']['dti']:.4f}</div>
<p>gems57-pooled-hide-v2 · 95% CI {ci(a['candidate'])} · {a['candidate']['withheld_positive_pixels']:,} withheld catalogue positives</p></section>
<section><div class="eyebrow">HISTORICAL P4 · SGMC PROXY (NOT A HOLDOUT)</div>
<div class="number">{b['candidate']['dti']:.4f}</div>
<p>Proxy-DTI · 95% CI {ci(b['candidate'])} · not organizer-confirmed</p></section>
<section><div class="eyebrow">HISTORICAL P4 · FORWARD DOT OVERLAP</div>
<div class="number">{archive_row['forward_overlap_within_3px']:.0%}</div>
<p>One SHA-verified binary registry witness · user stop threshold &gt;70% · <strong>STOP</strong></p></section></div>'''

    index = decision + f'''<section class="intro"><div class="eyebrow">WHAT WE KNOW</div>
<h2>The portal format check passed on an older TIFF. The protocol did not.</h2>
<p>The archived P4 field has a verified SHA-256 and satisfies the local float32/[0,1]/grid validator;
that is <em>not</em> an organizer submission receipt or uniqueness clearance. It also failed a
historical target-like proxy comparison with H33. The new byte-level overlap audit rejects it
under your literal forward-dot rule. No candidate was selected in this review.</p>
</section>{metrics}
<div class="columns">
<section class="panel"><h2>Measured stop, not a universal impossibility claim</h2>
<p>The binary registry witness covers {cover['witness_halo_fraction_off_catalogue']:.3%} of
{cover['off_catalogue_cells']:,} eligible off-catalogue cells within 3 pixels. It leaves
{cover['witness_halo_uncovered_off_catalogue']:,} cells uncovered, not zero. At P4's
{archive_row['binary_dots']:,}-dot budget, even optimally putting all uncovered cells first still
gives at least {cover['min_possible_forward_overlap_at_archived_budget']:.3%} forward overlap;
its measured value is {archive_row['forward_overlap_within_3px']:.0%}.
A smaller budget is not automatically unique or competitive.</p>
<a href="downloads/literal_overlap_stop.json">Inspect counts and pins →</a></section>
<section class="panel"><h2>Why the historical holdout is not enough</h2>
<p>HOLDOUT-DTI {a['candidate']['dti']:.4f} {ci(a['candidate'])} ({a['candidate']['withheld_positive_pixels']:,}
withheld positives; gems57-pooled-hide-v2) measures catalogue recovery. A separate SGMC proxy
favoured the H33 reference over P4: proxy difference {p4b['paired_differences']['h33_reference']['delta']:+.4f}
(95% CI {ci(p4b['paired_differences']['h33_reference'])}). Neither observes the hidden labels.
</p><a href="results.html">Historical measurements →</a></section></div>
<section><h2>Manual review links, not a submission button</h2>
<ul><li><a href="h33-analysis.html">H33 byte-level explanation and its score caveat</a></li>
<li><a href="hypotheses-next.html">Four untried, ranked geological hypotheses</a></li>
<li><a href="sources.html">Official sources and availability</a></li>
<li><a href="limitations.html">Irregularities, limitations and next steps</a></li></ul></section>
<section class="panel"><h2>Historical TIFF — for forensic review ONLY · DO NOT SUBMIT</h2>
<p>Previously published P4 · <code>{esc(archive_row['sha256'])}</code>. Kept byte-for-byte as
negative evidence, not generated in this run. Its old 37,654-dot result is not unique under the
current forward-dot stop. Do not use it in the competition upload form.</p>
<a class="button secondary" href="downloads/{esc(name)}.tif" download>Download P4 archive for review only — DO NOT SUBMIT</a>
<a class="button secondary" href="downloads/phase4_run_card.json">Historical card</a></section>'''

    # ------------------------------------------- parallel E2/E3 lane (integrated)
    e2card = load('evidence/e2/run_card.json', {})
    e2pub = load('evidence/e2/publication.json', {})
    e2hold = load('evidence/e2/holdout.json', {})
    e3card = load('evidence/e3/run_card.json', {})
    e2_section = ''
    if e2card and e2pub:
        _d = e2card['holdout_dti']
        e2_section = f"""<section class="panel"><h2>Historical E2 archive — DO NOT SUBMIT</h2>
<p>E2 used an independent preregistered alluvial-step lane, but failed its frozen D28 comparison.
HOLDOUT-DTI gems57-pooled-hide-v2: {_d['dti']:.4f} (95% CI {ci(_d)},
{_d['withheld_positive_pixels']:,} withheld catalogue positives). Its archived final dots also
have {stop['archive_checks'][1]['forward_overlap_within_3px']:.0%} forward overlap against the
same pinned registry witness, above the 70% stop. It is not a new or eligible submission.
</p><a class="button secondary" href="downloads/{esc(e2pub.get('file',''))}" download>
Download E2 archive for review only — DO NOT SUBMIT</a>
<a href="downloads/e2_run_card.json">Historical E2 run card</a>.</section>"""
    (DOCS / 'index.html').write_text(frame('Overview', index + e2_section))

    # ------------------------------------------------------------- submit guide
    summary = decision + f"""<section class="intro"><h2>Executive summary: what you can do now</h2>
<p><strong>Not available: an eligible new TIFF.</strong> Do not select an old file from the
archive as if it were this run's submission. Archived P4/E2 are hash-pinned local format
checks, but each fails the forward-overlap stop in <a href="downloads/literal_overlap_stop.json">
the independent receipt</a>. No new HOLDOUT-DTI, feature-alone canaries or organizer-confirmed
score was produced.</p><p>Read <a href="submission.html">the full upload procedure</a> for the day a future
candidate clears every gate; then a separate selector checks the live account's remaining weekly
allowance. The official rules allow <em>up to three submissions per week</em>, not three automatic
uploads per research session.</p></section>
<section class="panel"><h2>Scientific path to a future file</h2><ol>
<li>Assign the missing single-method lane; preregister one of the <a href="hypotheses-next.html">
untested hypotheses</a> on untouched spatial blocks.</li>
<li>Restore SHA-pinned features; canary every feature (AUC &gt;0.90 is suspected leakage),
hide buffered whole fault segments, rebuild catalogue features only from visible segments,
mask visible faults pixel-exactly, and compare pooled HOLDOUT-DTI + paired 95% CI against
a same-split current best.</li>
<li>Before dots, check the surface against the accessible registry; after dots, check again.
Stop on ρ &gt;0.90 or forward dot overlap &gt;0.70 against ANY one raster.
The inherited mutual-overlap exception is not permission to bypass this rule.</li>
<li>Only then use the shared submission writer and validate the exact file bytes:
float32, one band, EPSG:32611, 3730 × 3292, pinned transform and finite values in [0,1]
inside the footprint; no positive mapped-fault pixels. No organizer acceptance is claimed until a portal receipt exists.</li>
</ol></section>"""
    (DOCS / 'executive-summary.html').write_text(frame('Executive summary', summary))

    historical_checks = archive_row['shared_validator']['checks']
    vrows = [[esc(k), 'pass' if v else 'FAIL'] for k, v in historical_checks.items()]
    guide = decision + f"""<div class="eyebrow">SUBMISSION GUIDE — STOPPED THIS RUN</div>
<h1>How to upload a future cleared GeoTIFF (not an archived one)</h1>
<p class="lead">Currently there is <strong>no eligible filename, submission name or note</strong>
for this run. A button labelled "Download eligible submission TIFF" must not appear until
holdout, uniqueness on both stages, exact-byte validation and separate slot selection pass.</p>
<section><h2>Steps when a future candidate is approved</h2><ol class="steps">
<li>Confirm the status says <strong>download OK, submit recommended YES</strong> and inspect the
current run card. Check the proposed file's SHA-256 and the note is at most 140 characters.</li>
<li>Download the single-band <code>.tif</code> file (or a one-TIFF <code>.zip</code>, never both).
Compare its SHA-256 to the recorded byte-level validator; check CRS, shape, transform, finite
in-footprint values in [0,1] and the exact grid used in the contest sample.</li>
<li>Sign in and enroll at the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData
competition</a>. Open <em>Submit → Make new submission</em>. Confirm the account's
remaining weekly allowance and rules; this website cannot see that private status.</li>
<li>In <em>File to submit</em>, select only the approved new TIFF (or the corresponding one-TIFF ZIP).
Paste its unique short note into <em>Note (optional)</em>, then submit once.</li>
<li>Save the submission-page receipt (filename, timestamp, note and actual returned score).
Only that receipt permits <code>ORGANIZER-CONFIRMED</code> for the specific file. Before any
prize narrative, disclose any generative-AI assistance as required by the
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">September 2026 official rules, §3.2</a>.</li>
</ol></section>
<section class="panel"><h2>About the earlier '[0,1]' rejection</h2>
<p>According to the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">
official submission-format page</a>, the one float32 band must contain prediction values
in [0,1] on the target grid. The shared writer refuses non-finite and out-of-range input
instead of clipping it; the validator reopens the written file. An older archive below
passes the <em>local</em> byte check, but the portal has not accepted this run's file because
there is no new file. We cannot inspect the earlier rejected upload, so we cannot identify
whether its cause was a negative nodata sentinel, NaNs, or another value.</p>
<p>The official page says data outside bounds should be null/NaN; the conservative local
writer uses all-finite zeros outside the sample-defined footprint. Portal acceptance of
this difference has not been demonstrated here. File format does not override the
scientific and duplicate gates.</p></section>
<section><h2>Historical P4 file, for format education ONLY — DO NOT SUBMIT</h2>
<p><code>{esc(name)}.tif</code> · SHA-256 <code>{esc(archive_row['sha256'])}</code> ·
forward overlap {archive_row['forward_overlap_within_3px']:.0%} &gt; 70% stop.
These checks belong to an older run, not a newly generated submission.</p>
{table(['Historical local-validator check', 'Result'], vrows, 'Historical shared-validator receipt; NOT a submission permission')}
<p><a href="downloads/phase4_run_card.json">Older run card</a> ·
<a href="downloads/run_card.json">Current negative run card</a> ·
<a href="downloads/literal_overlap_stop.json">SHA-verified witness</a></p></section>"""
    (DOCS / 'submission.html').write_text(frame('How to submit', guide))

    # ------------------------------------------------------------------- results
    rows_a = instrument_rows(p4a)
    rows_bp = instrument_rows(p4b)
    rows_ball = instrument_rows(p4ball)
    ablate = []
    for tag, d in (('HOLDOUT-DTI A · shared holdout', p3a), ('PROXY-DTI B′ · SGMC', p3b), ('PROXY-DTI B · unrestricted SGMC', p3ball)):
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
        classification = 'HOLDOUT-DTI' if tag.endswith(' A') else 'PROXY-DTI'
        history.append([esc(f'{tag} · {classification}'), f"{cand['dti']:.4f}", ci(cand),
                        f"{ref['dti']:.4f}" if ref else '—'])
    results = f'''<div class="eyebrow">HISTORICAL EVIDENCE — DO NOT SUBMIT</div>
<h1>Earlier experiments are evidence, not a new result.</h1>
<p>This run made <strong>no</strong> new HOLDOUT-DTI measurement. Historical catalogue HOLDOUT-DTI
is from gems57-pooled-hide-v2, α = 0.2, β = 0.8, 300 m triangular kernel, pooled terms and
paired 20 km spatial-cluster bootstrap; SGMC B/B′ values are separately labelled proxy-DTI.
Neither type is a score for a hidden organizer test set.</p>
<p><strong>Correction to the old mutual-overlap conclusion.</strong> The pinned
<code>calib_r13lattice_00904.tif</code> (206,895 binary dots) covers
{cover['witness_halo_fraction_off_catalogue']:.3%}, not 100%, of off-catalogue cells
within 3 px. It covers {archive_row['forward_overlap_within_3px']:.0%} of P4's actual dots.
That exceeds the user's forward-only &gt;70% stop, although the older mutual check passed.
<a href="downloads/literal_overlap_stop.json">Recomputed receipt</a>.</p>
<h2>Archived Phase 4 candidate (NOT cleared)</h2>
{table(['Arm', 'HOLDOUT-DTI', '95% CI', 'Withheld positives'], rows_a, 'Historical A · gems57-pooled-hide-v2, buffered whole-catalogue holdout')}
{table(['Arm', 'PROXY-DTI', '95% CI', 'Proxy positives'], rows_bp, "Historical B′ · SGMC proxy, d ≥ 3 px; NOT a catalogue holdout")}
{table(['Arm', 'PROXY-DTI', '95% CI', 'Proxy positives'], rows_ball, 'Historical B · unrestricted SGMC proxy (map-duplication risk)')}
<h2>Historical experiment 3 ablations</h2>
{table(['Instrument / evidence class', 'Arm', 'DTI', '95% CI'], ablate, 'HOLDOUT-DTI A or SGMC proxy B/B′; not organizer-confirmed.')}
<h2>Historical feature-alone leakage canaries (NOT rerun here)</h2>
{table(['Feature', 'AUC (held-out)', 'Result'], canary_rows, '11,321 withheld catalogue positives vs 200,000 negatives (earlier run); AUC > 0.90 would stop.')}
<h2>Historical experiment sequence</h2>
{table(['Run / evidence class', 'Candidate DTI', '95% CI', 'H33 DTI'], history)}
<p><a href="downloads/phase4_run_card.json">Historical P4 card</a> ·
<a href="downloads/run_card.json">Current negative card</a> ·
<a href="downloads/literal_overlap_stop.json">New forward-overlap stop (supersedes old mutual audit)</a> ·
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
                    + table(['Arm', 'HOLDOUT-DTI', '95% CI', 'Withheld positives'], _rows,
                            'Historical E2 · gems57-pooled-hide-v2 · seed-20'))
    (DOCS / 'results.html').write_text(frame('Evidence', decision + results))

    # ------------------------------------------------------------------ markdown
    import markdown
    for src, dst, title in [('docs/hypotheses.md', 'hypotheses.html', 'Earlier hypotheses'),
                            ('docs/hypotheses-next.md', 'hypotheses-next.html', 'Next hypotheses'),
                            ('docs/h33-analysis.md', 'h33-analysis.html', 'H33 archive analysis'),
                            ('docs/irregularities.md', 'limitations.html', 'Limitations')]:
        text = (ROOT / src).read_text()
        body = markdown.markdown(text, extensions=['tables'])
        (DOCS / dst).write_text(frame(title, body))

    # -------------------------------------------------------------------- sources
    srows = [[f'<a href="{esc(s["url"])}">{esc(s["id"])}</a>', esc(s.get('authority', '')),
              esc(s.get('status', '')), esc(s.get('claim', '')) + '<br><small>'
              + esc(s.get('limit', '')) + '</small>'] for s in sources]
    src_page = f'''<div class="eyebrow">SOURCES</div><h1>Every claim points at a source or a receipt.</h1>
<p>Public organizer/USGS/GDR pages were read via the research-page tool on 2026-10-20;
this is a dated snapshot, not a live score feed or an authenticated submission-page receipt.
The account data tab redirects to login and direct shell downloads from non-GitHub hosts
are blocked here. Public owner mirrors are hash-verified, not organizer-authenticated.</p>
<p>At the dated public-leaderboard read, the top displayed value was
<code>0.4413</code> — a <strong>PUBLIC-LEADERBOARD-OBSERVATION</strong>, NOT an
ORGANIZER-CONFIRMED score for this or H33's TIFF. See
<a href="downloads/leaderboard_read.json">the time-stamped receipt</a>.</p>
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
<a href="downloads/upstream_fix_report.txt">Historical upstream fix report (plain text)</a></p>'''
    (DOCS / 'sources.html').write_text(frame('Sources', src_page))

    # Root entry point (repository-root Pages keeps working).
    (ROOT / 'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE70 · DO NOT SUBMIT</title>'
        '</head><body><h1>DO NOT SUBMIT</h1>'
        '<p>No eligible new TIFF. <a href="docs/index.html">Open the audited evidence site</a>.</p>'
        '</body></html>\n')
    (DOCS / '.nojekyll').touch()
    # Backwards-compatible entry points; they must not carry stale claims.
    for old, target in (('irregularities.html', 'limitations.html'),
                        ('status.html', 'index.html')):
        (DOCS / old).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={target}"><title>GEMSDOE70 · DO NOT SUBMIT</title>'
            f'</head><body><h1>DO NOT SUBMIT</h1><p>This page moved. '
            f'<a href="{target}">Continue</a>.</p></body></html>\n')
    (DOCS / 'status.json').unlink(missing_ok=True)
    # keep a root-level copy so older pages that link run-card.json still resolve
    (DOCS / 'run-card.json').write_text((ROOT / 'evidence/run_card.json').read_text())
    # Phase-1 receipts keep their historical names only under the archived prefix.
    for stale in ('holdout.json', 'holdout_folds.json', 'holdout_split.json',
                  'registry_saturation.json', 'surface_uniqueness.json',
                  'experiment_manifest.json'):
        (DOWN / stale).unlink(missing_ok=True)
    assert_no_public_release_claims(ROOT)
    print('site built:', ', '.join(sorted(p.name for p in DOCS.glob('*.html'))))


if __name__ == '__main__':
    main()
