#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor')]
import numpy as np, rasterio, json
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems57.grid import load_grid
from gems57 import holdout, evaluate_holdout

DATA = ROOT / '.cache/data'
GEMS = ROOT / '.cache/gems_data'
CLONE = Path('/tmp/60GEMSDOE')
H33 = CLONE / 'registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'

grid = load_grid(DATA)
fp, cat = grid.footprint, grid.catalogue
print("grid", fp.sum(), cat.sum(), flush=True)

feats={}
with rasterio.open(DATA / 'training_features.tif') as src:
    for i in range(1, src.count+1):
        desc = src.descriptions[i-1].split(' - ')[0].strip()
        a = src.read(i).astype(np.float32)
        a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
        feats[desc]=a
with rasterio.open(GEMS / 'external/lidar_scarp_features_u8.tif') as src:
    for i in range(1, src.count+1):
        desc = src.descriptions[i-1] or f'lidar_{i}'
        a = src.read(i).astype(np.float32); a[~fp]=np.nan
        feats[f'lidar_{desc}']=a
with rasterio.open(GEMS / 'external/geodawn_rad_u8.tif') as src:
    for i in range(1, src.count+1):
        desc = src.descriptions[i-1]
        a = src.read(i).astype(np.float32); a[~fp]=np.nan
        feats[f'rad_{desc}']=a
with rasterio.open(GEMS / 'external/geodawn_extensions_u8.tif') as src:
    for i in range(1, src.count+1):
        desc = src.descriptions[i-1]
        a = src.read(i).astype(np.float32); a[~fp]=np.nan
        feats[f'ext_{desc}']=a
names=list(feats.keys())
print(f"features {len(names)}", flush=True)

valid0=fp.copy()
for a in feats.values():
    valid0 &= np.isfinite(a)
valid=ndi.binary_erosion(valid0, iterations=12)
print(f"valid0 {valid0.sum()} valid {valid.sum()}", flush=True)

with rasterio.open(SGMC) as src:
    sgmc=src.read(1)>0
dcat=ndi.distance_transform_edt(~cat)
proxy=sgmc & ~cat & fp
proxy_prime=proxy & (dcat>=3)
print(f"proxy {proxy.sum()} prime {proxy_prime.sum()}", flush=True)

# quadrants
def quadrant_ids(fp):
    yy,xx=np.nonzero(fp); ym,xm=int(np.median(yy)),int(np.median(xx))
    gy,gx=np.ogrid[:fp.shape[0],:fp.shape[1]]
    q=np.full(fp.shape,-1,np.int8)
    q[(gy<ym)&(gx<xm)&fp]=0; q[(gy<ym)&(gx>=xm)&fp]=1
    q[(gy>=ym)&(gx<xm)&fp]=2; q[(gy>=ym)&(gx>=xm)&fp]=3
    return q
quad=quadrant_ids(fp)
quad_regions=[ndi.binary_erosion(quad==q, iterations=12)&fp for q in range(4)]

rng=np.random.default_rng(70020)
# Quick LOQO train/predict
from gems70 import method2
from scipy.stats import rankdata

oof_pred=np.full(fp.shape, np.nan, np.float32)

for q in range(4):
    print(f"Q{q}", flush=True)
    train_valid=valid.copy(); train_valid[quad_regions[q]]=False
    train_pos=train_valid & proxy_prime
    train_neg=train_valid & ~proxy
    pos_idx=np.flatnonzero(train_pos); neg_idx=np.flatnonzero(train_neg)
    print(f" pos {len(pos_idx)} neg {len(neg_idx)}", flush=True)
    # sample negatives
    if len(neg_idx)>120000:
        neg_idx=rng.choice(neg_idx, 120000, replace=False)
    if len(pos_idx)>40000:
        pos_idx=rng.choice(pos_idx, 40000, replace=False)
    Xp=np.stack([feats[n].ravel()[pos_idx] for n in names], axis=1)
    Xn=np.stack([feats[n].ravel()[neg_idx] for n in names], axis=1)
    X=np.vstack([Xp,Xn]); y=np.r_[np.ones(len(pos_idx)), np.zeros(len(neg_idx))]
    print(f" X {X.shape}", flush=True)
    clf=HistGradientBoostingClassifier(max_depth=6, max_iter=100, learning_rate=0.1, min_samples_leaf=30, random_state=20)
    clf.fit(X,y)
    print(f" fit q{q} done", flush=True)
    test_mask=valid & quad_regions[q]
    test_idx=np.flatnonzero(test_mask)
    Xt=np.stack([feats[n].ravel()[test_idx] for n in names], axis=1)
    prob=clf.predict_proba(Xt)[:,1]
    oof_pred.ravel()[test_idx]=prob
    # auc
    y_true=proxy_prime.ravel()[test_idx].astype(int)
    if y_true.sum()>0:
        print(f" AUC q{q} {roc_auc_score(y_true, prob):.4f}", flush=True)

print(f"oof finished nan {np.isnan(oof_pred[valid]).sum()} valid {valid.sum()}", flush=True)
# fill missing with median
oof_pred[np.isnan(oof_pred)&valid]=np.nanmedian(oof_pred[valid])
# rank
oof_rank=np.zeros(fp.shape, np.float32)
val_mask=valid & np.isfinite(oof_pred)
r=rankdata(oof_pred[val_mask], method='average')
oof_rank[val_mask]=((r-1)/(len(r)-1)).astype(np.float32)
print("rank done", flush=True)

# evaluate Holdout A
from gems57 import holdout, evaluate_holdout
folds,_=holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
def cropped(fold,p,valid):
    y,x=np.nonzero(fold['region'])
    y0,x0=max(0,int(y.min())-6),max(0,int(x.min())-6)
    y1,x1=min(p.shape[0],int(y.max())+7),min(p.shape[1],int(x.max())+7)
    sl=np.s_[y0:y1,x0:x1]
    sub={k:v[sl] for k,v in fold.items() if isinstance(v,np.ndarray) and v.shape==p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0,x0), global_shape=p.shape)

# dots
mask,cnt=method2.priority_thin(oof_rank, valid, target_n=38000)
print(f" candidate dots {cnt}", flush=True)
cand_field=mask.astype(np.float32)
random_dots=np.zeros(fp.shape,bool); ids=rng.choice(np.flatnonzero(valid),38000,replace=False); random_dots.ravel()[ids]=True
rand_field=random_dots.astype(np.float32)
with rasterio.open(H33) as src:
    h33=src.read(1).astype(np.float32)
h33_bin=np.where(np.isfinite(h33)&(h33>0.5)&fp,1.0,0.0).astype(np.float32)

arms={'candidate':cand_field,'random_control':rand_field,'h33_reference':h33_bin}
terms={k:0.0 for k in arms}
for fold in folds:
    for name,p in arms.items():
        r,t=cropped(fold,p,valid)
        terms[name]+=t
summary=evaluate_holdout.pooled_summary(terms, draws=500, seed=70420, candidate='candidate')
print("INSTRUMENT A", flush=True)
for k,v in summary['scores'].items():
    print(k, v['dti'], v['ci95'], flush=True)
for k,v in summary['paired_differences'].items():
    print(f"delta vs {k} {v['delta']} CI {v['ci95']}", flush=True)

# B' with OOF production same as candidate but with d>2 distance
dcat=ndi.distance_transform_edt(~cat)
# For B', produce dots using oof_rank but with catalogue exclusion >2
prod_mask, _ = method2.priority_thin(oof_rank, valid & (dcat>2), target_n=38000)
prod_field=prod_mask.astype(np.float32)
prod_arms={'candidate':prod_field,'random_control':rand_field,'h33_reference':h33_bin}
terms_b={k:0.0 for k in prod_arms}
quad2=holdout.quadrant_ids(fp)
for k in range(4):
    region=ndi.binary_erosion(quad2==k, iterations=12)&fp
    fold=dict(region=region, truth=proxy_prime & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
    for name,p in prod_arms.items():
        r,t=cropped(fold,p,valid)
        terms_b[name]+=t
summary_b=evaluate_holdout.pooled_summary(terms_b, draws=500, seed=70420, candidate='candidate')
print("INSTRUMENT B'", flush=True)
for k,v in summary_b['scores'].items():
    print(k, v['dti'], v['ci95'], flush=True)
for k,v in summary_b['paired_differences'].items():
    print(f"delta vs {k} {v['delta']} CI {v['ci95']}", flush=True)

# save
import json
Path('evidence/pilot2.json').write_text(json.dumps({'a':summary,'b':summary_b}, indent=2))
print("saved pilot2", flush=True)
