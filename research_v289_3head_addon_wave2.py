#!/usr/bin/env python3
"""v289 add-on Wave 2: ticket-structure research on canonical v288 final NO_BETs.
Research-only; source ends 2026-08-31 and September outcomes are never loaded.
"""
from pathlib import Path
import json, math, os
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1
import analyze_v243_3head_expand_feature_audit as v243

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave2.json')
OUT_MD=Path('research_v289_3head_addon_wave2.md')
BANK=10000
FIXED_NS=tuple(range(2,11))
TARGETS=(2.5,3.0,3.5,4.0,5.0,6.0,8.0)

def metrics(df,ret_col='ret_alt',hit_col='hit_alt'):
    n=int(len(df)); payout=float(pd.to_numeric(df[ret_col],errors='coerce').fillna(0).sum()) if n else 0.0
    hits=int(pd.to_numeric(df[hit_col],errors='coerce').fillna(0).sum()) if n else 0; stake=n*BANK
    return {'races':n,'hits':hits,'hit_rate_pct':100*hits/n if n else None,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None}

def max_dd(df,ret_col='ret_alt'):
    if len(df)==0:return 0.0
    z=df.sort_values(['date','race_code']); pnl=pd.to_numeric(z[ret_col],errors='coerce').fillna(0)-BANK
    curve=pnl.cumsum().to_numpy(float); peaks=np.maximum.accumulate(np.r_[0.0,curve]); dd=peaks[1:]-curve
    return float(dd.max()) if len(dd) else 0.0

def settle_n(ts,od,actual,n):
    vals=v243.v242.odds_for(ts,od,int(n))
    if vals is None:return None
    c=v243.v242.comp(vals); stakes=np.asarray(v243.v242.v234.v205.round_dutch(vals,BANK),int)
    if int(stakes.sum())!=BANK:return None
    hit=0; ret=0.0
    if actual in ts[:n]:
        j=ts[:n].index(actual)
        if stakes[j]>0: hit=1; ret=float(stakes[j])*float(vals[j])
    return {'n':int(n),'comp':float(c),'hit':int(hit),'ret':float(ret)}

def base_universe():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31':raise RuntimeError('September or later rows forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,_=w1.replay_operational_pre(q); replay=replay[replay.grade.isin(['S','A'])].copy(); w1.add_v288_route(replay)
    baseline=replay[replay.route!='NO_BET'].copy(); bm=w1.metric(baseline)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070.0)>.01:raise RuntimeError(f'baseline drift {bm}')
    candidates=replay[(replay.route=='NO_BET')&(replay.bet==1)].copy(); raw=q.copy(); w1.add_v288_route(raw,'raw_route')
    return q,baseline,candidates,raw

def regenerate(qcodes):
    cov=v243.v242.v234.reconstruct(); common=v243.v242.v234.validate_parser()
    if (cov.source=='missing').any():raise RuntimeError('missing Waku10; no imputation')
    d,_,vc,basefs=v243.v242.v234.build_restored(); fs=v243.v242.v234.full_features(d,basefs); fs=[x for x in fs if x in d.columns]
    odds=v243.v242.v234.v205.load_odds(); oi=odds.set_index('race_code',drop=False); wanted=set(str(x).zfill(12) for x in qcodes); rec=[]
    for mon in v243.v242.v234.MONTHS:
        first=pd.Timestamp(mon+'-01'); nextm=first+pd.offsets.MonthBegin(1); tr=d[d._date<first]
        pair=v243.v242.v234.v222.fit_pair(tr,'V221'); base_te,_=v243.v242.v234.v223.fit_head(d,list(basefs),vc,first,nextm)
        k=max(1,int((base_te._p>=.30).sum())); te,_=v243.v242.v234.v223.fit_head(d,fs,vc,first,nextm); sel=te.nlargest(k,'_p').copy()
        for _,r in sel.iterrows():
            code=str(r.get('race_code','')).zfill(12)
            if code not in wanted or code not in oi.index:continue
            if v243.v242.v234.v223.ii(r.get('valid_result'))!=1 or v243.v242.v234.v223.ii(r.get('course3'),3)!=3:continue
            act=v243.v242.v234.v222.v166.combo(r.get('actual_combo')); actual='-'.join(map(str,act)) if len(act)==3 else ''
            if not actual:continue
            ts,_=v243.scored_order(r,pair)
            if ts is None:continue
            od=oi.loc[code]; od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            base={'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code}
            for n in FIXED_NS:
                s=settle_n(ts,od,actual,n)
                if s:rec.append({**base,'config':f'top{n}','n_alt':s['n'],'comp_alt':s['comp'],'hit_alt':s['hit'],'ret_alt':s['ret']})
            for target in TARGETS:
                choices=[]
                for n in FIXED_NS:
                    vals=v243.v242.odds_for(ts,od,n)
                    if vals is not None:choices.append((abs(v243.v242.comp(vals)-target),n))
                if choices:
                    choices.sort(key=lambda x:(x[0],x[1])); s=settle_n(ts,od,actual,choices[0][1])
                    if s:rec.append({**base,'config':f'target{target:g}','n_alt':s['n'],'comp_alt':s['comp'],'hit_alt':s['hit'],'ret_alt':s['ret']})
    out=pd.DataFrame(rec)
    if len(out)==0:raise RuntimeError('no ticket matrix rows regenerated')
    return out,int(common)

def summarize_configs(mat,codes):
    z=mat[mat.race_code.astype(str).isin(set(str(x) for x in codes))]; rows=[]
    for cfg,g in z.groupby('config'):
        m=metrics(g); m['config']=cfg; by={mm:metrics(x) for mm,x in g.groupby('month')}; rois=[v['roi_pct'] for v in by.values() if v['roi_pct'] is not None]
        m['red_months']=sum(v<100 for v in rois); m['min_monthly_roi_pct']=min(rois) if rois else None; m['monthly']=by; m['max_drawdown_yen']=max_dd(g); rows.append(m)
    return rows

def pick_config(train,mode):
    scored=[]
    for cfg,g in train.groupby('config'):
        if len(g)<12:continue
        m=metrics(g); roi=(m['roi_pct'] or 0)/100; mons=[((metrics(x)['roi_pct'] or 0)/100,mm) for mm,x in g.groupby('month')]; red=sum(r<1 for r,_ in mons)
        if mode=='wf_profit':
            if len(g)<20 or roi<1.05:continue
            score=(roi-1)*math.sqrt(len(g))-0.10*red/max(1,len(mons))
        elif mode=='wf_stable':
            if len(g)<20 or roi<1 or red>len(mons)//2:continue
            score=(roi-1)*math.sqrt(len(g))+0.35*(min(r for r,_ in mons)-1)
        else:
            last=sorted(set(g.month))[-2:]; r=g[g.month.isin(last)]; rroi=((metrics(r)['roi_pct'] or 0)/100)
            if len(r)<10 or rroi<1.05:continue
            score=(rroi-1)*math.sqrt(len(r))
        scored.append((score,roi,cfg,m))
    return max(scored,key=lambda x:(x[0],x[1],x[2]),default=None)

def walkforward(mat,raw,candidates,baseline):
    cbm={m:set(g.race_code.astype(str)) for m,g in candidates.groupby('month')}; trainpool=raw[(raw.bet==1)&(raw.raw_route=='NO_BET')]; out=[]; detail={}
    for mode in ('wf_profit','wf_stable','wf_recent'):
        picks=[]; choices={}
        for m in sorted(cbm):
            codes=set(trainpool[trainpool.month<m].race_code.astype(str)); tr=mat[mat.race_code.astype(str).isin(codes)]; ch=pick_config(tr,mode)
            choices[m]=None if ch is None else {'config':ch[2],'train_roi_pct':100*ch[1],'train_races':ch[3]['races']}
            if ch:
                te=mat[(mat.month==m)&(mat.config==ch[2])&(mat.race_code.astype(str).isin(cbm[m]))]; picks.append(te)
        g=pd.concat(picks,ignore_index=True) if picks else mat.iloc[0:0].copy(); a=metrics(g); a['max_drawdown_yen']=max_dd(g)
        monthly={m:metrics(x) for m,x in g.groupby('month')}; rois=[v['roi_pct'] for v in monthly.values() if v['roi_pct'] is not None]; a['red_months']=sum(v<100 for v in rois); a['min_monthly_roi_pct']=min(rois) if rois else None
        b=baseline[['date','race_code','ret']].rename(columns={'ret':'ret_alt'}).copy(); b['hit_alt']=baseline.trifecta_hit.values; comb=pd.concat([b,g[['date','race_code','ret_alt','hit_alt']]],ignore_index=True); cm=metrics(comb); cm['max_drawdown_yen']=max_dd(comb)
        out.append({'method':mode,'addon':a,'monthly':monthly,'choices':choices,'combined':cm,'overlap_with_v288':0}); detail[mode]=g[['date','race_code','month','config','n_alt','comp_alt','hit_alt','ret_alt']].to_dict('records')
    return out,detail

def main():
    q,baseline,candidates,raw=base_universe(); mat,common=regenerate(q.race_code.astype(str)); cand=set(candidates.race_code.astype(str)); fixed=summarize_configs(mat,cand)
    for x in fixed:
        g=mat[(mat.config==x['config'])&(mat.race_code.astype(str).isin(cand))]; b=baseline[['date','race_code','ret']].rename(columns={'ret':'ret_alt'}).copy(); b['hit_alt']=baseline.trifecta_hit.values; comb=pd.concat([b,g[['date','race_code','ret_alt','hit_alt']]],ignore_index=True); x['combined']=metrics(comb); x['combined']['max_drawdown_yen']=max_dd(comb); x['overlap_with_v288']=0
    fixed.sort(key=lambda x:((x['roi_pct'] or -1),x['races']),reverse=True); wf,detail=walkforward(mat,raw,candidates,baseline)
    passers=[('fixed',x['config'],x['roi_pct'],x['races']) for x in fixed if x['races']>=20 and (x['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60]
    passers += [('walkforward',x['method'],x['addon']['roi_pct'],x['addon']['races']) for x in wf if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['addon']['min_monthly_roi_pct'] or 0)>=60]
    decision='SHADOW_CANDIDATE_WAVE2' if passers else 'NO_ADOPTION_WAVE2'; bm=w1.metric(baseline); bm['max_drawdown_yen']=w1.max_drawdown(baseline)
    out={'research_version':'v289-addon-wave2-ticket-structure','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'waku10_validated_races':common,'rules':{'baseline_fixed':'v288 operational 94R','candidate_universe':'operational PRE S/A + original v242-buyable + final v288 NO_BET','test_months':'2026-02..2026-08','july_august':'NON-PRISTINE','september_outcomes_used':False,'ticket_family':'frozen monthly V221 order + pre-race odds + exact 10,000-yen Dutch','fixed_topn':list(FIXED_NS),'target_composite_odds':list(TARGETS)},'baseline':bm,'candidate_pool_original':w1.metric(candidates),'ticket_matrix_rows':int(len(mat)),'fixed_ticket_policies':fixed,'walkforward_ticket_selectors':wf,'passers':passers,'decision':decision,'detail':detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# v289 3号艇 add-on auto research — Wave 2 ticket structure','', '- v288 baseline: **94R fixed; production unchanged**','- candidate: operational PRE S/A + original v242-buyable + final v288 NO_BET only','- ticket order: frozen monthly V221; odds are historical pre-race odds; settlement is exact 10,000-yen Dutch','- test: 2026-02..2026-08; July/August NON-PRISTINE; September outcomes not loaded','',f'## Baseline\n- {bm["races"]}R / {bm["hits"]} hits / ROI {bm["roi_pct"]:.3f}% / profit {bm["profit_yen"]:+,.0f} yen','', '## Fixed ticket structures','| config | add R | hits | ROI | profit | min month ROI | red months | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in fixed:
        c=x['combined']; lines.append(f'| {x["config"]} | {x["races"]} | {x["hits"]} | {x["roi_pct"]:.2f}% | {x["profit_yen"]:+,.0f} | {x["min_monthly_roi_pct"]:.2f}% | {x["red_months"]} | {c["races"]} | {c["roi_pct"]:.2f}% |')
    lines += ['', '## Prior-month-selected ticket structures','| selector | add R | hits | ROI | profit | min month ROI | red months | combined R | combined ROI |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in wf:
        a=x['addon']; c=x['combined']; mr=a['min_monthly_roi_pct']; lines.append(f'| {x["method"]} | {a["races"]} | {a["hits"]} | {a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}% | {a["profit_yen"]:+,.0f} | {mr if mr is not None else float("nan"):.2f}% | {a["red_months"]} | {c["races"]} | {c["roi_pct"]:.2f}% |')
    lines += ['', '## Decision',f'**{decision}**','', 'Wave 2 changes the ticket family rather than loosening v288 thresholds. Historical results remain model-selection evidence only.']
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines)); print('V289_WAVE2_TICKET_RESEARCH_OK')
if __name__=='__main__':main()
