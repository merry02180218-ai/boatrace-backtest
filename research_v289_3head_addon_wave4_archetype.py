#!/usr/bin/env python3
"""v289 Wave 4: venue / field-archetype residual add-on research.

Research-only. Keeps v288 fixed and evaluates only v288 final NO_BET races from
operational PRE S/A + v242-buyable population. Each test month is scored from
prior-month evidence only. September outcomes are forbidden.
"""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave4_archetype.json')
OUT_MD=Path('research_v289_3head_addon_wave4_archetype.md')
BANK=10000
FRACTIONS=(.25,.40)
MIN_LOCAL=30


def metric(df): return w1.metric(df)


def venue_code(s):
    s=str(s).split('.')[0].zfill(12)
    return s[8:10]


def make_archetype(df, med):
    def n(c): return pd.to_numeric(df[c],errors='coerce') if c in df.columns else pd.Series(np.nan,index=df.index)
    st=n('f__c_b3_minus_b4_st')
    motor=n('f__c_b3_minus_b2_motor')
    wall=n('f__c_wall12_weak')
    stretch=n('f__c_attack3_stretch')
    turn=n('f__c_attack3_turn')
    a=(st>=med['st']).astype(int)
    b=(motor>=med['motor']).astype(int)
    c=(wall<=med['wall']).astype(int)
    d=(stretch<=turn).fillna(False).astype(int)
    return 'S'+a.astype(str)+'M'+b.astype(str)+'W'+c.astype(str)+'A'+d.astype(str)


def local_rank(train,test,group_col,allcols,frac,min_local=MIN_LOCAL,roi_gate=None):
    chosen=[]; audit=[]
    for key,te in test.groupby(group_col,dropna=False):
        tr=train[train[group_col]==key].copy()
        if len(tr)<min_local or len(te)==0:
            audit.append({'group':str(key),'train':int(len(tr)),'test':int(len(te)),'status':'insufficient'})
            continue
        if roi_gate is not None:
            roi=100*pd.to_numeric(tr.ret,errors='coerce').fillna(0).sum()/(len(tr)*BANK)
            if roi<roi_gate:
                audit.append({'group':str(key),'train':int(len(tr)),'test':int(len(te)),'status':'roi_gate_fail','train_roi':float(roi)})
                continue
        fs=w1.fit_effect(tr,allcols,'hit',14)
        if len(fs)<3:
            audit.append({'group':str(key),'train':int(len(tr)),'test':int(len(te)),'status':'feature_fail'})
            continue
        trs=w1.signed_z_score(tr,tr,fs); tes=w1.signed_z_score(tr,te,fs)
        thr=float(trs.quantile(1-frac))
        g=te.loc[tes>=thr].copy()
        chosen.append(g)
        audit.append({'group':str(key),'train':int(len(tr)),'test':int(len(te)),'picked':int(len(g)),'status':'ok'})
    return (pd.concat(chosen,ignore_index=True) if chosen else test.iloc[0:0].copy()),audit


def monthly_stats(g):
    out={m:metric(x) for m,x in g.groupby('month')}
    rois=[x['roi_pct'] for x in out.values() if x['roi_pct'] is not None]
    return out,sum(r<100 for r in rois),min(rois) if rois else None


def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September or later rows forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,thresholds=w1.replay_operational_pre(q)
    replay=replay[replay.grade.isin(['S','A'])].copy(); w1.add_v288_route(replay)
    baseline=replay[replay.route!='NO_BET'].copy(); bm=metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01:
        raise RuntimeError(f'baseline drift {bm}')
    candidates=replay[(replay.route=='NO_BET')&(replay.bet==1)].copy()

    raw=q.copy(); w1.add_v288_route(raw,'raw_route')
    raw=raw[(raw.bet==1)&(raw.raw_route=='NO_BET')].copy()
    allcols=w1.safe_live_cols(raw)
    for z in (raw,candidates): z['_venue']=z.race_code.map(venue_code)

    picked={}; audit={}
    for m in sorted(candidates.month.unique()):
        tr=raw[raw.month<m].copy(); te=candidates[candidates.month==m].copy()
        if len(tr)==0 or len(te)==0: continue
        med={
            'st':float(pd.to_numeric(tr.get('f__c_b3_minus_b4_st'),errors='coerce').median()),
            'motor':float(pd.to_numeric(tr.get('f__c_b3_minus_b2_motor'),errors='coerce').median()),
            'wall':float(pd.to_numeric(tr.get('f__c_wall12_weak'),errors='coerce').median()),
        }
        tr['_arch']=make_archetype(tr,med); te['_arch']=make_archetype(te,med)
        tr['_venue_arch']=tr['_venue'].astype(str)+'/'+tr['_arch'].astype(str)
        te['_venue_arch']=te['_venue'].astype(str)+'/'+te['_arch'].astype(str)
        audit[m]={'train_rejects':int(len(tr)),'test_operational_rejects':int(len(te)),'medians':med,'methods':{}}
        for frac in FRACTIONS:
            g,a=local_rank(tr,te,'_venue',allcols,frac,MIN_LOCAL)
            picked.setdefault((f'venue_local',frac),[]).append(g); audit[m]['methods'][f'venue_local@{frac}']=a
            g,a=local_rank(tr,te,'_arch',allcols,frac,MIN_LOCAL)
            picked.setdefault((f'archetype_local',frac),[]).append(g); audit[m]['methods'][f'archetype_local@{frac}']=a
            g,a=local_rank(tr,te,'_venue_arch',allcols,frac,20)
            picked.setdefault((f'venue_archetype',frac),[]).append(g); audit[m]['methods'][f'venue_archetype@{frac}']=a
            g,a=local_rank(tr,te,'_venue',allcols,frac,25,roi_gate=100.0)
            picked.setdefault((f'venue_roi_gate',frac),[]).append(g); audit[m]['methods'][f'venue_roi_gate@{frac}']=a

    rows=[]; detail={}
    for (method,frac),parts in picked.items():
        g=pd.concat(parts,ignore_index=True) if parts else candidates.iloc[0:0].copy()
        if len(g): g=g.drop_duplicates(subset=['date','race_code'])
        gm=metric(g); gm['max_drawdown_yen']=w1.max_drawdown(g)
        monthly,red,minroi=monthly_stats(g)
        combined=pd.concat([baseline,g],ignore_index=True); cm=metric(combined); cm['max_drawdown_yen']=w1.max_drawdown(combined)
        row={'method':method,'fraction':frac,'addon':gm,'monthly':monthly,'red_months':red,'min_monthly_roi_pct':minroi,'combined':cm,'overlap_with_v288':0}
        rows.append(row)
        detail[f'{method}@{frac:.2f}']=[{'date':r.date,'race_code':str(r.race_code),'hit':int(r.trifecta_hit),'ret':float(r.ret)} for r in g.itertuples(index=False)]
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    decision='SHADOW_CANDIDATE_WAVE4' if passers else 'NO_ADOPTION_WAVE4'
    out={'research_version':'v289-addon-wave4-venue-archetype','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_fixed':'v288 operational 94R','population':'operational PRE S/A + v242-buyable + final v288 NO_BET only','not_threshold_relaxation':True,'test_months':'2026-02..2026-08','training':'prior months only','july_august':'NON-PRISTINE','september_outcomes_used':False,'fractions':list(FRACTIONS),'min_local':MIN_LOCAL},'baseline':{**bm,'max_drawdown_yen':w1.max_drawdown(baseline)},'candidate_pool':metric(candidates),'methods':rows,'passers':passers,'decision':decision,'thresholds':thresholds,'audit':audit,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on auto research — Wave 4 venue / field archetype','', '- v288 baseline **94R fixed / unchanged**','- target: operational PRE S/A + v242-buyable + final v288 NO_BET only','- distinct family: venue-local / field-archetype-local / venue×archetype / prior-venue-ROI gate','- every test month uses prior-month evidence only','- July/August NON-PRISTINE; September outcomes not loaded','',f'## Candidate pool\n- {len(candidates)}R','', '## Methods','| method | fraction | add R | hits | ROI | profit | min month ROI | red months | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mr=x['min_monthly_roi_pct']
        L.append(f'| {x["method"]} | {x["fraction"]:.2f} | {a["races"]} | {a["hits"]} | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {x["red_months"]} | {c["races"]} | {c["roi_pct"]:.2f}% |')
    L += ['', '## Decision',f'**{decision}**','', 'Historical passers can only advance to September outcome-blind shadow; v288 production is not replaced.']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L)); print('V289_WAVE4_ARCHETYPE_RESEARCH_OK')

if __name__=='__main__': main()
