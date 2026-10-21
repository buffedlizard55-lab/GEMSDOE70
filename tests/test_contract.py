import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import numpy as np
import pytest
from scipy import ndimage as ndi
from types import SimpleNamespace
from gems57 import holdout, uniqueness
from gems70 import method
from gems70.release import release_status, assert_no_public_rasters
ROOT=Path(__file__).resolve().parents[1]


def test_template_unchanged():
    pins=json.loads((ROOT/'registry/template_pin.json').read_text())
    for item in pins['files']:
        data=(ROOT/'vendor/gems57'/item['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==item['sha256']
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['git_blob']


def test_scientific_evidence_is_source_bound():
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    for p,h in card['method_source_sha256'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    assert len(card['submission_note'])<=140
    assert card['weekly_slots_used']==0
    assert card['organizer_confirmed_score'] is None
    assert card['verdict'] in {'promote','negative'}
    # a published artifact must carry a validator receipt and a hash
    if card['raster_sha256']:
        assert card['validator_output']['checks']
        assert all(card['validator_output']['checks'].values())


def test_holdout_whole_components_and_feature_buffer():
    cat=np.zeros((160,160),bool)
    for y in [20,30,45,60,100,115,130,140]:
        for x in [20,40,60,100,120,140]:cat[y,x:x+4]=True
    grid=SimpleNamespace(catalogue=cat,footprint=np.ones_like(cat))
    folds,_=holdout.buffered_component_draw(grid,seed=20,buffer_px=3,boundary_px=12)
    comp,n=ndi.label(cat,np.ones((3,3)))
    hidden=folds[0]['hidden_all']
    for i in range(1,n+1):
        assert (hidden[comp==i].all() or not hidden[comp==i].any())
    for f in folds:
        assert np.array_equal(f['masked_known'],cat&~hidden)
        assert not (f['visible']&hidden).any()
        assert ndi.distance_transform_edt(~f['visible'])[hidden].min()>3
        assert not (f['truth']&~f['region']).any()


def test_dense_support_is_not_exempted():
    # Corrected 2026-10-20: continuous values (<1) are not dots; only binary 1.0 counts.
    a=np.zeros((20,20));a[8,8]=1
    dense_continuous=np.full(a.shape,.001)  # continuous, not a dot set
    assert uniqueness.dot_overlap(a,dense_continuous)==0
    assert uniqueness.dot_overlap(np.zeros_like(a),dense_continuous)==0
    assert uniqueness.dot_overlap(a,np.zeros_like(a))==0
    # Binary dense with value 1.0 is a dot set and does overlap
    dense_binary=np.ones(a.shape)
    assert uniqueness.dot_overlap(a,dense_binary)==1


def test_constant_ranks_do_not_manufacture_edges():
    a=np.ones((40,40),np.float32);v=np.ones(a.shape,bool)
    r=method.rank01(a,v)
    assert np.ptp(r)==0
    fs=method.physical_features(a,a,a,v)
    assert all(not f.any() for f in fs.values())
    p=method.upper_surface(method.joint_field(fs,v),v)
    assert not p.any()


def test_release_reports_both_flags(tmp_path):
    from gems70.release import release_status
    p4=release_status(ROOT, phase='phase4')
    assert p4['download_ok'] is True and p4['submit_recommended'] is False
    real=release_status(ROOT)
    assert real['download_ok'] is True and real['submit_recommended'] is True
    assert release_status(tmp_path)['download_ok'] is False
    (tmp_path/'docs/downloads').mkdir(parents=True)
    (tmp_path/'docs/downloads/stale.tif').write_bytes(b'not-a-tiff')
    with pytest.raises(ValueError,match='Unauthorised'):assert_no_public_rasters(tmp_path)
    assert_no_public_rasters(ROOT)


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in {'href','src'} and v and not v.startswith(('http:','https:','#','mailto:')):self.links.append(v)


def test_pages_links_and_decision_banner():
    for p in (ROOT/'docs').glob('*.html'):
        text=p.read_text();parser=Links();parser.feed(text)
        for link in parser.links:assert (p.parent/link.split('#')[0].split('?')[0]).is_file(),(p,link)
    home=(ROOT/'docs/index.html').read_text()
    assert 'Download: yes.' in home
    assert 'Submit a weekly slot: recommended' in home
    assert 'DO NOT SUBMIT' in home


def test_full_brief_embedded_in_readme():
    readme=(ROOT/'README.md').read_text()
    assert (ROOT/'PROJECT_BRIEF.md').read_text() in readme
