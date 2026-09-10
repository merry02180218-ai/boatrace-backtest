#!/usr/bin/env python3
"""v260: adaptive composite-odds target by 4-head probability.

Keep v96 opponent ranking fixed. Improve realized new ROI only through point-count selection.
For each race choose N=2..20 whose combined odds is closest to a target.
Adaptive policy: if POST >= split use target_hi_prob (wider tickets / lower target), else target_lo_prob.
Primary comparison uses Feb-Jun only; Jul/Aug remain non-pristine and secondary.
Research/model-selection only. Exact 10,000-yen Dutch/Hamilton settlement.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds
ROOT=Path(__file__).resolve().parent; BANK=10000
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'; OUT=ROOT/'analysis_v260_4head_adaptive_comp_target.csv'; SUM=ROOT/'summary_v260_4head_adaptive_comp_target.md'
PRE_CUTS=(.25,.26,.27,.28); POST_CUTS=(.24,.25,.26); SPLITS=np.round(np.arange(.28,.401,.02),2)
TARGETS=np.arange(8.0,14.01,.5); NS=range(2,21)

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
 for pc in PRE_CUTS:
  for qc in POST_CUTS:
   elig=[x for x in base if float(x[0].PRE)>=pc and float(x[0].POST)>=qc]
   for sp in SPLITS:
    for th in TARGETS:
     for tl in TARGETS:
      # High p4 should not be forced to fewer tickets than low p4: target_hi <= target_lo.
      if th>tl:continue
      vals=[]
      for r,ch in elig:
       target=th if float(r.POST)>=sp else tl
       n,hit,ret,comp=min(ch,key=lambda x:(abs(x[3]-target),x[0]))
       vals.append({'month':r.month,'n':n,'hit':hit,'ret':ret,'comp':comp,'target':target})
      if not vals:continue
      q=pd.DataFrame(vals);q6=q[q.month<='2026-06'];cost=len(q)*BANK;c6=len(q6)*BANK
      rows.append({'pre_cut':pc,'post_cut':qc,'split_post':sp,'target_high_p4':th,'target_low_p4':tl,'R':len(q),'avg_n':q.n.mean(),'avg_comp':q.comp.mean(),'hit_pct':100*q.hit.mean(),'roi_pct':100*q.ret.sum()/cost,'profit_yen':q.ret.sum()-cost,'R_feb_jun':len(q6),'roi_feb_jun_pct':100*q6.ret.sum()/c6 if c6 else np.nan,'hit_feb_jun_pct':100*q6.hit.mean() if len(q6) else np.nan})
 d=pd.DataFrame(rows);d.to_csv(OUT,index=False)
 v=d[(d.R>=120)&(d.R<=180)&(d.R_feb_jun>=90)].copy();v['robust_score']=np.minimum(v.roi_pct,v.roi_feb_jun_pct)
 v=v.sort_values(['robust_score','roi_feb_jun_pct','roi_pct'],ascending=False)
 L=['# v260 4-head adaptive composite target','', '- v96 opponent ranking is fixed; only ticket count is changed.','- N=2..20, exact 10,000-yen inverse-odds Dutch/Hamilton.','- POST probability split chooses between two composite-odds targets.','- Primary evidence is Feb-Jun; Jul/Aug are non-pristine secondary evidence.','- retrospective model-selection only.','', '## Best robust 120-180R policies','|PRE|POST|split|high-p4 target|low-p4 target|R|avgN|avgComp|hit|ROI|Feb-Jun R|Feb-Jun hit|Feb-Jun ROI|min ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for _,r in v.head(50).iterrows():L.append(f'|{r.pre_cut:.2f}|{r.post_cut:.2f}|{r.split_post:.2f}|{r.target_high_p4:.1f}|{r.target_low_p4:.1f}|{int(r.R)}|{r.avg_n:.2f}|{r.avg_comp:.3f}|{r.hit_pct:.2f}%|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.hit_feb_jun_pct:.2f}%|{r.roi_feb_jun_pct:.2f}%|{r.robust_score:.2f}%|')
 # Focus on current two main gates.
 for pc,qc,name in [(.28,.25,'GATE_123R'),(.25,.25,'GATE_156R')]:
  z=d[(d.pre_cut==pc)&(d.post_cut==qc)].copy();z['robust_score']=np.minimum(z.roi_pct,z.roi_feb_jun_pct);z=z.sort_values(['robust_score','roi_feb_jun_pct'],ascending=False)
  L += ['',f'## {name} best adaptive policies','|split|high target|low target|R|avgN|hit|ROI|Feb-Jun ROI|min ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
  for _,r in z.head(20).iterrows():L.append(f'|{r.split_post:.2f}|{r.target_high_p4:.1f}|{r.target_low_p4:.1f}|{int(r.R)}|{r.avg_n:.2f}|{r.hit_pct:.2f}%|{r.roi_pct:.2f}%|{r.roi_feb_jun_pct:.2f}%|{r.robust_score:.2f}%|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
