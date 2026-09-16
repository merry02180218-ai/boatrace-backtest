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
 f=[c for c in train if c not in ['race_code','second','third','y']]; m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0)); m.fit(train[f],train.y); return m,f

def main():
 use=['date','race_code_norm','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
 df=pd.read_csv(SOURCE,usecols=use,low_memory=False); df.date=pd.to_datetime(df.date); df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64'); df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
 feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')]; assert len(feb)==3970
 codes=[str(int(x)).zfill(12) for x in df[(df.date>='2026-02-01')&(df.date<'2026-09-01')].rc.dropna().unique()]; direct=load_direct(codes)
 fh=feb[feb.settle__winner==3]; assert len(fh)==478
 fc=fh[fh.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))]; assert len(fc)==390
 train=pair_rows(fc,direct,'A',{}); model,feats=fit(train)
 rows=[]
 for month in range(2,9):
  start=pd.Timestamp(2026,month,1); end=start+pd.offsets.MonthBegin(1); h=df[(df.date>=start)&(df.date<end)&(df.settle__winner==3)]; h=h[h.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))]
  x=pair_rows(h,direct,'A',{}); x['p']=model.predict_proba(x[feats])[:,1]; x['exq']=[.55*direct[r]['ex'][int(a)]+.45*direct[r]['ex'][int(b)] for r,a,b in zip(x.race_code,x.second,x.third)]; x['stq']=[.55*direct[r]['st'][int(a)]+.45*direct[r]['st'][int(b)] for r,a,b in zip(x.race_code,x.second,x.third)]; x['adj']=WX*(x.exq-.5)+WS*(x.stq-.5); x['pc']=x.p+x.adj
  for rc,g in x.groupby('race_code'):
   b=g.sort_values(['p','second','third'],ascending=[False,True,True]); c=g.sort_values(['pc','second','third'],ascending=[False,True,True]); bt=b.head(3); ct=c.head(3); bh=bool(bt.y.eq(1).any()); ch=bool(ct.y.eq(1).any()); cat='rescued' if (not bh and ch) else 'broken' if (bh and not ch) else 'unchanged_hit' if bh else 'unchanged_miss'; gap=float(b.iloc[2].p-b.iloc[3].p); changed=set(zip(bt.second,bt.third))^set(zip(ct.second,ct.third)); swap_margin=float(max(c.iloc[2].pc-c.iloc[3].pc,0)); entered=ct[~ct.set_index(['second','third']).index.isin(bt.set_index(['second','third']).index)]; exited=bt[~bt.set_index(['second','third']).index.isin(ct.set_index(['second','third']).index)]; rows.append({'month':month,'race_code':rc,'category':cat,'base_gap_3_4':gap,'corrected_gap_3_4':swap_margin,'max_abs_adj':float(g.adj.abs().max()),'entered_exq':float(entered.exq.mean()) if len(entered) else np.nan,'entered_stq':float(entered.stq.mean()) if len(entered) else np.nan,'exited_exq':float(exited.exq.mean()) if len(exited) else np.nan,'exited_stq':float(exited.stq.mean()) if len(exited) else np.nan,'changed_pairs':len(changed)//2})
 outdf=pd.DataFrame(rows); outdf.to_csv('research_v289_3head_exhibition_rescue_break_decomp.csv',index=False)
 mainp=outdf[outdf.month<=6]; summary={}
 for cat,g in mainp.groupby('category'): summary[cat]={'n':len(g),'base_gap_median':float(g.base_gap_3_4.median()),'base_gap_mean':float(g.base_gap_3_4.mean()),'max_abs_adj_median':float(g.max_abs_adj.median()),'entered_exq_mean':float(g.entered_exq.mean()),'entered_stq_mean':float(g.entered_stq.mean()),'exited_exq_mean':float(g.exited_exq.mean()),'exited_stq_mean':float(g.exited_stq.mean())}
 gates=[]
 for gap in [0.0025,0.005,0.01,0.02,0.04]:
  for amin in [0.0,0.005,0.01,0.02]:
   z=mainp[(mainp.base_gap_3_4<=gap)&(mainp.max_abs_adj>=amin)]; r=int((z.category=='rescued').sum()); b=int((z.category=='broken').sum()); gates.append({'gap_max':gap,'adj_min':amin,'races':len(z),'rescued':r,'broken':b,'net':r-b})
 gates=sorted(gates,key=lambda q:(q['net'],q['races']),reverse=True)
 out={'phase':'RESCUE_BROKEN_DECOMPOSITION','analysis_period':'2026-02..2026-06','non_pristine_reference':'2026-07..2026-08','frozen_params':{'w_ex':WX,'w_st':WS},'summary':summary,'gate_candidates':gates,'best_gate_discovery':gates[0] if gates else None,'september_outcomes_read':False,'production_changed':False}
 Path('research_v289_3head_exhibition_rescue_break_decomp.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
