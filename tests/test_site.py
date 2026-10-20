from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
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
    inv = json.loads((ROOT / 'registry/published_artifacts.json').read_text())
    listed = {r['path']: r['sha256'] for r in inv['artifacts']}
    for p in (ROOT / 'docs').rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.tif', '.tiff', '.zip'}:
            rel = p.relative_to(ROOT).as_posix()
            assert rel in listed, rel
            assert hashlib.sha256(p.read_bytes()).hexdigest() == listed[rel], rel
    current = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert current['submission_name'] is None and current['raster_sha256'] is None
    archived = json.loads((ROOT / 'evidence/phase4/run_card.json').read_text())
    assert f"docs/downloads/{archived['submission_name']}.tif" in listed


def test_retracted_approval_json_is_private_but_preserved_byte_for_byte():
    receipt = json.loads((ROOT / 'evidence/publication_retractions.json').read_text())
    for row in receipt['removed_direct_urls']:
        assert not (ROOT / row['path']).exists()
        retained = ROOT / row['retained_exact_bytes']
        assert retained.is_file()
        assert hashlib.sha256(retained.read_bytes()).hexdigest() == row['sha256']
    assert json.loads((ROOT / 'docs/downloads/publication_retractions.json').read_text()) == receipt


def test_decision_is_explicit_on_the_landing_page():
    home = (ROOT / 'docs/index.html').read_text()
    assert 'DO NOT SUBMIT — no eligible new GeoTIFF.' in home
    assert 'Download a new submission file: NO.' in home
    assert 'Use a weekly slot: NO.' in home
    assert 'Download submission TIFF' not in home
    assert 'Download P4 archive for review only — DO NOT SUBMIT' in home
    assert json.loads((ROOT / 'docs/run-card.json').read_text())['verdict'] == 'negative'
    assert json.loads((ROOT / 'docs/sources.json').read_text()) == json.loads(
        (ROOT / 'registry/sources.json').read_text())
