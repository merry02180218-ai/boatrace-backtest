#!/usr/bin/env python3
"""Wave17: explicitly discriminate profitable vs unprofitable expanded-source races.

Population changed after Wave15, so OLD_NO_BET and OLD_PRE_EXCLUDED are modeled
separately.  Each test month uses only prior-month outcomes.  We fit three independent
signals inside each source group: hit probability, probability of positive race profit,
and conditional settled-value regression.  A consensus score is thresholded by prior
training quantiles.  Current rows with any required selected feature missing fail closed.
September outcomes are forbidden; legacy v288 94R is a floor and is never removed.
"""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_wave17_source_hurdle_ev.json')
OUT_MD=Path('research_v289_3head_wave17_source_hurdle_ev.md')
BANK=10000
FRACTIONS=(0.10,0.15,0.25,0.35)
SEED=20260913
MAX_FEATURES=24


def feature_screen(df, cols):
    rows=[]
    for c in cols:
        x=pd.to_numeric(df[c],errors='coerce')
        ok=np.isfinite(x)
        if int(ok.sum())<40: continue
        sd=float(x[ok].std())
        if not np.isfinite(sd) or sd<=1e-12: continue
        rows.append((float(ok.mean())*np.log1p(abs(sd)),c))
    return [c for _,c in sorted(rows,reverse=True)[:MAX_FEATURES]]


def zfit(tr, te):
    med=float(np.nanmedian(tr)) if len(tr) else 0.0
    sd=float(np.nanstd(tr,ddof=1)) if len(tr)>1 else 1.0
    if not np.isfinite(sd) or sd<1e-12: sd=1.0
    return np.clip((te-med)/sd,-6,6)


def cls_model():
    return RandomForestClassifier(n_estimators=500,max_depth=6,min_samples_leaf=6,
        max_features=.7,class_weight='balanced_subsample',random_state=SEED,n_jobs=-1)


def reg_model():
    return RandomForestRegressor(n_estimators=500,max_depth=6,min_samples_leaf=6,
        max_features=.7,random_state=SEED,n_jobs=-1)


def mmetric(df):
    m=w1.metric(df); m['max_drawdown_yen']=w1.max_drawdown(df); return m


def monthly(df):
    by={m:w1.metric(g) for m,g in df.groupby('month')}
    rois=[x['roi_pct'] for x in by.values() if x['roi_pct'] is not None]
    return by,(min(rois) if rois else None),sum(x<100 for x in rois)


def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September outcomes forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay_all,_=w1.replay_operational_pre(q); w1.add_v288_route(replay_all)
    old_pre=replay_all[replay_all.grade.isin(['S','A'])].copy()
    baseline=old_pre[old_pre.route!='NO_BET'].copy(); bm=w1.metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01:
        raise RuntimeError(f'baseline drift {bm}')
    basecodes=set(baseline.race_code.astype(str))
    oldcodes=set(old_pre[(old_pre.bet==1)&(old_pre.route=='NO_BET')].race_code.astype(str))

    grades=replay_all[['race_code','month','grade','_pre_score']].drop_duplicates(['race_code','month'])
    raw=q.copy(); w1.add_v288_route(raw,'raw_route'); raw=raw.merge(grades,on=['race_code','month'],how='inner')
    raw['source_group']=np.where(raw.race_code.astype(str).isin(oldcodes),'OLD_NO_BET','OLD_PRE_EXCLUDED')
    pool=raw[(raw.bet==1)&(raw.raw_route=='NO_BET')&(~raw.race_code.astype(str).isin(basecodes))].copy()
    if int((pool.source_group=='OLD_PRE_EXCLUDED').sum())<=0: raise RuntimeError('no PRE-excluded rows')

    allcols=w1.safe_live_cols(raw)
    # pre_score is available pre-deadline and useful for explicitly modeling PRE exclusion severity.
    if '_pre_score' in raw.columns: allcols=allcols+['_pre_score']
    picked={f:[] for f in FRACTIONS}; audit={}
    months=sorted(pool.month.unique())

    for m in months:
        month_audit={}
        for sg in ('OLD_NO_BET','OLD_PRE_EXCLUDED'):
            tr=raw[(raw.month<m)&(raw.bet==1)&(raw.raw_route=='NO_BET')&(raw.source_group==sg)].copy()
            te=pool[(pool.month==m)&(pool.source_group==sg)].copy()
            ma={'train_rows':int(len(tr)),'test_rows':int(len(te))}; month_audit[sg]=ma
            if len(tr)<55 or te.empty: continue
            fs=feature_screen(tr,allcols); ma['features']=fs
            if len(fs)<6: continue
            Xtr=tr[fs].apply(pd.to_numeric,errors='coerce')
            Xte=te[fs].apply(pd.to_numeric,errors='coerce')
            tr_valid=Xtr.notna().all(axis=1); te_valid=Xte.notna().all(axis=1)
            tr=tr.loc[tr_valid].copy(); Xtr=Xtr.loc[tr_valid]
            te=te.loc[te_valid].copy(); Xte=Xte.loc[te_valid]
            ma['valid_train']=int(len(tr)); ma['valid_test']=int(len(te))
            if len(tr)<50 or te.empty: continue
            yhit=pd.to_numeric(tr.trifecta_hit,errors='coerce').fillna(0).astype(int)
            yprofit=(pd.to_numeric(tr.ret,errors='coerce').fillna(0)>BANK).astype(int)
            yvalue=np.log1p(pd.to_numeric(tr.ret,errors='coerce').fillna(0)/BANK)
            if yhit.nunique()<2 or yprofit.nunique()<2 or int(yhit.sum())<8 or int(yprofit.sum())<5: continue
            mh=cls_model(); mp=cls_model(); mr=reg_model()
            mh.fit(Xtr,yhit); mp.fit(Xtr,yprofit); mr.fit(Xtr,yvalue)
            ph_tr=mh.predict_proba(Xtr)[:,1]; pp_tr=mp.predict_proba(Xtr)[:,1]; pv_tr=mr.predict(Xtr)
            ph_te=mh.predict_proba(Xte)[:,1]; pp_te=mp.predict_proba(Xte)[:,1]; pv_te=mr.predict(Xte)
            comp_tr=np.log(pd.to_numeric(tr.comp_odds,errors='coerce').clip(lower=.05).to_numpy(float))
            comp_te=np.log(pd.to_numeric(te.comp_odds,errors='coerce').clip(lower=.05).to_numpy(float))
            if not np.isfinite(comp_te).all():
                ok=np.isfinite(comp_te); te=te.iloc[np.where(ok)[0]].copy(); Xte=Xte.iloc[np.where(ok)[0]]
                ph_te=ph_te[ok]; pp_te=pp_te[ok]; pv_te=pv_te[ok]; comp_te=comp_te[ok]
            if te.empty: continue
            tr_score=(zfit(ph_tr,ph_tr)+zfit(pp_tr,pp_tr)+zfit(pv_tr,pv_tr)+zfit(comp_tr,comp_tr))/4.0
            te_score=(zfit(ph_tr,ph_te)+zfit(pp_tr,pp_te)+zfit(pv_tr,pv_te)+zfit(comp_tr,comp_te))/4.0
            te=te.copy(); te['_wave17_score']=te_score; te['_p_hit']=ph_te; te['_p_profit']=pp_te; te['_pred_value']=pv_te
            for frac in FRACTIONS:
                thr=float(np.quantile(tr_score,1-frac))
                g=te[te._wave17_score>=thr].copy(); g['_fraction']=frac
                picked[frac].append(g)
        audit[m]=month_audit

    rows=[]; detail={}
    for frac,parts in picked.items():
        g=pd.concat(parts,ignore_index=True) if parts else pool.iloc[0:0].copy()
        g=g.drop_duplicates('race_code').copy(); addon=mmetric(g); by,mn,red=monthly(g)
        overlap=len(set(g.race_code.astype(str)) & basecodes); comb=pd.concat([baseline,g],ignore_index=True); cm=mmetric(comb)
        src={sg:mmetric(x) for sg,x in g.groupby('source_group')}
        row={'method':'source_hurdle_ev_consensus','fraction':frac,'addon':addon,'monthly':by,'min_monthly_roi_pct':mn,
             'red_months':red,'overlap_with_v288':overlap,'combined':cm,'source_group_metrics':src,
             'old_pre_excluded_selected':int((g.source_group=='OLD_PRE_EXCLUDED').sum()) if len(g) else 0}
        rows.append(row)
        cols=['date','race_code','month','source_group','trifecta_hit','ret','comp_odds','_wave17_score','_p_hit','_p_profit','_pred_value']
        detail[f'frac@{frac:.2f}']=g[cols].to_dict('records') if len(g) else []
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['old_pre_excluded_selected']),reverse=True)
    passers=[x for x in rows if x['combined']['races']>=94 and x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3 and x['overlap_with_v288']==0]
    decision='SHADOW_CANDIDATE_WAVE17' if passers else 'NO_ADOPTION_WAVE17'
    out={'research_version':'wave17-source-hurdle-ev','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),
         'rules':{'baseline_policy':'legacy v288 94R is FLOOR','candidate':'expanded final-NO_BET including OLD_PRE_EXCLUDED','model':'source-specific hit + positive-profit hurdle + settled-value + market consensus','walk_forward':'prior-month-only Feb-Aug','july_august':'NON-PRISTINE','september_outcomes_used':False,'current_required_missing':'FAIL_CLOSED','overlap_required':0,'stake_per_race_yen':BANK},
         'baseline':mmetric(baseline),'expanded_pool':{'races':int(len(pool)),'old_no_bet':int((pool.source_group=='OLD_NO_BET').sum()),'old_pre_excluded':int((pool.source_group=='OLD_PRE_EXCLUDED').sum())},
         'methods':rows,'passers':passers,'decision':decision,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# 3号艇 Wave17 — source-specific hurdle EV','',f"Expanded pool: {len(pool)}R / PRE-excluded {int((pool.source_group=='OLD_PRE_EXCLUDED').sum())}R",'- source groups modeled independently; prior-month-only; required-current missing => fail closed','- Jul/Aug NON-PRISTINE; September outcomes unused; legacy 94R floor preserved','',
       '## Methods','|frac|add R|PRE-excl|hits|hit rate|ROI|profit|min month|red|max DD|combined R|combined ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mn=x['min_monthly_roi_pct']
        L.append(f"|{x['fraction']:.2f}|{a['races']}|{x['old_pre_excluded_selected']}|{a['hits']}|{a['hit_rate_pct'] if a['hit_rate_pct'] is not None else float('nan'):.2f}%|{a['roi_pct'] if a['roi_pct'] is not None else float('nan'):.2f}%|{a['profit_yen']:+,.0f}|{mn if mn is not None else float('nan'):.2f}%|{x['red_months']}|{a['max_drawdown_yen']:,.0f}|{c['races']}|{c['roi_pct']:.2f}%|")
    L += ['', '## Decision',f'**{decision}**']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('WAVE17_SOURCE_HURDLE_EV_OK')

if __name__=='__main__': main()
