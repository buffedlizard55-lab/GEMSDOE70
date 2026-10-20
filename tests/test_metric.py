"""Independent tiny-array oracle tests, not a private production evaluator."""
import numpy as np
import pytest
from gems57 import metric, evaluate_holdout


def oracle(p,g):
    truth=np.argwhere(g)
    dots=np.argwhere(p>0)
    k=lambda a,b:max(1-np.linalg.norm(a-b)/3,0)
    tp=sum(max([p[tuple(x)]*k(t,x) for x in dots]+[0]) for t in truth)
    fp=sum(p[tuple(x)]*(1-max([k(t,x) for t in truth]+[0])) for x in dots)
    return tp,fp,int(g.sum())-tp


@pytest.mark.parametrize('seed',range(5))
def test_exact_matches_independent_bruteforce(seed):
    rng=np.random.default_rng(seed)
    p=rng.random((8,9))*(rng.random((8,9))<.2)
    g=rng.random((8,9))<.1
    result=metric.dti_exact(p,g)
    expected=oracle(p,g)
    np.testing.assert_allclose([result['tp'],result['fp'],result['fn']],expected,atol=1e-10)


def test_marginal_coverage_is_not_bounded_by_self_credit():
    p=np.zeros((11,11));g=np.zeros((11,11),bool)
    p[5,5]=1;g[5,5:7]=True
    r=metric.dti_exact(p,g)
    assert r['tp']==pytest.approx(1+2/3)
    assert r['tp']>1  # dot self-credit is exactly one; do not use dT <= k.


def test_pooled_terms_and_known_pixel_exact_mask():
    p=np.zeros((30,30));g=np.zeros_like(p,bool);known=np.zeros_like(g)
    p[12,12]=1;g[12,12]=True
    p[22,22]=1;g[22,22]=True
    p[17,17]=1;known[17,17]=True
    fold={'region':np.ones_like(g),'truth':g,'visible':known,'masked_known':known}
    r,t=evaluate_holdout.evaluate(p,fold,np.ones_like(g),block_side=10)
    assert r['dti']==pytest.approx(1)
    assert r['fp']==0
    summary=evaluate_holdout.pooled_summary({'candidate':t,'control':t.copy()},draws=50,candidate='candidate')
    assert summary['scores']['candidate']['withheld_positive_pixels']==2
    assert summary['paired_differences']['control']['delta']==0


@pytest.mark.parametrize('value',[np.nan,np.inf,-.01,1.01])
def test_evaluator_rejects_invalid_values(value):
    p=np.zeros((6,6));p[0,0]=value
    g=np.zeros_like(p,bool);g[3,3]=True
    f={'region':np.ones_like(g),'truth':g,'visible':np.zeros_like(g)}
    with pytest.raises(ValueError): evaluate_holdout.evaluate(p,f,np.ones_like(g))
