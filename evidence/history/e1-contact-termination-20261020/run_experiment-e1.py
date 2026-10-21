"""Bounded experiment; literal duplicate witness stops BEFORE dot placement/export."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'vendor'), str(ROOT/'scripts')]
import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score
from gems57 import evaluate_holdout, holdout, uniqueness
from gems57.grid import load_grid
from gems70.method import physical_features, joint_field, rank01, upper_surface
from restore_data import DATA, PINS, sha, fetch

E = ROOT/'evidence'
CACHE = ROOT/'.cache'


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def cropped(fold, p, valid):
    y, x = np.nonzero(fold['region'])
    y0, x0 = max(0, int(y.min())-6), max(0, int(x.min())-6)
    y1, x1 = min(p.shape[0], int(y.max())+7), min(p.shape[1], int(x.max())+7)
    sl = np.s_[y0:y1, x0:x1]
    sub = {k:v[sl] for k,v in fold.items() if isinstance(v, np.ndarray) and v.shape==p.shape}
    return evaluate_holdout.evaluate(p[sl], sub, valid[sl], origin=(y0,x0), global_shape=p.shape)


def main():
    start = time.monotonic()
    manifest = E/'experiment_manifest.json'
    if manifest.exists():
        raise RuntimeError('Experiment already attempted. Inspect evidence; no silent reruns/tuning on these folds.')
    dump(manifest, {'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(), 'experiment_count':1,
                    'maximum_experiments':3, 'maximum_seconds':7200,
                    'preregistration_sha256':sha(ROOT/'docs/hypotheses.md'),
                    'source_sha256':{p:sha(ROOT/p) for p in ['src/gems70/method.py','scripts/run_experiment.py']}})
    def budget():
        if time.monotonic()-start > 7200:
            raise TimeoutError('two-hour experiment budget exhausted')
    for name, expected in PINS.items():
        if sha(DATA/name) != expected:
            raise ValueError('input pin mismatch: '+name)
    grid = load_grid(DATA)
    fp = grid.footprint
    raw = {}
    with rasterio.open(DATA/'training_features.tif') as src:
        if (src.shape, src.crs, src.transform)!=(grid.shape, grid.crs, grid.transform):
            raise ValueError('feature grid mismatch')
        dump(E/'feature_metadata.json', {'descriptions':list(src.descriptions),'nodata':src.nodata,
                                         'crs':str(src.crs),'shape':list(src.shape),
                                         'transform':list(src.transform)[:6]})
        for index, name in [(2,'rtp'),(13,'gravity'),(15,'basement')]:
            a = src.read(index).astype(np.float32)
            a[(a <= -1e30) | ~np.isfinite(a) | ~fp] = np.nan
            raw[name] = a
    valid = fp.copy()
    for a in raw.values(): valid &= np.isfinite(a)
    # Guard against filled-boundary artifacts: no output within the largest filter's truncation radius.
    valid = ndi.binary_erosion(valid, iterations=12)
    if not valid.any(): raise ValueError('no valid interior features')
    features = physical_features(raw['rtp'],raw['gravity'],raw['basement'], valid)
    folds, _ = holdout.buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=12)
    dump(E/'holdout_split.json', {'evidence_class':'HOLDOUT-DTI','evaluator_version':evaluate_holdout.VERSION,
        'receipts':[f['receipt'] for f in folds],
        'total_withheld_positive_pixels':int(sum((f['truth'] & valid).sum() for f in folds)),
        'catalogue_predictors':[], 'valid_feature_pixels':int(valid.sum()),
        'known_mask_rule':'catalogue minus globally withheld components, pixel exact; feature collar is not removed from evaluation',
        'limitation':'Mapped components are a surrogate for previously unmapped faults; no hidden organizer labels.'})
    # Canary positives and negatives are scored on exactly the evaluation domains.
    truth = np.zeros(fp.shape,bool)
    active = np.zeros(fp.shape,bool)
    for fold in folds:
        active |= valid & fold['region'] & ~fold['masked_known']
        truth |= valid & fold['truth']
    positives = np.flatnonzero(truth)
    negatives = np.flatnonzero(active & ~truth)
    rng = np.random.default_rng(70020)
    negatives = rng.choice(negatives, min(200000,len(negatives)), replace=False)
    labels = np.r_[np.ones(len(positives)),np.zeros(len(negatives))]
    canaries = {}
    for name, a in {**raw, **features}.items():
        values = np.r_[a.ravel()[positives],a.ravel()[negatives]]
        auc = float(roc_auc_score(labels,values))
        canaries[name] = {'evidence_class':'LEAKAGE-CANARY','auc':auc,'inverse_auc':1-auc,
                          'withheld_positive_pixels':len(positives),'negative_sample_pixels':len(negatives),
                          'suspected_leakage':bool(max(auc,1-auc) > .90)}
    dump(E/'canaries.json', canaries)
    if any(c['suspected_leakage'] for c in canaries.values()):
        raise RuntimeError('LEAKAGE CANARY STOP: feature-alone AUC > .90; no joint interpretation permitted')
    print('Feature-alone canaries complete.',flush=True)
    arms = {**{name:upper_surface(rank01(a,valid),valid) for name,a in {**raw, **features}.items()},
            'candidate':upper_surface(joint_field(features,valid),valid),
            'ablation_no_termination':upper_surface(joint_field(features,valid,('gravity_edge','basement_normal')),valid)}
    random = np.zeros(fp.shape,np.float32)
    # Fixed random sparse-control mass count, independent of fault labels.
    ids = rng.choice(np.flatnonzero(valid), int((arms['candidate']>0).sum()),replace=False)
    random.ravel()[ids] = .5
    arms['random_control'] = random
    terms = {}
    fold_results = {}
    for name, a in arms.items():
        budget()
        per_fold = [cropped(f, a, valid) for f in folds]
        terms[name] = sum(t for _,t in per_fold)
        fold_results[name] = [r for r,_ in per_fold]
        print(name, 'evaluated', flush=True)
    result = evaluate_holdout.pooled_summary(terms, draws=1000, seed=70020, candidate='candidate')
    result['interpretation'] = 'Continuous pre-placement surface HOLDOUT-DTI, not final dots, not organizer-confirmed.'
    result['current_holdout_best_comparable'] = None
    result['promotion_allowed'] = False
    result['promotion_blocker'] = 'No current-best implementation rerun on this identical split; controls are not a current-best certificate.'
    dump(E/'holdout.json', result)
    dump(E/'holdout_folds.json', fold_results)
    # Surface gate strictly precedes any placement or writer call.
    surface = arms['candidate'].copy()
    surface[grid.catalogue] = 0
    np.save(CACHE/'candidate_surface.npy', surface)
    witness = json.loads((ROOT/'registry/stop_witness.json').read_text())
    path = CACHE/'registry'/f"{witness['sha256']}.tif"
    repo, rel = witness['sources'][0].split(':',1)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open('wb') as out:
            subprocess.run(['gh','api',f"repos/buffedlizard55-lab/{repo}/git/blobs/{witness['blob']}",
                            '-H','Accept: application/vnd.github.raw'],stdout=out,check=True,timeout=300)
    if sha(path)!=witness['sha256']:
        raise ValueError('registry witness SHA mismatch')
    idx = {'complete_accessible_scan':False,
           'errors':['Early-stop witness scan only; not a complete updated registry inventory.'],
           'rasters':[{**witness,'cache_file':str(path)}]}
    audit = uniqueness.compare_array_to_registry(surface,idx,fp,include_reverse=False,
             expected_grid=(grid.shape,grid.crs,grid.transform))
    dump(E/'surface_uniqueness.json',audit)
    certificate = uniqueness.saturation_certificate(path,fp,grid.catalogue,
                      expected_grid=(grid.shape,grid.crs,grid.transform))
    dump(E/'registry_saturation.json',certificate)
    duplicate = any(r.get('duplicate_by_overlap') or r.get('duplicate_by_rho') for r in audit['rows'])
    checks = {'no_nan_inside_footprint':bool(np.isfinite(surface[fp]).all()),
              'all_values_finite':bool(np.isfinite(surface).all()),
              'values_in_0_1':bool((surface>=0).all() and (surface<=1).all()),
              'shape_matches':surface.shape==grid.shape,
              'zero_on_catalogue':not bool(surface[grid.catalogue].any()),
              'zero_outside_footprint':not bool(surface[~fp].any())}
    # No export occurs after a failed surface gate, even for a nominally valid field.
    card = {
      'hypothesis':'Magnetic-edge termination at a gravity-supported basement boundary',
      'mechanism':'Along-gravity-tangent change of magnetic edge amplitude, weighted by gravity edge and basement normal gradient',
      'non_fault_mimic':'Volcanic dike termination or intrusive lithologic contact',
      'hypothesis_status':'Provisional lane: method paragraph absent from supplied prompt',
      'verdict':'negative', 'stop_reason':'duplicate' if duplicate else 'incomplete registry and unavailable comparable current-best',
      'holdout_dti':{**result['scores']['candidate'], 'stage':'continuous pre-placement surface, not final dots',
                     'current_best_verified':False},
      'correlation_overlap_vs_registry':{
          'stage':'surface before final placement','rasters_checked':audit['registry_rasters_checked'],
          'registry_complete':False,'spearman':audit['worst_spearman_full_footprint'],
          'overlap_within_3px':audit['worst_dot_overlap'],
          'witness':witness['sources'][0], 'witness_sha256':witness['sha256'],
          'literal_duplicate':bool(duplicate),'final_dots':None,
          'final_dots_reason':'Not placed: literal surface stop rule.'},
      'raster_sha256':None,
      'raster_sha256_reason':'No submission TIFF written after surface gate stop.',
      'surface_decoded_float32_sha256':hashlib.sha256(np.ascontiguousarray(surface).tobytes()).hexdigest(),
      'validator_output':{'submission_tiff':None,'status':'NOT_WRITTEN',
          'pre_export_array_checks':checks,
          'crs_shape_transform_file_match':None,
          'reason':'Array checks are not a TIFF validator receipt; no output file exists.'},
      'submission_name':'gems70-contact-termination-e1-20261020-NOT-RELEASED',
      'submission_note':'Magnetic-edge termination on gravity/basement boundaries; negative surface gate; DO NOT SUBMIT.',
      'download_and_submit_ok':False, 'weekly_slots_used':0,
      'experiment_count':1,'elapsed_seconds':round(time.monotonic()-start,2),
      'organizer_confirmed_score':None,
      'evaluator_implementation_sha256':evaluate_holdout.implementation_hashes(),
      'method_source_sha256':{p:sha(ROOT/p) for p in ['src/gems70/method.py','scripts/run_experiment.py']},
    }
    dump(E/'run_card.json',card)
    print(json.dumps(card,indent=2),flush=True)

if __name__=='__main__': main()
