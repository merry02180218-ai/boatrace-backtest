#!/usr/bin/env python3
"""HEAD4 frozen120: fast pre-exhibition candidate tier audit.

No current-race exhibition, no odds, no outcome/payout fields enter the PRE mask.

The frozen 120R membership list is used only as an AFTER-THE-FACT recall label to
measure how much of the post-exhibition final set each PRE tier would have retained.
Therefore tuned PRE tiers are NON-PRISTINE research diagnostics.

Wide parent PRE gate:
- motor_win_diff_4v3 >= -0.0299361318939513
- motor_2ren_diff_4v3 >= -7.08
- player4_all_win >= 0.215605

The script searches only stricter versions of those same three causal/pre-race
features and reports minimum-volume simple gates at >=100%, >=95%, >=90% recall.
September outcomes remain unread. Production unchanged.
"""
from pathlib import Path
import hashlib
import itertools
import json
import numpy as np
import pandas as pd

import analyze_4head_b4_minus_b3_motor_win_2ren as motor
import analyze_4head_headrate_3ren_player_st as prior

ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/head4_pre_candidate_fast'); OUT.mkdir(parents=True,exist_ok=True)
MEMBERSHIP=ROOT/'artifacts'/'head4_120r_membership_codes_20260918.txt'
EXPECTED_HASH='37057b43e344309e3fd06dfa1f2b519cfaad16379e92bfda51166da42834844c'
START='2026-04-01'; END='2026-08-31'

BASE={
    'motor_win_diff_4v3':-0.0299361318939513,
    'motor_2ren_diff_4v3':-7.080000000000001,
    'player4_all_win':0.215605,
}

def membership():
    codes=[x.strip() for x in MEMBERSHIP.read_text().splitlines() if x.strip()]
    s='\n'.join(sorted(codes))+'\n'
    h=hashlib.sha256(s.encode()).hexdigest()
    if len(codes)!=120 or h!=EXPECTED_HASH:
        raise RuntimeError(f'membership drift n={len(codes)} hash={h}')
    return set(codes)

def daily_stats(x,m):
    q=x.loc[m]
    daily=q.groupby('date').size()
    return {
      'candidate_R':int(m.sum()),
      'active_days':int(q.date.nunique()),
      'avg_per_calendar_day':float(m.sum()/153.0),
      'avg_per_active_day':float(daily.mean()) if len(daily) else 0.0,
      'median_per_active_day':float(daily.median()) if len(daily) else 0.0,
      'p90_per_active_day':float(daily.quantile(.90)) if len(daily) else 0.0,
      'max_per_day':int(daily.max()) if len(daily) else 0,
    }

def recall_stats(x,m,final):
    codes=set(x.loc[m,'race_code'])
    got=len(codes&final)
    z=daily_stats(x,m)
    z.update({'final120_captured':got,'final120_missed':120-got,'recall_pct':100*got/120})
    return z

def main():
    final=membership()
    m=motor.build_motor_features().copy()
    p=prior.build_prior_features().copy()
    for z in (m,p):
        z['race_code']=z.race_code.astype(str).str.zfill(12)
        z['date']=z.date.astype(str)
        z['month']=z.date.str[:7]
    m=m[(m.date>=START)&(m.date<=END)].copy()
    p=p[(p.date>=START)&(p.date<=END)].copy()
    cols=['date','month','race_code','player4_all_win','player4_frame4_win','player4_recent_p2']
    x=m.merge(p[cols],on=['date','month','race_code'],how='left',validate='one_to_one')
    if x.race_code.duplicated().any(): raise RuntimeError('duplicate pre rows')
    if x.month.ge('2026-09').any(): raise RuntimeError('September access blocked')
    if not final.issubset(set(x.race_code)): raise RuntimeError('frozen120 not covered by pre universe')

    wide=(
      x.motor_win_diff_4v3.ge(BASE['motor_win_diff_4v3']) &
      x.motor_2ren_diff_4v3.ge(BASE['motor_2ren_diff_4v3']) &
      x.player4_all_win.ge(BASE['player4_all_win'])
    )
    ws=recall_stats(x,wide,final)
    if ws['final120_captured']!=120:
        raise RuntimeError(f'wide parent misses final120: {ws}')

    # Candidate thresholds are actual wide-universe quantiles, always no looser than base.
    qw=x.loc[wide].copy()
    qs=np.linspace(0,0.70,15)
    cuts={}
    for c in BASE:
        vals=pd.to_numeric(qw[c],errors='coerce').dropna()
        vv=sorted(set([BASE[c]]+[max(BASE[c],float(vals.quantile(q))) for q in qs]))
        cuts[c]=vv

    rows=[]
    # single, pair and triple tightened gates.
    features=list(BASE)
    for k in (1,2,3):
      for fs in itertools.combinations(features,k):
        grids=[cuts[f] for f in fs]
        for vals in itertools.product(*grids):
            mm=wide.copy()
            parts=[]
            for f,v in zip(fs,vals):
                mm &= pd.to_numeric(x[f],errors='coerce').ge(v)
                parts.append((f,float(v)))
            st=recall_stats(x,mm,final)
            rows.append({'kind':f'{k}D','rule':repr(parts),**st})

    grid=pd.DataFrame(rows).drop_duplicates(subset=['rule']).copy()
    grid=grid.sort_values(['candidate_R','recall_pct'],ascending=[True,False])
    grid.to_csv(OUT/'pre_tightening_grid.csv',index=False)

    selected=[]
    for target in (100,95,90):
        q=grid[grid.recall_pct.ge(target)].copy()
        if q.empty: continue
        # minimize volume, then prefer simpler gate, then higher recall.
        q['dims']=q.kind.str[0].astype(int)
        b=q.sort_values(['candidate_R','dims','recall_pct'],ascending=[True,True,False]).iloc[0].to_dict()
        b['target_recall_pct']=target
        selected.append(b)
    sel=pd.DataFrame(selected)
    sel.to_csv(OUT/'pre_recall_tiers.csv',index=False)

    # Wide monthly / daily.
    monthly=[]
    for mo,g in x[wide].groupby('month'):
        monthly.append({'month':mo,'candidate_R':len(g),'active_days':g.date.nunique(),
                        'avg_per_active_day':len(g)/g.date.nunique()})
    pd.DataFrame(monthly).to_csv(OUT/'wide_monthly.csv',index=False)
    x.loc[wide].groupby('date').size().rename('candidate_R').reset_index().to_csv(OUT/'wide_daily.csv',index=False)

    # Per-month final recall for selected tiers.
    tier_month=[]
    for _,r in sel.iterrows():
        import ast
        mm=wide.copy()
        for f,v in ast.literal_eval(r.rule):
            mm &= pd.to_numeric(x[f],errors='coerce').ge(float(v))
        cc=set(x.loc[mm,'race_code'])
        for mo in sorted(x.month.unique()):
            fm={c for c in final if c.startswith(mo.replace('-',''))}
            if not fm: continue
            got=len(fm&cc)
            tier_month.append({'target_recall_pct':int(r.target_recall_pct),'month':mo,
                               'final120_R':len(fm),'captured':got,'recall_pct':100*got/len(fm)})
    pd.DataFrame(tier_month).to_csv(OUT/'tier_recall_by_month.csv',index=False)

    detail=x[['date','month','race_code','motor_win_diff_4v3','motor_2ren_diff_4v3',
              'player4_all_win','player4_frame4_win','player4_recent_p2']].copy()
    detail['wide_pre']=wide.astype(int)
    detail['historical_final120_recall_label_only']=detail.race_code.isin(final).astype(int)
    detail.to_csv(OUT/'pre_detail.csv',index=False)

    summary={
      'status':'HEAD4_PRE_CANDIDATE_FAST_OK',
      'wide_rule':BASE,
      'wide':ws,
      'tiers':selected,
      'pre_mask_uses_current_exhibition':False,
      'pre_mask_uses_odds':False,
      'pre_mask_uses_result_or_payout':False,
      'tier_tuning_status':'NON_PRISTINE Apr-Aug final120 recall optimization',
      'september_2026':'UNREAD',
      'production_changed':False,
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=float)+'\n')
    print('HEAD4_PRE_CANDIDATE_FAST_OK')
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=float))
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__':
    main()
