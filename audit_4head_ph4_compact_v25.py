#!/usr/bin/env python3
"""v25 fixed falsification of v24 candidates. No threshold/family tuning."""
import json,os
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_player_waku_soft_ablation_v23 as v23
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv");TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv")
OUT=Path("/tmp/head4_ph4_compact_v25");OUT.mkdir(exist_ok=True)
PH4=['b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_win','b4_pl_frame_p2','b4_pl_recent_p2']
DEV={"2026-03","2026-04","2026-05"}
FIXED={'FULL_C05':{'C':.5,'cut':.36,'drop':()},'COMPACT_C01':{'C':.1,'cut':.36,'drop':('local_','boat_','top3')},'DROP_MOTOR_C025':{'C':.25,'cut':.36,'drop':('motor_',)}}
def pipe(C):
 return Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=C))])
def ci_boot(y,n=10000,seed=2501):
 if len(y)==0:return [None,None]
 r=np.random.default_rng(seed);a=np.asarray(y,float);m=r.choice(a,(n,len(a)),replace=True).mean(1);return [float(np.quantile(m,.025)),float(np.quantile(m,.975))]
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12)
 z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 ph=[c for c in z if '_pl_' in c]
 if ph:z=z.drop(columns=ph)
 z=z.merge(v23.build_ph(),on='race_code',how='left',validate='one_to_one')
 forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
 num=[c for c in z if c not in {'head4','race_code','month'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forbidden)]
 base=[c for c in num if '_pl_' not in c and not c.startswith('w10_') and not c.startswith('opp_waku_b')]
 tr=z[z.month.isin(DEV)].copy();ev=z[z.month.isin({'2026-06','2026-07','2026-08'})].copy()
 models={}
 for name,cfg in FIXED.items():
  feats=[c for c in base if not any(x in c.lower() for x in cfg['drop'])]+PH4
  p=pipe(cfg['C']);p.fit(tr[feats],tr.head4);ev[name]=p.predict_proba(ev[feats])[:,1];models[name]={'features':feats,**cfg}
 rec=[]
 for name,cfg in FIXED.items():
  for mo in ['2026-06','2026-07','2026-08']:
   s=ev[(ev.month==mo)&(ev[name]>=cfg['cut'])];ci=ci_boot(s.head4.to_numpy())
   rec.append({'model':name,'slice':'month','key':mo,'R':len(s),'head4':int(s.head4.sum()),'rate':float(s.head4.mean()),'lo95':ci[0],'hi95':ci[1]})
  # venue from race code positions 4:6
  q=ev.copy();q['venue']=q.race_code.str[4:6]
  for k,s0 in q[q[name]>=cfg['cut']].groupby('venue'):
   ci=ci_boot(s0.head4.to_numpy(),3000,2502);rec.append({'model':name,'slice':'venue','key':k,'R':len(s0),'head4':int(s0.head4.sum()),'rate':float(s0.head4.mean()),'lo95':ci[0],'hi95':ci[1]})
 pd.DataFrame(rec).to_csv(OUT/'stability.csv',index=False)
 # paired overlap/add-drop vs FULL, monthly and all eval
 sels={n:set(ev.loc[ev[n]>=cfg['cut'],'race_code']) for n,cfg in FIXED.items()}
 pair=[]
 for n in ('COMPACT_C01','DROP_MOTOR_C025'):
  for label,mask in [('ALL',pd.Series(True,index=ev.index)),('JUN',ev.month.eq('2026-06')),('JUL',ev.month.eq('2026-07')),('AUG',ev.month.eq('2026-08'))]:
   q=ev[mask].set_index('race_code');A=sels['FULL_C05']&set(q.index);B=sels[n]&set(q.index)
   for kind,codes in [('overlap',A&B),('full_only',A-B),('candidate_only',B-A)]:
    y=q.loc[list(codes),'head4'] if codes else pd.Series(dtype=float)
    pair.append({'candidate':n,'period':label,'kind':kind,'R':len(y),'head4':int(y.sum()),'rate':float(y.mean()) if len(y) else None})
 pd.DataFrame(pair).to_csv(OUT/'overlap_add_drop.csv',index=False)
 # feature inventory to catch ineffective pattern drops
 inv={n:{'features':len(v['features']),'removed':sorted(set(models['FULL_C05']['features'])-set(v['features']))} for n,v in models.items()}
 meta={'fixed_before_audit':FIXED,'fit':'Mar-May only','evaluation':'Jun-Aug only; no selection','holdout_used_for_selection':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'feature_inventory':inv}
 (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
 print(pd.DataFrame(rec).query("slice=='month'").to_string(index=False));print(pd.DataFrame(pair).to_string(index=False));print(json.dumps(meta,ensure_ascii=False));print("HEAD4_PH4_COMPACT_V25_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
