#!/usr/bin/env python3
"""v289 Wave 3: independent PRE-B live rescue add-on.

This does NOT loosen v288 S/A thresholds. It creates a separate population/route:
operational PRE grade B + existing v242-buyable ticket structure, then uses only
prior-month PRE-B outcomes to rank current-month PRE-B races.
September is never loaded. Research-only; any shadow promotion must fail closed.
"""
from pathlib import Path
import json, math, os
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave3_preb.json')
OUT_MD=Path('research_v289_3head_addon_wave3_preb.md')
BANK=10000
FRACTIONS=(.20,.35,.50)


def metric(df):
    return w1.metric(df)


def score_effect(tr,te,cols,mode='hit',topk=14):
    fs=w1.fit_effect(tr,cols,'hit' if mode=='hit' else 'value',topk)
    if len(fs)<3:
        return pd.Series(np.nan,index=te.index), pd.Series(np.nan,index=tr.index), len(fs)
    return w1.signed_z_score(tr,te,fs), w1.signed_z_score(tr,tr,fs), len(fs)


def monthly_stats(g):
    out={m:metric(x) for m,x in g.groupby('month')}
    rois=[x['roi_pct'] for x in out.values() if x['roi_pct'] is not None]
    return out, sum(r<100 for r in rois), min(rois) if rois else None


def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September or later rows forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,thresholds=w1.replay_operational_pre(q)

    # Fixed v288 baseline remains operational PRE S/A only.
    sa=replay[replay.grade.isin(['S','A'])].copy(); w1.add_v288_route(sa)
    baseline=sa[sa.route!='NO_BET'].copy(); bm=metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01:
        raise RuntimeError(f'baseline drift {bm}')

    # Independent population: PRE-B only; no baseline overlap possible by construction.
    pool=replay[(replay.grade=='B')&(replay.bet==1)].copy()
    allcols=w1.safe_live_cols(pool)
    livecols=w1.current_exhibition_cols(allcols)
    ticketcols=[c for c in ('p3','raw_top_n','comp_odds','f__c_attack3_stretch','f__c_attack3_turn','f__c_wall12_weak','f__c_b3_minus_b4_st','f__c_b3_minus_b4_waku_st','f__c_b3_minus_b2_motor','f__c_b3_inside_nst') if c in pool.columns]

    picked={}; audit={}
    months=sorted(pool.month.unique())
    for m in months:
        tr=pool[pool.month<m].copy(); te=pool[pool.month==m].copy()
        audit[m]={'train_preb':int(len(tr)),'test_preb':int(len(te))}
        # Require enough prior PRE-B evidence; otherwise fail closed for that month.
        if len(tr)<18 or len(te)==0: continue

        te_hit,tr_hit,n_hit=score_effect(tr,te,allcols,'hit',16)
        te_live,tr_live,n_live=score_effect(tr,te,livecols,'hit',12)
        te_ret,tr_ret,n_ret=score_effect(tr,te,allcols,'value',16)
        te_ticket,tr_ticket,n_ticket=score_effect(tr,te,ticketcols,'hit',10)
        audit[m].update({'hit_features':n_hit,'live_features':n_live,'return_features':n_ret,'ticket_features':n_ticket})

        methods={}
        if te_hit.notna().any(): methods['preb_hit_rank']=(tr_hit,te_hit)
        if te_live.notna().any(): methods['preb_exhibition_rank']=(tr_live,te_live)
        if te_ret.notna().any(): methods['preb_return_rank']=(tr_ret,te_ret)
        if te_ticket.notna().any(): methods['preb_ticket_quality']=(tr_ticket,te_ticket)
        if te_hit.notna().any() and te_live.notna().any() and te_ret.notna().any():
            tr_cons=(w1.standardize_by_train(tr_hit,tr_hit)+w1.standardize_by_train(tr_live,tr_live)+w1.standardize_by_train(tr_ret,tr_ret))/3
            te_cons=(w1.standardize_by_train(tr_hit,te_hit)+w1.standardize_by_train(tr_live,te_live)+w1.standardize_by_train(tr_ret,te_ret))/3
            methods['preb_consensus']=(tr_cons,te_cons)

        for method,(trs,tes) in methods.items():
            for frac in FRACTIONS:
                thr=float(trs.dropna().quantile(1-frac))
                idx=te.index[tes>=thr]
                picked.setdefault((method,frac),[]).append(te.loc[idx].copy())

        # EV family: prior-trained hit score + current pre-race composite odds; alpha chosen on prior PRE-B only.
        if te_hit.notna().any():
            for frac in FRACTIONS:
                alpha=w1.choose_ev_alpha(tr,tr_hit.fillna(tr_hit.median()),frac)
                trodds=np.log(pd.to_numeric(tr.comp_odds,errors='coerce').clip(lower=.05))
                teodds=np.log(pd.to_numeric(te.comp_odds,errors='coerce').clip(lower=.05))
                tr_ev=w1.standardize_by_train(tr_hit,tr_hit)+alpha*trodds.fillna(trodds.median())
                te_ev=w1.standardize_by_train(tr_hit,te_hit)+alpha*teodds.fillna(trodds.median())
                thr=float(tr_ev.dropna().quantile(1-frac)); idx=te.index[te_ev>=thr]
                picked.setdefault(('preb_ev',frac),[]).append(te.loc[idx].copy())

    rows=[]; detail={}
    for (method,frac),parts in picked.items():
        g=pd.concat(parts,ignore_index=True) if parts else pool.iloc[0:0].copy()
        gm=metric(g); gm['max_drawdown_yen']=w1.max_drawdown(g)
        monthly,red,minroi=monthly_stats(g)
        combined=pd.concat([baseline,g],ignore_index=True); cm=metric(combined); cm['max_drawdown_yen']=w1.max_drawdown(combined)
        row={'method':method,'fraction':frac,'addon':gm,'monthly':monthly,'red_months':red,'min_monthly_roi_pct':minroi,'combined':cm,'overlap_with_v288':0}
        rows.append(row)
        detail[f'{method}@{frac:.2f}']=[{'date':r.date,'race_code':str(r.race_code),'hit':int(r.trifecta_hit),'ret':float(r.ret)} for r in g.itertuples(index=False)]
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60]
    decision='SHADOW_CANDIDATE_WAVE3' if passers else 'NO_ADOPTION_WAVE3'
    out={'research_version':'v289-addon-wave3-preb-independent-route','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_fixed':'v288 operational 94R','population':'operational PRE grade B + existing v242 buyable only','not_threshold_relaxation':True,'test_months':'2026-02..2026-08','training':'prior operational PRE-B months only','july_august':'NON-PRISTINE','september_outcomes_used':False,'required_prior_preb_rows':18,'fractions':list(FRACTIONS)},'baseline':{**bm,'max_drawdown_yen':w1.max_drawdown(baseline)},'preb_pool':metric(pool),'methods':rows,'passers':passers,'decision':decision,'thresholds':thresholds,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on auto research — Wave 3 independent PRE-B rescue','', '- v288 baseline **94R fixed / unchanged**','- separate population: operational PRE grade B + v242-buyable only','- this is not a relaxation of the v288 S/A route; PRE-B is modeled independently from prior PRE-B outcomes','- test: Feb-Aug; each month uses prior operational PRE-B months only','- July/August NON-PRISTINE; September outcomes not loaded','',f'## PRE-B pool\n- {len(pool)}R / {int(pool.trifecta_hit.sum())} hits / raw ROI {100*pool.ret.fillna(0).sum()/(len(pool)*BANK) if len(pool) else float("nan"):.2f}%','', '## Methods','| method | fraction | add R | hits | ROI | profit | min month ROI | red months | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mr=x['min_monthly_roi_pct']
        L.append(f'| {x["method"]} | {x["fraction"]:.2f} | {a["races"]} | {a["hits"]} | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {x["red_months"]} | {c["races"]} | {c["roi_pct"]:.2f}% |')
    L += ['', '## Decision',f'**{decision}**','', 'Any historical passer advances only to September outcome-blind shadow; it does not replace v288.']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L)); print('V289_WAVE3_PREB_RESEARCH_OK')

if __name__=='__main__': main()
