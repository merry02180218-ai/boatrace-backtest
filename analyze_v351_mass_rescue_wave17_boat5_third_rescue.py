#!/usr/bin/env python3
"""Wave17: frozen audit of BOAT3_STRONGER -> boat5 as THIRD rescue.

Historical post-ranking/ticket-rescue research only.
- Eligibility uses only pre-result corrected exhibition/ST structure.
- Feb-Apr discovers the SECOND partner and fixed-3 replacement slot.
- May/June are frozen validation months.
- September 2026 outcomes/payouts are hard forbidden.
- Production is unchanged.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
import numpy as np
import pandas as pd
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct
import run_v326_1head_ticketaware_exhibition as v326
import research_v351_mass_rescue_wave12_frozen_guard as w12

SRC='analysis_v351_mass_rescue_wave10_rows.csv'
LO,HI=.350,.375
SCHEMAS={'lap+turn+straight','lap+turn'}
RANKS=['ex_rank','st_rank','turn_rank','straight_rank','orig_avg_rank']
SECOND_CHOICES=[2,3,4,6]
CLEAR=0.50


def combo(x):
 p=str(x).replace('>','-').replace(' ','').split('-')
 return tuple(map(int,p[:3])) if len(p)>=3 and all(z.isdigit() for z in p[:3]) else None


def tickets(x):
 out=[]
 for q in str(x).replace('|',';').replace(',',';').split(';'):
  c=combo(q)
  if c and c[0]==1: out.append(c)
 return out


def build_pre_result_strength(base):
 wanted=set(base.race_code)
 days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted})
 dayset=set(days); last=max(days)
 sums=defaultdict(list); allv=[]; feat={}; d=date(2025,10,1)
 while d<=last:
  ymd=d.strftime('%Y/%m/%d'); strows=rows(f'data/previews/stt/{ymd}.csv'); bias=v326.st_bias(sums,allv)
  if d in dayset:
   tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv')); stt=v326.bycode(strows); orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(2,7):
     if b in ex and b in st:
      o=os.get(b,{})
      feat[(code,b)]={'ex':ex[b],'st':st[b],'turn':o.get('turn',np.nan),'straight':o.get('straight',np.nan),'orig_avg':o.get('avg',np.nan)}
  v326.update_st(strows,sums,allv); d+=timedelta(days=1)
 rec=[]
 for code in wanted:
  for b in range(2,7):
   f=feat.get((code,b))
   if f is not None: rec.append({'race_code':code,'boat':b,**f})
 z=pd.DataFrame(rec)
 if z.empty: raise RuntimeError('no pre-result feature rows')
 z['ex_rank']=z.groupby('race_code').ex.rank(method='average',ascending=True)
 z['st_rank']=z.groupby('race_code').st.rank(method='average',ascending=True)
 for c in ['turn','straight','orig_avg']:
  z[c+'_rank']=z.groupby('race_code')[c].rank(method='average',ascending=True)
 z['strength_rank_mean']=z[RANKS].mean(axis=1,skipna=True)
 return z


def make_rows(base,feat):
 fi=feat.set_index(['race_code','boat']); out=[]
 for _,r in base.iterrows():
  code=r.race_code
  if (code,2) not in fi.index or (code,3) not in fi.index: continue
  s2=float(fi.loc[(code,2)].strength_rank_mean); s3=float(fi.loc[(code,3)].strength_rank_mean)
  diff=s2-s3
  # BOAT3_STRONGER means boat3 has the lower/better mean corrected rank.
  eligible=(diff>=CLEAR)
  a=combo(r.actual_combo); ts=tickets(r.tickets)
  if not a or len(ts)<3: continue
  ts=ts[:3]
  out.append({'race_code':code,'month':code[:6],'schema':r.schema,'jcd':int(r.jcd),'opp_mass':float(r.opp_mass),
              'head_hit':int(a[0]==1),'actual_combo':'-'.join(map(str,a)),'actual_second':int(a[1]),'actual_third':int(a[2]),
              'strength2':s2,'strength3':s3,'strength2_minus3':diff,'eligible':int(eligible),
              't1':'-'.join(map(str,ts[0])),'t2':'-'.join(map(str,ts[1])),'t3':'-'.join(map(str,ts[2])),
              'baseline_hit':int(a in ts)})
 return pd.DataFrame(out)


def eval_policy(g,second_boat,replace_slot):
 rec=[]; cand=(1,int(second_boat),5)
 for _,r in g.iterrows():
  a=combo(r.actual_combo); ts=[combo(r.t1),combo(r.t2),combo(r.t3)]
  bh=int(a in ts); ch=int(a==cand)
  add_hit=int(bh or ch); add_rescue=int((not bh) and ch)
  mod=list(ts); override=int(cand not in mod)
  if override: mod[int(replace_slot)]=cand
  fh=int(a in mod); rescue=int((not bh) and fh); damage=int(bh and (not fh))
  rec.append({**r.to_dict(),'candidate':'-'.join(map(str,cand)),'replace_slot':int(replace_slot)+1,'candidate_hit':ch,
              'add4_hit':add_hit,'add4_rescue':add_rescue,'fixed3_override':override,'fixed3_hit':fh,
              'fixed3_rescue':rescue,'fixed3_damage':damage})
 return pd.DataFrame(rec)


def summary(label,q):
 R=len(q)
 return {'scope':label,'R':R,'HEAD_hits':int(q.head_hit.sum()),'baseline_hits':int(q.baseline_hit.sum()),
         'baseline_rate':100*q.baseline_hit.mean() if R else np.nan,
         'candidate_hits':int(q.candidate_hit.sum()),'candidate_rate':100*q.candidate_hit.mean() if R else np.nan,
         'add4_hits':int(q.add4_hit.sum()),'add4_rescues':int(q.add4_rescue.sum()),'add4_delta':int(q.add4_hit.sum()-q.baseline_hit.sum()),
         'fixed3_overrides':int(q.fixed3_override.sum()),'fixed3_hits':int(q.fixed3_hit.sum()),
         'fixed3_rescues':int(q.fixed3_rescue.sum()),'fixed3_damages':int(q.fixed3_damage.sum()),
         'fixed3_net':int(q.fixed3_rescue.sum()-q.fixed3_damage.sum()),
         'fixed3_delta':int(q.fixed3_hit.sum()-q.baseline_hit.sum())}


def main():
 base=pd.read_csv(SRC,dtype={'race_code':str}); base.race_code=base.race_code.astype(str).str.zfill(12)
 if (base.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
 base=base[(base.opp_mass>=LO)&(base.opp_mass<HI)&base.schema.isin(SCHEMAS)].copy()
 if base.empty: raise RuntimeError('empty low-mass main-schema population')
 feat=build_pre_result_strength(base); allr=make_rows(base,feat)
 if (allr.race_code.str[:8]>='20260901').any(): raise RuntimeError('September row after feature build')
 elig=allr[allr.eligible.eq(1)].copy()
 train=elig[elig.month.isin(['202602','202603','202604'])].copy()
 if train.empty: raise RuntimeError('empty Feb-Apr discovery set')
 # Discover SECOND partner and replacement slot strictly on Feb-Apr by fixed-3 net;
 # tie-break: more rescues, fewer damages, lower second boat, later slot (drop rank3 first).
 grid=[]
 for sb in SECOND_CHOICES:
  for slot in range(3):
   q=eval_policy(train,sb,slot); s=summary('TRAIN',q)
   grid.append({'second_boat':sb,'replace_slot':slot+1,**s})
 gd=pd.DataFrame(grid)
 best=gd.sort_values(['fixed3_net','fixed3_rescues','fixed3_damages','second_boat','replace_slot'],ascending=[False,False,True,True,False]).iloc[0]
 chosen_second=int(best.second_boat); chosen_slot=int(best.replace_slot)-1
 gd['selected']=((gd.second_boat==chosen_second)&(gd.replace_slot==chosen_slot+1)).astype(int)
 gd.to_csv('analysis_v351_mass_rescue_wave17_discovery_grid.csv',index=False,encoding='utf-8-sig')

 rows_out=[]; sums=[]
 for m in ['202602','202603','202604','202605','202606']:
  g=elig[elig.month.eq(m)].copy(); q=eval_policy(g,chosen_second,chosen_slot) if len(g) else pd.DataFrame()
  if len(q): rows_out.append(q); sums.append({'month':m,**summary(m,q)})
 if not rows_out: raise RuntimeError('no Wave17 evaluated rows')
 detail=pd.concat(rows_out,ignore_index=True); sm=pd.DataFrame(sums)
 detail.to_csv('analysis_v351_mass_rescue_wave17_rows.csv',index=False,encoding='utf-8-sig')
 sm.to_csv('analysis_v351_mass_rescue_wave17_monthly.csv',index=False,encoding='utf-8-sig')
 frozen=detail[detail.month.isin(['202605','202606'])].copy()
 fs=pd.DataFrame([summary('MAY_JUNE_FROZEN',frozen)])
 fs.to_csv('analysis_v351_mass_rescue_wave17_frozen_summary.csv',index=False,encoding='utf-8-sig')

 print('SEPTEMBER_OUTCOMES_USED False')
 print('PRODUCTION_CHANGED False')
 print('HEAD_EXHIBITION_DIRECT_FEATURE False')
 print('RESEARCH_BAND',LO,HI,'BELOW_PRODUCTION_OPPONENT_MASS_CUTOFF_0.375 True')
 print('IMPORTANT 276R production purchases are not directly modified by this audit; this is a below-cutoff expansion/rescue study.')
 print('ELIGIBILITY outcome_independent BOAT3_STRONGER CLEAR_>=0.50')
 print('DISCOVERY Feb-Apr; FROZEN May-Jun')
 print('CHOSEN_SECOND',chosen_second,'CHOSEN_REPLACE_SLOT',chosen_slot+1,'CANDIDATE',f'1-{chosen_second}-5')
 print('\nDISCOVERY_GRID'); print(gd.to_string(index=False))
 print('\nMONTHLY'); print(sm.to_string(index=False))
 print('\nFROZEN_MAY_JUNE'); print(fs.to_string(index=False))
 print('\nNOTE add4 = baseline 3 tickets plus candidate (no damage by construction). fixed3 = replace one frozen slot, so rescue/damage/net are directly comparable.')

if __name__=='__main__': main()
