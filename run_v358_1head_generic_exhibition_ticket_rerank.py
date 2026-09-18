#!/usr/bin/env python3
from __future__ import annotations
"""v358: generic post-exhibition ticket rerank beyond the promoted 3->4 wall rule.

Research only. Race selection/HEAD gates stay frozen.  Current promoted wall3
policy is reconstructed first, then additional generic exhibition overlays are
tested without changing ticket count.
"""
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

from backtest import rows
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v326_1head_ticketaware_exhibition as v326
import run_v337_1head_head_cutoff_volume as v337
import run_v347_1head_opponent_attackcore as v347
import run_v351_1head_production_regression as base
import run_v346_1head_v345_production_regression as v346
import run_v351_1head_joint_roi_grid as grid
import run_v352_1head_wall3_risk_audit as v352

OUT=Path('/tmp/v358-generic-exhibition-rerank');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=v352.DEV;SUP=v352.SUP
G2=(0.5,1.0,2.0,3.0)
G3=(0.25,0.5,1.0,2.0)
AMIN=(0.50,0.60,0.70)
SCOPES=('WATCH_ONLY','ALL_BASIC')
FAMILIES=('GLOBAL','EXTRA_ADJ','EXTRA_ADJ_ST','GLOBAL_EXTRA_ADJ')
EXTRA_PAIRS=((2,3),(4,5),(5,6))
ALL_PAIRS=((2,3),(3,4),(4,5),(5,6))

def norm(q):
 s=sum(max(float(v),0.0) for v in q.values())
 if s<=0:return {k:1/len(q) for k in q}
 return {k:max(float(v),0.0)/s for k,v in q.items()}

def tickets(p2,pc):
 pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
 top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
 if len(top)!=3 or len(set(top))!=3:raise RuntimeError('invalid 3-ticket set')
 return ';'.join(f'1-{s}-{t}' for s,t in top)

def generic_exhibition(ids:set[str]):
 days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in ids})
 dayset=set(days);last=max(days);sums=defaultdict(list);allv=[];out=[];d=v337.PRELOAD
 while d<=last:
  ymd=d.strftime('%Y/%m/%d');strows=rows(f'data/previews/stt/{ymd}.csv');bias=v326.st_bias(sums,allv)
  if d in dayset:
   tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=v326.bycode(strows);orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   prefix=d.strftime('%Y%m%d')
   for code in sorted(c for c in ids if c.startswith(prefix)):
    tr=tkz.get(code,{});sr=stt.get(code,{});orr=orig.get(code,{})
    audit=v326.raw_completeness(tr,sr,orr)
    ready=all(audit[k] for k in ('tkz_all6','stt_all6','orig_straight_all6','orig_avg_all6'))
    rec={'race_code':code,'ex_ready':bool(ready)}
    if ready:
     ex,st,os=v326.corrected_direct(code,tkz,stt,orig,bias)
     for b in BOATS:
      rec[f'ex{b}']=float(ex[b]);rec[f'st{b}']=float(st[b]);rec[f'straight{b}']=float(os[b]['straight']);rec[f'avg{b}']=float(os[b]['avg'])
      rec[f'score{b}']=(prod.WALL3_SHADOW_W_EX*float(ex[b])+prod.WALL3_SHADOW_W_ST*float(st[b])+
                        prod.WALL3_SHADOW_W_STRAIGHT*float(os[b]['straight'])+prod.WALL3_SHADOW_W_ORIG_AVG*float(os[b]['avg']))
      rec[f'core{b}']=(prod.ATTACK_CORE_W_ONE_EX*float(ex[b])+prod.ATTACK_CORE_W_ONE_ST*float(st[b])+
                       prod.ATTACK_CORE_W_ONE_STRAIGHT*float(os[b]['straight'])+prod.ATTACK_CORE_W_ONE_ORIG_AVG*float(os[b]['avg']))
    out.append(rec)
  v326.update_st(strows,sums,allv);d+=timedelta(days=1)
 return pd.DataFrame(out)

def apply_vec(p2,pc,vec,g2,g3):
 q2={b:float(p2[b])*math.exp(g2*float(vec.get(b,0.0))) for b in BOATS};q2=norm(q2)
 q3={}
 for s in BOATS:
  q={t:float(pc[(s,t)])*math.exp(g3*float(vec.get(t,0.0))) for t in BOATS if t!=s};q=norm(q)
  for t,v in q.items():q3[(s,t)]=v
 return q2,q3

def wall3_official(p2,pc,r,watch):
 if not watch or not bool(r.ex_ready):return p2,pc,False,0.0
 ws=(prod.WALL3_SHADOW_W_EX*(r.ex3-r.ex4)+prod.WALL3_SHADOW_W_ST*(r.st3-r.st4)+
     prod.WALL3_SHADOW_W_STRAIGHT*(r.straight3-r.straight4)+prod.WALL3_SHADOW_W_ORIG_AVG*(r.avg3-r.avg4))
 a4=float(r.score4);risk=max(0.0,-float(ws)) if a4>=prod.WALL3_SHADOW_ATTACK4_MIN else 0.0
 if risk<=0:return p2,pc,False,risk
 vec={3:-risk,4:risk}
 return apply_vec(p2,pc,vec,prod.WALL3_SHADOW_SECOND_G2,prod.WALL3_SHADOW_THIRD_G3)[0],apply_vec(p2,pc,vec,prod.WALL3_SHADOW_SECOND_G2,prod.WALL3_SHADOW_THIRD_G3)[1],True,risk

def centered_score(r):
 vals={b:float(r[f'score{b}']) for b in BOATS};mu=sum(vals.values())/len(vals)
 return {b:vals[b]-mu for b in BOATS}

def adj_vec(r,amin,pairs,st_only=False):
 v={b:0.0 for b in BOATS};tr=[]
 for inner,outer in pairs:
  if float(r[f'score{outer}'])<amin:continue
  gap=(float(r[f'st{outer}'])-float(r[f'st{inner}'])) if st_only else (float(r[f'score{outer}'])-float(r[f'score{inner}']))
  if gap>0:
   v[outer]+=gap;v[inner]-=gap;tr.append(f'{inner}>{outer}')
 return v,tr

def addv(a,b):
 return {k:float(a.get(k,0))+float(b.get(k,0)) for k in BOATS}

def build_rows(sel,features,maps,cores):
 p2d,pcd,p2j,pcj=maps
 z=sel.merge(features,on='race_code',how='left',validate='one_to_one').copy()
 out=[]
 for _,r in z.iterrows():
  tm=str(r.month);code=str(r.race_code).zfill(12)
  p2,pc=v347.get_dist(tm,code,p2d,pcd,p2j,pcj)
  core=cores.get(code)
  if core is not None:p2=base._second_adjust(p2,core);pc=base._third_adjust(pc,core)
  else:p2={int(k):float(v) for k,v in p2.items()};pc={(int(s),int(t)):float(v) for (s,t),v in pc.items()}
  watch=float(r.opp_mass)>=prod.WATCH_OPPONENT_MASS_MIN
  pre=tickets(p2,pc)
  op2,op3,wapplied,wrisk=wall3_official(p2,pc,r,watch)
  official=tickets(op2,op3)
  out.append({**r.to_dict(),'operational_watch':watch,'pre_wall3_tickets':pre,'official_tickets':official,
              'wall3_applied':wapplied,'wall3_risk':wrisk,'_p2':op2,'_pc':op3})
 return out

def met(z,cache):return grid.met(z,cache)

def evaluate(rows,family,scope,amin,g2,g3,cache):
 rec=[];pair_counts=defaultdict(int)
 for rr in rows:
  r=pd.Series(rr);p2=rr['_p2'];pc=rr['_pc'];vec={b:0.0 for b in BOATS};tr=[]
  active=(scope=='ALL_BASIC') or bool(rr['operational_watch'])
  if active and bool(rr.get('ex_ready',False)):
   if family=='GLOBAL':vec=centered_score(r)
   elif family=='EXTRA_ADJ':vec,tr=adj_vec(r,amin,EXTRA_PAIRS,False)
   elif family=='EXTRA_ADJ_ST':vec,tr=adj_vec(r,amin,EXTRA_PAIRS,True)
   elif family=='GLOBAL_EXTRA_ADJ':
    av,tr=adj_vec(r,amin,EXTRA_PAIRS,False);vec=addv(centered_score(r),av)
  p2x,pcx=apply_vec(p2,pc,vec,g2,g3) if active else (p2,pc)
  ts=tickets(p2x,pcx);actual=str(rr['actual_combo'])
  changed=int(ts!=rr['official_tickets'])
  if changed:
   for x in tr:pair_counts[x]+=1
  rec.append({'month':str(rr['month']),'race_code':str(rr['race_code']).zfill(12),'head_hit':int(rr['head_hit']),
              'actual_combo':actual,'tickets':ts,'hit':int(actual in ts.split(';')),'official_tickets':rr['official_tickets'],
              'official_hit':int(actual in rr['official_tickets'].split(';')),'changed':changed,'operational_watch':int(rr['operational_watch'])})
 z=pd.DataFrame(rec);a=met(z,cache);dv=met(z[z.month.isin(DEV)],cache);sp=met(z[z.month.isin(SUP)],cache)
 m={'family':family,'scope':scope,'attack_min':amin,'g2':g2,'g3':g3,
    **{f'all_{k}':v for k,v in a.items()},**{f'dev_{k}':v for k,v in dv.items()},**{f'support_{k}':v for k,v in sp.items()},
    'changed_R':int(z.changed.sum()),'gain_R':int(((z.hit-z.official_hit)==1).sum()),'loss_R':int(((z.hit-z.official_hit)==-1).sum())}
 for p in ('2>3','4>5','5>6'):m[f'changed_trigger_{p}']=int(pair_counts[p])
 return z,m

def main():
 if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:raise RuntimeError('September guard disabled')
 y=grid.universe();maps=v347.opponent_maps();cache={}
 ym=y[pd.to_numeric(y.opp_mass,errors='coerce').ge(v352.BASIC['mass'])].copy()
 ym=v346.apply_v345_attack_core(ym)
 basic=grid.eval_cfg(ym,v352.BASIC['head'],v352.BASIC['env_w'],v352.BASIC['env_q'])
 if (len(basic),int(basic.head_hit.sum()))!=(165,140):raise RuntimeError(f'BASIC selection drift R={len(basic)} head={int(basic.head_hit.sum())}')
 ids=set(basic.race_code);features=generic_exhibition(ids)
 cores={}
 for _,fr in features[features.ex_ready.fillna(False)].iterrows():
  cores[str(fr.race_code).zfill(12)]={b:float(fr[f'core{b}']) for b in BOATS}
 rows=build_rows(basic,features,maps,cores)
 # Current promoted wall3 policy must reproduce v355 83 exact3.
 off=pd.DataFrame([{'month':str(r['month']),'race_code':str(r['race_code']).zfill(12),'head_hit':int(r['head_hit']),
                    'actual_combo':str(r['actual_combo']),'tickets':r['official_tickets'],
                    'hit':int(str(r['actual_combo']) in r['official_tickets'].split(';'))} for r in rows])
 om=met(off,cache)
 if om['R']!=165 or om['exact3']!=83:raise RuntimeError(f'official wall3 baseline drift {om}')
 summaries=[];races=[]
 for family in FAMILIES:
  for scope in SCOPES:
   amins=(0.60,) if family=='GLOBAL' else AMIN
   for amin in amins:
    for g2 in G2:
     for g3 in G3:
      z,m=evaluate(rows,family,scope,amin,g2,g3,cache);summaries.append(m)
      z['family']=family;z['scope']=scope;z['attack_min']=amin;z['g2']=g2;z['g3']=g3;races.append(z)
 sm=pd.DataFrame(summaries)
 sm['delta_hits_vs_official']=sm.all_exact3-int(om['exact3']);sm['delta_roi_pp_vs_official']=100*(sm.all_roi-float(om['roi']))
 sm['delta_dev_hits_vs_official']=sm.dev_exact3-int(met(off[off.month.isin(DEV)],cache)['exact3'])
 sm['delta_support_hits_vs_official']=sm.support_exact3-int(met(off[off.month.isin(SUP)],cache)['exact3'])
 # Candidate selection uses development only. Support never participates.
 sm['dev_floor_score']=sm.dev_roi
 best=sm.sort_values(['dev_exact3','dev_roi','changed_R'],ascending=[False,False,True]).iloc[0]
 rz=pd.concat(races,ignore_index=True)
 pick=rz[(rz.family==best.family)&(rz.scope==best.scope)&np.isclose(rz.attack_min,float(best.attack_min))&
         np.isclose(rz.g2,float(best.g2))&np.isclose(rz.g3,float(best.g3))].copy()
 cmp=off[['race_code','month','actual_combo','tickets','hit']].rename(columns={'tickets':'official_tickets_ref','hit':'official_hit_ref'}).merge(
     pick[['race_code','tickets','hit','changed']],on='race_code',validate='one_to_one')
 cmp['delta']=cmp.hit-cmp.official_hit_ref
 sm.to_csv(OUT/'grid.csv',index=False);cmp.to_csv(OUT/'best_paired.csv',index=False)
 result={'official_wall3_baseline':om,'grid_R':len(sm),'dev_selected_best':best.to_dict(),
         'best_gain_R':int((cmp.delta==1).sum()),'best_loss_R':int((cmp.delta==-1).sum()),
         'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
 (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
 print(json.dumps(result,indent=2,default=str),flush=True)
 print('\nTOP20',flush=True);print(sm.sort_values(['dev_exact3','dev_roi','all_exact3'],ascending=False).head(20).to_string(index=False),flush=True)

if __name__=='__main__':main()
