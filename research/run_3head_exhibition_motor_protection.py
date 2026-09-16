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
 m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0))
 m.fit(train[f],train.y); return m,f

def lane_motor(row,lane):
 a=pd.to_numeric(row.get(f'card__艇{lane}_モーター2連対率'),errors='coerce')
 b=pd.to_numeric(row.get(f'card__艇{lane}_モーター3連対率'),errors='coerce')
 if pd.isna(a) and pd.isna(b): return np.nan
 vals=[float(v)/100. for v in [a,b] if not pd.isna(v)]
 return float(np.mean(vals))

def pair_motor(row,a,b):
 x=lane_motor(row,int(a)); y=lane_motor(row,int(b))
 return .55*x+.45*y if np.isfinite(x) and np.isfinite(y) else np.nan

def metrics(z,rule):
 gapmin,exmax,stmax,mmax=rule
 off=z[(z.base_gap>=gapmin)&(z.ex_adv<=exmax)&(z.st_adv<=stmax)&(z.motor_adv<=mmax)]
 bb=int((off.category=='broken').sum()); rl=int((off.category=='rescued').sum())
 return {'off_races':int(len(off)),'broken_blocked':bb,'rescues_lost':rl,'net_off':bb-rl}

def main():
 use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
 df=pd.read_csv(SOURCE,usecols=use,low_memory=False); df.date=pd.to_datetime(df.date); df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64')
 df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
 # Hard stop: this research source/evaluation must never enter September.
 df=df[df.date<'2026-09-01'].copy()
 feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')]; assert len(feb)==3970
 codes=[str(int(x)).zfill(12) for x in df[df.date>='2026-02-01'].rc.dropna().unique()]; direct=load_direct(codes)
 fh=feb[feb.settle__winner==3]; assert len(fh)==478
 fc=fh[fh.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))]; assert len(fc)==390
 model,feats=fit(pair_rows(fc,direct,'A',{})); rows=[]
 rowmap={str(int(r.rc)).zfill(12):r for _,r in df.iterrows() if not pd.isna(r.rc)}
 for month in range(2,9):
  start=pd.Timestamp(2026,month,1); end=start+pd.offsets.MonthBegin(1)
  h=df[(df.date>=start)&(df.date<end)&(df.settle__winner==3)]; h=h[h.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))]
  x=pair_rows(h,direct,'A',{}); x['p']=model.predict_proba(x[feats])[:,1]
  x['exq']=[.55*direct[r]['ex'][int(a)]+.45*direct[r]['ex'][int(b)] for r,a,b in zip(x.race_code,x.second,x.third)]
  x['stq']=[.55*direct[r]['st'][int(a)]+.45*direct[r]['st'][int(b)] for r,a,b in zip(x.race_code,x.second,x.third)]
  x['motorq']=[pair_motor(rowmap[r],a,b) for r,a,b in zip(x.race_code,x.second,x.third)]
  x['adj']=WX*(x.exq-.5)+WS*(x.stq-.5); x['pc']=x.p+x.adj
  for rc,g in x.groupby('race_code'):
   b=g.sort_values(['p','second','third'],ascending=[False,True,True]); c=g.sort_values(['pc','second','third'],ascending=[False,True,True]); bt=b.head(3); ct=c.head(3)
   bh=bool(bt.y.eq(1).any()); ch=bool(ct.y.eq(1).any()); cat='rescued' if not bh and ch else 'broken' if bh and not ch else 'unchanged_hit' if bh else 'unchanged_miss'
   bi=pd.MultiIndex.from_frame(bt[['second','third']]); ci=pd.MultiIndex.from_frame(ct[['second','third']]); entered=ct[~pd.MultiIndex.from_frame(ct[['second','third']]).isin(bi)]; exited=bt[~pd.MultiIndex.from_frame(bt[['second','third']]).isin(ci)]
   def avg(z,k): return float(z[k].mean()) if len(z) and z[k].notna().any() else np.nan
   ee,es,em=avg(entered,'exq'),avg(entered,'stq'),avg(entered,'motorq'); xe,xs,xm=avg(exited,'exq'),avg(exited,'stq'),avg(exited,'motorq')
   rows.append({'month':month,'race_code':rc,'category':cat,'base_gap':float(b.iloc[2].p-b.iloc[3].p),'ex_adv':ee-xe if np.isfinite(ee) and np.isfinite(xe) else np.nan,'st_adv':es-xs if np.isfinite(es) and np.isfinite(xs) else np.nan,'motor_adv':em-xm if np.isfinite(em) and np.isfinite(xm) else np.nan,'entered_motor':em,'exited_motor':xm,'swap_adj_adv':float(entered.adj.mean()-exited.adj.mean()) if len(entered) and len(exited) else np.nan,'changed_pairs':len(set(map(tuple,bt[['second','third']].values))^set(map(tuple,ct[['second','third']].values)))//2})
 r=pd.DataFrame(rows); r.to_csv('research_v289_3head_motor_protection.csv',index=False)
 march=r[r.month==3].copy(); rules=[]
 # Simple operational protection grid. Motor advantage is entered minus exited; <=0 means new pair has no motor edge.
 for gapmin in [0,.005,.01,.02]:
  for exmax in [.10,.15,.20]:
   for stmax in [.10,.15,.20]:
    for mmax in [-.05,0,.025,.05]:
     rule=(gapmin,exmax,stmax,mmax); rules.append({'base_gap_min':gapmin,'ex_adv_max':exmax,'st_adv_max':stmax,'motor_adv_max':mmax,'march':metrics(march,rule)})
 rules=sorted(rules,key=lambda a:(a['march']['net_off'],a['march']['broken_blocked'],-a['march']['rescues_lost'],-a['march']['off_races']),reverse=True)
 frozen=rules[0]; fr=(frozen['base_gap_min'],frozen['ex_adv_max'],frozen['st_adv_max'],frozen['motor_adv_max'])
 monthly={str(m):metrics(r[r.month==m],fr) for m in range(2,9)}
 for m in range(2,9): monthly[str(m)]['non_pristine']=m in [7,8]
 aprjun={k:monthly[k] for k in ['4','5','6']}; stable_all_positive=all(aprjun[k]['net_off']>0 for k in aprjun)
 out={'phase':'MOTOR_AWARE_V288_PROTECTION','baseline_fit':'2026-02 common-ready heads (in-sample reference only)','rule_discovery':'2026-03 only','frozen_march_rule':{k:v for k,v in frozen.items() if k!='march'},'march_discovery_metrics':frozen['march'],'monthly_frozen_rule':monthly,'apr_jun_all_positive':stable_all_positive,'top_march_rules':rules[:12],'motor_definition':'pair=.55*second+.45*third; lane motor=mean(motor2rate,motor3rate)/100; motor_adv=entered-exited','exact_v288_exclusion_preserved':True,'september_outcomes_read':False,'production_changed':False}
 Path('research_v289_3head_motor_protection.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
