from __future__ import annotations
import itertools, json
from collections import Counter
import pandas as pd

from run_3head_funsite_broad50_wave11 import (
    BASE_SIGNALS, DISCOVERY_SUPPORTS, FEB_SUPPORTS,
    build_pre, load_canonical, walk_scores, build_cache,
    candidate_universe, evaluate, interaction_name, summarize, frontier
)

TOP_PER_STRATUM=25

def candidate_key(c):
    return (c['window'],c['gate_mode'],tuple(c['band']),c['interaction'],c['q'])

def min4(dec_z,jan_z):
    rates=[dec_z['h1']['rate'],dec_z['h2']['rate'],jan_z['h1']['rate'],jan_z['h2']['rate']]
    if any(x is None for x in rates):return -1
    return min(rates)

def joint_combined(dec_z,jan_z):
    n=dec_z['h1']['n']+dec_z['h2']['n']+jan_z['h1']['n']+jan_z['h2']['n']
    h=dec_z['h1']['hits']+dec_z['h2']['hits']+jan_z['h1']['hits']+jan_z['h2']['hits']
    return h/n if n else -1

def passes(z,mn):
    return (
        z['h1']['n']>=mn and z['h2']['n']>=mn and
        z['h1']['venues']>=8 and z['h2']['venues']>=8 and
        z['h1']['rate'] is not None and z['h2']['rate'] is not None
    )

def joint_freeze(dec_cache,jan_cache,interactions):
    evals=[]
    for c in candidate_universe(interactions):
        dz=evaluate(dec_cache,c)
        jz=evaluate(jan_cache,c)
        if dz is None or jz is None:continue
        evals.append({'candidate':c,'dec':dz,'jan':jz,'persistent_worst':min4(dz,jz),
                      'persistent_combined':joint_combined(dz,jz)})
    chosen=[];strata={}
    for mn in DISCOVERY_SUPPORTS:
        pool=[z for z in evals if passes(z['dec'],mn) and passes(z['jan'],mn)]
        pool=sorted(pool,key=lambda z:(z['persistent_worst'],z['persistent_combined'],
                                       z['dec']['h1']['n']+z['dec']['h2']['n']+
                                       z['jan']['h1']['n']+z['jan']['h2']['n']),reverse=True)
        strata[str(mn)]={
            'candidate_count':len(pool),
            'best_persistent_worst':pool[0]['persistent_worst'] if pool else None,
            'best':pool[0] if pool else None
        }
        chosen.extend(pool[:TOP_PER_STRATUM])
    out=[];seen=set()
    for z in sorted(chosen,key=lambda x:(x['persistent_worst'],x['persistent_combined']),reverse=True):
        k=candidate_key(z['candidate'])
        if k in seen:continue
        seen.add(k);out.append(z)
    return out,strata,evals

def top_signals(joint_frozen,n=8):
    cnt=Counter()
    for z in joint_frozen[:120]:
        for c in z['candidate']['members']:cnt[c]+=1
    return [x[0] for x in sorted(cnt.items(),key=lambda kv:(-kv[1],kv[0]))[:n]]

def frozen_settings(joint_pairs,joint_triples):
    rows=joint_pairs+joint_triples
    rows=sorted(rows,key=lambda z:(z['persistent_worst'],z['persistent_combined']),reverse=True)
    out=[];seen=set()
    for z in rows:
        c=z['candidate'];k=candidate_key(c)
        if k in seen:continue
        seen.add(k);out.append(c)
    return out

def frozen_interactions(settings):
    out=[];seen=set()
    for c in settings:
        t=tuple(c['members'])
        if t not in seen:seen.add(t);out.append(t)
    return out

def eval_exact_feb(pred,settings):
    cache=build_cache(pred);out=[]
    for c in settings:
        z=evaluate(cache,c)
        if z is not None:out.append(z)
    return out

def main():
    canon=load_canonical()
    nov,nres,na=build_pre('2025-11-01','2025-11-30',True)
    dec,dres,da=build_pre('2025-12-01','2025-12-31',True)
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    nov=nov.merge(nres[['rc','result_winner']],on='rc',how='inner')
    dec=dec.merge(dres[['rc','result_winner']],on='rc',how='inner')
    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    for x in [nov,dec,jan]:x['y']=(x.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    signals=[c for c in BASE_SIGNALS if all(c in x.columns for x in [nov,dec,jan,feb])]
    pairs=list(itertools.combinations(signals,2))

    dec_hist=pd.concat([nov,dec],ignore_index=True,sort=False)
    jan_hist=pd.concat([nov,dec,jan],ignore_index=True,sort=False)
    dec_pair=walk_scores(dec_hist,dec,pairs)
    jan_pair=walk_scores(jan_hist,jan,pairs)
    dec_pc=build_cache(dec_pair);jan_pc=build_cache(jan_pair)
    joint_pairs,pair_strata,_=joint_freeze(dec_pc,jan_pc,pairs)

    sigs=top_signals(joint_pairs,8)
    triples=list(itertools.combinations(sigs,3))
    joint_triples=[];triple_strata={}
    if triples:
        dec_tri=walk_scores(dec_hist,dec,triples)
        jan_tri=walk_scores(jan_hist,jan,triples)
        joint_triples,triple_strata,_=joint_freeze(build_cache(dec_tri),build_cache(jan_tri),triples)

    settings=frozen_settings(joint_pairs,joint_triples)
    interactions=frozen_interactions(settings)

    feb_hist=pd.concat([nov,dec,jan,feb],ignore_index=True,sort=False)
    feb_pred=walk_scores(feb_hist,feb,interactions)
    feb_evals=eval_exact_feb(feb_pred,settings)
    feb_front=frontier(feb_evals)

    wave11={'20':0.40,'30':0.3181818181818182,'50':0.2857142857142857,
            '75':0.25,'100':0.24}
    wave9={'20':0.391304347826087,'30':0.375,'50':0.34408602150537637,
           '75':0.34408602150537637,'100':0.3235294117647059}
    imp11={};imp9={}
    for k,v in feb_front.items():
        z=v['best_worst_half'];r=z['worst_half_rate'] if z else None
        imp11[k]=(r-wave11[k]) if r is not None else None
        imp9[k]=(r-wave9[k]) if r is not None else None

    out={
      'policy':{
        'pair_triple_discovery_pre_february_only':True,
        'december_and_january_persistence_required':True,
        'february_one_shot_transfer':True,
        'february_does_not_choose_formulas_or_settings':True,
        'march_outcomes_opened':False,'september_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'nov':na,'dec':da,'jan':ja,'feb':fa},
      'rows':{'nov':len(nov),'dec':len(dec),'jan':len(jan),'feb':len(feb)},
      'base_signal_count':len(signals),'pair_count':len(pairs),
      'pair_persistence_strata':pair_strata,
      'top_signals_for_triples':sigs,'triple_count':len(triples),
      'triple_persistence_strata':triple_strata,
      'frozen_setting_count':len(settings),'frozen_interaction_count':len(interactions),
      'feb_transfer_candidate_count':len(feb_evals),
      'feb_support_frontier':feb_front,
      'improvement_vs_wave11':imp11,'improvement_vs_wave9':imp9
    }
    with open('research_3head_funsite_broad50_wave13_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
