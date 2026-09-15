#!/usr/bin/env python3
from pathlib import Path
import numpy as np, pandas as pd
import analyze_4head_headrate_3ren_player_st as base
import analyze_4head_exhibition_original_trainonly as exmod
OUT=Path('/tmp/head4_relaxed_motor');OUT.mkdir(parents=True,exist_ok=True)
TRAIN=('2026-04','2026-05','2026-06'); HOLD=('2026-07','2026-08')
PLAYER_CUTS=(0.204165,0.210863,0.215605,0.224982)
FEATS={'ex4_adv_all':'basic_complete','ex4_adv_inside':'basic_complete','st4_adv_all':'basic_complete','st4_adv_inside':'basic_complete','turn4_adv_inside':'turn_available','turn4_minus3':'turn_available','straight4_adv_inside':'straight_available','straight4_minus3':'straight_available','orig4_adv_inside':'orig_avg_available'}
def m(x): return {'R':len(x),'H':int(x.head4.sum()),'rate':100*x.head4.mean() if len(x) else np.nan}
def main():
 z=base.settle_all().merge(base.build_motor_features(),on=['date','month','race_code'],how='left')
 z=z.merge(base.build_prior_features(),on=['date','month','race_code'],how='left')
 z['race_code']=z.race_code.astype(str).str.zfill(12);z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
 tr0=z[z.month.isin(TRAIN)].copy()
 # train-only motor thresholds; include current and progressively relaxed quantiles/zero floors
 w=pd.to_numeric(tr0.motor_win_diff_4v3,errors='coerce'); r=pd.to_numeric(tr0.motor_2ren_diff_4v3,errors='coerce')
 wc=sorted(set([base.WIN_CUT,0.0]+[float(w.quantile(q)) for q in (.30,.35,.40,.45,.50,.55)]))
 rc=sorted(set([base.REN2_CUT,0.0]+[float(r.quantile(q)) for q in (.30,.35,.40,.45,.50,.55)]))
 wanted=set(z.race_code); ex=exmod.build_ex(wanted);z=z.merge(ex,on='race_code',how='left');z.to_csv(OUT/'detail.csv',index=False)
 rows=[]
 for a in wc:
  for b in rc:
   motor=z[(z.motor_win_diff_4v3>=a)&(z.motor_2ren_diff_4v3>=b)]
   trm=motor[motor.month.isin(TRAIN)];hom=motor[motor.month.isin(HOLD)]
   if len(trm)<80: continue
   for pc in PLAYER_CUTS:
    tr=trm[trm.player4_all_win>=pc];ho=hom[hom.player4_all_win>=pc]
    if len(tr)<45: continue
    # no exhibition gate baseline
    rows.append({'win_cut':a,'ren2_cut':b,'motor_train_R':len(trm),'player_cut':pc,'feature':'NONE','avail':'ALL','cut':np.nan,'train_R':len(tr),'train_rate':m(tr)['rate'],'hold_R':len(ho),'hold_rate':m(ho)['rate']})
    for f,av in FEATS.items():
     tt=tr[(tr[av]==1)&tr[f].notna()];hh=ho[(ho[av]==1)&ho[f].notna()]
     if len(tt)<35: continue
     avrate=m(tt)['rate']; havrate=m(hh)['rate']
     for q in (.20,.30,.40,.50,.60):
      cut=float(tt[f].quantile(q));sel=tt[tt[f]>=cut]
      if len(sel)<35:continue
      hs=hh[hh[f]>=cut]
      rows.append({'win_cut':a,'ren2_cut':b,'motor_train_R':len(trm),'player_cut':pc,'feature':f,'avail':av,'cut':cut,'train_avail_R':len(tt),'train_avail_rate':avrate,'train_R':len(sel),'train_rate':m(sel)['rate'],'train_increment_pp':m(sel)['rate']-avrate,'hold_avail_R':len(hh),'hold_avail_rate':havrate,'hold_R':len(hs),'hold_rate':m(hs)['rate'],'hold_increment_pp':m(hs)['rate']-havrate})
 g=pd.DataFrame(rows);g.to_csv(OUT/'grid.csv',index=False)
 # train-only ranking: maximize R among >=35%, tie by rate; representative fixed before holdout reporting
 good=g[(g.train_rate>=35)&(g.train_R>=35)].sort_values(['train_R','train_rate'],ascending=[False,False])
 if good.empty: best=g.sort_values(['train_rate','train_R'],ascending=[False,False]).iloc[0]
 else: best=good.iloc[0]
 print('TRAIN_ONLY_SELECTED',best.to_dict())
 print('TOP_VOLUME_AT_35');print(g[(g.train_rate>=35)&(g.train_R>=35)].sort_values(['train_R','train_rate'],ascending=[False,False]).head(20).to_string(index=False))
 print('MOTOR_UNIVERSE_PARETO');
 u=g[['win_cut','ren2_cut','motor_train_R']].drop_duplicates().sort_values('motor_train_R',ascending=False);print(u.head(30).to_string(index=False))
 print('September UNREAD guard: END inherited through builders <= 2026-08-31; production untouched')
if __name__=='__main__':main()
