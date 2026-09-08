#!/usr/bin/env python3
"""v228 structural audit of the v227 3.00-3.25 composite-odds zone.
EXPLORATORY ONLY: historical closing odds are used by explicit exception. No production/pristine claim.
Dec2025-Jun2026 only; Jul/Aug excluded upstream by v226.
"""
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent; SRC=ROOT/'analysis_v226_3head_closing_odds_exploration.csv'; OUT=ROOT/'analysis_v228_3head_odds_zone_structure.csv'; SUM=ROOT/'summary_v228_3head_odds_zone_structure.md'; BANK=10000

def met(g):
 if len(g)==0:return None
 g=g.sort_values(['date','race_code']); r=len(g); ret=g.ret.sum(); cs=g.profit.cumsum(); dd=(cs.cummax()-cs).max();
 return dict(R=r,hit=100*g.hit.mean(),ROI=100*ret/(r*BANK),profit=ret-r*BANK,avg_comp=g.comp.mean(),avg_p3=g.p3.mean(),avg_est_hit=g.est_hit.mean(),avg_ev=g.ev.mean(),maxDD=dd)
def main():
 z=pd.read_csv(SRC,dtype={'race_code':str});z=z[(z.n==10)&z.fully_funded].copy();z['date']=pd.to_datetime(z.date);zone=z[(z.comp>=3.0)&(z.comp<3.25)].copy(); rows=[]
 def add(kind,label,g):
  q=met(g)
  if q:rows.append(dict(kind=kind,label=label,**q))
 add('overall','comp[3.00,3.25)',zone)
 for m,g in zone.groupby('month'):add('month',str(m),g)
 # p3 and estimated-hit coarse structure
 for lo,hi in [(0,.35),(.35,.40),(.40,.45),(.45,.50),(.50,1.01)]:add('p3',f'[{lo:.2f},{hi:.2f})',zone[(zone.p3>=lo)&(zone.p3<hi)])
 for lo,hi in [(0,.25),(.25,.30),(.30,.35),(.35,.40),(.40,.45),(.45,1.01)]:add('est_hit',f'[{lo:.2f},{hi:.2f})',zone[(zone.est_hit>=lo)&(zone.est_hit<hi)])
 for lo,hi in [(0,1.0),(1.0,1.1),(1.1,1.2),(1.2,1.3),(1.3,1.4),(1.4,99)]:add('ev',f'[{lo:.2f},{hi:.2f})',zone[(zone.ev>=lo)&(zone.ev<hi)])
 # race number/venue from 12-digit race code: YYYYMMDD + jcd(2) + race(2)
 zone['jcd']=zone.race_code.str.zfill(12).str[8:10];zone['race_no']=pd.to_numeric(zone.race_code.str.zfill(12).str[10:12],errors='coerce')
 for j,g in zone.groupby('jcd'):add('venue',j,g)
 for lo,hi in [(1,4),(4,7),(7,10),(10,13)]:add('race_no',f'{lo}-{hi-1}R',zone[(zone.race_no>=lo)&(zone.race_no<hi)])
 # hit-return concentration and chronology
 hits=zone[zone.hit==1].sort_values('ret',ascending=False).copy(); total_profit=zone.profit.sum(); top=[]
 for k in [1,2,3,5,10]:
  h=zone.drop(hits.head(k).index);top.append((k,len(h),100*h.ret.sum()/(len(h)*BANK) if len(h) else np.nan))
 # leave-one-month-out descriptive stability
 loo=[]
 for m in sorted(zone.month.unique()):
  h=zone[zone.month!=m];loo.append((m,len(h),100*h.ret.sum()/(len(h)*BANK) if len(h) else np.nan))
 o=pd.DataFrame(rows);o.to_csv(OUT,index=False)
 L=['# v228 3.00-3.25 odds-zone structural audit','', '**EXPLORATORY / CONTAMINATED BY DESIGN:** this zone was discovered with historical closing odds. This audit diagnoses structure; it is not independent validation.','- Dec2025-Jun2026 only; Jul/Aug remain excluded.','- Top10, exact 10,000-yen Dutch inherited from v226.','', '## Structural slices','', '|kind|slice|R|hit|ROI|profit|avg comp|avg p3|avg est hit|avg EV|maxDD|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for _,r in o.iterrows():L.append(f"|{r.kind}|{r.label}|{int(r.R)}|{r.hit:.1f}%|{r.ROI:.1f}%|{r.profit:.0f}|{r.avg_comp:.3f}|{r.avg_p3:.3f}|{r.avg_est_hit:.3f}|{r.avg_ev:.3f}|{r.maxDD:.0f}|")
 L+=['','## Payout concentration']+[f'- remove top {k} winning payouts: R={n}, ROI={roi:.1f}%' for k,n,roi in top]+['','## Leave-one-month-out']+[f'- exclude {m}: R={n}, ROI={roi:.1f}%' for m,n,roi in loo]+['','## Zone races']
 for _,r in zone.sort_values(['date','race_code']).iterrows():L.append(f"- {r.date.date()} {r.race_code}: p3={r.p3:.3f}, est_hit={r.est_hit:.3f}, comp={r.comp:.3f}, EV={r.ev:.3f}, hit={int(r.hit)}, return={r.ret:.0f}, profit={r.profit:.0f}")
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
