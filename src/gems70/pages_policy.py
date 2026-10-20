"""Audit the actual legacy-root Pages boundary, not just links in docs/.

JSON is a YAML subset, so _config.yml can be parsed without another dependency.
This is a publication policy for the stopped run, not a scientific release gate.
"""
from __future__ import annotations

import json
from pathlib import Path

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


def check_output(site: Path) -> dict:
    """Check the built directory, including direct URLs never linked by a page."""
    site = Path(site)
    if not site.is_dir() or site.is_symlink():
        raise ValueError('A real built site directory is required')
    paths = list(site.rglob('*'))
    violations = []
    for path in paths:
        rel = path.relative_to(site)
        if path.is_symlink():
            violations.append(f'{rel}: symlink')
        if rel.parts[0] not in PUBLIC_ROOTS:
            violations.append(f'{rel}: nonpublic root')
        if path.suffix.lower() in {'.tif', '.tiff', '.zip'}:
            violations.append(f'{rel}: stopped-run raster/archive')
    if violations:
        raise ValueError('Unsafe Pages build: ' + '; '.join(violations))
    for page in ['index.html', 'docs/index.html', 'docs/executive-summary.html']:
        p = site / page
        if not p.is_file():
            raise ValueError('Missing Pages entry point: ' + page)
        text = p.read_text()
        if 'DO NOT SUBMIT' not in text and 'Do not submit this run.' not in text:
            raise ValueError('Missing negative banner: ' + page)
    return {'built_output_ok': True, 'files_checked': sum(p.is_file() for p in paths),
            'raster_downloads': 0,
            'scope': 'Built-site publication only; not organizer acceptance or a scientific score.'}
