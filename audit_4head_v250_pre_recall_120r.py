#!/usr/bin/env python3
"""HEAD4 frozen120 vs result-blind v250 PRE score recall audit.

The v250 PRE model explicitly excludes current-race exhibition features and runs
monthly walk-forward. This audit rebuilds v250 through 2026-08, then AFTER
prediction generation compares PRE thresholds with the already-frozen 120R
post-exhibition membership.

No September outcomes/results. Production unchanged.
Apr-Aug recall tuning is NON-PRISTINE research evidence.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
import analyze_v250_4head_rebuild_baseline as v250

ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/head4_v250_pre_recall120'); OUT.mkdir(parents=True,exist_ok=True)
MEM=ROOT/'artifacts'/'head4_120r_membership_codes_20260918.txt'
EXPECTED='37057b43e344309e3fd06dfa1f2b519cfaad16379e92bfda51166da42834844c'
CUTS=[round(x,3) for x in np.arange(.10,.401,.005)]
MONTHS=['2026-04','2026-05','2026-06','2026-07','2026-08']

def load_membership():
    codes=[x.strip() for x in MEM.read_text().splitlines() if x.strip()]
    h=hashlib.sha256(('\n'.join(sorted(codes))+'\n').encode()).hexdigest()
    if len(codes)!=120 or h!=EXPECTED: raise RuntimeError(f'membership drift {len(codes)} {h}')
    return set(codes)

def main():
    final=load_membership()
    # Rebuild monthly walk-forward PRE scores. Features are frozen before same-day result join.
    v250.main()
    z=pd.read_csv(v250.OUT,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    z=z[(z.variant=='PRE') & z.month.isin(MONTHS)].copy()
    if z.empty or z.race_code.duplicated().any(): raise RuntimeError('invalid PRE predictions')
    if any(z.month.astype(str).ge('2026-09')): raise RuntimeError('September access blocked')
    if not final.issubset(set(z.race_code)):
        miss=sorted(final-set(z.race_code))
        raise RuntimeError(f'final120 absent from PRE universe: {miss[:10]}')

    # Persist per-race PRE scores for downstream pre-candidate combination audits.
    z[['date','month','race_code','p4head','y4head']].rename(columns={'p4head':'v250_PRE'}).to_csv(OUT/'pre_scores_all.csv',index=False)
    z[z.race_code.isin(final)][['date','month','race_code','p4head','y4head']].rename(columns={'p4head':'v250_PRE'}).to_csv(OUT/'pre_scores_final120.csv',index=False)

    rows=[]
    for cut in CUTS:
        m=z.p4head.ge(cut)
        codes=set(z.loc[m,'race_code'])
        got=len(codes&final)
        q=z[m]; daily=q.groupby('date').size()
        rows.append({
          'PRE_min':cut,'candidate_R':int(m.sum()),'final120_captured':got,
          'final120_missed':120-got,'recall_pct':100*got/120,
          'avg_per_calendar_day':float(m.sum()/153.0),
          'avg_per_active_day':float(daily.mean()) if len(daily) else 0.0,
          'p90_per_active_day':float(daily.quantile(.90)) if len(daily) else 0.0,
          'max_per_day':int(daily.max()) if len(daily) else 0,
        })
    g=pd.DataFrame(rows)
    g.to_csv(OUT/'pre_threshold_recall.csv',index=False)

    picks=[]
    for target in (100,95,90):
        q=g[g.recall_pct.ge(target)]
        if len(q):
            b=q.sort_values(['candidate_R','PRE_min'],ascending=[True,False]).iloc[0].to_dict()
            b['target_recall_pct']=target;picks.append(b)
    fixed=g[np.isclose(g.PRE_min,.28)].iloc[0].to_dict()
    picksdf=pd.DataFrame(picks); picksdf.to_csv(OUT/'recommended_recall_tiers.csv',index=False)

    # Month recall for selected tiers + fixed .28
    check=[('FIXED_PRE_028',.28)]+[(f'RECALL_{int(x["target_recall_pct"])}',float(x['PRE_min'])) for x in picks]
    mr=[]
    for name,cut in check:
        cc=set(z.loc[z.p4head.ge(cut),'race_code'])
        for mo in MONTHS:
            fm={x for x in final if x.startswith(mo.replace('-',''))}
            got=len(fm&cc)
            mr.append({'tier':name,'PRE_min':cut,'month':mo,'final_R':len(fm),'captured':got,'recall_pct':100*got/len(fm)})
    pd.DataFrame(mr).to_csv(OUT/'monthly_recall.csv',index=False)

    summary={
      'status':'HEAD4_V250_PRE_RECALL120_OK',
      'fixed_PRE_028':fixed,
      'recall_tiers':picks,
      'PRE_feature_semantics':'current-race exhibition excluded; v250 monthly walk-forward',
      'selection_status':'Apr-Aug NON_PRISTINE recall tuning',
      'september_2026':'UNREAD','production_changed':False,
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=float)+'\n')
    print('HEAD4_V250_PRE_RECALL120_OK')
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=float))
    print('9月_UNREAD');print('本番変更なし')
if __name__=='__main__':main()
