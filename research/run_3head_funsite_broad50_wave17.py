from __future__ import annotations
import json
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave16 import (
    build_pre_enhanced, load_canonical, choose_features, walk_predictions, eval_candidate
)

WINDOWS=[21,42]
BANDS=[(1,4),(1,6),(1,8),(1,10),(1,12)]
MODELS=['p_logit','p_hist','p_mean']
QS=[.95,.96,.97,.975,.98,.985,.99,.9925,.995]

def candidate_universe(family):
    out=[]
    for w in WINDOWS:
        for band in BANDS:
            for model in MODELS:
                for q in QS:
                    out.append({'family':family,'window':w,'band':list(band),'model':model,'q':q})
    return out

def month_eval(pred,c):
    return eval_candidate(pred,c,False)

def combined(z):
    n=z['h1']['n']+z['h2']['n']; h=z['h1']['hits']+z['h2']['hits']
    return {'n':n,'hits':h,'rate':h/n if n else None}

def six_half_rates(ms):
    vals=[]
    for m in ['nov','dec','jan']:
        for h in ['h1','h2']:
            r=ms[m][h]['rate']
            if r is None:return None
            vals.append(r)
    return vals

def pre_metrics(ms):
    rates=six_half_rates(ms)
    monthly={m:combined(ms[m]) for m in ['nov','dec','jan']}
    total_n=sum(v['n'] for v in monthly.values())
    total_h=sum(v['hits'] for v in monthly.values())
    avg_month_n=sum(v['n'] for v in monthly.values())/3
    return {
        'persistent_worst':min(rates) if rates else None,
        'persistent_mean_half':float(np.mean(rates)) if rates else None,
        'persistent_combined':total_h/total_n if total_n else None,
        'avg_month_n':avg_month_n,
        'monthly':monthly
    }

def eligible(ms,lo,hi):
    for m in ['nov','dec','jan']:
        z=ms[m]
        n=z['h1']['n']+z['h2']['n']
        if n<lo or n>hi:return False
        for h in ['h1','h2']:
            if z[h]['n']<8 or z[h]['venues']<6 or z[h]['rate'] is None:return False
    return True

def rank_key(row):
    p=row['pre']
    return (
        p['persistent_worst'],
        p['persistent_combined'],
        -abs(p['avg_month_n']-50.0),
        -max(abs(p['monthly'][m]['n']-50) for m in ['nov','dec','jan'])
    )

def summarize_candidate(c,ms):
    return {'candidate':c,'months':ms,'pre':pre_metrics(ms)}

def main():
    canon=load_canonical()
    octo,ores,oa=build_pre_enhanced('2025-10-01','2025-10-31',True)
    nov,nres,na=build_pre_enhanced('2025-11-01','2025-11-30',True)
    dec,dres,da=build_pre_enhanced('2025-12-01','2025-12-31',True)
    jan,jres,ja=build_pre_enhanced('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre_enhanced('2026-02-01','2026-02-28',True)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:
        raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    frames=[]
    for x,r in [(octo,ores),(nov,nres),(dec,dres),(jan,jres)]:
        y=x.merge(r[['rc','result_winner']],on='rc',how='inner')
        y['y']=(y.result_winner==3).astype(int)
        frames.append(y)
    octo,nov,dec,jan=frames
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(
        feb.drop(columns=['date']),on='rc',how='inner'
    )
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    all_data=pd.concat([octo,nov,dec,jan,feb],ignore_index=True,sort=False)
    base_feats,enh_feats,new_feats=choose_features(all_data)
    feature_sets={'ENHANCED':enh_feats}

    histories={
      'nov':pd.concat([octo,nov],ignore_index=True,sort=False),
      'dec':pd.concat([octo,nov,dec],ignore_index=True,sort=False),
      'jan':pd.concat([octo,nov,dec,jan],ignore_index=True,sort=False),
      'feb':pd.concat([octo,nov,dec,jan,feb],ignore_index=True,sort=False)
    }
    targets={'nov':nov,'dec':dec,'jan':jan,'feb':feb}
    preds={m:walk_predictions(histories[m],targets[m],feature_sets) for m in targets}

    results={}
    for family in ['ENHANCED']:
        rows=[]
        for c in candidate_universe(family):
            ms={m:month_eval(preds[m],c) for m in ['nov','dec','jan']}
            rows.append(summarize_candidate(c,ms))

        strict=[r for r in rows if eligible(r['months'],40,70)]
        wide=[r for r in rows if eligible(r['months'],30,80)]
        strict=sorted(strict,key=rank_key,reverse=True)
        wide=sorted(wide,key=rank_key,reverse=True)

        primary=strict[0] if strict else (wide[0] if wide else None)
        reference=None
        if primary:
            f=eval_candidate(preds['feb'],primary['candidate'],True)
            a,b=f['h1'],f['h2'];n=a['n']+b['n'];h=a['hits']+b['hits']
            reference={
              'candidate':primary['candidate'],
              'h1':a,'h2':b,
              'combined_n':n,'combined_hits':h,'combined_rate':h/n if n else None,
              'worst_half_rate':min(a['rate'],b['rate']) if a['rate'] is not None and b['rate'] is not None else None
            }

        results[family]={
          'strict_40_70_count':len(strict),
          'wide_30_80_count':len(wide),
          'primary_source':'strict_40_70' if strict else ('wide_30_80' if wide else None),
          'primary_pre_feb':primary,
          'top10_strict':strict[:10],
          'top10_wide':wide[:10],
          'feb_reference_non_pristine':reference
        }

    out={
      'policy':{
        'target_monthly_volume_40_70':True,
        'pre_feb_selection_only':True,
        'february_reference_non_pristine':True,
        'march_outcomes_opened':False,
        'september_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'oct':oa,'nov':na,'dec':da,'jan':ja,'feb':fa},
      'rows':{'oct':len(octo),'nov':len(nov),'dec':len(dec),'jan':len(jan),'feb':len(feb)},
      'feature_counts':{'base':len(base_feats),'new':len(new_feats),'enhanced':len(enh_feats)},
      'q_grid':QS,
      'results':results
    }
    with open('research_3head_funsite_broad50_wave17_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
