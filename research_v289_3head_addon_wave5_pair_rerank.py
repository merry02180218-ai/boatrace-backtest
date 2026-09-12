#!/usr/bin/env python3
"""v289 Wave 5: true opponent / trifecta-order re-ranking on v288 final NO_BETs.

Distinct from Wave 2: this changes the 2nd/3rd-place ticket ordering itself.
For each test month, a residual pair classifier is trained only on prior-month
v288-reject races in which boat 3 actually won. V221 pair features and current
pre-race odds are used; September outcomes are forbidden. Research-only.
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

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave5_pair_rerank.json')
OUT_MD=Path('research_v289_3head_addon_wave5_pair_rerank.md')
BANK=10000
MIN_POSITIVE_RACES=8
VARIANTS=('residual_target3','blend_target3','ev_target3','residual_top10','blend_top10','ev_top10')


def metric(df):
    n=len(df); ret=float(pd.to_numeric(df.ret_alt,errors='coerce').fillna(0).sum()) if n else 0.; hits=int(pd.to_numeric(df.hit_alt,errors='coerce').fillna(0).sum()) if n else 0
    stake=n*BANK
    return {'races':int(n),'hits':hits,'hit_rate_pct':100*hits/n if n else None,'stake_yen':stake,'payout_yen':ret,'profit_yen':ret-stake,'roi_pct':100*ret/stake if stake else None}


def maxdd(df):
    if len(df)==0:return 0.
    z=df.sort_values(['date','race_code']); pnl=pd.to_numeric(z.ret_alt,errors='coerce').fillna(0)-BANK
    c=pnl.cumsum().to_numpy(float); p=np.maximum.accumulate(np.r_[0.,c]); return float((p[1:]-c).max()) if len(c) else 0.


def base_universe():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31':raise RuntimeError('September or later rows forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,_=w1.replay_operational_pre(q); replay=replay[replay.grade.isin(['S','A'])].copy(); w1.add_v288_route(replay)
    baseline=replay[replay.route!='NO_BET'].copy(); bm=w1.metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.)>.01:raise RuntimeError(f'baseline drift {bm}')
    candidates=replay[(replay.route=='NO_BET')&(replay.bet==1)].copy()
    raw=q.copy(); w1.add_v288_route(raw,'raw_route'); raw=raw[(raw.bet==1)&(raw.raw_route=='NO_BET')].copy()
    return q,baseline,candidates,raw


def zrace(x):
    a=np.asarray(x,float); sd=float(np.std(a))
    return np.zeros_like(a) if not np.isfinite(sd) or sd<1e-12 else (a-float(np.mean(a)))/sd


def settle_top10(ts,od,actual):
    vals=v243.v242.odds_for(ts,od,10)
    if vals is None:return None
    stakes=np.asarray(v243.v242.v234.v205.round_dutch(vals,BANK),int)
    if stakes.sum()!=BANK:return None
    hit=0; ret=0.
    if actual in ts[:10]:
        j=ts[:10].index(actual)
        if stakes[j]>0:hit=1; ret=float(stakes[j])*float(vals[j])
    return {'hit':hit,'ret':ret,'n':10,'comp':float(v243.v242.comp(vals))}


def settle_target3(ts,od,actual):
    s=v243.v242.settle(ts,od,actual)
    if not s or s.get('action')!='bet':return None
    return {'hit':int(s['hit']),'ret':float(s['ret']),'n':int(s['top_n']),'comp':float(s['comp_odds'])}


def ticket_rows(r,base_pair,od=None):
    rows=[]
    for s in v243.v242.v234.v222.OPP:
        for t in v243.v242.v234.v222.OPP:
            if s==t:continue
            try:vec=np.asarray(v243.v242.v234.v222.pairvec(r,s,t,'V221'),float)
            except Exception:return None
            if not np.isfinite(vec).all():return None
            try:bp=float(base_pair.predict_proba(np.asarray([vec],float))[0,1])
            except Exception:return None
            ticket=f'3-{int(s)}-{int(t)}'; odd=np.nan
            if od is not None:
                try:odd=float(od[ticket])
                except Exception:odd=np.nan
            rows.append((ticket,vec,bp,odd))
    return rows


def fit_residual(train_codes,dmap,base_pair):
    X=[]; y=[]; positive_races=0; used_races=0
    for code in train_codes:
        r=dmap.get(str(code).zfill(12))
        if r is None:continue
        act=v243.v242.v234.v222.v166.combo(r.get('actual_combo'))
        if len(act)!=3 or int(act[0])!=3:continue
        tr=ticket_rows(r,base_pair,None)
        if tr is None:continue
        positive_races+=1; used_races+=1
        pos=f'3-{int(act[1])}-{int(act[2])}'
        for ticket,vec,bp,_ in tr:
            X.append(np.r_[vec,bp]); y.append(1 if ticket==pos else 0)
    if positive_races<MIN_POSITIVE_RACES or sum(y)<MIN_POSITIVE_RACES:return None,positive_races,used_races
    clf=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,class_weight='balanced',C=1.0,random_state=0))
    clf.fit(np.asarray(X,float),np.asarray(y,int))
    return clf,positive_races,used_races


def order_variants(r,base_pair,clf,od):
    tr=ticket_rows(r,base_pair,od)
    if tr is None:return None
    tickets=[x[0] for x in tr]; X=np.asarray([np.r_[x[1],x[2]] for x in tr],float); base=np.asarray([x[2] for x in tr],float); odds=np.asarray([x[3] for x in tr],float)
    if not np.isfinite(odds).all() or (odds<=0).any():return None
    res=clf.predict_proba(X)[:,1]
    blend=zrace(base)+zrace(res)
    ev=res*odds
    def order(score):return [tickets[i] for i in np.argsort(-np.asarray(score,float),kind='mergesort')]
    return {'residual':order(res),'blend':order(blend),'ev':order(ev)}


def monthly(g):
    by={m:metric(x) for m,x in g.groupby('month')}; rois=[x['roi_pct'] for x in by.values() if x['roi_pct'] is not None]
    return by,sum(r<100 for r in rois),min(rois) if rois else None


def main():
    q,baseline,candidates,raw=base_universe()
    cov=v243.v242.v234.reconstruct(); common=v243.v242.v234.validate_parser()
    if (cov.source=='missing').any():raise RuntimeError('missing Waku10; no imputation')
    d,_,_,_=v243.v242.v234.build_restored(); d=d.copy(); d['_code']=d.race_code.astype(str).str.split('.').str[0].str.zfill(12)
    dmap={str(r._code):r for _,r in d.iterrows()}
    odds=v243.v242.v234.v205.load_odds(); odds['race_code']=odds.race_code.astype(str).str.split('.').str[0].str.zfill(12); oi=odds.set_index('race_code',drop=False)
    cbm={m:g.copy() for m,g in candidates.groupby('month')}
    parts={v:[] for v in VARIANTS}; audit={}
    for m in sorted(cbm):
        first=pd.Timestamp(m+'-01'); base_pair=v243.v242.v234.v222.fit_pair(d[d._date<first],'V221')
        train_codes=list(raw[raw.month<m].race_code.astype(str).str.zfill(12))
        clf,pos,used=fit_residual(train_codes,dmap,base_pair)
        audit[m]={'train_reject_codes':len(train_codes),'pair_positive_races':int(pos),'pair_used_races':int(used),'test_candidates':int(len(cbm[m])),'model_available':bool(clf is not None)}
        if clf is None:continue
        for _,cr in cbm[m].iterrows():
            code=str(cr.race_code).zfill(12); r=dmap.get(code)
            if r is None or code not in oi.index:continue
            od=oi.loc[code]; od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            act=v243.v242.v234.v222.v166.combo(r.get('actual_combo')); actual='-'.join(map(str,act)) if len(act)==3 else ''
            if not actual:continue
            ovs=order_variants(r,base_pair,clf,od)
            if ovs is None:continue
            for key,ts in ovs.items():
                for mode in ('target3','top10'):
                    s=settle_target3(ts,od,actual) if mode=='target3' else settle_top10(ts,od,actual)
                    if s is None:continue
                    parts[f'{key}_{mode}'].append({'month':m,'date':str(cr.date),'race_code':code,'hit_alt':s['hit'],'ret_alt':s['ret'],'n_alt':s['n'],'comp_alt':s['comp']})
    rows=[]; detail={}
    for v in VARIANTS:
        g=pd.DataFrame(parts[v],columns=['month','date','race_code','hit_alt','ret_alt','n_alt','comp_alt'])
        a=metric(g); a['max_drawdown_yen']=maxdd(g); by,red,minroi=monthly(g)
        b=baseline[['date','race_code','ret','trifecta_hit']].copy().rename(columns={'ret':'ret_alt','trifecta_hit':'hit_alt'}); b['month']=b.date.astype(str).str[:7]
        comb=pd.concat([b[['month','date','race_code','hit_alt','ret_alt']],g[['month','date','race_code','hit_alt','ret_alt']]],ignore_index=True); cm=metric(comb); cm['max_drawdown_yen']=maxdd(comb)
        row={'method':v,'addon':a,'monthly':by,'red_months':red,'min_monthly_roi_pct':minroi,'combined':cm,'overlap_with_v288':0}
        rows.append(row); detail[v]=g.to_dict('records')
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    decision='SHADOW_CANDIDATE_WAVE5' if passers else 'NO_ADOPTION_WAVE5'
    bm=w1.metric(baseline); bm['max_drawdown_yen']=w1.max_drawdown(baseline)
    out={'research_version':'v289-addon-wave5-true-pair-rerank','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'waku10_validated_races':int(common),'rules':{'baseline_fixed':'v288 operational 94R','candidate_universe':'operational PRE S/A + original v242-buyable + final v288 NO_BET','test_months':'2026-02..2026-08','training':'prior-month reject races only; ticket model conditional on historical boat-3 wins','july_august':'NON-PRISTINE','september_outcomes_used':False,'not_threshold_relaxation':True,'changes_opponent_order':True,'min_positive_train_races':MIN_POSITIVE_RACES,'variants':list(VARIANTS)},'baseline':bm,'candidate_pool':w1.metric(candidates),'methods':rows,'passers':passers,'decision':decision,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on auto research — Wave 5 true opponent re-ranking','', '- v288 baseline **94R fixed / unchanged**','- target: operational PRE S/A + v242-buyable + final v288 NO_BET only','- unlike Wave 2, this retrains the 2着/3着 ordered-pair ranking itself from prior-month reject races','- variants: residual pair probability / V221+residual blend / ticket-level residual probability×pre-race odds EV; each with target3 or Top10 Dutch','- July/August NON-PRISTINE; September outcomes not loaded','', '## Methods','| method | add R | hits | ROI | profit | min month ROI | red months | max DD | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mr=x['min_monthly_roi_pct']
        L.append(f'| {x["method"]} | {a["races"]} | {a["hits"]} | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {x["red_months"]} | {a["max_drawdown_yen"]:,.0f} | {c["races"]} | {c["roi_pct"]:.2f}% |')
    L += ['', '## Decision',f'**{decision}**','', 'Historical passers can advance only to September outcome-blind shadow; v288 production is not replaced.']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('V289_WAVE5_PAIR_RERANK_OK')

if __name__=='__main__':main()
