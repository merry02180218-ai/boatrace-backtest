from __future__ import annotations
import json
import pandas as pd

from run_3head_funsite_broad50_wave7 import (
    WINDOWS, build_pre, load_canonical, curated_features, walk_predictions,
    candidate_universe, evaluate_candidate
)

SUPPORTS=[20,30,50,75,100,150,200]

def public(z):
    return {k:v for k,v in z.items() if not k.startswith('_')}

def summarize(z):
    if z is None:return None
    h1,h2=z['h1'],z['h2']
    n=h1['n']+h2['n']
    hits=h1['hits']+h2['hits']
    eligible=[w for w in z['weeks'] if w['n']>=5 and w['rate'] is not None]
    out=public(z)
    out.update({
        'worst_half_rate':min(h1['rate'],h2['rate']) if h1['rate'] is not None and h2['rate'] is not None else None,
        'combined_n':n,
        'combined_hits':hits,
        'combined_rate':hits/n if n else None,
        'eligible_week_count':len(eligible),
        'eligible_week_min_rate':min((w['rate'] for w in eligible),default=None),
        'eligible_week_mean_rate':sum(w['rate'] for w in eligible)/len(eligible) if eligible else None,
    })
    return out

def main():
    canon=load_canonical()
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:
        raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    jan['y']=(jan.result_winner==3).astype(int)

    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(
        feb.drop(columns=['date']),on='rc',how='inner'
    )
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    all_pre=pd.concat([jan,feb],ignore_index=True,sort=False)
    feats=curated_features(all_pre)
    for fr in [jan,feb]:
        for c in feats:
            if c not in fr.columns:fr[c]=float('nan')

    hist=pd.concat([jan,feb],ignore_index=True,sort=False)
    pred=walk_predictions(hist,feb,WINDOWS,feats)

    evals=[evaluate_candidate(pred,c) for c in candidate_universe(pred)]

    frontier={}
    for mn in SUPPORTS:
        pool=[z for z in evals if
              z['h1']['n']>=mn and z['h2']['n']>=mn and
              z['h1']['venues']>=8 and z['h2']['venues']>=8 and
              z['h1']['rate'] is not None and z['h2']['rate'] is not None]
        if not pool:
            frontier[str(mn)]={
                'candidate_count':0,
                'best_worst_half':None,
                'best_combined':None
            }
            continue

        best_worst=max(
            pool,
            key=lambda z:(
                min(z['h1']['rate'],z['h2']['rate']),
                (z['h1']['hits']+z['h2']['hits'])/(z['h1']['n']+z['h2']['n']),
                z['h1']['n']+z['h2']['n']
            )
        )
        best_combined=max(
            pool,
            key=lambda z:(
                (z['h1']['hits']+z['h2']['hits'])/(z['h1']['n']+z['h2']['n']),
                min(z['h1']['rate'],z['h2']['rate']),
                z['h1']['n']+z['h2']['n']
            )
        )
        frontier[str(mn)]={
            'candidate_count':len(pool),
            'best_worst_half':summarize(best_worst),
            'best_combined':summarize(best_combined)
        }

    # Also show the unrestricted useful-support Pareto top, ranked by worst-half precision,
    # but exclude tiny candidates under 20 per half.
    useful=[z for z in evals if
            z['h1']['n']>=20 and z['h2']['n']>=20 and
            z['h1']['venues']>=8 and z['h2']['venues']>=8 and
            z['h1']['rate'] is not None and z['h2']['rate'] is not None]
    useful=sorted(
        useful,
        key=lambda z:(
            min(z['h1']['rate'],z['h2']['rate']),
            (z['h1']['hits']+z['h2']['hits'])/(z['h1']['n']+z['h2']['n']),
            z['h1']['n']+z['h2']['n']
        ),
        reverse=True
    )

    out={
        'policy':{
            'wave7_family_unchanged':True,
            'february_only_diagnostic':True,
            'march_outcomes_opened':False,
            'september_outcomes_read':False,
            'production_v288_changed':False
        },
        'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
        'source_audit':{'jan':ja,'feb':fa},
        'rows':{'jan':len(jan),'feb':len(feb),'feb_prediction_rows':len(pred)},
        'features':len(feats),
        'candidate_count':len(evals),
        'support_frontier':frontier,
        'useful_top30':[summarize(z) for z in useful[:30]]
    }
    with open('research_3head_funsite_broad50_wave9_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
