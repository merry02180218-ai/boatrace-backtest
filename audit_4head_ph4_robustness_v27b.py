#!/usr/bin/env python3
"""v27b corrected venue robustness. Race code YYYYMMDDJJRR => venue JJ at [8:10]."""
import json
from pathlib import Path
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_player_waku_soft_ablation_v23 as v23
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv");TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv");OUT=Path("/tmp/head4_ph4_robustness_v27b");OUT.mkdir(exist_ok=True)
PH4=['b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_win','b4_pl_frame_p2','b4_pl_recent_p2'];CUT=.36;DEV={"2026-03","2026-04","2026-05"}
def mdl():return Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.1))])
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6];z['venue']=z.race_code.str[8:10]
 assert z.venue.nunique()>=20,(z.venue.nunique(),sorted(z.venue.unique()))
 assert z.venue.str.fullmatch(r'(0[1-9]|1[0-9]|2[0-4])').all(),sorted(z.venue.unique())
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12);z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 old=[c for c in z if '_pl_' in c]
 if old:z=z.drop(columns=old)
 z=z.merge(v23.build_ph(),on='race_code',how='left',validate='one_to_one')
 forb=("actual","result","payout","odds","finish","着順","1着","2着","3着");num=[c for c in z if c not in {'head4','race_code','month','venue'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forb)]
 base=[c for c in num if '_pl_' not in c and not c.startswith('w10_') and not c.startswith('opp_waku_b')];spec={'FULL_C01':base+PH4,'NOLOCAL_C01':[c for c in base if 'local_' not in c.lower()]+PH4}
 tr=z[z.month.isin(DEV)].copy();ev=z[z.month.isin({'2026-06','2026-07','2026-08'})].copy();rows=[]
 for n,f in spec.items():
  m=mdl();m.fit(tr[f],tr.head4);ev[n]=m.predict_proba(ev[f])[:,1];s=ev[ev[n]>=CUT];rows.append({'model':n,'left_out':'NONE','R':len(s),'head4':int(s.head4.sum()),'rate':float(s.head4.mean())})
  for v in sorted(ev.venue.unique()):
   q=ev[(ev.venue!=v)&(ev[n]>=CUT)];rows.append({'model':n,'left_out':v,'R':len(q),'head4':int(q.head4.sum()),'rate':float(q.head4.mean())})
 out=pd.DataFrame(rows);out.to_csv(OUT/'venue_loo.csv',index=False)
 # per-venue selected diagnostics, to reveal concentration
 pv=[]
 for n in spec:
  for v,q in ev[ev[n]>=CUT].groupby('venue'):pv.append({'model':n,'venue':v,'R':len(q),'head4':int(q.head4.sum()),'rate':float(q.head4.mean())})
 pd.DataFrame(pv).to_csv(OUT/'venue_selected.csv',index=False)
 meta={'race_code_schema':'YYYYMMDDJJRR','venue_slice':'[8:10]','venue_count':int(ev.venue.nunique()),'fixed_models':['FULL_C01','NOLOCAL_C01'],'C':.1,'cut':CUT,'fit':'Mar-May','evaluation':'Jun-Aug only','retuning':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False}
 (OUT/'meta.json').write_text(json.dumps(meta,indent=2)+"\n");print(out.to_string(index=False));print(pd.DataFrame(pv).to_string(index=False));print(json.dumps(meta));print("HEAD4_PH4_ROBUSTNESS_V27B_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
