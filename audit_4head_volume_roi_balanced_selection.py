#!/usr/bin/env python3
"""4号艇: Apr-Augを非pristine model-selection期間として使う volume+ROI balanced selection.

User objective:
- 買うレース数を減らさない（少なくとも現行45R以上）
- Apr-Jun / Jul-Augそれぞれでも現行BET Rを下回らない
- ROIを現行Apr-Aug retrospective baselineより上げる
- その条件下で5か月の最低ROIを最優先し、次に全体ROI、次にR数を優先

Jul/Augはここでは既に非pristine model-selectionへ昇格させる。
September 2026 outcomes/results are NEVER read.
Production is unchanged; this only freezes a research candidate for prospective use.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_4head_julaug_roi_collapse_attribution as src
import audit_4head_volume_preserving_rotation as rot

OUT=Path('/tmp/head4_volume_roi_balanced'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=rot.DEV_MONTHS+rot.VAL_MONTHS

def main():
    rd=src.rebuild()
    if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.raw_hit.sum())!=35:
        raise RuntimeError('fixed 164R reproduction failed')
    rd['period']=np.where(rd.month.le('2026-06'),'Apr-Jun','Jul-Aug')
    if any(rd.month.ge('2026-09')): raise RuntimeError('September outcome access blocked')

    dev=rd[rd.period.eq('Apr-Jun')]; val=rd[rd.period.eq('Jul-Aug')]
    base_dev_R=int(dev.current_bet.sum()); base_val_R=int(val.current_bet.sum())
    base_total_R=base_dev_R+base_val_R
    base_payout=float(rd.loc[rd.current_bet.eq(1),'payout_if_bet'].sum())
    base_roi=100*base_payout/(10000*base_total_R)

    rg=rot.rotation_grid(rd).copy()
    rg['total_R']=rg.dev_R+rg.val_R
    rg['overall_payout']=rg.dev_payout+rg.val_payout
    rg['overall_ROI']=100*rg.overall_payout/(10000*rg.total_R)
    rg['floor5_ROI']=rg[[f'{m}_ROI' for m in MONTHS]].min(axis=1)

    eligible=rg[
      (rg.dev_R>=base_dev_R)&
      (rg.val_R>=base_val_R)&
      (rg.total_R>=base_total_R)&
      (rg.overall_ROI>base_roi)
    ].copy()
    if eligible.empty: raise RuntimeError('no volume-preserving ROI-improving cells')
    eligible=eligible.sort_values(['floor5_ROI','overall_ROI','total_R'],ascending=[False,False,False]).reset_index(drop=True)
    eligible.head(200).to_csv(OUT/'balanced_ranked_top200.csv',index=False)
    s=eligible.iloc[0]

    # Drift guard for the current exact 164R research set.
    expected={'drop_mass':.425,'rescue_head':.22,'rescue_mass':.375,'rescue_comp_min':3.0}
    for k,v in expected.items():
        if abs(float(s[k])-v)>1e-12: raise RuntimeError(f'selection drift {k}={s[k]} expected={v}')
    if not pd.isna(s.drop_head): raise RuntimeError(f'selection drift drop_head={s.drop_head}')
    if int(s.total_R)!=77: raise RuntimeError(f'selection drift total_R={s.total_R}')
    if abs(float(s.overall_ROI)-141.17012987012987)>1e-6:
        raise RuntimeError(f'selection drift overall_ROI={s.overall_ROI}')

    # Rebuild exact selected mask for race/month detail.
    cur=rd.current_bet.eq(1)
    keep=cur & ~rd.opponent_mass.lt(float(s.drop_mass))
    rescue=(~cur)&rd.head_prob.ge(float(s.rescue_head))&rd.opponent_mass.ge(float(s.rescue_mass))&rd.composite_odds.ge(float(s.rescue_comp_min))
    mask=keep|rescue
    detail=rd.copy(); detail['selected_balanced']=mask.astype(int)
    detail['selection_role']=np.where(mask & cur,'KEEP_CURRENT',np.where(mask & ~cur,'ADD_RESCUE',np.where(cur,'DROP_CURRENT','PASS')))
    detail.to_csv(OUT/'race_detail_selected.csv',index=False)

    monthly=[]
    for mo in MONTHS:
        q=rd[rd.month.eq(mo)]; m=mask.loc[q.index]; c=q.current_bet.eq(1)
        st=10000*int(m.sum()); pay=float(q.loc[m,'payout_if_bet'].sum())
        monthly.append({
          'month':mo,'baseline_R':int(c.sum()),'selected_R':int(m.sum()),
          'current_removed':int((c&~m).sum()),'rescue_added':int((~c&m).sum()),
          'hits':int(q.loc[m,'raw_hit'].sum()),'head4':int(q.loc[m,'head4'].sum()),
          'ROI':100*pay/st if st else np.nan,
        })
    mm=pd.DataFrame(monthly); mm.to_csv(OUT/'monthly_selected.csv',index=False)

    # Neighborhood around selected point. This is robustness evidence, not a re-selection.
    near=rg[
      rg.drop_head.isna() &
      rg.drop_mass.isin([.40,.425,.45]) &
      rg.rescue_head.isin([.20,.22,.24]) &
      rg.rescue_mass.isin([.35,.375,.40]) &
      rg.rescue_comp_min.isin([0.0,3.0,3.5])
    ].copy()
    near['passes_base_constraints']=(near.dev_R>=base_dev_R)&(near.val_R>=base_val_R)&(near.total_R>=base_total_R)&(near.overall_ROI>base_roi)
    near['floor70']=near.floor5_ROI.ge(70)
    near['floor80']=near.floor5_ROI.ge(80)
    near=near.sort_values(['floor5_ROI','overall_ROI'],ascending=False)
    near.to_csv(OUT/'selected_neighborhood.csv',index=False)

    summary={
      'status':'RESEARCH_CANDIDATE_FREEZE_READY',
      'population':'fixed 164R head-rate research candidate',
      'selection_period':'2026-04..2026-08 NON_PRISTINE_MODEL_SELECTION',
      'baseline':{'R':base_total_R,'ROI':base_roi,'AprJun_R':base_dev_R,'JulAug_R':base_val_R,'monthly_floor_ROI':0.0},
      'selected_rule':{
        'keep_current_if':'current_bet AND opponent_mass >= 0.425',
        'add_rescue_if':'current_PASS AND head_prob >= 0.22 AND opponent_mass >= 0.375 AND composite_odds >= 3.0',
        'drop_head_extra_condition':None,
      },
      'selected':{
        'R':int(s.total_R),'ROI':float(s.overall_ROI),'monthly_floor_ROI':float(s.floor5_ROI),
        'AprJun_R':int(s.dev_R),'AprJun_ROI':float(s.dev_ROI),
        'JulAug_R':int(s.val_R),'JulAug_ROI':float(s.val_ROI),
      },
      'monthly':monthly,
      'neighbor_cells':int(len(near)),
      'neighbor_pass_base_constraints':int(near.passes_base_constraints.sum()),
      'neighbor_floor70_and_base_constraints':int((near.passes_base_constraints&near.floor70).sum()),
      'neighbor_floor80_and_base_constraints':int((near.passes_base_constraints&near.floor80).sum()),
      'formal_prospective_roi':'NOT_COMPUTABLE',
      'september_2026':'UNREAD',
      'production_changed':False,
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')

    print('4号艇_VOLUME_ROI_BALANCED_SELECTION_OK')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__': main()
