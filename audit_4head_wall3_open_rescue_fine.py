#!/usr/bin/env python3
"""Fine-grid expansion-only audit for 4HEAD formal wall3 open-path rescue.

Consumes frozen universe_with_wall.csv from the successful formal wall audit.
Never removes any frozen base120 race. September outcomes are not present.
"""
from pathlib import Path
import hashlib, json, os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_wall3_open_rescue_fine'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
MONTHS=DEV+SUP

COMP_FLOORS=(2.30,2.35,2.40,2.45,2.50,2.55,2.60,2.65,2.70)
Q_THRESHOLDS=tuple(round(x,3) for x in np.arange(.800,.841,.005))
BETAS=tuple(round(x,3) for x in np.arange(.025,.201,.025))
A4_MINS=(0.0,.30,.40,.50,.60,.70,.80)

def met(q):
    n=len(q); pay=float(q.payout_if_bet.sum()) if n else 0.0
    return {'R':int(n),'head4':int(q.head4.sum()) if n else 0,
            'head4_rate':100*float(q.head4.mean()) if n else np.nan,
            'exact3':int(q.raw_hit.sum()) if n else 0,
            'ROI':100*pay/(10000*n) if n else np.nan,'payout':pay}

def fullmet(q):
    o={}
    for n,z in [('all',q),('dev',q[q.month.isin(DEV)]),('support',q[q.month.isin(SUP)])]:
        for k,v in met(z).items():o[f'{n}_{k}']=v
    rois=[]
    for m in MONTHS:
        mm=met(q[q.month.eq(m)])
        for k,v in mm.items():o[f'{m}_{k}']=v
        if mm['R']:rois.append(mm['ROI'])
    o['monthly_floor_ROI']=min(rois) if rois else np.nan
    o['dev_monthly_floor_ROI']=min(o[f'{m}_ROI'] for m in DEV if o[f'{m}_R'])
    o['support_monthly_floor_ROI']=min(o[f'{m}_ROI'] for m in SUP if o[f'{m}_R'])
    return o

def key(ids):
    s=';'.join(sorted(ids))
    return hashlib.sha256(s.encode()).hexdigest()[:16],s

def main():
    p=os.environ.get('WALL_UNIVERSE')
    if not p: raise RuntimeError('WALL_UNIVERSE missing')
    z=pd.read_csv(p,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    if len(z)!=164 or any(z.month.astype(str).str.startswith('2026-09')):
        raise RuntimeError('frozen universe/september guard failed')
    z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
    z['wall_ready']=z.wall_ready.astype(str).str.lower().isin(('true','1'))
    base=z[z.base120].copy()
    bm=fullmet(base)
    if bm['all_R']!=120:raise RuntimeError(f'base120 drift {bm["all_R"]}')

    rows=[]; setrows=[]
    seen={}
    for cf in COMP_FLOORS:
      for qt in Q_THRESHOLDS:
       for beta in BETAS:
        for a4 in A4_MINS:
            open_ok=(z.wall_ready & (z.wall_score<0) & (z.attack4_score>=a4))
            rescue=(~z.base120)&open_ok&(z.composite_odds>=cf)&((z.quality+beta*z.open_risk)>=qt)
            sel=z.base120|rescue
            q=z[sel]
            ids=set(z.loc[rescue,'race_code'])
            h,s=key(ids)
            mm=fullmet(q)
            dr=z[rescue & z.month.isin(DEV)]
            sr=z[rescue & z.month.isin(SUP)]
            row={'comp_floor':cf,'quality_threshold':qt,'open_beta':beta,'attack4_min':a4,
                 'rescue_set_hash':h,'added_R':len(ids),'dev_added_R':len(dr),'support_added_R':len(sr),
                 'added_head4':int(z.loc[rescue,'head4'].sum()),'added_exact3':int(z.loc[rescue,'raw_hit'].sum()),
                 **mm}
            rows.append(row)
            if h not in seen:
                seen[h]=s
                setrows.append({'rescue_set_hash':h,'race_codes':s})
    g=pd.DataFrame(rows)
    sets=pd.DataFrame(setrows)
    freq=g.groupby('rescue_set_hash').size().rename('plateau_cells').reset_index()
    g=g.merge(freq,on='rescue_set_hash',how='left')
    g['dev_ROI_gain_pp']=g.dev_ROI-bm['dev_ROI']
    g['all_ROI_gain_pp']=g.all_ROI-bm['all_ROI']
    g['head_gain_pp']=g.all_head4_rate-bm['all_head4_rate']
    g['floor_gain_pp']=g.monthly_floor_ROI-bm['monthly_floor_ROI']

    # Expansion-only preference: 1-10 added, no all-period ROI deterioration,
    # no monthly-floor deterioration. Rank Apr-Jun gains before support outcomes;
    # plateau size breaks ties to favor threshold-stable rescue sets.
    elig=g[(g.added_R.between(1,10))&
           (g.all_ROI>=bm['all_ROI'])&
           (g.monthly_floor_ROI>=bm['monthly_floor_ROI'])].copy()
    if elig.empty: raise RuntimeError('no non-deteriorating open-wall rescue')
    ranked=elig.sort_values(
        ['dev_ROI','dev_head4_rate','plateau_cells','added_R'],
        ascending=[False,False,False,True]
    )
    best=ranked.iloc[0].to_dict()
    best_hash=str(best['rescue_set_hash'])
    best_ids=set(sets.loc[sets.rescue_set_hash.eq(best_hash),'race_codes'].iloc[0].split(';')) if best_hash else set()
    best_races=z[z.race_code.isin(best_ids)].copy()

    # Robust-set summary: aggregate identical rescue sets independent of exact params.
    group=g.groupby('rescue_set_hash').agg(
        plateau_cells=('rescue_set_hash','size'),
        added_R=('added_R','first'),dev_added_R=('dev_added_R','first'),support_added_R=('support_added_R','first'),
        all_R=('all_R','first'),all_head4=('all_head4','first'),all_head4_rate=('all_head4_rate','first'),
        all_exact3=('all_exact3','first'),all_ROI=('all_ROI','first'),
        dev_ROI=('dev_ROI','first'),support_ROI=('support_ROI','first'),
        monthly_floor_ROI=('monthly_floor_ROI','first')
    ).reset_index().merge(sets,on='rescue_set_hash',how='left')
    group=group.sort_values(['plateau_cells','all_ROI'],ascending=[False,False])

    g.to_csv(OUT/'fine_grid.csv',index=False)
    ranked.head(300).to_csv(OUT/'ranked_non_deteriorating.csv',index=False)
    group.to_csv(OUT/'rescue_set_plateaus.csv',index=False)
    best_races.to_csv(OUT/'best_rescue_races.csv',index=False)

    result={
      'baseline120':bm,
      'grid_cells':int(len(g)),
      'unique_rescue_sets':int(len(group)),
      'non_deteriorating_cells':int(len(elig)),
      'selected_dev_first':best,
      'selected_rescue_races':best_races[['date','month','race_code','head4','raw_hit','payout_if_bet','head_prob','opponent_mass','composite_odds','quality','wall_score','open_risk','attack4_score']].to_dict('records'),
      'selected_plateau_cells':int(best['plateau_cells']),
      'selected_support_added_R':int(best['support_added_R']),
      'top_plateaus':group.head(20).to_dict('records'),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    print('\nTOP NON-DETERIORATING',flush=True)
    print(ranked.head(30).to_string(index=False),flush=True)
    print('\nTOP PLATEAUS',flush=True)
    print(group.head(30).to_string(index=False),flush=True)

if __name__=='__main__':main()
