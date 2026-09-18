#!/usr/bin/env python3
"""Independent parity audit for HEAD4_NEWFEATURE_FIXED156_V1 production."""
from pathlib import Path
import json, math, os
import pandas as pd
import run_4head_120r_lastminute_fast as live

OUT=Path('/tmp/head4_newfeature_production_parity');OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')

def val(x):
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except Exception:return None

def main():
    p=os.environ['EXPANDED_FEATURES_208']
    z=pd.read_csv(p,dtype={'race_code':str})
    z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
    if len(z)!=208 or int(z.base120.sum())!=120:raise RuntimeError('universe/base120 drift')
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')
    art=live.load_newfeature_artifact()
    if abs(float(art['production_threshold'])-12.293333333333333)>1e-12:raise RuntimeError('threshold drift')

    scores=[]; sels=[]
    for _,r in z.iterrows():
        wall=val(r.get('wall_score')); stwall=val(r.get('st_wall_gap'))
        mwin=val(r.get('motor_win_diff_4v3')); m2=val(r.get('motor_2ren_diff_4v3'))
        raw={
          'hp':float(r.head_prob),'mass':float(r.opponent_mass),
          'st':float(r.st4_adv_inside),'orig':float(r.orig4_adv_inside),
          'market_conf':-math.log(max(float(r.composite_odds),1e-12)),
          'motor_win_rev':(-mwin if mwin is not None else None),
          'motor_2ren_rev':(-m2 if m2 is not None else None),
          'attack4':val(r.get('attack4_score')),
          'stwall_center':(-abs(stwall-.10) if stwall is not None else None),
          'wall_rev':(-wall if wall is not None else None),
        }
        score,ranks=live.score_newfeature_raw(raw,art);scores.append(score)
        add=(not bool(r.base120) and float(r.st4_adv_inside)>=-.80 and float(r.orig4_adv_inside)>=-.35 and score>=float(art['production_threshold']))
        sels.append(bool(r.base120) or add)
    z['live_newfeature_score']=scores;z['production_selected']=sels
    q=z[z.production_selected].copy()
    R=len(q);heads=int(q.head4.sum());hits=int(q.raw_hit.sum());roi=100*float(q.payout_if_bet.sum())/(10000*R)
    if (R,heads,hits)!=(156,73,40):raise RuntimeError(f'production parity count drift {(R,heads,hits)}')
    if abs(roi-140.99166666666667)>1e-9:raise RuntimeError(f'ROI drift {roi}')
    month={}
    for m in MONTHS:
        g=q[q.month.eq(m)];month[m]={'R':len(g),'ROI':100*float(g.payout_if_bet.sum())/(10000*len(g))}
    floor=min(x['ROI'] for x in month.values())
    sup=q[q.month.isin(('2026-07','2026-08'))]
    suproi=100*float(sup.payout_if_bet.sum())/(10000*len(sup))
    if abs(floor-87.21428571428571)>1e-9:raise RuntimeError(f'floor drift {floor}')
    if abs(suproi-113.17540983606557)>1e-9:raise RuntimeError(f'support ROI drift {suproi}')

    # Unit parity for LIVE motor feature construction (Nov-2025 causal state).
    card={'艇3_モーター番号':'11','艇4_モーター番号':'12','艇3_モーター2連対率':'30.0','艇4_モーター2連対率':'25.0'}
    state={'newfeature_motor_history_start':'2025-11-01','motors_newfeature_nov2025':{'07|11':{'w':2,'n':10},'07|12':{'w':4,'n':10}}}
    mf=live.newfeature_motor_raw(card,state,7)
    if abs(mf['motor_win_diff_4v3']-.2)>1e-12 or abs(mf['motor_2ren_diff_4v3']+5.0)>1e-12:
        raise RuntimeError(f'motor raw parity failed {mf}')

    # Unit parity for wall/attack construction.
    exh={'current_boats':{
      '3':{'cur_ex':.2,'cur_st':.3,'cur_orig_straight':.4,'cur_orig_avg':.5},
      '4':{'cur_ex':.1,'cur_st':.2,'cur_orig_straight':.3,'cur_orig_avg':.4},
    }}
    wf=live.newfeature_wall_raw(exh)
    expected=.20*.1+.40*.1+.25*.1+.15*.1
    if abs(wf['wall_score']-expected)>1e-12:raise RuntimeError(f'wall parity failed {wf}')

    z.to_csv(OUT/'parity_rows.csv',index=False)
    result={'profile':art['profile'],'R':R,'head4':heads,'head4_rate':100*heads/R,'exact3':hits,'ROI':roi,'monthly':month,'monthly_floor_ROI':floor,'support_ROI':suproi,'motor_unit':mf,'wall_unit':wf,'SEPTEMBER_OUTCOMES_READ':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('HEAD4_NEWFEATURE_PRODUCTION_PARITY_OK');print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
