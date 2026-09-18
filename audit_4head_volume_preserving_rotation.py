#!/usr/bin/env python3
"""4号艇: 買うレース数を極力減らさずROIを上げる volume-preserving rotation 監査。

研究ルール
- Apr-Jun = development, Jul-Aug = fixed retrospective validation.
- September 2026 outcomes/results are never read.
- Closing odds are retrospective diagnostic only; formal prospective ROI is NOT_COMPUTABLE.
- Production is never changed by this script.
- Search only simple pre-result observables already audited on the fixed 164R:
  head_prob, opponent_mass, composite_odds.
- Goal is not pure max ROI. Preserve/expand final BET count, and minimize removal of current BETs.

Two families:
1) EXPANSION_ONLY:
   keep every current comp>=7 BET, add selected current-PASS races.
2) ROTATION:
   optionally remove weak current BETs by opponent_mass (+ optional low head_prob),
   then add stronger current-PASS races.

Important:
- Jul-Aug metrics are validation/diagnostic only and MUST NOT be used to promote a rule.
- "minimum removal" outputs intentionally use Jul-Aug outcomes only to quantify how much
  hindsight rotation would have been required; they are attribution, not selection.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_4head_julaug_roi_collapse_attribution as src

OUT=Path('/tmp/head4_volume_preserving_rotation'); OUT.mkdir(parents=True,exist_ok=True)
DEV_MONTHS=['2026-04','2026-05','2026-06']
VAL_MONTHS=['2026-07','2026-08']

DROP_MASS=[.35,.375,.40,.425,.45]
DROP_HEAD=[None,.20,.22,.25,.28,.30]
RESCUE_HEAD=[.20,.22,.24,.26,.28,.30,.32]
RESCUE_MASS=[.30,.325,.35,.375,.40,.425]
RESCUE_COMP=[0.0,3.0,3.5,4.0,4.5,5.0,5.5,6.0]

EXP_HEAD=[round(x,2) for x in np.arange(.18,.361,.02)]
EXP_MASS=[round(x,3) for x in np.arange(.25,.451,.025)]
EXP_COMP=[0.0,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.25,6.5,6.75]


def stats(q,mask,prefix):
    b=q[mask]
    stake=10000*len(b); payout=float(b.payout_if_bet.sum())
    cur=q.current_bet.eq(1)
    removed=int((cur & ~mask).sum())
    added=int((~cur & mask).sum())
    return {
      f'{prefix}_R':len(b), f'{prefix}_current_removed':removed, f'{prefix}_rescue_added':added,
      f'{prefix}_hits':int(b.raw_hit.sum()), f'{prefix}_head4':int(b.head4.sum()),
      f'{prefix}_stake':stake, f'{prefix}_payout':payout,
      f'{prefix}_ROI':100*payout/stake if stake else np.nan,
    }


def monthly(q,mask):
    out={}
    for mo in DEV_MONTHS+VAL_MONTHS:
        z=q[q.month.eq(mo)]
        m=mask.loc[z.index]
        s=stats(z,m,mo)
        out.update(s)
    return out


def rescue_mask(q,rh,rm,lo):
    m=q.current_bet.eq(0) & q.head_prob.ge(rh) & q.opponent_mass.ge(rm)
    if lo>0: m &= q.composite_odds.ge(lo)
    return m


def expansion_grid(rd):
    rows=[]
    for rh in EXP_HEAD:
      for rm in EXP_MASS:
       for lo in EXP_COMP:
        m=rd.current_bet.eq(1) | rescue_mask(rd,rh,rm,lo)
        a={'family':'EXPANSION_ONLY','rescue_head':rh,'rescue_mass':rm,'rescue_comp_min':lo}
        a.update(stats(rd[rd.period.eq('Apr-Jun')],m.loc[rd.period.eq('Apr-Jun')],'dev'))
        a.update(stats(rd[rd.period.eq('Jul-Aug')],m.loc[rd.period.eq('Jul-Aug')],'val'))
        a.update(monthly(rd,m))
        rows.append(a)
    return pd.DataFrame(rows)


def rotation_grid(rd):
    rows=[]
    for dm in DROP_MASS:
      for dh in DROP_HEAD:
        cur=rd.current_bet.eq(1)
        drop=cur & rd.opponent_mass.lt(dm)
        if dh is not None: drop &= rd.head_prob.lt(dh)
        keep=cur & ~drop
        for rh in RESCUE_HEAD:
          for rm in RESCUE_MASS:
            for lo in RESCUE_COMP:
              m=keep | rescue_mask(rd,rh,rm,lo)
              a={'family':'ROTATION','drop_mass':dm,'drop_head':np.nan if dh is None else dh,
                 'rescue_head':rh,'rescue_mass':rm,'rescue_comp_min':lo}
              a.update(stats(rd[rd.period.eq('Apr-Jun')],m.loc[rd.period.eq('Apr-Jun')],'dev'))
              a.update(stats(rd[rd.period.eq('Jul-Aug')],m.loc[rd.period.eq('Jul-Aug')],'val'))
              a.update(monthly(rd,m))
              a['dev_month_floor_ROI']=min(a[f'{mo}_ROI'] for mo in DEV_MONTHS)
              a['val_month_floor_ROI']=min(a[f'{mo}_ROI'] for mo in VAL_MONTHS)
              rows.append(a)
    return pd.DataFrame(rows)


def pareto_dev(rg,base_dev_R):
    # Development-only admissibility. No Jul-Aug condition here.
    q=rg[(rg.dev_R>=base_dev_R)&(rg.dev_ROI>=100)].copy()
    if q.empty:return q
    # Primary ranking reflects user's stated objective:
    # preserve volume / minimize current removals / then improve monthly floor & ROI.
    q['dev_volume_ratio']=q.dev_R/base_dev_R
    q=q.sort_values(
      ['dev_current_removed','dev_month_floor_ROI','dev_ROI','dev_R'],
      ascending=[True,False,False,False]
    )
    return q


def main():
    rd=src.rebuild()
    if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.raw_hit.sum())!=35:
        raise RuntimeError('fixed 164R reproduction failed')
    rd['period']=np.where(rd.month.le('2026-06'),'Apr-Jun','Jul-Aug')
    if any(rd.month.ge('2026-09')): raise RuntimeError('September outcome access blocked')

    dev=rd[rd.period.eq('Apr-Jun')]; val=rd[rd.period.eq('Jul-Aug')]
    base_dev_R=int(dev.current_bet.sum()); base_val_R=int(val.current_bet.sum())
    base={
      **stats(dev,dev.current_bet.eq(1),'dev'),
      **stats(val,val.current_bet.eq(1),'val'),
    }

    eg=expansion_grid(rd); eg.to_csv(OUT/'expansion_only_grid.csv',index=False)
    rg=rotation_grid(rd); rg.to_csv(OUT/'rotation_grid.csv',index=False)

    # Development-only candidate ranking: legitimate research selection view.
    dp=pareto_dev(rg,base_dev_R)
    dp.head(200).to_csv(OUT/'development_ranked_top200.csv',index=False)

    # Expansion-only retrospective ceiling on Jul-Aug: attribution only.
    exv=eg.sort_values(['val_ROI','val_R','dev_ROI'],ascending=[False,False,False])
    exv.head(100).to_csv(OUT/'expansion_only_validation_ceiling_top100.csv',index=False)

    # HINDSIGHT DIAGNOSTICS ONLY: quantify minimum removal needed to recover Jul-Aug.
    pooled=rg[(rg.val_R>=base_val_R)&(rg.val_ROI>=100)].copy()
    pooled=pooled.sort_values(['val_current_removed','val_rescue_added','val_ROI'],ascending=[True,False,False])
    pooled.head(100).to_csv(OUT/'validation_min_removal_pooled100.csv',index=False)

    both=rg[(rg.val_R>=base_val_R)&
            (rg['2026-07_ROI']>=100)&(rg['2026-08_ROI']>=100)&
            (rg.dev_R>=base_dev_R)&(rg.dev_ROI>=100)].copy()
    both=both.sort_values(['val_current_removed','val_rescue_added','val_ROI'],ascending=[True,False,False])
    both.head(100).to_csv(OUT/'validation_min_removal_both_months100.csv',index=False)

    # Simple summary
    exp_best=exv.iloc[0] if len(exv) else None
    pool_best=pooled.iloc[0] if len(pooled) else None
    both_best=both.iloc[0] if len(both) else None
    summary={
      'baseline':{
        'dev_current_bet_R':base_dev_R,'dev_ROI':base['dev_ROI'],
        'val_current_bet_R':base_val_R,'val_ROI':base['val_ROI'],
      },
      'user_objective':'preserve/expand BET race count; minimize removals; improve ROI',
      'expansion_only_validation_ceiling': None if exp_best is None else {
        'val_R':int(exp_best.val_R),'val_ROI':float(exp_best.val_ROI),
        'dev_R':int(exp_best.dev_R),'dev_ROI':float(exp_best.dev_ROI),
        'rescue_head':float(exp_best.rescue_head),'rescue_mass':float(exp_best.rescue_mass),
        'rescue_comp_min':float(exp_best.rescue_comp_min),
      },
      'hindsight_min_removal_for_val_pooled_ROI100': None if pool_best is None else {
        'removed_current_val_R':int(pool_best.val_current_removed),
        'added_rescue_val_R':int(pool_best.val_rescue_added),
        'final_val_R':int(pool_best.val_R),'val_ROI':float(pool_best.val_ROI),
        'drop_mass':float(pool_best.drop_mass),
        'drop_head':None if pd.isna(pool_best.drop_head) else float(pool_best.drop_head),
        'rescue_head':float(pool_best.rescue_head),'rescue_mass':float(pool_best.rescue_mass),
        'rescue_comp_min':float(pool_best.rescue_comp_min),
      },
      'hindsight_min_removal_for_each_Jul_Aug_ROI100': None if both_best is None else {
        'removed_current_val_R':int(both_best.val_current_removed),
        'added_rescue_val_R':int(both_best.val_rescue_added),
        'final_val_R':int(both_best.val_R),'val_ROI':float(both_best.val_ROI),
        'Jul_ROI':float(both_best['2026-07_ROI']),'Aug_ROI':float(both_best['2026-08_ROI']),
        'dev_R':int(both_best.dev_R),'dev_ROI':float(both_best.dev_ROI),
        'drop_mass':float(both_best.drop_mass),
        'drop_head':None if pd.isna(both_best.drop_head) else float(both_best.drop_head),
        'rescue_head':float(both_best.rescue_head),'rescue_mass':float(both_best.rescue_mass),
        'rescue_comp_min':float(both_best.rescue_comp_min),
      },
      'formal_prospective_roi':'NOT_COMPUTABLE',
      'validation_used_for_promotion':False,
      'september_2026':'UNREAD',
      'production_changed':False,
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')

    print('4号艇_購入数維持_ROIローテーション監査_OK')
    print('BASE',json.dumps(summary['baseline'],ensure_ascii=False))
    print('EXPANSION_ONLY_CEILING',json.dumps(summary['expansion_only_validation_ceiling'],ensure_ascii=False))
    print('VAL_POOLED_MIN_REMOVAL',json.dumps(summary['hindsight_min_removal_for_val_pooled_ROI100'],ensure_ascii=False))
    print('VAL_BOTH_MONTHS_MIN_REMOVAL',json.dumps(summary['hindsight_min_removal_for_each_Jul_Aug_ROI100'],ensure_ascii=False))
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__':main()
