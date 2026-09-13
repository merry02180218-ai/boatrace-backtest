#!/usr/bin/env python3
"""Wave18: expand 3-head research from the full audited Feb-Aug universe.

Unlike Waves15-17 this does NOT prefilter to bet==1 / v288 NO_BET / old PRE.
It first audits whether non-bet rows carry usable hypothetical 3-head settlement.
If settlement is available, it runs prior-month-only full-universe ranking while preserving
legacy v288 94R as a floor. If not, it fails scientifically closed and records the exact
source gap instead of pretending the 54 PRE-excluded rows are the full universe.
"""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUTJ=Path('research_v289_3head_wave18_full_universe.json')
OUTM=Path('research_v289_3head_wave18_full_universe.md')
FRACTIONS=(0.01,0.02,0.03,0.05,0.08,0.10)


def n(df,c):
    return pd.to_numeric(df[c],errors='coerce') if c in df.columns else pd.Series(np.nan,index=df.index)


def metric(df):
    return w1.metric(df) if len(df) else {'races':0,'hits':0,'hit_rate_pct':None,'stake_yen':0,'payout_yen':0.0,'profit_yen':0.0,'roi_pct':None}


def monthly(df):
    by={m:metric(g) for m,g in df.groupby('month')}
    rois=[x['roi_pct'] for x in by.values() if x['roi_pct'] is not None]
    return by,(min(rois) if rois else None),sum(r<100 for r in rois)


def fail_closed_score(tr,te,features):
    cols=[c for _,_,c in features]
    if not cols:
        return pd.Series(np.nan,index=te.index),pd.Series(False,index=te.index)
    valid=te[cols].apply(pd.to_numeric,errors='coerce').notna().all(axis=1)
    s=pd.Series(np.nan,index=te.index,dtype=float)
    if valid.any(): s.loc[valid]=w1.signed_z_score(tr,te.loc[valid],features)
    return s,valid


def main():
    q=pd.read_csv(SRC,dtype={'race_code':str})
    q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September outcomes forbidden')

    # Rebuild unchanged legacy baseline solely to exclude overlap.
    q['_target']=w1.v243_target(q).astype(int)
    replay,_=w1.replay_operational_pre(q); w1.add_v288_route(replay)
    oldpre=replay[replay.grade.isin(['S','A'])].copy()
    baseline=oldpre[oldpre.route!='NO_BET'].copy()
    bm=metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01:
        raise RuntimeError(f'baseline drift {bm}')
    basecodes=set(baseline.race_code.astype(str))

    # FULL audited universe: no bet gate, no PRE grade gate, no old route gate.
    universe=q[~q.race_code.astype(str).isin(basecodes)].copy()
    universe=universe.drop_duplicates('race_code').copy()
    allcols=w1.safe_live_cols(universe)
    livecols=w1.current_exhibition_cols(allcols)

    bet=n(universe,'bet').fillna(0)
    nonbet=universe[bet!=1].copy()
    nonbet_positive=int(((n(nonbet,'ret').fillna(0)>0)|(n(nonbet,'trifecta_hit').fillna(0)>0)).sum())
    settlement_cols={'ret': 'ret' in universe.columns, 'trifecta_hit':'trifecta_hit' in universe.columns}
    settlement_usable=all(settlement_cols.values()) and nonbet_positive>0

    census={
      'all_rows_source':int(len(q)),
      'all_unique_races_source':int(q.race_code.nunique()),
      'legacy_baseline_races':94,
      'full_universe_excluding_baseline':int(len(universe)),
      'bet1_rows':int((bet==1).sum()),
      'bet0_rows':int((bet!=1).sum()),
      'nonbet_rows_with_positive_hypothetical_settlement':nonbet_positive,
      'settlement_columns':settlement_cols,
      'settlement_usable_for_full_universe_roi':bool(settlement_usable),
    }

    rows=[]; audit={}
    if settlement_usable:
        # Train on all prior rows with pre-deadline features; score all future non-baseline rows.
        months=sorted(universe.month.unique())
        picks={}
        for m in months:
            tr=universe[universe.month<m].copy(); te=universe[universe.month==m].copy()
            if len(tr)<100 or te.empty: continue
            hitfs=w1.fit_effect(tr,allcols,'hit',24)
            retfs=w1.fit_effect(tr,allcols,'value',24)
            livefs=w1.fit_effect(tr,livecols,'hit',16)
            th=w1.signed_z_score(tr,tr,hitfs); sh,vh=fail_closed_score(tr,te,hitfs)
            trr=w1.signed_z_score(tr,tr,retfs); sr,vr=fail_closed_score(tr,te,retfs)
            tl=w1.signed_z_score(tr,tr,livefs); sl,vl=fail_closed_score(tr,te,livefs)
            tc=(w1.standardize_by_train(th,th)+w1.standardize_by_train(trr,trr)+w1.standardize_by_train(tl,tl))/3
            valid=vh&vr&vl
            sc=pd.Series(np.nan,index=te.index,dtype=float)
            if valid.any(): sc.loc[valid]=(w1.standardize_by_train(th,sh.loc[valid])+w1.standardize_by_train(trr,sr.loc[valid])+w1.standardize_by_train(tl,sl.loc[valid]))/3
            audit[m]={'train_all_rows':int(len(tr)),'test_all_rows':int(len(te)),'valid_current':int(valid.sum())}
            for frac in FRACTIONS:
                thr=float(tc.quantile(1-frac)); g=te.loc[valid & (sc>=thr)].copy()
                picks.setdefault(frac,[]).append(g)
        for frac,parts in picks.items():
            g=pd.concat(parts,ignore_index=True) if parts else universe.iloc[0:0].copy()
            g=g.drop_duplicates('race_code'); overlap=len(set(g.race_code.astype(str))&basecodes)
            a=metric(g); a['max_drawdown_yen']=w1.max_drawdown(g)
            by,mn,red=monthly(g)
            comb=pd.concat([baseline,g],ignore_index=True); cm=metric(comb); cm['max_drawdown_yen']=w1.max_drawdown(comb)
            rows.append({'fraction':frac,'addon':a,'monthly':by,'min_monthly_roi_pct':mn,'red_months':red,'overlap_with_v288':overlap,'combined':cm})
        rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)

    passers=[x for x in rows if x['combined']['races']>=94 and x['overlap_with_v288']==0 and x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    if not settlement_usable:
        decision='SOURCE_REBUILD_REQUIRED_WAVE18'
        reason='Frozen v243 audit does not provide usable hypothetical settlement on non-bet rows; build an all-race 3-head settled source before model fitting.'
    elif passers:
        decision='SHADOW_CANDIDATE_WAVE18'; reason='At least one full-universe add-on passed research guards.'
    else:
        decision='NO_ADOPTION_WAVE18'; reason='Full-universe scoring ran, but no add-on passed ROI/stability guards.'

    out={'research_version':'wave18-full-universe','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'candidate_universe':'ALL audited Feb-Aug races excluding unchanged legacy v288 baseline; no bet/PRE/route prefilter','legacy_94r_policy':'FLOOR','july_august':'NON-PRISTINE','september_outcomes_used':False,'required_current_missing':'FAIL_CLOSED','predeadline_only':True,'stake_per_race_yen':10000},'baseline':bm,'census':census,'methods':rows,'passers':passers,'decision':decision,'reason':reason,'audit':audit}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# 3号艇 Wave18 — full-universe candidate generation','',f"- source unique races: **{census['all_unique_races_source']}**",f"- research universe excluding legacy 94R: **{census['full_universe_excluding_baseline']}R**",f"- BET=0 rows: **{census['bet0_rows']}R**",f"- BET=0 rows with positive hypothetical settlement: **{nonbet_positive}R**",f"- full-universe settlement usable: **{settlement_usable}**",'', '## Methods','|frac|add R|hits|ROI|profit|min month|red|max DD|combined R|combined ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mn=x['min_monthly_roi_pct']
        L.append(f"|{x['fraction']:.2f}|{a['races']}|{a['hits']}|{a['roi_pct'] if a['roi_pct'] is not None else float('nan'):.2f}%|{a['profit_yen']:+,.0f}|{mn if mn is not None else float('nan'):.2f}%|{x['red_months']}|{a['max_drawdown_yen']:,.0f}|{c['races']}|{c['roi_pct']:.2f}%|")
    L += ['', '## Decision',f'**{decision}**','',reason]
    OUTM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L)); print('WAVE18_FULL_UNIVERSE_OK')

if __name__=='__main__': main()
