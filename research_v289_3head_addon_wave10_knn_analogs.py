#!/usr/bin/env python3
"""v289 Wave10: nonparametric nearest-neighbour analog research on final v288 NO_BET.
Distinct from linear effect/logistic families. Prior-month only; September forbidden.
"""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.neighbors import KNeighborsRegressor
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave10_knn_analogs.json')
OUT_MD=Path('research_v289_3head_addon_wave10_knn_analogs.md')
KS=(25,50,75)
FRACTIONS=(.15,.25,.40)
BANK=10000
TOPK=24

def select_features(tr, cols):
    y=pd.to_numeric(tr.y3,errors='coerce').fillna(0).astype(int); rows=[]
    for c in cols:
        x=pd.to_numeric(tr[c],errors='coerce'); ok=x.notna()
        if ok.sum()<50: continue
        a=x[(y==1)&ok]; b=x[(y==0)&ok]; sd=x[ok].std()
        if len(a)>=8 and len(b)>=25 and np.isfinite(sd) and sd>1e-12:
            e=(a.mean()-b.mean())/sd
            if np.isfinite(e): rows.append((abs(e),c))
    return [c for _,c in sorted(rows,reverse=True)[:TOPK]]

def monthly_stats(g):
    out={m:w1.metric(x) for m,x in g.groupby('month')}
    rois=[x['roi_pct'] for x in out.values() if x['roi_pct'] is not None]
    return out,sum(r<100 for r in rois),min(rois) if rois else None

def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September or later rows forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,thresholds=w1.replay_operational_pre(q); replay=replay[replay.grade.isin(['S','A'])].copy(); w1.add_v288_route(replay)
    baseline=replay[replay.route!='NO_BET'].copy(); bm=w1.metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01: raise RuntimeError(f'baseline drift {bm}')
    cand=replay[(replay.route=='NO_BET')&(replay.bet==1)].copy()
    raw=q[q.bet==1].copy(); w1.add_v288_route(raw,'raw_route')
    cols=[c for c in w1.safe_live_cols(raw) if c!='p3']
    picked={}; audit={}
    for m in sorted(cand.month.unique()):
        tr=raw[raw.month<m].copy(); te=cand[cand.month==m].copy(); trrej=tr[tr.raw_route=='NO_BET'].copy()
        fs=select_features(tr,cols); audit[m]={'train_all':len(tr),'train_rejects':len(trrej),'test':len(te),'features':fs}
        if len(fs)<5 or len(trrej)<30: continue
        Xtr=tr[fs].apply(pd.to_numeric,errors='coerce'); Xrej=trrej[fs].apply(pd.to_numeric,errors='coerce'); Xte=te[fs].apply(pd.to_numeric,errors='coerce')
        valid=Xte.notna().all(axis=1); audit[m]['valid_current']=int(valid.sum())
        if not valid.any(): continue
        for k in KS:
            kk=min(k,max(5,len(tr)-1))
            pipe=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),KNeighborsRegressor(n_neighbors=kk,weights='distance',p=2))
            # head-win analog score
            pipe.fit(Xtr,pd.to_numeric(tr.y3,errors='coerce').fillna(0).astype(float))
            sre=pd.Series(pipe.predict(Xrej),index=trrej.index); ste=pd.Series(np.nan,index=te.index); ste.loc[valid]=pipe.predict(Xte.loc[valid])
            # payout-value analog score, log-scaled
            pipev=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),KNeighborsRegressor(n_neighbors=kk,weights='distance',p=2))
            yv=np.log1p(pd.to_numeric(tr.ret,errors='coerce').fillna(0)/BANK)
            pipev.fit(Xtr,yv); vre=pd.Series(pipev.predict(Xrej),index=trrej.index); vte=pd.Series(np.nan,index=te.index); vte.loc[valid]=pipev.predict(Xte.loc[valid])
            for frac in FRACTIONS:
                th=float(sre.quantile(1-frac)); idx=te.index[ste>=th]; picked.setdefault((f'knn_head_k{k}',frac),[]).append(te.loc[idx].copy())
                thv=float(vre.quantile(1-frac)); idx=te.index[vte>=thv]; picked.setdefault((f'knn_value_k{k}',frac),[]).append(te.loc[idx].copy())
                # independent consensus: both above their own quantile
                idx=te.index[(ste>=th)&(vte>=thv)]; picked.setdefault((f'knn_consensus_k{k}',frac),[]).append(te.loc[idx].copy())
    rows=[]; detail={}
    for (method,frac),parts in picked.items():
        g=pd.concat(parts,ignore_index=True) if parts else cand.iloc[0:0].copy(); a=w1.metric(g); a['max_drawdown_yen']=w1.max_drawdown(g)
        monthly,red,minroi=monthly_stats(g); comb=pd.concat([baseline,g],ignore_index=True); c=w1.metric(comb); c['max_drawdown_yen']=w1.max_drawdown(comb)
        rows.append({'method':method,'fraction':frac,'addon':a,'monthly':monthly,'red_months':red,'min_monthly_roi_pct':minroi,'combined':c,'overlap_with_v288':0})
        detail[f'{method}@{frac:.2f}']=[{'date':r.date,'race_code':str(r.race_code),'hit':int(r.trifecta_hit),'ret':float(r.ret)} for r in g.itertuples(index=False)]
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    decision='SHADOW_CANDIDATE_WAVE10' if passers else 'NO_ADOPTION_WAVE10'
    out={'research_version':'v289-addon-wave10-knn-analogs','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_fixed':'v288 operational 94R','candidate_universe':'final v288 NO_BET only','model':'nonparametric prior-month KNN analogs','existing_p3_used':False,'selected_feature_missing_current':'FAIL_CLOSED','july_august':'NON-PRISTINE','september_outcomes_used':False,'walk_forward':'Feb-Aug'},'baseline':{**bm,'max_drawdown_yen':w1.max_drawdown(baseline)},'candidate_pool':w1.metric(cand),'methods':rows,'passers':passers,'decision':decision,'audit':audit,'detail':detail,'thresholds':thresholds}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on auto research — Wave 10 KNN analogs','', '- v288 baseline **94R fixed / unchanged**','- final v288 NO_BET only','- nonparametric nearest-neighbour analog models; existing p3 excluded','- current selected feature missing => fail closed','- walk-forward Feb-Aug; Jul/Aug NON-PRISTINE; September outcomes unused','', '## Methods','| method | frac | add R | hits | hit rate | ROI | profit | min month ROI | red | max DD | overlap | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mr=x['min_monthly_roi_pct']
        L.append(f'| {x["method"]} | {x["fraction"]:.2f} | {a["races"]} | {a["hits"]} | {a["hit_rate_pct"] if a["hit_rate_pct"] is not None else float("nan"):.2f}% | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {x["red_months"]} | {a["max_drawdown_yen"]:,.0f} | 0 | {c["races"]} | {c["roi_pct"]:.2f}% |')
    L += ['', '## Decision',f'**{decision}**','', 'Only robust passers may advance to September outcome-blind shadow; v288 production remains unchanged.']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('V289_WAVE10_KNN_OK')

if __name__=='__main__': main()
