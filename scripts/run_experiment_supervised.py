#!/usr/bin/env python3
"""E4 supervised within-halo HGB (preregistration-supervised.md, hashed in manifest).
Lane: supervised within-halo ranking on SGMC proxy, LOQO, 39-feature stack.
"""
import datetime as dt, hashlib, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'vendor'), str(ROOT/'scripts')]
import numpy as np, rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid
from gems70.method import rank01
from gems70 import method2
from restore_data import DATA, PINS, sha

E = ROOT/'evidence'/'supervised'
CACHE = ROOT/'.cache'
CLONE = Path('/tmp/60GEMSDOE')
REG = CLONE/'registry'/'rasters'
H33 = CLONE/'registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif'
H33_SHA='c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
SGMC = CLONE/'data/external/sgmc_faults_100m.tif'
D_TARGET=38000
THIN_DIST=2.8
THIN_POOL=400000
NAME='gems70-supervised-hgb39-38000-20261021'
NOTE='Supervised HGB 39feat SGMC proxy LOQO 38k dots off-cat; HOLDOUT-DTI in run card'
BUDGET_S=7200

def dump(p,d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(d,indent=2,allow_nan=False,default=float)+'\n'); tmp.replace(p)

def cropped(fold,p,valid):
    y,x=np.nonzero(fold['region'])
    y0,x0=max(0,int(y.min())-6),max(0,int(x.min())-6)
    y1,x1=min(p.shape[0],int(y.max())+7),min(p.shape[1],int(x.max())+7)
    sl=np.s_[y0:y1,x0:x1]
    sub={k:v[sl] for k,v in fold.items() if isinstance(v,np.ndarray) and v.shape==p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0,x0), global_shape=p.shape)

def main():
    start=time.monotonic()
    manifest=E/'experiment_manifest.json'
    if manifest.exists():
        raise RuntimeError('E4 already attempted. Inspect evidence/supervised; no silent reruns.')
    E.mkdir(parents=True, exist_ok=True)
    dump(manifest, {'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                    'experiment':'E4-supervised-hgb39','maximum_experiments':3,'maximum_seconds':BUDGET_S,
                    'preregistration_sha256':sha(ROOT/'docs/preregistration-supervised.md'),
                    'source_sha256':{p:sha(ROOT/p) for p in ['src/gems70/method2.py','src/gems70/method.py','scripts/run_experiment_supervised.py']}})
    def budget():
        if time.monotonic()-start>BUDGET_S: raise TimeoutError('budget exhausted')
    for name,exp in PINS.items():
        if sha(DATA/name)!=exp: raise ValueError('pin mismatch '+name)
    if sha(H33)!=H33_SHA: raise ValueError('H33 sha')
    grid=load_grid(DATA); fp,cat=grid.footprint,grid.catalogue
    print('grid',grid.shape, int(fp.sum()), flush=True)

    # Load 39 features
    feats={}
    with rasterio.open(DATA/'training_features.tif') as src:
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1].split(' - ')[0].strip()
            a=src.read(i).astype(np.float32)
            a[(a<=-1e30) | ~np.isfinite(a) | ~fp]=np.nan
            feats[desc]=a
    with rasterio.open(ROOT/'.cache/gems_data/external/lidar_scarp_features_u8.tif') as src:
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1] or f'lidar_{i}'
            a=src.read(i).astype(np.float32); a[~fp]=np.nan
            feats[f'lidar_{desc}']=a
    with rasterio.open(ROOT/'.cache/gems_data/external/geodawn_rad_u8.tif') as src:
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1]
            a=src.read(i).astype(np.float32); a[~fp]=np.nan
            feats[f'rad_{desc}']=a
    with rasterio.open(ROOT/'.cache/gems_data/external/geodawn_extensions_u8.tif') as src:
        for i in range(1, src.count+1):
            desc=src.descriptions[i-1]
            a=src.read(i).astype(np.float32); a[~fp]=np.nan
            feats[f'ext_{desc}']=a
    names=list(feats.keys())
    print(f'features {len(names)}', flush=True)

    valid0=fp.copy()
    for a in feats.values(): valid0 &= np.isfinite(a)
    valid=ndi.binary_erosion(valid0, iterations=12)
    print(f'valid0 {int(valid0.sum())} valid {int(valid.sum())}', flush=True)
    if not valid.any(): raise ValueError('no valid')

    # SGMC proxy
    with rasterio.open(SGMC) as src:
        sgmc=src.read(1)>0
    dcat=ndi.distance_transform_edt(~cat)
    proxy=sgmc & ~cat & fp
    proxy_prime=proxy & (dcat>=3)
    print(f'sgmc {int(sgmc.sum())} proxy {int(proxy.sum())} prime {int(proxy_prime.sum())}', flush=True)

    # Holdout draw for instrument A
    folds,_=holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    dump(E/'holdout_split.json', {'evidence_class':'HOLDOUT-DTI','evaluator_version':evaluate_holdout.VERSION,
                                  'receipts':[f['receipt'] for f in folds],
                                  'total_withheld':int(sum((f['truth']&valid).sum() for f in folds)),
                                  'valid_pixels':int(valid.sum()),
                                  'known_rule':'catalogue minus globally withheld, pixel exact'})

    # Canaries: proxy prime vs random valid not proxy, and holdout truth vs negatives
    truth_proxy = valid & proxy_prime
    active_proxy = valid # for proxy canary domain
    pos_proxy=np.flatnonzero(truth_proxy); neg_pool=np.flatnonzero(valid & ~proxy)
    rng=np.random.default_rng(70020)
    neg_proxy=rng.choice(neg_pool, min(200000,len(neg_pool)), replace=False)
    labels_proxy=np.r_[np.ones(len(pos_proxy)), np.zeros(len(neg_proxy))]
    # holdout truth domain
    truth_hold=np.zeros(fp.shape,bool); active_hold=np.zeros(fp.shape,bool)
    for f in folds:
        active_hold |= valid & f['region'] & ~f['masked_known']
        truth_hold |= valid & f['truth']
    pos_hold=np.flatnonzero(truth_hold); neg_hold=np.flatnonzero(active_hold & ~truth_hold)
    neg_hold=rng.choice(neg_hold, min(200000,len(neg_hold)), replace=False)
    labels_hold=np.r_[np.ones(len(pos_hold)), np.zeros(len(neg_hold))]

    canaries={}
    for n,a in feats.items():
        for domain, pos, neg, lab, tag in [('proxy_prime',pos_proxy,neg_proxy,labels_proxy,'proxy'),('holdout_catalogue',pos_hold,neg_hold,labels_hold,'holdout')]:
            vals=np.r_[a.ravel()[pos], a.ravel()[neg]]
            if not np.isfinite(vals).all():
                raise ValueError(f'canary {n} {tag} non-finite')
            auc=float(roc_auc_score(lab, vals))
            canaries.setdefault(n, {})[tag]=dict(auc=auc, inverse=1-auc, suspected=bool(max(auc,1-auc)>0.90))
            if max(auc,1-auc)>0.90:
                raise RuntimeError(f'LEAKAGE CANARY STOP: {n} {tag} AUC {auc}')
    # also check derived OOF later
    print('canaries computed', flush=True)
    dump(E/'canaries.json', canaries)

    # Quadrant for LOQO
    quad=holdout.quadrant_ids(fp)
    quad_regions=[ndi.binary_erosion(quad==q, iterations=12)&fp for q in range(4)]

    # LOQO training
    feature_list=names
    oof_pred=np.full(fp.shape, np.nan, dtype=np.float32)

    for q in range(4):
        budget()
        train_valid=valid.copy(); train_valid[quad_regions[q]]=False
        train_pos=train_valid & proxy_prime
        train_neg=train_valid & ~proxy
        pos_idx=np.flatnonzero(train_pos); neg_idx=np.flatnonzero(train_neg)
        print(f'Q{q} pos {len(pos_idx)} neg {len(neg_idx)}', flush=True)
        if len(neg_idx)>120000: neg_idx=rng.choice(neg_idx,120000,replace=False)
        if len(pos_idx)>40000: pos_idx=rng.choice(pos_idx,40000,replace=False)
        Xp=np.stack([feats[n].ravel()[pos_idx] for n in feature_list], axis=1)
        Xn=np.stack([feats[n].ravel()[neg_idx] for n in feature_list], axis=1)
        X=np.vstack([Xp,Xn]); y=np.r_[np.ones(len(pos_idx)), np.zeros(len(neg_idx))]
        # check finite
        if not np.isfinite(X).all():
            raise ValueError('train non-finite')
        clf=HistGradientBoostingClassifier(max_depth=6, max_iter=100, learning_rate=0.1, min_samples_leaf=30, random_state=20)
        clf.fit(X,y)
        print(f' fit Q{q}', flush=True)
        test_mask=valid & quad_regions[q]
        test_idx=np.flatnonzero(test_mask)
        Xt=np.stack([feats[n].ravel()[test_idx] for n in feature_list], axis=1)
        prob=clf.predict_proba(Xt)[:,1]
        oof_pred.ravel()[test_idx]=prob
        y_true=proxy_prime.ravel()[test_idx].astype(int)
        if y_true.sum()>0:
            print(f' Q{q} LOQO AUC proxy {roc_auc_score(y_true, prob):.4f}', flush=True)

    oof_pred[np.isnan(oof_pred)&valid]=np.nanmedian(oof_pred[valid & np.isfinite(oof_pred)])
    print(f'oof missing after fill {np.isnan(oof_pred[valid]).sum()}', flush=True)

    # Canary for derived OOF feature on holdout
    vals_proxy=np.r_[oof_pred.ravel()[pos_proxy], oof_pred.ravel()[neg_proxy]]
    auc_proxy=float(roc_auc_score(labels_proxy, vals_proxy))
    vals_hold=np.r_[oof_pred.ravel()[pos_hold], oof_pred.ravel()[neg_hold]]
    auc_hold=float(roc_auc_score(labels_hold, vals_hold))
    print(f'OOF canary proxy AUC {auc_proxy:.4f} holdout AUC {auc_hold:.4f}', flush=True)
    canaries['OOF_prob_proxy_LOQO']={'proxy':dict(auc=auc_proxy, suspected=bool(max(auc_proxy,1-auc_proxy)>0.90)),
                                      'holdout':dict(auc=auc_hold, suspected=bool(max(auc_hold,1-auc_hold)>0.90))}
    if max(auc_proxy,1-auc_proxy)>0.90 or max(auc_hold,1-auc_hold)>0.90:
        raise RuntimeError('LEAKAGE canary OOF')
    dump(E/'canaries.json', canaries)

    # Rank fields
    # OOF rank for holdout evaluation
    oof_rank=np.zeros(fp.shape, np.float32)
    vm=valid & np.isfinite(oof_pred)
    r=rankdata(oof_pred[vm], method='average'); oof_rank[vm]=((r-1)/(len(r)-1)).astype(np.float32)
    # Save for uniqueness surface (continuous)
    np.save(CACHE/'supervised_oof_rank.npy', oof_rank)
    # Check surface uniqueness via Spearman only (continuous surface not to be evaluated via dot overlap)
    # We'll do minimal check: compute worst Spearman vs registry surfaces using rank

    # Global model for final submission (train on all)
    print('global model', flush=True)
    all_pos=np.flatnonzero(valid & proxy_prime); all_neg=np.flatnonzero(valid & ~proxy)
    all_neg=rng.choice(all_neg, min(200000,len(all_neg)), replace=False)
    Xp=np.stack([feats[n].ravel()[all_pos] for n in feature_list], axis=1)
    Xn=np.stack([feats[n].ravel()[all_neg] for n in feature_list], axis=1)
    X=np.vstack([Xp,Xn]); y=np.r_[np.ones(len(all_pos)), np.zeros(len(all_neg))]
    del Xp, Xn
    print(f'global X {X.shape}', flush=True)
    clf_g=HistGradientBoostingClassifier(max_depth=6, max_iter=100, learning_rate=0.1, min_samples_leaf=30, random_state=20)
    clf_g.fit(X,y)
    print('global fit done', flush=True)
    del X, y
    # chunked prediction for full_rank to avoid OOM (4.9M pixels)
    full_rank=np.zeros(fp.shape, np.float32)
    full_idx=np.flatnonzero(valid)
    chunk=500000
    probs=[]
    for i in range(0, len(full_idx), chunk):
        budget()
        idx_chunk=full_idx[i:i+chunk]
        Xf=np.stack([feats[n].ravel()[idx_chunk] for n in feature_list], axis=1)
        prob_chunk=clf_g.predict_proba(Xf)[:,1]
        probs.append(prob_chunk)
        print(f' chunk {i//chunk+1}/{(len(full_idx)+chunk-1)//chunk}', flush=True)
        del Xf, prob_chunk
    full_prob=np.concatenate(probs); del probs
    print(f'full_prob {full_prob.shape}', flush=True)
    r=rankdata(full_prob, method='average')
    full_rank.ravel()[full_idx]=((r-1)/(len(r)-1)).astype(np.float32)
    del full_prob, r
    np.save(CACHE/'supervised_full_rank.npy', full_rank)
    print('ranks ready', flush=True)

    # Dot emission
    cand_mask, n_cand = method2.priority_thin(oof_rank, valid, target_n=D_TARGET, min_dist=THIN_DIST, pool=THIN_POOL)
    print(f'holdout dots {n_cand}', flush=True)
    prod_mask, n_prod = method2.priority_thin(full_rank, valid & (dcat>2), target_n=D_TARGET, min_dist=THIN_DIST, pool=THIN_POOL)
    print(f'prod dots {n_prod}', flush=True)
    cand_field=cand_mask.astype(np.float32)
    prod_field=prod_mask.astype(np.float32) # for B' production (will be final submission field)

    # Reference arms
    with rasterio.open(H33) as src:
        h33=src.read(1).astype(np.float32)
    h33_bin=np.where(np.isfinite(h33)&(h33>0.5)&fp,1.0,0.0).astype(np.float32)
    # random
    random_dots=np.zeros(fp.shape,bool); ids=rng.choice(np.flatnonzero(valid), D_TARGET, replace=False); random_dots.ravel()[ids]=True
    rand_field=random_dots.astype(np.float32)
    # D28 for bonus
    d28_path=CLONE/'registry/rasters/GEMSDOE25__dotted-h19-5-d2-8.tif'
    with rasterio.open(d28_path) as src:
        d28=src.read(1).astype(np.float32)
    d28_bin=np.where(np.isfinite(d28)&(d28>0.5)&fp,1.0,0.0).astype(np.float32)

    arms={'candidate':cand_field,'random_control':rand_field,'h33_reference':h33_bin,'d28_ref':d28_bin}
    terms={k:0.0 for k in arms}
    folds_results={k:[] for k in arms}
    for fold in folds:
        for name,p in arms.items():
            r,t=cropped(fold,p,valid)
            terms[name]+=t
            folds_results[name].append(r)
    summary=evaluate_holdout.pooled_summary(terms, draws=1000, seed=70420, candidate='candidate')
    summary['instrument']='A: shared hide-and-recover catalogue holdout'
    dump(E/'instrumentA_holdout.json', summary); dump(E/'instrumentA_folds.json', folds_results)
    print('instrument A done', flush=True)

    # B' evaluation: use prod_field (final submission style) vs random vs h33
    quad2=holdout.quadrant_ids(fp)
    terms_b={k:0.0 for k in ['candidate','random_control','h33_reference']}
    folds_b={k:[] for k in terms_b}
    terms_ball={k:0.0 for k in terms_b}
    prod_arms={'candidate':prod_field,'random_control':rand_field,'h33_reference':h33_bin}
    for k in range(4):
        region=ndi.binary_erosion(quad2==k, iterations=12)&fp
        for (tag, mask, store) in [('prime',proxy_prime,terms_b),('all',proxy,terms_ball)]:
            fold=dict(region=region, truth=mask & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
            for name,p in prod_arms.items():
                r,t=cropped(fold,p,valid)
                store[name]+=t
                if tag=='prime': folds_b[name].append(r)
    summary_b=evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70420, candidate='candidate')
    summary_b['instrument']="B': SGMC proxy d>=3px"
    summary_b['proxy_prime_pixels']=int(proxy_prime.sum()); summary_b['proxy_all_pixels']=int(proxy.sum())
    dump(E/'instrumentB_prime.json', summary_b); dump(E/'instrumentB_prime_folds.json', folds_b)
    summary_ball=evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=70420, candidate='candidate')
    summary_ball['instrument']='B: unrestricted SGMC proxy'
    dump(E/'instrumentB_all.json', summary_ball)
    print('instrument B done', flush=True)

    # Uniqueness: before placement, surface Spearman only (no dot overlap)
    # Use full_rank as continuous surface; compare via uniqueness but expect low rho
    # Now final dots uniqueness vs 62 rasters
    # Build index
    records=[]
    for p in sorted(REG.glob('*.tif')):
        with rasterio.open(p) as src:
            if src.count!=1 or (src.height,src.width)!=grid.shape: continue
        records.append(dict(repo_first=p.name.split('__')[0], submission=p.name, sources=[p.name], cache_file=str(p), sha256=sha(p)))
    index=dict(complete_accessible_scan=True, errors=[], rasters=records)
    # Use prod dots for uniqueness (final submission)
    tmp_tif=CACHE/'supervised_prod_for_uniqueness.tif'
    if tmp_tif.exists(): tmp_tif.unlink()
    from gems57.grid import write_geotiff
    write_geotiff(tmp_tif, prod_field, nodata=None)
    audit=uniqueness.compare_to_registry(tmp_tif, index, fp, expected_grid=(grid.shape, grid.crs, grid.transform))
    audit['inventory_scope']=f"{len(records)} single-band 100 m rasters archived in buffedlizard55-lab/60GEMSDOE/registry/rasters; not an organizer registry and not exhaustive"
    dump(E/'uniqueness.json', audit)
    duplicate=bool(audit['unique'] is False or audit['duplicate_count']>0)
    print(f"uniqueness duplicate {duplicate} worst mutual {audit['worst_dot_overlap']:.4f} worst rho {audit['worst_spearman_full_footprint']}", flush=True)
    # Surface rho check
    # Compare oof_rank surface rho vs registry (should be low)
    # Use direct Spearman via uniqueness helper (we can reuse compare_array but with surface)
    # For continuous surface, we only check Spearman; but we can run same compare_array with continuous values
    # Build surface tmp
    tmp_surf=CACHE/'supervised_surface.tif'
    if tmp_surf.exists(): tmp_surf.unlink()
    # continuous surface in [0,1] already in [0,1] via rank, outside footprint 0
    surf_for_disk = np.where(fp, oof_rank, 0).astype(np.float32)
    write_geotiff(tmp_surf, surf_for_disk, nodata=None)
    # Use compare_array but we will just check rho limit
    surf_audit=uniqueness.compare_to_registry(tmp_surf, index, fp, expected_grid=(grid.shape, grid.crs, grid.transform))
    dump(E/'surface_uniqueness.json', surf_audit)
    print(f"surface worst rho {surf_audit['worst_spearman_full_footprint']}", flush=True)

    # Writer
    receipt=validated=None
    if not duplicate:
        from gems57 import submission_writer
        receipt=submission_writer.write_submission(ROOT/'docs/downloads'/f'{NAME}.tif', prod_field, ROOT/'data/bridge/sample_submission.tif', fp, note=NOTE, name=NAME, catalogue=cat, metadata={'evidence_class':'HOLDOUT-DTI+PROXY-DTI; not organizer-confirmed'})
        validated=receipt['validator']
    dump(E/'submission_receipt.json', dict(receipt=receipt, validated=validated, duplicate=duplicate, surface_audit=surf_audit))

    a=summary['scores']; b=summary_b['scores']
    db=summary_b['paired_differences']
    gate_a=bool(a['candidate']['dti'] >= a['h33_reference']['dti'])
    gate_b=bool(db['h33_reference']['delta']>0 and db['h33_reference']['ci95'][0]>0)
    # also require candidate > random significantly
    gate_rand=bool(summary_b['paired_differences']['random_control']['ci95'][0]>0)
    promoted=bool(not duplicate and validated and gate_a and gate_b and gate_rand)
    # For supervised lane, we consider B' primary; if B' not significant but beats H33 point-wise and beats random, we still publish as negative but downloadable
    # Promotion requires all gates; otherwise negative
    card={
        'hypothesis':'Supervised HGB 39-feature SGMC proxy LOQO (E4)',
        'mechanism':'HistGradientBoosting p(proxy) from 39 physics+lidar+rad bands, LOQO OOF ranks, 2.8px priority thinning 38k dots d>2px',
        'non_fault_mimic':'Alluvial lithologic K/Th boundary, flat playa, volcanic flow edge, road grade',
        'verdict':'promote' if promoted else 'negative',
        'evidence_class':'HOLDOUT-DTI (A) and PROXY-DTI (B/B_prime); neither organizer-confirmed',
        'instrument_a_holdout':{k:{kk:v[kk] for kk in ('dti','ci95','withheld_positive_pixels')} for k,v in a.items()},
        'instrument_b_prime_proxy':{k:{kk:v[kk] for kk in ('dti','ci95','withheld_positive_pixels')} for k,v in b.items()},
        'instrument_b_unrestricted':{k:{kk:v[kk] for kk in ('dti','ci95')} for k,v in summary_ball['scores'].items()},
        'paired_a_vs_h33':summary['paired_differences']['h33_reference'],
        'paired_b_prime_vs_h33':db['h33_reference'],
        'paired_b_prime_vs_random':summary_b['paired_differences']['random_control'],
        'gate_a_candidate_ge_h33':bool(gate_a),
        'gate_b_prime_candidate_gt_h33_significant':gate_b,
        'gate_b_prime_vs_random_significant':gate_rand,
        'correlation_overlap_vs_registry':{
            'stage':'final production dots (38000 binary)',
            'rasters_checked':audit['registry_rasters_checked'],
            'inventory_scope':audit['inventory_scope'],
            'overlap_definition':audit.get('overlap_definition'),
            'worst_mutual_overlap':audit['worst_dot_overlap'],
            'worst_mutual_submission':audit['worst_overlap_submission'],
            'worst_forward_overlap':audit['worst_forward_overlap'],
            'worst_forward_submission':audit['worst_forward_submission'],
            'worst_spearman_full_footprint':audit['worst_spearman_full_footprint'],
            'worst_rho_submission':audit['worst_rho_submission'],
            'worst_jaccard':audit['worst_jaccard_dot_sets'],
            'duplicate':duplicate,
            'surface_worst_rho':surf_audit['worst_spearman_full_footprint'],
        },
        'raster_sha256':receipt['sha256'] if receipt else None,
        'raster_sha256_reason':None if receipt else 'uniqueness gate failed; no TIFF written',
        'validator_output':validated,
        'submission_name':NAME,
        'submission_note':NOTE,
        'note_chars':len(NOTE),
        'download_and_submit_ok':promoted,
        'download_ok':bool(receipt and not duplicate),
        'submit_recommended':promoted,
        'weekly_slots_used':0,
        'experiment_count':1,
        'elapsed_seconds':round(time.monotonic()-start,2),
        'organizer_confirmed_score':None,
        'evaluator_implementation_sha256':evaluate_holdout.implementation_hashes(),
        'method_source_sha256':{p:sha(ROOT/p) for p in ['src/gems70/method2.py','src/gems70/method.py','scripts/run_experiment_supervised.py']},
        'registered_parameters':dict(dot_count=D_TARGET, thin_dist_px=THIN_DIST, thin_pool=THIN_POOL, max_depth=6, max_iter=100, learning_rate=0.1, min_samples_leaf=30, feature_count=len(names)),
        'feature_names':names,
    }
    dump(E/'run_card.json', card)
    print(json.dumps(card, indent=2, default=float), flush=True)

if __name__=='__main__':
    main()
