"""Forensic measurement of archived files; never used as candidate predictions."""
from pathlib import Path
import sys
import json
import hashlib
import subprocess
import numpy as np
import rasterio
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from gems57.grid import load_grid
REF='32024716f218d06a94e01464157392119c03cb15'
FILES={
 'h33':'registry/rasters/GEMSDOE32__h33-2-b2-zeros.tif',
 'h27':'registry/rasters/GEMSDOE28__h27-4-r1-solo-d2-8.tif',
 'd28':'registry/rasters/GEMSDOE25__dotted-h19-5-d2-8.tif'}
def main():
 grid=load_grid(ROOT/'.cache/data')
 dist=ndi.distance_transform_edt(~grid.catalogue)
 arrays={}; rows={}
 for name,rel in FILES.items():
  p=ROOT/'.cache/audit'/f'{name}.tif'
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():
   with p.open('wb') as out:
    subprocess.run(['gh','api',f'repos/buffedlizard55-lab/60GEMSDOE/contents/{rel}?ref={REF}',
                    '-H','Accept: application/vnd.github.raw'],check=True,stdout=out)
  with rasterio.open(p) as src:
   assert (src.shape,src.crs,src.transform)==(grid.shape,grid.crs,grid.transform)
   a=src.read(1)
   support=np.isfinite(a)&(a>0)&grid.footprint
  arrays[name]=support
  rows[name]={'evidence_class':'DATA-MEASUREMENT','source':f'https://github.com/buffedlizard55-lab/60GEMSDOE/blob/{REF}/{rel}',
      'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'positive_pixels':int(support.sum()),
      'on_catalogue':int((support&grid.catalogue).sum()),'min_catalogue_distance_px':float(dist[support].min()),
      'median_catalogue_distance_m':float(np.median(dist[support])*100),
      'within_300m_fraction':float((dist[support]<=3).mean()),
      'finite_values':np.unique(a[np.isfinite(a)]).tolist()}
 comparisons={}
 for old,new in [('d28','h27'),('h27','h33')]:
  removed=arrays[old]&~arrays[new]; added=arrays[new]&~arrays[old]
  comparisons[f'{old}_to_{new}']={'removed':int(removed.sum()),'added':int(added.sum()),
      'removed_catalogue_distances_px':np.unique(dist[removed]).tolist(),
      'exactly_old_with_distance_gt_2':bool(np.array_equal(arrays[new],arrays[old]&(dist>2)))}
 assert rows['h33']['sha256']=='c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9'
 (ROOT/'evidence/h33_audit.json').write_text(json.dumps({'evidence_class':'DATA-MEASUREMENT','files':rows,
       'comparisons':comparisons,'organizer_confirmed_scores':None,
       'score_caveat':'User/family reported scores have no authenticated submission-page receipt in this audit.'},indent=2)+'\n')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
