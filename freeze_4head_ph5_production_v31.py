#!/usr/bin/env python3
"""v29 fixed rolling-origin PLAYER_HISTORY component ablation."""
import json
from pathlib import Path
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_player_waku_soft_ablation_v23 as v23
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv");TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv");OUT=Path("/tmp/head4_ph5_production_freeze_v31");OUT.mkdir(exist_ok=True)
CUT=.36;C=.5
PH={'all_win':'b4_pl_all_win','all_p2':'b4_pl_all_p2','frame_win':'b4_pl_frame_win','frame_p2':'b4_pl_frame_p2','recent_p2':'b4_pl_recent_p2'}
SPECS={'PH_FULL5':list(PH.values())}
def mdl():return Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=C))])
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12);z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 old=[c for c in z if '_pl_' in c]
 if old:z=z.drop(columns=old)
 z=z.merge(v23.build_ph(),on='race_code',how='left',validate='one_to_one')
 forb=("actual","result","payout","odds","finish","着順","1着","2着","3着");num=[c for c in z if c not in {'head4','race_code','month'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forb)]
 base=[c for c in num if '_pl_' not in c and not c.startswith('w10_') and not c.startswith('opp_waku_b')]
 rows=[];race=[]
 rolls=[('2026-06',['2026-03','2026-04','2026-05']),('2026-07',['2026-03','2026-04','2026-05','2026-06']),('2026-08',['2026-03','2026-04','2026-05','2026-06','2026-07'])]
 for test,trm in rolls:
  tr=z[z.month.isin(trm)];te=z[z.month.eq(test)].copy()
  for name,extra in SPECS.items():
   fs=base+extra;m=mdl();m.fit(tr[fs],tr.head4);p=m.predict_proba(te[fs])[:,1];sel=p>=CUT
   rows.append({'model':name,'test_month':test,'train_months':','.join(trm),'R':int(sel.sum()),'head4':int(te.loc[sel,'head4'].sum()),'rate':float(te.loc[sel,'head4'].mean()) if sel.sum() else None})
   for rc,y,pr,se in zip(te.race_code,te.head4,p,sel):race.append({'race_code':rc,'month':test,'model':name,'p':float(pr),'selected':bool(se),'head4':int(y)})
 out=pd.DataFrame(rows);out.to_csv(OUT/'monthly.csv',index=False);r=pd.DataFrame(race);r.to_csv(OUT/'race_scores.csv',index=False)
 agg=out.groupby('model',as_index=False).agg(R=('R','sum'),head4=('head4','sum'));agg['rate']=agg.head4/agg.R;agg.to_csv(OUT/'aggregate.csv',index=False)
 # fixed paired selection deltas versus FULL5 and BASE
 pairs=[]
 for ref in ['PH_FULL5']:
  for cand in SPECS:
   if cand==ref:continue
   a=r[r.model.eq(ref)].set_index('race_code');b=r[r.model.eq(cand)].set_index('race_code')
   for period in ['ALL','2026-06','2026-07','2026-08']:
    ids=a.index if period=='ALL' else a[a.month.eq(period)].index;aa=a.loc[ids].selected.astype(bool);bb=b.loc[ids].selected.astype(bool)
    for kind,mask in [('overlap',aa&bb),('ref_only',aa&~bb),('cand_only',~aa&bb)]:
     y=a.loc[ids[mask],'head4'];pairs.append({'reference':ref,'candidate':cand,'period':period,'kind':kind,'R':len(y),'head4':int(y.sum()),'rate':float(y.mean()) if len(y) else None})
 pd.DataFrame(pairs).to_csv(OUT/'paired.csv',index=False)
 # fit the formally adopted PH5 head model through 2026-08-31; September remains unread
 fs=base+SPECS['PH_FULL5']; final=mdl(); final.fit(z[z.month.isin(['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08'])][fs],z[z.month.isin(['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08'])].head4)
 imp=final.named_steps['imp'];sc=final.named_steps['sc'];lr=final.named_steps['lr']; artifact={'id':'HEAD4_PH5_PRODUCTION_V31_20260831','model_type':'SimpleImputer(median)->StandardScaler->LogisticRegression','fit_period':{'months':['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08'],'max_date':'2026-08-31'},'features':fs,'feature_count':len(fs),'cut':CUT,'C':C,'imputer_median':imp.statistics_.tolist(),'scaler_mean':sc.mean_.tolist(),'scaler_scale':sc.scale_.tolist(),'coef':lr.coef_[0].tolist(),'intercept':float(lr.intercept_[0]),'player_history_features':SPECS['PH_FULL5'],'same_day_results_used':False,'september_labels_used':False,'production_status':'FORMALLY_ADOPTED_BY_USER_2026-09-22'}; (OUT/'head4_ph5_production_v31_20260831.json').write_text(json.dumps(artifact,indent=2)+'\n')
 meta={'design':'rolling origin fixed PH component ablation','C':C,'cut':CUT,'specs':SPECS,'retuning':False,'no_future_month_in_training':True,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':True}
 (OUT/'meta.json').write_text(json.dumps(meta,indent=2)+"\n");print(out.to_string(index=False));print(agg.to_string(index=False));print(json.dumps(meta));print("HEAD4_PH5_PRODUCTION_FREEZE_V31_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
