#!/usr/bin/env python3
"""HEAD4 120R research: pre-exhibition candidate coverage audit.

Purpose
-------
Create a genuinely pre-exhibition parent candidate layer for the current 120R
post-exhibition research rule.

PRE candidate uses ONLY:
- causal prior motor win-rate difference 4 vs 3
- race-card motor 2-ren difference 4 vs 3
- causal prior player-4 all-race win rate

It explicitly does NOT use:
- current exhibition / exhibition ST / original exhibition
- opponent_mass
- composite odds
- result / payout / finishing order

The historical final120 set is used only AFTER pre-candidate construction to
measure recall. It never enters the PRE mask.

Optional head_prob tiers are diagnostic convenience tiers only and are marked
NON-PRISTINE because their recall is measured against the already-selected
Apr-Aug final120 set.

September 2026 outcomes remain UNREAD. Production unchanged.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import analyze_4head_b4_minus_b3_motor_win_2ren as motor
import analyze_4head_headrate_3ren_player_st as prior
import audit_4head_julaug_roi_collapse_attribution as finalsrc
import audit_4head_headprob_pass_rescue as hpsrc

OUT=Path('/tmp/head4_pre_candidate_audit'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'

WIN=-0.0299361318939513
REN2=-7.080000000000001
PLAYER=.215605
HP_CUTS=[None,.08,.10,.12,.14,.16,.18,.20,.22,.24,.26,.28,.30]


def final120_codes():
    rd=finalsrc.rebuild().copy()
    rd['race_code']=rd.race_code.astype(str).str.zfill(12)
    cur=rd.composite_odds.ge(7.0)
    base77=(
        (cur & rd.opponent_mass.ge(.425)) |
        ((~cur) & rd.head_prob.ge(.22) &
         rd.opponent_mass.ge(.375) & rd.composite_odds.ge(3.0))
    )
    score=rd.head_prob + 1.50*rd.opponent_mass
    sel=base77 | ((~base77) & rd.composite_odds.ge(2.5) & score.ge(.82))
    codes=set(rd.loc[sel,'race_code'])
    if len(codes)!=120:
        raise RuntimeError(f'final120 drift: {len(codes)}')
    return codes


def main():
    m=motor.build_motor_features().copy()
    p=prior.build_prior_features().copy()
    for z in (m,p):
        z['race_code']=z.race_code.astype(str).str.zfill(12)
        z['date']=z.date.astype(str)
        z['month']=z.date.str[:7]

    m=m[(m.date>=START)&(m.date<=END)].copy()
    p=p[(p.date>=START)&(p.date<=END)].copy()
    keep_prior=['date','month','race_code','player4_all_win','player4_frame4_win','player4_recent_p2']
    x=m.merge(p[keep_prior],on=['date','month','race_code'],how='left',validate='one_to_one')
    if x.race_code.duplicated().any():
        raise RuntimeError('pre-universe duplicate race_code')
    if len(x)==0:
        raise RuntimeError('empty pre-universe')
    if x.month.astype(str).ge('2026-09').any():
        raise RuntimeError('September pre-universe access blocked')

    pre=(
        x.motor_win_diff_4v3.ge(WIN) &
        x.motor_2ren_diff_4v3.ge(REN2) &
        x.player4_all_win.ge(PLAYER)
    )
    x['pre_candidate_wide']=pre.astype(int)

    final120=final120_codes()
    universe=set(x.race_code)
    missing=sorted(final120-universe)
    if missing:
        raise RuntimeError(f'final120 missing from pre-universe: {missing[:10]}')
    pre_codes=set(x.loc[pre,'race_code'])
    missed_wide=sorted(final120-pre_codes)
    if missed_wide:
        raise RuntimeError(f'wide PRE gate misses final120: {missed_wide[:10]}')

    # Optional pre-race head_prob tiers. Historical scoring source itself is already
    # leakage-audited; tier recall vs final120 is diagnostic/non-pristine.
    hs=hpsrc.headprob_scores().copy()
    hs['race_code']=hs.race_code.astype(str).str.zfill(12)
    x=x.merge(hs,on='race_code',how='left',validate='one_to_one')

    rows=[]
    for cut in HP_CUTS:
        mask=pre.copy()
        label='WIDE_PRE_ONLY'
        if cut is not None:
            mask &= x.head_prob.ge(cut)
            label=f'PRE_PLUS_HEAD_{cut:.2f}'
        codes=set(x.loc[mask,'race_code'])
        captured=len(final120 & codes)
        daily=x.loc[mask].groupby('date').size()
        rows.append({
            'tier':label,
            'head_prob_min':np.nan if cut is None else cut,
            'candidate_R':int(mask.sum()),
            'days_with_candidates':int((daily>0).sum()),
            'avg_candidates_per_calendar_day':float(mask.sum()/153.0),
            'avg_candidates_per_active_day':float(daily.mean()) if len(daily) else 0.0,
            'median_candidates_per_active_day':float(daily.median()) if len(daily) else 0.0,
            'p90_candidates_per_active_day':float(daily.quantile(.90)) if len(daily) else 0.0,
            'max_candidates_per_day':int(daily.max()) if len(daily) else 0,
            'final120_captured':captured,
            'final120_recall_pct':100*captured/120,
            'final120_missed':120-captured,
        })
    tiers=pd.DataFrame(rows)
    tiers.to_csv(OUT/'pre_candidate_tiers.csv',index=False)

    # Monthly and daily size for the guaranteed-recall wide PRE layer.
    monthly=[]
    for mo,g in x[pre].groupby('month'):
        monthly.append({'month':mo,'candidate_R':len(g),'days':g.date.nunique(),
                        'avg_per_active_day':len(g)/g.date.nunique() if g.date.nunique() else 0})
    pd.DataFrame(monthly).to_csv(OUT/'wide_pre_monthly.csv',index=False)
    daily=x.loc[pre].groupby('date').size().rename('candidate_R').reset_index()
    daily.to_csv(OUT/'wide_pre_daily.csv',index=False)

    # Final120 recall by month from wide pre layer (must be 100% each month).
    final_month=x[x.race_code.isin(final120)][['race_code','date','month']].copy()
    recall_month=[]
    for mo,g in final_month.groupby('month'):
        got=sum(c in pre_codes for c in g.race_code)
        recall_month.append({'month':mo,'final120_R':len(g),'captured_by_wide_pre':got,
                             'recall_pct':100*got/len(g)})
    pd.DataFrame(recall_month).to_csv(OUT/'final120_recall_by_month.csv',index=False)

    # Store only pre-result feature columns + historical final-membership marker for audit.
    detail=x[['date','month','race_code','motor_win_diff_4v3','motor_2ren_diff_4v3',
              'player4_all_win','player4_frame4_win','player4_recent_p2','head_prob',
              'pre_candidate_wide']].copy()
    detail['historical_final120_for_recall_only']=detail.race_code.isin(final120).astype(int)
    detail.to_csv(OUT/'pre_candidate_detail.csv',index=False)

    wide=tiers.iloc[0].to_dict()
    # Informational convenience tiers: highest cut maintaining >=95% and >=90% recall.
    valid95=tiers[(tiers.tier!='WIDE_PRE_ONLY')&(tiers.final120_recall_pct>=95)].copy()
    valid90=tiers[(tiers.tier!='WIDE_PRE_ONLY')&(tiers.final120_recall_pct>=90)].copy()
    tier95=None if valid95.empty else valid95.sort_values(['candidate_R','head_prob_min']).iloc[0].to_dict()
    tier90=None if valid90.empty else valid90.sort_values(['candidate_R','head_prob_min']).iloc[0].to_dict()

    summary={
      'status':'HEAD4_PRE_CANDIDATE_AUDIT_OK',
      'period':'2026-04-01..2026-08-31',
      'pre_rule':{
        'motor_win_diff_4v3_min':WIN,
        'motor_2ren_diff_4v3_min':REN2,
        'player4_all_win_min':PLAYER,
      },
      'uses_current_exhibition':False,
      'uses_current_odds':False,
      'uses_result_or_payout_in_pre_mask':False,
      'wide_pre':wide,
      'optional_95pct_recall_tier':tier95,
      'optional_90pct_recall_tier':tier90,
      'final120_recall_by_month':recall_month,
      'head_prob_tiers_note':'diagnostic NON-PRISTINE convenience tiers; WIDE_PRE_ONLY is the zero-miss parent layer',
      'september_2026':'UNREAD',
      'production_changed':False,
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=float)+'\n')

    print('HEAD4_PRE_CANDIDATE_AUDIT_OK')
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=float))
    print('9月_UNREAD')
    print('本番変更なし')


if __name__=='__main__':
    main()
