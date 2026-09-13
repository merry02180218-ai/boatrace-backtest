#!/usr/bin/env python3
"""Wave15: reopen races excluded by the old PRE S/A candidate source.

The v288 94-race production set is a floor, not a fixed research count.  We keep every
baseline race and search additional buyable final-NO_BET races including PRE-B rows that
were outside the former add-on universe.  Old Wave1 signal families are deliberately
retested because the population changed.  Every test month is scored with prior-month
outcomes only; current required features fail closed.  September outcomes are forbidden.
"""
from pathlib import Path
import json, os, math
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_wave15_expanded_source_replay.json')
OUT_MD=Path('research_v289_3head_wave15_expanded_source_replay.md')
BANK=10000
FRACTIONS=(0.15,0.25,0.45)
METHODS=('residual_hit','exhibition_upgrade','return_rank','orthogonal_consensus','ev_calibrated')


def fail_closed_score(tr, te, feats):
    if not feats:
        return pd.Series(np.nan,index=te.index), pd.Series(False,index=te.index)
    cols=[c for _,_,c in feats]
    valid=te[cols].apply(pd.to_numeric,errors='coerce').notna().all(axis=1)
    score=pd.Series(np.nan,index=te.index,dtype=float)
    if valid.any(): score.loc[valid]=w1.signed_z_score(tr,te.loc[valid],feats)
    return score,valid


def mmetric(df):
    m=w1.metric(df); m['max_drawdown_yen']=w1.max_drawdown(df); return m


def monthly(df):
    by={m:w1.metric(g) for m,g in df.groupby('month')}
    rois=[x['roi_pct'] for x in by.values() if x['roi_pct'] is not None]
    return by, (min(rois) if rois else None), sum(r<100 for r in rois)


def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September outcomes forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay_all,pre_thresholds=w1.replay_operational_pre(q)
    w1.add_v288_route(replay_all)
    old_pre=replay_all[replay_all.grade.isin(['S','A'])].copy()
    baseline=old_pre[old_pre.route!='NO_BET'].copy()
    bm=w1.metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01:
        raise RuntimeError(f'baseline drift {bm}')
    basecodes=set(baseline.race_code.astype(str))

    raw=q.copy(); w1.add_v288_route(raw,'raw_route')
    grades=replay_all[['race_code','month','grade','_pre_score']].drop_duplicates(['race_code','month'])
    raw=raw.merge(grades,on=['race_code','month'],how='inner')
    pool=raw[(raw.bet==1)&(raw.raw_route=='NO_BET')&(~raw.race_code.astype(str).isin(basecodes))].copy()
    oldcodes=set(old_pre[(old_pre.bet==1)&(old_pre.route=='NO_BET')].race_code.astype(str))
    pool['source_group']=np.where(pool.race_code.astype(str).isin(oldcodes),'OLD_NO_BET','OLD_PRE_EXCLUDED')
    if not (pool.source_group=='OLD_PRE_EXCLUDED').any(): raise RuntimeError('expanded source contains no formerly PRE-excluded rows')

    allcols=w1.safe_live_cols(raw); livecols=w1.current_exhibition_cols(allcols)
    months=sorted(pool.month.unique()); picked={}; audit={}
    for m in months:
        tr=raw[(raw.month<m)&(raw.bet==1)&(raw.raw_route=='NO_BET')].copy()
        te=pool[pool.month==m].copy()
        if len(tr)<50 or te.empty: continue
        hitfs=w1.fit_effect(tr,allcols,'hit',18)
        livefs=w1.fit_effect(tr,livecols,'hit',12)
        retfs=w1.fit_effect(tr,allcols,'value',18)
        tr_hit=w1.signed_z_score(tr,tr,hitfs); te_hit,v_hit=fail_closed_score(tr,te,hitfs)
        tr_live=w1.signed_z_score(tr,tr,livefs); te_live,v_live=fail_closed_score(tr,te,livefs)
        tr_ret=w1.signed_z_score(tr,tr,retfs); te_ret,v_ret=fail_closed_score(tr,te,retfs)
        tr_cons=(w1.standardize_by_train(tr_hit,tr_hit)+w1.standardize_by_train(tr_live,tr_live)+w1.standardize_by_train(tr_ret,tr_ret))/3.0
        v_cons=v_hit&v_live&v_ret
        te_cons=pd.Series(np.nan,index=te.index,dtype=float)
        if v_cons.any():
            te_cons.loc[v_cons]=(w1.standardize_by_train(tr_hit,te_hit.loc[v_cons])+w1.standardize_by_train(tr_live,te_live.loc[v_cons])+w1.standardize_by_train(tr_ret,te_ret.loc[v_cons]))/3.0
        scoremap={'residual_hit':(tr_hit,te_hit,v_hit),'exhibition_upgrade':(tr_live,te_live,v_live),'return_rank':(tr_ret,te_ret,v_ret),'orthogonal_consensus':(tr_cons,te_cons,v_cons)}
        audit[m]={'train_rows':int(len(tr)),'expanded_test_rows':int(len(te)),'old_pre_excluded_rows':int((te.source_group=='OLD_PRE_EXCLUDED').sum()),'valid_hit':int(v_hit.sum()),'valid_live':int(v_live.sum()),'valid_return':int(v_ret.sum()),'valid_consensus':int(v_cons.sum())}
        for method,(trs,tes,valid) in scoremap.items():
            for frac in FRACTIONS:
                thr=float(trs.quantile(1-frac)); g=te.loc[valid & (tes>=thr)].copy()
                picked.setdefault((method,frac),[]).append(g)
        for frac in FRACTIONS:
            alpha=w1.choose_ev_alpha(tr,tr_hit,frac)
            tro=w1.num(tr,'comp_odds')
            tr_ev=w1.standardize_by_train(tr_hit,tr_hit)+alpha*np.log(tro.clip(lower=.05)).fillna(0)
            valid=v_hit & pd.to_numeric(te.comp_odds,errors='coerce').notna()
            te_ev=pd.Series(np.nan,index=te.index,dtype=float)
            if valid.any(): te_ev.loc[valid]=w1.standardize_by_train(tr_hit,te_hit.loc[valid])+alpha*np.log(pd.to_numeric(te.loc[valid,'comp_odds'],errors='coerce').clip(lower=.05))
            thr=float(tr_ev.quantile(1-frac)); g=te.loc[valid & (te_ev>=thr)].copy(); picked.setdefault(('ev_calibrated',frac),[]).append(g)

    rows=[]; detail={}
    for key,parts in picked.items():
        method,frac=key; g=pd.concat(parts,ignore_index=True) if parts else pool.iloc[0:0].copy()
        g=g.drop_duplicates('race_code').copy(); addon=mmetric(g); by,mn,red=monthly(g)
        overlap=len(set(g.race_code.astype(str)) & basecodes)
        comb=pd.concat([baseline,g],ignore_index=True); cm=mmetric(comb)
        expanded_n=int((g.source_group=='OLD_PRE_EXCLUDED').sum()) if len(g) else 0
        row={'method':method,'fraction':frac,'addon':addon,'monthly':by,'min_monthly_roi_pct':mn,'red_months':red,'max_drawdown_yen':addon['max_drawdown_yen'],'overlap_with_v288':overlap,'old_pre_excluded_selected':expanded_n,'combined':cm}
        rows.append(row)
        detail[f'{method}@{frac:.2f}']=g[['date','race_code','month','grade','source_group','trifecta_hit','ret']].to_dict('records') if len(g) else []
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['old_pre_excluded_selected'],x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['combined']['races']>=94 and x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3 and x['overlap_with_v288']==0]
    decision='SHADOW_CANDIDATE_WAVE15' if passers else 'NO_ADOPTION_WAVE15'
    out={'research_version':'wave15-expanded-source-replay','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_policy':'v288 legacy 94R is a FLOOR; never reduce it','candidate_universe':'buyable final-NO_BET including races formerly excluded by old PRE S/A source','reused_families':list(METHODS),'test':'prior-month-only walk-forward Feb-Aug','july_august':'NON-PRISTINE','september_outcomes_used':False,'current_required_missing':'FAIL_CLOSED','overlap_with_v288_required':0,'stake_per_race_yen':BANK},'baseline':mmetric(baseline),'expanded_pool':{'races':int(len(pool)),'old_no_bet':int((pool.source_group=='OLD_NO_BET').sum()),'old_pre_excluded':int((pool.source_group=='OLD_PRE_EXCLUDED').sum())},'methods':rows,'passers':passers,'decision':decision,'pre_thresholds':pre_thresholds,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# 3号艇 Wave15 — expanded source + prior-Wave replay','', '- legacy v288 **94R is a floor, not a fixed research count**','- candidate source now includes buyable final-NO_BET races formerly excluded by old PRE S/A','- old Wave1 signal families are re-evaluated only because the population changed','- prior-month-only walk-forward; Jul/Aug NON-PRISTINE; September outcomes unused','- current required features missing => fail closed; overlap with legacy v288 must be 0','',f"Expanded pool: {len(pool)}R (old NO_BET {int((pool.source_group=='OLD_NO_BET').sum())} / old PRE-excluded {int((pool.source_group=='OLD_PRE_EXCLUDED').sum())})",'', '## Methods','|method|frac|add R|old PRE-excluded|hits|ROI|profit|min month|red|max DD|combined R|combined ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mn=x['min_monthly_roi_pct']
        L.append(f"|{x['method']}|{x['fraction']:.2f}|{a['races']}|{x['old_pre_excluded_selected']}|{a['hits']}|{a['roi_pct'] if a['roi_pct'] is not None else float('nan'):.2f}%|{a['profit_yen']:+,.0f}|{mn if mn is not None else float('nan'):.2f}%|{x['red_months']}|{a['max_drawdown_yen']:,.0f}|{c['races']}|{c['roi_pct']:.2f}%|")
    L += ['', '## Decision',f'**{decision}**']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('WAVE15_EXPANDED_SOURCE_OK')

if __name__=='__main__': main()
