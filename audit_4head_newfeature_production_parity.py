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
    z['selection_path']=z.apply(lambda r: ('base120' if bool(r.base120) else ('newfeature_add' if bool(r.production_selected) else 'not_selected')),axis=1)
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

    # Diagnostic only: head-probability bands inside frozen production selections.
    # This does not alter production and does not access September.
    bands=[(-1.0,.10,'lt_010'),(.10,.18,'010_018'),(.18,1.01,'ge_018')]
    hp_bands={}
    for lo,hi,name in bands:
        g=q[(q.head_prob>=lo)&(q.head_prob<hi)].copy()
        Rb=len(g); hb=int(g.head4.sum()) if Rb else 0; xb=int(g.raw_hit.sum()) if Rb else 0
        stake=10000*Rb
        payout=float(g.payout_if_bet.sum()) if Rb else 0.0
        hp_bands[name]={'R':Rb,'head4':hb,'head4_rate':(100*hb/Rb if Rb else None),'exact3':xb,'stake':stake,'payout':payout,'ROI':(100*payout/stake if stake else None),'mean_head_prob':(float(g.head_prob.mean()) if Rb else None)}

    # Diagnostic only: decompose frozen 156 by selection path and head-probability band.
    path_band={}
    for path in ('base120','newfeature_add'):
        pg=q[q.selection_path.eq(path)]
        path_band[path]={'R':len(pg),'head4':int(pg.head4.sum()),'exact3':int(pg.raw_hit.sum()),'ROI':(100*float(pg.payout_if_bet.sum())/(10000*len(pg)) if len(pg) else None),'bands':{}}
        for lo,hi,name in bands:
            g=pg[(pg.head_prob>=lo)&(pg.head_prob<hi)]
            rb=len(g); payout=float(g.payout_if_bet.sum()) if rb else 0.0
            path_band[path]['bands'][name]={'R':rb,'head4':int(g.head4.sum()) if rb else 0,'head4_rate':(100*float(g.head4.sum())/rb if rb else None),'exact3':int(g.raw_hit.sum()) if rb else 0,'ROI':(100*payout/(10000*rb) if rb else None)}

    # Diagnostic: historical BET concentration by calendar date in the 208-row research universe.
    # Uses only Apr-Aug historical rows; September remains unread.
    date_col=next((c for c in ('date','race_date','target_date') if c in z.columns),None)
    daily_bet={}
    if date_col:
        dz=z.copy(); dz['_audit_date']=dz[date_col].astype(str).str[:10]
        dg=dz.groupby('_audit_date',dropna=False)
        counts=dg.production_selected.sum().astype(int)
        base_counts=dg.base120.sum().astype(int)
        add_counts=(dg.production_selected.sum()-dg.base120.sum()).astype(int)
        # Calendar-day denominator must be Apr-Aug calendar days, not only dates
        # represented by the narrowed 208-row research universe.
        full_days=pd.date_range('2026-04-01','2026-08-31',freq='D').strftime('%Y-%m-%d')
        counts=counts.reindex(full_days,fill_value=0)
        base_counts=base_counts.reindex(full_days,fill_value=0)
        add_counts=add_counts.reindex(full_days,fill_value=0)
        daily_bet={
          'date_column':date_col,
          'calendar_days_apr_aug':int(len(full_days)),
          'days_in_universe':int(counts.size),
          'total_selected':int(counts.sum()),
          'mean_bets_per_universe_day':float(counts.mean()),
          'median_bets_per_universe_day':float(counts.median()),
          'max_bets_per_universe_day':int(counts.max()),
          'days_ge_7_bets':int((counts>=7).sum()),
          'share_days_ge_7_bets':float((counts>=7).mean()),
          'p95_bets_per_calendar_day':float(counts.quantile(.95)),
          'days_ge_5_bets':int((counts>=5).sum()),
          'daily_counts':{str(k):{'selected':int(counts.loc[k]),'base120':int(base_counts.loc[k]),'newfeature_add':int(add_counts.loc[k])} for k in counts.index}
        }

    z.to_csv(OUT/'parity_rows.csv',index=False)
    result={'profile':art['profile'],'R':R,'head4':heads,'head4_rate':100*heads/R,'exact3':hits,'ROI':roi,'monthly':month,'monthly_floor_ROI':floor,'support_ROI':suproi,'motor_unit':mf,'wall_unit':wf,'head_prob_bands':hp_bands,'selection_path_head_prob_bands':path_band,'daily_bet_concentration':daily_bet,'SEPTEMBER_OUTCOMES_READ':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('HEAD4_NEWFEATURE_PRODUCTION_PARITY_OK');print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
