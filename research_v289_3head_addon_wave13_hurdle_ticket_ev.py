#!/usr/bin/env python3
"""Wave13: hurdle-calibrated ticket generator for v288 final NO_BET add-ons.

This changes the candidate mechanism again after Wave12: instead of regressing settled
return directly, it decomposes each pre-deadline ticket option into (1) probability of
hitting and (2) payout conditional on a hit. Their product is a hurdle EV. A second,
independent direct-value model must agree on the chosen ticket before the race is eligible.
Every test month is trained on prior months only. September outcomes are forbidden.
"""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
import research_v289_3head_addon as w1
import research_v289_3head_addon_wave2 as w2

OUT_JSON=Path('research_v289_3head_addon_wave13_hurdle_ticket_ev.json')
OUT_MD=Path('research_v289_3head_addon_wave13_hurdle_ticket_ev.md')
BANK=10000
FRACTIONS=(.10,.20,.30,.40)
TOPK=18
SEED=20260913


def select_features(tr, cols):
    # Race-level feature screen against whether any regenerated ticket family hit.
    tgt=tr.groupby('race_code',as_index=False).hit_alt.max().rename(columns={'hit_alt':'race_hit'})
    base=tr.drop_duplicates('race_code')[['race_code']+cols].merge(tgt,on='race_code',how='inner')
    y=pd.to_numeric(base.race_hit,errors='coerce').fillna(0)
    rows=[]
    for c in cols:
        x=pd.to_numeric(base[c],errors='coerce'); ok=x.notna()&np.isfinite(x)&np.isfinite(y)
        if ok.sum()<30 or x[ok].std()<=1e-12: continue
        r=np.corrcoef(x[ok],y[ok])[0,1]
        if np.isfinite(r): rows.append((abs(r),c))
    return [c for _,c in sorted(rows,reverse=True)[:TOPK]]


def metric_ticket(df):
    n=len(df); payout=float(pd.to_numeric(df.ret_alt,errors='coerce').fillna(0).sum()) if n else 0.0
    hits=int(pd.to_numeric(df.hit_alt,errors='coerce').fillna(0).sum()) if n else 0; stake=n*BANK
    return {'races':int(n),'hits':hits,'hit_rate_pct':100*hits/n if n else None,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None}


def maxdd_ticket(df):
    if len(df)==0:return 0.0
    z=df.sort_values(['date','race_code']); pnl=pd.to_numeric(z.ret_alt,errors='coerce').fillna(0)-BANK
    curve=pnl.cumsum().to_numpy(float); peaks=np.maximum.accumulate(np.r_[0.,curve]); return float((peaks[1:]-curve).max())


def monthly(g):
    d={m:metric_ticket(x) for m,x in g.groupby('month')}; r=[x['roi_pct'] for x in d.values() if x['roi_pct'] is not None]
    return d,sum(x<100 for x in r),min(r) if r else None


def build_matrix(q, raw, candidate_codes):
    mat,_=w2.regenerate(q.race_code.astype(str)); mat['race_code']=mat.race_code.astype(str)
    featcols=w1.safe_live_cols(raw); featcols=[c for c in featcols if c in raw.columns and c not in ('p3',)]
    race=raw[['race_code','month','raw_route']+featcols].copy(); race['race_code']=race.race_code.astype(str); race=race.drop_duplicates('race_code')
    mat=mat.merge(race,on=['race_code','month'],how='left'); mat['is_candidate']=mat.race_code.isin(set(candidate_codes))
    return mat,featcols


def make_models():
    hit=make_pipeline(SimpleImputer(strategy='median'),RandomForestClassifier(n_estimators=320,max_depth=6,min_samples_leaf=7,max_features=.7,class_weight='balanced_subsample',random_state=SEED,n_jobs=-1))
    pay=make_pipeline(SimpleImputer(strategy='median'),RandomForestRegressor(n_estimators=280,max_depth=5,min_samples_leaf=5,max_features=.7,random_state=SEED+1,n_jobs=-1))
    direct=make_pipeline(SimpleImputer(strategy='median'),RandomForestRegressor(n_estimators=280,max_depth=5,min_samples_leaf=8,max_features=.7,random_state=SEED+2,n_jobs=-1))
    return hit,pay,direct


def main():
    q,baseline,candidates,raw=w2.base_universe()
    if q.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    candcodes=set(candidates.race_code.astype(str)); mat,allcols=build_matrix(q,raw,candcodes)
    trainmat=mat[mat.raw_route=='NO_BET'].copy(); months=sorted(candidates.month.unique())
    choices=[]; audit={}
    for m in months:
        tr=trainmat[trainmat.month<m].copy(); te=mat[(mat.month==m)&mat.is_candidate].copy()
        audit[m]={'train_ticket_rows':int(len(tr)),'train_races':int(tr.race_code.nunique()),'test_ticket_rows':int(len(te)),'test_races':int(te.race_code.nunique())}
        if tr.race_code.nunique()<35 or te.empty: continue
        fs=select_features(tr,allcols); audit[m]['features']=fs
        if len(fs)<5: continue
        modelcols=fs+['n_alt','comp_alt']
        Xtr=tr[modelcols].apply(pd.to_numeric,errors='coerce'); yh=pd.to_numeric(tr.hit_alt,errors='coerce').fillna(0).astype(int)
        if yh.nunique()<2 or int(yh.sum())<20: continue
        hit,pay,direct=make_models(); hit.fit(Xtr,yh)
        hmask=yh.eq(1)&pd.to_numeric(tr.ret_alt,errors='coerce').gt(0)
        if int(hmask.sum())<20: continue
        pay.fit(Xtr.loc[hmask],np.log1p(pd.to_numeric(tr.loc[hmask,'ret_alt'],errors='coerce')/BANK))
        direct.fit(Xtr,np.log1p(pd.to_numeric(tr.ret_alt,errors='coerce').fillna(0)/BANK))
        Xte=te[modelcols].apply(pd.to_numeric,errors='coerce'); valid=Xte.notna().all(axis=1); te=te.loc[valid].copy()
        audit[m]['valid_ticket_rows']=int(len(te)); audit[m]['valid_races']=int(te.race_code.nunique())
        if te.empty: continue
        Xt=te[modelcols].apply(pd.to_numeric,errors='coerce')
        te['_p_hit']=hit.predict_proba(Xt)[:,1]
        te['_cond_pay']=BANK*np.expm1(np.maximum(0,pay.predict(Xt)))
        te['_hurdle_ev']=te._p_hit*te._cond_pay
        te['_direct_ev']=BANK*np.expm1(np.maximum(0,direct.predict(Xt)))
        # Candidate source: hurdle model chooses one exact ticket; independent direct model must choose same config.
        hbest=te.sort_values(['race_code','_hurdle_ev'],ascending=[True,False]).groupby('race_code',as_index=False).head(1).copy()
        dbest=te.sort_values(['race_code','_direct_ev'],ascending=[True,False]).groupby('race_code',as_index=False).head(1)[['race_code','config']].rename(columns={'config':'direct_config'})
        best=hbest.merge(dbest,on='race_code',how='left'); best['_agree']=best.config.eq(best.direct_config)
        # Train-only hurdle score distribution creates outcome-blind coverage gates for each test month.
        ptr=hit.predict_proba(Xtr)[:,1]; cpay=BANK*np.expm1(np.maximum(0,pay.predict(Xtr))); hev=ptr*cpay
        t2=tr[['race_code','config']].copy(); t2['_hev']=hev
        tbest=t2.sort_values(['race_code','_hev'],ascending=[True,False]).groupby('race_code',as_index=False).head(1)
        for frac in FRACTIONS:
            cutoff=float(tbest._hev.quantile(1-frac)); g=best[best._agree & (best._hurdle_ev>=cutoff)].copy(); g['_fraction']=frac; choices.append(g)
        audit[m]['agreement_races']=int(best._agree.sum())
    rows=[]; detail={}
    for frac in FRACTIONS:
        parts=[x for x in choices if len(x) and float(x['_fraction'].iloc[0])==frac]
        g=pd.concat(parts,ignore_index=True) if parts else mat.iloc[0:0].copy()
        a=metric_ticket(g); a['max_drawdown_yen']=maxdd_ticket(g); mo,red,mn=monthly(g)
        b=baseline[['date','race_code','ret','trifecta_hit']].copy(); b['month']=b.date.astype(str).str[:7]; b=b.rename(columns={'ret':'ret_alt','trifecta_hit':'hit_alt'})
        comb=pd.concat([b,g[['date','race_code','month','ret_alt','hit_alt']]],ignore_index=True); cm=metric_ticket(comb); cm['max_drawdown_yen']=maxdd_ticket(comb)
        row={'method':'hurdle_ticket_ev_consensus','fraction':frac,'addon':a,'monthly':mo,'red_months':red,'min_monthly_roi_pct':mn,'combined':cm,'overlap_with_v288':0,'config_counts':g.config.value_counts().to_dict() if len(g) else {}}
        rows.append(row); detail[f'hurdle_ticket_ev_consensus@{frac:.2f}']=g[['date','race_code','month','config','n_alt','comp_alt','hit_alt','ret_alt','_p_hit','_cond_pay','_hurdle_ev','_direct_ev']].to_dict('records') if len(g) else []
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    dec='SHADOW_CANDIDATE_WAVE13' if passers else 'NO_ADOPTION_WAVE13'
    bm=w1.metric(baseline); out={'research_version':'v289-addon-wave13-hurdle-ticket-ev','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_fixed':'v288 94R','candidate':'final v288 NO_BET only','mechanism':'two-part ticket generator: P(hit) x conditional payout with independent direct-value ticket agreement','ticket_family':'Wave2 regenerated Top2..Top10 + target composite odds; exact 10000-yen Dutch','test':'walk-forward Feb-Aug','training':'prior-month final-NO_BET ticket rows only','current_required_missing':'FAIL_CLOSED','july_august':'NON-PRISTINE','september_outcomes_used':False},'baseline':{**bm,'max_drawdown_yen':w1.max_drawdown(baseline)},'candidate_pool':w1.metric(candidates),'methods':rows,'passers':passers,'decision':dec,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on — Wave 13 hurdle ticket EV','', '- v288 **94R fixed**, final NO_BET only','- new candidate generator: P(ticket hit) × conditional payout, with independent direct-value agreement','- exact 10,000-yen Dutch; prior-month-only walk-forward Feb-Aug','- required current feature missing => fail closed','- Jul/Aug NON-PRISTINE; September outcomes unused','', '## Methods','|method|frac|R|hits|hit rate|ROI|profit|min month|red|max DD|overlap|combined R|combined ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mn=x['min_monthly_roi_pct']
        L.append(f'|{x["method"]}|{x["fraction"]:.2f}|{a["races"]}|{a["hits"]}|{a["hit_rate_pct"] if a["hit_rate_pct"] is not None else float("nan"):.2f}%|{a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}%|{a["profit_yen"]:+,.0f}|{mn if mn is not None else float("nan"):.2f}%|{x["red_months"]}|{a["max_drawdown_yen"]:,.0f}|0|{c["races"]}|{c["roi_pct"]:.2f}%|')
    L += ['', '## Decision',f'**{dec}**']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('V289_WAVE13_HURDLE_TICKET_EV_OK')
if __name__=='__main__': main()
