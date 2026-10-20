from scripts.refresh_sibling_registry import (
    _json_nodata, _safe_regular_file, parse_ls_tree_z, valid_repo_slug,
)


def test_json_nodata_serializes_gdal_nan_without_nonstandard_json():
    import json
    assert _json_nodata(None) is None
    assert _json_nodata(-9999.0) == -9999.0
    assert json.dumps(_json_nodata(float("nan")), allow_nan=False) == '"nan"'


def test_repo_slug_validation_rejects_path_components():
    assert valid_repo_slug("GEMSDOE70")
    assert valid_repo_slug("gems-doe_70.v2")
    for bad in ("", ".", "..", "../outside", "owner/repo", "/tmp/repo", "-bad"):
        assert not valid_repo_slug(bad)


def test_safe_regular_file_excludes_symlinks_and_paths_outside_tree():
    assert _safe_regular_file({"mode": "100644", "path": "docs/candidate.tif"})
    assert not _safe_regular_file({"mode": "120000", "path": "docs/candidate.tif"})
    assert not _safe_regular_file({"mode": "100644", "path": "../outside.tif"})
    assert not _safe_regular_file({"mode": "100644", "path": "/tmp/outside.tif"})


def test_parse_ls_tree_z_keeps_spaces_and_only_tiffs():
    raw = (
        b"100644 blob 0123456789abcdef0123456789abcdef01234567\t"
        b"docs/downloads/a candidate.tif\0"
        b"100644 blob 1123456789abcdef0123456789abcdef01234567\t"
        b"docs/downloads/another.TIFF\0"
        b"100644 blob 2123456789abcdef0123456789abcdef01234567\t"
        b"README.md\0"
    )
    rows = parse_ls_tree_z(raw)
    assert [row["path"] for row in rows] == [
        "docs/downloads/a candidate.tif",
        "docs/downloads/another.TIFF",
    ]
    assert rows[0]["blob"].startswith("012345")


def test_parse_ls_tree_z_empty_and_non_blob_entries():
    assert parse_ls_tree_z(b"") == []
    raw = (
        b"040000 tree 0123456789abcdef0123456789abcdef01234567\tdocs/downloads\0"
        b"100644 blob 1123456789abcdef0123456789abcdef01234567\tdocs/downloads/x.txt\0"
    )
    assert parse_ls_tree_z(raw) == []
