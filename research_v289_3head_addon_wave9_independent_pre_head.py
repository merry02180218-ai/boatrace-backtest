#!/usr/bin/env python3
"""v289 Wave 9: independent PRE head-probability candidate generator.

Distinct from Wave1 residual ranking: fit a fresh boat-3 win classifier on all prior-month
buyable races, then apply it only to operational v288 final NO_BET candidates.
All model inputs are pre-deadline columns from the frozen v243 audit artifact.
Current-row missingness on any selected model feature fails closed. September is forbidden.
"""
from pathlib import Path
import json, math, os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave9_independent_pre_head.json')
OUT_MD=Path('research_v289_3head_addon_wave9_independent_pre_head.md')
BANK=10000
FRACTIONS=(.15,.25,.40)
ALPHAS=(0.0,.25,.50,1.0)
TOPK=30


def feature_rank(tr, cols):
    y=pd.to_numeric(tr['y3'],errors='coerce').fillna(0).astype(int)
    rows=[]
    for c in cols:
        x=pd.to_numeric(tr[c],errors='coerce'); ok=x.notna()
        if ok.sum()<40: continue
        a=x[(y==1)&ok]; b=x[(y==0)&ok]; sd=x[ok].std()
        if len(a)>=8 and len(b)>=25 and np.isfinite(sd) and sd>1e-12:
            e=(a.mean()-b.mean())/sd
            if np.isfinite(e): rows.append((abs(e),c))
    return [c for _,c in sorted(rows,reverse=True)[:TOPK]]


def fit_predict(tr, te, fs):
    if len(fs)<5 or tr['y3'].nunique()<2: return None,None
    X=tr[fs].apply(pd.to_numeric,errors='coerce'); y=pd.to_numeric(tr.y3,errors='coerce').fillna(0).astype(int)
    pipe=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.35,max_iter=2000,class_weight='balanced',solver='liblinear'))
    pipe.fit(X,y)
    ptr=pd.Series(pipe.predict_proba(X)[:,1],index=tr.index)
    # fail closed on every required current feature
    Xte=te[fs].apply(pd.to_numeric,errors='coerce'); valid=Xte.notna().all(axis=1)
    pte=pd.Series(np.nan,index=te.index,dtype=float)
    if valid.any(): pte.loc[valid]=pipe.predict_proba(Xte.loc[valid])[:,1]
    return ptr,pte


def monthly_stats(g):
    out={m:w1.metric(x) for m,x in g.groupby('month')}
    rois=[x['roi_pct'] for x in out.values() if x['roi_pct'] is not None]
    return out,sum(r<100 for r in rois),min(rois) if rois else None


def choose_alpha(trrej, p, frac):
    odds=np.log(pd.to_numeric(trrej.comp_odds,errors='coerce').clip(lower=.05))
    logit=np.log(np.clip(p,1e-6,1-1e-6)/np.clip(1-p,1e-6,1-1e-6))
    best=None
    for a in ALPHAS:
        s=logit+a*odds.fillna(odds.median())
        thr=float(s.quantile(1-frac)); g=trrej.loc[s>=thr]
        if len(g)<15: continue
        m=w1.metric(g); roi=m['roi_pct'] or 0
        score=(roi-100)*math.sqrt(len(g)/20)
        row=(score,roi,a)
        if best is None or row>best: best=row
    return best[2] if best else 0.0


def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September or later rows forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,thresholds=w1.replay_operational_pre(q); replay=replay[replay.grade.isin(['S','A'])].copy(); w1.add_v288_route(replay)
    baseline=replay[replay.route!='NO_BET'].copy(); bm=w1.metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01: raise RuntimeError(f'baseline drift {bm}')
    candidates=replay[(replay.route=='NO_BET')&(replay.bet==1)].copy()
    raw=q[q.bet==1].copy(); w1.add_v288_route(raw,'raw_route')
    # exclude ticket/settlement/result fields; y3 is target only, never a feature
    cols=w1.safe_live_cols(raw)
    cols=[c for c in cols if c not in ('p3',)]  # independent from existing p3 head score
    picked={}; audit={}
    for m in sorted(candidates.month.unique()):
        tr=raw[raw.month<m].copy(); te=candidates[candidates.month==m].copy(); trrej=tr[tr.raw_route=='NO_BET'].copy()
        fs=feature_rank(tr,cols)
        ptr,pte=fit_predict(tr,te,fs)
        audit[m]={'train_all_buyable':int(len(tr)),'train_rejects':int(len(trrej)),'test_candidates':int(len(te)),'features':fs,'valid_current_rows':int(pte.notna().sum()) if pte is not None else 0}
        if ptr is None or pte is None or len(trrej)<20: continue
        # score prior rejects using same model; safe because their outcomes are prior-month only
        ptrrej=ptr.loc[trrej.index]
        for frac in FRACTIONS:
            thr=float(ptrrej.quantile(1-frac)); idx=te.index[pte>=thr]
            picked.setdefault((f'head_prob',frac),[]).append(te.loc[idx].copy())
            a=choose_alpha(trrej,ptrrej,frac)
            trlog=np.log(np.clip(ptrrej,1e-6,1-1e-6)/np.clip(1-ptrrej,1e-6,1-1e-6))
            telog=np.log(np.clip(pte,1e-6,1-1e-6)/np.clip(1-pte,1e-6,1-1e-6))
            trodds=np.log(pd.to_numeric(trrej.comp_odds,errors='coerce').clip(lower=.05)); teodds=np.log(pd.to_numeric(te.comp_odds,errors='coerce').clip(lower=.05))
            trs=trlog+a*trodds.fillna(trodds.median()); tes=telog+a*teodds.fillna(trodds.median())
            evthr=float(trs.quantile(1-frac)); idx=te.index[tes>=evthr]
            picked.setdefault((f'head_ev',frac),[]).append(te.loc[idx].copy())
    rows=[]; detail={}
    for (method,frac),parts in picked.items():
        g=pd.concat(parts,ignore_index=True) if parts else candidates.iloc[0:0].copy(); a=w1.metric(g); a['max_drawdown_yen']=w1.max_drawdown(g)
        monthly,red,minroi=monthly_stats(g); comb=pd.concat([baseline,g],ignore_index=True); c=w1.metric(comb); c['max_drawdown_yen']=w1.max_drawdown(comb)
        rows.append({'method':method,'fraction':frac,'addon':a,'monthly':monthly,'red_months':red,'min_monthly_roi_pct':minroi,'combined':c,'overlap_with_v288':0})
        detail[f'{method}@{frac:.2f}']=[{'date':r.date,'race_code':str(r.race_code),'hit':int(r.trifecta_hit),'ret':float(r.ret)} for r in g.itertuples(index=False)]
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    decision='SHADOW_CANDIDATE_WAVE9' if passers else 'NO_ADOPTION_WAVE9'
    out={'research_version':'v289-addon-wave9-independent-pre-head','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_fixed':'v288 operational 94R','candidate_universe':'operational PRE S/A + v242 buyable + final v288 NO_BET only','training_population':'all prior-month v242-buyable races','target':'boat3 actual win y3, prior months only','independent_from_existing_p3':True,'selected_feature_missing_current':'FAIL_CLOSED','july_august':'NON-PRISTINE','september_outcomes_used':False,'test':'walk-forward Feb-Aug'},'baseline':{**bm,'max_drawdown_yen':w1.max_drawdown(baseline)},'candidate_pool':w1.metric(candidates),'methods':rows,'passers':passers,'decision':decision,'audit':audit,'detail':detail,'thresholds':thresholds}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on auto research — Wave 9 independent PRE head model','', '- v288 baseline **94R fixed / unchanged**','- target only final v288 NO_BET','- fresh boat3-win classifier trained on all prior-month buyable races; existing p3 excluded','- selected current feature missing => fail closed','- walk-forward Feb-Aug; July/August NON-PRISTINE; September outcomes not loaded','', '## Methods','| method | frac | add R | hits | hit rate | ROI | profit | min month ROI | red months | max DD | overlap | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mr=x['min_monthly_roi_pct']
        L.append(f'| {x["method"]} | {x["fraction"]:.2f} | {a["races"]} | {a["hits"]} | {a["hit_rate_pct"] if a["hit_rate_pct"] is not None else float("nan"):.2f}% | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {x["red_months"]} | {a["max_drawdown_yen"]:,.0f} | 0 | {c["races"]} | {c["roi_pct"]:.2f}% |')
    L += ['', '## Decision',f'**{decision}**','', 'Only robust historical passers may advance to September outcome-blind shadow; production v288 remains unchanged.']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('V289_WAVE9_INDEPENDENT_PRE_HEAD_OK')

if __name__=='__main__': main()
