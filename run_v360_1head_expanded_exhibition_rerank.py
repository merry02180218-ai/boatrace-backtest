#!/usr/bin/env python3
from __future__ import annotations
"""v360: expanded-universe validation of post-exhibition opponent reranking.

Research only.  It widens the race denominator beyond current LIVE 165R while
keeping each universe fixed and changing only the 3-ticket opponent ordering.
September outcomes are forbidden.
"""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import urllib.request
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import backtest
import run_v299_1head_trifecta3_policy_search as v299
import run_v337_1head_head_cutoff_volume as v337
import run_v346_1head_v345_production_regression as v346
import run_v347_1head_opponent_attackcore as v347
import run_v351_1head_production_regression as base
import run_v351_1head_joint_roi_grid as grid
import run_v352_1head_wall3_risk_audit as v352
import run_v358_1head_generic_exhibition_ticket_rerank as v358

OUT=Path('/tmp/v360-expanded-exhibition-rerank');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=v352.DEV;SUP=v352.SUP

UNIVERSES={
 'LIVE165': {'head':.790,'mass':.375,'env_w':.05,'env_q':.70,'expected_R':165},
 'H078_M375': {'head':.780,'mass':.375,'env_w':.05,'env_q':.70,'expected_R':236},
 'H0775_M375': {'head':.775,'mass':.375,'env_w':.05,'env_q':.70,'expected_R':269},
 'H0775_M350': {'head':.775,'mass':.350,'env_w':.05,'env_q':.70,'expected_R':313},
 'PROD276': {'head':.780,'mass':.375,'env_w':.10,'env_q':.65,'expected_R':276},
}
PAIRS={'2>3':((2,3),),'3>4':((3,4),),'4>5':((4,5),),'5>6':((5,6),),'ALL_ADJ':((2,3),(3,4),(4,5),(5,6))}
ATTACK_MIN=.60
G2=.50
G3=.50


def install_preview_cache():
    paths=[]
    d=v337.PRELOAD
    last=pd.Timestamp('2026-08-31').date()
    while d<=last:
        ymd=d.strftime('%Y/%m/%d')
        for kind in ('stt','tkz','original_exhibition'):
            paths.append(f'data/previews/{kind}/{ymd}.csv')
        if d>=pd.Timestamp('2026-02-01').date():
            paths.append(f'data/results/payouts/{ymd}.csv')
        d+=timedelta(days=1)
    original=backtest.fetch
    def one(path):
        try:
            with urllib.request.urlopen(backtest.BASE+path,timeout=30) as r:
                return path,r.read().decode('utf-8-sig')
        except Exception:
            return path,''
    cache={}
    with ThreadPoolExecutor(max_workers=32) as ex:
        for path,txt in ex.map(one,paths):
            cache[path]=txt
    def cached(path):
        if path in cache:return cache[path]
        return original(path)
    backtest.fetch=cached
    return {'paths':len(paths),'nonempty':sum(bool(v) for v in cache.values())}

def norm(q):
 s=sum(max(float(v),0.0) for v in q.values())
 return {k:max(float(v),0.0)/s for k,v in q.items()} if s>0 else {k:1/len(q) for k in q}

def tickets(p2,pc):
 pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
 top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
 if len(top)!=3 or len(set(top))!=3: raise RuntimeError('invalid ticket set')
 return ';'.join(f'1-{s}-{t}' for s,t in top)

def apply_vec(p2,pc,vec):
 q2={b:float(p2[b])*math.exp(G2*float(vec.get(b,0))) for b in BOATS};q2=norm(q2)
 q3={}
 for s in BOATS:
  q={t:float(pc[(s,t)])*math.exp(G3*float(vec.get(t,0))) for t in BOATS if t!=s};q=norm(q)
  for t,v in q.items():q3[(s,t)]=v
 return q2,q3

def adj_vec(r,pairs):
 v={b:0.0 for b in BOATS};tr=[]
 for inner,outer in pairs:
  if float(r[f'score{outer}'])<ATTACK_MIN: continue
  gap=float(r[f'score{outer}'])-float(r[f'score{inner}'])
  if gap>0:
   v[outer]+=gap;v[inner]-=gap;tr.append(f'{inner}>{outer}')
 return v,tr

def met(z,cache): return grid.met(z,cache)

def select_universe(y,cfg,maps,cores):
 ym=y[pd.to_numeric(y.opp_mass,errors='coerce').ge(cfg['mass'])].copy()
 ym=v346.apply_v345_attack_core(ym)
 s=grid.eval_cfg(ym,cfg['head'],cfg['env_w'],cfg['env_q'])
 s=s.copy();s.race_code=s.race_code.astype(str).str.zfill(12)
 if len(s)!=cfg['expected_R']: raise RuntimeError(f'universe drift expected {cfg["expected_R"]} got {len(s)} cfg={cfg}')
 return s

def baseline_rows(sel,features,maps,cores):
 p2d,pcd,p2j,pcj=maps
 z=sel.merge(features,on='race_code',how='left',validate='one_to_one')
 rec=[]
 for _,r in z.iterrows():
  code=str(r.race_code).zfill(12);tm=str(r.month)
  p2,pc=v347.get_dist(tm,code,p2d,pcd,p2j,pcj)
  core=cores.get(code)
  if core is not None:
   p2=base._second_adjust(p2,core);pc=base._third_adjust(pc,core)
  else:
   p2={int(k):float(v) for k,v in p2.items()};pc={(int(s),int(t)):float(v) for (s,t),v in pc.items()}
  bt=tickets(p2,pc);actual=str(r.actual_combo)
  rec.append({**r.to_dict(),'base_tickets':bt,'base_hit':int(actual in bt.split(';')),'_p2':p2,'_pc':pc})
 return rec

def evaluate(rows,label,pairs,scope,cache):
 rec=[];triggers=defaultdict(int)
 for rr in rows:
  r=pd.Series(rr);active=(scope=='ALL') or float(rr['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN
  p2,pc=rr['_p2'],rr['_pc'];vec={b:0.0 for b in BOATS};tr=[]
  if active and bool(rr.get('ex_ready',False)):
   vec,tr=adj_vec(r,pairs)
   if any(abs(x)>0 for x in vec.values()):p2,pc=apply_vec(p2,pc,vec)
  ts=tickets(p2,pc);actual=str(rr['actual_combo']);hit=int(actual in ts.split(';'))
  changed=int(ts!=rr['base_tickets'])
  if changed:
   for x in tr:triggers[x]+=1
  rec.append({'month':str(rr['month']),'race_code':str(rr['race_code']).zfill(12),'head_hit':int(rr['head_hit']),
              'actual_combo':actual,'tickets':ts,'hit':hit,'base_tickets':rr.base_tickets,
              'base_hit':int(rr['base_hit']),'changed':changed,'opp_mass':float(rr.opp_mass)})
 z=pd.DataFrame(rec)
 a=met(z,cache);dv=met(z[z.month.isin(DEV)],cache);sp=met(z[z.month.isin(SUP)],cache)
 m={'variant':label,'scope':scope,**{f'all_{k}':v for k,v in a.items()},**{f'dev_{k}':v for k,v in dv.items()},
    **{f'support_{k}':v for k,v in sp.items()},'changed_R':int(z.changed.sum()),
    'gain_R':int(((z.hit-z.base_hit)==1).sum()),'loss_R':int(((z.hit-z.base_hit)==-1).sum())}
 for p in PAIRS:m[f'trigger_{p}']=int(triggers[p])
 return z,m

def baseline_metrics(rows,cache):
 z=pd.DataFrame([{'month':str(r['month']),'race_code':str(r['race_code']).zfill(12),'head_hit':int(r['head_hit']),
                  'actual_combo':str(r['actual_combo']),'tickets':r['base_tickets'],'hit':int(r['base_hit'])} for r in rows])
 a=met(z,cache);dv=met(z[z.month.isin(DEV)],cache);sp=met(z[z.month.isin(SUP)],cache)
 return z,{'variant':'BASE','scope':'NA',**{f'all_{k}':v for k,v in a.items()},**{f'dev_{k}':v for k,v in dv.items()},
           **{f'support_{k}':v for k,v in sp.items()},'changed_R':0,'gain_R':0,'loss_R':0}

def main():
 if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:raise RuntimeError('September guard disabled')
 prefetch=install_preview_cache();print('preview_cache',prefetch,flush=True)
 y=grid.universe();maps=v347.opponent_maps();cache={}
 sels={name:select_universe(y,cfg,maps,{}) for name,cfg in UNIVERSES.items()}
 union=set().union(*(set(s.race_code) for s in sels.values()))
 features=v358.generic_exhibition(union);features.to_csv(OUT/'expanded_exhibition_features.csv',index=False)
 # Build one opponent-core map from the same causal corrected exhibition features.
 cores={}
 for _,r in features[features.ex_ready.fillna(False)].iterrows():
  cores[str(r.race_code).zfill(12)]={b:float(r[f'core{b}']) for b in BOATS}
 summaries=[];monthly=[];paired=[];bases={}
 for uname,sel in sels.items():
  rows=baseline_rows(sel,features,maps,cores)
  bz,bm=baseline_metrics(rows,cache);bm['universe']=uname;summaries.append(bm);bases[uname]=bm
  for mon,g in bz.groupby('month'):
   mm=met(g,cache);monthly.append({'universe':uname,'variant':'BASE','scope':'NA','month':mon,**mm})
  for pname,pairs in PAIRS.items():
   for scope in ('ALL','MASS425'):
    z,m=evaluate(rows,pname,pairs,scope,cache);m['universe']=uname;summaries.append(m)
    z['universe']=uname;z['variant']=pname;z['scope']=scope;paired.append(z)
    for mon,g in z.groupby('month'):
     mm=met(g,cache);monthly.append({'universe':uname,'variant':pname,'scope':scope,'month':mon,**mm})
 sm=pd.DataFrame(summaries);mo=pd.DataFrame(monthly);pr=pd.concat(paired,ignore_index=True)
 for uname in UNIVERSES:
  b=sm[(sm.universe==uname)&(sm.variant=='BASE')].iloc[0]
  ix=sm.universe.eq(uname)
  sm.loc[ix,'delta_hits']=sm.loc[ix,'all_exact3']-int(b.all_exact3)
  sm.loc[ix,'delta_roi_pp']=100*(sm.loc[ix,'all_roi']-float(b.all_roi))
  sm.loc[ix,'delta_dev_hits']=sm.loc[ix,'dev_exact3']-int(b.dev_exact3)
  sm.loc[ix,'delta_support_hits']=sm.loc[ix,'support_exact3']-int(b.support_exact3)
 sm.to_csv(OUT/'summary.csv',index=False);mo.to_csv(OUT/'monthly.csv',index=False);pr.to_csv(OUT/'race_predictions.csv',index=False)
 # Generalization view: fixed variant must be non-negative hits in >=4/5 universes and improve dev in >=3.
 cand=sm[sm.variant.ne('BASE')].copy()
 grp=cand.groupby(['variant','scope']).agg(universes=('universe','nunique'),positive_all=('delta_hits',lambda s:int((s>0).sum())),
     nonnegative_all=('delta_hits',lambda s:int((s>=0).sum())),positive_dev=('delta_dev_hits',lambda s:int((s>0).sum())),
     nonnegative_support=('delta_support_hits',lambda s:int((s>=0).sum())),mean_delta_hits=('delta_hits','mean'),
     mean_delta_roi_pp=('delta_roi_pp','mean'),total_changed=('changed_R','sum'),total_gain=('gain_R','sum'),total_loss=('loss_R','sum')).reset_index()
 robust=grp[(grp.nonnegative_all>=4)&(grp.positive_dev>=2)&(grp.nonnegative_support>=4)].sort_values(
     ['positive_all','positive_dev','mean_delta_hits','mean_delta_roi_pp'],ascending=False)
 grp.to_csv(OUT/'generalization.csv',index=False)
 result={'preview_cache':prefetch,'universes':{k:{'cfg':UNIVERSES[k],'baseline':bases[k]} for k in UNIVERSES},
         'fixed_attack_min':ATTACK_MIN,'fixed_g2':G2,'fixed_g3':G3,
         'best_generalization':robust.iloc[0].to_dict() if len(robust) else None,
         'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
 (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
 print(json.dumps(result,indent=2,default=str),flush=True)
 print('\nGENERALIZATION',flush=True);print(grp.sort_values(['positive_all','positive_dev','mean_delta_hits'],ascending=False).to_string(index=False),flush=True)
 print('\nSUMMARY',flush=True);print(sm[['universe','variant','scope','all_R','all_exact3','all_roi','delta_hits','delta_roi_pp','dev_exact3','delta_dev_hits','support_exact3','delta_support_hits','changed_R','gain_R','loss_R']].to_string(index=False),flush=True)

if __name__=='__main__':main()
