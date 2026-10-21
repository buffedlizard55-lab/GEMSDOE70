from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import main


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"a", "link"} and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "img" and "src" in attrs:
            self.links.append(attrs["src"])


def test_site_rebuild_has_verified_downloads_and_zero_broken_links():
    main()
    for p in list(ROOT.glob("*.html")) + list((ROOT / "docs").glob("*.html")):
        text = p.read_text()
        assert '<html lang="en">' in text
        parser = Links()
        parser.feed(text)
        for link in parser.links:
            u = urlsplit(link)
            if u.scheme or u.netloc or not u.path:
                continue
            target = (p.parent / unquote(u.path)).resolve()
            assert target.is_file(), f"broken local link {p}: {link}"


def test_exact_authorized_artifacts_and_permissions():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    expected = {
        card["submission_paths"]["primary_tif"],
        card["submission_paths"]["zip"],
    }
    found = {
        p.relative_to(ROOT).as_posix()
        for parent in ["docs", "assets", "evidence"]
        for suffix in ["*.tif", "*.zip"]
        for p in (ROOT / parent).rglob(suffix)
    }
    assert found == expected
    for rel in expected:
        p = ROOT / rel
        assert (p.stat().st_mode & 0o444) == 0o444
