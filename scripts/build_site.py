#!/usr/bin/env python3
"""Build a static, negative-only Pages report. No scientific artifacts are published."""
from __future__ import annotations
import html
import json
from pathlib import Path
import sys
import re
import markdown
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from release_gate import status

NAV = [('index.html','Overview'), ('executive-summary.html','Submission guide'),
       ('research.html','Research'), ('sources.html','Sources'), ('review.html','Audit'),
       ('requirements.html','Requirements'), ('run-card.html','Run card')]
CSS = '''
:root{--bg:#f5f7f9;--ink:#183037;--muted:#53656d;--teal:#006c64;--line:#d7e1e4;--warn:#8c351c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--teal);text-underline-offset:3px}a:hover{color:#043e3a}a:focus-visible{outline:3px solid #cf6100;outline-offset:4px}
header{background:#fff;border-bottom:1px solid var(--line)}.top{max-width:1180px;margin:auto;padding:22px 30px;display:flex;align-items:center;gap:26px;justify-content:space-between}.brand{text-decoration:none;color:var(--ink);font-weight:800;letter-spacing:-.04em;font-size:24px}.brand span{color:var(--teal)}nav{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}nav a{text-decoration:none;color:var(--muted)}nav a[aria-current=page]{color:var(--teal);font-weight:750;border-bottom:2px solid var(--teal)}
main{max-width:1120px;margin:0 auto;padding:34px 30px 70px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:var(--teal);font-size:12px;font-weight:800}h1{font-size:clamp(30px,5vw,50px);line-height:1.15;letter-spacing:-.045em;margin:18px 0 24px}h2{font-size:26px;letter-spacing:-.025em;margin-top:38px}h3{font-size:20px}p{max-width:85ch}.lead{font-size:20px;color:var(--muted);max-width:800px}.alert{background:#fff3ea;border:1px solid #e5b79a;border-left:5px solid #a34223;border-radius:8px;padding:22px 26px;margin:18px 0 30px}.alert strong{color:var(--warn);font-size:19px}.alert p{margin:7px 0 0}.pill{font-size:12px;font-weight:800;letter-spacing:.08em;border-radius:6px;background:#fce5d7;color:#81351d;padding:6px 10px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:28px 0}.card{padding:24px;background:#fff;border:1px solid var(--line);border-radius:12px}.card h2{margin:0 0 8px;font-size:19px}.stat{font-size:30px;font-weight:800;letter-spacing:-.03em}.muted{color:var(--muted)}.button{display:inline-block;background:var(--teal);color:#fff!important;padding:11px 17px;border-radius:7px;text-decoration:none;font-size:14px;font-weight:700;margin:8px 10px 8px 0}.button.secondary{background:#fff;color:var(--teal)!important;border:1px solid var(--line)}
article{background:#fff;border:1px solid var(--line);border-radius:12px;padding:28px 32px;overflow-wrap:anywhere}article h1{font-size:34px}article>h1:first-child{margin-top:0}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:20px 0}table{width:100%;border-collapse:collapse;font-size:14px;min-width:650px}th,td{text-align:left;padding:13px 15px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#eef5f4}tr:last-child td{border-bottom:0}pre{overflow:auto;background:#eef3f5;border-radius:8px;padding:18px;font-size:13px}code{background:#edf2f3;border-radius:3px;padding:.12em .3em;font-size:.88em}pre code{background:transparent;padding:0}blockquote{border-left:3px solid #91b9b1;padding-left:18px;color:var(--muted)}li{margin:6px 0}.proof{border:1px solid #b5d1ca;background:#eef7f4;border-radius:10px;padding:22px}.proof code{overflow-wrap:anywhere}.small{font-size:13px;color:var(--muted)}footer{border-top:1px solid var(--line);padding:24px 30px;color:var(--muted);font-size:13px;max-width:1120px;margin:auto}
@media(max-width:850px){.top{align-items:flex-start;flex-direction:column;gap:14px}.cards{grid-template-columns:1fr}main{padding:22px 18px 48px}article{padding:22px 18px}nav{gap:12px}.top{padding:18px}h1{font-size:36px}}
@media print{nav,.button{display:none}body,article{background:#fff}main{max-width:none;padding:0}.alert{break-inside:avoid}pre{white-space:pre-wrap}}
'''


def rewrite_links(body):
    mapping = {'reports/review.md':'review.html', 'reports/research.md':'research.html',
               'reports/executive-summary.md':'executive-summary.html',
               'reports/sources.md':'sources.html','reports/requirements.md':'requirements.html',
               'review.md':'review.html','research.md':'research.html'}
    def replace(m):
        link=m.group(1)
        if link.startswith('../'):
            link=link[3:]
        return 'href="'+mapping.get(link,link)+'"'
    body=re.sub(r'href="([^"]+)"',replace,body)
    return body.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')


def render_md(path):
    return rewrite_links(markdown.markdown(path.read_text(),extensions=['tables','fenced_code']))


def frame(filename,title,body,*,article=False):
    links=''.join(f'<a href="{url}"'+(' aria-current="page"' if url==filename else '')+f'>{label}</a>' for url,label in NAV)
    banner='<aside class="alert" aria-label="Submission status"><strong>BLOCKED · DO NOT SUBMIT</strong><p>No new TIFF exists. The literal uniqueness rule cannot pass while a registry member is positive throughout the footprint. No competition slot used.</p></aside>'
    content=f'<article>{body}</article>' if article else body
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="GEMSDOE70: transparent fault-discovery audit, submission status, research queue and official sources."><title>{html.escape(title)} · GEMSDOE70</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="small" href="#main" style="position:absolute;left:8px;top:0">Skip to content</a><header><div class="top"><a class="brand" href="index.html">GEMS<span>DOE70</span></a><nav aria-label="Main navigation">{links}</nav></div></header><main id="main"><div class="eyebrow">Geothermal fault discovery / Evidence first</div>{banner}{content}</main><footer>Reviewed 20 October 2026 UTC · Static research report, not a model-generation service.<br>Maximize P(Win): protect submission slots. Own the Outcome: publish failed gates.<br><a href="https://github.com/buffedlizard55-lab/GEMSDOE70">Code &amp; evidence</a> · <a href="PROMPT.md">Working brief</a> · <a href="HANDOFF.md">Next-session handoff</a></footer></body></html>'''


def main():
    state=status()
    # Deliberately no positive publication branch: a card cannot authorize downloads.
    if state['download_available'] or state['approved_for_weekly_slot']:
        raise ValueError('this negative-only publisher cannot publish a positive release')
    proof=json.loads((ROOT/'evidence/preflight.json').read_text())
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    total=proof['coverage']['footprint_pixels']
    body=f'''<span class="pill">NEGATIVE RESULT · NO DOWNLOADABLE TIFF</span><h1>Discover faults.<br>Never manufacture confidence.</h1><p class="lead">A clear submission decision, traceable geological reasoning, and honest limits. This run stopped at the mandatory registry gate—not at a fabricated score.</p><a class="button" href="executive-summary.html">Read the submission guide →</a><a class="button secondary" href="evidence/run_card.json" download>Download negative run card</a><p class="small">The JSON is evidence only. It is not a competition submission file.</p><div class="cards"><section class="card"><h2>Submission TIFF</h2><div class="stat">Not generated</div><p class="muted">No renamed reference, random substitute, or false “ready” label.</p></section><section class="card"><h2>Scientific holdout</h2><div class="stat">Not run</div><p class="muted">No fitted model, comparable best, canary or HOLDOUT-DTI claimed.</p></section><section class="card"><h2>Weekly slots used</h2><div class="stat">None</div><p class="muted">Promotion to an actual slot belongs to a separate selector.</p></section></div><section class="proof"><h2 style="margin-top:0">The decisive preflight finding</h2><p>A hash-verified registry raster is positive at all <strong>{total:,}</strong> finite sample-footprint cells. Any nonempty candidate inside that footprint overlaps this raster at distance zero. Its forward overlap is therefore <strong>100%</strong>, above the protocol’s <strong>70%</strong> stop threshold.</p><p>This is a registry-support measurement, not a performance score. We did not exclude dense rasters or change the definition to pass.</p><a href="evidence/preflight.json">Read the measured proof →</a></section><h2>What the review established</h2><ul><li>The starting repository contained only a README—not the claimed training pipeline.</li><li>The required single-method lane paragraph was not supplied.</li><li>The H33 reference is a sparse, catalogue-flank-pruned artifact. Its reported performance has no artifact-bound organizer receipt here.</li><li>Shared evaluation and packaging code was restored unchanged and checked against upstream Git blobs.</li><li>Four geological hypotheses are ranked for later review, not presented as tested discoveries.</li></ul><h2>A useful next step, not another copied TIFF</h2><p>Resolve the lane and registry-definition conflict, authenticate the data, then preregister one method on untouched blocks. Canary every feature, beat a rebuilt same-evaluator current best, check surface uniqueness before placement, and validate the final bytes. Only then can a selector decide whether to use a slot.</p><a class="button secondary" href="research.html">Explore the research queue</a><a class="button secondary" href="sources.html">Audit the sources</a>'''
    (ROOT/'assets').mkdir(exist_ok=True)
    (ROOT/'assets/site.css').write_text(CSS.strip()+'\n')
    (ROOT/'index.html').write_text(frame('index.html','Submission readiness',body))
    pages=[('executive-summary.html','Submission guide','executive-summary.md'),
           ('research.html','Research queue','research.md'),('sources.html','Source ledger','sources.md'),
           ('review.html','Repository audit','review.md'),('requirements.html','Requirements','requirements.md')]
    for filename,title,source in pages:
        (ROOT/filename).write_text(frame(filename,title,render_md(ROOT/'reports'/source),article=True))
    detail='<h1>Run card</h1><p>Negative preflight result. Null fields mean <strong>not measured</strong>; they are not zero performance or a validator pass.</p><a class="button secondary" href="evidence/run_card.json" download>Download JSON evidence</a><pre><code>'+html.escape(json.dumps(card,indent=2))+'</code></pre>'
    (ROOT/'run-card.html').write_text(frame('run-card.html','Run card',detail,article=True))
    (ROOT/'evidence/release-status.json').write_text(json.dumps(state,indent=2)+'\n')
    (ROOT/'.nojekyll').touch()
    print('Built seven negative-only pages. No TIFF download link created.')


if __name__=='__main__':
    main()
