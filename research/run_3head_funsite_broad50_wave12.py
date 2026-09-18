from __future__ import annotations
import itertools, json, math
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave11 import (
    BASE_SIGNALS, WINDOWS, BANDS, DISCOVERY_SUPPORTS, FEB_SUPPORTS,
    build_pre, load_canonical, walk_scores, build_cache, candidate_universe,
    evaluate, stratified_freeze, top_signals_from_pairs, interaction_name,
    worst, combined
)

TOPNS=[3,5,8,12,20,33]
JAN_FREEZE_TOP_PER_STRATUM=12

def reconstruct_january(dec,jan):
    signals=[c for c in BASE_SIGNALS if c in dec.columns and c in jan.columns]
    pairs=list(itertools.combinations(signals,2))
    hist=pd.concat([dec,jan],ignore_index=True,sort=False)

    pp=walk_scores(hist,jan,pairs)
    pc=build_cache(pp)
    pe=[z for c in candidate_universe(pairs) if (z:=evaluate(pc,c)) is not None]
    fp,_=stratified_freeze(pe)

    top_signals=top_signals_from_pairs(fp,8)
    triples=list(itertools.combinations(top_signals,3))
    tp=walk_scores(hist,jan,triples) if triples else pd.DataFrame()
    te=[]
    if len(tp):
        tc=build_cache(tp)
        te=[z for c in candidate_universe(triples) if (z:=evaluate(tc,c)) is not None]
    ft,_=stratified_freeze(te) if te else ([],{})

    frozen=fp+ft
    frozen=sorted(frozen,key=lambda z:(worst(z),combined(z),z['h1']['n']+z['h2']['n']),reverse=True)

    # One representative setting per exact interaction formula, selected only on January.
    reps=[];seen=set()
    for z in frozen:
        if z['interaction'] in seen:continue
        seen.add(z['interaction'])
        reps.append(z)
    return signals,pairs,triples,reps,pp,tp

def selected_rcs(pred,z):
    if pred is None or len(pred)==0:return set()
    sub=pred[(pred.window==z['window'])&(pred.gate_mode==z['gate_mode'])].copy()
    col='i_'+z['interaction']
    if col not in sub.columns:return set()
    rn=pd.to_numeric(sub.race_no,errors='coerce').to_numpy(float)
    lo,hi=z['band']
    sc=pd.to_numeric(sub[col],errors='coerce').to_numpy(float)
    m=(rn>=lo)&(rn<=hi)&(sc>=z['q'])
    return set(pd.to_numeric(sub.loc[m,'rc'],errors='coerce').dropna().astype(int).tolist())

def base_arrays(frame):
    x=frame[['rc','date','venue','y']].drop_duplicates('rc').sort_values(['date','rc']).copy()
    return x,{
      'rc':pd.to_numeric(x.rc,errors='coerce').astype(int).to_numpy(),
      'day':x.date.dt.day.to_numpy(),
      'y':x.y.to_numpy(dtype=int),
      'venue':pd.factorize(x.venue.astype(str))[0]
    }

def metric(mask,arr):
    m=np.asarray(mask,bool);n=int(m.sum());y=arr['y']
    return {'n':n,'hits':int(y[m].sum()) if n else 0,
            'rate':float(y[m].mean()) if n else None,
            'venues':int(np.unique(arr['venue'][m]).size) if n else 0}

def vote_matrix(frame,reps,pair_pred,triple_pred):
    _,arr=base_arrays(frame)
    idx={int(rc):i for i,rc in enumerate(arr['rc'])}
    mat=np.zeros((len(arr['rc']),len(reps)),dtype=np.int16)
    for j,z in enumerate(reps):
        pred=pair_pred if len(z['members'])==2 else triple_pred
        for rc in selected_rcs(pred,z):
            i=idx.get(int(rc))
            if i is not None:mat[i,j]=1
    return arr,mat

def eval_ensemble(arr,mat,n_top,k):
    n_top=min(n_top,mat.shape[1])
    votes=mat[:,:n_top].sum(axis=1)
    m=votes>=k
    d=arr['day']
    z={'n_top':n_top,'k':k}
    z['h1']=metric(m&(d<=15),arr);z['h2']=metric(m&(d>=16),arr)
    return z

def ensemble_universe(arr,mat):
    rows=[]
    for n in TOPNS:
        n=min(n,mat.shape[1])
        if n<1:continue
        ks={1,2,3,4,5,math.ceil(n*.25),math.ceil(n*.50),math.ceil(n*.75)}
        for k in sorted(x for x in ks if 1<=x<=n):
            rows.append(eval_ensemble(arr,mat,n,k))
    # dedup definitions when TOPNS collapse at available rep count
    out=[];seen=set()
    for z in rows:
        key=(z['n_top'],z['k'])
        if key not in seen:seen.add(key);out.append(z)
    return out

def freeze_ensembles(rows):
    chosen=[];strata={}
    for mn in DISCOVERY_SUPPORTS:
        pool=[z for z in rows if z['h1']['n']>=mn and z['h2']['n']>=mn and
              z['h1']['venues']>=8 and z['h2']['venues']>=8]
        pool=sorted(pool,key=lambda z:(worst(z),combined(z),z['h1']['n']+z['h2']['n']),reverse=True)
        strata[str(mn)]={'candidate_count':len(pool),'best':pool[0] if pool else None}
        chosen.extend(pool[:JAN_FREEZE_TOP_PER_STRATUM])
    out=[];seen=set()
    for z in chosen:
        key=(z['n_top'],z['k'])
        if key not in seen:seen.add(key);out.append(z)
    return out,strata

def feb_frontier(rows):
    out={}
    for mn in FEB_SUPPORTS:
        pool=[z for z in rows if z['h1']['n']>=mn and z['h2']['n']>=mn and
              z['h1']['venues']>=8 and z['h2']['venues']>=8]
        best=max(pool,key=lambda z:(worst(z),combined(z),z['h1']['n']+z['h2']['n'])) if pool else None
        if best:
            n=best['h1']['n']+best['h2']['n'];h=best['h1']['hits']+best['h2']['hits']
            best={**best,'worst_half_rate':worst(best),'combined_n':n,
                  'combined_hits':h,'combined_rate':h/n if n else None}
        out[str(mn)]={'candidate_count':len(pool),'best_worst_half':best}
    return out

def main():
    canon=load_canonical()
    dec,dres,da=build_pre('2025-12-01','2025-12-31',True)
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    dec=dec.merge(dres[['rc','result_winner']],on='rc',how='inner')
    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    dec['y']=(dec.result_winner==3).astype(int);jan['y']=(jan.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    signals,pairs,triples,reps,jpp,jtp=reconstruct_january(dec,jan)
    jarr,jmat=vote_matrix(jan,reps,jpp,jtp)
    jen=ensemble_universe(jarr,jmat)
    frozen,jstrata=freeze_ensembles(jen)

    # February replay uses exact January-selected representative formulas and ensemble definitions.
    interactions=[]
    seen=set()
    for z in reps:
        t=tuple(z['members'])
        if t not in seen:seen.add(t);interactions.append(t)
    feb_hist=pd.concat([dec,jan,feb],ignore_index=True,sort=False)
    fpairs=[t for t in interactions if len(t)==2]
    ftriples=[t for t in interactions if len(t)==3]
    fpp=walk_scores(feb_hist,feb,fpairs) if fpairs else pd.DataFrame()
    ftp=walk_scores(feb_hist,feb,ftriples) if ftriples else pd.DataFrame()
    farr,fmat=vote_matrix(feb,reps,fpp,ftp)

    feb_rows=[eval_ensemble(farr,fmat,z['n_top'],z['k']) for z in frozen]
    front=feb_frontier(feb_rows)

    wave11={'20':0.40,'30':0.3181818181818182,'50':0.2857142857142857,
            '75':0.25,'100':0.24}
    wave9={'20':0.391304347826087,'30':0.375,'50':0.34408602150537637,
           '75':0.34408602150537637,'100':0.3235294117647059}
    imp11={};imp9={}
    for k,v in front.items():
        z=v['best_worst_half']
        imp11[k]=None if not z else z['worst_half_rate']-wave11[k]
        imp9[k]=None if not z else z['worst_half_rate']-wave9[k]

    out={
      'policy':{
        'representatives_selected_january_only':True,
        'ensemble_selected_january_only':True,
        'february_one_shot_transfer':True,
        'march_outcomes_opened':False,'september_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'dec':da,'jan':ja,'feb':fa},
      'rows':{'dec':len(dec),'jan':len(jan),'feb':len(feb)},
      'representative_count':len(reps),
      'representatives':[{
         'interaction':z['interaction'],'members':z['members'],'window':z['window'],
         'gate_mode':z['gate_mode'],'band':z['band'],'q':z['q'],
         'jan_worst_half':worst(z),'jan_combined':combined(z)
      } for z in reps],
      'january_ensemble_strata':jstrata,
      'frozen_ensemble_count':len(frozen),
      'feb_transfer_candidate_count':len(feb_rows),
      'feb_support_frontier':front,
      'improvement_vs_wave11':imp11,
      'improvement_vs_wave9':imp9
    }
    with open('research_3head_funsite_broad50_wave12_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
