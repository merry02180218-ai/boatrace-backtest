#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import json, pickle

import numpy as np
import pandas as pd

from backtest import rows
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v299_1head_trifecta3_policy_search as v299
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v312_1head_opponent_outer_gate as v312
import run_v320_1head_exact3_ticket_policy as v320
import run_v326_1head_ticketaware_exhibition as v326
import run_v332_1head_attack_first_redesign as v332

ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/v337'); OUT.mkdir(parents=True,exist_ok=True)
DEV_PRED=ROOT/'analysis_v308_1head_volume_opponent_joint_pred.csv'
JUL_HEAD=ROOT/'cache_v321_julaug_nonpristine_head.csv'
SECOND=ROOT/'cache_v321_julaug_second.pkl'
BASE_PC=ROOT/'cache_v321_julaug_base_pc.pkl'
THIRD=ROOT/'cache_v321_julaug_third.pkl'

CUTS=[0.8073405637,0.80,0.79,0.78,0.77,0.75]
OPP=.375
POLICY='HYBRID'; ALPHA=.70
MONTHS=['2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
PRELOAD=date(2025,10,1)
CFG={'family':'ATTACK_ENV_SOFT','env_w':0.1,'q':0.65}


def pct(n,d): return 100*n/d if d else float('nan')
def met(z):
    n=len(z); h=int(z.head_hit.sum()) if n else 0; e=int(z.hit.sum()) if n else 0
    return {'R':n,'head':h,'head_rate':pct(h,n),'exact3':e,'exact3_rate':pct(e,n)}

def validate_no_sep(df):
    if any(str(x).startswith('2026-09') for x in df.get('month',pd.Series(dtype=str)).astype(str).unique()):
        raise RuntimeError('September entered v337')

def canonical_anchor(canon):
    selected=[]
    for m in MONTHS:
        if m=='2026-08': tr=canon[canon.month.isin(MONTHS[:-1])].copy()
        else: tr=canon[canon.month.isin([x for x in MONTHS[:-1] if x!=m])].copy()
        z=canon[canon.month.eq(m)].copy(); p,_=v332.fit_apply(tr,z,CFG); selected.append(p)
    s=pd.concat(selected,ignore_index=True)
    mm=met(s)
    if (mm['R'],mm['head'],mm['exact3'])!=(96,83,45):
        raise AssertionError(f'CANONICAL_V332_DRIFT before v337 overlay: {mm}')
    return s

def dev_ticket_map(ids:set[str]):
    d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
    validate_no_sep(d)
    p2,pc=v320.build_factorized(d,p3,p4)
    fn=v299.STRATEGIES[POLICY]
    out={}
    for tm in list(v298.TEST_MONTHS):
        for code in d.loc[(d.month==tm)&d.race_code.isin(ids),'race_code'].astype(str):
            probs=v299.pair_prob(p2[tm][code],pc[tm][code],ALPHA)
            top3=fn(p2[tm][code],pc[tm][code],probs)[:3]
            out[code]=';'.join(f'1-{s}-{t}' for s,t in top3)
    return out

def load_candidate_base():
    dev=pd.read_csv(DEV_PRED,dtype={'race_code':str}); dev.race_code=dev.race_code.astype(str).str.zfill(12)
    dev['month']=dev.test_month.astype(str); validate_no_sep(dev)
    dev=dev[pd.to_numeric(dev.opp_mass,errors='coerce').ge(OPP)&pd.to_numeric(dev.p_head,errors='coerce').ge(min(CUTS))].copy()
    ids=set(dev.race_code)
    dt=dev_ticket_map(ids)
    dev['tickets']=dev.race_code.map(dt)
    if dev.tickets.isna().any(): raise RuntimeError(f'missing dev frozen tickets {int(dev.tickets.isna().sum())}')
    dev['hit']=[int(str(a) in str(t).split(';')) for a,t in zip(dev.actual_combo,dev.tickets)]
    dev['head_hit']=pd.to_numeric(dev.head_hit,errors='coerce').fillna(0).astype(int)
    dev=dev[['month','race_code','head_hit','actual_combo','p_head','opp_mass','tickets','hit']].copy()

    j=pd.read_csv(JUL_HEAD,dtype={'race_code':str}); j.race_code=j.race_code.astype(str).str.zfill(12); validate_no_sep(j)
    with SECOND.open('rb') as f: sec=pickle.load(f)
    with BASE_PC.open('rb') as f: bpc=pickle.load(f)
    with THIRD.open('rb') as f: pc=pickle.load(f)
    base_p2=sec['base_p2']; p2=sec['p2']; fn=v299.STRATEGIES[POLICY]
    rec=[]
    for _,r in j.iterrows():
        tm=str(r.month); code=str(r.race_code).zfill(12)
        if code not in base_p2.get(tm,{}) or code not in bpc.get(tm,{}): continue
        mass=v300.base5(base_p2[tm][code],bpc[tm][code])[1]
        ph=float(r.p_head)
        if mass<OPP or ph<min(CUTS): continue
        if code not in p2.get(tm,{}) or code not in pc.get(tm,{}): raise RuntimeError(f'missing JA frozen opponent {tm} {code}')
        probs=v299.pair_prob(p2[tm][code],pc[tm][code],ALPHA); top3=fn(p2[tm][code],pc[tm][code],probs)[:3]
        tickets=';'.join(f'1-{s}-{t}' for s,t in top3); actual=str(r.actual_combo)
        rec.append({'month':tm,'race_code':code,'head_hit':int(r.head_hit),'actual_combo':actual,'p_head':ph,'opp_mass':float(mass),'tickets':tickets,'hit':int(actual in tickets.split(';'))})
    ja=pd.DataFrame(rec); validate_no_sep(ja)
    y=pd.concat([dev,ja],ignore_index=True,sort=False); y.race_code=y.race_code.astype(str).str.zfill(12)
    if y.race_code.duplicated().any(): raise RuntimeError('duplicate candidate race_code')
    y.to_csv(OUT/'analysis_v337_candidate_base.csv',index=False)
    return y

def build_exhibition(base):
    wanted=set(base.race_code); selected_days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted})
    dayset=set(selected_days); last=max(selected_days); sums=defaultdict(list); allv=[]; features={}
    d=PRELOAD
    while d<=last:
        ymd=d.strftime('%Y/%m/%d'); strows=rows(f'data/previews/stt/{ymd}.csv'); bias=v326.st_bias(sums,allv)
        if d in dayset:
            tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv')); stt=v326.bycode(strows); orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
            prefix=d.strftime('%Y%m%d')
            for code in sorted(c for c in wanted if c.startswith(prefix)):
                tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
                audit={'has_tkz':int(code in tkz),'has_stt':int(code in stt),'has_orig':int(code in orig),**v326.raw_completeness(tr,sr,orr)}
                audit['source_complete']=int(all(audit[k] for k in ['tkz_all6','stt_all6','orig_turn_all6','orig_straight_all6','orig_avg_all6']))
                ex,st,os=v326.corrected_direct(code,tkz,stt,orig,bias)
                b=base.loc[base.race_code.eq(code)].iloc[0]
                z=v326.partial_feature_row(b,ex,st,os,audit); z.update(audit); features[code]=z
        v326.update_st(strows,sums,allv); d+=timedelta(days=1)
    feat=pd.DataFrame.from_dict(features,orient='index'); feat.index.name='race_code'; feat=feat.reset_index()
    y=base.merge(feat,on='race_code',how='left',validate='one_to_one')

    # Identity repair: the adopted 400-row v332 universe must use exactly the same
    # exhibition-feature route as v332 itself.  Broad v337-only candidates retain
    # the dynamic reconstruction above.  This prevents transient remote preview
    # fetch misses in the much broader sweep from changing the frozen anchor.
    canon=v332.load_all().copy(); canon.race_code=canon.race_code.astype(str).str.zfill(12); validate_no_sep(canon)
    canon_pass=canonical_anchor(canon)
    overlay_cols=list(v326.MODEL_FEATURES)+[
        'has_tkz','has_stt','has_orig','tkz_all6','stt_all6','orig_turn_all6',
        'orig_straight_all6','orig_avg_all6','orig_turn_straight_all6','source_complete',
        'second_boats','third_boats','covered_boats','uncovered_boats'
    ]
    overlay_cols=[c for c in overlay_cols if c in canon.columns]
    cm=canon.set_index('race_code')
    mask=y.race_code.isin(cm.index)
    for c in overlay_cols:
        y.loc[mask,c]=y.loc[mask,'race_code'].map(cm[c])
    pd.DataFrame({'race_code':y.loc[mask,'race_code'].astype(str)}).to_csv(OUT/'analysis_v337_canonical_overlay.csv',index=False)

    for c in ['tkz_all6','stt_all6','orig_turn_all6','orig_straight_all6','orig_avg_all6']:
        y[c]=pd.to_numeric(y.get(c),errors='coerce').fillna(0).astype(int)
    y['attack_ready']=y.tkz_all6.eq(1)&y.stt_all6.eq(1)&y.orig_straight_all6.eq(1)&y.orig_avg_all6.eq(1)
    y['env_ready']=y.tkz_all6.eq(1)&y.stt_all6.eq(1)&y.orig_turn_all6.eq(1)&y.orig_straight_all6.eq(1)
    for c in ['one_ex','one_st','one_straight','one_orig_avg','sec_ex_mean_margin','sec_st_mean_margin','third_turn_mean_margin','third_straight_mean_margin']:
        y[c]=pd.to_numeric(y.get(c),errors='coerce')
    y['attack_core']=np.nan; m=y.attack_ready
    y.loc[m,'attack_core']=.30*y.loc[m,'one_ex']+.30*y.loc[m,'one_st']+.23*y.loc[m,'one_straight']+.17*y.loc[m,'one_orig_avg']
    y['env_pair']=np.nan; m=y.env_ready
    y.loc[m,'env_pair']=.30*y.loc[m,'sec_ex_mean_margin']+.30*y.loc[m,'sec_st_mean_margin']+.20*y.loc[m,'third_turn_mean_margin']+.20*y.loc[m,'third_straight_mean_margin']
    y.to_csv(OUT/'analysis_v337_candidate_exhibition.csv',index=False)
    return y,canon_pass,len(cm.index.intersection(set(y.race_code)))

def eval_cut(allrows,cut):
    y=allrows[pd.to_numeric(allrows.p_head,errors='coerce').ge(cut)].copy(); selected=[]; monthly=[]
    for m in MONTHS:
        if m=='2026-08': tr=y[y.month.isin(MONTHS[:-1])].copy()
        else: tr=y[y.month.isin([x for x in MONTHS[:-1] if x!=m])].copy()
        z=y[y.month.eq(m)].copy(); p,_=v332.fit_apply(tr,z,CFG); p=p.copy(); p['eval_month']=m; selected.append(p)
        monthly.append({'cutoff':cut,'month':m,'pre_R':len(z),**{f'pass_{k}':v for k,v in met(p).items()}})
    s=pd.concat(selected,ignore_index=True) if selected else y.iloc[0:0].copy(); sm=met(s)
    return y,s,monthly,{'cutoff':cut,'pre_R':len(y),**sm,'races_per_month':len(s)/7.0}

def main():
    base=load_candidate_base(); y,canon_pass,overlay_n=build_exhibition(base); validate_no_sep(y)
    results={}; summaries=[]; monthly=[]
    for c in CUTS:
        pre,p,m,sm=eval_cut(y,c); results[c]=(pre,p); summaries.append(sm); monthly+=m
    anchor=results[CUTS[0]][1]
    ar=met(anchor)
    if (ar['R'],ar['head'],ar['exact3'])!=(96,83,45):
        pd.DataFrame(summaries).to_csv(OUT/'analysis_v337_summary.csv',index=False)
        pd.DataFrame(monthly).to_csv(OUT/'analysis_v337_monthly.csv',index=False)
        raise AssertionError(f'ANCHOR_IDENTITY_DRIFT got {ar} expected 96/83/45')
    if set(anchor.race_code.astype(str))!=set(canon_pass.race_code.astype(str)):
        miss=sorted(set(canon_pass.race_code.astype(str))-set(anchor.race_code.astype(str)))
        extra=sorted(set(anchor.race_code.astype(str))-set(canon_pass.race_code.astype(str)))
        raise AssertionError(f'ANCHOR_RACECODE_DRIFT missing={miss} extra={extra}')
    ref=set(anchor.race_code.astype(str)); bands=[]
    for c in CUTS[1:]:
        p=results[c][1]; add=p[~p.race_code.astype(str).isin(ref)].copy(); mm=met(add)
        bands.append({'cutoff':c,'added_pass_R':mm['R'],'added_head_rate':mm['head_rate'],'added_exact3_rate':mm['exact3_rate']})
    pd.DataFrame(summaries).to_csv(OUT/'analysis_v337_summary.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'analysis_v337_monthly.csv',index=False)
    pd.DataFrame(bands).to_csv(OUT/'analysis_v337_added_vs_anchor.csv',index=False)
    result={'WAKU10_DEPENDENCY':'NONE_IN_V308_V337_PATH','WAKU10_CHANGED_1HEAD_ROWS':0,'WAKU10_CUTOFF_CROSSINGS':0,
            'CANONICAL_V332_OVERLAY_ROWS':overlay_n,'anchor':ar,'summary':summaries,'added_vs_anchor':bands,'SEPTEMBER_OUTCOMES_READ':False}
    (OUT/'result_v337.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    L=['# v337 head-cutoff-only volume audit','', '- Waku10 dependency in v308/v337 PRE path: NONE.','- September outcomes unread.',
       '- v332 exhibition filter fixed: ATTACK_ENV_SOFT env_w=.1 q=.65.',f'- canonical v332 exhibition overlay rows: {overlay_n}.','']
    for r in summaries: L.append(f"- cutoff={r['cutoff']:.10f}: PRE {r['pre_R']}, PASS {r['R']} ({r['races_per_month']:.1f}/month), head {r['head']}/{r['R']}={r['head_rate']:.2f}%, exact3 {r['exact3']}/{r['R']}={r['exact3_rate']:.2f}%")
    L+=['','## Newly admitted final PASS vs anchor']
    for r in bands:L.append(f"- cutoff={r['cutoff']:.2f}: +{r['added_pass_R']} PASS, head {r['added_head_rate']:.2f}%, exact3 {r['added_exact3_rate']:.2f}%")
    (OUT/'summary_v337.md').write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L),flush=True)

if __name__=='__main__': main()
