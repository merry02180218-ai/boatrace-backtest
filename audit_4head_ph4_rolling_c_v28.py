#!/usr/bin/env python3
"""v28 rolling-origin falsification of PH4 regularization. Fixed cut .36."""
import json
from pathlib import Path
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_player_waku_soft_ablation_v23 as v23
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv");TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv");OUT=Path("/tmp/head4_ph4_rolling_c_v28");OUT.mkdir(exist_ok=True)
PH4=['b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_win','b4_pl_frame_p2','b4_pl_recent_p2'];CUT=.36
def mdl(C):return Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=C))])
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12);z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 old=[c for c in z if '_pl_' in c]
 if old:z=z.drop(columns=old)
 z=z.merge(v23.build_ph(),on='race_code',how='left',validate='one_to_one')
 forb=("actual","result","payout","odds","finish","着順","1着","2着","3着");num=[c for c in z if c not in {'head4','race_code','month'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forb)]
 base=[c for c in num if '_pl_' not in c and not c.startswith('w10_') and not c.startswith('opp_waku_b')];feats=base+PH4
 rows=[];race=[]
 # rolling origin: June fit Mar-May; July fit Mar-Jun; August fit Mar-Jul.
 for test,trainmonths in [('2026-06',['2026-03','2026-04','2026-05']),('2026-07',['2026-03','2026-04','2026-05','2026-06']),('2026-08',['2026-03','2026-04','2026-05','2026-06','2026-07'])]:
  tr=z[z.month.isin(trainmonths)];te=z[z.month.eq(test)].copy()
  for name,C in [('FULL_C05',.5),('FULL_C01',.1)]:
   m=mdl(C);m.fit(tr[feats],tr.head4);p=m.predict_proba(te[feats])[:,1];sel=p>=CUT
   rows.append({'model':name,'test_month':test,'train_months':','.join(trainmonths),'train_R':len(tr),'R':int(sel.sum()),'head4':int(te.loc[sel,'head4'].sum()),'rate':float(te.loc[sel,'head4'].mean()) if sel.sum() else None})
   for rc,y,pr,se in zip(te.race_code,te.head4,p,sel):race.append({'race_code':rc,'month':test,'model':name,'p':float(pr),'selected':bool(se),'head4':int(y)})
 out=pd.DataFrame(rows);out.to_csv(OUT/'monthly.csv',index=False);r=pd.DataFrame(race);r.to_csv(OUT/'race_scores.csv',index=False)
 # paired selection changes C05 -> C01 per month and aggregate
 wide=r.pivot(index=['race_code','month','head4'],columns='model',values=['p','selected']).reset_index();pairs=[]
 for period in ['ALL','2026-06','2026-07','2026-08']:
  q=wide if period=='ALL' else wide[wide.month.eq(period)];a=q[('selected','FULL_C05')].astype(bool);b=q[('selected','FULL_C01')].astype(bool)
  for kind,mask in [('overlap',a&b),('c05_only',a&~b),('c01_only',~a&b)]:
   y=q.loc[mask,('head4','')];pairs.append({'period':period,'kind':kind,'R':len(y),'head4':int(y.sum()),'rate':float(y.mean()) if len(y) else None})
 pd.DataFrame(pairs).to_csv(OUT/'paired.csv',index=False)
 meta={'design':'rolling origin','cut':CUT,'C_values':[.5,.1],'test_months':['2026-06','2026-07','2026-08'],'no_future_month_in_training':True,'retuning':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False}
 (OUT/'meta.json').write_text(json.dumps(meta,indent=2)+"\n");print(out.to_string(index=False));print(pd.DataFrame(pairs).to_string(index=False));print(json.dumps(meta));print("HEAD4_PH4_ROLLING_C_V28_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
