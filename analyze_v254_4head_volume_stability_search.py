#!/usr/bin/env python3
"""v254 research: 4-head volume/stability search.

Goal: avoid over-selecting a tiny high-ROI cell. Search PRE/POST thresholds finely,
keep FIXED2 tickets, and prioritize 120-180 settled races plus monthly stability.
All outputs are retrospective model-selection evidence; Jul/Aug are NON-PRISTINE.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v254_4head_volume_stability_search.csv'
SUM=ROOT/'summary_v254_4head_volume_stability_search.md'
BANK=10000
CUTS=np.round(np.arange(.15,.321,.01),2)

def main():
 p=pd.read_csv(PRED,dtype={'race_code':str});p['race_code']=p.race_code.str.zfill(12)
 w=p.pivot_table(index=['date','month','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index()
 rs=c4.read();orders=v251.pair_orders(rs);am=v251.actual_map(rs)
 od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
 rows=[]
 for _,r in w.iterrows():
  code=str(r.race_code).zfill(12);k=(str(r.date),code);order=orders.get(k);a=am.get(k)
  if not order or not a or a[3]!=1 or code not in oi.index: continue
  o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
  ts=[f'4-{x}-{y}' for x,y in order[:2]]
  s=v251.settle(code,ts,o,a)
  if s is None: continue
  hit,ret,comp=s
  rows.append({'date':r.date,'month':r.month,'race_code':code,'pre':float(r.PRE),'post':float(r.POST),'hit':hit,'return_yen':ret,'comp_odds':comp,'head4':int(a[0]==4)})
 z=pd.DataFrame(rows)
 out=[]
 for pc in CUTS:
  for qc in CUTS:
   q=z[(z.pre>=pc)&(z.post>=qc)]
   if q.empty: continue
   cost=len(q)*BANK;ret=q.return_yen.sum();months=[]
   for m,g in q.groupby('month'):
    months.append((m,len(g),100*g.return_yen.sum()/(len(g)*BANK),100*g.hit.mean()))
   q6=q[q.month<='2026-06'];c6=len(q6)*BANK;r6=q6.return_yen.sum()
   monthly_rois=[x[2] for x in months]
   profitable=sum(x>=100 for x in monthly_rois)
   out.append({'pre_cut':pc,'post_cut':qc,'R':len(q),'head4_rate_pct':100*q.head4.mean(),'hit_rate_pct':100*q.hit.mean(),'avg_comp_odds':q.comp_odds.mean(),'profit_yen':ret-cost,'roi_pct':100*ret/cost,'R_feb_jun':len(q6),'roi_feb_jun_pct':100*r6/c6 if c6 else np.nan,'hit_feb_jun_pct':100*q6.hit.mean() if len(q6) else np.nan,'profitable_months':profitable,'months_present':len(months),'min_month_roi_pct':min(monthly_rois) if monthly_rois else np.nan,'median_month_roi_pct':np.median(monthly_rois) if monthly_rois else np.nan})
 d=pd.DataFrame(out);d.to_csv(OUT,index=False)
 vol=d[(d.R>=120)&(d.R<=180)].copy()
 # Rank by robustness first: Feb-Jun ROI, all ROI, sample size; no claim of pristine validation.
 vol=vol.sort_values(['roi_feb_jun_pct','roi_pct','R'],ascending=[False,False,False])
 L=['# v254 4-head volume/stability search','', '- FIXED2のみ。PRE/POSTを0.01刻みで探索。','- 主対象は120〜180R。1R10,000円Hamilton Dutch、外れは-10,000円。','- Feb-Junもpristineではなくrobustness参考。Jul/AugはNON-PRISTINE。','- 最高ROIをそのままproduction採用しない。','', '## Best volume cells (120-180R)','|PRE|POST|R|4-head|hit|avg comp|profit|ROI|Feb-Jun R|Feb-Jun ROI|profitable months|median month ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for _,r in vol.head(30).iterrows():
  L.append(f'|{r.pre_cut:.2f}|{r.post_cut:.2f}|{int(r.R)}|{r.head4_rate_pct:.2f}%|{r.hit_rate_pct:.2f}%|{r.avg_comp_odds:.3f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.roi_feb_jun_pct:.2f}%|{int(r.profitable_months)}/{int(r.months_present)}|{r.median_month_roi_pct:.2f}%|')
 robust=vol[(vol.roi_pct>=100)&(vol.roi_feb_jun_pct>=100)&(vol.R_feb_jun>=90)].sort_values(['R','roi_feb_jun_pct'],ascending=[False,False])
 L += ['','## Volume-first robustness shortlist','- 条件: 120-180R、全期間ROI>=100%、Feb-Jun ROI>=100%、Feb-Jun>=90R。','|PRE|POST|R|hit|ROI|Feb-Jun R|Feb-Jun hit|Feb-Jun ROI|profitable months|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 if robust.empty:L.append('|—|—|—|—|—|—|—|—|該当なし|')
 else:
  for _,r in robust.head(30).iterrows():L.append(f'|{r.pre_cut:.2f}|{r.post_cut:.2f}|{int(r.R)}|{r.hit_rate_pct:.2f}%|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.hit_feb_jun_pct:.2f}%|{r.roi_feb_jun_pct:.2f}%|{int(r.profitable_months)}/{int(r.months_present)}|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
