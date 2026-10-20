"""Actual shared writer contract; synthetic fixtures are not competition submissions."""
import zipfile
import numpy as np
import pytest
from gems57 import grid
from gems57.submission_writer import write_submission


@pytest.mark.parametrize('value',[np.nan,np.inf,-1,1.0001])
def test_range_failures_leave_no_output(tmp_path,value):
    p=np.zeros((3,3),np.float32);p[1,1]=value
    with pytest.raises(ValueError,match='finite|normalized'):
        write_submission(tmp_path/'bad.tif',p,tmp_path/'missing.tif',np.ones_like(p,bool),name='test',note='test')
    assert not list(tmp_path.iterdir())


def test_note_and_footprint_fail_before_export(tmp_path):
    p=np.ones((3,3),np.float32)
    with pytest.raises(ValueError,match='note'):
        write_submission(tmp_path/'bad.tif',p,tmp_path/'missing',np.ones_like(p,bool),name='test',note='x'*141)
    with pytest.raises(ValueError,match='outside'):
        write_submission(tmp_path/'bad.tif',p,tmp_path/'missing',np.zeros_like(p,bool),name='test',note='test')
    assert not list(tmp_path.iterdir())


def test_real_tiff_zip_roundtrip_and_no_overwrite(tmp_path):
    a=np.zeros(grid.SHAPE,np.float32);a[100,100]=.5
    fp=np.ones(grid.SHAPE,bool)
    sample=tmp_path/'sample.tif'
    grid.write_geotiff(sample,np.zeros_like(a))
    dest=tmp_path/'SYNTHETIC-UNIT-TEST-NOT-A-SUBMISSION.tif'
    receipt=write_submission(dest,a,sample,fp,name='synthetic unit test',note='Not a competition prediction')
    assert receipt['validator']['all_checks_passed']
    assert receipt['validator']['n_nan']==0
    assert receipt['validator']['min']==0
    assert receipt['validator']['max']==.5
    with zipfile.ZipFile(dest.with_suffix('.zip')) as z:
        assert z.namelist()==[dest.name]
        assert z.read(dest.name)==dest.read_bytes()
    with pytest.raises(FileExistsError):
        write_submission(dest,a,sample,fp,name='synthetic',note='test')
