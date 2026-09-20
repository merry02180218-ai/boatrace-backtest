#!/usr/bin/env python3
"""4HEAD expanded post-exhibition pool — Stage 1 sizing.

Expansion-only research around the frozen 164R candidate.
September outcomes are blocked.  Pool choice is based on target size only,
not head outcomes, to avoid using labels to pick the relaxed structural cuts.
"""
from __future__ import annotations
from pathlib import Path
import csv, json, os
import numpy as np
import pandas as pd

import analyze_4head_headrate_3ren_player_st as prior
import analyze_4head_exhibition_original_trainonly as ex
from analyze_4head_b4_minus_b3_motor_full_universe import settle_all
import analyze_4head_b4_minus_b3_motor_win_2ren as motor

OUT=Path('/tmp/head4_expanded_pool_stage1'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
WIN=-0.0299361318939513
REN2=-7.080000000000001
PLAYER=.215605
FROZEN_ST=-0.6000000000000001
FROZEN_ORIG=-0.057777777777777706
TARGET_POOL=450

_local_root=os.environ.get('BOATRACECSV_LOCAL_ROOT')
if _local_root:
    _root=Path(_local_root)
    def _rows(path):
        p=_root/path
        if not p.is_file(): return []
        try:
            with p.open(encoding='utf-8-sig',newline='') as fh:
                return list(csv.DictReader(fh))
        except Exception:
            return []
    prior.rows=_rows
    ex.rows=_rows
    motor.rows=_rows
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
    z=z.merge(motor.build_motor_features(),on=['date','month','race_code'],how='left')
    pf=prior.build_prior_features()[['date','month','race_code','player4_all_win']]
    z=z.merge(pf,on=['date','month','race_code'],how='left')
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
    # LIVE-comparable monitoring parent: same frozen motor/player thresholds as
    # scan_4head_120r_pre_live. Historical archive is complete here, so the
    # LIVE missing-feature fail-open branch is not expected to add rows.
    parent_mask=(
      z.motor_win_diff_4v3.ge(WIN) &
      z.motor_2ren_diff_4v3.ge(REN2) &
      z.player4_all_win.ge(PLAYER)
    )
    wide=z[parent_mask].copy()
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
    grid.to_csv(OUT/'pool_grid.csv',index=False)
    good=grid[(grid.old164_recall.eq(164)) & grid.R.between(250,650)].copy()
    fallback_used=False
    if good.empty:
        fallback_used=True
        good=grid[(grid.old164_recall.eq(164)) & grid.R.ge(164)].copy()
    if good.empty:
        raise RuntimeError('no expansion-only structural pool')
    # Pool selection deliberately ignores head4 labels.
    good=good.sort_values(['distance_target','R','st_cut','orig_cut'],
                          ascending=[True,True,False,False])
    best=good.iloc[0].to_dict()
    sel=q.struct_ready & q.st4_adv_inside.ge(float(best['st_cut'])) & q.orig4_adv_inside.ge(float(best['orig_cut']))
    pool=q[sel].copy()
    pool['is_old164']=pool.old164.astype(int)

    q.to_csv(OUT/'wide_parent_with_exhibition.csv',index=False)
    pool.to_csv(OUT/'selected_pool.csv',index=False)
    # Diagnostic only: daily concentration at the LIVE monitoring-parent stage.
    # This is the correct denominator for comparison with current LIVE watchlist,
    # unlike the later 226R/208R research pools.
    daily_parent=wide.groupby('date').size().astype(int)
    all_days=pd.Index(sorted(z.date.astype(str).unique()))
    daily_parent=daily_parent.reindex(all_days,fill_value=0)
    # Per-gate pass diagnostics for explaining unusually large LIVE parent days.
    gate_daily=pd.DataFrame({
      'date':z.date.astype(str),
      'motor_win_pass':z.motor_win_diff_4v3.ge(WIN).astype(int),
      'motor_2ren_pass':z.motor_2ren_diff_4v3.ge(REN2).astype(int),
      'player_pass':z.player4_all_win.ge(PLAYER).astype(int),
      'parent_pass':parent_mask.astype(int),
    }).groupby('date').sum().reindex(all_days,fill_value=0)
    gate_summary={}
    for c in ('motor_win_pass','motor_2ren_pass','player_pass','parent_pass'):
        x=gate_daily[c]
        gate_summary[c]={
          'mean':float(x.mean()),'median':float(x.median()),'p95':float(x.quantile(.95)),
          'max':int(x.max()),'days_ge_today_parent34':int((x>=34).sum())
        }

    parent_daily={
      'days_in_settled_universe':int(len(daily_parent)),
      'total_monitoring_parent':int(daily_parent.sum()),
      'mean_monitoring_parent_per_day':float(daily_parent.mean()),
      'median_monitoring_parent_per_day':float(daily_parent.median()),
      'p95_monitoring_parent_per_day':float(daily_parent.quantile(.95)),
      'max_monitoring_parent_per_day':int(daily_parent.max()),
      'days_ge_7_parent':int((daily_parent>=7).sum()),
      'share_days_ge_7_parent':float((daily_parent>=7).mean()),
      'daily_counts':{str(k):int(v) for k,v in daily_parent.items()},
    }

    result={
      'wide_parent_R':int(len(wide)),
      'struct_ready_R':int(q.struct_ready.sum()),
      'old164_R':int(len(old)),
      'old164_head4':int(old.head4.sum()),
      'target_pool_R':TARGET_POOL,
      'grid_R_min':int(grid.R.min()),
      'grid_R_max':int(grid.R.max()),
      'fallback_outside_250_650':fallback_used,
      'selected_pool':best,
      'selected_pool_month_R':{m:int((pool.month==m).sum()) for m in MONTHS},
      'live_comparable_monitoring_parent_daily':parent_daily,
      'live_comparable_gate_daily_summary':gate_summary,
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
