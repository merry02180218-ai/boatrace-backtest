#!/usr/bin/env python3
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

SRC='analysis_v351_schema_correct_rebuild.csv'
OUT='analysis_v351_schema_calibration.csv'
SUM='analysis_v351_schema_calibration_summary.csv'

def calibrate(g):
    g=g.sort_values('race_code').copy(); g['corrected_p']=np.nan
    scored=g[g.schema_p.notna()].copy()
    for i,row in scored.iterrows():
        tr=scored[scored.race_code < row.race_code]
        # calibration must itself be chronological; use only earlier OOF predictions.
        if len(tr)<5 or tr.head_hit.nunique()<2: continue
        x=tr[['schema_p']].values; y=tr.head_hit.astype(int).values
        m=LogisticRegression(C=1.0,max_iter=2000).fit(x,y)
        g.loc[i,'corrected_p']=m.predict_proba([[row.schema_p]])[0,1]
    return g

def main():
    d=pd.read_csv(SRC,dtype={'race_code':str}); d.race_code=d.race_code.str.zfill(12)
    parts=[]
    for schema,g in d.groupby('schema',dropna=False): parts.append(calibrate(g))
    z=pd.concat(parts).sort_values('race_code')
    rows=[]
    for schema,g in z.groupby('schema',dropna=False):
        ready=g[g.schema_ready.eq(1)]; raw=ready[ready.schema_p.notna()]; cal=ready[ready.corrected_p.notna()]
        pick=cal[cal.corrected_p>=.78]
        rows.append({'schema':schema,'ready':len(ready),'raw_oof':len(raw),'cal_oof':len(cal),'cut078_r':len(pick),'head':int(pick.head_hit.sum()),'head_rate':100*pick.head_hit.mean() if len(pick) else np.nan,'exact3':int(pick.hit.sum()),'exact3_rate':100*pick.hit.mean() if len(pick) else np.nan})
        print('SCHEMA',schema,'READY',len(ready),'RAW_OOF',len(raw),'CAL_OOF',len(cal),'CUT078_R',len(pick),'HEAD',int(pick.head_hit.sum()),'HEAD_RATE',100*pick.head_hit.mean() if len(pick) else np.nan,'EXACT3',int(pick.hit.sum()),'EXACT3_RATE',100*pick.hit.mean() if len(pick) else np.nan)
    z.to_csv(OUT,index=False,encoding='utf-8-sig'); pd.DataFrame(rows).to_csv(SUM,index=False,encoding='utf-8-sig')
if __name__=='__main__': main()
