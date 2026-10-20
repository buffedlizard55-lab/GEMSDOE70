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


def test_site_rebuild_has_no_tiff_download_or_broken_local_link():
    main()
    for p in ROOT.glob('*.html'):
        text=p.read_text()
        assert 'DO NOT SUBMIT' in text
        assert '<html lang="en">' in text
        parser=Links();parser.feed(text)
        for link in parser.links:
            u=urlsplit(link)
            if u.scheme or u.netloc or not u.path:continue
            assert not u.path.lower().endswith(('.tif','.tiff','.zip')),f'misleading artifact link {p}: {link}'
            target=(p.parent/unquote(u.path)).resolve()
            assert target.is_file(),f'broken local link {p}: {link}'


def test_no_scientific_artifact_is_published():
    # Exactly one pinned E2 review TIFF+ZIP in docs; none anywhere else.
    import json
    pub=json.loads((ROOT/'evidence/e2/publication.json').read_text())
    docs_rasters={p.name for p in (ROOT/'docs').rglob('*') if p.suffix.lower() in {'.tif','.tiff','.zip'}}
    assert docs_rasters=={pub['file'],pub['zip_file']}
    for parent in ['assets','evidence']:
        for suffix in ['*.tif','*.zip']:
            assert not list((ROOT/parent).rglob(suffix))
