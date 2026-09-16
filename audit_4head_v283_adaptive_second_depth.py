#!/usr/bin/env python3
"""Adaptive SECOND-depth audit for frozen v283. Development Apr-Jun only; Sep never read."""
from pathlib import Path
import json, numpy as np, pandas as pd
import analyze_4head_v283_second_margin_rescue as prev
import audit_4head_86r_v283_closing_odds as audit
from head4_v291_downstream_inference import BOATS, v283_top4
OUT=Path('/tmp/head4_v283_adaptive_second_depth'); OUT.mkdir(parents=True,exist_ok=True)
STAKE=100; THIRD_GAP=.10
G3=[.05,.075,.10,.15,.20,.25,.30]
G4=[.025,.05,.075,.10,.15,.20]

def ranked(row):
 return sorted(BOATS,key=lambda s:(-float(row.p2[s]),s))

def pairs_depth(row,depth=2,tgap=None):
 so=ranked(row); seconds=so[:depth]; out=[]
 for s in seconds:
  ts=sorted((t for t in BOATS if t!=s),key=lambda t:(-float(row.pc[(s,t)]),t))
  n=3 if tgap is not None and float(row.pc[(s,ts[1])]-row.pc[(s,ts[2])])<=tgap else 2
  out += [(s,t) for t in ts[:n]]
 base=v283_top4(row.p2,row.pc)
 return list(dict.fromkeys(base+[x for x in out if x not in base]))

def adaptive_depth(row,g3,g4):
 so=ranked(row); gap23=float(row.p2[so[1]]-row.p2[so[2]]); gap34=float(row.p2[so[2]]-row.p2[so[3]])
 if gap23>g3: return 2
 return 4 if gap34<=g4 else 3

def pairs_adaptive(row,g3,g4,tgap=None): return pairs_depth(row,adaptive_depth(row,g3,g4),tgap)

def settle(df,mode_fn):
 cache={}; rows=[]
 for _,r in df.iterrows():
  ps=mode_fn(r); oq=cache.setdefault(r.date,audit.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)] if len(oq) else oq; covered=len(oo)==1
  hp=(int(r.actual_second),int(r.actual_third)) if r.head4 else None; hit=covered and hp in ps
  odd=pd.to_numeric(oo.iloc[0].get(f'4-{hp[0]}-{hp[1]}'),errors='coerce') if hit else np.nan; hit=bool(hit and pd.notna(odd)); payout=float(odd*STAKE) if hit else 0.; stake=len(ps)*STAKE if covered else 0
  rows.append({'date':r.date,'month':r.month,'race_code':r.race_code,'tickets':len(ps),'stake':stake,'hit':int(hit),'payout':payout,'profit':payout-stake})
 return pd.DataFrame(rows)

def metric(q):
 st=float(q.stake.sum()); pay=float(q.payout.sum()); return {'R':len(q),'tickets':int(q.tickets.sum()),'hits':int(q.hit.sum()),'stake':st,'payout':pay,'profit':pay-st,'roi_pct':100*pay/st if st else np.nan}

def main():
 df,_=prev.build(); assert df.date.max()<='2026-08-31' and len(df)==164
 # add rank-depth diagnostics
 for i,r in df.iterrows():
  so=ranked(r); df.at[i,'second_gap34']=float(r.p2[so[2]]-r.p2[so[3]]); df.at[i,'second_gap24']=float(r.p2[so[1]]-r.p2[so[3]])
 dev=df[df.month.isin(['2026-04','2026-05','2026-06'])].copy()
 scan=[]
 for g3 in G3:
  for g4 in G4:
   q=settle(dev,lambda r,g3=g3,g4=g4:pairs_adaptive(r,g3,g4,None)); m=metric(q); scan.append({'g3':g3,'g4':g4,**m})
 sc=pd.DataFrame(scan)
 # Apr-Jun only: maximize profit, then ROI, then fewer tickets, then tighter thresholds.
 best=sc.sort_values(['profit','roi_pct','tickets','g3','g4'],ascending=[False,False,True,True,True]).iloc[0]; bg3=float(best.g3); bg4=float(best.g4)
 modes={
  'base4':lambda r:pairs_depth(r,2,None),
  'second_top3':lambda r:pairs_depth(r,3,None),
  'second_top4':lambda r:pairs_depth(r,4,None),
  'third_margin':lambda r:pairs_depth(r,2,THIRD_GAP),
  'second3_third_margin':lambda r:pairs_depth(r,3,THIRD_GAP),
  'adaptive_second':lambda r:pairs_adaptive(r,bg3,bg4,None),
  'adaptive_second_third':lambda r:pairs_adaptive(r,bg3,bg4,THIRD_GAP),
 }
 allrec=[]
 for name,fn in modes.items():
  q=settle(df,fn); q['mode']=name; allrec.append(q)
 rd=pd.concat(allrec,ignore_index=True)
 periods={'Apr-Jun':['2026-04','2026-05','2026-06'],'Jul-Aug':['2026-07','2026-08'],'July':['2026-07'],'August':['2026-08'],'Apr-Aug':['2026-04','2026-05','2026-06','2026-07','2026-08']}; sm=[]
 for pn,mons in periods.items():
  for name in modes:
   q=rd[(rd.month.isin(mons))&(rd['mode'].eq(name))]; sm.append({'period':pn,'mode':name,**metric(q)})
 summary=pd.DataFrame(sm)
 miss=df[(df.head4.eq(1))&(df.second_rank>2)].copy(); miss=miss[['date','month','race_code','actual_second','actual_third','second_rank','second_order','second_gap23','second_gap34','second_gap24']]
 # depth fire counts on all candidate races
 df['adaptive_depth']=df.apply(lambda r:adaptive_depth(r,bg3,bg4),axis=1)
 depth=df.groupby(['month','adaptive_depth']).size().reset_index(name='R')
 sc.to_csv(OUT/'dev_adaptive_grid.csv',index=False); summary.to_csv(OUT/'summary.csv',index=False); miss.to_csv(OUT/'second_miss_depth.csv',index=False); depth.to_csv(OUT/'adaptive_depth_counts.csv',index=False); rd.to_csv(OUT/'race_mode_detail.csv',index=False)
 meta={'chosen_g3':bg3,'chosen_g4':bg4,'selection':'Apr-Jun max profit, then ROI, fewer tickets, tighter thresholds','third_gap':THIRD_GAP,'formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','production':'HEAD4_V291_COMP7 unchanged'}; (OUT/'meta.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('HEAD4_V283_ADAPTIVE_SECOND_DEPTH_OK'); print('CHOSEN',bg3,bg4); print('\nSECOND_MISS_DEPTH\n',miss.to_string(index=False)); print('\nDEPTH_COUNTS\n',depth.to_string(index=False)); print('\nSUMMARY\n',summary.to_string(index=False)); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')
if __name__=='__main__': main()
