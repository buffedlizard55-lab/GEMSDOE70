"""Packaging tests only. Temporary toy outputs are NOT competition submissions."""
from pathlib import Path
import json
import subprocess
import sys
import zipfile
import numpy as np
import pytest
import rasterio
from gems57.submission_writer import write_submission
from gems57 import grid
ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('value',[np.nan,np.inf,-np.inf,-9999.,-3.4e38,-.01,1.001])
def test_shared_writer_rejects_invalid_output_without_clipping(tmp_path,value):
    p=np.zeros((2,2));p[0,0]=value
    with pytest.raises(ValueError,match='normalized, finite'):
        write_submission(tmp_path/'not-a-submission.tif',p,'no-sample',np.ones(p.shape,bool),
                         note='software test',name='software-test')
    assert not list(tmp_path.iterdir())


def test_shared_writer_rejects_long_note_and_catalogue_hits(tmp_path):
    p=np.ones((2,2))
    with pytest.raises(ValueError,match='note'):
        write_submission(tmp_path/'toy.tif',p,'no-sample',p.astype(bool),note='x'*141,name='toy')
    with pytest.raises(ValueError,match='mapped catalogue'):
        write_submission(tmp_path/'toy.tif',p,'no-sample',p.astype(bool),note='toy',name='toy',catalogue=p.astype(bool))
    assert not list(tmp_path.iterdir())


def test_shared_writer_full_grid_roundtrip_in_temporary_directory(tmp_path):
    # One toy point checks serialization only. It is not a geological experiment.
    g=grid.load_grid(ROOT/'data/bridge')
    p=np.zeros(g.shape,np.float32)
    y,x=np.argwhere(g.footprint & ~g.catalogue)[0]
    p[y,x]=.5
    path=tmp_path/'software-test-NOT-FOR-SUBMISSION.tif'
    receipt=write_submission(path,p,ROOT/'data/bridge/sample_submission.tif',g.footprint,
             note='Synthetic packaging test only; not a scientific candidate.',
             name='software-test-not-a-candidate',catalogue=g.catalogue)
    assert receipt['validator']['all_checks_passed']
    assert not receipt['approved_for_weekly_slot']
    with rasterio.open(path) as ds:
        assert ds.crs==g.crs and ds.transform==g.transform and ds.shape==g.shape
        assert np.isfinite(ds.read(1)).all()
        assert ds.nodata is None
    with zipfile.ZipFile(path.with_suffix('.zip')) as z:
        assert z.namelist()==[path.name]
        assert z.read(path.name)==path.read_bytes()
    result=subprocess.run([sys.executable,str(ROOT/'scripts/validate_submission.py'),str(path)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout)
    assert report['shared_validator']['all_checks_passed']
    assert report['approved_for_weekly_slot'] is False
    with pytest.raises(FileExistsError):
        write_submission(path,p,ROOT/'data/bridge/sample_submission.tif',g.footprint,
                         note='test',name='test',catalogue=g.catalogue)


def test_validator_missing_file_returns_structured_negative(tmp_path):
    result=subprocess.run([sys.executable,str(ROOT/'scripts/validate_submission.py'),str(tmp_path/'missing.tif')],capture_output=True,text=True)
    assert result.returncode==1
    report=json.loads(result.stdout)
    assert not report['local_format_pass'] and not report['approved_for_weekly_slot']
    assert 'error' in report


def test_validator_wrong_shape_returns_structured_negative(tmp_path):
    path=tmp_path/'wrong-grid.tif'
    with rasterio.open(path,'w',driver='GTiff',height=4,width=4,count=1,dtype='float32',
                       crs=grid.CRS_EPSG,transform=grid.TRANSFORM,nodata=np.nan) as ds:
        ds.write(np.zeros((4,4),np.float32),1)
    result=subprocess.run([sys.executable,str(ROOT/'scripts/validate_submission.py'),str(path)],capture_output=True,text=True)
    assert result.returncode==1
    report=json.loads(result.stdout)
    assert not report['local_format_pass']
    assert report['sample_comparison']['ok'] is False
    assert report['sample_comparison']['nodata']=='nan'


def test_report_metadata_sanitization_does_not_fabricate_a_pass():
    sys.path.insert(0,str(ROOT/'scripts'))
    from validate_submission import json_safe
    r=json_safe({'ok':False,'nodata':float('nan'),'values':[float('inf'),-.1]})
    assert r=={'ok':False,'nodata':'nan','values':['inf',-.1]}
    json.dumps(r,allow_nan=False)
