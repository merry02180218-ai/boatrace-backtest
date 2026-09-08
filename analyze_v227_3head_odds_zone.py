#!/usr/bin/env python3
"""v227 exploratory odds-zone robustness audit.
Historical closing odds are intentionally used by explicit exception. Discovery only, not pristine validation.
Consumes v226 race-level output and studies Top10 composite-odds bands jointly with p3/estimated hit probability.
"""
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v226_3head_closing_odds_exploration.csv'
OUT=ROOT/'analysis_v227_3head_odds_zone.csv'; SUM=ROOT/'summary_v227_3head_odds_zone.md'; BANK=10000
COMP_BINS=[0,2.0,2.25,2.5,2.75,3.0,3.25,3.5,4.0,99]
P_BINS=[0,.30,.35,.40,.45,.50,.60,1.01]
EH_BINS=[0,.20,.25,.30,.35,.40,.45,.50,1.01]
def metrics(g):
 if len(g)==0:return None
 r=len(g); roi=100*g.ret.sum()/(r*BANK); prof=g.ret.sum()-r*BANK
 s=g.sort_values(['date','race_code']).profit.cumsum(); dd=(s.cummax()-s).max() if len(s) else 0
 losses=(g.sort_values(['date','race_code']).hit.eq(0)).astype(int); maxloss=cur=0
 for x in losses:
  cur=cur+1 if x else 0;maxloss=max(maxloss,cur)
 monthly=[]
 for m,x in g.groupby('month'):
  monthly.append((m,len(x),100*x.ret.sum()/(len(x)*BANK)))
 profm=sum(x[2]>=100 for x in monthly)
 # remove largest payouts, preserving each removed race as a full 10k wager deletion
 rr=[]
 for k in [1,3,5]:
  q=g.nlargest(k,'ret').index; h=g.drop(q); rr.append(100*h.ret.sum()/(len(h)*BANK) if len(h) else np.nan)
 return dict(R=r,hit=100*g.hit.mean(),avg_comp=g.comp.mean(),avg_p3=g.p3.mean(),avg_est_hit=g.est_hit.mean(),avg_ev=g.ev.mean(),ROI=roi,profit=prof,maxDD=dd,maxL=maxloss,prof_months=profm,months=len(monthly),rm1=rr[0],rm3=rr[1],rm5=rr[2],monthly=';'.join(f'{m}:{n}:{v:.1f}' for m,n,v in monthly))
def main():
 z=pd.read_csv(SRC,dtype={'race_code':str});z=z[(z.n==10)&z.fully_funded].copy();z['date']=pd.to_datetime(z.date)
 rows=[]
 def add(kind,label,g):
  q=metrics(g)
  if q: rows.append(dict(kind=kind,label=label,**q))
 # broad thresholds for continuity
 for c in [2.25,2.5,2.75,3.0,3.25,3.5]:add('threshold',f'comp>={c}',z[z.comp>=c])
 # non-overlapping odds bands
 for lo,hi in zip(COMP_BINS[:-1],COMP_BINS[1:]):add('comp_band',f'{lo:.2f}-{hi:.2f}',z[(z.comp>=lo)&(z.comp<hi)])
 # p3 x odds: deliberately coarse, predeclared bins, no fine threshold optimizer
 for plo,phi in zip(P_BINS[:-1],P_BINS[1:]):
  for clo,chi in zip(COMP_BINS[:-1],COMP_BINS[1:]):add('p3_x_comp',f'p3[{plo:.2f},{phi:.2f}) comp[{clo:.2f},{chi:.2f})',z[(z.p3>=plo)&(z.p3<phi)&(z.comp>=clo)&(z.comp<chi)])
 # estimated final-hit x odds zones
 for elo,ehi in zip(EH_BINS[:-1],EH_BINS[1:]):
  for clo,chi in zip(COMP_BINS[:-1],COMP_BINS[1:]):add('esthit_x_comp',f'eh[{elo:.2f},{ehi:.2f}) comp[{clo:.2f},{chi:.2f})',z[(z.est_hit>=elo)&(z.est_hit<ehi)&(z.comp>=clo)&(z.comp<chi)])
 # theory EV gates, not optimized to realized ROI
 for e in [.95,1.0,1.05,1.10,1.15,1.20,1.25,1.30]:add('theory_ev',f'ev>={e:.2f}',z[z.ev>=e])
 o=pd.DataFrame(rows);o.to_csv(OUT,index=False)
 keep=o[(o.R>=20)].sort_values(['kind','ROI'],ascending=[True,False])
 L=['# v227 odds-zone robustness exploration','', '**EXPLORATORY / CONTAMINATED BY DESIGN:** closing odds are used for discovery. No rule here is pristine validation.','- Input: v226 Top10 race-level rows, Dec2025-Jun2026 only. Jul/Aug excluded.','- 10,000 yen exact Dutch settlement inherited from v226.','- Coarse predeclared bins are used to avoid a fine-grained threshold optimizer.','- rm1/rm3/rm5 = ROI after removing the 1/3/5 largest payout races.','', '## Cells with at least 20 races','', '|kind|zone|R|hit|ROI|profit|maxDD|maxL|prof months|rm1|rm3|rm5|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for _,r in keep.iterrows():L.append(f"|{r.kind}|{r.label}|{int(r.R)}|{r.hit:.1f}%|{r.ROI:.1f}%|{r.profit:.0f}|{r.maxDD:.0f}|{int(r.maxL)}|{int(r.prof_months)}/{int(r.months)}|{r.rm1:.1f}%|{r.rm3:.1f}%|{r.rm5:.1f}%|")
 L+=['','## Threshold monthly detail']
 for _,r in o[o.kind=='threshold'].iterrows():L.append(f"- {r.label}: {r.monthly}")
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
