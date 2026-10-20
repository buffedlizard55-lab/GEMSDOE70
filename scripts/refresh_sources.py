"""Timestamp source availability without pretending HTTP health verifies scientific claims."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import datetime as dt
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def check(row):
    url=row.get('retrieved_via',row['url'])
    r=subprocess.run(['curl','-I','-L','--max-time','12','--silent','--show-error',
                      '--output','/dev/null','--write-out','%{http_code}',url],capture_output=True,text=True,timeout=18)
    return {'id':row['id'],'url':url,'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'http_status':r.stdout.strip(),'curl_exit':r.returncode,
            'reachable':r.returncode==0 and r.stdout.strip()=='200',
            'error':r.stderr.strip()[:300],
            'meaning':'HTTP availability only, not truth verification or organizer score confirmation.'}

def main():
    rows=json.loads((ROOT/'registry/sources.json').read_text())
    with ThreadPoolExecutor(max_workers=8) as ex: checks=list(ex.map(check,rows))
    out={'generated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'checks':checks,
         'live_leaderboard_verified':False,
         'network_scope':'This session permits GitHub/npm/PyPI hosts only; failures do not establish a source is globally unavailable.'}
    (ROOT/'evidence/source_health.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
