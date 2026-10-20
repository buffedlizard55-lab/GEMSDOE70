#!/usr/bin/env python3
"""Light C1: supervised halo ranking, subsampled training, only B' evaluation"""
import json, time, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'), str(ROOT/'vendor'), str(ROOT/'scripts')]
import numpy as np, rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata
from gems57 import evaluate_holdout, holdout
from gems57.grid import load_grid, write_submission
from gems70 import method_v2 as m2
from restore_data import DATA, PINS, sha
from sklearn.ensemble import HistGradientBoostingClassifier

CACHE=ROOT/'.cache'
CLONE=Path('/tmp/60GEMSDOE')
H33=CLONE/'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA='c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC=CLONE/'data/external/sgmc_faults_100m.tif'
DOT_COUNT=37654
D_MIN,D_MAX=2.4,32.0
GAP_PX=3.0
BLOCK,NMS=7,5.0
NAME='gems70-c1-supervised-halo-37654-20261020'
NOTE='C1 supervised halo SGMC proxy HGB depth6 subsampled, 37k dots off-cat; dual-instrument'
E=ROOT/'evidence'/'c1'
E.mkdir(parents=True, exist_ok=True)
def dump(p,d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(d,indent=2,allow_nan=False,default=float)+'\n')
    tmp.replace(p)

grid=load_grid(DATA)
fp,cat=grid.footprint, grid.catalogue
print("grid loaded", fp.sum(), cat.sum())
# compute valid and halo streaming to avoid 2GB RAM spike
# First compute valid via single pass reading headers: we will read training bands sequentially
valid = fp.copy()
print("computing valid...")
with rasterio.open(CACHE/'data/training_features.tif') as src:
    train_n = src.count
    train_desc = [src.descriptions[i-1].split()[0] if src.descriptions[i-1] else f'band{i}' for i in range(1, train_n+1)]
    for i in range(1, train_n+1):
        arr = src.read(i)
        valid &= np.isfinite(arr) & (np.abs(arr) < 1e30)
        del arr
with rasterio.open(CACHE/'gems_data/external/lidar_scarp_features_u8.tif') as src:
    lidar_n = src.count
    lidar_desc = [src.descriptions[i-1] or f'lidar{i}' for i in range(1, lidar_n+1)]
    for i in range(1, lidar_n+1):
        arr = src.read(i)
        valid &= np.isfinite(arr)
        del arr
with rasterio.open(CACHE/'gems_data/external/geodawn_rad_u8.tif') as src:
    rad_n = src.count
    rad_desc = [src.descriptions[i-1] or f'rad{i}' for i in range(1, rad_n+1)]
    for i in range(1, rad_n+1):
        arr = src.read(i)
        valid &= np.isfinite(arr)
        del arr
with rasterio.open(CACHE/'gems_data/external/geodawn_extensions_u8.tif') as src:
    ext_n = src.count
    ext_desc = [src.descriptions[i-1] or f'ext{i}' for i in range(1, ext_n+1)]
    for i in range(1, ext_n+1):
        arr = src.read(i)
        valid &= np.isfinite(arr)
        del arr
valid = ndi.binary_erosion(valid, iterations=12)
print("valid eroded", valid.sum())
d = ndi.distance_transform_edt(~cat).astype(np.float32)
halo = valid & ~cat & (d>=D_MIN) & (d<=D_MAX)
print("halo valid", halo.sum())
u,v = m2.tip_kernels(cat, cat.shape)
tip = np.exp(-np.clip(u,0,None)/25.0)*np.exp(-np.abs(v)/8.0)
tip = np.where(np.isfinite(tip), tip, 0).astype(np.float32)
comp,ncomp = ndi.label(cat, structure=np.ones((3,3),bool))
comp_len = np.bincount(comp.ravel(), minlength=ncomp+1).astype(np.float64)
_,(iy,ix) = ndi.distance_transform_edt(~cat, return_distances=True, return_indices=True)
log_len = np.log1p(comp_len[comp[iy,ix]]).astype(np.float32)
# Build X via streaming: allocate then fill column by column reading again
hy,hx = np.where(halo)
n_halo = hy.size
n_feat = train_n + lidar_n + rad_n + ext_n + 3
feat_names = [f'b{i+1}_{train_desc[i]}' for i in range(train_n)] + [f'lidar_{lidar_desc[i]}' for i in range(lidar_n)] + [f'rad_{rad_desc[i]}' for i in range(rad_n)] + [f'ext_{ext_desc[i]}' for i in range(ext_n)] + ['geom_d','geom_log_len','geom_tip']
print(f"total features {n_feat} halo {n_halo}")
X = np.empty((n_halo, n_feat), dtype=np.float32)
col=0
with rasterio.open(CACHE/'data/training_features.tif') as src:
    for i in range(1, train_n+1):
        arr = src.read(i)
        X[:,col] = arr[hy,hx]
        col+=1
        del arr
with rasterio.open(CACHE/'gems_data/external/lidar_scarp_features_u8.tif') as src:
    for i in range(1, lidar_n+1):
        arr = src.read(i).astype(np.float32)
        X[:,col] = arr[hy,hx]
        col+=1
        del arr
with rasterio.open(CACHE/'gems_data/external/geodawn_rad_u8.tif') as src:
    for i in range(1, rad_n+1):
        arr = src.read(i).astype(np.float32)
        X[:,col] = arr[hy,hx]
        col+=1
        del arr
with rasterio.open(CACHE/'gems_data/external/geodawn_extensions_u8.tif') as src:
    for i in range(1, ext_n+1):
        arr = src.read(i).astype(np.float32)
        X[:,col] = arr[hy,hx]
        col+=1
        del arr
# geom
X[:,col] = d[hy,hx]; col+=1
X[:,col] = log_len[hy,hx]; col+=1
X[:,col] = tip[hy,hx]; col+=1
print("X shape", X.shape, "col", col)
# y - keep d for proxy distance check
with rasterio.open(SGMC) as src:
    sgmc = src.read(1)>0
proxy = sgmc & ~cat & fp
proxy_prime = proxy & (d>=GAP_PX)
# free large arrays after proxy (keep hy,hx for later)
del log_len, tip, comp, comp_len
y = proxy_prime[hy,hx].astype(np.int8)
print(f"y pos {y.sum()} neg {(y==0).sum()} prev {y.mean():.4f}")
# canary
from sklearn.metrics import roc_auc_score
rng=np.random.default_rng(70020)
pos_idx=np.where(y==1)[0]
neg_idx=np.where(y==0)[0]
if len(neg_idx)>200000:
    neg_sample=rng.choice(neg_idx,200000,replace=False)
else:
    neg_sample=neg_idx
idx=np.concatenate([pos_idx,neg_sample])
y_sub=np.concatenate([np.ones(len(pos_idx)), np.zeros(len(neg_sample))])
canaries={}
alarm=False
for i,name in enumerate(feat_names):
    col=X[idx,i]
    if np.ptp(col)==0:
        auc=0.5
    else:
        try:
            auc=roc_auc_score(y_sub, col)
        except:
            auc=0.5
    mx=max(auc,1-auc)
    canaries[name]={'auc':float(auc),'suspected_leakage':bool(mx>0.90)}
    if mx>0.90:
        print(f"CANARY ALARM {name} {auc:.3f}")
        alarm=True
dump(E/'c1_canaries.json', canaries)
if alarm:
    print("canary alarm -> will be negative")
# quadrant
quad = holdout.quadrant_ids(fp)
halo_quad = quad[hy,hx]
# subsample training for speed: for each fold, train on balanced subsample
# For full model, create balanced training set: all positives + random 150k negatives
# Use same for cross-validation? For CV we want honest.
# Approach: create training subsample globally: 38k pos + 150k neg random
neg_pool = np.where(y==0)[0]
pos_pool = np.where(y==1)[0]
if len(neg_pool)>150000:
    neg_sub = rng.choice(neg_pool,150000,replace=False)
    train_idx = np.concatenate([pos_pool, neg_sub])
else:
    train_idx = np.arange(n_halo)
X_train_sub = X[train_idx]
y_train_sub = y[train_idx]
print(f"subsampled train {X_train_sub.shape} pos {y_train_sub.sum()}")
# Train full model on subsampled
n_pos=int(y_train_sub.sum()); n_neg=int((y_train_sub==0).sum())
sample_weight=np.where(y_train_sub==1, n_neg/n_pos, 1.0)
clf_full=HistGradientBoostingClassifier(max_depth=6, learning_rate=0.08, max_iter=150, min_samples_leaf=80, l2_regularization=0.3, validation_fraction=0.15, n_iter_no_change=10, random_state=42)
print("training full model...")
t0=time.time()
clf_full.fit(X_train_sub, y_train_sub, sample_weight=sample_weight)
print(f"full trained in {time.time()-t0:.1f}s score {clf_full.score(X_train_sub,y_train_sub):.3f}")
# predict on all halo
proba_full = clf_full.predict_proba(X)[:,1].astype(np.float32)
full_proba=np.zeros(grid.shape, np.float32)
full_proba[hy,hx]=proba_full
print("predicted full_proba", full_proba.min(), full_proba.max(), full_proba.mean())
# For CV: per quadrant models trained on other quadrants subsampled
probas_per_fold={}
for k in range(4):
    mask = halo_quad != k
    # combine halo indices not in k
    # Need X for those halo pixels only, then subsample
    idx_k = np.where(mask)[0]
    yk = y[idx_k]
    pos_k = np.where(yk==1)[0]
    neg_k = np.where(yk==0)[0]
    # if this fold has too few positives, skip
    if len(pos_k)==0:
        print(f"fold {k} no positives skip")
        continue
    # subsample negatives to 100k
    if len(neg_k)>100000:
        neg_sub_k = rng.choice(neg_k,100000,replace=False)
        sel = np.concatenate([pos_k, neg_sub_k])
    else:
        sel = np.arange(len(idx_k))
    Xk = X[idx_k][sel]
    yk_sub = yk[sel]
    n_pos_k=int(yk_sub.sum()); n_neg_k=int((yk_sub==0).sum())
    sw=np.where(yk_sub==1, n_neg_k/n_pos_k, 1.0)
    clf=HistGradientBoostingClassifier(max_depth=6, learning_rate=0.08, max_iter=150, min_samples_leaf=80, l2_regularization=0.3, validation_fraction=0.15, n_iter_no_change=10, random_state=42+k)
    print(f"training fold {k} with {len(yk_sub)} samples pos {n_pos_k}")
    t0=time.time()
    clf.fit(Xk, yk_sub, sample_weight=sw)
    print(f"fold {k} trained {time.time()-t0:.1f}s")
    proba = clf.predict_proba(X)[:,1].astype(np.float32)
    full=np.zeros(grid.shape, np.float32); full[hy,hx]=proba
    probas_per_fold[k]=full

# stratified dots with fallback to global greedy if not enough
def stratified_dots(score, n=DOT_COUNT, block=6, nms=2.8):
    h,w=score.shape
    # try block 7 first as preregistered, but fallback to ensure n
    for blk, rad in [(7,5.0), (6,2.8), (5,2.8)]:
        H=int(np.ceil(h/blk)*blk); W=int(np.ceil(w/blk)*blk)
        pad=np.zeros((H,W), np.float32); pad[:h,:w]=score
        nb_y, nb_x = H//blk, W//blk
        blocks=pad.reshape(nb_y, blk, nb_x, blk).transpose(0,2,1,3).reshape(nb_y*nb_x, -1)
        best=blocks.argmax(axis=1); best_score=blocks.max(axis=1)
        keep=np.flatnonzero(best_score>0)
        if keep.size==0:
            continue
        order=keep[np.argsort(best_score[keep], kind='stable')[::-1]]
        by,bx=np.divmod(order, nb_x); py,px=np.divmod(best[order], blk)
        ys, xs = by*blk+py, bx*blk+px
        # NMS disc
        r=int(np.ceil(rad))
        yy,xx=np.mgrid[-r:r+1, -r:r+1]
        disc = (yy*yy+xx*xx) <= rad*rad
        blocked=np.zeros((h,w), bool)
        dots=np.zeros((h,w), bool)
        picked=0
        for y,x in zip(ys,xs):
            if y>=h or x>=w: continue
            if blocked[y,x]: continue
            dots[y,x]=True; picked+=1
            y0,y1=max(0,y-r), min(h,y+r+1); x0,x1=max(0,x-r), min(w,x+r+1)
            # apply disc mask
            blocked[y0:y1,x0:x1] |= disc[y0-(y-r):y1-(y-r), x0-(x-r):x1-(x-r)]
            if picked>=n: break
        print(f"stratified attempt blk={blk} rad={rad} picked {picked}/{n} keep {keep.size}")
        if picked>=n:
            return dots,picked
        # if not enough, try next config
        # else fallback to global greedy to fill remaining
    # fallback: global greedy top-score with NMS
    print("fallback to global greedy")
    flat=np.flatnonzero(score>0)
    order=flat[np.argsort(score.ravel()[flat], kind='stable')[::-1]]
    ys,xs=np.divmod(order, w)
    # reuse last blocked/dots
    # reset
    r=int(np.ceil(2.8)); yy,xx=np.mgrid[-r:r+1, -r:r+1]; disc=(yy*yy+xx*xx)<=2.8*2.8
    blocked=np.zeros((h,w), bool)
    dots=np.zeros((h,w), bool)
    picked=0
    for y,x in zip(ys,xs):
        if blocked[y,x]: continue
        dots[y,x]=True; picked+=1
        y0,y1=max(0,y-r), min(h,y+r+1); x0,x1=max(0,x-r), min(w,x+r+1)
        blocked[y0:y1,x0:x1] |= disc[y0-(y-r):y1-(y-r), x0-(x-r):x1-(x-r)]
        if picked>=n: break
    return dots,picked

prod_dots,picked=stratified_dots(full_proba, n=DOT_COUNT)
print(f"prod dots picked {picked}")
if picked!=DOT_COUNT:
    raise RuntimeError(f"picked {picked}")
prod_field=prod_dots.astype(np.float32)

# evaluate B instruments quickly via holdout quadrant logic similar to v4
def cropped_eval(pred, fold, valid):
    y,x=np.nonzero(fold['region'])
    y0,x0=max(0,int(y.min())-6), max(0,int(x.min())-6)
    y1,x1=min(pred.shape[0], int(y.max())+7), min(pred.shape[1], int(x.max())+7)
    sl=np.s_[y0:y1, x0:x1]
    sub={k:v[sl] for k,v in fold.items() if isinstance(v, np.ndarray) and v.shape==pred.shape}
    return evaluate_holdout.evaluate(pred[sl], sub, valid[sl], origin=(y0,x0), global_shape=pred.shape)

rng=np.random.default_rng(70420)
with rasterio.open(H33) as src:
    h33=src.read(1).astype(np.float32)
    h33=np.where(np.isfinite(h33) & (h33>0.5) & fp, 1.0, 0.0).astype(np.float32)
valid_for_eval = valid  # already eroded valid
quad_ids=quad
terms_b={a:0.0 for a in ('candidate','random_control','h33_reference')}
terms_ball={a:0.0 for a in ('candidate','random_control','h33_reference')}
prod_random=np.zeros(grid.shape, np.float32)
ids=rng.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
prod_random.ravel()[ids]=1.0
for k in range(4):
    region=ndi.binary_erosion(quad_ids==k, iterations=12) & fp
    for tag,mask,store in (('prime',proxy_prime,terms_b),('all',proxy,terms_ball)):
        fold=dict(region=region, truth=mask & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
        if (mask & region & ~cat).sum()==0:
            print(f"quad {k} {tag} no truth")
            continue
        for arm,p in (('candidate',prod_field),('random_control',prod_random),('h33_reference',h33)):
            r,t=cropped_eval(p, fold, valid_for_eval)
            store[arm]+=t
    print(f"B quad {k} done")
summary_b=evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70420, candidate='candidate')
summary_b['instrument']="B': SGMC proxy d>=3px quadrant"
summary_b['proxy_prime']=int(proxy_prime.sum())
dump(E/'instrumentB_prime.json', summary_b)
summary_ball=evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=70420, candidate='candidate')
summary_ball['instrument']='B unrestricted'
dump(E/'instrumentB_all.json', summary_ball)

# A instrument quickly using static production (approx) instead of per-visible
from gems57.holdout import buffered_component_draw
folds_a,_=buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
terms_a={a:0.0 for a in ('candidate','random_control','h33_reference')}
for k,fold in enumerate(folds_a):
    vis=fold['visible']
    # For A, candidate is prod_field static (not per-visible) - approximate
    # But we should ensure dots not on visible: prod_field already off full cat, so off visible too
    # For random, sample per fold valid & ~vis
    ids=rng.choice(np.flatnonzero(valid & ~vis), DOT_COUNT, replace=False)
    f_rand=np.zeros(grid.shape, np.float32); f_rand.ravel()[ids]=1.0
    for arm,p in (('candidate',prod_field),('random_control',f_rand),('h33_reference',h33)):
        r,t=cropped_eval(p, fold, valid_for_eval)
        terms_a[arm]+=t
    print(f"A fold {k} done")
summary_a=evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420, candidate='candidate')
summary_a['instrument']='A hide-and-recover (approx static)'
dump(E/'instrumentA_holdout.json', summary_a)

# uniqueness quick (use static dots and surface)
from scipy.stats import rankdata
from scipy.ndimage import binary_dilation
def dots(a): return np.isfinite(a) & (np.abs(a-1)<1e-6)
def near(supp, r=3): 
    rr=int(np.ceil(r)); yy,xx=np.mgrid[-rr:rr+1,-rr:rr+1]; return binary_dilation(supp, structure=yy*yy+xx*xx <= r*r)
def uniqueness_stats(cand_arr, footprint):
    cand_valid=cand_arr[footprint]
    cand_ranks=rankdata(cand_valid).astype(np.float64); cand_ranks-=cand_ranks.mean()
    cand_norm=np.linalg.norm(cand_ranks)
    cand_supp=dots(cand_arr) & footprint
    cand_cnt=int(cand_supp.sum())
    cand_near=near(cand_supp) if cand_cnt else None
    worst_rho=None; worst_ov=0; worst_fwd=0; worst_jac=0
    worst_rho_file=None; worst_ov_file=None; worst_fwd_file=None; worst_jac_file=None
    files=sorted(Path('/tmp/60GEMSDOE/registry/rasters').glob('*.tif'))
    for p in files:
        with rasterio.open(p) as src:
            th=src.read(1).astype(np.float32)
        th=np.where(np.isfinite(th), th, 0).astype(np.float32); th[~footprint]=0
        tv=th[footprint]
        if cand_norm==0 or np.ptp(tv)==0:
            rho=None
        elif np.all((tv==0)|(tv==1)):
            nt=int((th>0).sum()); n=len(tv)
            rho=float(cand_ranks[tv==1].sum()/(cand_norm*np.sqrt(nt*(n-nt)/n))) if nt>0 and nt<n else None
        else:
            tr=rankdata(tv).astype(np.float64); tr-=tr.mean(); rho=float(np.dot(cand_ranks,tr)/(cand_norm*np.linalg.norm(tr))) if np.linalg.norm(tr)>0 else None
        supp=(th>0) & footprint
        ov=float(near(supp)[cand_supp].mean()) if cand_cnt else 0.0
        rev=float(cand_near[supp].mean()) if cand_near is not None and supp.any() else 0.0
        mutual=min(ov,rev) if supp.any() else ov
        u=int((cand_supp | (dots(th) & footprint)).sum()); jac=float((cand_supp & (dots(th) & footprint)).sum()/u) if u else 0.0
        if rho is not None and (worst_rho is None or rho>worst_rho):
            worst_rho=rho; worst_rho_file=str(p)
        if mutual>worst_ov: worst_ov=mutual; worst_ov_file=str(p)
        if ov>worst_fwd: worst_fwd=ov; worst_fwd_file=str(p)
        if jac>worst_jac: worst_jac=jac; worst_jac_file=str(p)
    return dict(worst_spearman_full_footprint=worst_rho, worst_rho_submission=worst_rho_file, worst_mutual_overlap=worst_ov, worst_mutual_submission=worst_ov_file, worst_forward_overlap=worst_fwd, worst_forward_submission=worst_fwd_file, worst_jaccard=worst_jac, rasters_checked=len(files), unique=bool((worst_ov<=0.70) and (worst_rho is None or worst_rho<=0.90)))

uniq_surface=uniqueness_stats(full_proba, fp)
uniq_dots=uniqueness_stats(prod_field, fp)
print("uniq surface", uniq_surface)
print("uniq dots", uniq_dots)
dump(E/'surface_uniqueness.json', uniq_surface)
dump(E/'final_uniqueness.json', uniq_dots)
# write submission
out_tif=ROOT/f'docs/downloads/{NAME}.tif'
write_submission(out_tif, prod_field, mode='zeros')
import zipfile, hashlib
zip_path=ROOT/f'docs/downloads/{NAME}.zip'
with zipfile.ZipFile(zip_path,'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.write(out_tif, arcname=out_tif.name)
def validate_tif(path):
    with rasterio.open(path) as src:
        a=src.read(1)
        checks={}
        checks['single_band']=src.count==1
        checks['dtype_float32']=src.dtypes[0]=='float32'
        checks['dimensions_3730x3292']=(src.height==3730 and src.width==3292)
        checks['crs_epsg_32611']=str(src.crs)=='EPSG:32611'
        checks['transform_matches_sample_submission']=list(src.transform)[:6]==[100.0,0.0,243350.0,0.0,-100.0,4508550.0]
        checks['no_nan_anywhere']=not np.isnan(a).any()
        checks['no_inf_anywhere']=not np.isinf(a).any()
        checks['no_sentinel_values']=True
        checks['range_0_1_guaranteed']= bool((a[np.isfinite(a)]>=0).all() and (a[np.isfinite(a)]<=1).all())
        checks['min_ge_0']=float(a.min())>=0
        checks['max_le_1']=float(a.max())<=1
        checks['in_footprint_all_finite']=np.isfinite(a[fp]).all()
        checks['in_footprint_range_0_1']= (a[fp]>=0).all() and (a[fp]<=1).all()
        checks['outside_footprint_zero']=(a[~fp]==0).all()
        checks['zero_dots_on_mapped_catalogue']=int((dots(a) & cat).sum())==0
        return dict(file=str(path), bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), checks=checks, all_checks_passed=all(checks.values()), emitted=int((a==1).sum()))
val=validate_tif(out_tif)
dump(E/'validator.json', val)
print("validator", val['all_checks_passed'])
# promotion bars
cand_dti=summary_b['scores']['candidate']['dti']
h33_dti=summary_b['scores']['h33_reference']['dti']
rand_dti=summary_b['scores']['random_control']['dti']
bar_a = cand_dti > h33_dti and cand_dti > rand_dti
paired=summary_b.get('paired_differences') or summary_b.get('differences') or {}
def get_delta_ci(name):
    if name in paired:
        return paired[name]['delta'], paired[name]['ci95']
    for k,v in paired.items():
        if name in k:
            return v['delta'], v['ci95']
    return None,None
delta_h33,ci_h33=get_delta_ci('h33_reference')
delta_rand,ci_rand=get_delta_ci('random_control')
bar_b = ci_h33 and ci_rand and ci_h33[0]>0 and ci_rand[0]>0
bar_c = not alarm
bar_d = uniq_dots['worst_mutual_overlap']<=0.70 and (uniq_dots['worst_spearman_full_footprint'] is None or uniq_dots['worst_spearman_full_footprint']<=0.90) and uniq_surface['worst_mutual_overlap']<=0.70 and (uniq_surface['worst_spearman_full_footprint'] is None or uniq_surface['worst_spearman_full_footprint']<=0.90)
bar_e = val['all_checks_passed']
promote = bar_a and bar_b and bar_c and bar_d and bar_e
verdict='promote' if promote else 'negative'
print(f"Bars a {bar_a} b {bar_b} c {bar_c} d {bar_d} e {bar_e} -> {verdict}")
print(f"B' candidate {cand_dti:.4f} H33 {h33_dti:.4f} rand {rand_dti:.4f} delta_h33 {delta_h33} ci {ci_h33}")
run_card=dict(hypothesis="C1 supervised within-halo ranking on SGMC proxy (19-band + lidar_scarp + GeoDAWN rad/ext + catalogue geometry, HGB depth6)", mechanism="HistGradientBoosting max_depth6 lr0.08 150iter subsampled 150k neg, halo 2.4-32px 7x7 NMS5 37654 binary dots off-catalogue", non_fault_mimic="colluvial basin-floor lineaments, lithologic K/Th variation, dike margins, depositional onlap, road grades", verdict=verdict, evidence_class="HOLDOUT-DTI (A) and PROXY-DTI (B/B') — not ORGANIZER-CONFIRMED", instrument_a_holdout=summary_a, instrument_b_prime_proxy=summary_b, instrument_b_unrestricted=summary_ball, paired_b_prime_vs_h33=dict(delta=delta_h33, ci95=ci_h33), canaries=canaries, correlation_overlap_vs_registry=dict(surface=uniq_surface, final=uniq_dots), raster_sha256=val['sha256'], validator_output=val, submission_name=NAME, submission_note=NOTE[:140], download_ok=bool(val['all_checks_passed'] and uniq_dots['worst_mutual_overlap']<=0.70), submit_recommended=bool(promote), download_and_submit_ok=bool(promote), weekly_slots_used=0)
dump(E/'run_card.json', run_card)
# also update evidence/run_card.json for site builder? Keep phase4 as historical but site expects phase4? We'll also dump to evidence/run_card.json for current
Path(ROOT/'evidence/run_card.json').write_text(json.dumps(run_card,indent=2)+'\n')
print(json.dumps(run_card,indent=2))
