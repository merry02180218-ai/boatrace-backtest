#!/usr/bin/env python3
from pathlib import Path
import itertools
import numpy as np, pandas as pd
import analyze_4head_headrate_3ren_player_st as base
import analyze_4head_exhibition_original_trainonly as exmod
OUT=Path('/tmp/head4_111r_orig_combo'); OUT.mkdir(parents=True,exist_ok=True)
TRAIN=('2026-04','2026-05','2026-06'); HOLD=('2026-07','2026-08')
WIN=-0.029936; REN2=-7.08; PLAYER=.215605; ST=-0.60
ORIG={'turn4_adv_inside':'turn_available','turn4_minus3':'turn_available','straight4_adv_inside':'straight_available','straight4_minus3':'straight_available','orig4_adv_inside':'orig_avg_available'}
def met(x): return len(x),int(x.head4.sum()),100*x.head4.mean() if len(x) else np.nan
def main():
 z=base.settle_all().merge(base.build_motor_features(),on=['date','month','race_code'],how='left').merge(base.build_prior_features(),on=['date','month','race_code'],how='left')
 z['race_code']=z.race_code.astype(str).str.zfill(12); z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
 ex=exmod.build_ex(set(z.race_code)); z=z.merge(ex,on='race_code',how='left')
 z=z[(z.motor_win_diff_4v3>=WIN)&(z.motor_2ren_diff_4v3>=REN2)&(z.player4_all_win>=PLAYER)&(z.basic_complete==1)&(z.st4_adv_inside>=ST)].copy()
 tr=z[z.month.isin(TRAIN)].copy(); ho=z[z.month.isin(HOLD)].copy()
 print('FIXED_BASE train',met(tr),'hold',met(ho))
 # Train-only thresholds per original feature; availability itself is never a positive signal.
 cuts={}
 for f,av in ORIG.items():
  e=tr[(tr[av]==1)&tr[f].notna()]
  cuts[f]=sorted(set(float(e[f].quantile(q)) for q in (.20,.30,.40,.50,.60))) if len(e) else []
 rows=[]
 # single-feature same-availability audit
 for f,av in ORIG.items():
  tt=tr[(tr[av]==1)&tr[f].notna()]; hh=ho[(ho[av]==1)&ho[f].notna()]
  br=met(tt)[2]; bhr=met(hh)[2]
  for c in cuts[f]:
   a=tt[tt[f]>=c]; b=hh[hh[f]>=c]
   rows.append(dict(kind='single',rule=f,cut=str(c),train_avail_R=len(tt),train_avail_rate=br,train_R=len(a),train_rate=met(a)[2],train_inc=met(a)[2]-br,hold_avail_R=len(hh),hold_avail_rate=bhr,hold_R=len(b),hold_rate=met(b)[2],hold_inc=met(b)[2]-bhr))
 # adaptive score: each available original item votes pass/fail; unavailable item contributes nothing.
 # thresholds are train-only; require at least one available item, but report against same availability-pattern baseline.
 choices=[]
 for f in ORIG:
  if cuts[f]: choices.append((f,cuts[f][1])) # q30 fixed from train
 def scored(df):
  x=df.copy(); votes=np.zeros(len(x)); n=np.zeros(len(x))
  for f,c in choices:
   av=ORIG[f]; ok=(x[av]==1)&x[f].notna(); n+=ok.to_numpy(); votes+=(ok&(x[f]>=c)).to_numpy()
  x['orig_n']=n; x['orig_votes']=votes; x['orig_score']=np.where(n>0,votes/n,np.nan); return x
 ts=scored(tr); hs=scored(ho)
 for min_n in (1,2,3):
  for sc in (.4,.5,.6,.67,.75,1.0):
   elig=ts[ts.orig_n>=min_n]; helig=hs[hs.orig_n>=min_n]
   a=elig[elig.orig_score>=sc]; b=helig[helig.orig_score>=sc]
   if len(a)<25: continue
   rows.append(dict(kind='adaptive_vote',rule=f'min_n={min_n};score>={sc}',cut='',train_avail_R=len(elig),train_avail_rate=met(elig)[2],train_R=len(a),train_rate=met(a)[2],train_inc=met(a)[2]-met(elig)[2],hold_avail_R=len(helig),hold_avail_rate=met(helig)[2],hold_R=len(b),hold_rate=met(b)[2],hold_inc=met(b)[2]-met(helig)[2]))
 g=pd.DataFrame(rows); g.to_csv(OUT/'grid.csv',index=False); z.to_csv(OUT/'detail.csv',index=False)
 # Selection strictly train-only: prioritize >=40% and maximum R; otherwise best rate/volume Pareto.
 cand=g[(g.train_rate>=40)&(g.train_R>=25)].sort_values(['train_R','train_rate'],ascending=[False,False])
 if cand.empty: cand=g.sort_values(['train_rate','train_R'],ascending=[False,False])
 print('TRAIN_ONLY_SELECTED'); print(cand.head(1).to_string(index=False))
 print('TOP_TRAIN'); print(g.sort_values(['train_R','train_rate'],ascending=[False,False]).head(30).to_string(index=False))
 print('September UNREAD; production HEAD4_V291_COMP7 untouched')
if __name__=='__main__': main()
