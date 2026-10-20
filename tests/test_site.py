from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_site import main


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs: self.links.append(attrs['href'])
        if tag == 'link' and 'href' in attrs: self.links.append(attrs['href'])


def test_site_rebuild_has_no_broken_local_link():
    main()
    for p in ROOT.glob('*.html'):
        text = p.read_text()
        assert '<html lang="en">' in text
        parser = Links(); parser.feed(text)
        for link in parser.links:
            u = urlsplit(link)
            if u.scheme or u.netloc or not u.path: continue
            target = (p.parent / unquote(u.path)).resolve()
            assert target.is_file(), f'broken local link {p}: {link}'


def test_docs_pages_do_not_link_outside_published_site_root():
    site = ROOT / 'docs'
    for p in site.rglob('*.html'):
        parser = Links(); parser.feed(p.read_text())
        for link in parser.links:
            u = urlsplit(link)
            if u.scheme or u.netloc or not u.path:
                continue
            target = (p.parent / unquote(u.path)).resolve()
            assert target.is_relative_to(site.resolve()), f'link escapes published site {p}: {link}'
            assert target.is_file(), f'broken published-site link {p}: {link}'


def test_every_published_artifact_is_inventoried():
    import hashlib
    inv = json.loads((ROOT / 'registry/published_artifacts.json').read_text())
    listed = {r['path']: r['sha256'] for r in inv['artifacts']}
    for p in (ROOT / 'docs').rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.tif', '.tiff', '.zip'}:
            rel = p.relative_to(ROOT).as_posix()
            assert rel in listed, rel
            assert hashlib.sha256(p.read_bytes()).hexdigest() == listed[rel], rel
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert f"docs/downloads/{card['submission_name']}.tif" in listed


def test_decision_is_explicit_on_the_landing_page():
    home = (ROOT / 'docs/index.html').read_text()
    assert 'DO NOT SUBMIT — literal protocol stop' in home
    assert 'Download archived TIFF (review only)' in home
    assert 'Submit to DrivenData:</strong> no' in home
    assert 'Download submission TIFF' not in home
    assert 'unique, auditable candidate' not in home


def test_submission_guide_does_not_invite_upload_of_review_artifact():
    guide = (ROOT / 'docs/submission.html').read_text()
    assert 'Do not submit the archived TIFF.' in guide
    assert 'downloadable only for review and analysis' in guide
    assert 'do not use the file above' in guide
    assert 'Upload a weekly slot' not in guide


def test_published_dti_results_carry_evidence_metadata():
    results = (ROOT / 'docs/results.html').read_text()
    assert 'HOLDOUT-DTI' in results
    assert 'gems57-pooled-hide-v2' in results
    assert 'withheld positives' in results
    assert '95% CI' in results
    analysis = (ROOT / 'docs/h33-analysis.html').read_text()
    assert 'not ORGANIZER-CONFIRMED' in analysis
    assert 'plausible explanation' in analysis
    assert 'not</strong> identify why' in analysis
