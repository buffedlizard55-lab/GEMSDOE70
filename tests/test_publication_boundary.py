"""Publication configuration must exclude the repository's forensic archives."""
import importlib.util
from pathlib import Path
import pytest
from gems70.release import assert_no_public_rasters

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_pages', ROOT/'scripts/check_pages.py')
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)


@pytest.mark.parametrize('settings', [
    None, [], {},
    {'build_type': 'legacy', 'source': {'branch': 'main', 'path': '/'}, 'https_enforced': True},
    {'build_type': 'workflow', 'source': pages.EXPECTED_SOURCE, 'https_enforced': True},
    {'build_type': 'legacy', 'source': pages.EXPECTED_SOURCE, 'https_enforced': False},
])
def test_unsafe_or_unknown_configuration_fails(settings):
    assert not pages.boundary_status(settings)


def test_docs_only_source():
    assert pages.boundary_status({'build_type': 'legacy',
                                 'source': pages.EXPECTED_SOURCE, 'https_enforced': True})


@pytest.mark.parametrize('kind', ['file', 'directory', 'dangling'])
def test_symlink_cannot_bypass_artifact_guard(tmp_path, kind):
    docs = tmp_path/'docs'
    docs.mkdir()
    target = tmp_path/'quarantine'
    if kind == 'file':
        target.write_bytes(b'quarantined TIFF')
    elif kind == 'directory':
        target.mkdir()
        (target/'unsafe.tif').write_bytes(b'TIFF')
    (docs/'innocent.txt').symlink_to(target, target_is_directory=kind == 'directory')
    with pytest.raises(ValueError, match='must not publish'):
        assert_no_public_rasters(tmp_path)


def test_read_only_check_does_not_reconfigure(monkeypatch):
    calls = []
    def fake_api(*args, **kwargs):
        calls.append((args, kwargs))
        return {'build_type': 'legacy', 'source': {'branch': 'main', 'path': '/'}}
    monkeypatch.setattr(pages, 'api', fake_api)
    assert pages.main([]) == 2
    assert calls == [((), {})]


def test_auth_failure_is_closed(monkeypatch):
    def fake_api(*args, **kwargs):
        raise OSError('GitHub unavailable')
    monkeypatch.setattr(pages, 'api', fake_api)
    assert pages.main([]) == 2


def test_real_root_publication_guard():
    from gems70.release_e3 import assert_root_guard_e3
    assert_root_guard_e3(ROOT)


@pytest.mark.parametrize('bypass', ['nojekyll', 'root_tiff', 'symlink', 'unexcluded'])
def test_root_publication_cannot_expose_archives(tmp_path, bypass):
    import json
    from gems70.release import assert_root_pages_guard
    (tmp_path/'_config.yml').write_text(json.dumps({'exclude': ['quarantine', 'data']}))
    (tmp_path/'quarantine').mkdir()
    (tmp_path/'quarantine/unsafe.tif').write_bytes(b'archive')
    assert_root_pages_guard(tmp_path)
    if bypass == 'nojekyll':
        (tmp_path/'.nojekyll').touch()
    elif bypass == 'root_tiff':
        (tmp_path/'new.TIF').write_bytes(b'archive')
    elif bypass == 'symlink':
        (tmp_path/'ordinary.txt').symlink_to(tmp_path/'quarantine')
    else:
        (tmp_path/'_config.yml').write_text('{"exclude": ["data"]}')
    with pytest.raises(ValueError):
        assert_root_pages_guard(tmp_path)
