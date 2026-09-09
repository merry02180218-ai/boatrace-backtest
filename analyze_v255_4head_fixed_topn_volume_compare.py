#!/usr/bin/env python3
"""v255 research: compare fixed TopN=2..10 for 4-head model under volume-aware PRE/POST gates.

Retrospective model-selection only. Jul/Aug are NON-PRISTINE; Feb-Jun are also not pristine.
Exact 10,000-yen inverse-odds Dutch settlement via v251.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v255_4head_fixed_topn_volume_compare.csv'
SUM=ROOT/'summary_v255_4head_fixed_topn_volume_compare.md'
BANK=10000
CUTS=np.round(np.arange(.15,.321,.01),2)
NS=range(2,11)

def main():
 p=pd.read_csv(PRED,dtype={'race_code':str}); p['race_code']=p.race_code.str.zfill(12)
 w=p.pivot_table(index=['date','month','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index()
 rs=c4.read(); orders=v251.pair_orders(rs); am=v251.actual_map(rs)
 od=load_odds(); oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
 rows=[]
 for _,r in w.iterrows():
  code=str(r.race_code).zfill(12); k=(str(r.date),code); order=orders.get(k); a=am.get(k)
  if not order or not a or a[3]!=1 or code not in oi.index: continue
  o=oi.loc[code]; o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
  for n in NS:
   ts=[f'4-{x}-{y}' for x,y in order[:n]]
   s=v251.settle(code,ts,o,a)
   if s is None: continue
   hit,ret,comp=s
   rows.append({'date':r.date,'month':r.month,'race_code':code,'pre':float(r.PRE),'post':float(r.POST),'n':n,'hit':hit,'return_yen':ret,'comp_odds':comp,'head4':int(a[0]==4)})
 z=pd.DataFrame(rows)
 out=[]
 for n in NS:
  zn=z[z.n==n]
  for pc in CUTS:
   for qc in CUTS:
    q=zn[(zn.pre>=pc)&(zn.post>=qc)]
    if q.empty: continue
    ret=q.return_yen.sum(); cost=len(q)*BANK
    q6=q[q.month<='2026-06']; r6=q6.return_yen.sum(); c6=len(q6)*BANK
    mroi=[]
    for m,g in q.groupby('month'): mroi.append(100*g.return_yen.sum()/(len(g)*BANK))
    out.append({'n':n,'pre_cut':pc,'post_cut':qc,'R':len(q),'head4_rate_pct':100*q.head4.mean(),'hit_rate_pct':100*q.hit.mean(),'avg_comp_odds':q.comp_odds.mean(),'profit_yen':ret-cost,'roi_pct':100*ret/cost,'R_feb_jun':len(q6),'hit_feb_jun_pct':100*q6.hit.mean() if len(q6) else np.nan,'roi_feb_jun_pct':100*r6/c6 if c6 else np.nan,'profitable_months':sum(x>=100 for x in mroi),'months_present':len(mroi),'median_month_roi_pct':np.median(mroi) if mroi else np.nan})
 d=pd.DataFrame(out); d.to_csv(OUT,index=False)
 L=['# v255 4-head fixed TopN volume comparison','', '- TopN=2〜10固定を同一PRE/POSTグリッドで比較。','- 主対象120〜180R。1R10,000円 inverse-odds Dutch、100円Hamilton。','- Feb-Junもpristineではなくrobustness参考。Jul/AugはNON-PRISTINE。','', '## Best cell by N within 120-180R','|N|PRE|POST|R|hit|avg comp|profit|ROI|Feb-Jun R|Feb-Jun hit|Feb-Jun ROI|profitable months|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for n in NS:
  q=d[(d.n==n)&(d.R>=120)&(d.R<=180)].copy()
  if q.empty: continue
  q=q.sort_values(['roi_feb_jun_pct','roi_pct','R'],ascending=[False,False,False])
  r=q.iloc[0]
  L.append(f'|{n}|{r.pre_cut:.2f}|{r.post_cut:.2f}|{int(r.R)}|{r.hit_rate_pct:.2f}%|{r.avg_comp_odds:.3f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.hit_feb_jun_pct:.2f}%|{r.roi_feb_jun_pct:.2f}%|{int(r.profitable_months)}/{int(r.months_present)}|')
 L += ['','## Robust cells across all N','- 条件: 120-180R、全期間ROI>=100%、Feb-Jun ROI>=100%、Feb-Jun>=90R。','|N|PRE|POST|R|hit|ROI|Feb-Jun R|Feb-Jun ROI|avg comp|profitable months|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 q=d[(d.R>=120)&(d.R<=180)&(d.roi_pct>=100)&(d.roi_feb_jun_pct>=100)&(d.R_feb_jun>=90)].sort_values(['roi_feb_jun_pct','roi_pct','R'],ascending=[False,False,False])
 if q.empty: L.append('|—|—|—|—|—|—|—|—|—|該当なし|')
 else:
  for _,r in q.head(40).iterrows(): L.append(f'|{int(r.n)}|{r.pre_cut:.2f}|{r.post_cut:.2f}|{int(r.R)}|{r.hit_rate_pct:.2f}%|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.roi_feb_jun_pct:.2f}%|{r.avg_comp_odds:.3f}|{int(r.profitable_months)}/{int(r.months_present)}|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
