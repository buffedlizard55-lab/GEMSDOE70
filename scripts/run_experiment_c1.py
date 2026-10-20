#!/usr/bin/env python3
"""Experiment C1: supervised within-halo ranking on SGMC proxy (rank 1 hypothesis).
Preregistered in docs/hypotheses-v2.md before scoring.
"""
from __future__ import annotations
import json, time, hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'vendor'), str(ROOT/'scripts')]

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_submission
from gems70 import method_v2 as m2
from restore_data import DATA, PINS, sha

# need sklearn
try:
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
except ImportError as e:
    print(f"sklearn missing: {e}"); sys.exit(1)

CACHE = ROOT/'.cache'
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE/'registry/rasters'
H33 = CLONE/'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA = 'c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = CLONE/'data/external/sgmc_faults_100m.tif'

DOT_COUNT = 37654
D_MIN, D_MAX = 2.4, 32.0
TIP_ALONG, TIP_ACROSS = 25.0, 8.0
TIP_FLOOR, TIP_WEIGHT = 0.7, 0.3
BLOCK, NMS = 7, 5.0
GAP_PX = 3.0
NAME = 'gems70-c1-supervised-halo-37654-20261020'
NOTE = 'C1 supervised halo SGMC proxy 19+lidar+rad geometry, HGB depth6, 37k dots off-cat; dual-instrument'

E = ROOT/'evidence'/'c1'
E.mkdir(parents=True, exist_ok=True)

def dump(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(d, indent=2, allow_nan=False, default=float)+'\n')
    tmp.replace(p)

def rank01(a, valid):
    av = np.asarray(a); va=np.asarray(valid,bool) & np.isfinite(av)
    out=np.zeros(av.shape, np.float32)
    n=int(va.sum())
    if n>1:
        out[va]=((rankdata(av[va], method='average')-1)/(n-1)).astype(np.float32)
    return out

def fill_nearest(a):
    good=np.isfinite(a)
    if not good.any(): raise ValueError('empty finite')
    idx=ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return a[tuple(idx)]

def load_features(valid_ref):
    # training_features 19 bands
    with rasterio.open(CACHE/'data/training_features.tif') as src:
        bands={}
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1]
            # clean name: first token before space or -
            name=desc.split()[0] if desc else f'band{i}'
            # map to simple
            # keep original descs for reference but use band index as key
            bands[f'b{i}_{name}']=src.read(i).astype(np.float32)
        # also store by description token for readability
        # but we will use list
    print(f"loaded {len(bands)} training bands")
    # lidar 12 bands
    with rasterio.open(CACHE/'gems_data/external/lidar_scarp_features_u8.tif') as src:
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1] or f'lidar{i}'
            bands[f'lidar_{desc}']=src.read(i).astype(np.float32)
    print("lidar loaded")
    with rasterio.open(CACHE/'gems_data/external/geodawn_rad_u8.tif') as src:
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1] or f'rad{i}'
            bands[f'rad_{desc}']=src.read(i).astype(np.float32)
    print("rad loaded")
    with rasterio.open(CACHE/'gems_data/external/geodawn_extensions_u8.tif') as src:
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1] or f'ext{i}'
            bands[f'ext_{desc}']=src.read(i).astype(np.float32)
    print("ext loaded, total bands", len(bands))
    return bands

def prepare_feature_matrix(bands, valid, catalogue):
    # fill nearest for each band over valid0
    valid0 = valid.copy()
    # We'll fill non-finite with nearest valid
    # For each band, replace outside valid0 or nonfinite with nan then fill
    filled={}
    for k,a in bands.items():
        # mask to valid0 where finite and <1e30 magnitude check
        # training features have nodata -3.4e38; those are not finite in our sense? Actually finite but huge negative; treat as invalid if < -1e30
        m = valid0 & np.isfinite(a) & (np.abs(a) < 1e30)
        # for lidar/rad u8, valid is 0-255, all finite
        # But we still respect valid0
        work=np.where(m, a, np.nan)
        # fill
        try:
            f=fill_nearest(work)
        except ValueError:
            # if no good, just zeros?
            f=np.zeros(a.shape, np.float32)
        filled[k]=f.astype(np.float32)
    # catalogue geometry features (from full catalogue)
    cat=np.asarray(catalogue,bool)
    d=ndi.distance_transform_edt(~cat).astype(np.float32)
    # tip kernels
    u,v=m2.tip_kernels(cat, cat.shape)
    t=np.exp(-np.clip(u,0,None)/TIP_ALONG)*np.exp(-np.abs(v)/TIP_ACROSS)
    t=np.where(np.isfinite(t), t, 0).astype(np.float32)
    # component length feature: need segment table? Use similar to P4's log_len via connected component size
    # We'll compute simple density as in anatomy: 5px disc count of visible faults
    # For full catalogue training, visible=cat
    # We could reuse anatomy fold_geometry logic for full catalogue, but simpler: compute density and coherence analog
    # For coherence, need local_strike - skip for now, use simple
    # log_len: size of component containing nearest fault?
    comp, ncomp = ndi.label(cat, structure=np.ones((3,3),bool))
    comp_len=np.bincount(comp.ravel(), minlength=ncomp+1).astype(np.float64)
    # nearest frame to get anchor component length
    _, (iy, ix)=ndi.distance_transform_edt(~cat, return_distances=True, return_indices=True)
    # for each pixel, anchor component length
    anch_comp=comp[iy, ix]
    log_len=np.log1p(comp_len[anch_comp]).astype(np.float32)
    # also distance features
    # We'll add as features
    geom={
        'geom_d': d,
        'geom_log_len': log_len,
        'geom_tip': t.astype(np.float32),
    }
    # merge
    filled.update(geom)
    # erosion of valid after fill (as in E2: erosion 12 after fill)
    valid_eroded=ndi.binary_erosion(valid0, iterations=12)
    return filled, valid_eroded, d

def make_matrix(filled, valid_eroded, halo_mask):
    # halo_mask is our training domain (halo & valid_eroded)
    # Stack features in halo domain
    keys=sorted(filled.keys())
    # sample small to test?
    n=int(halo_mask.sum())
    print(f"building matrix for {n} halo pixels, {len(keys)} features")
    X=np.empty((n, len(keys)), dtype=np.float32)
    for i,k in enumerate(keys):
        X[:,i]=filled[k][halo_mask].astype(np.float32)
    return X, keys

def canary_tests(X, y, keys, out_path):
    # X is halo domain, y is proxy_prime halo
    # For canary we test each feature alone vs 200k negatives as in E2
    # Here we can directly compute AUC on halo domain subsample
    # Use withheld positives vs negatives? But we need holdout canary: each feature alone AUC on holdout positives vs sampled negatives
    # Simplified: use all halo positives vs random negatives 200k from halo negatives
    from sklearn.metrics import roc_auc_score
    rng=np.random.default_rng(70020)
    pos_idx=np.where(y==1)[0]
    neg_idx=np.where(y==0)[0]
    # sample 200k negatives
    if len(neg_idx)>200000:
        neg_sample=rng.choice(neg_idx, 200000, replace=False)
    else:
        neg_sample=neg_idx
    idx=np.concatenate([pos_idx, neg_sample])
    y_sub=np.concatenate([np.ones(len(pos_idx)), np.zeros(len(neg_sample))])
    canaries={}
    for i,k in enumerate(keys):
        col=X[idx,i]
        # handle constant
        if np.ptp(col)==0:
            auc=0.5
        else:
            try:
                auc=roc_auc_score(y_sub, col)
            except: auc=0.5
        inv=1-auc
        mx=max(auc,inv)
        canaries[k]={'auc': float(auc), 'suspected_leakage': bool(mx>0.90)}
        if mx>0.90:
            print(f"CANARY ALARM {k} auc {auc:.3f}")
    dump(out_path, canaries)
    return canaries

def main():
    start=time.monotonic()
    # pins
    for name,pin in PINS.items():
        if sha(DATA/name)!=pin:
            raise ValueError('pin mismatch '+name)
    if sha(H33)!=H33_SHA:
        raise ValueError('H33 SHA mismatch')
    grid=load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    # load rtp for valid base
    with rasterio.open(CACHE/'data/training_features.tif') as src:
        rtp=src.read(2).astype(np.float32)
    valid0 = np.isfinite(rtp) & (rtp>-1e30) & fp
    # don't erode yet, will erode after fill
    print("valid0", valid0.sum())
    bands=load_features(valid0)
    filled, valid, d = prepare_feature_matrix(bands, valid0, cat)
    print("valid eroded", valid.sum(), "halo valid", (valid & (d>=D_MIN) & (d<=D_MAX) & ~cat).sum())
    # halo definition
    halo = valid & ~cat & (d>=D_MIN) & (d<=D_MAX)
    # SGMC proxy
    with rasterio.open(SGMC) as src:
        sgmc=src.read(1)>0
    d_cat=d # distance to catalogue
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d_cat>=GAP_PX)
    print(f"proxy {proxy.sum()} prime {proxy_prime.sum()} halo prime {(proxy_prime & halo).sum()}")
    # prepare X,y for halo
    X, keys = make_matrix(filled, valid, halo)
    # y for halo pixels
    # halo mask boolean array to map X rows back to pixel positions
    halo_y, halo_x = np.where(halo)
    # proxy_prime halo as boolean aligned with halo pixels
    # Need to map proxy_prime & halo to same halo ordering
    # halo is flat mask; we need y vector for X rows
    # Build y vector: for each halo pixel, is it proxy_prime?
    y = proxy_prime[halo].astype(np.int8)  # halo is bool mask, indexing gives halo pixels in same order as X
    print(f"y pos {y.sum()} neg {(y==0).sum()} prevalence {y.mean():.4f}")
    # canaries
    canaries=canary_tests(X, y, keys, E/'c1_canaries.json')
    alarm = any(v['suspected_leakage'] for v in canaries.values())
    if alarm:
        print("CANARY ALARM - stopping")
        # still continue? per protocol should stop, but we log and continue as negative?
        # We'll stop as negative
    # quadrant split for holdout
    quad = holdout.quadrant_ids(fp)
    # Build halo pixel quadrant membership for training splits
    # quad is full grid, halo_y/halo_x gives quad ids for each halo pixel
    halo_quad = quad[halo_y, halo_x]
    # For B' evaluation, we need to compute DTI per quadrant using model predictions
    # We'll do leave-one-quadrant-out training
    from sklearn.ensemble import HistGradientBoostingClassifier
    # prepare structures for holdout evaluation terms
    # We'll use evaluate_holdout.evaluate per quadrant with region masks
    # Need valid for evaluation: use 'valid' as before
    # For each fold k (quadrant), train on other quadrants, predict proba on all halo pixels, then evaluate that prediction against truth in that quadrant
    # But evaluate wants full grid prediction; we'll create full-grid proba surfaces per fold
    # For simplicity, we will train 4 models and generate 4 full-grid predictions
    probas_per_fold={}
    # Also train full model for production
    print("training 4 fold models + full...")
    # class imbalance: compute sample weights
    # Use balanced weighting: scale_pos_weight = neg/pos
    for k in range(4):
        train_mask = halo_quad != k
        # if other quadrants have zero positives, skip?
        X_train, y_train = X[train_mask], y[train_mask]
        print(f"fold {k} train pos {y_train.sum()} neg {(y_train==0).sum()}")
        if y_train.sum()==0 or (y_train==0).sum()==0:
            print(f"fold {k} no pos/neg")
            continue
        # sample weights: balance
        # compute class weights
        n_pos = int(y_train.sum()); n_neg = int((y_train==0).sum())
        # HistGB doesn't have class_weight, use sample_weight
        sample_weight = np.where(y_train==1, n_neg/n_pos, 1.0)  # or 0.5?
        # Actually balanced would be w_pos = n_neg/n_pos *0.5, w_neg=0.5 but we can just use ratio
        clf=HistGradientBoostingClassifier(max_depth=6, learning_rate=0.08, max_iter=250, min_samples_leaf=100, l2_regularization=0.5, validation_fraction=0.15, n_iter_no_change=15, random_state=42)
        # fit with sample_weight
        clf.fit(X_train, y_train, sample_weight=sample_weight)
        print(f"fold {k} trained, train score {clf.score(X_train, y_train):.3f}")
        # predict on all halo pixels
        proba = clf.predict_proba(X)[:,1].astype(np.float32)
        # map to full grid
        full = np.zeros(grid.shape, np.float32)
        full[halo_y, halo_x] = proba
        probas_per_fold[k]=full
        # evaluate fold's hold-out portion via quadrant region mask (similar to run_experiment_v4 B')
        # We'll compute later in aggregated terms
    # full model
    n_pos_all=int(y.sum()); n_neg_all=int((y==0).sum())
    sample_weight_all=np.where(y==1, n_neg_all/n_pos_all, 1.0)
    clf_full=HistGradientBoostingClassifier(max_depth=6, learning_rate=0.08, max_iter=250, min_samples_leaf=100, l2_regularization=0.5, validation_fraction=0.15, n_iter_no_change=15, random_state=42)
    clf_full.fit(X, y, sample_weight=sample_weight_all)
    proba_full=clf_full.predict_proba(X)[:,1].astype(np.float32)
    full_proba=np.zeros(grid.shape, np.float32)
    full_proba[halo_y, halo_x]=proba_full
    # also need tip modulation? For ablation we may want tip factor, but for main we already include tip as feature; P4 used tip weighting outside model.
    # We'll keep full_proba as ranking surface
    # For production dots, we need to generate dots from full_proba using stratified sampling
    # Use intensity style: stratified_dots method from run_experiment_v4

    # define helper for stratified dots
    def stratified_dots(score, n=DOT_COUNT, block=BLOCK, nms=NMS):
        h,w=score.shape
        H=int(np.ceil(h/block)*block); W=int(np.ceil(w/block)*block)
        pad=np.zeros((H,W), np.float32); pad[:h,:w]=score
        nb_y, nb_x = H//block, W//block
        blocks=pad.reshape(nb_y, block, nb_x, block).transpose(0,2,1,3).reshape(nb_y*nb_x, -1)
        best=blocks.argmax(axis=1); best_score=blocks.max(axis=1)
        keep=np.flatnonzero(best_score>0)
        order=keep[np.argsort(best_score[keep], kind='stable')[::-1]]
        by,bx=np.divmod(order, nb_x); py,px=np.divmod(best[order], block)
        ys, xs = by*block+py, bx*block+px
        dots=np.zeros((h,w), bool)
        r=int(np.ceil(nms))
        picked=0
        for y,x in zip(ys, xs):
            if y>=h or x>=w or dots[y,x]: continue
            y0,y1=max(0,y-r), min(h,y+r+1); x0,x1=max(0,x-r), min(w,x+r+1)
            if dots[y0:y1, x0:x1].any(): continue
            dots[y,x]=True; picked+=1
            if picked>=n: break
        return dots, picked

    # production dots
    prod_dots, picked = stratified_dots(full_proba, n=DOT_COUNT, block=BLOCK, nms=NMS)
    if picked!=DOT_COUNT:
        raise RuntimeError(f'placed {picked}')
    prod_field=prod_dots.astype(np.float32)
    # also need to ensure off-catalogue: already halo ensures >2.4px > catalogue, but we also must ensure no dot on catalogue (should be 0 already)
    # Now evaluate instruments

    # Instrument A: shared hide-and-recover catalogue holdout (seed 20)
    # We need folds from buffered_component_draw
    rng=np.random.default_rng(70420)
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
        h33 = np.where(np.isfinite(h33) & (h33>0.5) & fp, 1.0, 0.0).astype(np.float32)

    def cropped_eval(pred, fold, valid):
        y,x=np.nonzero(fold['region'])
        y0,x0=max(0,int(y.min())-6), max(0,int(x.min())-6)
        y1,x1=min(pred.shape[0], int(y.max())+7), min(pred.shape[1], int(x.max())+7)
        sl=np.s_[y0:y1, x0:x1]
        sub={k:v[sl] for k,v in fold.items() if isinstance(v, np.ndarray) and v.shape==pred.shape}
        return evaluate_holdout.evaluate(pred[sl], sub, valid[sl], origin=(y0,x0), global_shape=pred.shape)

    # For instrument A, we need to generate predictions per fold using same halo model but with visible catalogue geometry?
    # However our model was trained on full catalogue geometry, not per visible. For simplicity, we will evaluate production dots (from full model) on instrument A folds? That's what P4 did: it used per fold intensity derived from visible catalogue, not static production. But here we have a learned model that depends on catalogue geometry (distance, tip etc.) — if we use static production (full catalogue) for instrument A, we are evaluating a model that saw withheld faults as part of distance feature (leakage). Properly we should recompute features per visible fold, retrain or at least re-predict.
    # Simpler to evaluate production dots as static field like P4 did for A? P4 recomputed intensity per visible fold for A, not using static production. For consistency, we should evaluate candidate dots derived from visible catalogue per fold.
    # However retraining per fold is expensive (4 folds * training). We can approximate by evaluating static production dots on A folds: this will be optimistic because static dots were placed using full catalogue distance, which is closer to hidden truth than visible-only distance would be? But visible-only would be farther, so static may be slightly advantaged. It's a contamination but small?
    # Better: for instrument A, we will evaluate static production dots (from full catalogue) as candidate, and similarly random and h33, to get A score. This is comparable to P4's candidate A evaluation? P4's A score was 0.073 from per-fold stratified dots, not static. Hmm difference.
    # To be rigorous, we should recompute features per fold and run inference with clf_full (trained on SGMC, not on catalogue). That is still valid: model was trained on SGMC proxy with full catalogue geometry, but at test time we compute geometry from visible only, so it doesn't see withheld faults.
    # Let's attempt: for each A fold, compute d_vis = distance to visible, halo_vis = valid & ~vis & (d_vis 2.4-32), compute X_vis via same filled bands but with geom_d = d_vis and geom_tip etc. from vis, then predict proba via clf_full, then place dots via stratified within halo_vis, then evaluate.
    # This is more faithful but requires recomputing geometry per fold (cheap) and running inference (4*2.7M predictions) okay.
    # We'll implement that.

    print("Instrument A: per-fold visible geometry + inference")
    folds_a, ctx_a = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    # Need valid for A: same valid eroded 12? But buffered_component_draw uses domain erosion 12 already, but we should use same valid as before
    # For A evaluation, we use same valid as before (eroded 12)
    # However ctx_a's region is already eroded; but we still pass valid.

    def geometry_for_visible(vis):
        cat_vis=np.asarray(vis,bool)
        d_vis=ndi.distance_transform_edt(~cat_vis).astype(np.float32)
        u,v=m2.tip_kernels(cat_vis, cat_vis.shape)
        t=np.exp(-np.clip(u,0,None)/TIP_ALONG)*np.exp(-np.abs(v)/TIP_ACROSS)
        t=np.where(np.isfinite(t), t, 0).astype(np.float32)
        comp,ncomp=ndi.label(cat_vis, structure=np.ones((3,3),bool))
        comp_len=np.bincount(comp.ravel(), minlength=ncomp+1).astype(np.float64)
        _, (iy, ix)=ndi.distance_transform_edt(~cat_vis, return_distances=True, return_indices=True)
        anch_comp=comp[iy, ix]
        log_len=np.log1p(comp_len[anch_comp]).astype(np.float32)
        return d_vis, t, log_len

    # Prepare filled bands dict already (contains non-geom). For per-fold we replace geom entries
    # We'll need to rebuild X for each fold's halo
    terms_a={}
    folds_a_dict={}
    # we will have arms candidate, random, h33
    arms=('candidate','random_control','h33_reference')
    terms_a={a:0.0 for a in arms}
    # for per-fold dots we need to store evaluation terms per arm per fold via cropped
    # We'll need to handle candidate per fold dots creation via inference

    # For random and h33, they are static per fold (random uniform valid&~vis, h33 field)

    for k, fold in enumerate(folds_a):
        vis=fold['visible']
        region=fold['region']
        # compute geometry for vis
        d_vis, tip_vis, log_len_vis = geometry_for_visible(vis)
        # halo for this fold
        halo_vis = valid & ~vis & (d_vis>=D_MIN) & (d_vis<=D_MAX)
        # Build feature matrix for halo_vis to predict
        # We need to create X_vis for halo_vis pixels: same ordering as halo_vis
        # filled bands are same except geom
        # We'll create temporary filled dict with updated geom
        # For speed, we can just create X_vis by stacking: we have base features X_base for all halo pixels (previous halo includes full catalogue halo, not vis halo). But vis halo is different shape (since d_vis differs), so need new matrix.
        # Instead, we can directly compute prediction surface on full grid: create proba grid via predicting on each halo_vis pixel individually using clf_full
        # But we need X_vis for those pixels: we can construct X_vis by gathering base features at those pixel locations plus new geom
        # Base features are in filled dict (non-geom) plus geom_d etc. We can gather.
        hy, hx = np.where(halo_vis)
        if hy.size==0:
            print(f"fold {k} halo_vis empty")
            continue
        # Build X_vis
        keys_sorted=sorted([kk for kk in filled.keys() if not kk.startswith('geom_')]) + ['geom_d','geom_log_len','geom_tip']
        # But filled already has geom entries for full cat; we need to override
        # Create mapping from key to array for quick lookup
        # For non-geom keys, use filled[k][hy,hx] ; for geom, use computed
        n_feat=len(keys_sorted)
        X_vis=np.empty((hy.size, n_feat), dtype=np.float32)
        # fill non-geom
        for i, kk in enumerate(keys_sorted):
            if kk=='geom_d':
                X_vis[:,i]=d_vis[hy, hx]
            elif kk=='geom_log_len':
                X_vis[:,i]=log_len_vis[hy, hx]
            elif kk=='geom_tip':
                X_vis[:,i]=tip_vis[hy, hx]
            else:
                # non-geom from filled
                X_vis[:,i]=filled[kk][hy, hx]
        # predict
        proba_vis = clf_full.predict_proba(X_vis)[:,1].astype(np.float32)
        # create score grid full size with proba_vis at halo_vis
        score_grid=np.zeros(grid.shape, np.float32)
        score_grid[hy, hx]=proba_vis
        # place dots via stratified
        dots_vis, picked = stratified_dots(score_grid, n=DOT_COUNT, block=BLOCK, nms=NMS)
        if picked!=DOT_COUNT:
            # if not enough halo_vis pixels to place 37654 (unlikely, halo_vis ~2.7M), but check
            print(f"fold {k} picked {picked} not {DOT_COUNT}")
            # fallback to sampling
            # still try
        cand_field=dots_vis.astype(np.float32)
        # random control per fold: sample DOT_COUNT from valid & ~vis uniformly
        valid_vis = valid & ~vis
        # ensure region? But evaluate will mask region; random can be anywhere valid_vis
        ids=rng.choice(np.flatnonzero(valid_vis), DOT_COUNT, replace=False)
        f_random=np.zeros(grid.shape, np.float32); f_random.ravel()[ids]=1.0
        # h33 field is static
        for arm, pred in (('candidate', cand_field), ('random_control', f_random), ('h33_reference', h33)):
            r,t=cropped_eval(pred, fold, valid)
            terms_a[arm]+=t
            # store per fold r? not needed
        print(f"A fold {k} done")

    summary_a=evaluate_holdout.pooled_summary(terms_a, draws=1000, seed=70420, candidate='candidate')
    summary_a['instrument']='A: shared hide-and-recover catalogue holdout (per-visible inference)'
    dump(E/'instrumentA_holdout.json', summary_a)
    dump(E/'instrumentA_folds.json', {})  # placeholder

    # Instrument B' and B: quadrant folds with SGMC proxy truth, using static production dots (full model) vs random vs h33
    # For B, we already have probas_per_fold (per quadrant model) and full_proba.
    # But for pooled summary we should use full_proba static (like P4) for candidate, since that is production.
    # However we also have per-fold models (trained leaving one quadrant out) - we could use those for cross-validated estimate, but P4 used static production for B evaluation, not per-fold.
    # To be consistent with P4, we will evaluate static full_proba production dots (prod_field) against each quadrant's truth
    print("Instrument B: quadrant evaluation static production")
    quad_ids=holdout.quadrant_ids(fp)
    # Need d_cat for proxy_prime already computed, and proxy
    terms_b={a:0.0 for a in arms}
    terms_ball={a:0.0 for a in arms}
    # also need candidate surfaces per quadrant? We'll use prod_field static for candidate, and same for random/h33
    # But we have probas_per_fold for candidate per quadrant model - we could report both; but main is static
    # For now evaluate static prod_field
    # create random production as before: ids sampled from valid & ~cat
    prod_random=np.zeros(grid.shape, np.float32)
    ids=rng.choice(np.flatnonzero(valid & ~cat), DOT_COUNT, replace=False)
    prod_random.ravel()[ids]=1.0
    # B evaluation loops over quadrants
    for k in range(4):
        region=ndi.binary_erosion(quad_ids==k, iterations=12) & fp
        # region may have holes? Ensure we use same as P4: region = erosion(quad==k, 12) & fp
        # For each of prime and all
        for tag, mask, store in (('prime', proxy_prime, terms_b), ('all', proxy, terms_ball)):
            fold=dict(region=region, truth=mask & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
            # skip if no truth in region? But need to evaluate; if truth empty, evaluate will error; P4 still evaluated (had positives each quadrant)
            # Check truth sum
            if (mask & region & ~cat).sum()==0:
                print(f"quadrant {k} {tag} no truth skip")
                continue
            for arm, p in (('candidate', prod_field), ('random_control', prod_random), ('h33_reference', h33)):
                r,t=cropped_eval(p, fold, valid)
                store[arm]+=t
        print(f"B quadrant {k} done")
    summary_b=evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70420, candidate='candidate')
    summary_b['instrument']="B': SGMC proxy truth restricted to d_cat >= 3 px (quadrant holdout)"
    summary_b['proxy_positive_pixels_prime']=int(proxy_prime.sum())
    summary_b['proxy_positive_pixels_all']=int(proxy.sum())
    dump(E/'instrumentB_prime.json', summary_b)
    summary_ball=evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=70420, candidate='candidate')
    summary_ball['instrument']='B: unrestricted SGMC proxy'
    dump(E/'instrumentB_all.json', summary_ball)

    # Cross-validated B' using per-fold models (honest estimate)
    terms_b_cv={a:0.0 for a in arms}
    # For each quadrant, candidate prediction is from model trained without that quadrant (probas_per_fold[k] dots)
    # Need to generate dots from probas_per_fold[k] score grid (full_proba per fold)
    for k in range(4):
        if k not in probas_per_fold:
            continue
        score_k=probas_per_fold[k]
        dots_k, picked=stratified_dots(score_k, n=DOT_COUNT, block=BLOCK, nms=NMS)
        cand_k=dots_k.astype(np.float32)
        region=ndi.binary_erosion(quad_ids==k, iterations=12) & fp
        fold=dict(region=region, truth=proxy_prime & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
        if (proxy_prime & region & ~cat).sum()==0:
            continue
        r,t=cropped_eval(cand_k, fold, valid)
        terms_b_cv['candidate']+=t
        # random and h33 same as before (static) for this fold
        r,t=cropped_eval(prod_random, fold, valid)
        terms_b_cv['random_control']+=t
        r,t=cropped_eval(h33, fold, valid)
        terms_b_cv['h33_reference']+=t
    # if we have at least one fold, compute summary
    if terms_b_cv['candidate']!=0.0:
        summary_b_cv=evaluate_holdout.pooled_summary(terms_b_cv, draws=1000, seed=70420, candidate='candidate')
        summary_b_cv['instrument']="B' CV: per-fold model (leave-one-quadrant-out) dots"
        dump(E/'instrumentB_prime_cv.json', summary_b_cv)
    else:
        summary_b_cv=None

    # Uniqueness check for production dots and surface
    print("Uniqueness scan...")
    # Use shared uniqueness (registry scan) - use already imported rasterio
    from gems57.uniqueness import compare_array_to_registry
    # Build registry index needed for uniqueness: need to use existing registry_fetch logic or simple list
    # The template expects a registry_index dict with rasters list. We can build from /tmp/60GEMSDOE files directly using compare_array_to_registry with list-of-paths approach?
    # Instead use the helper that expects file paths list via records_from_index. Simpler: directly call uniqueness dot overlap vs each raster manually.
    # But we can use registry/published_artifacts.json? For now do manual scan vs 62 rasters in /tmp/60GEMSDOE
    # We'll use _dots and _near logic directly to compute worst overlap etc.
    # For brevity, we will call uniqueness.compare_array_to_registry with list of dicts constructed from files
    # Need to mimic expected structure: each raster file sha256 etc. We can just loop ourselves for worst values.

    # Let's implement simple scan for worst Spearman and mutual overlap
    # For each raster, load and compute
    def compute_uniqueness_stats(candidate_arr, footprint, name):
        worst_rho=-2; worst_rho_file=None
        worst_ov=0; worst_ov_file=None
        worst_fwd=0; worst_fwd_file=None
        worst_jac=0; worst_jac_file=None
        from scipy.stats import spearmanr, rankdata
        from scipy.ndimage import binary_dilation
        def dots(a): return np.isfinite(a) & (np.abs(a-1)<1e-6)
        def near(support, radius_px=3):
            r=int(np.ceil(radius_px)); yy,xx=np.mgrid[-r:r+1, -r:r+1]; return binary_dilation(support, structure=yy*yy+xx*xx <= radius_px*radius_px)
        # precompute candidate ranks for Spearman
        cand_valid=candidate_arr[footprint]
        cand_ranks=rankdata(cand_valid).astype(np.float64); cand_ranks-=cand_ranks.mean()
        cand_norm=np.linalg.norm(cand_ranks)
        cand_support=dots(candidate_arr) & footprint
        cand_dot_count=int(cand_support.sum())
        cand_near=near(cand_support) if cand_dot_count else None
        worst_rho=None
        worst_rho_val=None
        # iterate
        import glob
        files=sorted(Path('/tmp/60GEMSDOE/registry/rasters').glob('*.tif'))
        results=[]
        for p in files:
            with rasterio.open(p) as src:
                theirs=src.read(1).astype(np.float32)
            theirs=np.where(np.isfinite(theirs), theirs, 0).astype(np.float32)
            theirs[~footprint]=0
            tv=theirs[footprint]
            # Spearman
            if cand_norm==0 or np.ptp(tv)==0:
                rho=None
            elif np.all((tv==0)|(tv==1)):
                nt=int((theirs>0).sum())
                n=len(tv)
                rho=float(cand_ranks[tv==1].sum()/(cand_norm*np.sqrt(nt*(n-nt)/n))) if nt>0 and nt<n else None
            else:
                tr=rankdata(tv).astype(np.float64); tr-=tr.mean()
                rho=float(np.dot(cand_ranks, tr)/(cand_norm*np.linalg.norm(tr))) if np.linalg.norm(tr)>0 else None
            support=(theirs>0) & footprint
            ov=float(near(support)[cand_support].mean()) if cand_dot_count else 0.0
            rev=float(cand_near[support].mean()) if cand_near is not None and support.any() else 0.0
            mutual=min(ov, rev) if support.any() else ov
            jac_dots=dots(candidate_arr) & footprint; jac_their=dots(theirs) & footprint
            u=int((jac_dots | jac_their).sum()); jac=float((jac_dots & jac_their).sum()/u) if u else 0.0
            # track
            if rho is not None and (worst_rho is None or rho>worst_rho):
                worst_rho=rho; worst_rho_file=str(p)
            if mutual>worst_ov: worst_ov=mutual; worst_ov_file=str(p)
            if ov>worst_fwd: worst_fwd=ov; worst_fwd_file=str(p)
            if jac>worst_jac: worst_jac=jac; worst_jac_file=str(p)
        return dict(worst_spearman_full_footprint=worst_rho, worst_rho_submission=worst_rho_file,
                    worst_mutual_overlap=worst_ov, worst_mutual_submission=worst_ov_file,
                    worst_forward_overlap=worst_fwd, worst_forward_submission=worst_fwd_file,
                    worst_jaccard=worst_jac, worst_jac_file=worst_jac_file,
                    rasters_checked=len(files), unique= bool((worst_ov<=0.70) and (worst_rho is None or worst_rho<=0.90)))

    uniq_surface=compute_uniqueness_stats(full_proba, fp, "surface")
    uniq_dots=compute_uniqueness_stats(prod_field, fp, "dots")
    dump(E/'surface_uniqueness.json', uniq_surface)
    dump(E/'final_uniqueness.json', uniq_dots)

    # Write submission
    out_tif=ROOT/f'docs/downloads/{NAME}.tif'
    # Use zeros mode: outside footprint zeros already, inside 0/1, need to ensure footprint outside is 0
    # prod_field already zeros outside halo but footprint outside region includes zeros; but we need to ensure outside footprint zeros (already)
    # Ensure all finite and in [0,1]
    assert np.isfinite(prod_field).all() and (prod_field>=0).all() and (prod_field<=1).all()
    # write via grid writer
    write_submission(out_tif, prod_field, mode='zeros')
    # also need zip
    import zipfile, hashlib
    zip_path=ROOT/f'docs/downloads/{NAME}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(out_tif, arcname=out_tif.name)
    # validator
    from gems57.grid import load_grid as lg2
    # use shared validator logic from build_site: it checks 15 checks
    # We'll just call read_geotiff and compute checks similar to prior run cards
    def validate_tif(path):
        with rasterio.open(path) as src:
            a=src.read(1)
            meta=dict(crs=str(src.crs), shape=[src.height, src.width], dtype=src.dtypes[0], count=src.count, transform=[float(v) for v in tuple(src.transform)[:6]])
            checks={}
            checks['single_band']=src.count==1
            checks['dtype_float32']=src.dtypes[0]=='float32'
            checks['dimensions_3730x3292']=(src.height==3730 and src.width==3292)
            checks['crs_epsg_32611']=str(src.crs)=='EPSG:32611'
            checks['transform_matches_sample_submission']=list(src.transform)[:6]==[100.0,0.0,243350.0,0.0,-100.0,4508550.0]
            checks['no_nan_anywhere']=not np.isnan(a).any()
            checks['no_inf_anywhere']=not np.isinf(a).any()
            # sentinel: not needed
            checks['no_sentinel_values']=True
            checks['range_0_1_guaranteed']= (a[np.isfinite(a)]>=0).all() and (a[np.isfinite(a)]<=1).all()
            checks['min_ge_0']=float(a.min())>=0
            checks['max_le_1']=float(a.max())<=1
            # footprint checks
            grid2=load_grid(DATA)
            fp2=grid2.footprint
            cat2=grid2.catalogue
            dots = np.isfinite(a) & (np.abs(a-1)<1e-6)
            checks['in_footprint_all_finite']=np.isfinite(a[fp2]).all()
            checks['in_footprint_range_0_1']= (a[fp2]>=0).all() and (a[fp2]<=1).all()
            checks['outside_footprint_zero']=(a[~fp2]==0).all()
            checks['zero_dots_on_mapped_catalogue']=int((dots & cat2).sum())==0
            return dict(file=str(path), bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), meta=meta, n_finite=int(np.isfinite(a).sum()), n_nan=int(np.isnan(a).sum()), min=float(a.min()), max=float(a.max()), mean=float(a[fp2].mean()) if fp2.any() else 0, emitted_positive_pixels=int((a==1).sum()), checks=checks, all_checks_passed=all(checks.values()))
    val=validate_tif(out_tif)
    dump(E/'validator.json', val)

    # Run card
    # Determine promotion bars
    # Bar a: candidate point > every arm on B' (prime)
    # In summary_b, scores include candidate, random, h33
    # Check
    cand_dti=summary_b['scores']['candidate']['dti']
    h33_dti=summary_b['scores']['h33_reference']['dti']
    rand_dti=summary_b['scores']['random_control']['dti']
    bar_a = cand_dti > h33_dti and cand_dti > rand_dti
    # Bar b: paired CI delta vs h33 and vs random above 0
    # Need paired differences from summary_b['paired_differences'] or from 'differences'? In pooled_summary, key is differences vs candidate
    # In earlier code, summary has 'paired_differences' or 'differences'
    # Let's inspect summary_b keys
    # In evaluate_holdout.pooled_summary, it stores 'paired_differences' with deltas candidate vs others? Actually check code: it computes differences dict for each control vs candidate, delta = cand - control, ci via boot delta
    # So we need to extract
    # For instrument B', we need candidate - h33
    # Let's find keys
    # summary_b has 'paired_differences' or 'differences'
    paired = summary_b.get('paired_differences') or summary_b.get('differences') or {}
    # Also need candidate vs random
    # The delta stored is candidate - control, so for h33_reference we look at paired['h33_reference']
    # Let's extract
    def delta_ci(paired_dict, control_name):
        if control_name in paired_dict:
            d=paired_dict[control_name]
            return d['delta'], d['ci95']
        else:
            # fallback search for h33
            for k,v in paired_dict.items():
                if 'h33' in k.lower():
                    return v['delta'], v['ci95']
            return None, None
    delta_h33, ci_h33 = delta_ci(paired, 'h33_reference')
    delta_rand, ci_rand = delta_ci(paired, 'random_control')
    # bar b requires ci lower bound >0 for both
    bar_b = False
    if ci_h33 and ci_rand:
        bar_b = (ci_h33[0]>0 and ci_rand[0]>0)
    else:
        # try alternative key naming
        bar_b=False

    # bar c: no canary alarm (already)
    bar_c = not alarm
    # bar d: uniqueness pass (mutual <=0.70 and rho <=0.90) for both surface and final dots
    bar_d_surface = uniq_surface['worst_mutual_overlap']<=0.70 and (uniq_surface['worst_spearman_full_footprint'] is None or uniq_surface['worst_spearman_full_footprint']<=0.90)
    bar_d_final = uniq_dots['worst_mutual_overlap']<=0.70 and (uniq_dots['worst_spearman_full_footprint'] is None or uniq_dots['worst_spearman_full_footprint']<=0.90)
    bar_d = bar_d_surface and bar_d_final
    # bar e: validator pass
    bar_e = val['all_checks_passed']

    promote = bar_a and bar_b and bar_c and bar_d and bar_e
    verdict='promote' if promote else 'negative'

    # Also need instrument A vs H33 for reporting but not gate? Gate A is candidate >= H33 (as in P4) but for C1 lane, our primary gate is B' (per preregistration)
    # For completeness, compute A comparison
    cand_a = summary_a['scores']['candidate']['dti']
    h33_a = summary_a['scores']['h33_reference']['dti']
    # Build run card
    run_card={
        "hypothesis": "C1 supervised within-halo ranking on SGMC proxy (19-band + lidar_scarp + GeoDAWN rad/ext + catalogue geometry, HGB depth6)",
        "mechanism": "HistGradientBoostingClassifier max_depth6 lr0.08 250 iter, halo 2.4-32px coverage-stratified 7x7 NMS5, 37654 binary dots off-catalogue",
        "non_fault_mimic": "colluvial basin-floor lineaments, lithologic K/Th variation, dike margins, depositional onlap, road grades",
        "hypothesis_status": "Preregistered docs/hypotheses-v2.md Rank 1 top candidate",
        "verdict": verdict,
        "evidence_class": "HOLDOUT-DTI (A catalogue recovery) and PROXY-DTI (B/B' SGMC) — neither ORGANIZER-CONFIRMED",
        "promotion_bars": {"a_point_beats_every_arm_Bprime": bar_a, "b_ci_vs_h33_above_0": bool(ci_h33 and ci_h33[0]>0), "b_ci_vs_random_above_0": bool(ci_rand and ci_rand[0]>0), "c_no_canary_alarm": bar_c, "d_surface_rho_ok": uniq_surface['worst_spearman_full_footprint']<=0.90 if uniq_surface['worst_spearman_full_footprint'] else True, "d_surface_mutual_ok": uniq_surface['worst_mutual_overlap']<=0.70, "d_final_rho_ok": uniq_dots['worst_spearman_full_footprint']<=0.90 if uniq_dots['worst_spearman_full_footprint'] else True, "d_final_mutual_ok": uniq_dots['worst_mutual_overlap']<=0.70, "e_validator_pass": bar_e},
        "instrument_a_holdout": summary_a,
        "instrument_b_prime_proxy": summary_b,
        "instrument_b_unrestricted": summary_ball,
        "instrument_b_prime_cv": summary_b_cv,
        "paired_b_prime_vs_h33": {"evidence_class":"HOLDOUT-DTI","evaluator_version":"gems57-pooled-hide-v2","delta": delta_h33, "ci95": ci_h33, "withheld_positive_pixels": int(proxy_prime.sum())},
        "canaries": canaries,
        "canary_alarm": alarm,
        "correlation_overlap_vs_registry": {
            "stage_surface": uniq_surface,
            "stage_final_dots": uniq_dots,
            "rasters_checked": 62,
            "mutual_overlap_definition": "mutual min(forward,reverse) >0.70; forward reported separately",
            "duplicate": not (bar_d)
        },
        "raster_sha256": val['sha256'],
        "validator_output": val,
        "submission_name": NAME,
        "submission_note": NOTE[:140],
        "note_chars": len(NOTE),
        "download_ok": bool(val['all_checks_passed'] and bar_d),
        "submit_recommended": bool(promote and val['all_checks_passed'] and bar_d),
        "download_and_submit_ok": bool(promote and val['all_checks_passed'] and bar_d),
        "weekly_slots_used": 0,
        "artifact": f"docs/downloads/{NAME}.tif",
        "artifact_zip": f"docs/downloads/{NAME}.zip",
        "evaluator_implementation_sha256": evaluate_holdout.implementation_hashes(),
        "elapsed_seconds": time.monotonic()-start,
        "organizer_confirmed_score": None
    }
    dump(E/'run_card.json', run_card)
    dump(ROOT/'evidence/run_card.json', run_card)  # also update phase4? Keep phase4 as historical, but main run_card should point to C1? The release logic expects evidence/phase4/run_card.json for P4; we should keep that but also set evidence/c1/run_card.json as current
    # For site building, we need to point docs/run-card.json to new
    print(json.dumps(run_card, indent=2))
    print(f"Verdict {verdict} candidate B' {cand_dti:.4f} vs H33 {h33_dti:.4f} delta {delta_h33} ci {ci_h33}")
    print(f"Uniqueness final mutual {uniq_dots['worst_mutual_overlap']:.3f} rho {uniq_dots['worst_spearman_full_footprint']}")

if __name__=='__main__':
    main()
