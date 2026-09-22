#!/usr/bin/env python3
"""v26 attribution audit: opponent-local removal vs regularization. Fixed cut .36."""
import json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_player_waku_soft_ablation_v23 as v23
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv");TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv")
OUT=Path("/tmp/head4_ph4_local_reg_v26");OUT.mkdir(exist_ok=True)
PH4=['b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_win','b4_pl_frame_p2','b4_pl_recent_p2'];DEV={"2026-03","2026-04","2026-05"};CUT=.36
SPECS={'FULL_C05':(.5,False),'FULL_C01':(.1,False),'NOLOCAL_C05':(.5,True),'NOLOCAL_C01':(.1,True)}
def model(C):return Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=C))])
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12);z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 old=[c for c in z if '_pl_' in c]
 if old:z=z.drop(columns=old)
 z=z.merge(v23.build_ph(),on='race_code',how='left',validate='one_to_one')
 forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
 num=[c for c in z if c not in {'head4','race_code','month'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forbidden)]
 base=[c for c in num if '_pl_' not in c and not c.startswith('w10_') and not c.startswith('opp_waku_b')]
 tr=z[z.month.isin(DEV)].copy();ev=z[z.month.isin({'2026-06','2026-07','2026-08'})].copy();meta={};rows=[]
 for name,(C,nolocal) in SPECS.items():
  feats=[c for c in base if not(nolocal and 'local_' in c.lower())]+PH4;p=model(C);p.fit(tr[feats],tr.head4);ev[name]=p.predict_proba(ev[feats])[:,1];meta[name]={'C':C,'cut':CUT,'features':len(feats),'removed':sorted(set(base+PH4)-set(feats))}
  for mo in ['2026-06','2026-07','2026-08']:
   s=ev[(ev.month==mo)&(ev[name]>=CUT)];rows.append({'model':name,'month':mo,'R':len(s),'head4':int(s.head4.sum()),'rate':float(s.head4.mean())})
 pd.DataFrame(rows).to_csv(OUT/'monthly.csv',index=False)
 # exact 2x2 attribution on identical eval universe
 sels={n:set(ev.loc[ev[n]>=CUT,'race_code']) for n in SPECS};pairs=[]
 for a,b,label in [('FULL_C05','FULL_C01','REG_ONLY'),('FULL_C05','NOLOCAL_C05','LOCAL_ONLY'),('FULL_C05','NOLOCAL_C01','BOTH'),('FULL_C01','NOLOCAL_C01','LOCAL_AT_C01'),('NOLOCAL_C05','NOLOCAL_C01','REG_AT_NOLOCAL')]:
  for mo in ['ALL','2026-06','2026-07','2026-08']:
   q=ev if mo=='ALL' else ev[ev.month.eq(mo)];univ=set(q.race_code);A=sels[a]&univ;B=sels[b]&univ
   for kind,codes in [('overlap',A&B),('a_only',A-B),('b_only',B-A)]:
    y=q.set_index('race_code').loc[list(codes),'head4'] if codes else pd.Series(dtype=float);pairs.append({'contrast':label,'period':mo,'kind':kind,'R':len(y),'head4':int(y.sum()),'rate':float(y.mean()) if len(y) else None})
 pd.DataFrame(pairs).to_csv(OUT/'paired.csv',index=False)
 m={'specs':meta,'fit':'Mar-May only','evaluation':'Jun-Aug fixed; no selection/tuning','holdout_used_for_selection':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False}
 (OUT/'meta.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n");print(pd.DataFrame(rows).to_string(index=False));print(pd.DataFrame(pairs).to_string(index=False));print(json.dumps(m,ensure_ascii=False));print("HEAD4_PH4_LOCAL_REG_V26_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
