from __future__ import annotations
import itertools, json
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from run_3head_funsite_broad50_wave11 import (
    BASE_SIGNALS, WINDOWS, BANDS, QS, build_pre, load_canonical,
    walk_scores, candidate_universe, interaction_name
)

KS=[2,3,4]
CLUSTER_SUPPORTS=[5,8,12,16]
TOP_PER_CLUSTER=[1,2]
FREEZE_HALF_SUPPORTS=[15,20,30,50,75,100]
FEB_SUPPORTS=[20,30,50,75,100]
FIXED_TRIPLE_SIGNALS=[
    'sig_vs1_全国2連対率','sig_attack_player_inner','sig_b1_pressure',
    'sig_vs2_全国2連対率','sig_attack_start_inner',
    'sig_vs2_全国平均ST','sig_vs1_全国平均ST','sig_b2_wall_break'
]

def daily_descriptors(frame,signals):
    rows=[]
    for day,g in frame.groupby(frame.date.dt.normalize()):
        row={'date':pd.Timestamp(day)}
        for c in signals:
            x=pd.to_numeric(g[c],errors='coerce').to_numpy(float)
            x=x[np.isfinite(x)]
            if len(x)==0:
                med=q75=pos=np.nan
            else:
                med=float(np.median(x));q75=float(np.quantile(x,.75));pos=float(np.mean(x>0))
            row[f'{c}__med']=med
            row[f'{c}__q75']=q75
            row[f'{c}__pos']=pos
        rows.append(row)
    return pd.DataFrame(rows).sort_values('date').reset_index(drop=True)

def fit_regimes(descs,k):
    hist=pd.concat([descs['nov'],descs['dec'],descs['jan']],ignore_index=True,sort=False)
    raw_feats=[c for c in hist.columns if c!='date']
    hx=hist[raw_feats].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan)
    med=hx.median(numeric_only=True)
    feats=[c for c in raw_feats if c in med.index and np.isfinite(med[c])]
    if len(feats)<5:
        raise RuntimeError(f'insufficient finite regime features: {len(feats)}')
    med=med[feats]
    X=hx[feats].fillna(med).to_numpy(float)
    scaler=StandardScaler().fit(X)
    km=KMeans(n_clusters=k,random_state=140+k,n_init=30).fit(scaler.transform(X))
    maps={}
    for name,d in descs.items():
        z=d[feats].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan).fillna(med).to_numpy(float)
        lab=km.predict(scaler.transform(z))
        maps[name]={pd.Timestamp(dt).normalize():int(cl) for dt,cl in zip(d.date,lab)}
    return maps,{'k':k,'feature_count':len(feats),'dropped_all_nan_features':len(raw_feats)-len(feats),
                 'cluster_sizes':{str(int(a)):int(b) for a,b in pd.Series(km.labels_).value_counts().sort_index().items()}}

def pred_cache(pred,cluster_map):
    cache={}
    for w in WINDOWS:
      for mode in ['pct','positive']:
        sub=pred[(pred.window==w)&(pred.gate_mode==mode)].copy()
        if len(sub)==0:continue
        cache[(w,mode)]={
          'sub':sub,
          'rn':pd.to_numeric(sub.race_no,errors='coerce').to_numpy(float),
          'score_cols':{c[2:]:pd.to_numeric(sub[c],errors='coerce').to_numpy(float)
                        for c in sub.columns if c.startswith('i_')},
          'cluster':np.array([cluster_map.get(pd.Timestamp(x).normalize(),-1) for x in sub.date],dtype=int),
          'y':sub.y.to_numpy(dtype=int),
          'venue':sub.venue.astype(str).to_numpy(),
          'rc':pd.to_numeric(sub.rc,errors='coerce').to_numpy()
        }
    return cache

def candidate_mask(arr,c,cluster_id=None):
    sc=arr['score_cols'].get(c['interaction'])
    if sc is None:return None
    lo,hi=c['band']
    m=(arr['rn']>=lo)&(arr['rn']<=hi)&np.isfinite(sc)&(sc>=c['q'])
    if cluster_id is not None:m &= (arr['cluster']==cluster_id)
    return m

def met(mask,arr):
    m=np.asarray(mask,bool);n=int(m.sum())
    return {'n':n,'hits':int(arr['y'][m].sum()) if n else 0,
            'rate':float(arr['y'][m].mean()) if n else None,
            'venues':int(np.unique(arr['venue'][m]).size) if n else 0}

def eval_cluster(cache,c,cluster_id):
    arr=cache.get((c['window'],c['gate_mode']))
    if arr is None:return None
    m=candidate_mask(arr,c,cluster_id)
    return met(m,arr) if m is not None else None

def combined_month_stats(stats):
    n=sum(x['n'] for x in stats);h=sum(x['hits'] for x in stats)
    return h/n if n else -1

def rank_tuple(month_stats):
    rates=[x['rate'] for x in month_stats]
    if any(r is None for r in rates):return (-1,-1,-1)
    return (min(rates),combined_month_stats(month_stats),sum(x['n'] for x in month_stats))

def precompute_cluster_tops(caches,universe,k):
    # One scan per K. Keep only the top-2 rows needed for every support floor.
    best={(cl,sf):[] for cl in range(k) for sf in CLUSTER_SUPPORTS}
    for c in universe:
        for cl in range(k):
            stats=[eval_cluster(caches[m],c,cl) for m in ['nov','dec','jan']]
            if any(x is None for x in stats):continue
            key=rank_tuple(stats)
            if key[0] < 0:continue
            for sf in CLUSTER_SUPPORTS:
                if any(x['n']<sf or x['venues']<min(4,sf) for x in stats):continue
                arr=best[(cl,sf)]
                arr.append((key,c,stats))
                arr.sort(key=lambda z:z[0],reverse=True)
                if len(arr)>max(TOP_PER_CLUSTER):del arr[max(TOP_PER_CLUSTER):]
    return best

def choices_from_precomputed(best,k,support_floor,topn):
    out={}
    for cl in range(k):
        rows=best.get((cl,support_floor),[])[:topn]
        if len(rows)<topn:return None
        out[cl]=rows
    return out

def selected_rcs_for_candidate(cache,c,cluster_id):
    arr=cache.get((c['window'],c['gate_mode']))
    if arr is None:return set()
    m=candidate_mask(arr,c,cluster_id)
    if m is None:return set()
    return set(int(x) for x in arr['rc'][m] if np.isfinite(x))

def base_frame(frame):
    return frame[['rc','date','venue','y']].drop_duplicates('rc').sort_values(['date','rc']).copy()

def selector_metrics(frame,caches,cluster_choices,month_name,feb=False):
    selected=set()
    for cl,rows in cluster_choices.items():
        for _,c,_ in rows:
            selected |= selected_rcs_for_candidate(caches[month_name],c,cl)
    base=base_frame(frame)
    m=base.rc.astype(int).isin(selected).to_numpy()
    day=base.date.dt.day.to_numpy()
    if feb:
        m1=m&(day<=14);m2=m&(day>=15)
    else:
        m1=m&(day<=15);m2=m&(day>=16)
    def mm(mask):
        n=int(mask.sum());y=base.y.to_numpy(dtype=int)
        return {'n':n,'hits':int(y[mask].sum()) if n else 0,
                'rate':float(y[mask].mean()) if n else None,
                'venues':int(base.loc[mask,'venue'].nunique()) if n else 0}
    return {'h1':mm(m1),'h2':mm(m2),'selected_n':int(m.sum())}

def persistent_worst(diag):
    rates=[]
    for m in ['nov','dec','jan']:
        for h in ['h1','h2']:
            r=diag[m][h]['rate']
            if r is None:return -1
            rates.append(r)
    return min(rates)

def persistent_combined(diag):
    n=h=0
    for m in ['nov','dec','jan']:
        for half in ['h1','h2']:
            n+=diag[m][half]['n'];h+=diag[m][half]['hits']
    return h/n if n else -1

def build_variant(k,support_floor,topn,choices,frames,caches):
    diag={m:selector_metrics(frames[m],caches,choices,m,False) for m in ['nov','dec','jan']}
    return {
      'k':k,'cluster_support_floor':support_floor,'top_per_cluster':topn,
      'choices':{
        str(cl):[
          {'rank':list(key),'candidate':c,
           'nov':stats[0],'dec':stats[1],'jan':stats[2]}
          for key,c,stats in rows
        ] for cl,rows in choices.items()
      },
      'pre_feb':diag,
      'persistent_worst':persistent_worst(diag),
      'persistent_combined':persistent_combined(diag)
    }

def freeze_variants(variants):
    frozen=[];strata={}
    for mn in FREEZE_HALF_SUPPORTS:
        pool=[]
        for v in variants:
            ok=True
            for m in ['nov','dec','jan']:
                for h in ['h1','h2']:
                    z=v['pre_feb'][m][h]
                    if z['n']<mn or z['venues']<8:ok=False
            if ok:pool.append(v)
        pool=sorted(pool,key=lambda v:(v['persistent_worst'],v['persistent_combined'],
                                      sum(v['pre_feb'][m]['selected_n'] for m in ['nov','dec','jan'])),reverse=True)
        strata[str(mn)]={
          'candidate_count':len(pool),
          'best':pool[0] if pool else None
        }
        if pool:frozen.append(pool[0])
    out=[];seen=set()
    for v in frozen:
        key=(v['k'],v['cluster_support_floor'],v['top_per_cluster'])
        if key not in seen:seen.add(key);out.append(v)
    return out,strata

def feb_frontier(rows):
    out={}
    for mn in FEB_SUPPORTS:
        pool=[z for z in rows if z['feb']['h1']['n']>=mn and z['feb']['h2']['n']>=mn and
              z['feb']['h1']['venues']>=8 and z['feb']['h2']['venues']>=8]
        def key(z):
            a=z['feb']['h1'];b=z['feb']['h2']
            n=a['n']+b['n'];h=a['hits']+b['hits']
            return (min(a['rate'],b['rate']),h/n if n else -1,n)
        best=max(pool,key=key) if pool else None
        if best:
            a=best['feb']['h1'];b=best['feb']['h2'];n=a['n']+b['n'];h=a['hits']+b['hits']
            best={**best,'feb_worst_half_rate':min(a['rate'],b['rate']),
                  'feb_combined_n':n,'feb_combined_hits':h,'feb_combined_rate':h/n if n else None}
        out[str(mn)]={'candidate_count':len(pool),'best':best}
    return out

def main():
    canon=load_canonical()
    octo,_,oa=build_pre('2025-10-01','2025-10-31',False)
    nov,nres,na=build_pre('2025-11-01','2025-11-30',True)
    dec,dres,da=build_pre('2025-12-01','2025-12-31',True)
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    for frame,res in [(nov,nres),(dec,dres),(jan,jres)]:
        frame.drop(columns=['result_winner'],errors='ignore',inplace=True)
        frame.merge(res[['rc','result_winner']],on='rc',how='inner')
    nov=nov.merge(nres[['rc','result_winner']],on='rc',how='inner')
    dec=dec.merge(dres[['rc','result_winner']],on='rc',how='inner')
    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    for x in [nov,dec,jan]:x['y']=(x.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    frames={'nov':nov,'dec':dec,'jan':jan,'feb':feb}
    signals=[c for c in BASE_SIGNALS if all(c in x.columns for x in frames.values())]
    pairs=list(itertools.combinations(signals,2))
    triple_signals=[c for c in FIXED_TRIPLE_SIGNALS if c in signals]
    triples=list(itertools.combinations(triple_signals,3))
    interactions=pairs+triples
    universe=candidate_universe(interactions)

    descs={m:daily_descriptors(frames[m],signals) for m in frames}
    histories={
      'nov':pd.concat([octo,nov],ignore_index=True,sort=False),
      'dec':pd.concat([octo,nov,dec],ignore_index=True,sort=False),
      'jan':pd.concat([octo,nov,dec,jan],ignore_index=True,sort=False),
      'feb':pd.concat([octo,nov,dec,jan,feb],ignore_index=True,sort=False)
    }
    preds={m:walk_scores(histories[m],frames[m],interactions) for m in frames}

    all_variants=[];cluster_meta={}
    regime_maps={}
    for k in KS:
        maps,meta=fit_regimes(descs,k)
        cluster_meta[str(k)]=meta;regime_maps[k]=maps
        caches={m:pred_cache(preds[m],maps[m]) for m in frames}
        precomputed=precompute_cluster_tops(caches,universe,k)
        for sf in CLUSTER_SUPPORTS:
            for topn in TOP_PER_CLUSTER:
                choices=choices_from_precomputed(precomputed,k,sf,topn)
                if choices is None:continue
                all_variants.append(build_variant(k,sf,topn,choices,frames,caches))

    frozen,strata=freeze_variants(all_variants)
    feb_rows=[]
    for v in frozen:
        k=v['k'];maps=regime_maps[k]
        caches={m:pred_cache(preds[m],maps[m]) for m in frames}
        choices={}
        for cl,rows in v['choices'].items():
            choices[int(cl)]=[]
            for row in rows:
                choices[int(cl)].append((tuple(row['rank']),row['candidate'],[row['nov'],row['dec'],row['jan']]))
        fm=selector_metrics(feb,caches,choices,'feb',True)
        feb_rows.append({**v,'feb':fm})
    front=feb_frontier(feb_rows)

    wave9={'20':0.391304347826087,'30':0.375,'50':0.34408602150537637,
           '75':0.34408602150537637,'100':0.3235294117647059}
    imp={}
    for k,v in front.items():
        b=v['best'];imp[k]=(b['feb_worst_half_rate']-wave9[k]) if b else None

    out={
      'policy':{
        'regime_features_pre_only':True,'regime_fit_nov_dec_jan_unlabeled_distribution_only':True,
        'interaction_selection_nov_dec_jan_only':True,'february_one_shot_transfer':True,
        'march_outcomes_opened':False,'september_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'oct':oa,'nov':na,'dec':da,'jan':ja,'feb':fa},
      'rows':{'oct':len(octo),'nov':len(nov),'dec':len(dec),'jan':len(jan),'feb':len(feb)},
      'base_signal_count':len(signals),'pair_count':len(pairs),'fixed_triple_count':len(triples),
      'interaction_count':len(interactions),'candidate_setting_count':len(universe),
      'cluster_meta':cluster_meta,
      'selector_variant_count':len(all_variants),
      'pre_feb_freeze_strata':strata,
      'frozen_selector_count':len(frozen),
      'feb_frozen_results':feb_rows,
      'feb_support_frontier':front,
      'wave9_baseline':wave9,'improvement_vs_wave9':imp
    }
    with open('research_3head_funsite_broad50_wave14_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
