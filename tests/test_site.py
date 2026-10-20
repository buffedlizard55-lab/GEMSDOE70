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
    assert 'Download: yes — existing bytes available for forensic review only.' in home
    assert 'not certified for upload format or uniqueness' in home
    assert 'Submit a weekly slot: not recommended' in home
    assert 'Download archived TIFF — DO NOT SUBMIT' in home
