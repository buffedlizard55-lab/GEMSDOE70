#!/usr/bin/env python3
"""Pilot: supervised within-halo HGB on SGMC proxy, LOQO.
Quick feasibility check before full experiment.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'vendor')]
import numpy as np, rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
import hashlib

from gems57.grid import load_grid
from gems57 import holdout, evaluate_holdout, uniqueness
from gems57.evaluate_holdout import VERSION

DATA = ROOT / '.cache/data'
GEMS = ROOT / '.cache/gems_data'
CLONE = Path('/tmp/60GEMSDOE')
H33 = CLONE / 'registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif'
SGMC = CLONE / 'data/external/sgmc_faults_100m.tif'

def sha(p): import hashlib; h=hashlib.sha256(); [h.update(b) for b in open(p,'rb').read(1<<20) if True]; return h.hexdigest() # dummy

def load_features():
    grid = load_grid(DATA)
    fp, cat = grid.footprint, grid.catalogue
    # 19-band training_features
    feats = {}
    with rasterio.open(DATA / 'training_features.tif') as src:
        for i in range(1, src.count+1):
            desc = src.descriptions[i-1]
            a = src.read(i).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            feats[desc.split(' - ')[0].strip()] = a
            # also keep by index for debug
    # external lidar 12 bands
    with rasterio.open(GEMS / 'external/lidar_scarp_features_u8.tif') as src:
        for i in range(1, src.count+1):
            desc = src.descriptions[i-1] or f'lidar_{i}'
            a = src.read(i).astype(np.float32)
            # u8 quantised: keep as float, outside footprint is 0? check finite
            a[~fp] = np.nan
            feats[f'lidar_{desc}'] = a
    with rasterio.open(GEMS / 'external/geodawn_rad_u8.tif') as src:
        for i in range(1, src.count+1):
            desc = src.descriptions[i-1]
            a = src.read(i).astype(np.float32)
            a[~fp] = np.nan
            feats[f'rad_{desc}'] = a
    with rasterio.open(GEMS / 'external/geodawn_extensions_u8.tif') as src:
        for i in range(1, src.count+1):
            desc = src.descriptions[i-1]
            a = src.read(i).astype(np.float32)
            a[~fp] = np.nan
            feats[f'ext_{desc}'] = a
    print(f"loaded {len(feats)} features", flush=True)
    return grid, feats

def build_valid(feats, fp):
    valid0 = fp.copy()
    for a in feats.values():
        valid0 &= np.isfinite(a)
    valid = ndi.binary_erosion(valid0, iterations=12)
    print(f"valid0 {valid0.sum()} valid {valid.sum()} fp {fp.sum()}", flush=True)
    return valid0, valid

def get_proxy(grid):
    sgmc = None
    with rasterio.open(SGMC) as src:
        sgmc = src.read(1) > 0
    fp, cat = grid.footprint, grid.catalogue
    d = ndi.distance_transform_edt(~cat)
    proxy = sgmc & ~cat & fp
    proxy_prime = proxy & (d >= 3)
    print(f"sgmc {sgmc.sum()} proxy {proxy.sum()} prime {proxy_prime.sum()} cat {cat.sum()} d>=3 proxy {proxy_prime.sum()}", flush=True)
    return sgmc, proxy, proxy_prime, d

def quadrant_ids(fp):
    yy, xx = np.nonzero(fp)
    ym, xm = int(np.median(yy)), int(np.median(xx))
    gy, gx = np.ogrid[:fp.shape[0], :fp.shape[1]]
    q = np.full(fp.shape, -1, np.int8)
    q[(gy < ym) & (gx < xm) & fp] = 0
    q[(gy < ym) & (gx >= xm) & fp] = 1
    q[(gy >= ym) & (gx < xm) & fp] = 2
    q[(gy >= ym) & (gx >= xm) & fp] = 3
    return q

def rank01(values, valid):
    from scipy.stats import rankdata
    a = np.asarray(values); valid = np.asarray(valid, bool) & np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    n = int(valid.sum())
    if n>1:
        out[valid] = ((rankdata(a[valid], method='average')-1)/(n-1)).astype(np.float32)
    return out

def main():
    grid, feats = load_features()
    fp, cat = grid.footprint, grid.catalogue
    sgmc, proxy, proxy_prime, dcat = get_proxy(grid)
    valid0, valid = build_valid(feats, fp)

    # Prepare feature matrix stacked (H,W,D)
    names = list(feats.keys())
    print("feature names:", names[:5], "...", len(names))
    # Build X for training: valid pixels
    # For memory, stack as float32 2D array sampled
    # Create quadrant for LOQO
    quad = quadrant_ids(fp)

    # Quick canary: AUC per feature on proxy_prime vs random valid not proxy
    rng = np.random.default_rng(70020)
    truth_prox = valid & proxy_prime
    # Sample negatives: valid not proxy
    neg_pool = np.flatnonzero(valid & ~proxy)
    pos_idx = np.flatnonzero(truth_prox)
    neg_sample = rng.choice(neg_pool, min(200000, len(neg_pool)), replace=False)
    pos_sample = pos_idx # all positives prime = 62649, manageable
    labels = np.r_[np.ones(len(pos_sample)), np.zeros(len(neg_sample))]
    print(f"canary: pos {len(pos_sample)} neg {len(neg_sample)}", flush=True)
    canaries = {}
    for n in names:
        a = feats[n]
        vals = np.r_[a.ravel()[pos_sample], a.ravel()[neg_sample]]
        if not np.isfinite(vals).all():
            print(f"skip {n} non-finite")
            continue
        auc = roc_auc_score(labels, vals)
        canaries[n] = auc
        if auc>0.65 or auc<0.35:
            print(f"CANARY {n:20s} AUC {auc:.3f}")
        if max(auc,1-auc) > 0.90:
            print(f"LEAKAGE ALARM {n} {auc}")
    # print top 10
    top = sorted(canaries.items(), key=lambda kv: max(kv[1],1-kv[1]), reverse=True)[:10]
    print("top canaries (proxy truth):", top, flush=True)

    # Also canary on holdout truth (catalogue withheld simulation)
    # Quick: use buffered_component_draw truth
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    truth_hold = np.zeros(fp.shape, bool)
    active_hold = np.zeros(fp.shape, bool)
    for f in folds:
        active_hold |= valid & f['region'] & ~f['masked_known']
        truth_hold |= valid & f['truth']
    pos_h = np.flatnonzero(truth_hold)
    neg_h = np.flatnonzero(active_hold & ~truth_hold)
    neg_h = rng.choice(neg_h, min(200000, len(neg_h)), replace=False)
    labels_h = np.r_[np.ones(len(pos_h)), np.zeros(len(neg_h))]
    print(f"holdout canary pos {len(pos_h)} neg {len(neg_h)}", flush=True)
    for n in names:
        a=feats[n]
        vals=np.r_[a.ravel()[pos_h], a.ravel()[neg_h]]
        auc=roc_auc_score(labels_h, vals)
        if auc>0.60 or auc<0.40:
            print(f"HOLDOUT CANARY {n:20s} AUC {auc:.3f}")

    # Supervised LOQO: for each quadrant q, train on proxy_prime pixels outside q (and inside valid+eroded? use valid)
    # Build feature stack array for all valid pixels
    # For speed, use only top features by canary? Let's use all 39 but may be heavy. Use select: top 10 canary + all physics 19 + lidar/rad
    # Actually just use all 39: 5M pixels * 39 = 200M floats ~800MB too large. So sample training.

    feature_list = names  # all
    # Precompute rank? No, use raw values

    # For each quadrant, define train mask
    pred_rank = np.zeros(fp.shape, np.float32)  # will fill per quadrant
    # Also need global rank for final submission dots (train on all)
    # Let's do LOQO for holdout evaluation, then final model train on all for submission

    # Collect training samples per quadrant
    # To avoid leakage, for each quadrant we must exclude proxy positives inside quadrant from training (they are test). Also need to respect valid erosion already.
    # Negative training = valid & ~proxy_prime & ~outside training region? Actually we train on all valid outside test quadrant (or outside eroded test region) to keep similar distribution.
    # Use quadrant eroded by 12 as region (same as holdout domain)

    # Build quadrant regions
    quad_regions = []
    for q in range(4):
        region = ndi.binary_erosion(quad==q, iterations=12) & fp
        quad_regions.append(region)

    oof_pred = np.full(fp.shape, np.nan, dtype=np.float32)

    for q in range(4):
        print(f"\n--- LOQO quadrant {q} ---", flush=True)
        # train region = valid outside q's region? Actually union of other quadrants' eroded regions
        train_valid = valid.copy()
        train_valid[quad_regions[q]] = False  # hold out this quadrant's scored domain
        # Also must ensure not training on eroded boundary? Already valid is eroded by 12, but quad regions also eroded, so fine
        # Positive training
        train_pos = train_valid & proxy_prime
        train_neg = train_valid & ~proxy & ~proxy_prime  # valid not proxy
        # Sample
        pos_idx = np.flatnonzero(train_pos)
        neg_idx = np.flatnonzero(train_neg)
        npos = len(pos_idx)
        nneg = len(neg_idx)
        print(f" train pos {npos} neg {nneg}", flush=True)
        # Downsample negatives to balance: use 3x positives or 50k
        if nneg > 150000:
            neg_idx = rng.choice(neg_idx, 150000, replace=False)
        if npos > 50000:
            pos_idx = rng.choice(pos_idx, 50000, replace=False)
        # If npos too small (<1000) warn
        if npos < 500:
            print(f"WARNING q{q} few positives")
        # Build X train
        X_pos = np.stack([feats[n].ravel()[pos_idx] for n in feature_list], axis=1)
        X_neg = np.stack([feats[n].ravel()[neg_idx] for n in feature_list], axis=1)
        X_train = np.vstack([X_pos, X_neg])
        y_train = np.r_[np.ones(len(pos_idx)), np.zeros(len(neg_idx))]
        print(f" X_train {X_train.shape}", flush=True)
        # Fill NaN? Should be none inside valid
        if not np.isfinite(X_train).all():
            print("non-finite in X_train!")
            # replace with median
            med = np.nanmedian(X_train, axis=0)
            X_train = np.where(np.isfinite(X_train), X_train, med)
        clf = HistGradientBoostingClassifier(max_depth=8, max_iter=150, learning_rate=0.08, min_samples_leaf=50, random_state=20)
        clf.fit(X_train, y_train)
        # Predict on test quadrant's valid pixels
        test_mask = valid & quad_regions[q]
        test_idx = np.flatnonzero(test_mask)
        X_test = np.stack([feats[n].ravel()[test_idx] for n in feature_list], axis=1)
        if not np.isfinite(X_test).all():
            med = np.nanmedian(X_test, axis=0)
            X_test = np.where(np.isfinite(X_test), X_test, med)
        prob = clf.predict_proba(X_test)[:,1]
        oof_pred.ravel()[test_idx] = prob
        print(f" oof pred q{q} mean {prob.mean():.4f} max {prob.max():.4f}", flush=True)
        # report AUC on quadrant holdout proxy
        truth_q = proxy_prime & test_mask
        # sample balanced AUC via all test positives vs negatives
        y_true = truth_q.ravel()[test_idx].astype(int)
        if y_true.sum()>0 and y_true.sum()<len(y_true):
            auc = roc_auc_score(y_true, prob)
            print(f" LOQO AUC proxy q{q}: {auc:.4f}", flush=True)

    # Fill missing (outside quad regions) with global model or 0
    missing = ~np.isfinite(oof_pred) & valid
    print(f"missing oof {missing.sum()}", flush=True)
    # Train global model for missing and for final rank
    print("\n--- Global model ---", flush=True)
    all_pos = np.flatnonzero(valid & proxy_prime)
    all_neg = np.flatnonzero(valid & ~proxy)
    all_neg = rng.choice(all_neg, min(200000, len(all_neg)), replace=False)
    X_pos = np.stack([feats[n].ravel()[all_pos] for n in feature_list], axis=1)
    X_neg = np.stack([feats[n].ravel()[all_neg] for n in feature_list], axis=1)
    X_train = np.vstack([X_pos, X_neg])
    y_train = np.r_[np.ones(len(all_pos)), np.zeros(len(all_neg))]
    clf_global = HistGradientBoostingClassifier(max_depth=8, max_iter=200, learning_rate=0.08, min_samples_leaf=50, random_state=20)
    clf_global.fit(X_train, y_train)
    # Predict missing
    if missing.any():
        idx = np.flatnonzero(missing)
        Xt = np.stack([feats[n].ravel()[idx] for n in feature_list], axis=1)
        oof_pred.ravel()[idx] = clf_global.predict_proba(Xt)[:,1]
    # Also full prediction for submission (use global)
    full_idx = np.flatnonzero(valid)
    X_full = np.stack([feats[n].ravel()[full_idx] for n in feature_list], axis=1)
    full_prob = clf_global.predict_proba(X_full)[:,1]
    full_pred = np.full(fp.shape, 0.0, dtype=np.float32)
    full_pred.ravel()[full_idx] = full_prob.astype(np.float32)
    # Rank it
    from scipy.stats import rankdata
    # For dot placement, rank over valid
    rank_field = np.zeros(fp.shape, np.float32)
    r = rankdata(full_prob, method='average')
    rank_field.ravel()[full_idx] = ((r-1)/(len(r)-1)).astype(np.float32)

    # OOF rank for holdout evaluation (use oof_pred)
    oof_rank = np.zeros(fp.shape, np.float32)
    valid_oof = valid & np.isfinite(oof_pred)
    r2 = rankdata(oof_pred[valid_oof], method='average')
    oof_rank[valid_oof] = ((r2-1)/(len(r2)-1)).astype(np.float32)

    # Now evaluate HOLDOUT-DTI on catalogue withheld folds using oof_rank vs random vs H33
    # Need to emit dots: priority thinning
    from gems70 import method2
    # Use method2.priority_thin
    print("\n--- Evaluating HOLDOUT-DTI (instrument A) ---", flush=True)
    # Helper to create dots from rank
    def dots_from_rank(rank_field, allowed, n=38000):
        mask, cnt = method2.priority_thin(rank_field, allowed, target_n=n)
        print(f" dots {cnt} vs target {n} allowed {allowed.sum()}")
        return mask, cnt

    # Build allowed for holdout = valid (already eroded) but need to handle catalogue masking via evaluator
    # For dot placement for holdout evaluation, we use valid & ~? The evaluator will mask visible faults, but dots should not be on visible faults during training? For comparability, previous experiments placed dots without catalogue exclusion for holdout then evaluator masked. So we follow same: allowed = valid (no catalogue exclusion) for holdout dots.
    # For final submission, allowed = valid & (dist_cat >2)

    candidate_dots, n_cand = dots_from_rank(oof_rank, valid, n=38000)
    cand_field = candidate_dots.astype(np.float32)

    # Random control
    random_dots = np.zeros(fp.shape, bool)
    ids = rng.choice(np.flatnonzero(valid), 38000, replace=False)
    random_dots.ravel()[ids] = True
    rand_field = random_dots.astype(np.float32)

    # H33
    with rasterio.open(H33) as src:
        h33 = src.read(1).astype(np.float32)
    h33_bin = np.where(np.isfinite(h33) & (h33>0.5) & fp, 1.0, 0.0).astype(np.float32)

    # Evaluate via holdout buffered draw
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    # Use evaluate_holdout
    def cropped(fold, p, valid):
        y, x = np.nonzero(fold['region'])
        y0, x0 = max(0, int(y.min())-6), max(0, int(x.min())-6)
        y1, x1 = min(p.shape[0], int(y.max())+7), min(p.shape[1], int(x.max())+7)
        sl=np.s_[y0:y1, x0:x1]
        sub = {k: v[sl] for k,v in fold.items() if isinstance(v,np.ndarray) and v.shape==p.shape}
        return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0,x0), global_shape=p.shape)

    arms = {'candidate': cand_field, 'random_control': rand_field, 'h33_reference': h33_bin}
    terms = {k:0.0 for k in arms}
    for fold in folds:
        for name, p in arms.items():
            r,t = cropped(fold, p, valid)
            terms[name] += t
    summary = evaluate_holdout.pooled_summary(terms, draws=1000, seed=70420, candidate='candidate')
    print("\nINSTRUMENT A HOLDOUT-DTI", flush=True)
    for k,v in summary['scores'].items():
        print(f"{k:15s} DTI {v['dti']:.4f} CI {v['ci95']}", flush=True)
    for k,v in summary['paired_differences'].items():
        print(f"delta vs {k}: {v['delta']:.4f} CI {v['ci95']}", flush=True)

    # Instrument B'
    print("\n--- INSTRUMENT B' (SGMC proxy prime) ---", flush=True)
    quad2 = holdout.quadrant_ids(fp)
    terms_b = {k:0.0 for k in arms}
    # But for B', we need production dots (final submission dots) not OOF? For feasibility, use full_pred ranking dots
    final_allowed = valid & (dcat >= 3)  # Wait proxy prime requires d>=3, but submission dots must be off catalogue >2px? Use >2 for final
    # Let's create production dots from full rank (trained on all)
    prod_dots, _ = dots_from_rank(rank_field, valid & (dcat>2), n=38000)
    prod_field = prod_dots.astype(np.float32)
    # Use prod vs random vs h33 for B'
    prod_arms = {'candidate': prod_field, 'random_control': rand_field, 'h33_reference': h33_bin}
    for k in range(4):
        region = ndi.binary_erosion(quad2==k, iterations=12) & fp
        for tag, mask in [('prime', proxy_prime)]:
            fold = dict(region=region, truth=mask & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
            for name, p in prod_arms.items():
                r,t = cropped(fold, p, valid)
                terms_b[name] += t
    summary_b = evaluate_holdout.pooled_summary(terms_b, draws=1000, seed=70420, candidate='candidate')
    print("INSTRUMENT B' SGMC prime", flush=True)
    for k,v in summary_b['scores'].items():
        print(f"{k:15s} DTI {v['dti']:.4f} CI {v['ci95']}", flush=True)
    for k,v in summary_b['paired_differences'].items():
        print(f"delta vs {k}: {v['delta']:.4f} CI {v['ci95']}", flush=True)

    # Also evaluate unrestricted B
    terms_ball = {k:0.0 for k in prod_arms}
    for k in range(4):
        region = ndi.binary_erosion(quad2==k, iterations=12) & fp
        fold = dict(region=region, truth=proxy & region & ~cat, visible=cat, masked_known=cat, hidden_all=np.zeros_like(cat))
        for name, p in prod_arms.items():
            r,t = cropped(fold, p, valid)
            terms_ball[name] += t
    summary_ball = evaluate_holdout.pooled_summary(terms_ball, draws=1000, seed=70420, candidate='candidate')
    print("INSTRUMENT B unrestricted", flush=True)
    for k,v in summary_ball['scores'].items():
        print(f"{k:15s} DTI {v['dti']:.4f} CI {v['ci95']}", flush=True)

    # Save quick results
    out = {
        'instrument_a': summary,
        'instrument_b_prime': summary_b,
        'instrument_b': summary_ball,
        'feature_names': feature_list,
        'oof_mean': float(np.nanmean(oof_pred[valid])),
        'full_mean': float(np.nanmean(full_pred[valid])),
    }
    Path('evidence/pilot_supervised.json').write_text(__import__('json').dumps(out, indent=2))
    print("saved pilot", flush=True)

if __name__ == '__main__':
    main()
