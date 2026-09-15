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
BASIC_FEATS={'ex4_adv_all':'basic_complete','ex4_adv_inside':'basic_complete','st4_adv_all':'basic_complete','st4_adv_inside':'basic_complete'}
ORIG_FEATS={'turn4_adv_inside':'turn_available','turn4_minus3':'turn_available','straight4_adv_inside':'straight_available','straight4_minus3':'straight_available','orig4_adv_inside':'orig_avg_available'}

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
    basic=int(bool(audit['tkz_all6']) and bool(audit['stt_all6']))
    turn_av=int(bool(audit['orig_turn_all6']));straight_av=int(bool(audit['orig_straight_all6']));avg_av=int(bool(audit['orig_avg_all6']))
    z={'race_code':c,'venue_code':c[8:10],'basic_complete':basic,'turn_available':turn_av,'straight_available':straight_av,'orig_avg_available':avg_av,'orig_row_present':int(bool(orr)),**audit}
    if basic:
     ex,st,os=corrected_direct(c,tkz,stt,orig,bias);inside=(1,2,3);others=(1,2,3,5,6)
     z.update({'ex4_adv_all':avg([ex[b] for b in others])-ex[4],'ex4_adv_inside':avg([ex[b] for b in inside])-ex[4],'st4_adv_all':avg([st[b] for b in others])-st[4],'st4_adv_inside':avg([st[b] for b in inside])-st[4]})
     if turn_av:
      turn={b:os[b]['turn'] for b in range(1,7)};z.update({'turn4_adv_inside':turn[4]-avg([turn[b] for b in inside]),'turn4_minus3':turn[4]-turn[3]})
     if straight_av:
      straight={b:os[b]['straight'] for b in range(1,7)};z.update({'straight4_adv_inside':straight[4]-avg([straight[b] for b in inside]),'straight4_minus3':straight[4]-straight[3]})
     if avg_av:
      oa={b:os[b]['avg'] for b in range(1,7)};z['orig4_adv_inside']=oa[4]-avg([oa[b] for b in inside])
    out.append(z)
  update_st(strows,sums,allv);d+=timedelta(days=1)
 return pd.DataFrame(out)
def metric(x):return {'R':len(x),'H':int(x.head4.sum()),'rate':100*x.head4.mean() if len(x) else np.nan}
def main():
 z=base.settle_all().merge(base.build_motor_features(),on=['race_code','month'],how='inner');z=z[(z.motor_win_diff_4v3>=base.WIN_CUT)&(z.motor_2ren_diff_4v3>=base.REN2_CUT)];z=z.merge(base.build_prior_features(),on=['race_code','month'],how='left')
 z['race_code']=z.race_code.astype(str).str.zfill(12);z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
 ex=build_ex(set(z.race_code));z=z.merge(ex,on='race_code',how='left');z.to_csv(OUT/'detail.csv',index=False)
 venue=z.groupby('venue_code',dropna=False).agg(R=('race_code','size'),basic=('basic_complete','sum'),turn=('turn_available','sum'),straight=('straight_available','sum'),orig_avg=('orig_avg_available','sum'),orig_rows=('orig_row_present','sum')).reset_index();venue.to_csv(OUT/'venue_availability.csv',index=False);print('VENUE_ITEM_AVAILABILITY');print(venue.to_string(index=False))
 grid=[]
 for pc in PLAYER_CUTS:
  b=z[z.player4_all_win>=pc];tr=b[b.month.isin(TRAIN)];ho=b[b.month.isin(HOLD)];print('BASE',pc,metric(tr),'HOLD',metric(ho),'basic',int(tr.basic_complete.fillna(0).sum()),'turn',int(tr.turn_available.fillna(0).sum()),'straight',int(tr.straight_available.fillna(0).sum()),'avg',int(tr.orig_avg_available.fillna(0).sum()),'/',len(tr))
  for f,av in {**BASIC_FEATS,**ORIG_FEATS}.items():
   tt=tr[(tr[av]==1)&tr[f].notna()];hh=ho[(ho[av]==1)&ho[f].notna()]
   if len(tt)<25:continue
   train_av_base=metric(tt);hold_av_base=metric(hh)
   for q in np.arange(.15,.86,.05):
    cut=float(tt[f].quantile(q));a=tt[tt[f]>=cut]
    if len(a)<25:continue
    hm=metric(hh[hh[f]>=cut]);am=metric(a)
    grid.append({'player_cut':pc,'feature':f,'availability':av,'q':q,'cut':cut,'train_avail_base_R':train_av_base['R'],'train_avail_base_rate':train_av_base['rate'],'train_increment_pp':am['rate']-train_av_base['rate'],'hold_avail_base_R':hold_av_base['R'],'hold_avail_base_rate':hold_av_base['rate'],'hold_increment_pp':hm['rate']-hold_av_base['rate'],**{f'train_{k}':v for k,v in am.items()},**{f'hold_{k}':v for k,v in hm.items()}})
 g=pd.DataFrame(grid);g.to_csv(OUT/'grid.csv',index=False)
 cand=g[g.train_R>=35].copy();cand['goal35']=(cand.train_rate>=35).astype(int);cand=cand.sort_values(['goal35','train_rate','train_R'],ascending=[False,False,False]);best=cand.iloc[0]
 print('SELECTED_TRAIN_ONLY',best[['player_cut','feature','availability','q','cut','train_avail_base_R','train_avail_base_rate','train_R','train_rate','train_increment_pp']].to_dict());print('FIXED_HOLD',{'avail_base_R':int(best.hold_avail_base_R),'avail_base_rate':float(best.hold_avail_base_rate),'R':int(best.hold_R),'rate':float(best.hold_rate),'increment_pp':float(best.hold_increment_pp)})
 print('TOP10_TRAIN_ONLY');print(cand[['player_cut','feature','availability','cut','train_avail_base_rate','train_R','train_rate','train_increment_pp','hold_avail_base_rate','hold_R','hold_rate','hold_increment_pp']].head(10).to_string(index=False));print('Availability flags are audit/sample masks only, never predictive bonuses. September blind guard PASS; production untouched')
if __name__=='__main__':main()
