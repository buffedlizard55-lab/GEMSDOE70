from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_site import main


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='a' and 'href' in attrs:self.links.append(attrs['href'])
        if tag=='link' and 'href' in attrs:self.links.append(attrs['href'])


def test_site_rebuild_has_bound_tiff_download_and_no_broken_local_link():
    main()
    for p in ROOT.glob('*.html'):
        text=p.read_text()
        assert 'DO NOT SUBMIT' in text
        assert '<html lang="en">' in text
        parser=Links();parser.feed(text)
        for link in parser.links:
            u=urlsplit(link)
            if u.scheme or u.netloc or not u.path:continue
            if u.path.lower().endswith(('.tif','.tiff','.zip')):
                assert 'gems70-fusion-dotted-37654-20261020' in u.path, f'unbound artifact link {p}: {link}'
            target=(p.parent/unquote(u.path)).resolve()
            assert target.is_file(),f'broken local link {p}: {link}'


def test_only_hash_bound_scientific_artifact_is_published():
    import hashlib, json
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    tifs=list((ROOT/'docs').rglob('*.tif')); zips=list((ROOT/'docs').rglob('*.zip'))
    assert [p.name for p in tifs]==['gems70-fusion-dotted-37654-20261020.tif']
    assert [p.name for p in zips]==['gems70-fusion-dotted-37654-20261020.zip']
    assert hashlib.sha256(tifs[0].read_bytes()).hexdigest()==card['raster_sha256']
    for parent in ['assets','evidence']:
        for suffix in ['*.tif','*.zip']:
            assert not list((ROOT/parent).rglob(suffix))
