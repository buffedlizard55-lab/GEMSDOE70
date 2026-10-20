"""Synthetic SOFTWARE tests, never reported as scientific HOLDOUT-DTI results."""
import numpy as np
import pytest
from gems57 import metric, evaluate_holdout, uniqueness


@pytest.mark.parametrize('seed',range(6))
def test_soft_metric_matches_literal_equations(seed):
    rng=np.random.default_rng(seed)
    p=rng.random((9,12));p[p<.85]=0
    g=rng.random(p.shape)>.92
    exact=metric.dti_exact(p,g);brute=metric.dti_bruteforce(p,g)
    for key in ['tp','fp','fn','dti']:
        assert exact[key]==pytest.approx(brute[key],abs=1e-10)


@pytest.mark.parametrize('kind',['empty_prediction','empty_truth','perfect','soft','binary'])
def test_metric_edge_cases(kind):
    rng=np.random.default_rng(77)
    p=(rng.random((12,10))>.85).astype(float);g=rng.random(p.shape)>.88
    if kind=='empty_prediction':p[:]=0
    if kind=='empty_truth':g[:]=False
    if kind=='perfect':p=g.astype(float)
    if kind=='soft':p*=.4
    a=metric.dti_exact(p,g); b=metric.dti_bruteforce(p,g)
    assert a['dti']==pytest.approx(b['dti'])
    if kind=='binary':assert a['dti']==pytest.approx(metric.dti_binary(p>0,g)['dti'])


def test_visible_faults_are_pixel_exactly_masked_and_terms_pool():
    p=np.zeros((16,16));p[1,1]=1;p[10,10]=.7
    truth=np.zeros(p.shape,bool);truth[10,10]=True
    visible=np.zeros(p.shape,bool);visible[1,1]=True
    region=np.ones(p.shape,bool)
    fold={'truth':truth,'visible':visible,'region':region}
    r,t=evaluate_holdout.evaluate(p,fold,region,block_side=4)
    p[1,1]=0
    direct=metric.dti_exact(p,truth,known=visible)
    assert r['n_emitted']==1
    assert r['dti']==pytest.approx(direct['dti'])
    np.testing.assert_allclose(t.sum(axis=0),[r['tp'],r['fp'],r['fn'],r['n_truth']])


def test_pooled_summary_requires_aligned_truth_and_reports_ci():
    a=np.array([[1.,.5,1.,2.],[2.,.4,2.,4.],[.5,.1,.5,1.]])
    b=np.array([[.5,.8,1.5,2.],[1.,.8,3.,4.],[.2,.4,.8,1.]])
    r=evaluate_holdout.pooled_summary({'candidate':a,'control':b},candidate='candidate',draws=50)
    score=r['scores']['candidate']
    assert score['withheld_positive_pixels']==7
    assert len(score['ci95'])==2
    assert score['dti']==pytest.approx(float(evaluate_holdout.from_terms(a.sum(axis=0))))
    b[0,3]=3
    with pytest.raises(ValueError):evaluate_holdout.pooled_summary({'candidate':a,'control':b},candidate='candidate')


def test_literal_thresholds_are_strict_not_inclusive():
    assert uniqueness.RHO_LIMIT==.9
    assert uniqueness.OVERLAP_LIMIT==.7
    meta={'my_dots':3,'candidate_rank_variation':True}
    row={'submission':'toy','spearman_full_footprint':.9,'my_dots_within_3px_of_theirs':.7,
         'jaccard_dot_sets':0.,'duplicate_by_rho':False,'duplicate_by_overlap':False}
    r=uniqueness.summarize_registry_rows([row],registry_rasters_expected=1,
         complete_accessible_scan=True,source_errors=[],candidate_meta=meta,scope='synthetic software test')
    assert r['unique']
    row=dict(row,duplicate_by_overlap=True,my_dots_within_3px_of_theirs=.7000001)
    r=uniqueness.summarize_registry_rows([row],registry_rasters_expected=1,
         complete_accessible_scan=True,source_errors=[],candidate_meta=meta,scope='synthetic software test')
    assert not r['unique'] and r['stop_required']
