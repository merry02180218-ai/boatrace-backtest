#!/usr/bin/env python3
"""Develop loss-structure diagnostics on Nov-Jan only for frozen 3HEAD A + purchase .60.
No March tuning; no Sep-2026 outcomes.
"""
import json, pandas as pd, numpy as np
from run_3head_a_purchase_gate_dev import DEV,A,mask
from run_3head_wave20_manual_gate import prep_month,prefetch_sources,build_motor_exhibition,build_pre_enhanced,make_pre_scores

FEATURES=['post_st_edge1','post_st_edge2','post_st_inner_edge','post_st_rank3',
'post_ex_edge1','post_ex_edge2','post_ex_inner_edge',
'post_motor_rank_edge1','post_motor_rank_edge2','post_motor_inner_rank_edge',
'post_motor_st_edge1','post_motor_st_edge2',
'post_turn_edge1','post_turn_edge2','post_turn_inner_edge',
'post_straight_edge1','post_straight_edge2','post_straight_inner_edge',
'post_lap_edge1','post_lap_edge2','post_lap_inner_edge']

def stat(x,c):
 q=pd.to_numeric(x[c],errors='coerce'); a=q[x.y==1].dropna(); b=q[x.y==0].dropna()
 return {'feature':c,'head_n':len(a),'loss_n':len(b),'head_median':float(a.median()) if len(a) else None,
 'loss_median':float(b.median()) if len(b) else None,'delta_loss_minus_head':float(b.median()-a.median()) if len(a) and len(b) else None}

def main():
 raw={}
 for k,(a,b) in DEV.items():
  x,r,audit=build_pre_enhanced(a,b,True);raw[k]=(x,r,audit)
 frames={k:prep_month(x,r) for k,(x,r,_) in raw.items()}
 # prep_month intentionally reduces settlement to binary y; attach winner only for this diagnostic.
 for k,(x,r,_) in raw.items():
  rr=r.copy(); wcol='winner' if 'winner' in rr.columns else ('result_winner' if 'result_winner' in rr.columns else None)
  if wcol is None: raise RuntimeError(f'no winner column in raw result for {k}: {list(rr.columns)}')
  key='rc' if 'rc' in rr.columns else 'race_code'
  wm=rr[[key,wcol]].copy().rename(columns={key:'rc',wcol:'diag_winner'}); wm['rc']=wm.rc.astype(str)
  frames[k]['rc']=frames[k].rc.astype(str); frames[k]=frames[k].merge(wm,on='rc',how='left',validate='one_to_one')
 scores,_=make_pre_scores(frames);days,cache=prefetch_sources();post,_=build_motor_exhibition(days,cache)
 rows=[]
 for k in ['nov','dec','jan']:
  d=scores[k].merge(post,on=['rc','date'],how='left',validate='one_to_one')
  rn=pd.to_numeric(d.race_no,errors='coerce');pre=pd.to_numeric(d.pre_score,errors='coerce')
  m=(rn>=1)&(rn<=12)&(pre>=.925)&mask(d,A['conds'])&(pd.to_numeric(d.post_motor_inner_rank_edge,errors='coerce')>=.60)
  q=d[m].copy();q['month']=k;rows.append(q)
 z=pd.concat(rows,ignore_index=True)
 if len(z)!=118 or int(z.y.sum())!=54: raise RuntimeError(f'frozen dev drift {len(z)}/{int(z.y.sum())}')
 stats=[stat(z,c) for c in FEATURES if c in z]
 # Directly isolate the dominant failure mode: boat1 wins vs boat3 wins.
 rw=pd.to_numeric(z['diag_winner'],errors='coerce')
 z13=z[(rw==1)|(rw==3)].copy(); z13['target3']=(rw.loc[z13.index]==3).astype(int)
 direct=[]
 for c in FEATURES:
  if c not in z13: continue
  q=pd.to_numeric(z13[c],errors='coerce'); a=q[z13.target3==1].dropna(); b=q[z13.target3==0].dropna()
  direct.append({'feature':c,'head3_n':len(a),'boat1win_n':len(b),'head3_median':float(a.median()) if len(a) else None,'boat1win_median':float(b.median()) if len(b) else None,'boat1_minus_head3':float(b.median()-a.median()) if len(a) and len(b) else None})
 direct=sorted(direct,key=lambda r:abs(r['boat1_minus_head3'] or 0),reverse=True)
 # descriptive thresholds from development quantiles; report kept volume/head rate, not auto-adopt.
 tails=[]
 for c in FEATURES:
  if c not in z:continue
  q=pd.to_numeric(z[c],errors='coerce'); 
  if q.notna().sum()<50:continue
  for pct in [.20,.25,.33,.67,.75,.80]:
   t=float(q.quantile(pct))
   for op in ['ge','le']:
    m=(q>=t) if op=='ge' else (q<=t); n=int(m.sum())
    if n<60:continue
    h=int(z.loc[m,'y'].sum())
    month_min=min(int(m[z.month==mon].sum()) for mon in ['nov','dec','jan'])
    tails.append({'feature':c,'op':op,'threshold':t,'n':n,'heads':h,'head_rate':h/n,'month_min_n':month_min})
 tails=sorted(tails,key=lambda r:(r['head_rate'],r['n']),reverse=True)
 out={'policy':{'A_frozen':True,'purchase_gate_min':.60,'development':['2025-11','2025-12','2026-01'],'march_used_for_selection':False,'september_2026_used':False},
 'baseline':{'n':len(z),'heads':int(z.y.sum()),'head_rate':float(z.y.mean()),'boat1_wins':int((rw==1).sum())},'boat3_vs_boat1_direct':direct,'feature_head_vs_loss':stats,'descriptive_tail_top40':tails[:40]}
 open('research_3head_a_loss_structure_dev.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
