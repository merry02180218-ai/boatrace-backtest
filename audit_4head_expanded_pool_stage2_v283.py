#!/usr/bin/env python3
"""4HEAD expanded-universe Stage 2: frozen v283 + odds + nested expansion search.

Consumes Stage1's label-independent 226R pool. The frozen 120R set is mandatory
and cannot be removed. New selection is expansion-only.
September outcomes/odds are blocked.
"""
from __future__ import annotations
from pathlib import Path
import json, math, os
import numpy as np
import pandas as pd

import audit_4head_headprob_pass_rescue as hpmod
import audit_4head_86r_v283_closing_odds as oddsmod
import run_4head_v291_third010_live as live
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, BOATS

OUT=Path('/tmp/head4_expanded_pool_stage2'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
DEV=('2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

COMP_FLOORS=(1.5,2.0,2.25,2.5,2.75,3.0,3.5)
Q_CUTS=tuple(round(x,3) for x in np.arange(.65,.901,.025))
HP_FLOORS=(0.0,.08,.12,.16,.20,.24)
MASS_FLOORS=(.20,.25,.30,.325,.35,.375,.40)
ST_FLOORS=(-.80,-.70,-.60)
ORIG_FLOORS=(-.35,-.25,-.15,-.057777777777777706)

def pair_mass(p2,pc,tickets):
    vals={}
    for s in BOATS:
      for t in BOATS:
        if s==t: continue
        vals[(s,t)]=math.exp(
          live.ALPHA2*math.log(max(float(p2[s]),1e-12))+
          (1-live.ALPHA2)*math.log(max(float(pc[(s,t)]),1e-12))
        )
    den=sum(vals.values())
    return sum(vals[x]/den for x in tickets)

def met(q):
    n=len(q); pay=float(q.payout_if_bet.sum()) if n else 0.0
    return {'R':int(n),'head4':int(q.head4.sum()) if n else 0,
            'head4_rate':100*float(q.head4.mean()) if n else np.nan,
            'exact3':int(q.raw_hit.sum()) if n else 0,
            'exact3_rate':100*float(q.raw_hit.mean()) if n else np.nan,
            'payout':pay,'ROI':100*pay/(10000*n) if n else np.nan}

def fullmet(q):
    o={}
    for name,z in [('all',q),('dev',q[q.month.isin(DEV)]),('support',q[q.month.isin(SUP)])]:
        for k,v in met(z).items(): o[f'{name}_{k}']=v
    mr=[]
    for m in MONTHS:
        mm=met(q[q.month.eq(m)])
        for k,v in mm.items(): o[f'{m}_{k}']=v
        if mm['R']: mr.append(mm['ROI'])
    o['monthly_floor_ROI']=min(mr) if mr else np.nan
    o['dev_monthly_floor_ROI']=min(o[f'{m}_ROI'] for m in DEV if o[f'{m}_R'])
    o['support_monthly_floor_ROI']=min(o[f'{m}_ROI'] for m in SUP if o[f'{m}_R'])
    return o

def main():
    p=os.environ.get('EXPANDED_POOL')
    if not p: raise RuntimeError('EXPANDED_POOL missing')
    pool=pd.read_csv(p,dtype={'race_code':str})
    pool['race_code']=pool.race_code.astype(str).str.zfill(12)
    if len(pool)!=226: raise RuntimeError(f'pool drift {len(pool)} != 226')
    if any(pool.month.astype(str).str.startswith('2026-09')): raise RuntimeError('SEPTEMBER OUTCOME ACCESS')
    if int(pool.is_old164.sum())!=164: raise RuntimeError('old164 subset drift')

    codes=set(pool.race_code)
    d=oddsmod.source_rows(codes,'2026-04-01','2026-08-31')
    d['race_code']=d.race_code.astype(str).str.zfill(12)
    coverage=set(d.race_code)
    if coverage!=codes:
        missing=sorted(codes-coverage)
        raise RuntimeError(f'V93_FEATURE_COVERAGE {len(coverage)}/{len(codes)} missing={missing[:12]}')

    long=oddsmod.build_long_all(d)
    art=load_artifact(); sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features'])
    hpfile=os.environ.get('HEADPROB_SCORED')
    if hpfile:
        hps=pd.read_csv(hpfile,dtype={'race_code':str})[['race_code','head_prob']].copy()
        hps['race_code']=hps.race_code.astype(str).str.zfill(12)
    else:
        hps=hpmod.headprob_scores(); hps['race_code']=hps.race_code.astype(str).str.zfill(12)
    hpmap=dict(zip(hps.race_code,hps.head_prob))
    truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third)))
           for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}
    pmeta=pool.set_index('race_code')
    odds_cache={}; rows=[]; excluded_odds=[]

    for code,g in long.groupby('race_code'):
        sr=[]
        for _,r in g.iterrows():
            x={'boat':int(r.boat)}; x.update({f:r[f] for f in sf}); sr.append(x)
        p2=score_second(sr,art)
        pc=score_conditional_third(oddsmod.conditional_rows(g,sf,cf),art)
        tickets=live.production_tickets(p2,pc)
        pairs=[tuple(map(int,x.split('-')[1:])) for x in tickets]
        mass=pair_mass(p2,pc,pairs)
        ds=str(g.date.iloc[0]); mon=ds[:7]
        oq=odds_cache.setdefault(ds,oddsmod.odds_for_date(ds))
        oo=oq[oq.race_code.astype(str)==str(code)] if len(oq) else oq
        if len(oo)!=1:
            if int(pmeta.loc[code].is_old164)==1:
                raise RuntimeError(f'ODDS_COVERAGE_OLD164 {code} {len(oo)}')
            excluded_odds.append({'race_code':code,'reason':f'odds_rows_{len(oo)}'})
            continue
        ovs=[]
        for t in tickets:
            v=pd.to_numeric(oo.iloc[0].get(t),errors='coerce')
            if pd.isna(v) or float(v)<=0:
                if int(pmeta.loc[code].is_old164)==1:
                    raise RuntimeError(f'ODDS_BAD_OLD164 {code} {t}')
                excluded_odds.append({'race_code':code,'reason':f'bad_ticket_odds_{t}'})
                ovs=[]
                break
            ovs.append(float(v))
        if not ovs:
            continue
        comp=live.composite_odds(ovs)
        actual=truth.get(str(code))
        actual_combo=f'4-{actual[1]}-{actual[2]}' if actual and actual[0]==4 else ''
        hit=bool(actual_combo and actual_combo in tickets)
        stakes={x['combo']:x['stake'] for x in live.dutch(tickets,ovs)}
        payout=float(stakes.get(actual_combo,0))*float(oo.iloc[0].get(actual_combo,0)) if hit else 0.0
        m=pmeta.loc[code]
        hp=float(hpmap.get(code,np.nan))
        if not np.isfinite(hp): raise RuntimeError(f'HEADPROB_MISSING {code}')
        rows.append({
          'date':ds,'month':mon,'race_code':code,
          'is_old164':int(m.is_old164),'head4':int(actual is not None and actual[0]==4),
          'head_prob':hp,'opponent_mass':mass,'composite_odds':comp,
          'quality':hp+1.50*mass,'st4_adv_inside':float(m.st4_adv_inside),
          'orig4_adv_inside':float(m.orig4_adv_inside),'tickets':len(tickets),
          'raw_hit':int(hit),'payout_if_bet':payout,
        })
    z=pd.DataFrame(rows)
    if len(z)+len(excluded_odds)!=226: raise RuntimeError(f'coverage accounting rows={len(z)} excluded={len(excluded_odds)}')
    if int(z.is_old164.sum())!=164: raise RuntimeError('old164 lost during odds fail-closed')

    # Reconstruct the frozen 120R only inside the old164 candidate.
    z['base77']=z.is_old164.eq(1) & (
      ((z.composite_odds>=7.0)&(z.opponent_mass>=.425)) |
      ((z.composite_odds<7.0)&(z.head_prob>=.22)&(z.opponent_mass>=.375)&(z.composite_odds>=3.0))
    )
    z['base120']=z.base77 | (
      z.is_old164.eq(1) & (~z.base77) & (z.composite_odds>=2.5) & (z.quality>=.82)
    )
    base=z[z.base120].copy(); bm=fullmet(base)
    if bm['all_R']!=120 or abs(bm['all_ROI']-127.72166666666666)>.02:
        raise RuntimeError(f'base120 parity failed R={bm["all_R"]} ROI={bm["all_ROI"]}')

    grid=[]
    for cf in COMP_FLOORS:
      for qc in Q_CUTS:
       for hf in HP_FLOORS:
        for mf in MASS_FLOORS:
         for sfloor in ST_FLOORS:
          for ofloor in ORIG_FLOORS:
            add=(~z.base120)&z.composite_odds.ge(cf)&z.quality.ge(qc)&z.head_prob.ge(hf)&z.opponent_mass.ge(mf)&z.st4_adv_inside.ge(sfloor)&z.orig4_adv_inside.ge(ofloor)
            sel=z.base120|add
            q=z[sel]
            mm=fullmet(q)
            outside=int((add & z.is_old164.eq(0)).sum())
            grid.append({
              'comp_floor':cf,'quality_cut':qc,'head_floor':hf,'mass_floor':mf,
              'st_floor':sfloor,'orig_floor':ofloor,
              'added_R':int(add.sum()),'added_outside164_R':outside,
              **mm
            })
    g=pd.DataFrame(grid)

    # Target volume profiles chosen using Apr-Jun outcomes only.
    targets={}
    for label,lo,hi in [('160R',155,169),('180R',170,189),('200R',190,209),('220R',210,226)]:
        e=g[g.all_R.between(lo,hi)].copy()
        if e.empty: continue
        e['target_mid_dist']=(e.all_R-(lo+hi)/2).abs()
        e=e.sort_values(
          ['dev_monthly_floor_ROI','dev_ROI','dev_head4_rate','target_mid_dist','all_R'],
          ascending=[False,False,False,True,False]
        )
        targets[label]=e.iloc[0].to_dict()

    # Label-exposed diagnostics only: identify max volume that still has every month >=100,
    # but never use this row as the dev-selected recommendation.
    stable=g[(g.monthly_floor_ROI>=100)&(g.all_ROI>=bm['all_ROI'])].copy()
    stable_best=stable.sort_values(['all_R','all_ROI'],ascending=[False,False]).iloc[0].to_dict() if len(stable) else None

    g.to_csv(OUT/'expanded_grid.csv',index=False)
    z.to_csv(OUT/'race_detail_226.csv',index=False)
    pd.DataFrame(list(targets.values())).to_csv(OUT/'dev_selected_targets.csv',index=False)

    result={
      'pool_R':226,
      'verified_odds_pool_R':int(len(z)),
      'excluded_no_verified_odds_R':int(len(excluded_odds)),
      'excluded_no_verified_odds':excluded_odds,
      'base120':bm,
      'grid_cells':int(len(g)),
      'dev_selected_targets':targets,
      'all_months_100_diagnostic_max_volume':stable_best,
      'selection_of_targets_used_support_outcomes':False,
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print('HEAD4_EXPANDED_POOL_STAGE2_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__':main()
