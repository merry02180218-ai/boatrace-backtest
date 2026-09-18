#!/usr/bin/env python3
"""4号艇: 77Rを全件残した nested linear-score high-volume frontier.

Research only.
- Fixed 164R head-rate research population.
- Apr-Aug = NON-PRISTINE model-selection.
- September 2026 outcomes/results are never read.
- Closing/composite odds ROI is retrospective diagnostic only.
- Production is never changed by this script.

Base 77R is preserved exactly:
  current BET AND opponent_mass >= .425
  OR current PASS AND head_prob >= .22 AND opponent_mass >= .375 AND composite_odds >= 3.0

Extra nested races:
  composite_odds >= COMP_MIN
  AND head_prob + W * opponent_mass >= SCORE_MIN

This smooth score is intentionally limited to the two observables that repeatedly mattered
in prior audits. It avoids adding original-exhibition complexity.

Frozen comparison profiles:
- 115R stability profile: comp>=2.5, W=1.50, score>=0.83
- 120R preferred high-volume profile: comp>=2.5, W=1.50, score>=0.82
- 127R volume profile: comp>=2.5, W=1.65, score>=0.8525
- 130R aggressive profile: comp>=2.5, W=1.75, score>=0.8825
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_4head_julaug_roi_collapse_attribution as src

OUT=Path('/tmp/head4_nested_linear_frontier'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=['2026-04','2026-05','2026-06','2026-07','2026-08']
BASELINE_ROI=124.86222222222223

def base77_mask(rd):
    cur=rd.current_bet.eq(1)
    return ((cur & rd.opponent_mass.ge(.425)) |
            ((~cur) & rd.head_prob.ge(.22) & rd.opponent_mass.ge(.375) & rd.composite_odds.ge(3.0)))

def profile_mask(rd,base,comp,w,score_min):
    extra=(~base) & rd.composite_odds.ge(comp) & (rd.head_prob + w*rd.opponent_mass).ge(score_min)
    return base | extra

def metric(rd,m):
    R=int(m.sum())
    pay=float(rd.loc[m,'payout_if_bet'].sum())
    out={'R':R,'ROI':100*pay/(10000*R) if R else np.nan,
         'added_beyond77':R-77}
    floors=[]
    for mo in MONTHS:
        mm=m & rd.month.eq(mo)
        rr=int(mm.sum())
        p=float(rd.loc[mm,'payout_if_bet'].sum())
        roi=100*p/(10000*rr) if rr else np.nan
        out[f'{mo}_R']=rr
        out[f'{mo}_ROI']=roi
        floors.append(roi)
    out['floor5_ROI']=min(floors)
    out['all_months_ge100']=all(x>=100 for x in floors)
    return out

def main():
    rd=src.rebuild()
    if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.raw_hit.sum())!=35:
        raise RuntimeError('fixed 164R reproduction failed')
    if any(rd.month.ge('2026-09')):
        raise RuntimeError('September outcome access blocked')

    base=base77_mask(rd)
    bm=metric(rd,base)
    if bm['R']!=77 or abs(bm['ROI']-141.16883116883116)>1e-6:
        raise RuntimeError(f'base77 drift: {bm}')

    defs={
      'stable115':(2.5,1.50,.83),
      'preferred120':(2.5,1.50,.82),
      'volume127':(2.5,1.65,.8525),
      'aggressive130':(2.5,1.75,.8825),
    }
    expected={
      'stable115':(115,133.27478260869565,107.73529411764706),
      'preferred120':(120,127.72166666666666,101.75),
      'volume127':(127,128.32125984251968,96.39473684210526),
      'aggressive130':(130,125.36,91.575),
    }

    profiles=[]
    details=rd.copy()
    details['base77']=base.astype(int)
    for name,(comp,w,th) in defs.items():
        m=profile_mask(rd,base,comp,w,th)
        z=metric(rd,m)
        er,eroi,efloor=expected[name]
        if z['R']!=er or abs(z['ROI']-eroi)>1e-6 or abs(z['floor5_ROI']-efloor)>1e-6:
            raise RuntimeError(f'{name} drift: {z}')
        row={'profile':name,'comp_min':comp,'weight':w,'score_min':th,**z}
        profiles.append(row)
        details[name]=m.astype(int)
    pd.DataFrame(profiles).to_csv(OUT/'frozen_profiles.csv',index=False)
    details.to_csv(OUT/'race_detail_profiles.csv',index=False)

    # Fine frontier around the 120R area.
    rows=[]
    for comp in np.arange(2.30,2.701,.05):
      for w in np.arange(1.20,1.801,.025):
        for th in np.arange(.70,.951,.0025):
          m=profile_mask(rd,base,float(comp),float(w),float(th))
          z=metric(rd,m)
          if 110<=z['R']<=135 and z['ROI']>BASELINE_ROI:
            rows.append({'comp_min':round(float(comp),3),'weight':round(float(w),3),
                         'score_min':round(float(th),4),**z})
    grid=pd.DataFrame(rows).drop_duplicates()
    grid.to_csv(OUT/'fine_frontier_grid.csv',index=False)

    all100=grid[grid.all_months_ge100].copy()
    if all100.empty:
        raise RuntimeError('no all-month>=100 frontier cells')
    maxR=int(all100.R.max())
    if maxR!=121:
        raise RuntimeError(f'all-month>=100 maxR drift: {maxR}')
    max_all100=all100[all100.R.eq(maxR)].sort_values(['ROI','floor5_ROI'],ascending=False)
    max_all100.to_csv(OUT/'max_volume_all_months_ge100.csv',index=False)

    # Cleaner preferred point keeps comp floor 2.5 and sits on a plateau.
    local=grid[
      grid.comp_min.eq(2.5) &
      grid.weight.between(1.40,1.60) &
      grid.score_min.between(.79,.85)
    ].copy()
    local['near_115_125_floor95']=(local.R.between(115,125)&
                                    local.ROI.gt(BASELINE_ROI)&
                                    local.floor5_ROI.ge(95))
    local['near_115_125_all100']=(local.R.between(115,125)&
                                   local.ROI.gt(BASELINE_ROI)&
                                   local.all_months_ge100)
    local.to_csv(OUT/'preferred120_neighborhood.csv',index=False)

    pref=[x for x in profiles if x['profile']=='preferred120'][0]
    summary={
      'status':'NESTED_LINEAR_HIGH_VOLUME_RESEARCH_READY',
      'base77':bm,
      'preferred120':pref,
      'preferred_rule':'base77 OR (composite_odds >= 2.5 AND head_prob + 1.50*opponent_mass >= 0.82)',
      'max_R_with_all_5_months_ge100_in_fine_grid':maxR,
      'max_R_all100_best':max_all100.iloc[0].to_dict(),
      'local_plateau':{
        'cells':int(len(local)),
        'cells_R115_125_floor95':int(local.near_115_125_floor95.sum()),
        'cells_R115_125_all_months_ge100':int(local.near_115_125_all100.sum()),
      },
      'selection_period':'2026-04..2026-08 NON_PRISTINE_MODEL_SELECTION',
      'formal_prospective_roi':'NOT_COMPUTABLE',
      'september_2026':'UNREAD',
      'production_changed':False,
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=float)+'\n')

    print('4号艇_NESTED_LINEAR_HIGH_VOLUME_OK')
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=float))
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__':
    main()
