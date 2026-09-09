#!/usr/bin/env python3
"""v257: extend v256 variable TopN composite-odds target from 10 to 15.
Research/model-selection only; Jul/Aug NON-PRISTINE. Exact 10k Dutch settlement.
"""
from pathlib import Path
import numpy as np,pandas as pd
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds
ROOT=Path(__file__).resolve().parent;BANK=10000
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv';OUT=ROOT/'analysis_v257_4head_variable_comp10to15.csv';SUM=ROOT/'summary_v257_4head_variable_comp10to15.md'
CUTS=np.round(np.arange(.15,.321,.01),2);TARGETS=np.arange(10.0,15.01,.5);NS=range(2,21)
def main():
 p=pd.read_csv(PRED,dtype={'race_code':str});p.race_code=p.race_code.str.zfill(12)
 w=p.pivot_table(index=['date','month','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index()
 rs=c4.read();orders=v251.pair_orders(rs);am=v251.actual_map(rs);od=load_odds();oi=od.set_index('race_code',drop=False)
 base=[]
 for _,r in w.iterrows():
  code=str(r.race_code).zfill(12);order=orders.get((str(r.date),code));a=am.get((str(r.date),code))
  if not order or not a or a[3]!=1 or code not in oi.index:continue
  o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
  ch=[]
  for n in NS:
   s=v251.settle(code,[f'4-{x}-{y}' for x,y in order[:n]],o,a)
   if s is not None:ch.append((n,*s))
  if ch:base.append((r,ch))
 rows=[]
 for pc in CUTS:
  for qc in CUTS:
   elig=[x for x in base if float(x[0].PRE)>=pc and float(x[0].POST)>=qc]
   for target in TARGETS:
    vals=[]
    for r,ch in elig:
     n,hit,ret,comp=min(ch,key=lambda x:(abs(x[3]-target),x[0]))
     vals.append({'month':r.month,'n':n,'hit':hit,'ret':ret,'comp':comp})
    if not vals:continue
    q=pd.DataFrame(vals);cost=len(q)*BANK;ret=q.ret.sum();q6=q[q.month<='2026-06'];c6=len(q6)*BANK
    rows.append({'pre_cut':pc,'post_cut':qc,'target_comp':target,'R':len(q),'avg_n':q.n.mean(),'avg_comp':q.comp.mean(),'hit_pct':100*q.hit.mean(),'roi_pct':100*ret/cost,'profit_yen':ret-cost,'R_feb_jun':len(q6),'roi_feb_jun_pct':100*q6.ret.sum()/c6 if c6 else np.nan})
 d=pd.DataFrame(rows);d.to_csv(OUT,index=False)
 v=d[(d.R>=120)&(d.R<=180)].sort_values(['roi_feb_jun_pct','roi_pct'],ascending=False)
 L=['# v257 4-head variable TopN / composite target 10-15','', '- N=2..20から各レースで目標合成オッズに最も近いNを選択。','- 目標10.0〜15.0を0.5刻み。PRE/POST 0.15〜0.32を0.01刻み。','- 主対象120〜180R。1R10,000円 inverse-odds Dutch / Hamilton。','- retrospective model-selection evidence。Jul/Aug NON-PRISTINE。','', '## Best 120-180R cells','|PRE|POST|target|R|avg N|avg comp|hit|profit|ROI|Feb-Jun R|Feb-Jun ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for _,r in v.head(50).iterrows():L.append(f'|{r.pre_cut:.2f}|{r.post_cut:.2f}|{r.target_comp:.1f}|{int(r.R)}|{r.avg_n:.2f}|{r.avg_comp:.3f}|{r.hit_pct:.2f}%|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.roi_feb_jun_pct:.2f}%|')
 for pc,qc,label in [(.28,.25,'PRE>=0.28 / POST>=0.25'),(.25,.25,'PRE>=0.25 / POST>=0.25')]:
  L+=['',f'## Target comparison at {label}','|target|R|avg N|avg comp|hit|ROI|Feb-Jun ROI|','|---:|---:|---:|---:|---:|---:|---:|']
  for _,r in d[(d.pre_cut==pc)&(d.post_cut==qc)].sort_values('target_comp').iterrows():L.append(f'|{r.target_comp:.1f}|{int(r.R)}|{r.avg_n:.2f}|{r.avg_comp:.3f}|{r.hit_pct:.2f}%|{r.roi_pct:.2f}%|{r.roi_feb_jun_pct:.2f}%|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
