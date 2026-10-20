"""Audit the actual legacy-root Pages boundary, not just links in docs/.

JSON is a YAML subset, so _config.yml can be parsed without another dependency.
This is a publication policy for the stopped run, not a scientific release gate.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit


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
    return {'source_policy_ok': True, 'public_roots': sorted(PUBLIC_ROOTS),
            'excluded_private_roots': sorted(private)}


def check_output(site: Path, baseurl: str = '/GEMSDOE70', *, allowed_artifacts=None) -> dict:
    """Check the built directory, including direct URLs never linked by a page."""
    site = Path(site)
    if not site.is_dir() or site.is_symlink():
        raise ValueError('A real built site directory is required')
    import hashlib
    allowed_artifacts = allowed_artifacts or {}
    raster_count = 0
    paths = list(site.rglob('*'))
    raster_count = 0
    violations = []
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
        if path.suffix.lower() in {'.tif', '.tiff', '.zip'}:
            expected = allowed_artifacts.get(rel.as_posix())
            if (not expected or not path.is_file() or path.is_symlink()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
                violations.append(f'{rel}: stopped-run raster/archive')
            else:
                raster_count += 1
    if violations:
        raise ValueError('Unsafe Pages build: ' + '; '.join(violations))
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
        p = site / page
        if not p.is_file():
            raise ValueError('Missing Pages entry point: ' + page)
        text = p.read_text()
        if 'DO NOT SUBMIT' not in text and 'Do not submit this run.' not in text:
            raise ValueError('Missing negative banner: ' + page)
    return {'built_output_ok': True, 'files_checked': sum(p.is_file() for p in paths),
            'raster_downloads': raster_count,
            'scope': 'Built-site publication only; not organizer acceptance or a scientific score.'}
