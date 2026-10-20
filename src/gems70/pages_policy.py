"""Audit the actual legacy-root Pages boundary, not just links in docs/.

JSON is a YAML subset, so _config.yml can be parsed without another dependency.
This is a publication policy for the stopped run, not a scientific release gate.
"""
from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .release import assert_no_public_release_claims


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in {'href', 'src'} or not value:
                continue
            url = urlsplit(value)
            if not url.scheme and not url.netloc and url.path:
                self.paths.append(unquote(url.path))

PUBLIC_ROOTS = frozenset({
    'docs', 'index.html', 'executive-summary.html', 'requirements.html',
    'research.html', 'review.html', 'run-card.html', 'sources.html',
})


def check_source(root: Path) -> dict:
    root = Path(root)
    if (root / '.nojekyll').exists():
        raise ValueError('Root .nojekyll bypasses the quarantine exclusions')
    config = json.loads((root / '_config.yml').read_text())
    excluded = set(config.get('exclude', []))
    # Check tracked AND currently present untracked visible paths. New public
    # top-level content needs review instead of being silently copied by Jekyll.
    private = {p.name for p in root.iterdir()
               if not p.name.startswith('.') and p.name not in PUBLIC_ROOTS}
    missing = private - excluded
    if missing:
        raise ValueError('Unclassified root paths need Pages exclusion: ' + ', '.join(sorted(missing)))
    if excluded & PUBLIC_ROOTS:
        raise ValueError('Public entry points must not be excluded')
    assert_no_public_release_claims(root)
    return {'source_policy_ok': True, 'public_roots': sorted(PUBLIC_ROOTS),
            'excluded_private_roots': sorted(private)}


def check_output(site: Path, baseurl: str = '/GEMSDOE70', *, inventory: Path | None = None) -> dict:
    """Check actual built bytes, including direct URLs not linked by any page.

    The merged checkout already published historical research TIFFs. An exact
    SHA-pinned archived byte may be served with the DO NOT SUBMIT banner, but
    no unknown/replaced raster is allowed. Being public is NOT an upload gate.
    """
    site = Path(site)
    if not site.is_dir() or site.is_symlink():
        raise ValueError('A real built site directory is required')
    if inventory is None:
        inventory = Path(__file__).resolve().parents[2] / 'registry/published_artifacts.json'
    pins = json.loads(Path(inventory).read_text())
    if not isinstance(pins.get('artifacts'), list):
        raise ValueError('Missing Pages artifact inventory')
    allowed = {row['path']: row['sha256'] for row in pins['artifacts']
               if isinstance(row, dict) and isinstance(row.get('path'), str)
               and row['path'].startswith('docs/downloads/')
               and row['path'].lower().endswith(('.tif', '.tiff', '.zip'))}
    paths = list(site.rglob('*'))
    violations = []
    rasters = 0
    for path in paths:
        rel = path.relative_to(site)
        if path.is_symlink():
            violations.append(f'{rel}: symlink')
        # GitHub's legacy Jekyll builder injects the default theme stylesheet
        # even though repository assets/ is excluded. Permit only that exact
        # generated CSS path and its directories, never arbitrary assets/ files.
        theme_css = rel.as_posix() == 'assets/css/style.css' and path.is_file()
        theme_dir = rel.as_posix() in {'assets', 'assets/css'} and path.is_dir()
        if rel.parts[0] not in PUBLIC_ROOTS and not (theme_css or theme_dir):
            violations.append(f'{rel}: nonpublic root')
        if path.suffix.lower() in {'.tif', '.tiff', '.zip'} and path.is_file():
            pin = allowed.get(rel.as_posix())
            if (not pin or not isinstance(pin, str) or len(pin) != 64
                    or hashlib.sha256(path.read_bytes()).hexdigest() != pin):
                violations.append(f'{rel}: unpinned or changed raster/archive')
            else:
                rasters += 1
    if violations:
        raise ValueError('Unsafe Pages build: ' + '; '.join(violations))
    assert_no_public_release_claims(site)
    # Check the deployed tree, not the checkout where excluded evidence still
    # exists. A source-relative evidence link may otherwise pass local tests
    # yet become a 404 after quarantine exclusions take effect.
    for page in site.rglob('*.html'):
        links = LocalLinks()
        links.feed(page.read_text())
        for link in links.paths:
            if baseurl and link.startswith(baseurl.rstrip('/') + '/'):
                link = link[len(baseurl.rstrip('/')):]
            target = ((site / link.lstrip('/')) if link.startswith('/')
                      else (page.parent / link)).resolve()
            if not target.is_relative_to(site.resolve()) or not target.exists():
                raise ValueError(f'Broken built-site link: {page.relative_to(site)} -> {link}')
    for page in ['index.html', 'docs/index.html', 'docs/executive-summary.html']:
        if not (site / page).is_file():
            raise ValueError('Missing Pages entry point: ' + page)
    # A direct HTML URL to an old status/guide must not contradict the current
    # negative, even if it is absent from the navigation. Downloads are raw
    # receipts only; an unexpected HTML there could be a hidden promotion page.
    for p in site.rglob('*.html'):
        if p.parent not in (site, site / 'docs'):
            raise ValueError('Unexpected HTML in Pages downloads: ' + p.relative_to(site).as_posix())
        text = p.read_text()
        if 'DO NOT SUBMIT' not in text and 'Do not submit this run.' not in text:
            raise ValueError('Missing negative banner: ' + p.relative_to(site).as_posix())
    return {'built_output_ok': True, 'files_checked': sum(p.is_file() for p in paths),
            'raster_downloads': rasters, 'archived_rasters_are_not_submissions': True,
            'scope': 'Pinned archived research downloads only; not organizer acceptance, a new submission or a scientific score.'}
