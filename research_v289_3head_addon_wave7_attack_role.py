#!/usr/bin/env python3
"""v289 Wave 7: attack-style-conditioned 2nd/3rd role models.

For each walk-forward test month, final-v288-NO_BET candidates are split by a
pre-race attack-style signal (stretch vs turn). Separate 2nd/3rd opponent-role
models are fitted only from prior-month reject races in the same regime where
boat 3 actually won. Missing regime/model => fail closed. September outcomes
are forbidden; v288 production stays fixed.
"""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import research_v289_3head_addon as w1
import analyze_v243_3head_expand_feature_audit as v243
import research_v289_3head_addon_wave5_pair_rerank as w5
import research_v289_3head_addon_wave6_role_split as w6

OUT_JSON=Path('research_v289_3head_addon_wave7_attack_role.json')
OUT_MD=Path('research_v289_3head_addon_wave7_attack_role.md')
MIN_POSITIVE_RACES=5
VARIANTS=('attack_role_product_target3','attack_role_ev_target3','attack_role_product_top10','attack_role_ev_top10')
OPP=tuple(v243.v242.v234.v222.OPP)


def regime(row):
    a=pd.to_numeric(pd.Series([row.get('f__c_attack3_stretch',np.nan)]),errors='coerce').iloc[0]
    b=pd.to_numeric(pd.Series([row.get('f__c_attack3_turn',np.nan)]),errors='coerce').iloc[0]
    if not np.isfinite(a) or not np.isfinite(b): return None
    return 'stretch' if a>=b else 'turn'


def fit_roles(train_codes,dmap):
    X2=[]; y2=[]; X3=[]; y3=[]; positive=0
    for code in train_codes:
        r=dmap.get(str(code).zfill(12))
        if r is None: continue
        act=v243.v242.v234.v222.v166.combo(r.get('actual_combo'))
        if len(act)!=3 or int(act[0])!=3: continue
        positive+=1
        for boat in OPP:
            v2=w6.role_vec(r,boat,'second'); v3=w6.role_vec(r,boat,'third')
            if v2 is None or v3 is None: continue
            X2.append(v2); y2.append(1 if int(boat)==int(act[1]) else 0)
            X3.append(v3); y3.append(1 if int(boat)==int(act[2]) else 0)
    if positive<MIN_POSITIVE_RACES or sum(y2)<MIN_POSITIVE_RACES or sum(y3)<MIN_POSITIVE_RACES:
        return None,None,positive
    def fit(X,y):
        m=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,class_weight='balanced',C=1.0,random_state=0))
        m.fit(np.asarray(X,float),np.asarray(y,int)); return m
    return fit(X2,y2),fit(X3,y3),positive


def monthly(g):
    by={m:w5.metric(x) for m,x in g.groupby('month')}; rois=[x['roi_pct'] for x in by.values() if x['roi_pct'] is not None]
    return by,sum(r<100 for r in rois),min(rois) if rois else None


def main():
    q,baseline,candidates,raw=w5.base_universe()
    if q.date.max()>'2026-08-31': raise RuntimeError('September or later rows forbidden')
    cov=v243.v242.v234.reconstruct(); common=v243.v242.v234.validate_parser()
    if (cov.source=='missing').any(): raise RuntimeError('missing Waku10; no imputation')
    d,_,_,_=v243.v242.v234.build_restored(); d=d.copy(); d['_code']=d.race_code.astype(str).str.split('.').str[0].str.zfill(12)
    dmap={str(r._code):r for _,r in d.iterrows()}
    odds=v243.v242.v234.v205.load_odds(); odds['race_code']=odds.race_code.astype(str).str.split('.').str[0].str.zfill(12); oi=odds.set_index('race_code',drop=False)
    raw=raw.copy(); candidates=candidates.copy(); raw['_regime']=raw.apply(regime,axis=1); candidates['_regime']=candidates.apply(regime,axis=1)
    parts={v:[] for v in VARIANTS}; audit={}
    for m in sorted(candidates.month.unique()):
        audit[m]={}
        for rg in ('stretch','turn'):
            tr=raw[(raw.month<m)&(raw._regime==rg)]
            m2,m3,pos=fit_roles(list(tr.race_code.astype(str).str.zfill(12)),dmap)
            te=candidates[(candidates.month==m)&(candidates._regime==rg)]
            audit[m][rg]={'train_reject_codes':int(len(tr)),'boat3_win_train_races':int(pos),'test_candidates':int(len(te)),'model_available':bool(m2 is not None and m3 is not None)}
            if m2 is None or m3 is None: continue
            for _,cr in te.iterrows():
                code=str(cr.race_code).zfill(12); r=dmap.get(code)
                if r is None or code not in oi.index: continue
                od=oi.loc[code]; od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
                act=v243.v242.v234.v222.v166.combo(r.get('actual_combo')); actual='-'.join(map(str,act)) if len(act)==3 else ''
                if not actual: continue
                ovs=w6.order_variants(r,m2,m3,od)
                if ovs is None: continue
                for key,ts in ovs.items():
                    for mode in ('target3','top10'):
                        s=w5.settle_target3(ts,od,actual) if mode=='target3' else w5.settle_top10(ts,od,actual)
                        if s is None: continue
                        name=f'attack_{key}_{mode}'
                        parts[name].append({'month':m,'date':str(cr.date),'race_code':code,'regime':rg,'hit_alt':s['hit'],'ret_alt':s['ret'],'n_alt':s['n'],'comp_alt':s['comp']})
    rows=[]; detail={}
    for v in VARIANTS:
        g=pd.DataFrame(parts[v],columns=['month','date','race_code','regime','hit_alt','ret_alt','n_alt','comp_alt'])
        a=w5.metric(g); a['max_drawdown_yen']=w5.maxdd(g); by,red,minroi=monthly(g)
        b=baseline[['date','race_code','ret','trifecta_hit']].copy().rename(columns={'ret':'ret_alt','trifecta_hit':'hit_alt'}); b['month']=b.date.astype(str).str[:7]
        comb=pd.concat([b[['month','date','race_code','hit_alt','ret_alt']],g[['month','date','race_code','hit_alt','ret_alt']]],ignore_index=True); cm=w5.metric(comb); cm['max_drawdown_yen']=w5.maxdd(comb)
        overlap=len(set(g.race_code.astype(str)) & set(baseline.race_code.astype(str)))
        rows.append({'method':v,'addon':a,'monthly':by,'red_months':red,'min_monthly_roi_pct':minroi,'combined':cm,'overlap_with_v288':int(overlap)}); detail[v]=g.to_dict('records')
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    if any(x['overlap_with_v288'] for x in rows): raise RuntimeError('v288 overlap detected')
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    decision='SHADOW_CANDIDATE_WAVE7' if passers else 'NO_ADOPTION_WAVE7'
    bm=w1.metric(baseline); bm['max_drawdown_yen']=w1.max_drawdown(baseline)
    out={'research_version':'v289-addon-wave7-attack-style-role','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'waku10_validated_races':int(common),'rules':{'baseline_fixed':'v288 operational 94R','candidate_universe':'operational PRE S/A + original v242-buyable + final v288 NO_BET','test_months':'2026-02..2026-08','training':'prior-month reject races only, same pre-race attack regime, separate 2nd/3rd role models','regime':'stretch if f__c_attack3_stretch >= f__c_attack3_turn else turn; missing => fail closed','july_august':'NON-PRISTINE','september_outcomes_used':False,'not_threshold_relaxation':True,'min_positive_train_races':MIN_POSITIVE_RACES,'variants':list(VARIANTS)},'baseline':bm,'candidate_pool':w1.metric(candidates),'methods':rows,'passers':passers,'decision':decision,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on auto research — Wave 7 attack-style-conditioned role models','', '- v288 baseline **94R fixed / unchanged**','- target: final v288 NO_BET only','- pre-race attack regime: stretch vs turn; separate 2着/3着 role models within each regime','- missing regime/model => fail closed','- July/August NON-PRISTINE; September outcomes not loaded','', '## Methods','| method | add R | hits | hit rate | ROI | profit | min month ROI | red months | max DD | overlap | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mr=x['min_monthly_roi_pct']
        L.append(f'| {x["method"]} | {a["races"]} | {a["hits"]} | {a["hit_rate_pct"] if a["hit_rate_pct"] is not None else float("nan"):.2f}% | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {x["red_months"]} | {a["max_drawdown_yen"]:,.0f} | {x["overlap_with_v288"]} | {c["races"]} | {c["roi_pct"]:.2f}% |')
    L += ['', '## Decision',f'**{decision}**','', 'Only robust historical passers may advance to September outcome-blind shadow; v288 production is never replaced directly.']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('V289_WAVE7_ATTACK_ROLE_OK')

if __name__=='__main__': main()
