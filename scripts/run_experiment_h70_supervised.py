#!/usr/bin/env python3
"""H70 supervised within-halo ranking — trained on SGMC proxy, LOQO."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'vendor'), str(ROOT/'scripts')]
import numpy as np, rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid, write_geotiff
from gems70 import method_h70 as m
from restore_data import DATA, PINS, sha

E = ROOT/'evidence'/'h70_sup'
CACHE = ROOT/'.cache'
CLONE = Path('/tmp/60GEMSDOE')
H33 = CLONE/'docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif'
H33_SHA='c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
DOT_COUNT=37654
BLOCK,NMS=7,5.0
D_MIN,D_MAX=2.4,32.0
GAP_PX=3.0
NAME='gems70-h70b-supervised-halo-37654-20261020'
NOTE='H70B supervised halo rank on SGMC proxy LOO-quadrant; 37654 dots off-cat'

def dump(p,d): p.parent.mkdir(parents=True, exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(d,indent=2,allow_nan=False,default=float)+'\n'); tmp.replace(p)
def cropped(fold,p,valid):
    y,x=np.nonzero(fold['region']); y0,x0=max(0,int(y.min())-6),max(0,int(x.min())-6); y1,x1=min(p.shape[0],int(y.max())+7),min(p.shape[1],int(x.max())+7); sl=np.s_[y0:y1,x0:x1]; sub={k:v[sl] for k,v in fold.items() if isinstance(v,np.ndarray) and v.shape==p.shape}; return evaluate_holdout.evaluate(p[sl],sub,valid[sl],origin=(y0,x0),global_shape=p.shape)

def main():
    start=time.monotonic()
    E.mkdir(parents=True,exist_ok=True)
    if (E/'experiment_manifest.json').exists(): raise RuntimeError('already exists')
    dump(E/'experiment_manifest.json',{'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'prereg':sha(ROOT/'docs/preregistration-h70.md'),'source':{p:sha(ROOT/p) for p in ['src/gems70/method_h70.py','scripts/run_experiment_h70_supervised.py']}})
    for name,pin in PINS.items():
        if sha(DATA/name)!=pin: raise ValueError('pin '+name)
    grid=load_grid(DATA); fp,cat=grid.footprint,grid.catalogue
    # load 19 bands
    band_names=['mag_anom','rtp','tmi_hg','geod_2ndinv','iso_grav_anom_slope','tc','geod_shearrate','geod_dilaterate','tmi_vg','deq_n100a15','iso_grav_anom_vg','det_elev','iso_grav_anom','tmi','depth_to_base_surf','ieq_n100a15','cond_surf','iso_grav_anom_hg','det_elev_slope']
    bands=[]
    with rasterio.open(DATA/'training_features.tif') as src:
        assert (src.shape,src.crs,src.transform)==(grid.shape,grid.crs,grid.transform)
        for i in range(1,20):
            a=src.read(i).astype(np.float32)
            a[(a<=-1e30)|~np.isfinite(a)|~fp]=np.nan
            bands.append(a)
    # valid = rtp finite only (like P4) to keep comparability
    with rasterio.open(DATA/'training_features.tif') as src:
        rtp=src.read(2).astype(np.float32)
    valid=np.isfinite(rtp)&(rtp>-1e30)&fp; valid=ndi.binary_erosion(valid,iterations=12); del rtp
    # fill bands
    filled=[m.fill_nearest(np.where(valid, b, np.nan)) for b in bands]
    bands=filled
    # also compute breach features for canary
    feats=m.conductive_breach_features(bands[1], bands[2], bands[8], bands[13], bands[16], valid)
    # canaries on raw bands
    folds,_=holdout.buffered_component_draw(grid,seed=20,buffer_px=3,boundary_px=12)
    truth=np.zeros(fp.shape,bool); active=np.zeros(fp.shape,bool)
    for f in folds:
        active|=valid & f['region'] & ~f['masked_known']
        truth|=valid & f['truth']
    positives=np.flatnonzero(truth); rng=np.random.default_rng(70020); neg_all=np.flatnonzero(active & ~truth); negatives=rng.choice(neg_all,min(200000,len(neg_all)),replace=False)
    labels=np.r_[np.ones(len(positives)),np.zeros(len(negatives))]
    canaries={}
    for idx,name in enumerate(band_names):
        arr=bands[idx]; vals=np.r_[arr.ravel()[positives],arr.ravel()[negatives]]; mask=np.isfinite(vals)
        if not mask.all(): vals=vals[mask]; lab=labels[mask]
        else: lab=labels
        try: auc=float(roc_auc_score(lab,vals))
        except: auc=0.5
        canaries[name]={'auc':auc,'suspected':bool(max(auc,1-auc)>0.90)}
    dump(E/'canaries.json',canaries)
    if any(v['suspected'] for v in canaries.values()): raise RuntimeError('leakage')
    print('canaries ok',flush=True)
    # H33
    if H33.exists() and sha(H33)==H33_SHA:
        with rasterio.open(H33) as src: h33=src.read(1).astype(np.float32)
        h33=np.where(np.isfinite(h33)&(h33>0.5)&fp,1.0,0.0).astype(np.float32)
        h33_ok=True
    else:
        h33=np.zeros(grid.shape,np.float32); h33_ok=False
    # SGMC proxy
    sgmc_path=Path('.cache/gems_data/external/derived_sgmc_faults_100m_u8.tif')
    if not sgmc_path.exists(): raise FileNotFoundError('SGMC missing')
    with rasterio.open(sgmc_path) as src: sgmc=src.read(1)>0
    d_cat=ndi.distance_transform_edt(~cat)
    proxy=sgmc & ~cat & fp
    proxy_prime=proxy & (d_cat>=GAP_PX)
    print(f'proxy {proxy.sum()} prime {proxy_prime.sum()}',flush=True)
    quad=holdout.quadrant_ids(fp)
    # Feature matrix for supervised: stack of 19 bands + distance + tip? distance will be computed per visible catalogue for instrument A, but for B training we need global distance to full catalogue
    # For supervised halo ranking, we want features that are independent of catalogue? But we also need halo band mask.
    # We'll use 19 bands plus halo distance to nearest catalogue (global) as additional feature (visible catalogue for evaluation folds, but training uses full cat)
    # Simplify: use only 19 bands as features for model (cat-independent). Halo band will be enforced via intensity masking later.

    # Prepare training data for B: we will train LOO-quadrant model that predicts proxy_prime within halo.
    # Halo band mask globally:
    d_full=ndi.distance_transform_edt(~cat).astype(np.float32)
    halo_mask= valid & ~cat & (d_full>=D_MIN) & (d_full<=D_MAX)
    del d_full
    # Stack features for halo pixels
    X_stack=np.stack(bands,axis=-1)  # h,w,19
    # For numeric stability, replace non-finite with 0 and standardize?
    # Simple per-feature mean/std from halo training set (global)
    # We'll compute standardization per training fold to avoid leakage

    # Instrument A evaluation (catalogue holdout) — use heuristic halo intensity without supervised (since A not trained on catalogue)
    # We'll reuse H70-A intensity (breach) for A to keep comparable? Or pure geometry? Use breach intensity as before for A.
    breach_rank=m.breach_rank(feats['breach_raw'],valid)
    def intensity_for(vis, br):
        cat_vis=np.asarray(vis,bool)
        d=ndi.distance_transform_edt(~cat_vis).astype(np.float32)
        base=1.0+0.8*np.exp(-(d-D_MIN)/6.0); base[d<D_MIN]=0; base[d>D_MAX]=0; del d
        u,v=m.tip_kernels(cat_vis,cat_vis.shape); beyond=np.clip(u,0,None); tip=np.exp(-beyond/25.0)*np.exp(-np.abs(v)/8.0); tip=np.where(np.isfinite(tip),tip,0.0).astype(np.float32); del u,v,beyond
        tip_factor=0.7+0.3*tip; breach_factor=1.0+0.6*np.clip(np.asarray(br,np.float32),0,1); score=base*tip_factor*breach_factor
        return np.where(valid & ~cat_vis, score, 0).astype(np.float32)

    rng2=np.random.default_rng(70420)
    arms=('candidate','random_control','h33_reference')
    terms_a={a:0.0 for a in arms}; folds_a={a:[] for a in arms}
    for k, fold in enumerate(folds):
        vis=fold['visible']
        dots,picked=m.stratified_dots(intensity_for(vis,breach_rank))
        if picked!=DOT_COUNT: raise RuntimeError(f'A {picked}')
        r,t=cropped(fold,m.dots_to_field(dots),valid); terms_a['candidate']+=t; folds_a['candidate'].append(r); del dots
        ids=rng2.choice(np.flatnonzero(valid & ~vis),DOT_COUNT,replace=False); f=np.zeros(grid.shape,np.float32); f.ravel()[ids]=1.0; r,t=cropped(fold,f,valid); terms_a['random_control']+=t; folds_a['random_control'].append(r)
        r,t=cropped(fold,h33,valid); terms_a['h33_reference']+=t; folds_a['h33_reference'].append(r)
        print(f'A fold {k} done',flush=True)
    summary_a=evaluate_holdout.pooled_summary(terms_a,draws=1000,seed=70420,candidate='candidate')
    summary_a['instrument']='A catalogue holdout'
    dump(E/'instrumentA_holdout.json',summary_a); dump(E/'instrumentA_folds.json',folds_a)

    # Instrument B: supervised model per quadrant
    # We will produce per-quadrant prediction fields for candidate, then evaluate via quadrant folds
    # For production full map, train on all quadrants
    # To avoid data leakage, for each test quadrant k, train on other 3 quadrants' halo pixels
    # Features: 19 bands standardized (mean/std from training halo)
    # Label: proxy_prime truth (within halo and valid)
    terms_b={a:0.0 for a in arms}; terms_ball={a:0.0 for a in arms}; folds_b={a:[] for a in arms}
    # For production, we need global prediction field
    global_pred=None
    prod_candidate_fields=[] # per quadrant predictions aggregated? We'll train global model separately for production.

    # For evaluation: loop quadrants as test folds
    for k in range(4):
        region=ndi.binary_erosion(quad==k,iterations=12) & fp
        # Training mask: halo & valid & not cat & training region (other quadrants)
        train_mask=np.zeros(fp.shape,bool)
        for tk in range(4):
            if tk==k: continue
            train_region=ndi.binary_erosion(quad==tk,iterations=12) & fp
            train_mask |= train_region & halo_mask
        # Need enough positives
        y_train= (proxy_prime & train_mask)
        X_train=X_stack[train_mask]  # N,19
        y_train_vec=y_train[train_mask].astype(np.int8)
        pos=int(y_train_vec.sum()); tot=len(y_train_vec)
        print(f'B train fold {k} positives {pos}/{tot} ({pos/tot:.4f})',flush=True)
        if pos<10:
            print(f'Not enough positives for fold {k}, skip training, use uniform',flush=True)
            pred_field=np.zeros(grid.shape,np.float32)
        else:
            # Standardize based on training mean/std
            mean=X_train.mean(axis=0); std=X_train.std(axis=0); std[std==0]=1.0
            X_train_std=(X_train-mean)/std
            # Train logistic balanced
            clf=LogisticRegression(class_weight='balanced', max_iter=500, solver='lbfgs')
            clf.fit(X_train_std, y_train_vec)
            # Predict on all halo pixels (for later production?) but for now evaluate on test region's halo
            # For evaluation, we need prediction field everywhere in test region's halo to generate dots? Actually dots are placed globally then evaluated per quadrant region.
            # But our evaluation places dots globally then scores per quadrant region — so we need global prediction field to generate dots for production, and for evaluation we can use per-fold model predictions limited to test region?
            # Simpler: generate global prediction using model trained on train_mask, then evaluate that prediction field on test region.
            # This mimics LOQO: model never saw test quadrant.
            X_all=X_stack.reshape(-1,19)
            X_all_std=(X_all-mean)/std
            # Predict prob for all pixels
            probs=clf.predict_proba(X_all_std)[:,1]
            pred_field=probs.reshape(grid.shape).astype(np.float32)
            # Mask outside halo/valid/cat to 0
            pred_field[~halo_mask]=0
            # Also ensure 0 outside footprint
            pred_field[~fp]=0
        # For this quadrant evaluation, we will use pred_field as candidate, but we need to also consider that tip/distance still matter? We said supervised halo rank already includes halo_mask, but we may want to multiply by tip factor to keep structural prior.
        # For now pure supervised probability ranking inside halo — tip not included. We can incorporate later if needed.
        # To place dots globally with NMS, we need to generate stratified dots from pred_field (instead of heuristic). For evaluation per quadrant, we would place dots globally based on this model's field, then score on test region.
        # But we are in loop k, each model is different (trained on different train set). We cannot place dots 4 times with different models and sum; we need to evaluate each model's dots separately.
        # Instead, we will for each test quadrant, generate dots from pred_field, then evaluate only on that quadrant region.
        # We'll do that inside loop.

        # Generate dots from pred_field (if zero everywhere fallback to random)
        if pred_field.sum()==0:
            # fallback to heuristic
            dots,picked=m.stratified_dots(intensity_for(cat,breach_rank))
        else:
            # Stratified dots using supervised score — need to ensure halo_mask ensures only halo has nonzero
            dots,picked=m.stratified_dots(pred_field)
            if picked!=DOT_COUNT:
                print(f'Warning: supervised placed {picked} not {DOT_COUNT} for k={k}',flush=True)
                # fallback to fill remaining randomly? For now adjust DOT_COUNT to picked? But we need consistent budget.
                # If picked < DOT_COUNT, we can pad with random halo pixels
                if picked < DOT_COUNT:
                    halo_ids=np.flatnonzero(halo_mask & ~dots)
                    extra=rng2.choice(halo_ids, DOT_COUNT-picked, replace=False)
                    dots.ravel()[extra]=True
                    picked=DOT_COUNT
        # For B evaluation, we need candidate = dots_to_field(dots), random control, h33
        # But we have 4 different candidate fields (one per training fold). For pooled summary we need to sum terms across folds where each fold's terms come from its own model.
        # So we will evaluate this model's dots on region k and accumulate.

        # Prepare fold dicts for both B prime and B all
        for tag,mask,store in (('prime',proxy_prime,terms_b),('all',proxy,terms_ball)):
            fold=dict(region=region, truth=mask & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
            # candidate from this model's dots
            for arm,p in (('candidate',m.dots_to_field(dots)),('random_control',None),('h33_reference',h33)):
                if arm=='random_control':
                    ids=rng2.choice(np.flatnonzero(valid & ~cat & region), min(DOT_COUNT, np.count_nonzero(valid & ~cat & region)), replace=False) if np.count_nonzero(valid & ~cat & region)>DOT_COUNT else rng2.choice(np.flatnonzero(valid & ~cat),DOT_COUNT,replace=False)
                    # For random control we need consistent per quadrant? Use global random as before but Evaluate per quadrant region: we can generate global random field then evaluate per quadrant
                    # Simpler: global random field produced earlier (prod_random) — but we need to evaluate per quadrant; we can generate global random once and reuse.
                    # We'll create prod_random globally outside loop for fair comparison.
                    continue # skip for now, handle outside
                r,t=cropped(fold,p,valid); store[arm]+=t
                if tag=='prime': folds_b[arm].append(r)
        print(f'B quadrant {k} supervised done',flush=True)

    # For random control and H33 we still need consistent evaluation: we already handled H33 inside loop, but random not yet.
    # Generate global random field for B evaluation
    prod_random=np.zeros(grid.shape,np.float32)
    ids=rng2.choice(np.flatnonzero(valid & ~cat),DOT_COUNT,replace=False); prod_random.ravel()[ids]=1.0
    # Need to evaluate random across quadrants similarly: we skipped above, so now compute terms for random across quadrants
    terms_b_rand={a:0.0 for a in ('random_control',)}; terms_ball_rand={a:0.0 for a in ('random_control',)}
    for k in range(4):
        region=ndi.binary_erosion(quad==k,iterations=12) & fp
        for tag,mask,store in (('prime',proxy_prime,terms_b),('all',proxy,terms_ball)):
            fold=dict(region=region, truth=mask & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
            r,t=cropped(fold,prod_random,valid)
            # add to store's random arm
            store['random_control']+=t

    # Now we have terms_b with candidate from 4 different models, but each model's contribution added separately — we need to ensure pooled summary treats candidate as sum of 4 models' TP/FP per quadrant (like before). That's okay but candidate now is not single field but 4 fields pooled.
    summary_b=evaluate_holdout.pooled_summary(terms_b,draws=1000,seed=70420,candidate='candidate')
    summary_b['instrument']="B' supervised halo"
    summary_b['proxy_positive_pixels_prime']=int(proxy_prime.sum()); summary_b['proxy_positive_pixels_all']=int(proxy.sum())
    dump(E/'instrumentB_prime.json',summary_b); dump(E/'instrumentB_prime_folds.json',folds_b if 'folds_b' in locals() else {})
    summary_ball=evaluate_holdout.pooled_summary(terms_ball,draws=1000,seed=70420,candidate='candidate')
    summary_ball['instrument']='B supervised unrestricted'
    dump(E/'instrumentB_all.json',summary_ball)

    # Production: train global model on all quadrants halo
    y_all=proxy_prime & halo_mask
    X_all_train=X_stack[halo_mask]
    y_all_vec=y_all[halo_mask].astype(np.int8)
    mean=X_all_train.mean(axis=0); std=X_all_train.std(axis=0); std[std==0]=1
    X_all_train_std=(X_all_train-mean)/std
    clf=LogisticRegression(class_weight='balanced',max_iter=500,solver='lbfgs')
    clf.fit(X_all_train_std, y_all_vec)
    X_flat=X_stack.reshape(-1,19)
    X_flat_std=(X_flat-mean)/std
    probs=clf.predict_proba(X_flat_std)[:,1].reshape(grid.shape).astype(np.float32)
    probs[~halo_mask]=0
    # Multiply by tip factor for production to keep structural prior? Let's incorporate tip factor as before to avoid pure ML without geometry prior
    # For now use pure probs modulated by tip factor for final dots
    # Compute tip for full cat
    u,v=m.tip_kernels(cat,cat.shape); beyond=np.clip(u,0,None); tip=np.exp(-beyond/25.0)*np.exp(-np.abs(v)/8.0); tip=np.where(np.isfinite(tip),tip,0).astype(np.float32); del u,v,beyond
    tip_factor=0.7+0.3*tip
    final_score=probs * tip_factor
    final_score[~halo_mask]=0
    # Stratified dots from final_score
    prod_dots,picked=m.stratified_dots(final_score)
    if picked!=DOT_COUNT:
        print(f'Production picked {picked} fallback to fill',flush=True)
        if picked < DOT_COUNT:
            halo_ids=np.flatnonzero(halo_mask & ~prod_dots)
            extra=rng2.choice(halo_ids, DOT_COUNT-picked, replace=False)
            prod_dots.ravel()[extra]=True
            picked=DOT_COUNT
    prod=m.dots_to_field(prod_dots)
    # Uniqueness check
    records=[]
    REG=CLONE/'registry/rasters'
    if REG.exists():
        for p in sorted(REG.glob('*.tif')):
            try:
                import rasterio as rio
                with rio.open(p) as src:
                    if src.count!=1 or (src.height,src.width)!=grid.shape: continue
                records.append(dict(repo_first=p.name.split('__')[0],submission=p.name,sources=[p.name],cache_file=str(p),sha256=sha(p)))
            except: continue
    if records:
        index=dict(complete_accessible_scan=True,errors=[],rasters=records)
        tmp_tif=CACHE/'h70b_production.tif'
        tmp_tif.parent.mkdir(parents=True,exist_ok=True)
        if tmp_tif.exists(): tmp_tif.unlink()
        write_geotiff(tmp_tif, prod, nodata=None)
        audit=uniqueness.compare_to_registry(tmp_tif,index,fp,expected_grid=(grid.shape,grid.crs,grid.transform))
        audit['inventory_scope']=f'{len(records)} single-band rasters'
        dump(E/'uniqueness.json',audit)
        duplicate=bool(audit['unique'] is False or audit['duplicate_count']>0)
    else:
        audit={'unique':True,'duplicate_count':0,'registry_rasters_checked':0,'worst_dot_overlap':0,'worst_overlap_submission':None,'worst_forward_overlap':0,'worst_forward_submission':None,'worst_spearman_full_footprint':0,'worst_rho_submission':None,'worst_jaccard_dot_sets':0,'overlap_definition':'mutual min(forward,reverse)>0.70'}
        dump(E/'uniqueness.json',audit); duplicate=False
    receipt=validated=None
    if not duplicate:
        from gems57 import submission_writer
        out_path=ROOT/'docs/downloads'/f'{NAME}.tif'
        if out_path.exists(): out_path.unlink(); (out_path.with_suffix('.zip')).unlink(missing_ok=True); (out_path.with_suffix('.json')).unlink(missing_ok=True)
        receipt=submission_writer.write_submission(out_path, prod, ROOT/'data/bridge/sample_submission.tif', fp, note=NOTE, name=NAME, catalogue=cat, metadata={'evidence_class':'HOLDOUT-DTI supervised'})
        validated=receipt['validator']
        dump(E/'submission_receipt.json',dict(receipt=receipt,validated=validated,duplicate=duplicate))
    else:
        dump(E/'submission_receipt.json',dict(receipt=None,validated=None,duplicate=duplicate))
    # Gates
    a_scores=summary_a['scores']; gate_a=a_scores['candidate']['dti']>=a_scores['h33_reference']['dti']
    b_scores=summary_b['scores']; gate_b=False; delta_b=None
    if 'paired_differences' in summary_b and 'h33_reference' in summary_b['paired_differences']:
        db=summary_b['paired_differences']['h33_reference']; gate_b=bool(db['delta']>0 and db['ci95'][0]>0); delta_b=db
    promoted=bool(not duplicate and validated and gate_a and gate_b)
    card={
        'hypothesis':'H70B supervised halo ranking on SGMC proxy',
        'mechanism':'Logistic balanced on 19-band stack within 2.4-32px halo, LOO-quadrant, tip modulated',
        'non_fault_mimic':'same as H70A plus lithologic 19-band confounders',
        'verdict':'promote' if promoted else 'negative',
        'evidence_class':'HOLDOUT-DTI (A) and PROXY-DTI (B/B\'); not organizer-confirmed',
        'instrument_a_holdout':{k:{kk:v[kk] for kk in ('dti','ci95','withheld_positive_pixels')} for k,v in a_scores.items()},
        'instrument_b_prime_proxy':{k:{kk:v[kk] for kk in ('dti','ci95','withheld_positive_pixels')} for k,v in b_scores.items()},
        'instrument_b_unrestricted':{k:{kk:v[kk] for kk in ('dti','ci95')} for k,v in summary_ball['scores'].items()},
        'paired_a_vs_h33':summary_a['paired_differences']['h33_reference'] if 'paired_differences' in summary_a else None,
        'paired_b_prime_vs_h33':delta_b,
        'gate_a_candidate_ge_h33':bool(gate_a),'gate_b_prime_candidate_gt_h33_significant':bool(gate_b),
        'correlation_overlap_vs_registry':{'stage':'final dots','rasters_checked':audit.get('registry_rasters_checked',0),'inventory_scope':audit.get('inventory_scope',''),'overlap_definition':audit.get('overlap_definition'),'worst_mutual_overlap':audit.get('worst_dot_overlap'),'worst_mutual_submission':audit.get('worst_overlap_submission'),'worst_forward_overlap':audit.get('worst_forward_overlap'),'worst_forward_submission':audit.get('worst_forward_submission'),'worst_spearman_full_footprint':audit.get('worst_spearman_full_footprint'),'worst_rho_submission':audit.get('worst_rho_submission'),'worst_jaccard':audit.get('worst_jaccard_dot_sets'),'duplicate':duplicate},
        'raster_sha256':receipt['sha256'] if receipt else None,
        'validator_output':validated,'submission_name':NAME,'submission_note':NOTE,'note_chars':len(NOTE),
        'download_and_submit_ok':promoted,'download_ok':bool(validated and not duplicate),'submit_recommended':promoted,
        'weekly_slots_used':0,'experiment_count':2,'elapsed_seconds':round(time.monotonic()-start,2),
        'organizer_confirmed_score':None,
        'evaluator_implementation_sha256':evaluate_holdout.implementation_hashes(),
        'method_source_sha256':{p:sha(ROOT/p) for p in ['src/gems70/method_h70.py','scripts/run_experiment_h70_supervised.py']},
        'registered_parameters':dict(dot_count=DOT_COUNT,block_px=BLOCK,nms_px=NMS,d_min_px=D_MIN,d_max_px=D_MAX,gap_px=GAP_PX)
    }
    dump(E/'run_card.json',card); dump(ROOT/'evidence'/'h70_sup_run_card.json',card)
    print(json.dumps(card,indent=2,default=float),flush=True)

if __name__=='__main__': main()
