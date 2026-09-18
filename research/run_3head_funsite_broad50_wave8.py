from __future__ import annotations
import json
import pandas as pd

from run_3head_funsite_broad50_wave7 import (
    WINDOWS, build_pre, load_canonical, curated_features, walk_predictions,
    candidate_universe, evaluate_candidate, candidate_mask, metric
)

FLOORS=[
    {'name':'0.47','floor':.47,'min_half_n':25},
    {'name':'0.45','floor':.45,'min_half_n':30},
    {'name':'0.425','floor':.425,'min_half_n':40},
    {'name':'0.40','floor':.40,'min_half_n':50},
]

def qualifies(z,spec):
    a,b=z['h1'],z['h2'];floor=spec['floor'];mn=spec['min_half_n']
    if a['n']<mn or b['n']<mn or a['venues']<8 or b['venues']<8:return False
    if (a['rate'] or 0)<floor or (b['rate'] or 0)<floor:return False
    eligible=[w for w in z['weeks'] if w['n']>=5]
    return len(eligible)>=3 and sum((w['rate'] or 0)>=floor-.05 for w in eligible)>=3

def public(z):
    return {k:v for k,v in z.items() if not k.startswith('_')}

def march_eval(pred,cand):
    if cand is None:return None
    sub=pred[pred.window==cand['window']].copy()
    m=candidate_mask(sub,cand)
    sel=sub.loc[m].sort_values(['date','rc']).copy();n=len(sel);h=n//2
    return {'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
            'early_n':h,'early_hits':int(sel.iloc[:h].y.sum()),
            'late_n':n-h,'late_hits':int(sel.iloc[h:].y.sum()),
            'venue_count':int(sel.venue.nunique()) if n else 0}

def main():
    canon=load_canonical()
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)
    mar,_,ma=build_pre('2026-03-01','2026-03-31',False)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    jan['y']=(jan.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    mar=canon[canon.date>='2026-03-01'][['rc','date','settle__winner']].merge(mar.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)
    mar['y']=(pd.to_numeric(mar.settle__winner,errors='coerce')==3).astype(int)

    all_pre=pd.concat([jan,feb,mar],ignore_index=True,sort=False)
    feats=curated_features(all_pre)
    for fr in [jan,feb,mar]:
        for c in feats:
            if c not in fr.columns:fr[c]=float('nan')

    feb_history=pd.concat([jan,feb],ignore_index=True,sort=False)
    feb_pred=walk_predictions(feb_history,feb,WINDOWS,feats)

    universe=candidate_universe(feb_pred)
    evals=[evaluate_candidate(feb_pred,c) for c in universe]
    pareto=sorted(
        evals,
        key=lambda z:(min(z['h1']['rate'] or 0,z['h2']['rate'] or 0),
                      z['h1']['n']+z['h2']['n']),
        reverse=True
    )

    freezes={}
    selected=[]
    for spec in FLOORS:
        pool=[z for z in evals if qualifies(z,spec)]
        volume=max(pool,key=lambda z:(z['h1']['n']+z['h2']['n'],min(z['h1']['rate'],z['h2']['rate']))) if pool else None
        precision=max(pool,key=lambda z:(min(z['h1']['rate'],z['h2']['rate']),z['h1']['n']+z['h2']['n'])) if pool else None
        freezes[spec['name']]={
            'count':len(pool),
            'volume':public(volume) if volume else None,
            'precision':public(precision) if precision else None,
        }
        for z in [volume,precision]:
            if z is not None:selected.append(z)

    replay_windows=sorted(set(z['window'] for z in selected))
    march_results={k:{'volume':None,'precision':None} for k in freezes}
    if replay_windows:
        full_history=pd.concat([jan,feb,mar],ignore_index=True,sort=False)
        march_pred=walk_predictions(full_history,mar,replay_windows,feats)
        for spec in FLOORS:
            key=spec['name'];fr=freezes[key]
            march_results[key]['volume']=march_eval(march_pred,fr['volume']) if fr['volume'] else None
            march_results[key]['precision']=march_eval(march_pred,fr['precision']) if fr['precision'] else None

    out={
      'policy':{
        'wave7_family_unchanged':True,'february_freeze_only':True,
        'march_single_chronological_replay':True,'march_does_not_change_freezes':True,
        'september_outcomes_read':False,'production_v288_changed':False,
        'recent_end_date_fail_closed':True
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'jan':ja,'feb':fa,'mar':ma},
      'rows':{'jan':len(jan),'feb':len(feb),'mar':len(mar),'feb_prediction_rows':len(feb_pred)},
      'features':len(feats),'candidate_count':len(evals),
      'floors':freezes,
      'march_results':march_results,
      'feb_pareto_top50':[public(z) for z in pareto[:50]]
    }
    with open('research_3head_funsite_broad50_wave8_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
