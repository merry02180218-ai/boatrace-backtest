#!/usr/bin/env python3
"""4HEAD: formal 3-vs-4 wall overlay on frozen 120R nested-linear selection.

Research only.
- Apr-Aug 2026 historical diagnostics only.
- September outcomes are never selected/read.
- The frozen 77R base is never removed.
- v283 ticket set / payout semantics are unchanged.
- wall3 same-day feature semantics are reused exactly from 1HEAD v352.
"""
from __future__ import annotations

from pathlib import Path
import csv
import json
import math
import os

import numpy as np
import pandas as pd

import audit_4head_julaug_roi_collapse_attribution as src
import run_v352_1head_wall3_risk_audit as wall1

OUT=Path('/tmp/head4_wall3_head_rotation')
OUT.mkdir(parents=True,exist_ok=True)

# Optional local mirror for the formal 1HEAD wall builder.  This changes only
# I/O, not feature semantics: the same archived BoatraceCSV files are read.
_local_root=os.environ.get('BOATRACECSV_LOCAL_ROOT')
if _local_root:
    _brroot=Path(_local_root)
    def _local_rows(path):
        p=_brroot/path
        if not p.is_file():
            return []
        try:
            with p.open(encoding='utf-8-sig',newline='') as fh:
                return list(csv.DictReader(fh))
        except Exception:
            return []
    wall1.rows=_local_rows

DEV=('2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
MONTHS=DEV+SUP

COMP_FLOORS=(2.30,2.40,2.50,2.60,2.70)
Q_THRESHOLDS=tuple(round(x,2) for x in np.arange(.78,.861,.01))
OPEN_BETAS=(0.0,.10,.20,.30,.40,.50,.60)
BLOCK_BETAS=(0.0,.10,.20,.30,.40,.50,.60)
ATTACK4_MIN=(0.0,.50,.60,.70)

def metrics(q:pd.DataFrame)->dict:
    n=len(q)
    payout=float(q.payout_if_bet.sum()) if n else 0.0
    return {
        'R':int(n),
        'head4':int(q.head4.sum()) if n else 0,
        'head4_rate':100*float(q.head4.mean()) if n else np.nan,
        'exact3':int(q.raw_hit.sum()) if n else 0,
        'exact3_rate':100*float(q.raw_hit.mean()) if n else np.nan,
        'payout':payout,
        'ROI':100*payout/(10000*n) if n else np.nan,
        'avg_head_prob':float(q.head_prob.mean()) if n else np.nan,
        'avg_opponent_mass':float(q.opponent_mass.mean()) if n else np.nan,
        'avg_comp':float(q.composite_odds.mean()) if n else np.nan,
        'avg_wall_score':float(q.wall_score.mean()) if n else np.nan,
    }

def period_metrics(q:pd.DataFrame)->dict:
    out={}
    for name,z in [
        ('all',q),
        ('dev',q[q.month.isin(DEV)]),
        ('support',q[q.month.isin(SUP)]),
    ]:
        for k,v in metrics(z).items():
            out[f'{name}_{k}']=v
    month_rois=[]
    for m in MONTHS:
        mm=metrics(q[q.month.eq(m)])
        for k,v in mm.items():
            out[f'{m}_{k}']=v
        if mm['R']:
            month_rois.append(mm['ROI'])
    out['monthly_floor_ROI']=min(month_rois) if month_rois else np.nan
    out['dev_monthly_floor_ROI']=min(out[f'{m}_ROI'] for m in DEV if out[f'{m}_R']>0)
    out['support_monthly_floor_ROI']=min(out[f'{m}_ROI'] for m in SUP if out[f'{m}_R']>0)
    return out

def prepare()->pd.DataFrame:
    rd=src.rebuild()
    rd['race_code']=rd.race_code.astype(str).str.zfill(12)
    rd['month']=rd.month.astype(str)
    if len(rd)!=164:
        raise RuntimeError(f'candidate universe drift {len(rd)} != 164')
    if any(rd.month.str.startswith('2026-09')):
        raise RuntimeError('SEPTEMBER OUTCOME ACCESS')
    wall=wall1.exhibition_wall(set(rd.race_code))
    wall['race_code']=wall.race_code.astype(str).str.zfill(12)
    keep=['race_code','wall_exhibition_ready','ex_wall_gap','st_wall_gap',
          'straight_wall_gap','avg_wall_gap','ex_wall_score','attack4_score','wall3_score']
    z=rd.merge(wall[keep],on='race_code',how='left',validate='one_to_one')
    z=z.rename(columns={'ex_wall_score':'wall_score'})
    z['wall_ready']=z.wall_exhibition_ready.fillna(False).astype(bool)
    z['wall_score']=pd.to_numeric(z.wall_score,errors='coerce')
    z['attack4_score']=pd.to_numeric(z.attack4_score,errors='coerce')
    z['open_risk']=(-z.wall_score).clip(lower=0).fillna(0.0)
    z['block_risk']=(z.wall_score).clip(lower=0).fillna(0.0)
    z['quality']=z.head_prob+1.50*z.opponent_mass

    # Frozen 77R base from the current 120R research line.
    z['base77']=(
        ((z.composite_odds>=7.0)&(z.opponent_mass>=.425)) |
        ((z.composite_odds<7.0)&(z.head_prob>=.22)&(z.opponent_mass>=.375)&(z.composite_odds>=3.0))
    )
    z['base120']=z.base77 | ((~z.base77)&(z.composite_odds>=2.5)&(z.quality>=.82))

    n77=int(z.base77.sum()); n120=int(z.base120.sum())
    bym=z[z.base120].groupby('month').size().to_dict()
    expected={'2026-04':22,'2026-05':28,'2026-06':21,'2026-07':31,'2026-08':18}
    if n77!=77 or n120!=120 or any(int(bym.get(m,0))!=n for m,n in expected.items()):
        raise RuntimeError(f'frozen 120R drift n77={n77} n120={n120} months={bym}')
    return z

def select_cfg(z,cf,qt,ob,bb,a4):
    open_term=z.open_risk.where((z.attack4_score>=a4)&z.wall_ready,0.0)
    block_term=z.block_risk.where(z.wall_ready,0.0)
    qw=z.quality + ob*open_term - bb*block_term
    sel=z.base77 | ((~z.base77)&(z.composite_odds>=cf)&(qw>=qt))
    return sel,qw

def strata(z):
    rows=[]
    bins=[-1.01,-.60,-.40,-.20,0.0,.20,.40,.60,1.01]
    labels=['<=-.60','-.60:-.40','-.40:-.20','-.20:0','0:.20','.20:.40','.40:.60','>=.60']
    x=z.copy()
    x['wall_band']=pd.cut(x.wall_score,bins=bins,labels=labels,include_lowest=True,right=False)
    for scope,mask in [('UNIVERSE',pd.Series(True,index=x.index)),('BASE120',x.base120)]:
        q=x[mask]
        for band,g in q.groupby('wall_band',observed=True):
            rows.append({'scope':scope,'band':str(band),**metrics(g)})
    # Simple signs / attack-conditioned signs.
    for scope,mask in [('UNIVERSE',pd.Series(True,index=x.index)),('BASE120',x.base120)]:
        q=x[mask]
        tests=[
          ('WALL_NEG',q.wall_score<0),
          ('WALL_POS',q.wall_score>=0),
          ('OPEN_A4_50',(q.wall_score<0)&(q.attack4_score>=.50)),
          ('OPEN_A4_60',(q.wall_score<0)&(q.attack4_score>=.60)),
          ('OPEN_A4_70',(q.wall_score<0)&(q.attack4_score>=.70)),
          ('BLOCK_GE_20',q.wall_score>=.20),
          ('BLOCK_GE_40',q.wall_score>=.40),
        ]
        for name,m in tests:
            rows.append({'scope':scope,'band':name,**metrics(q[m])})
    return pd.DataFrame(rows)

def main():
    z=prepare()
    base=z[z.base120].copy()
    base_m=period_metrics(base)

    rows=[]
    for cf in COMP_FLOORS:
      for qt in Q_THRESHOLDS:
       for ob in OPEN_BETAS:
        for bb in BLOCK_BETAS:
         for a4 in ATTACK4_MIN:
            sel,qw=select_cfg(z,cf,qt,ob,bb,a4)
            q=z[sel].copy()
            q['quality_wall']=qw[sel]
            pm=period_metrics(q)
            removed=set(base.race_code)-set(q.race_code)
            added=set(q.race_code)-set(base.race_code)
            row={
                'comp_floor':cf,'quality_threshold':qt,'open_beta':ob,
                'block_beta':bb,'attack4_min':a4,
                'removed_from_120':len(removed),'added_to_120':len(added),
                'changed_R':len(removed)+len(added),
                'base77_retained':int(z.loc[z.base77,'race_code'].isin(set(q.race_code)).sum()),
                **pm,
            }
            rows.append(row)
    grid=pd.DataFrame(rows)

    # Candidate freeze discipline:
    # - preserve every base77 by construction;
    # - keep overall volume 115-125 and dev/support volumes near the 120R baseline;
    # - rank using Apr-Jun outcomes only; support outcomes are report-only.
    eligible=grid[
        grid.all_R.between(115,125) &
        grid.dev_R.between(66,76) &
        grid.support_R.between(44,54) &
        grid.base77_retained.eq(77)
    ].copy()
    if eligible.empty:
        raise RuntimeError('no eligible wall3 configs')
    eligible['distance120']=(eligible.all_R-120).abs()
    eligible['dev_head_gain_pp']=eligible.dev_head4_rate-base_m['dev_head4_rate']
    eligible['dev_roi_gain_pp']=eligible.dev_ROI-base_m['dev_ROI']
    eligible['dev_floor_gain_pp']=eligible.dev_monthly_floor_ROI-base_m['dev_monthly_floor_ROI']

    # Prefer stronger Apr-Jun monthly floor, then ROI, head rate, volume closeness,
    # then lower churn. Jul-Aug outcome metrics are intentionally absent from rank key.
    ranked=eligible.sort_values(
        ['dev_monthly_floor_ROI','dev_ROI','dev_head4_rate','distance120','changed_R'],
        ascending=[False,False,False,True,True]
    )
    best=ranked.iloc[0].to_dict()

    sel,qw=select_cfg(
        z,float(best['comp_floor']),float(best['quality_threshold']),
        float(best['open_beta']),float(best['block_beta']),float(best['attack4_min'])
    )
    chosen=z[sel].copy()
    chosen['quality_wall']=qw[sel]
    chosen['was_base120']=chosen.base120
    chosen['change_type']=np.where(
        chosen.race_code.isin(set(base.race_code)),
        'KEPT',
        'ADDED'
    )
    removed=base[~base.race_code.isin(set(chosen.race_code))].copy()
    removed['quality_wall']=(
        removed.quality
        + float(best['open_beta'])*removed.open_risk.where((removed.attack4_score>=float(best['attack4_min']))&removed.wall_ready,0.0)
        - float(best['block_beta'])*removed.block_risk.where(removed.wall_ready,0.0)
    )
    removed['change_type']='REMOVED'
    changes=pd.concat([
        chosen[chosen.change_type.eq('ADDED')],
        removed
    ],ignore_index=True,sort=False)

    # Diagnostics only: strongest all-period candidate under same volume constraints,
    # clearly separate from the Apr-Jun-frozen selected candidate.
    diag=eligible.sort_values(
        ['monthly_floor_ROI','all_ROI','all_head4_rate','distance120','changed_R'],
        ascending=[False,False,False,True,True]
    ).iloc[0].to_dict()

    z.to_csv(OUT/'universe_with_wall.csv',index=False)
    grid.to_csv(OUT/'grid.csv',index=False)
    ranked.head(200).to_csv(OUT/'dev_ranked_top200.csv',index=False)
    chosen.to_csv(OUT/'chosen_races.csv',index=False)
    changes.to_csv(OUT/'chosen_changes.csv',index=False)
    st=strata(z); st.to_csv(OUT/'wall_strata.csv',index=False)

    result={
      'baseline120':base_m,
      'baseline77_R':int(z.base77.sum()),
      'baseline120_R':int(z.base120.sum()),
      'wall_ready_R':int(z.wall_ready.sum()),
      'grid_cells':int(len(grid)),
      'eligible_cells':int(len(eligible)),
      'selection_rule':'Apr-Jun monthly floor -> Apr-Jun ROI -> Apr-Jun head4 rate -> distance to 120 -> churn',
      'selected_on_dev_only':best,
      'selected_support_report':{
          'Jul-Aug_R':int(best['support_R']),
          'Jul-Aug_ROI':float(best['support_ROI']),
          'Jul-Aug_head4_rate':float(best['support_head4_rate']),
          'Jul_ROI':float(best['2026-07_ROI']),
          'Aug_ROI':float(best['2026-08_ROI']),
          'support_monthly_floor_ROI':float(best['support_monthly_floor_ROI']),
      },
      'all_period_diagnostic_best_not_for_selection':diag,
      'selected_removed_from_base120':int(best['removed_from_120']),
      'selected_added_to_base120':int(best['added_to_120']),
      'selected_change_rows':int(len(changes)),
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    print('\nTOP DEV-FROZEN CANDIDATES',flush=True)
    print(ranked.head(20).to_string(index=False),flush=True)
    print('\nWALL STRATA',flush=True)
    print(st.to_string(index=False),flush=True)

if __name__=='__main__':
    main()
