#!/usr/bin/env python3
"""Audit 3HEAD adopted A+.60 opponent ranking using 1HEAD/4HEAD role-split references.
Development only: Nov-Jan. March is not used for selection. Sep-2026 outcomes unread.
This stage freezes the cohort and measures current V221 ordered-pair coverage before rebuilding SECOND/THIRD.
"""
import json, pandas as pd
from run_3head_a_loss_structure_dev import DEV,A,mask
from run_3head_wave20_manual_gate import prep_month,prefetch_sources,build_motor_exhibition,build_pre_enhanced,make_pre_scores
from run_3head_funsite_broad50_wave6 import fetch

def main():
 raw={}
 for k,(a,b) in DEV.items():
  x,r,audit=build_pre_enhanced(a,b,True); raw[k]=(x,r,audit)
 frames={k:prep_month(x,r) for k,(x,r,_) in raw.items()}
 scores,_=make_pre_scores(frames); days,cache=prefetch_sources(); post,_=build_motor_exhibition(days,cache)
 rec=[]
 for k in ['nov','dec','jan']:
  d=scores[k].merge(post,on=['rc','date'],how='left',validate='one_to_one')
  rn=pd.to_numeric(d.race_no,errors='coerce'); pre=pd.to_numeric(d.pre_score,errors='coerce')
  m=(rn>=1)&(rn<=12)&(pre>=.925)&mask(d,A['conds'])&(pd.to_numeric(d.post_motor_inner_rank_edge,errors='coerce')>=.60)
  q=d[m].copy()
  if len(q)==0: continue
  # Settlement winner only for conditional opponent diagnostics; never a feature.
  # build exact 1st/2nd/3rd settlement from the same realtime result source; build_pre_enhanced only retains winner.
  ds=pd.to_datetime(q.date).dt.date.unique(); settled=[]
  for day in ds:
   for rr in fetch('results/realtime',day):
    code=str(rr.get('レースコード','')).strip()
    a=[str(rr.get(f'{i}着_艇番','')).strip() for i in (1,2,3)]
    if code.isdigit() and all(x in {'1','2','3','4','5','6'} for x in a):
     settled.append({'rc':int(code),'winner':int(a[0]),'second':int(a[1]),'third':int(a[2])})
  sm=pd.DataFrame(settled).drop_duplicates('rc')
  if sm.empty: raise RuntimeError('no full trifecta settlement rows')
  try: sm['rc']=sm['rc'].astype(q.rc.dtype)
  except: sm['rc']=pd.to_numeric(sm.rc,errors='coerce').astype(q.rc.dtype)
  q=q.merge(sm,on='rc',how='left',validate='one_to_one'); q['month']=k
  rec.append(q[['rc','month','winner','second','third']])
 z=pd.concat(rec,ignore_index=True)
 if len(z)!=118: raise RuntimeError(f'cohort drift {len(z)}')
 zw=z[pd.to_numeric(z.winner,errors='coerce')==3].copy()
 out={'policy':{'cohort':'frozen 3HEAD A + purchase .60','development':['2025-11','2025-12','2026-01'],'march_used_for_selection':False,'september_2026_used':False},
      'cohort':{'n':len(z),'head3_wins':len(zw),'head_rate':len(zw)/len(z)},
      'opponent_targets':{'head3_win_races':len(zw),'second_counts':zw.second.astype(str).value_counts().to_dict(),'third_counts':zw.third.astype(str).value_counts().to_dict()},
      'next_model':{'reference_1head':'v317 SECOND + v318 THIRD; factorized preferred over v319 direct pair','reference_4head':'v280/v281 role split + scenario THIRD; v283 TOP2XTOP2 pair ordering','plan':'build separate SECOND and conditional THIRD models on this frozen cohort; compare TOP2xTOP2 and conditional pair order; no odds until coverage is frozen'}}
 open('research_3head_a_opponent_reference_audit.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
