#!/usr/bin/env python3
"""v27 fixed robustness: FULL_C01 vs NOLOCAL_C01, venue LOO and threshold-edge."""
import json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_player_waku_soft_ablation_v23 as v23
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv");TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv");OUT=Path("/tmp/head4_ph4_robustness_v27");OUT.mkdir(exist_ok=True)
PH4=['b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_win','b4_pl_frame_p2','b4_pl_recent_p2'];CUT=.36;DEV={"2026-03","2026-04","2026-05"}
def mdl():return Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.1))])
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6];z['venue']=z.race_code.str[4:6]
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12);z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 old=[c for c in z if '_pl_' in c]
 if old:z=z.drop(columns=old)
 z=z.merge(v23.build_ph(),on='race_code',how='left',validate='one_to_one')
 forb=("actual","result","payout","odds","finish","着順","1着","2着","3着");num=[c for c in z if c not in {'head4','race_code','month','venue'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forb)]
 base=[c for c in num if '_pl_' not in c and not c.startswith('w10_') and not c.startswith('opp_waku_b')];spec={'FULL_C01':base+PH4,'NOLOCAL_C01':[c for c in base if 'local_' not in c.lower()]+PH4}
 tr=z[z.month.isin(DEV)].copy();ev=z[z.month.isin({'2026-06','2026-07','2026-08'})].copy()
 for n,f in spec.items():m=mdl();m.fit(tr[f],tr.head4);ev[n]=m.predict_proba(ev[f])[:,1]
 rows=[]
 for n in spec:
  s=ev[ev[n]>=CUT];rows.append({'model':n,'slice':'ALL','key':'ALL','R':len(s),'head4':int(s.head4.sum()),'rate':float(s.head4.mean())})
  for v in sorted(ev.venue.unique()):
   q=ev[(ev.venue!=v)&(ev[n]>=CUT)];rows.append({'model':n,'slice':'LEAVE_VENUE_OUT','key':v,'R':len(q),'head4':int(q.head4.sum()),'rate':float(q.head4.mean())})
  # fixed score bands around .36, diagnostic only
  for lo,hi in [(.30,.34),(.34,.35),(.35,.36),(.36,.37),(.37,.38),(.38,.40),(.40,.45),(.45,1.01)]:
   q=ev[(ev[n]>=lo)&(ev[n]<hi)];rows.append({'model':n,'slice':'SCORE_BAND','key':f'{lo:.2f}-{hi:.2f}','R':len(q),'head4':int(q.head4.sum()),'rate':float(q.head4.mean()) if len(q) else None})
 pd.DataFrame(rows).to_csv(OUT/'robustness.csv',index=False)
 # score/rank sensitivity between models
 q=ev[['race_code','month','venue','head4','FULL_C01','NOLOCAL_C01']].copy();q['delta']=q.NOLOCAL_C01-q.FULL_C01;q['full_sel']=q.FULL_C01>=CUT;q['nolocal_sel']=q.NOLOCAL_C01>=CUT;q.to_csv(OUT/'race_scores.csv',index=False)
 flips=q[q.full_sel!=q.nolocal_sel];print(pd.DataFrame(rows).to_string(index=False));print("FLIPS",len(flips),int(flips.head4.sum()),float(flips.head4.mean()) if len(flips) else None);print(flips[['month','venue','head4','FULL_C01','NOLOCAL_C01','delta','full_sel','nolocal_sel']].to_string(index=False))
 meta={'fixed_models':['FULL_C01','NOLOCAL_C01'],'C':.1,'cut':CUT,'fit':'Mar-May','evaluation':'Jun-Aug diagnostics only','retuning':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False};(OUT/'meta.json').write_text(json.dumps(meta,indent=2)+"\n");print(json.dumps(meta));print("HEAD4_PH4_ROBUSTNESS_V27_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
