#!/usr/bin/env python3
"""4号艇: 77Rより購入数を増やす Apr-Aug higher-volume frontier 監査。

研究前提
- fixed 164R head-rate research population only.
- Apr-Aug is NON-PRISTINE model-selection for this new candidate.
- September 2026 outcomes/results are never read.
- Closing odds/composite odds based ROI is retrospective diagnostic; formal prospective ROI NOT_COMPUTABLE.
- Production is unchanged by this audit.

User objective:
- previous balanced candidate 77Rより買うレース数を増やす。
- overall Apr-Aug retrospective ROI must remain above current baseline 124.8622%.
- prefer 100R+ if possible.
- do not accept a pure-volume point if the 5-month ROI floor collapses too far.

Search family:
KEEP current BET unless both:
  opponent_mass < DROP_MASS and head_prob < DROP_HEAD
ADD current PASS when:
  head_prob >= RESCUE_HEAD
  opponent_mass >= RESCUE_MASS
  composite_odds >= RESCUE_COMP_MIN

Primary HIGH_VOLUME selection:
- final R >= 100
- overall ROI > current baseline
- five-month minimum ROI >= 75
- maximize overall ROI; tie-break by larger R then larger monthly floor.

Also reports max-volume frontiers at minimum R 90/100/110/115/120.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_4head_julaug_roi_collapse_attribution as src

OUT=Path('/tmp/head4_higher_volume_frontier'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=['2026-04','2026-05','2026-06','2026-07','2026-08']
DROP_MASS=[.375,.3875,.40,.4125,.425]
DROP_HEAD=[.23,.24,.25,.26,.27,.28,.29]
RESCUE_HEAD=[.20,.21,.22,.23,.24]
RESCUE_MASS=[.2875,.30,.3125,.325,.3375,.35]
RESCUE_COMP=[2.0,2.25,2.5,2.75,3.0]

def eval_rule(rd,dm,dh,rh,rm,rc):
    cur=rd.current_bet.eq(1)
    drop=cur & rd.opponent_mass.lt(dm) & rd.head_prob.lt(dh)
    rescue=(~cur)&rd.head_prob.ge(rh)&rd.opponent_mass.ge(rm)&rd.composite_odds.ge(rc)
    m=(cur&~drop)|rescue
    out={
      'drop_mass':dm,'drop_head':dh,'rescue_head':rh,'rescue_mass':rm,'rescue_comp_min':rc,
      'R':int(m.sum()),'removed_current':int((cur&~m).sum()),'added_rescue':int((~cur&m).sum()),
      'hits':int(rd.loc[m,'raw_hit'].sum()),'head4':int(rd.loc[m,'head4'].sum()),
    }
    pay=float(rd.loc[m,'payout_if_bet'].sum()); out['ROI']=100*pay/(10000*out['R']) if out['R'] else np.nan
    vals=[]
    for mo in MONTHS:
        q=rd.month.eq(mo); mm=m&q; rr=int(mm.sum()); p=float(rd.loc[mm,'payout_if_bet'].sum())
        roi=100*p/(10000*rr) if rr else np.nan
        out[f'{mo}_R']=rr; out[f'{mo}_ROI']=roi; vals.append(roi)
    out['floor5_ROI']=min(vals)
    return out,m

def main():
    rd=src.rebuild()
    if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.raw_hit.sum())!=35:
        raise RuntimeError('fixed 164R reproduction failed')
    if any(rd.month.ge('2026-09')): raise RuntimeError('September outcome access blocked')
    cur=rd.current_bet.eq(1)
    base_R=int(cur.sum())
    base_ROI=100*float(rd.loc[cur,'payout_if_bet'].sum())/(10000*base_R)
    if base_R!=45 or abs(base_ROI-124.86222222222223)>1e-9:
        raise RuntimeError(f'baseline drift R={base_R} ROI={base_ROI}')

    rows=[]
    masks={}
    for dm in DROP_MASS:
      for dh in DROP_HEAD:
       for rh in RESCUE_HEAD:
        for rm in RESCUE_MASS:
         for rc in RESCUE_COMP:
          o,m=eval_rule(rd,dm,dh,rh,rm,rc)
          rows.append(o)
          masks[(dm,dh,rh,rm,rc)]=m
    grid=pd.DataFrame(rows)
    grid.to_csv(OUT/'higher_volume_grid.csv',index=False)

    eligible=grid[(grid.R>=100)&(grid.ROI>base_ROI)&(grid.floor5_ROI>=75)].copy()
    if eligible.empty: raise RuntimeError('no eligible 100R+ high-volume cells')
    ranked=eligible.sort_values(['ROI','R','floor5_ROI'],ascending=[False,False,False]).reset_index(drop=True)
    ranked.head(200).to_csv(OUT/'high_volume_ranked_top200.csv',index=False)
    s=ranked.iloc[0]

    # Drift guard for exact current research population.
    expected={'drop_mass':.40,'drop_head':.26,'rescue_head':.22,'rescue_mass':.325,'rescue_comp_min':2.5}
    for k,v in expected.items():
        if abs(float(s[k])-v)>1e-12: raise RuntimeError(f'selection drift {k}={s[k]} expected={v}')
    if int(s.R)!=110 or abs(float(s.ROI)-141.32454545454544)>1e-6:
        raise RuntimeError(f'selection drift R={s.R} ROI={s.ROI}')

    key=tuple(float(s[k]) for k in ['drop_mass','drop_head','rescue_head','rescue_mass','rescue_comp_min'])
    m=masks[key]
    detail=rd.copy()
    detail['selected_high_volume']=m.astype(int)
    detail['selection_role']=np.where(m&cur,'KEEP_CURRENT',np.where(m&~cur,'ADD_RESCUE',np.where(cur,'DROP_CURRENT','PASS')))
    detail.to_csv(OUT/'race_detail_selected.csv',index=False)

    # Volume frontier snapshots. For each minimum-R target, prioritize monthly floor then ROI.
    fronts=[]
    for target in [90,100,110,115,120]:
        q=grid[(grid.R>=target)&(grid.ROI>base_ROI)].copy()
        if q.empty: continue
        b=q.sort_values(['floor5_ROI','ROI','R'],ascending=[False,False,False]).iloc[0].to_dict()
        b['target_min_R']=target; fronts.append(b)
    pd.DataFrame(fronts).to_csv(OUT/'volume_frontier_snapshots.csv',index=False)

    # Selected-point local neighborhood robustness.
    near=grid[
      grid.drop_mass.isin([.3875,.40,.4125])&
      grid.drop_head.isin([.25,.26,.27])&
      grid.rescue_head.isin([.21,.22,.23])&
      grid.rescue_mass.isin([.3125,.325,.3375])&
      grid.rescue_comp_min.isin([2.25,2.5,2.75])
    ].copy()
    near['pass_100R_baseROI']=(near.R>=100)&(near.ROI>base_ROI)
    near['pass_100R_baseROI_floor70']=near.pass_100R_baseROI&(near.floor5_ROI>=70)
    near['pass_100R_baseROI_floor75']=near.pass_100R_baseROI&(near.floor5_ROI>=75)
    near.to_csv(OUT/'selected_neighborhood.csv',index=False)

    summary={
      'status':'HIGH_VOLUME_RESEARCH_CANDIDATE_READY',
      'baseline':{'R':base_R,'ROI':base_ROI},
      'previous_balanced_reference':{'R':77,'ROI':141.17012987012987,'monthly_floor_ROI':85.80},
      'selected_rule':{
        'keep_current_if':'NOT(opponent_mass < 0.400 AND head_prob < 0.26)',
        'add_rescue_if':'current_PASS AND head_prob >= 0.22 AND opponent_mass >= 0.325 AND composite_odds >= 2.5'
      },
      'selected':{k:(int(s[k]) if k in ['R','removed_current','added_rescue','hits','head4'] else float(s[k]))
                  for k in ['R','removed_current','added_rescue','hits','head4','ROI','floor5_ROI']},
      'monthly':[{ 'month':mo,'R':int(s[f'{mo}_R']),'ROI':float(s[f'{mo}_ROI']) } for mo in MONTHS],
      'neighborhood':{
        'cells':int(len(near)),
        'R100_baseROI':int(near.pass_100R_baseROI.sum()),
        'R100_baseROI_floor70':int(near.pass_100R_baseROI_floor70.sum()),
        'R100_baseROI_floor75':int(near.pass_100R_baseROI_floor75.sum()),
      },
      'formal_prospective_roi':'NOT_COMPUTABLE',
      'selection_period':'2026-04..2026-08 NON_PRISTINE_MODEL_SELECTION',
      'september_2026':'UNREAD',
      'production_changed':False
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')

    print('4号艇_HIGHER_VOLUME_FRONTIER_OK')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__': main()
