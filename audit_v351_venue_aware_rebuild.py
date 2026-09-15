#!/usr/bin/env python3
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import run_v326_1head_ticketaware_exhibition as v326

FEATURE_GROUPS={
 'base':['one_ex','one_st','sec_ex_mean_margin','sec_st_mean_margin'],
 'turn':['one_turn','sec_turn_mean_margin','third_turn_mean_margin','covered_turn_weak_margin','uncovered_turn_dominance'],
 'straight':['one_straight','sec_straight_mean_margin','third_straight_mean_margin','covered_straight_weak_margin','uncovered_straight_dominance'],
 'avg':['one_orig_avg','third_orig_mean_margin'],
 'balance':['covered_balance_min'],
}

def metrics(g):
 n=len(g); h=int(g.head_hit.sum()) if n else 0; hit=int(g.hit.sum()) if n else 0
 return {'R':n,'head_H':h,'head_rate':100*h/n if n else np.nan,'exact3_H':hit,'exact3_rate':100*hit/n if n else np.nan}

def main():
 y=v326.build_dataset().copy(); y['jcd']=y.race_code.astype(str).str.zfill(12).str[8:10].astype(int)
 # A race is usable when the common exhibition pair exists; optional original-exhibition groups are selected only when present.
 y['venue_ready']=(y.tkz_all6.eq(1)&y.stt_all6.eq(1)).astype(int)
 rows=[]
 for jcd,g in y.groupby('jcd'):
  feats=list(FEATURE_GROUPS['base'])
  for flag,grp in [('orig_turn_all6','turn'),('orig_straight_all6','straight'),('orig_avg_all6','avg'),('orig_turn_straight_all6','balance')]:
   if g[flag].mean()>=0.80: feats+=FEATURE_GROUPS[grp]
  ready=g[g.venue_ready.eq(1)&g[feats].notna().all(axis=1)].copy()
  r={'jcd':jcd,'features':';'.join(feats),**metrics(g)}
  r.update({f'ready_{k}':v for k,v in metrics(ready).items()}); rows.append(r)
 out=pd.DataFrame(rows); out.to_csv('analysis_v351_venue_aware_coverage.csv',index=False)
 print(out.to_string(index=False)); print('TOTAL',len(y),'VENUE_READY',int(y.venue_ready.sum()))
 # Leakage-safe chronological evaluation: each race is scored only from earlier races of the same venue-feature schema.
 y=y.sort_values('race_code').copy(); y['venue_aware_p']=np.nan
 for jcd,g in y.groupby('jcd'):
  spec=out.loc[out.jcd.eq(jcd),'features'].iloc[0].split(';'); idx=list(g.index)
  for pos,i in enumerate(idx):
   if not y.loc[i,'venue_ready'] or y.loc[i,spec].isna().any(): continue
   train=y.loc[idx[:pos]]; train=train[train.venue_ready.eq(1)&train[spec].notna().all(axis=1)]
   if len(train)<12 or train.head_hit.nunique()<2: continue
   m=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=2000))])
   m.fit(train[spec],train.head_hit); y.loc[i,'venue_aware_p']=m.predict_proba(y.loc[[i],spec])[:,1][0]
 scored=y[y.venue_aware_p.notna()].copy()
 print('CHRONO_SCORED',metrics(scored))
 for cut in [.70,.75,.78,.80,.82,.85]:
  p=scored[scored.venue_aware_p>=cut]; print('CUT',cut,metrics(p))
 y.to_csv('analysis_v351_venue_aware_scored.csv',index=False)
if __name__=='__main__': main()
