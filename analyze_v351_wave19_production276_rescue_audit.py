#!/usr/bin/env python3
from __future__ import annotations
"""Wave19: frozen 1-3-5 rescue on canonical v351 production 276R."""
from collections import defaultdict
from datetime import date,timedelta
import math
import pandas as pd
from backtest import rows
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v326_1head_ticketaware_exhibition as v326
import run_v337_1head_head_cutoff_volume as v337
import run_v347_1head_opponent_attackcore as legacy
BOATS=(2,3,4,5,6); GAP=.50

def norm(q):
 s=sum(max(float(v),0) for v in q.values()); return {k:(max(float(v),0)/s if s else 1/len(q)) for k,v in q.items()}
def adj2(p,c): return norm({b:float(p[b])*math.exp(float(prod.OPPONENT_CORE_SECOND_G2)*(float(c[b])-.5)) for b in BOATS})
def adj3(p,c):
 o={}
 for s in BOATS:
  q=norm({t:float(p[(s,t)])*math.exp(float(prod.OPPONENT_CORE_THIRD_G3)*(float(c[t])-.5)) for t in BOATS if t!=s}); o.update({(s,t):v for t,v in q.items()})
 return o
def tickets(p2,pc): return [f'1-{s}-{t}' for s,t in v299.STRATEGIES['HYBRID'](p2,pc,v299.pair_prob(p2,pc,prod.TICKET_ALPHA))[:3]]
def production():
 sel,pre=legacy.current_selected(); sel=sel.copy(); sel['race_code']=sel.race_code.astype(str).str.zfill(12)
 if (len(sel),int(sel.head_hit.sum()))!=(276,241): raise RuntimeError('selection sentinel drift')
 ids=set(sel.race_code); p2d,pcd,p2j,pcj=legacy.opponent_maps(); cores=legacy.build_opponent_attackcore(ids); rec=[]
 for _,r in sel.sort_values('race_code').iterrows():
  code=str(r.race_code).zfill(12); tm=str(r.month)
  if code[:8]>='20260901': raise RuntimeError('September row detected')
  p2,pc=legacy.get_dist(tm,code,p2d,pcd,p2j,pcj); c=cores.get(code)
  if c is not None: p2,pc=adj2(p2,c),adj3(pc,c)
  ts=tickets(p2,pc); actual=str(r.actual_combo); rec.append(dict(month=tm,race_code=code,actual_combo=actual,baseline_tickets=';'.join(ts),baseline_hit=int(actual in ts)))
 z=pd.DataFrame(rec)
 if (len(z),int(z.baseline_hit.sum()))!=(276,131): raise RuntimeError(f'canonical hard guard failed {(len(z),int(z.baseline_hit.sum()))}')
 return z,pre
def ranks(v): return pd.Series(v).rank(method='average',ascending=True).to_dict()
def strength(ids):
 days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in ids}); dayset=set(days); last=max(days); sums=defaultdict(list); allv=[]; out={}; d=v337.PRELOAD
 while d<=last:
  y=d.strftime('%Y/%m/%d'); sr=rows(f'data/previews/stt/{y}.csv'); bias=v326.st_bias(sums,allv)
  if d in dayset:
   tk=v326.bycode(rows(f'data/previews/tkz/{y}.csv')); st=v326.bycode(sr); og=v326.bycode(rows(f'data/previews/original_exhibition/{y}.csv')); prefix=d.strftime('%Y%m%d')
   for code in sorted(c for c in ids if c.startswith(prefix)):
    a=v326.raw_completeness(tk.get(code,{}),st.get(code,{}),og.get(code,{}))
    if not all(a[k] for k in ('tkz_all6','stt_all6','orig_straight_all6','orig_avg_all6')): continue
    ex,sv,os=v326.corrected_direct(code,tk,st,og,bias); er=ranks(ex); srk=ranks(sv); rr=ranks({b:os[b]['straight'] for b in BOATS}); ar=ranks({b:os[b]['avg'] for b in BOATS}); sc={b:(er[b]+srk[b]+rr[b]+ar[b])/4 for b in BOATS}; out[code]=sc[2]-sc[3]
  v326.update_st(sr,sums,allv); d+=timedelta(days=1)
 return out
def main():
 z,pre=production(); ss=strength(set(z.race_code)); rec=[]
 for _,r in z.iterrows():
  gap=ss.get(r.race_code,float('nan')); eligible=pd.notna(gap) and gap>=GAP; base=r.baseline_tickets.split(';'); final=list(base); cand='1-3-5'; already=cand in base; override=False
  if eligible and not already: final[1]=cand; override=True
  if len(set(final))<3: final=list(base); override=False
  fh=int(r.actual_combo in final); q=r.to_dict(); q.update(strength2_minus3=gap,eligible=int(eligible),candidate_already_present=int(already),override=int(override),final_tickets=';'.join(final),final_hit=fh,rescue=int(fh and not r.baseline_hit),damage=int(r.baseline_hit and not fh)); rec.append(q)
 q=pd.DataFrame(rec); q.to_csv('analysis_v351_wave19_production276_rows.csv',index=False,encoding='utf-8-sig'); out=[]
 for label,g in [('ALL',q)]+[(f'MONTH:{k}',v) for k,v in q.groupby('month')]: out.append(dict(slice=label,races=len(g),baseline_hits=int(g.baseline_hit.sum()),final_hits=int(g.final_hit.sum()),eligible=int(g.eligible.sum()),override=int(g.override.sum()),already=int(g.candidate_already_present.sum()),rescue=int(g.rescue.sum()),damage=int(g.damage.sum()),net=int(g.rescue.sum()-g.damage.sum())))
 sm=pd.DataFrame(out); sm.to_csv('analysis_v351_wave19_production276_summary.csv',index=False,encoding='utf-8-sig'); print('PRE_R',pre); print(sm.to_string(index=False)); print('CANONICAL_GUARD',len(q),int(q.baseline_hit.sum())); print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False')
if __name__=='__main__': main()
