#!/usr/bin/env python3
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from collections import defaultdict
from statistics import mean
import analyze_4head_headrate_3ren_player_st as base
import run_v326_1head_ticketaware_exhibition as v326
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct,ff

OUT=Path('/tmp/head4_exhibition');OUT.mkdir(parents=True,exist_ok=True)
TRAIN=('2026-04','2026-05','2026-06');HOLD=('2026-07','2026-08')
PLAYER_CUTS=(0.210863,0.215605)
PRELOAD=date(2025,10,1);END=date(2026,8,31)

def bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def avg(v):return float(np.mean(v)) if v else np.nan
def st_bias(sums,allv):
 g=mean(allv) if allv else .15;return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}
def update_st(rs,sums,allv):
 for r in rs:
  for b in range(1,7):
   v=ff(r.get(f'艇{b}_スタート展示'))
   if v is not None and -.30<v<1.0:sums[b].append(v);allv.append(v)
def build_ex(wanted):
 sums=defaultdict(list);allv=[];out=[];d=PRELOAD
 while d<=END:
  if d.year==2026 and d.month==9:raise RuntimeError('September outcome access blocked')
  y=d.strftime('%Y/%m/%d');strows=rows(f'data/previews/stt/{y}.csv');bias=st_bias(sums,allv)
  if d>=date(2026,4,1):
   tkz=bycode(rows(f'data/previews/tkz/{y}.csv'));stt=bycode(strows);orig=bycode(rows(f'data/previews/original_exhibition/{y}.csv'))
   for c in [x for x in wanted if x.startswith(d.strftime('%Y%m%d'))]:
    tr,sr,orr=tkz.get(c,{}),stt.get(c,{}),orig.get(c,{})
    audit=v326.raw_completeness(tr,sr,orr)
    complete=int(all(audit[k] for k in ('tkz_all6','stt_all6','orig_turn_all6','orig_straight_all6','orig_avg_all6')))
    z={'race_code':c,'ex_complete':complete,**audit}
    if complete:
     ex,st,os=corrected_direct(c,tkz,stt,orig,bias)
     turn={b:os[b]['turn'] for b in range(1,7)};straight={b:os[b]['straight'] for b in range(1,7)};oa={b:os[b]['avg'] for b in range(1,7)}
     inside=(1,2,3);others=(1,2,3,5,6)
     z.update({
      'ex4_adv_all':avg([ex[b] for b in others])-ex[4],
      'ex4_adv_inside':avg([ex[b] for b in inside])-ex[4],
      'st4_adv_all':avg([st[b] for b in others])-st[4],
      'st4_adv_inside':avg([st[b] for b in inside])-st[4],
      'turn4_adv_inside':turn[4]-avg([turn[b] for b in inside]),
      'straight4_adv_inside':straight[4]-avg([straight[b] for b in inside]),
      'orig4_adv_inside':oa[4]-avg([oa[b] for b in inside]),
      'straight4_minus3':straight[4]-straight[3],
      'turn4_minus3':turn[4]-turn[3],
     })
    out.append(z)
  update_st(strows,sums,allv);d+=timedelta(days=1)
 return pd.DataFrame(out)
def metric(x):return {'R':len(x),'H':int(x.head4.sum()),'rate':100*x.head4.mean() if len(x) else np.nan}
def main():
 z=base.settle_all().merge(base.build_motor_features(),on=['race_code','month'],how='inner')
 z=z[(z.motor_win_diff_4v3>=base.WIN_CUT)&(z.motor_2ren_diff_4v3>=base.REN2_CUT)]
 z=z.merge(base.build_prior_features(),on=['race_code','month'],how='left')
 z['race_code']=z.race_code.astype(str).str.zfill(12);z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
 ex=build_ex(set(z.race_code));z=z.merge(ex,on='race_code',how='left');z.to_csv(OUT/'detail.csv',index=False)
 feats=['ex4_adv_all','ex4_adv_inside','st4_adv_all','st4_adv_inside','turn4_adv_inside','straight4_adv_inside','orig4_adv_inside','straight4_minus3','turn4_minus3']
 grid=[]
 for pc in PLAYER_CUTS:
  b=z[z.player4_all_win>=pc];tr=b[b.month.isin(TRAIN)];ho=b[b.month.isin(HOLD)]
  print('BASE',pc,metric(tr),'HOLD',metric(ho),'complete',int(tr.ex_complete.fillna(0).sum()),'/',len(tr))
  for f in feats:
   tt=tr[(tr.ex_complete==1)&tr[f].notna()];hh=ho[(ho.ex_complete==1)&ho[f].notna()]
   if len(tt)<25:continue
   for q in np.arange(.15,.86,.05):
    cut=float(tt[f].quantile(q));a=tt[tt[f]>=cut]
    if len(a)<25:continue
    grid.append({'player_cut':pc,'feature':f,'q':q,'cut':cut,**{f'train_{k}':v for k,v in metric(a).items()},**{f'hold_{k}':v for k,v in metric(hh[hh[f]>=cut]).items()}})
 g=pd.DataFrame(grid);g.to_csv(OUT/'grid.csv',index=False)
 cand=g[(g.train_R>=35)].copy();cand['goal35']=(cand.train_rate>=35).astype(int)
 cand=cand.sort_values(['goal35','train_rate','train_R'],ascending=[False,False,False]);best=cand.iloc[0]
 print('SELECTED_TRAIN_ONLY',best[['player_cut','feature','q','cut','train_R','train_rate']].to_dict())
 print('FIXED_HOLD',{'R':int(best.hold_R),'rate':float(best.hold_rate)})
 print('TOP10_TRAIN_ONLY');print(cand[['player_cut','feature','cut','train_R','train_rate','hold_R','hold_rate']].head(10).to_string(index=False))
 print('September blind guard PASS; production untouched')
if __name__=='__main__':main()
