from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from research.run_3head_exhibition_v5 import EX, STATIC, load_direct, pair_rows
SOURCE='analysis_v289_3head_wave21_allrace_feature_settled.csv'; WX=.08; WS=.08

def fit(train):
 f=[c for c in train if c not in ['race_code','second','third','y']]
 m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0));m.fit(train[f],train.y);return m,f

def main():
 use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
 df=pd.read_csv(SOURCE,usecols=use,low_memory=False);df.date=pd.to_datetime(df.date);df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64');df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
 feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')];assert len(feb)==3970
 codes=[str(int(x)).zfill(12) for x in df[(df.date>='2026-02-01')&(df.date<'2026-09-01')].rc.dropna().unique()];direct=load_direct(codes)
 fh=feb[feb.settle__winner==3];assert len(fh)==478
 fc=fh[fh.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))];assert len(fc)==390
 model,feats=fit(pair_rows(fc,direct,'A',{})); rows=[]
 for month in range(2,9):
  start=pd.Timestamp(2026,month,1);end=start+pd.offsets.MonthBegin(1);h=df[(df.date>=start)&(df.date<end)&(df.settle__winner==3)];h=h[h.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))]
  x=pair_rows(h,direct,'A',{});x['p']=model.predict_proba(x[feats])[:,1];x['exq']=[.55*direct[r]['ex'][int(a)]+.45*direct[r]['ex'][int(b)] for r,a,b in zip(x.race_code,x.second,x.third)];x['stq']=[.55*direct[r]['st'][int(a)]+.45*direct[r]['st'][int(b)] for r,a,b in zip(x.race_code,x.second,x.third)];x['adj']=WX*(x.exq-.5)+WS*(x.stq-.5);x['pc']=x.p+x.adj
  for rc,g in x.groupby('race_code'):
   b=g.sort_values(['p','second','third'],ascending=[False,True,True]);c=g.sort_values(['pc','second','third'],ascending=[False,True,True]);bt=b.head(3);ct=c.head(3);bh=bool(bt.y.eq(1).any());ch=bool(ct.y.eq(1).any());cat='rescued' if not bh and ch else 'broken' if bh and not ch else 'unchanged_hit' if bh else 'unchanged_miss'
   bi=pd.MultiIndex.from_frame(bt[['second','third']]);ci=pd.MultiIndex.from_frame(ct[['second','third']]);entered=ct[~pd.MultiIndex.from_frame(ct[['second','third']]).isin(bi)];exited=bt[~pd.MultiIndex.from_frame(bt[['second','third']]).isin(ci)]
   ee=float(entered.exq.mean()) if len(entered) else np.nan;es=float(entered.stq.mean()) if len(entered) else np.nan;xe=float(exited.exq.mean()) if len(exited) else np.nan;xs=float(exited.stq.mean()) if len(exited) else np.nan
   rows.append({'month':month,'race_code':rc,'category':cat,'base_gap':float(b.iloc[2].p-b.iloc[3].p),'entered_exq':ee,'entered_stq':es,'exited_exq':xe,'exited_stq':xs,'ex_adv':ee-xe if np.isfinite(ee) and np.isfinite(xe) else np.nan,'st_adv':es-xs if np.isfinite(es) and np.isfinite(xs) else np.nan,'entered_quality':(ee+es)/2 if np.isfinite(ee) and np.isfinite(es) else np.nan,'swap_adj_adv':float(entered.adj.mean()-exited.adj.mean()) if len(entered) and len(exited) else np.nan,'changed_pairs':len(set(map(tuple,bt[['second','third']].values))^set(map(tuple,ct[['second','third']].values)))//2})
 r=pd.DataFrame(rows);r.to_csv('research_v289_3head_exhibition_off_gate.csv',index=False)
 # Discovery on Feb-Mar only; evaluate the same simple OFF rules separately on pristine Apr-Jun.
 discovery=r[r.month<=3]; pristine=r[r.month.isin([4,5,6])]
 rules=[]
 for qmax in [.55,.60,.625,.65,.675]:
  for advmax in [.15,.20,.25,.30]:
   for gapmin in [0,.005,.01,.02]:
    def ev(z):
     off=z[(z.entered_quality<=qmax)&(z.ex_adv<=advmax)&(z.base_gap>=gapmin)]
     # Turning correction OFF recovers broken (+1) but sacrifices rescued (-1).
     return {'off_races':int(len(off)),'broken_blocked':int((off.category=='broken').sum()),'rescues_lost':int((off.category=='rescued').sum()),'net_off':int((off.category=='broken').sum()-(off.category=='rescued').sum())}
    d=ev(discovery);p=ev(pristine);rules.append({'entered_quality_max':qmax,'ex_adv_max':advmax,'base_gap_min':gapmin,'discovery':d,'apr_jun_pristine':p})
 rules=sorted(rules,key=lambda a:(a['discovery']['net_off'],a['discovery']['broken_blocked'],-a['discovery']['rescues_lost']),reverse=True)
 monthly={}
 for m in range(2,9):
  z=r[r.month==m];monthly[str(m)]={'races':len(z),'rescued':int((z.category=='rescued').sum()),'broken':int((z.category=='broken').sum()),'net_correction':int((z.category=='rescued').sum()-(z.category=='broken').sum()),'non_pristine':m in [7,8]}
 top=rules[:10]
 out={'phase':'EXHIBITION_OFF_GATE','discovery_period':'2026-02..2026-03','pristine_validation':'2026-04..2026-06','non_pristine_reference':'2026-07..2026-08','monthly':monthly,'top_discovery_rules':top,'september_outcomes_read':False,'production_changed':False}
 Path('research_v289_3head_exhibition_off_gate.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
