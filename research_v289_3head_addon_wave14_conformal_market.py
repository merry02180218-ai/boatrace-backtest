#!/usr/bin/env python3
"""Wave14: conformal selective gating over a deterministic pre-deadline market ticket policy.

The candidate source is intentionally different from Waves1-13.  We first choose one
exact JPY10,000 Dutch ticket configuration using only pre-deadline market structure
(composite odds and ticket count), then learn whether that deterministic ticket is
selectively trustworthy.  Each test month uses only prior-month outcomes.  A chronological
fit/calibration split creates positive-class conformal acceptance thresholds; current
required feature missingness fails closed.  September outcomes are forbidden.
"""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
import research_v289_3head_addon as w1
import research_v289_3head_addon_wave2 as w2
import research_v289_3head_addon_wave13_hurdle_ticket_ev as w13

OUT_JSON=Path('research_v289_3head_addon_wave14_conformal_market.json')
OUT_MD=Path('research_v289_3head_addon_wave14_conformal_market.md')
BANK=10000
ALPHAS=(0.05,0.10,0.20,0.30)
SEED=20260913
MAX_FEATURES=24
POLICIES=('market_density','market_efficiency')


def qhigher(x, q):
    a=np.sort(np.asarray(x,float))
    if len(a)==0: return None
    k=int(np.ceil(q*len(a)))-1
    return float(a[min(max(k,0),len(a)-1)])


def numeric_feature_screen(df, cols):
    rows=[]
    for c in cols:
        x=pd.to_numeric(df[c],errors='coerce')
        ok=np.isfinite(x)
        if ok.sum()<30: continue
        sd=float(x[ok].std())
        if sd<=1e-12: continue
        coverage=float(ok.mean())
        rows.append((coverage*np.log1p(sd),c))
    return [c for _,c in sorted(rows,reverse=True)[:MAX_FEATURES]]


def market_score(df, policy):
    comp=pd.to_numeric(df.comp_alt,errors='coerce')
    n=pd.to_numeric(df.n_alt,errors='coerce')
    if policy=='market_density':
        return comp/np.sqrt(n.clip(lower=1))
    if policy=='market_efficiency':
        return comp/n.clip(lower=1)
    raise ValueError(policy)


def choose_market_ticket(mat, policy):
    z=mat.copy()
    z['_market_score']=market_score(z,policy)
    z=z[np.isfinite(z._market_score)].copy()
    z=z.sort_values(['race_code','_market_score','comp_alt'],ascending=[True,False,False])
    return z.groupby('race_code',as_index=False).head(1).copy()


def make_model():
    return make_pipeline(
        SimpleImputer(strategy='median'),
        RandomForestClassifier(n_estimators=500,max_depth=6,min_samples_leaf=6,
                               max_features=.7,class_weight='balanced_subsample',
                               random_state=SEED,n_jobs=-1)
    )


def metric(g): return w13.metric_ticket(g)
def maxdd(g): return w13.maxdd_ticket(g)
def monthly(g): return w13.monthly(g)


def main():
    q,baseline,candidates,raw=w2.base_universe()
    if q.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    candcodes=set(candidates.race_code.astype(str))
    mat,allcols=w13.build_matrix(q,raw,candcodes)
    mat=mat[mat.raw_route=='NO_BET'].copy()
    months=sorted(candidates.month.unique())
    results=[]; detail={}; audit={}

    for policy in POLICIES:
        chosen=choose_market_ticket(mat,policy)
        chosen['is_candidate']=chosen.race_code.astype(str).isin(candcodes)
        policy_parts={a:[] for a in ALPHAS}
        audit[policy]={}
        for m in months:
            tr=chosen[chosen.month<m].copy()
            te=chosen[(chosen.month==m)&chosen.is_candidate].copy()
            ma={'train_races':int(len(tr)),'test_races':int(len(te))}
            audit[policy][m]=ma
            if len(tr)<50 or te.empty: continue
            fs=numeric_feature_screen(tr,allcols)
            ma['features']=fs
            if len(fs)<5: continue
            tr=tr.sort_values(['date','race_code']).reset_index(drop=True)
            split=max(30,int(np.floor(len(tr)*0.70)))
            if split>=len(tr)-15: split=len(tr)-15
            fit=tr.iloc[:split].copy(); cal=tr.iloc[split:].copy()
            yfit=pd.to_numeric(fit.hit_alt,errors='coerce').fillna(0).astype(int)
            ycal=pd.to_numeric(cal.hit_alt,errors='coerce').fillna(0).astype(int)
            if yfit.nunique()<2 or int(yfit.sum())<10 or int(ycal.sum())<4: continue
            model=make_model(); model.fit(fit[fs].apply(pd.to_numeric,errors='coerce'),yfit)
            # Fail closed for the current/calibration rows used to establish the gate.
            cal_valid=cal[fs].apply(pd.to_numeric,errors='coerce').notna().all(axis=1)
            cal=cal.loc[cal_valid].copy(); ycal=ycal.loc[cal_valid]
            te_valid=te[fs].apply(pd.to_numeric,errors='coerce').notna().all(axis=1)
            te=te.loc[te_valid].copy()
            ma['cal_races']=int(len(cal)); ma['valid_test_races']=int(len(te))
            if len(cal)<12 or int(ycal.sum())<4 or te.empty: continue
            pcal=model.predict_proba(cal[fs].apply(pd.to_numeric,errors='coerce'))[:,1]
            pte=model.predict_proba(te[fs].apply(pd.to_numeric,errors='coerce'))[:,1]
            te['_p_hit']=pte
            pos_scores=1.0-pcal[ycal.to_numpy()==1]
            ma['positive_calibration']=int(len(pos_scores))
            for alpha in ALPHAS:
                qv=qhigher(pos_scores,1-alpha)
                if qv is None: continue
                cutoff=1.0-qv
                g=te[te._p_hit>=cutoff].copy()
                g['_alpha']=alpha; g['_cutoff']=cutoff
                policy_parts[alpha].append(g)
                ma[f'cutoff_a{alpha:.2f}']=cutoff

        for alpha in ALPHAS:
            parts=policy_parts[alpha]
            g=pd.concat(parts,ignore_index=True) if parts else chosen.iloc[0:0].copy()
            a=metric(g); a['max_drawdown_yen']=maxdd(g); mo,red,mn=monthly(g)
            b=baseline[['date','race_code','ret','trifecta_hit']].copy(); b['month']=b.date.astype(str).str[:7]
            b=b.rename(columns={'ret':'ret_alt','trifecta_hit':'hit_alt'})
            comb=pd.concat([b,g[['date','race_code','month','ret_alt','hit_alt']]],ignore_index=True)
            cm=metric(comb); cm['max_drawdown_yen']=maxdd(comb)
            row={'method':f'conformal_{policy}','alpha':alpha,'addon':a,'monthly':mo,
                 'red_months':red,'min_monthly_roi_pct':mn,'combined':cm,
                 'overlap_with_v288':0,'config_counts':g.config.value_counts().to_dict() if len(g) else {}}
            results.append(row)
            detail[f'{policy}@a{alpha:.2f}']=g[['date','race_code','month','config','n_alt','comp_alt','hit_alt','ret_alt','_market_score','_p_hit','_cutoff']].to_dict('records') if len(g) else []

    results.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in results if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    dec='SHADOW_CANDIDATE_WAVE14' if passers else 'NO_ADOPTION_WAVE14'
    bm=w1.metric(baseline)
    out={'research_version':'v289-addon-wave14-conformal-market','github_run_id':os.getenv('GITHUB_RUN_ID'),
         'source_max_date':q.date.max(),'rules':{'baseline_fixed':'v288 94R','candidate':'final v288 NO_BET only',
         'mechanism':'deterministic pre-deadline market ticket policy + chronological positive-class conformal selective gate',
         'ticket_family':'Wave2 regenerated configurations, exact 10000-yen Dutch','test':'walk-forward Feb-Aug',
         'training':'prior-month final-NO_BET only; chronological fit/calibration split','current_required_missing':'FAIL_CLOSED',
         'july_august':'NON-PRISTINE','september_outcomes_used':False},
         'baseline':{**bm,'max_drawdown_yen':w1.max_drawdown(baseline)},'candidate_pool':w1.metric(candidates),
         'methods':results,'passers':passers,'decision':dec,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on — Wave 14 conformal market gating','',
       '- v288 **94R fixed**, final NO_BET only','- deterministic pre-deadline market-structure ticket choice, then conformal selective gating',
       '- prior-month-only walk-forward Feb-Aug; chronological fit/calibration split','- exact 10,000-yen Dutch; required current feature missing => fail closed',
       '- Jul/Aug NON-PRISTINE; September outcomes unused','', '## Methods',
       '|method|alpha|R|hits|hit rate|ROI|profit|min month|red|max DD|overlap|combined R|combined ROI|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in results:
        a=x['addon']; c=x['combined']; mn=x['min_monthly_roi_pct']
        L.append(f'|{x["method"]}|{x["alpha"]:.2f}|{a["races"]}|{a["hits"]}|{a["hit_rate_pct"] if a["hit_rate_pct"] is not None else float("nan"):.2f}%|{a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}%|{a["profit_yen"]:+,.0f}|{mn if mn is not None else float("nan"):.2f}%|{x["red_months"]}|{a["max_drawdown_yen"]:,.0f}|0|{c["races"]}|{c["roi_pct"]:.2f}%|')
    L += ['', '## Decision',f'**{dec}**']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L)); print('V289_WAVE14_CONFORMAL_MARKET_OK')

if __name__=='__main__': main()
