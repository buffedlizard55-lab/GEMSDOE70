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


def test_no_prediction_rasters_are_public():
    inv = json.loads((ROOT / 'registry/published_artifacts.json').read_text())
    assert not [row for row in inv['artifacts']
                if row['path'].lower().endswith(('.tif', '.tiff', '.zip'))]
    for p in (ROOT / 'docs').rglob('*'):
        assert not (p.is_file() and p.suffix.lower() in {'.tif', '.tiff', '.zip'}), p
    manifest = json.loads((ROOT / 'quarantine/published-downloads-2026-10-20/manifest.json').read_text())
    assert len(manifest['files']) >= 9


def test_decision_is_explicit_on_the_landing_page():
    home = (ROOT / 'docs/index.html').read_text()
    assert 'STOP — no TIFF cleared for download or submission' in home
    assert 'No TIFF is authorized for download or submission' in home
    assert 'Download submission TIFF' not in home
