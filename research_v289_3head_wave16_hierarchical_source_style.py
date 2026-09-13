#!/usr/bin/env python3
"""Wave16: source-group x attack-style hierarchical models on expanded candidates.

Legacy v288 94R is retained as a floor. Candidate pool includes final-NO_BET races that
were OLD_NO_BET or formerly OLD_PRE_EXCLUDED. Every test month uses prior-month outcomes
only. Jul/Aug are NON-PRISTINE; September outcomes are forbidden. Required current
features fail closed. No legacy-v288 overlap is allowed.
"""
from pathlib import Path
import json, os, math
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_wave16_hierarchical_source_style.json')
OUT_MD=Path('research_v289_3head_wave16_hierarchical_source_style.md')
BANK=10000
FRACTIONS=(0.10,0.15,0.25)
METHODS=('hit','exhibition','return','consensus')


def metric(df):
    m=w1.metric(df); m['max_drawdown_yen']=w1.max_drawdown(df); return m

def monthly(df):
    by={m:w1.metric(g) for m,g in df.groupby('month')}; rs=[x['roi_pct'] for x in by.values() if x['roi_pct'] is not None]
    return by,(min(rs) if rs else None),sum(r<100 for r in rs)

def attack_style(df):
    a=pd.to_numeric(df.get('f__c_attack3_stretch'),errors='coerce')
    b=pd.to_numeric(df.get('f__c_attack3_turn'),errors='coerce')
    out=pd.Series('MISSING',index=df.index,dtype=object)
    ok=a.notna()&b.notna(); out.loc[ok]=np.where(a.loc[ok]<=b.loc[ok],'MAKURI','MAKURISASHI')
    return out

def fail_score(tr,te,features):
    cols=[c for _,_,c in features]
    valid=pd.Series(False,index=te.index)
    s=pd.Series(np.nan,index=te.index,dtype=float)
    if not cols:return s,valid
    valid=te[cols].apply(pd.to_numeric,errors='coerce').notna().all(axis=1)
    if valid.any():s.loc[valid]=w1.signed_z_score(tr,te.loc[valid],features)
    return s,valid

def fit_features(tr,cols,mode,k):
    return w1.fit_effect(tr,cols,'value' if mode=='return' else 'hit',k)

def hierarchical_score(train,test,allcols,livecols,mode):
    score=pd.Series(np.nan,index=test.index,dtype=float); valid=pd.Series(False,index=test.index)
    train=train.copy(); test=test.copy(); train['style']=attack_style(train); test['style']=attack_style(test)
    cols=livecols if mode=='exhibition' else allcols
    for (src,sty),tei in test.groupby(['source_group','style']):
        if sty=='MISSING':continue
        tri=train[(train.source_group==src)&(train['style']==sty)]
        fallback=train[train.source_group==src]
        use=tri if len(tri)>=45 and pd.to_numeric(tri.trifecta_hit,errors='coerce').fillna(0).sum()>=5 else fallback
        if len(use)<45:continue
        fs=fit_features(use,cols,mode,14 if mode!='exhibition' else 10)
        ss,v=fail_score(use,tei,fs)
        score.loc[tei.index]=ss; valid.loc[tei.index]=v
    return score,valid

def train_reference_score(train,allcols,livecols,mode):
    # reference distribution produced with same source/style hierarchy inside prior data only
    out=pd.Series(np.nan,index=train.index,dtype=float)
    tr=train.copy(); tr['style']=attack_style(tr)
    cols=livecols if mode=='exhibition' else allcols
    for (src,sty),idx in tr.groupby(['source_group','style']).groups.items():
        if sty=='MISSING':continue
        cell=tr.loc[idx]; fallback=tr[tr.source_group==src]
        use=cell if len(cell)>=45 and pd.to_numeric(cell.trifecta_hit,errors='coerce').fillna(0).sum()>=5 else fallback
        if len(use)<45:continue
        fs=fit_features(use,cols,mode,14 if mode!='exhibition' else 10)
        if fs:out.loc[idx]=w1.signed_z_score(use,cell,fs)
    return out

def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31':raise RuntimeError('September outcomes forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,_=w1.replay_operational_pre(q); w1.add_v288_route(replay)
    old_pre=replay[replay.grade.isin(['S','A'])].copy(); baseline=old_pre[old_pre.route!='NO_BET'].copy()
    bm=w1.metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01:raise RuntimeError(f'baseline drift {bm}')
    basecodes=set(baseline.race_code.astype(str))
    grades=replay[['race_code','month','grade','_pre_score']].drop_duplicates(['race_code','month'])
    raw=q.copy(); w1.add_v288_route(raw,'raw_route'); raw=raw.merge(grades,on=['race_code','month'],how='inner')
    oldcodes=set(old_pre[(old_pre.bet==1)&(old_pre.route=='NO_BET')].race_code.astype(str))
    elig=raw[(raw.bet==1)&(raw.raw_route=='NO_BET')&(~raw.race_code.astype(str).isin(basecodes))].copy()
    elig['source_group']=np.where(elig.race_code.astype(str).isin(oldcodes),'OLD_NO_BET','OLD_PRE_EXCLUDED')
    elig['style']=attack_style(elig)
    if int((elig.source_group=='OLD_PRE_EXCLUDED').sum())==0:raise RuntimeError('no expanded candidates')
    allcols=w1.safe_live_cols(raw); livecols=w1.current_exhibition_cols(allcols)
    # ensure training rows carry the same source definition without looking at future months
    raw['source_group']=np.where(raw.race_code.astype(str).isin(oldcodes),'OLD_NO_BET','OLD_PRE_EXCLUDED')
    raw['style']=attack_style(raw)
    picked={}; audit={}
    for m in sorted(elig.month.unique()):
        tr=raw[(raw.month<m)&(raw.bet==1)&(raw.raw_route=='NO_BET')&(~raw.race_code.astype(str).isin(basecodes))].copy()
        te=elig[elig.month==m].copy()
        if len(tr)<60 or te.empty:continue
        refs={}; tests={}; valids={}
        for method in ('hit','exhibition','return'):
            refs[method]=train_reference_score(tr,allcols,livecols,method)
            tests[method],valids[method]=hierarchical_score(tr,te,allcols,livecols,method)
        # consensus requires independent valid scores and z-standardizes on prior train refs
        vr=valids['hit']&valids['exhibition']&valids['return']; cons=pd.Series(np.nan,index=te.index,dtype=float)
        ref_valid=refs['hit'].notna()&refs['exhibition'].notna()&refs['return'].notna()
        refc=(w1.standardize_by_train(refs['hit'].dropna(),refs['hit'].loc[ref_valid])+w1.standardize_by_train(refs['exhibition'].dropna(),refs['exhibition'].loc[ref_valid])+w1.standardize_by_train(refs['return'].dropna(),refs['return'].loc[ref_valid]))/3
        if vr.any():
            cons.loc[vr]=(w1.standardize_by_train(refs['hit'].dropna(),tests['hit'].loc[vr])+w1.standardize_by_train(refs['exhibition'].dropna(),tests['exhibition'].loc[vr])+w1.standardize_by_train(refs['return'].dropna(),tests['return'].loc[vr]))/3
        refs['consensus']=refc; tests['consensus']=cons; valids['consensus']=vr
        audit[m]={'train':int(len(tr)),'test':int(len(te)),'old_pre_excluded':int((te.source_group=='OLD_PRE_EXCLUDED').sum())}
        for method in METHODS:
            r=refs[method].dropna()
            if len(r)<30:continue
            for frac in FRACTIONS:
                thr=float(r.quantile(1-frac)); g=te.loc[valids[method]&(tests[method]>=thr)].copy(); picked.setdefault((method,frac),[]).append(g)
    rows=[]; detail={}
    for (method,frac),parts in picked.items():
        g=pd.concat(parts,ignore_index=True).drop_duplicates('race_code') if parts else elig.iloc[0:0].copy()
        a=metric(g); by,mn,red=monthly(g); overlap=len(set(g.race_code.astype(str))&basecodes); comb=metric(pd.concat([baseline,g],ignore_index=True))
        sg={k:metric(v) for k,v in g.groupby('source_group')}; sty={k:metric(v) for k,v in g.groupby('style')}
        row={'method':method,'fraction':frac,'addon':a,'monthly':by,'min_monthly_roi_pct':mn,'red_months':red,'overlap_with_v288':overlap,'source_metrics':sg,'style_metrics':sty,'old_pre_excluded_selected':int((g.source_group=='OLD_PRE_EXCLUDED').sum()) if len(g) else 0,'combined':comb}
        rows.append(row); detail[f'{method}@{frac:.2f}']=g[['date','race_code','month','source_group','style','trifecta_hit','ret']].to_dict('records') if len(g) else []
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['combined']['races']>=94 and x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3 and x['overlap_with_v288']==0]
    decision='SHADOW_CANDIDATE_WAVE16' if passers else 'NO_ADOPTION_WAVE16'
    out={'research_version':'wave16-hierarchical-source-style','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_policy':'legacy v288 94R floor','candidate':'expanded final-NO_BET including OLD_PRE_EXCLUDED','model':'source-group x attack-style hierarchy with source fallback','test':'prior-month-only Feb-Aug walk-forward','july_august':'NON-PRISTINE','september_outcomes_used':False,'current_required_missing':'FAIL_CLOSED','stake_per_race_yen':BANK},'baseline':metric(baseline),'expanded_pool':{'races':int(len(elig)),'old_no_bet':int((elig.source_group=='OLD_NO_BET').sum()),'old_pre_excluded':int((elig.source_group=='OLD_PRE_EXCLUDED').sum())},'methods':rows,'passers':passers,'decision':decision,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# 3号艇 Wave16 — hierarchical source x attack-style','',f"Expanded pool: {len(elig)}R / PRE-excluded {int((elig.source_group=='OLD_PRE_EXCLUDED').sum())}R",'- legacy 94R floor preserved; prior-month-only; Jul/Aug NON-PRISTINE; September outcomes unused','', '## Methods','|method|frac|add R|PRE-excl|hits|hit rate|ROI|profit|min month|red|max DD|combined R|combined ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; L.append(f"|{x['method']}|{x['fraction']:.2f}|{a['races']}|{x['old_pre_excluded_selected']}|{a['hits']}|{a['hit_rate_pct'] if a['hit_rate_pct'] is not None else float('nan'):.2f}%|{a['roi_pct'] if a['roi_pct'] is not None else float('nan'):.2f}%|{a['profit_yen']:+,.0f}|{x['min_monthly_roi_pct'] if x['min_monthly_roi_pct'] is not None else float('nan'):.2f}%|{x['red_months']}|{a['max_drawdown_yen']:,.0f}|{c['races']}|{c['roi_pct']:.2f}%|")
    L += ['', '## Decision',f'**{decision}**']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('WAVE16_HIERARCHICAL_OK')

if __name__=='__main__':main()
