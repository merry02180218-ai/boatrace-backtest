"""4-head opponent research: race-development regime classification.
Research only. Frozen PH5 production population. June development, Jul-Aug holdout.
September outcomes remain unread. No production mutation.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_4head_opponent_second_rerank_v2 as base

OUT=Path('/tmp/head4_opponent_regime_v1'); OUT.mkdir(parents=True,exist_ok=True)

def classify_truth(s,t):
    inner={1,2,3}
    if s in inner and t in inner: return 'INNER_REMAIN'
    if s==5 or t==5: return 'FIVE_FOLLOW'
    if s==6 or t==6: return 'SIX_RISE'
    return 'MIXED'

def race_features(g):
    inn=g[g.boat.isin([1,2,3])]; out=g[g.boat.isin([5,6])]
    def med(q,c):
        x=pd.to_numeric(q[c],errors='coerce')
        return float(x.median()) if x.notna().any() else np.nan
    def mx(q,c):
        x=pd.to_numeric(q[c],errors='coerce')
        return float(x.max()) if x.notna().any() else np.nan
    r=g.iloc[0]
    rec={'race_code':r.race_code,'month':r.month,'actual_second':int(r.actual_second),'actual_third':int(r.actual_third)}
    for c in ['pl_frame_p2','pl_recent_p2','w10_wr','w10_st','w10_sr','w10_rel4_wr','w10_rel4_st','w10_rel4_sr']:
        rec['inner_'+c]=med(inn,c); rec['outer_'+c]=med(out,c); rec['gap_'+c]=rec['inner_'+c]-rec['outer_'+c]
    for b in (1,2,3,5,6):
        q=g[g.boat.eq(b)]
        for c in ['p2','pl_frame_p2','pl_recent_p2','w10_wr','w10_st','w10_sr','w10_rel4_wr']:
            rec[f'b{b}_{c}']=med(q,c)
    rec['inner_p2_max']=mx(inn,'p2'); rec['outer_p2_max']=mx(out,'p2')
    rec['truth_regime']=classify_truth(rec['actual_second'],rec['actual_third'])
    return rec

def main():
    z=base.build_long()
    races=pd.DataFrame([race_features(g) for _,g in z.groupby('race_code',sort=False)])
    if len(races)!=81: raise RuntimeError(f'HEAD4_POPULATION_DRIFT {len(races)} != 81')
    dev=races[races.month.eq('2026-06')].copy()
    hold=races[races.month.isin(['2026-07','2026-08'])].copy()
    if len(dev)!=24 or len(hold)!=57: raise RuntimeError('MONTH_SPLIT_DRIFT')
    # First pass is intentionally descriptive: establish whether stable regimes exist
    # before fitting a classifier or changing tickets.
    summary=(races.groupby(['month','truth_regime']).size().rename('R').reset_index())
    pct=summary.copy(); pct['pct']=pct.R/pct.groupby('month').R.transform('sum')*100
    pair=(races.assign(pair=races.actual_second.astype(str)+'-'+races.actual_third.astype(str))
          .groupby(['month','pair']).size().rename('R').reset_index()
          .sort_values(['month','R'],ascending=[True,False]))
    races.to_csv(OUT/'race_regime_features.csv',index=False)
    pct.to_csv(OUT/'regime_monthly.csv',index=False)
    pair.to_csv(OUT/'pair_monthly.csv',index=False)
    meta={'head4_R':len(races),'dev':'2026-06 only','holdout':['2026-07','2026-08'],
          'dev_R':len(dev),'holdout_R':len(hold),'SEPTEMBER_OUTCOMES_READ':False,
          'PH5_HEAD_MODEL_CHANGED':False,'PRODUCTION_CHANGED':False,
          'stage':'DESCRIPTIVE_REGIME_DISCOVERY_ONLY'}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print('REGIME_MONTHLY',pct.to_json(orient='records',force_ascii=False))
    print('PAIR_TOP',pair.groupby('month').head(8).to_json(orient='records',force_ascii=False))
    print(json.dumps(meta,ensure_ascii=False))
    print('HEAD4_OPPONENT_REGIME_V1_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__': main()
