"""Restore cached input bytes, never previous predictions as a candidate."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '.cache/data'
FEAT_REF = 'c0c06ac82178f26b94fce3397036ef8f12a2f3a0'
AUX_REF = '32024716f218d06a94e01464157392119c03cb15'
PINS = {
 'training_features.tif': '4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5',
 'existing_faults.tif': '7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093',
 'sample_submission.tif': '2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc'}

def fetch(repo, ref, path, dest):
 dest.parent.mkdir(parents=True, exist_ok=True)
 if not dest.exists():
  temp = dest.with_suffix(dest.suffix + '.tmp')
  with temp.open('wb') as f:
   subprocess.run(['gh','api',f'repos/buffedlizard55-lab/{repo}/contents/{path}?ref={ref}', '-H','Accept: application/vnd.github.raw'], stdout=f, check=True, timeout=300)
  temp.replace(dest)
 return dest

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20), b''): h.update(b)
 return h.hexdigest()

def main():
 DATA.mkdir(parents=True, exist_ok=True)
 if not (DATA/'training_features.tif').exists():
  def part(i):
   p=f'gems-geodawn-numerical-features.tif.part-00{i}'
   return fetch('GEMSDOE',FEAT_REF,'data/bridge/'+p,DATA/p)
  with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex: parts=list(ex.map(part, range(5)))
  with (DATA/'training_features.tif').open('wb') as out:
   for p in parts:
    with p.open('rb') as f:
     for b in iter(lambda:f.read(1<<20), b''): out.write(b)
  for p in parts: p.unlink()
 for n, src in [('existing_faults.tif','data/bridge/existing_faults.tif'),('sample_submission.tif','data/sample_submission.tif')]:
  fetch('60GEMSDOE',AUX_REF,src,DATA/n)
 rows={n:{'sha256':sha(DATA/n),'expected':v,'ok':sha(DATA/n)==v} for n,v in PINS.items()}
 (ROOT/'evidence/data_receipt.json').write_text(json.dumps({'evidence_class':'DATA-MEASUREMENT','provenance':'Public owner mirrors; hash consistency is not organizer authentication','feature_ref':FEAT_REF,'aux_ref':AUX_REF,'files':rows},indent=2)+'\n')
 if not all(r['ok'] for r in rows.values()): raise ValueError('input SHA256 mismatch; remove corrupt cache and restore')
 print(json.dumps(rows,indent=2), flush=True)
if __name__=='__main__': main()
