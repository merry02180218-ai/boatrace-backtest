#!/usr/bin/env python3
"""v24 fine ablation around PH4 anchor. Imports v23 causal PH builder.
Fit Mar-May; June selects cut with volume floor; Jul/Aug report separately only.
"""
import json,os
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_waku10_rel43_v4 as w4
import research_4head_player_waku_soft_ablation_v23 as v23
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv");TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv")
OUT=Path("/tmp/head4_ph4_fine_ablation_v24");OUT.mkdir(exist_ok=True)
DEV={"2026-03","2026-04","2026-05"};VAL={"2026-06"};HOLD={"2026-07","2026-08"}
PH4=['b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_win','b4_pl_frame_p2','b4_pl_recent_p2']
def fit(tr,qs,feats,C):
 p=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=C))]);p.fit(tr[feats],tr.head4);return [p.predict_proba(q[feats])[:,1] for q in qs]
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12)
 z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 phcols=[x for x in z if '_pl_' in x]
 if phcols:z=z.drop(columns=phcols)
 z=z.merge(v23.build_ph(),on='race_code',how='left',validate='one_to_one')
 forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
 numeric=[c for c in z if c not in {'head4','race_code','month'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forbidden)]
 base=[c for c in numeric if '_pl_' not in c and not c.startswith('w10_') and not c.startswith('opp_waku_b')]
 groups={
 'local':lambda c:'local_' in c.lower(),'motor':lambda c:'motor_' in c.lower(),'boat':lambda c:'boat_' in c.lower(),
 'top3':lambda c:'top3' in c.lower(),'top2':lambda c:'top2' in c.lower(),'avg_st':lambda c:'avg_st' in c.lower(),
 'national_win':lambda c:'national_win' in c.lower(),
 }
 fam={'FULL':base}
 for n,fn in groups.items():fam['DROP_'+n.upper()]=[c for c in base if not fn(c)]
 # cumulative compact sets, intentionally chosen before holdout inspection
 fam['NO_LOCAL_BOAT_TOP3']=[c for c in base if not (groups['local'](c) or groups['boat'](c) or groups['top3'](c))]
 fam['CORE_WIN_ST_MOTOR']=[c for c in base if ('national_win' in c.lower() or 'avg_st' in c.lower() or 'motor_' in c.lower())]
 tr=z[z.month.isin(DEV)].copy();va=z[z.month.isin(VAL)].copy();ho=z[z.month.isin(HOLD)].copy();out=[]
 for name,bf in fam.items():
  feats=bf+PH4
  for C in (.1,.25,.5,1.0):
   ps=fit(tr,[tr,va,ho],feats,C); key=f'{name}_C{C}'
   for q,p in zip((tr,va,ho),ps):q[key]=p
   cand=[]
   for cut in np.arange(.20,.451,.01):
    s=va[va[key]>=cut]
    if 45<=len(s)<=70:cand.append((float(s.head4.mean()),len(s),float(cut)))
   if not cand:continue
   chosen=sorted(cand,key=lambda x:(x[0],x[1]),reverse=True)[0][2]
   for period,q in [('DEV',tr),('JUN',va),('JUL',ho[ho.month.eq('2026-07')]),('AUG',ho[ho.month.eq('2026-08')]),('JUL_AUG',ho)]:
    s=q[q[key]>=chosen];out.append({'model':key,'period':period,'cut':chosen,'features':len(feats),'R':len(s),'head4':int(s.head4.sum()),'rate':float(s.head4.mean()) if len(s) else None})
 comp=pd.DataFrame(out);comp.to_csv(OUT/'comparison.csv',index=False)
 rank=comp[comp.period.eq('JUN')].sort_values(['rate','R'],ascending=[False,False]);rank.to_csv(OUT/'june_ranking.csv',index=False)
 meta={'anchor':'PH4','selection':'June only, 45-70 races','holdout_used_for_selection':False,'C_grid':[.1,.25,.5,1.0],'families':{k:len(v)+len(PH4) for k,v in fam.items()},'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False}
 (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
 print(comp.to_string(index=False));print("TOP_JUNE");print(rank.head(20).to_string(index=False));print(json.dumps(meta,ensure_ascii=False));print("HEAD4_PH4_FINE_ABLATION_V24_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
