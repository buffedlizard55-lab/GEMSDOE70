"""Regression: Pages permits only exact-byte archived files, never new rasters."""
import hashlib
import json
from pathlib import Path

import pytest

from gems70.pages_policy import check_output, check_source
from gems70.release import assert_no_public_rasters

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


def test_hash_pinned_archival_bytes_only_pass_both_guards(tmp_path):
    source = tmp_path / 'source'
    site = tmp_path / 'built-site'
    source.mkdir()
    site.mkdir()
    safe_output(site)
    archive = source / 'docs/downloads/review-only.tif'
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b'synthetic archived bytes; guard test only')
    built = site / 'docs/downloads/review-only.tif'
    built.parent.mkdir()
    built.write_bytes(archive.read_bytes())
    inventory = source / 'registry/published_artifacts.json'
    inventory.parent.mkdir()
    inventory.write_text(json.dumps({'artifacts': [{
        'path': 'docs/downloads/review-only.tif',
        'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    }]}))
    assert_no_public_rasters(source)
    assert check_output(site, inventory=inventory)['raster_downloads'] == 1
    archive.write_bytes(b'replaced bytes')
    built.write_bytes(archive.read_bytes())
    with pytest.raises(ValueError, match='hash-drifted'):
        assert_no_public_rasters(source)
    with pytest.raises(ValueError, match='unpinned or changed'):
        check_output(site, inventory=inventory)


@pytest.mark.parametrize('payload, reason', [
    ('{"verdict":"promote","download_and_submit_ok":true}', 'Stale affirmative'),
    ('{"verdict":"promote-to-selector-only"}', 'Stale affirmative'),
    ('{"download_ok_for_selector_review":true,"submit_ok":false}', 'Stale affirmative'),
    ('<<<<<<< HEAD\n{broken JSON}', 'Malformed public JSON'),
])
def test_unlinked_stale_json_cannot_publish_old_approval(tmp_path, payload, reason):
    safe_output(tmp_path)
    receipt = tmp_path / 'docs/downloads/old-status.json'
    receipt.parent.mkdir()
    receipt.write_text(payload)
    with pytest.raises(ValueError, match=reason):
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


def test_unlinked_old_html_status_cannot_claim_approval(tmp_path):
    safe_output(tmp_path)
    (tmp_path / 'docs/status.html').write_text('Download submission TIFF now!')
    with pytest.raises(ValueError, match='negative banner: docs/status.html'):
        check_output(tmp_path)


def test_download_directory_is_raw_receipts_not_hidden_html(tmp_path):
    safe_output(tmp_path)
    nested = tmp_path / 'docs/downloads/old-promotion.html'
    nested.parent.mkdir()
    nested.write_text('DO NOT SUBMIT, but old approval text could be hidden here')
    with pytest.raises(ValueError, match='Unexpected HTML in Pages downloads'):
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
