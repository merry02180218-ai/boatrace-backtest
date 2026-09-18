#!/usr/bin/env python3
"""4号艇: 77R balanced candidate を全件残したまま追加する nested expansion 監査。

Base 77R research candidate:
- KEEP current BET when opponent_mass >= 0.425
- ADD current PASS when head_prob >= 0.22, opponent_mass >= 0.375, composite_odds >= 3.0

This audit NEVER removes any of those 77 races.
Extra races are only added from outside the 77R set by a relaxed simple gate:
  head_prob >= EXTRA_HEAD
  opponent_mass >= EXTRA_MASS
  composite_odds >= EXTRA_COMP

Apr-Aug is NON-PRISTINE model-selection for this research candidate.
September 2026 outcomes/results remain UNREAD.
Production unchanged.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_4head_julaug_roi_collapse_attribution as src

OUT=Path('/tmp/head4_nested_expansion'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=['2026-04','2026-05','2026-06','2026-07','2026-08']
HEADS=[.16,.17,.18,.19,.20,.21,.22,.23]
MASSES=[.25,.2625,.275,.2875,.30,.3125,.325,.3375,.35,.3625,.375]
COMPS=[0.0,2.0,2.25,2.5,2.75,3.0,3.25]

def metric(rd,m):
    R=int(m.sum()); pay=float(rd.loc[m,'payout_if_bet'].sum())
    out={'R':R,'ROI':100*pay/(10000*R) if R else np.nan}
    vals=[]
    for mo in MONTHS:
        mm=m&rd.month.eq(mo); rr=int(mm.sum()); p=float(rd.loc[mm,'payout_if_bet'].sum())
        roi=100*p/(10000*rr) if rr else np.nan
        out[f'{mo}_R']=rr;out[f'{mo}_ROI']=roi; vals.append(roi)
    out['floor5_ROI']=min(vals)
    return out

def main():
    rd=src.rebuild()
    if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.raw_hit.sum())!=35:
        raise RuntimeError('fixed 164R reproduction failed')
    if any(rd.month.ge('2026-09')): raise RuntimeError('September outcome access blocked')

    cur=rd.current_bet.eq(1)
    base77=(cur&rd.opponent_mass.ge(.425)) | ((~cur)&rd.head_prob.ge(.22)&rd.opponent_mass.ge(.375)&rd.composite_odds.ge(3.0))
    b=metric(rd,base77)
    if b['R']!=77 or abs(b['ROI']-141.16883116883116)>1e-6:
        raise RuntimeError(f'77R base drift: {b}')

    rows=[]; masks={}
    for h in HEADS:
      for mass in MASSES:
       for comp in COMPS:
        extra=(~base77)&rd.head_prob.ge(h)&rd.opponent_mass.ge(mass)&rd.composite_odds.ge(comp)
        m=base77|extra
        o={'extra_head':h,'extra_mass':mass,'extra_comp_min':comp,'added_R':int(extra.sum())}
        o.update(metric(rd,m)); rows.append(o); masks[(h,mass,comp)]=m
    grid=pd.DataFrame(rows); grid.to_csv(OUT/'nested_expansion_grid.csv',index=False)

    # Stable expansion: maximize R while keeping overall ROI above original current baseline
    # and every month >=75%. Tie-break by higher monthly floor then ROI.
    current_baseline_roi=124.86222222222223
    stable=grid[(grid.ROI>current_baseline_roi)&(grid.floor5_ROI>=75)].copy()
    if stable.empty: raise RuntimeError('no stable nested expansion')
    stable=stable.sort_values(['R','floor5_ROI','ROI'],ascending=[False,False,False]).reset_index(drop=True)
    s=stable.iloc[0]
    if int(s.R)!=93 or abs(float(s.ROI)-128.64623655913978)>1e-6:
        raise RuntimeError(f'stable selection drift R={s.R} ROI={s.ROI}')

    # High-volume expansion: require >=110R, preserve overall ROI > current baseline,
    # then maximize monthly floor first and ROI second.
    high=grid[(grid.R>=110)&(grid.ROI>current_baseline_roi)].copy()
    if high.empty: raise RuntimeError('no 110R+ nested expansion')
    high=high.sort_values(['floor5_ROI','ROI','R'],ascending=[False,False,False]).reset_index(drop=True)
    h=high.iloc[0]
    if int(h.R)!=110 or abs(float(h.ROI)-137.2390909090909)>1e-6:
        raise RuntimeError(f'high selection drift R={h.R} ROI={h.ROI}')

    stable.head(100).to_csv(OUT/'stable_ranked_top100.csv',index=False)
    high.head(100).to_csv(OUT/'high_volume_ranked_top100.csv',index=False)

    # Snapshot best available point for minimum target volumes.
    snaps=[]
    for target in [85,90,95,100,105,110,115,120,130]:
        q=grid[(grid.R>=target)&(grid.ROI>current_baseline_roi)].copy()
        if q.empty: continue
        z=q.sort_values(['floor5_ROI','ROI','R'],ascending=[False,False,False]).iloc[0].to_dict()
        z['target_min_R']=target; snaps.append(z)
    pd.DataFrame(snaps).to_csv(OUT/'nested_volume_snapshots.csv',index=False)

    # Race detail for both frozen research profiles.
    skey=(float(s.extra_head),float(s.extra_mass),float(s.extra_comp_min))
    hkey=(float(h.extra_head),float(h.extra_mass),float(h.extra_comp_min))
    detail=rd.copy()
    detail['base77']=base77.astype(int)
    detail['stable93']=masks[skey].astype(int)
    detail['high110']=masks[hkey].astype(int)
    detail.to_csv(OUT/'race_detail_profiles.csv',index=False)

    summary={
      'status':'NESTED_EXPANSION_RESEARCH_READY',
      'base77':b,
      'stable_profile':{
        'rule':f'base77 OR (head_prob>={s.extra_head} AND opponent_mass>={s.extra_mass} AND composite_odds>={s.extra_comp_min})',
        **{k:(int(s[k]) if k in ['R','added_R'] else float(s[k])) for k in ['R','added_R','ROI','floor5_ROI']},
        'monthly':[{ 'month':mo,'R':int(s[f'{mo}_R']),'ROI':float(s[f'{mo}_ROI']) } for mo in MONTHS],
      },
      'high_volume_profile':{
        'rule':f'base77 OR (head_prob>={h.extra_head} AND opponent_mass>={h.extra_mass} AND composite_odds>={h.extra_comp_min})',
        **{k:(int(h[k]) if k in ['R','added_R'] else float(h[k])) for k in ['R','added_R','ROI','floor5_ROI']},
        'monthly':[{ 'month':mo,'R':int(h[f'{mo}_R']),'ROI':float(h[f'{mo}_ROI']) } for mo in MONTHS],
      },
      'all_base77_races_preserved':True,
      'formal_prospective_roi':'NOT_COMPUTABLE',
      'selection_period':'2026-04..2026-08 NON_PRISTINE_MODEL_SELECTION',
      'september_2026':'UNREAD',
      'production_changed':False,
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print('4号艇_NESTED_EXPANSION_OK')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__':main()
