#!/usr/bin/env python3
"""v289 Wave 6: separate 2nd-place / 3rd-place role models for v288 final NO_BETs.

Structurally distinct from Wave 5's ordered-pair classifier. For each test month,
fit two opponent-role classifiers only on prior-month reject races where boat 3 won:
one model estimates each opponent's probability of finishing 2nd, another of finishing
3rd. Ticket scores combine the independently estimated role probabilities. September
outcomes are forbidden. Research-only; v288 baseline remains fixed.
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

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave6_role_split.json')
OUT_MD=Path('research_v289_3head_addon_wave6_role_split.md')
BANK=10000
MIN_POSITIVE_RACES=8
VARIANTS=('role_product_target3','role_ev_target3','role_product_top10','role_ev_top10')
OPP=tuple(v243.v242.v234.v222.OPP)


def role_vec(r, boat, role):
    vecs=[]
    if role=='second':
        for t in OPP:
            if int(t)==int(boat): continue
            try: v=np.asarray(v243.v242.v234.v222.pairvec(r,boat,t,'V221'),float)
            except Exception: return None
            if not np.isfinite(v).all(): return None
            vecs.append(v)
    else:
        for s in OPP:
            if int(s)==int(boat): continue
            try: v=np.asarray(v243.v242.v234.v222.pairvec(r,s,boat,'V221'),float)
            except Exception: return None
            if not np.isfinite(v).all(): return None
            vecs.append(v)
    if not vecs:return None
    a=np.asarray(vecs,float)
    return np.r_[a.mean(axis=0),a.max(axis=0),a.min(axis=0)]


def fit_roles(train_codes,dmap):
    X2=[]; y2=[]; X3=[]; y3=[]; positive=0
    for code in train_codes:
        r=dmap.get(str(code).zfill(12))
        if r is None:continue
        act=v243.v242.v234.v222.v166.combo(r.get('actual_combo'))
        if len(act)!=3 or int(act[0])!=3:continue
        positive+=1
        for b in OPP:
            v2=role_vec(r,b,'second'); v3=role_vec(r,b,'third')
            if v2 is None or v3 is None:continue
            X2.append(v2); y2.append(1 if int(b)==int(act[1]) else 0)
            X3.append(v3); y3.append(1 if int(b)==int(act[2]) else 0)
    if positive<MIN_POSITIVE_RACES or sum(y2)<MIN_POSITIVE_RACES or sum(y3)<MIN_POSITIVE_RACES:return None,None,positive
    def fit(X,y):
        clf=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,class_weight='balanced',C=1.0,random_state=0))
        clf.fit(np.asarray(X,float),np.asarray(y,int)); return clf
    return fit(X2,y2),fit(X3,y3),positive


def order_variants(r,m2,m3,od):
    p2={}; p3={}
    for b in OPP:
        v2=role_vec(r,b,'second'); v3=role_vec(r,b,'third')
        if v2 is None or v3 is None:return None
        p2[int(b)]=float(m2.predict_proba([v2])[0,1]); p3[int(b)]=float(m3.predict_proba([v3])[0,1])
    rows=[]
    for s in OPP:
        for t in OPP:
            if int(s)==int(t):continue
            ticket=f'3-{int(s)}-{int(t)}'
            try:odd=float(od[ticket])
            except Exception:return None
            if not np.isfinite(odd) or odd<=0:return None
            prob=p2[int(s)]*p3[int(t)]
            rows.append((ticket,prob,prob*odd))
    return {
        'role_product':[x[0] for x in sorted(rows,key=lambda x:(-x[1],x[0]))],
        'role_ev':[x[0] for x in sorted(rows,key=lambda x:(-x[2],x[0]))],
    }


def monthly(g):
    by={m:w5.metric(x) for m,x in g.groupby('month')}; rois=[x['roi_pct'] for x in by.values() if x['roi_pct'] is not None]
    return by,sum(r<100 for r in rois),min(rois) if rois else None


def main():
    q,baseline,candidates,raw=w5.base_universe()
    cov=v243.v242.v234.reconstruct(); common=v243.v242.v234.validate_parser()
    if (cov.source=='missing').any():raise RuntimeError('missing Waku10; no imputation')
    d,_,_,_=v243.v242.v234.build_restored(); d=d.copy(); d['_code']=d.race_code.astype(str).str.split('.').str[0].str.zfill(12)
    dmap={str(r._code):r for _,r in d.iterrows()}
    odds=v243.v242.v234.v205.load_odds(); odds['race_code']=odds.race_code.astype(str).str.split('.').str[0].str.zfill(12); oi=odds.set_index('race_code',drop=False)
    cbm={m:g.copy() for m,g in candidates.groupby('month')}; parts={v:[] for v in VARIANTS}; audit={}
    for m in sorted(cbm):
        train_codes=list(raw[raw.month<m].race_code.astype(str).str.zfill(12))
        m2,m3,pos=fit_roles(train_codes,dmap)
        audit[m]={'train_reject_codes':len(train_codes),'boat3_win_train_races':int(pos),'test_candidates':int(len(cbm[m])),'model_available':bool(m2 is not None and m3 is not None)}
        if m2 is None or m3 is None:continue
        for _,cr in cbm[m].iterrows():
            code=str(cr.race_code).zfill(12); r=dmap.get(code)
            if r is None or code not in oi.index:continue
            od=oi.loc[code]; od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            act=v243.v242.v234.v222.v166.combo(r.get('actual_combo')); actual='-'.join(map(str,act)) if len(act)==3 else ''
            if not actual:continue
            ovs=order_variants(r,m2,m3,od)
            if ovs is None:continue
            for key,ts in ovs.items():
                for mode in ('target3','top10'):
                    s=w5.settle_target3(ts,od,actual) if mode=='target3' else w5.settle_top10(ts,od,actual)
                    if s is None:continue
                    parts[f'{key}_{mode}'].append({'month':m,'date':str(cr.date),'race_code':code,'hit_alt':s['hit'],'ret_alt':s['ret'],'n_alt':s['n'],'comp_alt':s['comp']})
    rows=[]; detail={}
    for v in VARIANTS:
        g=pd.DataFrame(parts[v],columns=['month','date','race_code','hit_alt','ret_alt','n_alt','comp_alt'])
        a=w5.metric(g); a['max_drawdown_yen']=w5.maxdd(g); by,red,minroi=monthly(g)
        b=baseline[['date','race_code','ret','trifecta_hit']].copy().rename(columns={'ret':'ret_alt','trifecta_hit':'hit_alt'}); b['month']=b.date.astype(str).str[:7]
        comb=pd.concat([b[['month','date','race_code','hit_alt','ret_alt']],g[['month','date','race_code','hit_alt','ret_alt']]],ignore_index=True); cm=w5.metric(comb); cm['max_drawdown_yen']=w5.maxdd(comb)
        rows.append({'method':v,'addon':a,'monthly':by,'red_months':red,'min_monthly_roi_pct':minroi,'combined':cm,'overlap_with_v288':0}); detail[v]=g.to_dict('records')
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    decision='SHADOW_CANDIDATE_WAVE6' if passers else 'NO_ADOPTION_WAVE6'
    bm=w1.metric(baseline); bm['max_drawdown_yen']=w1.max_drawdown(baseline)
    out={'research_version':'v289-addon-wave6-role-split','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'waku10_validated_races':int(common),'rules':{'baseline_fixed':'v288 operational 94R','candidate_universe':'operational PRE S/A + original v242-buyable + final v288 NO_BET','test_months':'2026-02..2026-08','training':'prior-month reject races only; separate 2nd and 3rd role models conditional on historical boat-3 wins','july_august':'NON-PRISTINE','september_outcomes_used':False,'not_threshold_relaxation':True,'separate_second_third_models':True,'min_positive_train_races':MIN_POSITIVE_RACES,'variants':list(VARIANTS)},'baseline':bm,'candidate_pool':w1.metric(candidates),'methods':rows,'passers':passers,'decision':decision,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on auto research — Wave 6 separate 2nd/3rd role models','', '- v288 baseline **94R fixed / unchanged**','- target: operational PRE S/A + v242-buyable + final v288 NO_BET only','- structurally distinct from Wave 5: trains separate 2着 and 3着 opponent-role classifiers','- ticket order: role probability product or role-probability×pre-race-odds EV; target3 / Top10 Dutch','- July/August NON-PRISTINE; September outcomes not loaded','', '## Methods','| method | add R | hits | ROI | profit | min month ROI | red months | max DD | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mr=x['min_monthly_roi_pct']
        L.append(f'| {x["method"]} | {a["races"]} | {a["hits"]} | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {x["red_months"]} | {a["max_drawdown_yen"]:,.0f} | {c["races"]} | {c["roi_pct"]:.2f}% |')
    L += ['', '## Decision',f'**{decision}**','', 'Historical passers can advance only to September outcome-blind shadow; v288 production is not replaced.']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('V289_WAVE6_ROLE_SPLIT_OK')

if __name__=='__main__':main()
