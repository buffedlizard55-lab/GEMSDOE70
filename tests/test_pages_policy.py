"""Regression: root Pages must not publish archived placeholder predictions."""
import json
from pathlib import Path

import pytest

from gems70.pages_policy import check_output, check_source

ROOT = Path(__file__).resolve().parents[1]


def test_real_legacy_root_config_excludes_private_artifacts():
    report = check_source(ROOT)
    assert report['source_policy_ok']
    excluded = json.loads((ROOT / '_config.yml').read_text())['exclude']
    assert {'quarantine', 'data', 'evidence', 'vendor', 'scripts', 'src', 'registry'} <= set(excluded)
    assert (ROOT / 'docs/.nojekyll').is_file()  # nested marker does not bypass root Jekyll


def test_nojekyll_bypass_is_rejected(tmp_path):
    (tmp_path / '.nojekyll').touch()
    with pytest.raises(ValueError, match='bypasses'):
        check_source(tmp_path)


def test_unreviewed_root_content_fails_closed(tmp_path):
    (tmp_path / '_config.yml').write_text('{"exclude": ["_config.yml"]}')
    (tmp_path / 'new-artifacts').mkdir()
    with pytest.raises(ValueError, match='new-artifacts'):
        check_source(tmp_path)


def safe_output(path):
    (path / 'docs').mkdir()
    for name in ['index.html', 'docs/index.html', 'docs/executive-summary.html']:
        (path / name).write_text('DO NOT SUBMIT')


def test_safe_built_output(tmp_path):
    safe_output(tmp_path)
    assert check_output(tmp_path)['raster_downloads'] == 0


@pytest.mark.parametrize('name', ['quarantine/hidden.txt', 'data/input.tif',
                                 'docs/downloads/decoy.TIF', 'docs/a.TiFf', 'docs/a.ZIP'])
def test_direct_url_artifacts_rejected_without_any_link(tmp_path, name):
    safe_output(tmp_path)
    path = tmp_path / name
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_bytes(b'not advertised but still reachable')
    with pytest.raises(ValueError, match='Unsafe Pages build'):
        check_output(tmp_path)


def test_output_symlinks_rejected(tmp_path):
    safe_output(tmp_path)
    (tmp_path / 'docs/archive').symlink_to(ROOT / 'quarantine', target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        check_output(tmp_path)


def test_empty_or_bannerless_output_rejected(tmp_path):
    with pytest.raises(ValueError, match='Missing Pages entry'):
        check_output(tmp_path)
    safe_output(tmp_path)
    (tmp_path / 'docs/index.html').write_text('READY TO SUBMIT')
    with pytest.raises(ValueError, match='negative banner'):
        check_output(tmp_path)


def test_github_generated_theme_css_only_is_allowed(tmp_path):
    safe_output(tmp_path)
    css = tmp_path / 'assets/css/style.css'
    css.parent.mkdir(parents=True)
    css.write_text('/* GitHub default theme */')
    assert check_output(tmp_path)['built_output_ok']
    (tmp_path / 'assets/archived.html').write_text('unsafe private page')
    with pytest.raises(ValueError, match='nonpublic root'):
        check_output(tmp_path)


def test_link_to_checkout_only_evidence_is_rejected_in_built_output(tmp_path):
    safe_output(tmp_path)
    page = tmp_path / 'docs/index.html'
    page.write_text('DO NOT SUBMIT <a href="../evidence/preflight.json">Evidence</a>')
    with pytest.raises(ValueError, match='Broken built-site link'):
        check_output(tmp_path)
    page.write_text('DO NOT SUBMIT <a href="https://github.com/example/evidence.json">Evidence</a>')
    assert check_output(tmp_path)['built_output_ok']


def test_project_pages_mount_is_resolved_against_site(tmp_path):
    safe_output(tmp_path)
    (tmp_path / 'index.html').write_text(
        'DO NOT SUBMIT <a href="/GEMSDOE70/docs/index.html">Current site</a>')
    assert check_output(tmp_path)['built_output_ok']


def test_explicit_inventory_allows_only_hash_pinned_review_artifact(tmp_path):
    import hashlib
    safe_output(tmp_path)
    rel = 'docs/review.tif'
    raster = tmp_path / rel
    raster.write_bytes(b'review fixture')
    allowed = {rel: hashlib.sha256(raster.read_bytes()).hexdigest()}
    assert check_output(tmp_path, allowed_artifacts=allowed)['raster_downloads'] == 1
    raster.write_bytes(b'tampered')
    with pytest.raises(ValueError, match='Unsafe Pages build'):
        check_output(tmp_path, allowed_artifacts=allowed)


def test_integrated_current_pages_after_markdown_exclusion(tmp_path):
    import shutil
    from gems70.release import published_artifacts
    from gems70.pages_policy import PUBLIC_ROOTS
    for name in PUBLIC_ROOTS:
        p = ROOT / name
        if p.is_dir():
            shutil.copytree(p, tmp_path / name, ignore=shutil.ignore_patterns('*.md'))
        elif p.is_file():
            shutil.copyfile(p, tmp_path / name)
    result = check_output(tmp_path, allowed_artifacts=published_artifacts(ROOT))
    assert result['built_output_ok']
    assert result['raster_downloads'] == len(published_artifacts(ROOT))
