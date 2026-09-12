#!/usr/bin/env python3
"""Wave11: v288 reject-cause mixture-of-experts for final NO_BET add-ons."""
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT_JSON=Path('research_v289_3head_addon_wave11_reject_cause_moe.json')
OUT_MD=Path('research_v289_3head_addon_wave11_reject_cause_moe.md')
FRACTIONS=(.20,.35,.50); BANK=10000

def n(df,c): return pd.to_numeric(df[c],errors='coerce')

def cause(df):
    final=w1.v243_target(df)
    s1=n(df,'f__c_b3_minus_b4_waku_st')<=w1.WAKU34
    s2=n(df,'f__c_b3_minus_b4_st')>=w1.ST34
    s3=n(df,'f__c_b3_meetst')<=w1.MEETST
    a1=n(df,'f__c_b3_minus_b4_st')>=w1.A_ST34
    a2=n(df,'f__c_wall12_weak')<=w1.A_WALL
    b1=n(df,'f__c_b3_minus_b2_motor')>=w1.B_MOTOR
    b2=n(df,'f__c_b3_inside_nst')<=w1.B_NST
    ss=final.astype(int)+s1.fillna(False).astype(int)+s2.fillna(False).astype(int)+s3.fillna(False).astype(int)
    aa=a1.fillna(False).astype(int)+a2.fillna(False).astype(int)
    bb=b1.fillna(False).astype(int)+b2.fillna(False).astype(int)
    # nearest failed route; tie preference S>A>B. If required fields missing, UNKNOWN => fail closed.
    required=pd.concat([s1,s2,s3,a1,a2,b1,b2],axis=1).notna().all(axis=1)
    out=pd.Series('UNKNOWN',index=df.index,dtype=object)
    for i in df.index[required]:
        vals=[(int(ss.loc[i]),'NEAR_S'),(int(aa.loc[i]),'NEAR_A'),(int(bb.loc[i]),'NEAR_B')]
        out.loc[i]=max(vals,key=lambda x:(x[0], {'NEAR_S':3,'NEAR_A':2,'NEAR_B':1}[x[1]]))[1]
    return out

def monthstats(g):
    d={m:w1.metric(x) for m,x in g.groupby('month')}; r=[x['roi_pct'] for x in d.values() if x['roi_pct'] is not None]
    return d,sum(x<100 for x in r),min(r) if r else None

def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    if q.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    q['_target']=w1.v243_target(q).astype(int)
    replay,thr=w1.replay_operational_pre(q); replay=replay[replay.grade.isin(['S','A'])].copy(); w1.add_v288_route(replay)
    base=replay[replay.route!='NO_BET'].copy(); bm=w1.metric(base)
    if bm['races']!=94 or bm['hits']!=52 or abs(bm['payout_yen']-1622070)>.01: raise RuntimeError(f'baseline drift {bm}')
    cand=replay[(replay.route=='NO_BET')&(replay.bet==1)].copy(); cand['cause']=cause(cand)
    raw=q[q.bet==1].copy(); w1.add_v288_route(raw,'raw_route'); raw['cause']=cause(raw)
    cols=w1.safe_live_cols(raw); live=w1.current_exhibition_cols(cols)
    picks={}; audit={}
    for m in sorted(cand.month.unique()):
        trall=raw[(raw.month<m)&(raw.raw_route=='NO_BET')].copy(); teall=cand[cand.month==m].copy(); audit[m]={}
        for c in ('NEAR_S','NEAR_A','NEAR_B'):
            tr=trall[trall.cause==c].copy(); te=teall[teall.cause==c].copy(); audit[m][c]={'train':len(tr),'test':len(te)}
            if len(tr)<30 or len(te)==0: continue
            hitfs=w1.fit_effect(tr,cols,'hit',14); retfs=w1.fit_effect(tr,cols,'value',14); exfs=w1.fit_effect(tr,live,'hit',10)
            if min(len(hitfs),len(retfs))<3: continue
            shtr=w1.signed_z_score(tr,tr,hitfs); shte=w1.signed_z_score(tr,te,hitfs)
            srtr=w1.signed_z_score(tr,tr,retfs); srte=w1.signed_z_score(tr,te,retfs)
            setr=w1.signed_z_score(tr,tr,exfs) if len(exfs)>=3 else pd.Series(0.,index=tr.index)
            sete=w1.signed_z_score(tr,te,exfs) if len(exfs)>=3 else pd.Series(0.,index=te.index)
            ctr=(w1.standardize_by_train(shtr,shtr)+w1.standardize_by_train(srtr,srtr)+w1.standardize_by_train(setr,setr))/3
            cte=(w1.standardize_by_train(shtr,shte)+w1.standardize_by_train(srtr,srte)+w1.standardize_by_train(setr,sete))/3
            for f in FRACTIONS:
                for name,a,b in [('cause_hit',shtr,shte),('cause_value',srtr,srte),('cause_consensus',ctr,cte)]:
                    cutoff=float(a.quantile(1-f)); idx=te.index[b>=cutoff]; picks.setdefault((name,f),[]).append(te.loc[idx].copy())
    rows=[]
    for (method,f),parts in picks.items():
        g=pd.concat(parts,ignore_index=True) if parts else cand.iloc[0:0].copy(); a=w1.metric(g); a['max_drawdown_yen']=w1.max_drawdown(g)
        mo,red,mn=monthstats(g); co=pd.concat([base,g],ignore_index=True); cm=w1.metric(co); cm['max_drawdown_yen']=w1.max_drawdown(co)
        rows.append({'method':method,'fraction':f,'addon':a,'monthly':mo,'red_months':red,'min_monthly_roi_pct':mn,'combined':cm,'overlap_with_v288':0})
    rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
    passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3]
    dec='SHADOW_CANDIDATE_WAVE11' if passers else 'NO_ADOPTION_WAVE11'
    out={'research_version':'v289-addon-wave11-reject-cause-moe','github_run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'rules':{'baseline_fixed':'v288 94R','candidate':'final v288 NO_BET only','model':'nearest-v288-route reject cause mixture','missing_cause':'FAIL_CLOSED','walk_forward':'Feb-Aug prior months only','july_august':'NON-PRISTINE','september_outcomes_used':False},'baseline':{**bm,'max_drawdown_yen':w1.max_drawdown(base)},'candidate_pool':w1.metric(cand),'cause_counts':cand.cause.value_counts(dropna=False).to_dict(),'methods':rows,'passers':passers,'decision':dec,'audit':audit,'thresholds':thr}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v289 3号艇 add-on — Wave 11 reject-cause mixture-of-experts','', '- v288 **94R fixed**; final NO_BET only','- pre-race nearest failed route: NEAR_S / NEAR_A / NEAR_B; missing cause => fail closed','- cause-specific hit / realized-value / exhibition-consensus experts, prior months only','- Jul/Aug NON-PRISTINE; September unused','', '## Methods','|method|frac|R|hits|ROI|profit|min month|red|max DD|overlap|combined R|combined ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        a=x['addon']; c=x['combined']; mn=x['min_monthly_roi_pct']
        L.append(f'|{x["method"]}|{x["fraction"]:.2f}|{a["races"]}|{a["hits"]}|{a["roi_pct"] if a["roi_pct"] is not None else float("nan"):.2f}%|{a["profit_yen"]:+,.0f}|{mn if mn is not None else float("nan"):.2f}%|{x["red_months"]}|{a["max_drawdown_yen"]:,.0f}|0|{c["races"]}|{c["roi_pct"]:.2f}%|')
    L += ['', '## Decision',f'**{dec}**']
    OUT_MD.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L)); print('V289_WAVE11_REJECT_CAUSE_OK')
if __name__=='__main__': main()
