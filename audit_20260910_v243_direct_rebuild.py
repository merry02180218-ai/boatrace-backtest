#!/usr/bin/env python3
"""Re-run canonical v243 with the same input topology it used originally.

Key point: canonical v243 did NOT download the v233 recovered-Waku10 artifact.
For Waku10 days missing from BoatraceCSV it therefore queried Boatcast directly.
This audit reproduces that topology, but parallelizes day reconstruction so the
software-equivalence diagnosis finishes much faster.

No thresholds/features are changed. Jul/Aug remain NON-PRISTINE.
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path

import pandas as pd

import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v243_3head_expand_feature_audit as v243

REF=os.environ.get('BOATRACECSV_REF','f4552b6a02b5cf3eb78e85eb650f4a1b1a4cd39b')
GOLD=Path(os.environ.get('V243_GOLD','golden_v243/analysis_v243_3head_expand_feature_audit.csv'))
OUT=Path('audit_20260910_v243_direct_rebuild.json')

# v234 historically hard-coded /main/ for published Waku10. For a reproducible
# historical audit, point that family at the exact same BoatraceCSV snapshot as
# backtest.rows(). LIVE keeps using main when BOATRACECSV_REF is absent.
v234.PUB=f'https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/{REF}/data/programs/waku10/'


def direct_parallel_reconstruct():
    """Exact v234 reconstruction semantics, but no v233 fallback and parallel by day."""
    v234.REST.mkdir(parents=True,exist_ok=True)
    days=[]; d=v234.START
    while d<=v234.END:
        days.append(d); d+=timedelta(days=1)

    def published(day):
        rel=f'{day:%Y/%m/%d}.csv'
        return day,v234.get(v234.PUB+rel,5)

    pubs={}
    with ThreadPoolExecutor(max_workers=24) as ex:
        futs=[ex.submit(published,d) for d in days]
        for n,f in enumerate(as_completed(futs),1):
            day,b=f.result(); pubs[day]=b
            if n%50==0: print('published probe',n,'/',len(days),flush=True)

    missing=[d for d in days if not pubs.get(d)]
    print('DIRECT_TOPOLOGY published_days=',len(days)-len(missing),'boatcast_days=',len(missing),flush=True)

    direct={}
    # Each fetch_all_day already uses 32 race-request workers. Keep only four
    # concurrent days to avoid changing semantics while cutting wall-clock time.
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs={ex.submit(v234.fetch_all_day,d):d for d in missing}
        for n,f in enumerate(as_completed(futs),1):
            day=futs[f]; direct[day]=f.result()
            if n%20==0: print('direct boatcast days',n,'/',len(missing),flush=True)

    coverage=[]
    for day in days:
        rel=f'{day:%Y/%m/%d}.csv'; dest=v234.REST/rel
        pub=pubs.get(day,b'')
        if pub:
            dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(pub)
            n=max(0,len(pub.decode('utf-8-sig',errors='ignore').splitlines())-1)
            coverage.append({'date':str(day),'source':'published','rows':n,'raw_files':0})
            continue
        raws=direct.get(day,[]); rs=[]
        for jo,rr,src,b in raws:
            r=v234.parse_raw(b,day,jo,rr)
            if r: rs.append(r)
        if rs: v234.write_rows(dest,rs)
        coverage.append({'date':str(day),'source':'direct_boatcast' if rs else 'missing','rows':len(rs),'raw_files':len(raws)})
    q=pd.DataFrame(coverage); q.to_csv(v234.COV,index=False)
    return q


def norm_code(s): return s.astype(str).str.replace(r'\.0$','',regex=True).str.zfill(12)


def compare_generated_to_gold():
    generated=Path('analysis_v243_3head_expand_feature_audit.csv')
    if not generated.exists(): raise RuntimeError('v243 output missing')
    if not GOLD.exists(): raise RuntimeError(f'golden artifact missing: {GOLD}')
    a=pd.read_csv(generated,dtype={'race_code':str}); g=pd.read_csv(GOLD,dtype={'race_code':str})
    a['race_code']=norm_code(a['race_code']); g['race_code']=norm_code(g['race_code'])
    aa=a.set_index('race_code'); gg=g.set_index('race_code'); common=aa.index.intersection(gg.index)
    p3a=pd.to_numeric(aa.loc[common,'p3'],errors='coerce'); p3g=pd.to_numeric(gg.loc[common,'p3'],errors='coerce')
    p3diff=float((p3a-p3g).abs().max()) if len(common) else None
    result={
      'boatracecsv_ref':REF,
      'generated_rows':len(a),'golden_rows':len(g),'common_races':len(common),
      'race_set_match':set(aa.index)==set(gg.index),'p3_max_abs_diff':p3diff,
    }
    for c in ['bet','raw_top_n','raw_comp_odds','top_n','comp_odds','trifecta_hit','ret','profit']:
        if c in aa.columns and c in gg.columns:
            x=aa.loc[common,c]; y=gg.loc[common,c]
            nx=pd.to_numeric(x,errors='coerce'); ny=pd.to_numeric(y,errors='coerce')
            both_num=nx.notna()|ny.notna()
            eq=pd.Series(True,index=common)
            eq.loc[both_num]=(nx.loc[both_num]-ny.loc[both_num]).abs().fillna(float('inf'))<=1e-10
            eq.loc[~both_num]=x.loc[~both_num].astype(str).values==y.loc[~both_num].astype(str).values
            result[c+'_mismatch']=int((~eq).sum())
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DIRECT_REBUILD_AUDIT',json.dumps(result,ensure_ascii=False),flush=True)
    return result


def main():
    # Force the exact canonical v243 topology: there is no /tmp/v233 artifact.
    v234.V233=Path('/tmp/NO_V233_FOR_CANONICAL_V243')
    v234.reconstruct=direct_parallel_reconstruct
    # v243 imports v242.v234; same module object, but assign defensively.
    v243.v242.v234.PUB=v234.PUB
    v243.v242.v234.V233=v234.V233
    v243.v242.v234.reconstruct=direct_parallel_reconstruct
    v243.main()
    compare_generated_to_gold()

if __name__=='__main__': main()
