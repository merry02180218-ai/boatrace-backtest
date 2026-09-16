#!/usr/bin/env python3
"""Sparse SECOND-rank4 rescue. Threshold selection Apr-Jun only; Sep never read."""
from pathlib import Path
import json, pandas as pd
import audit_4head_v283_adaptive_second_depth as a
OUT=Path('/tmp/head4_v283_sparse_rank4'); OUT.mkdir(parents=True,exist_ok=True)
THIRD=.10
GAPS=[.01,.02,.03,.04,.05,.06,.075,.10,.125,.15,.20]

def gap24(r):
 s=a.ranked(r); return float(r.p2[s[1]]-r.p2[s[3]])

def sparse(r,g,base_depth=2,tgap=None):
 # Keep the chosen base policy; add SECOND rank4 only when ranks2-4 are genuinely close.
 d=4 if gap24(r)<=g else base_depth
 return a.pairs_depth(r,d,tgap)

def main():
 df,_=a.prev.build(); assert len(df)==164 and df.date.max()<='2026-08-31'
 dev=df[df.month.isin(['2026-04','2026-05','2026-06'])]
 scan=[]
 for g in GAPS:
  q=a.settle(dev,lambda r,g=g:sparse(r,g,2,None)); scan.append({'gap24':g,**a.metric(q)})
 sc=pd.DataFrame(scan)
 # Development only: maximize profit, then ROI, fewer tickets, tighter threshold.
 best=sc.sort_values(['profit','roi_pct','tickets','gap24'],ascending=[False,False,True,True]).iloc[0]; bg=float(best.gap24)
 modes={
  'base4':lambda r:a.pairs_depth(r,2,None),
  'third_margin':lambda r:a.pairs_depth(r,2,THIRD),
  'second3_third_margin':lambda r:a.pairs_depth(r,3,THIRD),
  'sparse_rank4':lambda r:sparse(r,bg,2,None),
  'sparse_rank4_third':lambda r:sparse(r,bg,2,THIRD),
  'second3_sparse_rank4_third':lambda r:sparse(r,bg,3,THIRD),
 }
 rec=[]
 for n,f in modes.items():
  q=a.settle(df,f); q['mode']=n; q['gap24']=df.apply(gap24,axis=1).values; q['rank4_fire']=(q.gap24<=bg).astype(int); rec.append(q)
 rd=pd.concat(rec,ignore_index=True)
 periods={'Apr-Jun':['2026-04','2026-05','2026-06'],'Jul-Aug':['2026-07','2026-08'],'July':['2026-07'],'August':['2026-08'],'Apr-Aug':['2026-04','2026-05','2026-06','2026-07','2026-08']}
 sm=[]
 for pn,mons in periods.items():
  for n in modes:
   q=rd[(rd.month.isin(mons))&(rd['mode'].eq(n))]; sm.append({'period':pn,'mode':n,**a.metric(q),'fire_races':int(q.rank4_fire.sum())})
 summary=pd.DataFrame(sm)
 # rank4 misses only, for transparent rescue accounting.
 miss=df[(df.head4.eq(1))&(df.second_rank.eq(4))].copy(); miss['gap24']=miss.apply(gap24,axis=1); miss['fires']=miss.gap24<=bg
 miss=miss[['date','month','race_code','actual_second','actual_third','second_rank','gap24','fires']]
 sc.to_csv(OUT/'dev_gap24_scan.csv',index=False); summary.to_csv(OUT/'summary.csv',index=False); rd.to_csv(OUT/'race_detail.csv',index=False); miss.to_csv(OUT/'rank4_misses.csv',index=False)
 meta={'chosen_gap24':bg,'selection':'Apr-Jun max profit, then ROI, fewer tickets, tighter threshold','third_gap':THIRD,'formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','production':'HEAD4_V291_COMP7 unchanged'}; (OUT/'meta.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('HEAD4_V283_SPARSE_RANK4_RESCUE_OK'); print('CHOSEN_GAP24',bg); print('\nRANK4_MISSES\n',miss.to_string(index=False)); print('\nSUMMARY\n',summary.to_string(index=False)); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')
if __name__=='__main__': main()
