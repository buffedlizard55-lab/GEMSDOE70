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
    # Historical build_site.py asserts no public rasters (negative gate); new site uses custom pages
    # Here we verify current custom site has valid local links and no misleading artifacts outside whitelist
    from gems70.release import assert_no_public_rasters
    assert_no_public_rasters(ROOT)
    for p in list((ROOT/'docs').glob('*.html')) + list(ROOT.glob('*.html')):
        if not p.is_file(): continue
        text=p.read_text()
        # New site should have READY banner
        if p.name == 'index.html' and p.parent.name == 'docs':
            assert 'Ready to download' in text
        parser=Links();parser.feed(text)
        for link in parser.links:
            u=urlsplit(link)
            if u.scheme or u.netloc or not u.path:continue
            # Whitelisted TIFF/ZIP are allowed
            if u.path.lower().endswith(('.tif','.tiff','.zip')):
                assert 'gems70-discordance-corridor' in u.path, f'unexpected artifact link {p}: {link}'
            target=(p.parent/unquote(u.path)).resolve()
            assert target.is_file(),f'broken local link {p}: {link}'


def test_no_scientific_artifact_is_published():
    # v2 validated submission is whitelisted
    import json as js
    j=js.loads((ROOT/'evidence/submission_v2.json').read_text())
    allowed={j['file_paths']['tif'], j['file_paths']['zip']}
    found=set(p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').rglob('*.tif')) | set(p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').rglob('*.zip'))
    assert found == allowed
