from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from research.run_3head_exhibition_v5 import EX, STATIC, combo, load_direct, pair_rows

SOURCE='analysis_v289_3head_wave21_allrace_feature_settled.csv'
WEIGHTS=[0.0,0.01,0.02,0.03,0.05,0.08]
THRESHOLDS=[0.0,0.10,0.20,0.30]

def oof_baseline(x):
 feats=[c for c in x if c not in ['race_code','second','third','y']]
 oof=np.full(len(x),np.nan)
 for tr,va in GroupKFold(5).split(x,groups=x.race_code):
  m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0))
  m.fit(x.iloc[tr][feats],x.iloc[tr].y);oof[va]=m.predict_proba(x.iloc[va][feats])[:,1]
 return oof

def top3(v,score):
 z=v.copy();z['_score']=score
 return z.sort_values(['race_code','_score','second','third'],ascending=[True,False,True,True]).groupby('race_code').head(3)

def hitset(top):
 return {rc for rc,g in top.groupby('race_code') if g.y.eq(1).any()}

def main():
 use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
 df=pd.read_csv(SOURCE,usecols=use,low_memory=False);df.date=pd.to_datetime(df.date);df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64')
 df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
 feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')].copy();assert len(feb)==3970
 heads=feb[feb.settle__winner==3].copy();assert len(heads)==478
 codes=[str(int(x)).zfill(12) for x in feb.rc.dropna()];direct=load_direct(codes)
 common=heads[heads.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))].copy();assert len(common)==390
 x=pair_rows(common,direct,'A',{});x['p']=oof_baseline(x)
 # Direct scores are race-relative [0,1], higher is better after correction.
 x['exq']=[.55*direct[rc]['ex'][int(a)]+.45*direct[rc]['ex'][int(b)] for rc,a,b in zip(x.race_code,x.second,x.third)]
 x['stq']=[.55*direct[rc]['st'][int(a)]+.45*direct[rc]['st'][int(b)] for rc,a,b in zip(x.race_code,x.second,x.third)]
 base=top3(x,x.p);basehits=hitset(base);allr=set(x.race_code.unique())
 rows=[]
 for wx in WEIGHTS:
  for ws in WEIGHTS:
   if wx==0 and ws==0:continue
   raw=wx*(x.exq-.5)+ws*(x.stq-.5)
   strength=(x.exq-.5).abs()+(x.stq-.5).abs()
   for th in THRESHOLDS:
    adj=np.where(strength>=th,raw,0.0);tt=top3(x,x.p+adj);hh=hitset(tt)
    rescued=len((allr-basehits)&hh);broken=len(basehits-hh);hits=len(hh)
    rows.append({'w_ex':wx,'w_st':ws,'threshold':th,'hits':hits,'capture':hits/len(allr),'rescued_miss':rescued,'broken_hit':broken,'net_rescue':rescued-broken})
 res=pd.DataFrame(rows).sort_values(['net_rescue','hits','broken_hit','w_ex','w_st','threshold'],ascending=[False,False,True,True,True,True])
 best=res.iloc[0].to_dict();best={k:(int(v) if k in ['hits','rescued_miss','broken_hit','net_rescue'] else float(v)) for k,v in best.items()}
 out={'phase':'FEB_POST_RANKING_TICKET_RESCUE','canonical_feb_eligible':len(feb),'canonical_feb_heads':len(heads),'common_ready_head_races':len(common),'baseline_hits':len(basehits),'baseline_capture':len(basehits)/len(allr),'grid_rows':len(res),'best':best,'positive_net_exists':bool(res.net_rescue.max()>0),'september_outcomes_read':False,'production_changed':False}
 res.to_csv('research_v289_3head_exhibition_ticket_rescue_grid.csv',index=False)
 Path('research_v289_3head_exhibition_ticket_rescue.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print(json.dumps(out,ensure_ascii=False,indent=2));print('\nTOP10');print(res.head(10).to_string(index=False))
if __name__=='__main__':main()
