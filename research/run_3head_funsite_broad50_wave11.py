from __future__ import annotations
import itertools, json, warnings
from collections import Counter
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave6 import build_pre, load_canonical

warnings.filterwarnings("ignore")

WINDOWS=[21,28,42]
BANDS=[(1,6),(1,8),(1,10),(1,12)]
QS=[.75,.80,.85,.875,.90,.925,.95,.975]
DISCOVERY_SUPPORTS=[15,20,30,50,75,100]
FEB_SUPPORTS=[20,30,50,75,100]
BASE_SIGNALS=[
  'sig_vs1_全国2連対率','sig_vs2_全国2連対率','sig_vs4_全国2連対率',
  'sig_vs1_全国平均ST','sig_vs2_全国平均ST','sig_vs4_全国平均ST',
  'sig_vs1_当地2連対率','sig_vs2_当地2連対率','sig_vs4_当地2連対率',
  'sig_vs1_モーター2連対率','sig_vs2_モーター2連対率','sig_vs4_モーター2連対率',
  'sig_attack_player_inner','sig_attack_start_inner','sig_attack_motor_inner',
  'sig_attack_recent_inner','sig_b1_pressure','sig_b2_wall_break','sig_b4_counter_margin'
]

def pct_ref(ref,x):
    a=np.asarray(ref,float);a=a[np.isfinite(a)];a=np.sort(a)
    xx=np.asarray(x,float);out=np.full(len(xx),np.nan)
    if len(a)==0:return out
    ok=np.isfinite(xx)
    out[ok]=np.searchsorted(a,xx[ok],side='right')/len(a)
    return out

def prepare_base(train,target,signals,positive):
    trm=[];txm=[];used=[]
    for c in signals:
        if c not in train.columns or c not in target.columns:continue
        tr=pd.to_numeric(train[c],errors='coerce').to_numpy(float)
        tx=pd.to_numeric(target[c],errors='coerce').to_numpy(float)
        if np.isfinite(tr).sum()<50:continue
        ptr=pct_ref(tr,tr);ptx=pct_ref(tr,tx)
        if positive:
            ptr=np.where(np.isfinite(tr)&(tr>0),ptr,0.0)
            ptx=np.where(np.isfinite(tx)&(tx>0),ptx,0.0)
        trm.append(ptr);txm.append(ptx);used.append(c)
    return np.column_stack(trm),np.column_stack(txm),used

def interaction_name(cols):
    return 'X'.join(cols)

def interaction_scores(train,target,interactions,positive):
    needed=sorted(set(c for t in interactions for c in t))
    btr,btx,used=prepare_base(train,target,needed,positive)
    pos={c:i for i,c in enumerate(used)}
    out={}
    for tup in interactions:
        if not all(c in pos for c in tup):continue
        it=[pos[c] for c in tup]
        ptr=np.prod(btr[:,it],axis=1)
        ptx=np.prod(btx[:,it],axis=1)
        if positive:
            ref=ptr[np.isfinite(ptr)&(ptr>0)]
            sc=pct_ref(ref,ptx) if len(ref) else np.zeros(len(target))
            sc=np.where(np.isfinite(ptx)&(ptx>0),sc,0.0)
        else:
            sc=pct_ref(ptr,ptx)
        out[interaction_name(tup)]=sc
    return out

def walk_scores(history,target,interactions):
    rows=[]
    target=target.sort_values(['date','rc']).copy()
    for dayv in sorted(target.date.dt.normalize().unique()):
        day=pd.Timestamp(dayv)
        today=target[target.date.dt.normalize()==day].copy()
        for window in WINDOWS:
            tr=history[(history.date<day)&(history.date>=day-pd.Timedelta(days=window))].copy()
            if len(tr)<500:continue
            for mode,positive in [('pct',False),('positive',True)]:
                scores=interaction_scores(tr,today,interactions,positive)
                base=today[['rc','date','venue','race_no','y']].copy()
                base['window']=window;base['gate_mode']=mode
                for name,val in scores.items():base['i_'+name]=val
                rows.append(base)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def build_cache(pred):
    cache={}
    for window in WINDOWS:
      for mode in ['pct','positive']:
        sub=pred[(pred.window==window)&(pred.gate_mode==mode)].copy()
        if len(sub)==0:continue
        arr={
          'rn':pd.to_numeric(sub.race_no,errors='coerce').to_numpy(float),
          'day':sub.date.dt.day.to_numpy(),
          'y':sub.y.to_numpy(dtype=int),
          'venue':pd.factorize(sub.venue.astype(str))[0]
        }
        for c in sub.columns:
            if c.startswith('i_'):arr[c]=pd.to_numeric(sub[c],errors='coerce').to_numpy(float)
        cache[(window,mode)]=arr
    return cache

def met(mask,arr):
    m=np.asarray(mask,bool);n=int(m.sum());y=arr['y']
    return {'n':n,'hits':int(y[m].sum()) if n else 0,
            'rate':float(y[m].mean()) if n else None,
            'venues':int(np.unique(arr['venue'][m]).size) if n else 0}

def candidate_universe(interactions):
    out=[]
    for window in WINDOWS:
      for mode in ['pct','positive']:
       for band in BANDS:
        for tup in interactions:
         name=interaction_name(tup)
         for q in QS:
          out.append({'window':window,'gate_mode':mode,'band':list(band),
                      'interaction':name,'members':list(tup),'q':q})
    return out

def evaluate(cache,c):
    key=(c['window'],c['gate_mode'])
    if key not in cache:
        return None
    arr=cache[key]
    ikey='i_'+c['interaction']
    if ikey not in arr:
        return None
    rn=arr['rn'];lo,hi=c['band']
    m=(rn>=lo)&(rn<=hi)&(arr[ikey]>=c['q'])
    d=arr['day'];z=dict(c)
    z['h1']=met(m&(d<=15),arr);z['h2']=met(m&(d>=16),arr)
    return z

def worst(z):
    if z['h1']['rate'] is None or z['h2']['rate'] is None:return -1
    return min(z['h1']['rate'],z['h2']['rate'])

def combined(z):
    n=z['h1']['n']+z['h2']['n'];h=z['h1']['hits']+z['h2']['hits']
    return h/n if n else -1

def stratified_freeze(evals):
    chosen=[]
    strata={}
    for mn in DISCOVERY_SUPPORTS:
        pool=[z for z in evals if z['h1']['n']>=mn and z['h2']['n']>=mn and
              z['h1']['venues']>=8 and z['h2']['venues']>=8]
        pool=sorted(pool,key=lambda z:(worst(z),combined(z),z['h1']['n']+z['h2']['n']),reverse=True)
        top=pool[:25]
        strata[str(mn)]={'candidate_count':len(pool),'top_worst_half':worst(top[0]) if top else None}
        chosen.extend(top)
    seen=set();uniq=[]
    for z in chosen:
        key=(z['window'],z['gate_mode'],tuple(z['band']),z['interaction'],z['q'])
        if key in seen:continue
        seen.add(key);uniq.append(z)
    return uniq,strata

def top_signals_from_pairs(frozen,n=8):
    cnt=Counter()
    for z in frozen[:100]:
        for c in z['members']:cnt[c]+=1
    # Deterministic tie break by signal name.
    return [x[0] for x in sorted(cnt.items(),key=lambda kv:(-kv[1],kv[0]))[:n]]

def evaluate_frozen_on_feb(pred,frozen):
    cache=build_cache(pred);out=[]
    available=set()
    for arr in cache.values():
        available.update(c[2:] for c in arr if c.startswith('i_'))
    for z in frozen:
        if z['interaction'] not in available:continue
        c={k:z[k] for k in ['window','gate_mode','band','interaction','members','q']}
        z=evaluate(cache,c)
        if z is not None:out.append(z)
    return out

def summarize(z):
    if z is None:return None
    n=z['h1']['n']+z['h2']['n'];hits=z['h1']['hits']+z['h2']['hits']
    return {**z,'worst_half_rate':worst(z),'combined_n':n,
            'combined_hits':hits,'combined_rate':hits/n if n else None}

def frontier(evals):
    out={}
    for mn in FEB_SUPPORTS:
        pool=[z for z in evals if z['h1']['n']>=mn and z['h2']['n']>=mn and
              z['h1']['venues']>=8 and z['h2']['venues']>=8]
        best=max(pool,key=lambda z:(worst(z),combined(z),z['h1']['n']+z['h2']['n'])) if pool else None
        out[str(mn)]={'candidate_count':len(pool),'best_worst_half':summarize(best)}
    return out

def main():
    canon=load_canonical()

    dec,dres,da=build_pre('2025-12-01','2025-12-31',True)
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)

    # Continue the established cross-source safety check against canonical February.
    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    dec=dec.merge(dres[['rc','result_winner']],on='rc',how='inner')
    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    dec['y']=(dec.result_winner==3).astype(int);jan['y']=(jan.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    signals=[c for c in BASE_SIGNALS if c in dec.columns and c in jan.columns and c in feb.columns]
    pairs=list(itertools.combinations(signals,2))

    # Stage A: pair discovery is January-only using December + prior-January history.
    jan_hist=pd.concat([dec,jan],ignore_index=True,sort=False)
    jan_pair_pred=walk_scores(jan_hist,jan,pairs)
    jan_pair_cache=build_cache(jan_pair_pred)
    pair_evals=[z for c in candidate_universe(pairs) if (z:=evaluate(jan_pair_cache,c)) is not None]
    frozen_pairs,pair_strata=stratified_freeze(pair_evals)

    # Stage B: choose only the signal vocabulary for triples from January pair evidence.
    top_signals=top_signals_from_pairs(frozen_pairs,8)
    triples=list(itertools.combinations(top_signals,3))
    jan_triple_pred=walk_scores(jan_hist,jan,triples) if triples else pd.DataFrame()
    triple_evals=[]
    if len(jan_triple_pred):
        tc=build_cache(jan_triple_pred)
        triple_evals=[z for c in candidate_universe(triples) if (z:=evaluate(tc,c)) is not None]
    frozen_triples,triple_strata=stratified_freeze(triple_evals) if triple_evals else ([],{})

    # Freeze formula identities from January before any February scoring.
    jan_frozen=frozen_pairs+frozen_triples
    seen=set();frozen=[]
    for z in sorted(jan_frozen,key=lambda z:(worst(z),combined(z)),reverse=True):
        key=(z['window'],z['gate_mode'],tuple(z['band']),z['interaction'],z['q'])
        if key in seen:continue
        seen.add(key);frozen.append(z)

    frozen_interactions=[]
    tup_seen=set()
    for z in frozen:
        t=tuple(z['members'])
        if t not in tup_seen:
            tup_seen.add(t);frozen_interactions.append(t)

    # One-shot February transfer. Formula selection above is already complete.
    feb_hist=pd.concat([dec,jan,feb],ignore_index=True,sort=False)
    feb_pred=walk_scores(feb_hist,feb,frozen_interactions)
    feb_evals=evaluate_frozen_on_feb(feb_pred,frozen)
    feb_front=frontier(feb_evals)

    baseline={'20':0.391304347826087,'30':0.375,'50':0.34408602150537637,
              '75':0.34408602150537637,'100':0.3235294117647059}
    improvement={}
    for k,v in feb_front.items():
        z=v['best_worst_half']
        improvement[k]=(z['worst_half_rate']-baseline[k]) if z else None

    out={
      'policy':{
        'interaction_discovery_january_only':True,
        'december_history_for_january_walkforward':True,
        'february_one_shot_transfer':True,
        'february_does_not_choose_formulas':True,
        'march_outcomes_opened':False,'september_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'dec':da,'jan':ja,'feb':fa},
      'rows':{'dec':len(dec),'jan':len(jan),'feb':len(feb)},
      'base_signal_count':len(signals),'pair_count':len(pairs),
      'pair_discovery_strata':pair_strata,
      'top_signals_for_triples':top_signals,'triple_count':len(triples),
      'triple_discovery_strata':triple_strata,
      'frozen_candidate_count':len(frozen),
      'frozen_interaction_count':len(frozen_interactions),
      'feb_transfer_candidate_count':len(feb_evals),
      'feb_support_frontier':feb_front,
      'wave9_baseline':baseline,'improvement_vs_wave9':improvement
    }
    with open('research_3head_funsite_broad50_wave11_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
