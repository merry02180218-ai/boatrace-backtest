#!/usr/bin/env python3
"""4HEAD expanded post-exhibition pool — Stage 1 sizing.

Expansion-only research around the frozen 164R candidate.
September outcomes are blocked.  Pool choice is based on target size only,
not head outcomes, to avoid using labels to pick the relaxed structural cuts.
"""
from __future__ import annotations
from pathlib import Path
import json, os
import numpy as np
import pandas as pd

import analyze_4head_headrate_3ren_player_st as prior
import analyze_4head_exhibition_original_trainonly as ex
from analyze_4head_b4_minus_b3_motor_full_universe import settle_all
from analyze_4head_b4_minus_b3_motor_win_2ren import build_motor_features

OUT=Path('/tmp/head4_expanded_pool_stage1'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
WIN=-0.0299361318939513
REN2=-7.080000000000001
PLAYER=.215605
FROZEN_ST=-0.6000000000000001
FROZEN_ORIG=-0.057777777777777706
TARGET_POOL=450
ST_CUTS=(-1.20,-1.00,-.90,-.80,-.70,-.60)
ORIG_CUTS=(-.35,-.30,-.25,-.20,-.15,-.10,FROZEN_ORIG)

def met(q):
    return {
      'R':len(q),
      'head4':int(q.head4.sum()) if len(q) else 0,
      'head4_rate':100*float(q.head4.mean()) if len(q) else np.nan,
    }

def main():
    if any(m.startswith('2026-09') for m in MONTHS):
        raise RuntimeError('SEPTEMBER OUTCOME ACCESS')
    z=settle_all(months=MONTHS)
    z=z.merge(build_motor_features(),on=['date','month','race_code'],how='left')
    pf=prior.build_prior_features()[['date','month','race_code','player4_all_win']]
    z=z.merge(pf,on=['date','month','race_code'],how='left')
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
    wide=z[
      z.motor_win_diff_4v3.ge(WIN) &
      z.motor_2ren_diff_4v3.ge(REN2) &
      z.player4_all_win.ge(PLAYER)
    ].copy()
    if wide.empty: raise RuntimeError('wide parent empty')

    ef=ex.build_ex(set(wide.race_code))
    ef['race_code']=ef.race_code.astype(str).str.zfill(12)
    q=wide.merge(ef,on='race_code',how='left',validate='one_to_one')
    q['struct_ready']=(
      q.basic_complete.fillna(0).astype(int).eq(1) &
      q.orig_avg_available.fillna(0).astype(int).eq(1) &
      pd.to_numeric(q.st4_adv_inside,errors='coerce').notna() &
      pd.to_numeric(q.orig4_adv_inside,errors='coerce').notna()
    )
    q['old164']=(
      q.struct_ready &
      q.st4_adv_inside.ge(FROZEN_ST) &
      q.orig4_adv_inside.ge(FROZEN_ORIG)
    )
    old=q[q.old164].copy()
    if (len(old),int(old.head4.sum()))!=(164,70):
        raise RuntimeError(f'old164 parity failed {(len(old),int(old.head4.sum()))}')

    rows=[]
    for sc in ST_CUTS:
      for oc in ORIG_CUTS:
        # expansion only: never stricter than frozen thresholds
        if sc>FROZEN_ST+1e-12 or oc>FROZEN_ORIG+1e-12: continue
        m=q.struct_ready & q.st4_adv_inside.ge(sc) & q.orig4_adv_inside.ge(oc)
        x=q[m].copy()
        ids=set(x.race_code)
        old_recall=int(old.race_code.isin(ids).sum())
        row={'st_cut':sc,'orig_cut':oc,'R':len(x),'added_vs164':len(x)-164,
             'old164_recall':old_recall,'head4':int(x.head4.sum()),
             'head4_rate':100*float(x.head4.mean()) if len(x) else np.nan,
             'distance_target':abs(len(x)-TARGET_POOL)}
        for mon in MONTHS:
            g=x[x.month.eq(mon)]
            row[f'{mon}_R']=len(g)
            row[f'{mon}_head4_rate']=100*float(g.head4.mean()) if len(g) else np.nan
        rows.append(row)
    grid=pd.DataFrame(rows)
    good=grid[(grid.old164_recall.eq(164)) & grid.R.between(250,650)].copy()
    if good.empty: raise RuntimeError('no 250-650 expanded pool')
    # Pool selection deliberately ignores head4 labels.
    good=good.sort_values(['distance_target','R','st_cut','orig_cut'],
                          ascending=[True,True,False,False])
    best=good.iloc[0].to_dict()
    sel=q.struct_ready & q.st4_adv_inside.ge(float(best['st_cut'])) & q.orig4_adv_inside.ge(float(best['orig_cut']))
    pool=q[sel].copy()
    pool['is_old164']=pool.old164.astype(int)

    grid.to_csv(OUT/'pool_grid.csv',index=False)
    q.to_csv(OUT/'wide_parent_with_exhibition.csv',index=False)
    pool.to_csv(OUT/'selected_pool.csv',index=False)
    result={
      'wide_parent_R':int(len(wide)),
      'struct_ready_R':int(q.struct_ready.sum()),
      'old164_R':int(len(old)),
      'old164_head4':int(old.head4.sum()),
      'target_pool_R':TARGET_POOL,
      'selected_pool':best,
      'selected_pool_month_R':{m:int((pool.month==m).sum()) for m in MONTHS},
      'selection_used_head_outcomes':False,
      'old164_subset':bool(set(old.race_code).issubset(set(pool.race_code))),
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print('\nNEAR TARGET')
    print(good.head(20).to_string(index=False))
    print('HEAD4_EXPANDED_POOL_STAGE1_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__': main()
