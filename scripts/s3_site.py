"""Session-3 site fragments, built only from evidence/s3/** receipts (no hand-typed numbers).

Kept separate from build_site.py so parallel sessions can keep editing the main builder
without conflicting with this lane. Every function returns '' when its evidence is absent.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COPIES = {
    'evidence/s3/run_card.json': 's3_run_card.json',
    'evidence/s3/run_card_raw.json': 's3_run_card_raw.json',
    'evidence/s3/proxy_calibration.json': 's3_proxy_calibration.json',
    'evidence/s3/terrain_marginals.json': 's3_terrain_marginals.json',
    'evidence/s3/canaries.json': 's3_canaries.json',
    'evidence/s3/instrumentB_prime.json': 's3_instrumentB_prime.json',
    'evidence/s3/instrumentA_holdout.json': 's3_instrumentA_holdout.json',
    'evidence/s3/uniqueness.json': 's3_uniqueness.json',
    'evidence/s3/surface_uniqueness.json': 's3_surface_uniqueness.json',
    'evidence/s3/sibling_uniqueness.json': 's3_sibling_uniqueness.json',
    'evidence/s3/loqo_folds.json': 's3_loqo_folds.json',
    'evidence/s3/e2/run_card.json': 's3e2_run_card.json',
    'evidence/s3/e2/instrumentB_prime.json': 's3e2_instrumentB_prime.json',
    'evidence/s3/e2/instrumentA_holdout.json': 's3e2_instrumentA_holdout.json',
    'evidence/s3/e2/uniqueness.json': 's3e2_uniqueness.json',
    'evidence/s3/e2/strata.json': 's3e2_strata.json',
}
NAV_ENTRY = ('s3-findings.html', 'Session 3')
MARKDOWN = ('docs/s3-findings.md', 's3-findings.html', 'Session 3')


def _load(rel):
    p = ROOT / rel
    return json.loads(p.read_text()) if p.is_file() else None


def esc(x):
    return html.escape(str(x))


def ci(d):
    return f"[{d['ci95'][0]:.4f}, {d['ci95'][1]:.4f}]"


def _table(headers, rows, caption):
    head = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return (f'<div class="table-wrap"><table><caption>{esc(caption)}</caption><thead><tr>{head}</tr>'
            f'</thead><tbody>{body}</tbody></table></div>')


def _cards():
    e1, e2, cal = (_load('evidence/s3/run_card.json'), _load('evidence/s3/e2/run_card.json'),
                   _load('evidence/s3/proxy_calibration.json'))
    return (e1, e2, cal) if (e1 and e2 and cal) else (None, None, None)


def banner():
    """Landing-page block: the per-file download/submit decision for Session 3."""
    e1, e2, cal = _cards()
    if not e1:
        return ''
    tm = {r['label']: r for r in (_load('evidence/s3/terrain_marginals.json') or {}).get('rows', [])}
    e1s = tm.get('S3-E1 (this session)', {}).get('frac_steep_top_quartile', float('nan'))
    gos = tm.get('gate_ortho (reported 0.2376)', {}).get('frac_steep_top_quartile', float('nan'))
    d1 = e1['paired_b_prime']['h33_reference']
    d2 = e2['paired_b_prime']['random_stratified']
    u1 = e1['correlation_overlap_vs_registry']
    rows = [
        [f'<a href="downloads/{esc(Path(e1["artifact"]).name)}" download><code>{esc(Path(e1["artifact"]).name)}</code></a>',
         'E1 · proxy-trained ranking, H33 spacing', 'yes', '<strong>NO</strong>',
         f"Passed its pre-registered proxy gate (B′ Δ vs H33 {d1['delta']:+.4f}, CI {ci(d1)}) but "
         f"<strong>vetoed</strong>: offline B′ does not track the live board (ρ = {cal['spearman_live_vs_b_prime']:.2f}, "
         f"n = {cal['n']}); {100 * e1s:.0f} % of its dots are in the steepest terrain quartile, like the "
         f"live-tested gate_ortho file ({100 * gos:.0f} %, reported 0.2376 &lt; 0.2778)."],
        [f'<a href="downloads/{esc(Path(e2["artifact"]).name)}" download><code>{esc(Path(e2["artifact"]).name)}</code></a>',
         'E2 · same model, ranking only within H33 distance × slope strata', 'yes', '<strong>NO</strong>',
         f"Negative: no significant gain over random placement within the same strata "
         f"(B′ Δ {d2['delta']:+.4f}, CI {ci(d2)})."],
    ]
    return f'''<section class="stop" aria-labelledby="s3">
<div class="eyebrow">SESSION 3 · SUPERVISED PROXY RANKING · DECISION</div>
<h2 id="s3">Session 3 files: download for review — do NOT submit</h2>
<p>Both files pass the shared validator (single band, float32, 3730 × 3292, EPSG:32611, values
exactly 0/1, no NaN, 37,654 dots) and are unique under the mutual rule against
{u1['final_rasters_checked']} archived rasters and every sibling TIFF in this repository (worst mutual
overlap {u1['final_worst_mutual_overlap']:.2f}). Under the <em>literal</em> forward-overlap rule they
reach {u1['final_worst_forward_overlap']:.2f} against the dense r13 lattice, like every dot file here.
<strong>Neither is evidence of a live score above 0.2778.</strong> Weekly slots used: 0.</p>
{_table(['File', 'What it is', 'Download', 'Submit', 'Why'], rows, 'Session 3 · download vs submit')}
<p class="small"><a href="s3-findings.html">Session 3 findings and live-board calibration table</a> ·
<a href="downloads/s3_run_card.json">E1 run card</a> · <a href="downloads/s3e2_run_card.json">E2 run card</a> ·
<a href="downloads/s3_proxy_calibration.json">calibration receipt</a> ·
<a href="downloads/s3_sibling_uniqueness.json">sibling uniqueness</a></p></section>'''


def guide_note():
    e1, e2, _ = _cards()
    if not e1:
        return ''
    return f'''<section class="stop"><div class="eyebrow">SESSION 3 FILES</div>
<h2>The two Session 3 files are not upload candidates.</h2>
<p>They carry <code>DO-NOT-SUBMIT</code> in their names on purpose (E1 vetoed, E2 negative). Their
names and notes are recorded only for audit: <code>{esc(e1['submission_name'])}</code> /
<code>{esc(e1['submission_note'])}</code>; <code>{esc(e2['submission_name'])}</code> /
<code>{esc(e2['submission_note'])}</code>. See <a href="s3-findings.html">Session 3 findings</a>.</p></section>'''


def results_block(instrument_rows, table):
    e1, e2, _ = _cards()
    if not e1:
        return ''
    b1, a1, b2 = (_load('evidence/s3/instrumentB_prime.json'), _load('evidence/s3/instrumentA_holdout.json'),
                  _load('evidence/s3/e2/instrumentB_prime.json'))
    return ('<h2>Session 3 — supervised proxy ranking (E1 vetoed, E2 negative)</h2>'
            '<p>Pre-registered in <code>docs/preregistration-s3.md</code> and <code>docs/preregistration-s3-e2.md</code>; '
            'leave-one-quadrant-out out-of-fold B′. E1 rule outcome promote, final negative after the calibration veto.</p>'
            + table(['Arm', 'DTI', '95% CI', 'Positives'], instrument_rows(b1), 'S3-E1 · Instrument B′ (OOF)')
            + table(['Arm', 'DTI', '95% CI', 'Positives'], instrument_rows(a1), 'S3-E1 · Instrument A (diagnostic)')
            + table(['Arm', 'DTI', '95% CI', 'Positives'], instrument_rows(b2),
                    'S3-E2 · Instrument B′ (the s3_e1_candidate row is the in-sample production file; not comparable)')
            + '<p><a href="s3-findings.html">Calibration table and discussion →</a></p>')


def readme_block():
    e1, e2, cal = _cards()
    if not e1:
        return ''
    d1 = e1['paired_b_prime']['h33_reference']
    d2 = e2['paired_b_prime']['random_stratified']
    return f'''## Session 3 (branch arena/a0382202): supervised proxy ranking — **download for review, do NOT submit**

| File | Download | Submit | Why |
|---|---|---|---|
| [`{Path(e1['artifact']).name}`]({e1['artifact']}) | yes | **NO** | E1: pre-registered proxy gate passed (B′ Δ vs H33 {d1['delta']:+.4f}, 95 % CI [{d1['ci95'][0]:+.4f}, {d1['ci95'][1]:+.4f}]) but **vetoed** — offline B′ does not track the live board (Spearman {cal['spearman_live_vs_b_prime']:.2f}, n = {cal['n']}) and the gain is confounded with steep terrain |
| [`{Path(e2['artifact']).name}`]({e2['artifact']}) | yes | **NO** | E2: negative — within H33's distance × slope strata, no gain over random placement (B′ Δ {d2['delta']:+.4f}, CI [{d2['ci95'][0]:+.4f}, {d2['ci95'][1]:+.4f}]) |

Key finding for every lane: the offline instruments (B′ and A) do not order the 18 archived files
with reported live scores the way the board did (Spearman {cal['spearman_live_vs_b_prime']:.2f} and
{cal['spearman_live_vs_a']:.2f}). [Findings](docs/s3-findings.md) · [E1 card](evidence/s3/run_card.json) ·
[E2 card](evidence/s3/e2/run_card.json) · [calibration](evidence/s3/proxy_calibration.json) ·
preregistrations [S3](docs/preregistration-s3.md), [S3-E2](docs/preregistration-s3-e2.md).

'''
