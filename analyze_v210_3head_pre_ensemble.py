#!/usr/bin/env python3
"""v210: SHADOW ensemble PRE for canonical 3-head production.

Goal: reduce exhibition workload while preserving eventual v165 p3head>=0.30 passes.
Strict protocol: June train -> July ensemble/cut selection -> frozen August report.
No current-race exhibition/result/odds enters PRE features. FINAL remains v165>=.30 -> v166 Top10.
August has already been inspected in project history, so this is SHADOW replay, not pristine adoption evidence.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v207_3head_enhanced_pre as v207
import analyze_v191_3head_clean_pre_restore_june as restore

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v210_3head_pre_ensemble.csv'
ROI_OUT=ROOT/'analysis_v210_3head_pre_ensemble_roi.csv'
SUMMARY=ROOT/'summary_v210_3head_pre_ensemble.md'
TARGETS=[.08,.10,.12]
SPECIAL={'202608112308','202608210409'}


def pct_rank(x):
    s=pd.Series(np.asarray(x,float))
    return s.rank(method='average',pct=True).to_numpy(float)


def ensemble(scores, mode):
    a=np.vstack(scores)
    if mode=='mean': return a.mean(axis=0)
    if mode=='max': return a.max(axis=0)
    if mode=='top2':
        z=np.sort(a,axis=0)
        return z[-2:,:].mean(axis=0)
    if mode=='prior_plus_base': return .6*a[2]+.4*a[0]
    raise ValueError(mode)


def cut_for_rate(p,rate):
    return float(np.quantile(np.asarray(p,float),1-rate,method='higher'))


def metric(df,p,cut):
    y=df.label.to_numpy(int);sel=np.asarray(p)>=cut;pos=int(y.sum());tp=int(((y==1)&sel).sum());n=int(sel.sum())
    return {'R':len(df),'formal':pos,'watch':n,'watch_rate':n/len(df),'recall':tp/pos if pos else 0,'precision':tp/n if n else 0,'tp':tp}


def main():
    hist,miss,cover,missing_dates=restore.hist_rows()
    h=pd.DataFrame(hist);h['_code']=h.race_code.map(v207.norm_code)
    att=pd.read_csv(v207.ATT);att['_code']=att.race_code.map(v207.norm_code)
    keep=['_code']+v207.TACTICS+v207.PRIOR_EX
    h=h.merge(att[keep],on='_code',how='inner',validate='one_to_one')
    for c in v207.TACTICS+v207.PRIOR_EX:
        h[c]=pd.to_numeric(h[c],errors='coerce').fillna(.5)
    h['venue']=h['venue'].astype(str)
    tr=h[h.month=='2026-06'].copy();tu=h[h.month=='2026-07'].copy();te=h[h.month=='2026-08'].copy()
    if min(len(tr),len(tu),len(te))<1000: raise RuntimeError(f'bad sizes {len(tr),len(tu),len(te)}')

    names=list(v207.SETS.keys())
    pj=[];pa=[]
    for name in names:
        m=v207.fit_model(tr,v207.SETS[name])
        pj.append(pct_rank(v207.probs(m,tu,v207.SETS[name])))
        pa.append(pct_rank(v207.probs(m,te,v207.SETS[name])))

    modes=['mean','max','top2','prior_plus_base']
    candidates=[]
    frozen={}
    for mode in modes:
        sj=ensemble(pj,mode);sa=ensemble(pa,mode)
        for rate in TARGETS:
            cut=cut_for_rate(sj,rate);mj=metric(tu,sj,cut);ma=metric(te,sa,cut)
            candidates.append({'mode':mode,'target':rate,'cut':cut,**{f'jul_{k}':v for k,v in mj.items()}})
            frozen[(mode,rate)]={'sj':sj,'sa':sa,'cut':cut,'mj':mj,'ma':ma}

    selected={}
    for rate in TARGETS:
        c=[x for x in candidates if x['target']==rate]
        c.sort(key=lambda x:(x['jul_recall'],x['jul_precision'],-x['jul_watch_rate']),reverse=True)
        selected[rate]=c[0]['mode']

    rows=[]
    for mode in modes:
        for rate in TARGETS:
            z=frozen[(mode,rate)]
            for split,mm in [('tune_july',z['mj']),('shadow_aug',z['ma'])]:
                rows.append({'mode':mode,'target_rate':rate,'selected_on_july':int(selected[rate]==mode),'split':split,'cut':z['cut'],**mm})
    pd.DataFrame(rows).to_csv(OUT,index=False,encoding='utf-8-sig')

    prod=pd.read_csv(v207.V195);prod=prod[prod.month=='2026-08'].copy();prod['_code']=prod.race_code.map(v207.norm_code)
    od=v207.load_od3()
    fin=pd.read_csv(v207.V108,usecols=['race_code','turn_margin23','st_margin23']);fin['_code']=fin.race_code.map(v207.norm_code);fin=fin.drop_duplicates('_code').set_index('_code')
    money=[];audit=[]
    for rate in TARGETS:
        mode=selected[rate];z=frozen[(mode,rate)]
        sel=set(te.loc[np.asarray(z['sa'])>=z['cut'],'_code'])
        tag=f'v210_{int(rate*100)}pct_{mode}'
        money+=v207.settle(prod,sel,od,tag,fin)
        for code in sorted(SPECIAL):
            rr=te[te['_code']==code]
            if len(rr):
                idx=rr.index[0];pos=te.index.get_loc(idx);score=float(z['sa'][pos])
                audit.append({'tag':tag,'race_code':code,'score':score,'cut':z['cut'],'pre_watch':int(score>=z['cut']),'formal_label':int(rr.iloc[0].label)})
    pd.DataFrame(money).to_csv(ROI_OUT,index=False,encoding='utf-8-sig')

    L=['# v210 3-head PRE ensemble — SHADOW','','**Goal: predict eventual v165 p3head>=30% using PRE-safe data with fewer exhibition checks.**','',
       '- Protocol: June train -> July ensemble/cut selection -> frozen August replay.','- August is report-only and already inspected historically; do not call this pristine OOS adoption evidence.',
       f'- rows: June {len(tr)}, July {len(tu)}, August {len(te)}; unmatched {miss}; missing dates {missing_dates or "none"}.','',
       '## July-selected ensemble, frozen August','|target|ensemble|cut|July watch|July recall|July precision|Aug watch|Aug recall|Aug precision|','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for rate in TARGETS:
        mode=selected[rate];z=frozen[(mode,rate)];a=z['mj'];b=z['ma']
        L.append(f'|{rate*100:.0f}%|{mode}|{z["cut"]:.6f}|{a["watch"]} ({a["watch_rate"]*100:.1f}%)|{a["recall"]*100:.1f}%|{a["precision"]*100:.1f}%|{b["watch"]} ({b["watch_rate"]*100:.1f}%)|{b["recall"]*100:.1f}%|{b["precision"]*100:.1f}%|')
    L+=['','## August operational settlement (od3, ¥10,000 Dutch)','|rule|settled R|Top10 hit|avg composite|return|ROI|','|---|---:|---:|---:|---:|---:|']
    for rate in TARGETS:
        tag=f'v210_{int(rate*100)}pct_{selected[rate]}';rr=[x for x in money if x['tag']==tag];a=v207.agg(rr)
        L.append(f'|{tag}|{a["R"]}|{a["hit_rate"]*100:.1f}%|{a["avg_comp"]:.3f}|¥{a["return"]:,.0f}|**{a["roi"]:.1f}%**|')
    L+=['','## Previously missed profitable races audit','|rule|race|score|cut|PRE watch|formal v165 pass|','|---|---|---:|---:|---|---|']
    for x in audit:
        L.append(f'|{x["tag"]}|{x["race_code"]}|{x["score"]:.6f}|{x["cut"]:.6f}|{"YES" if x["pre_watch"] else "NO"}|{x["formal_label"]}|')
    L+=['','## Decision','- Production remains unchanged. v210 is SHADOW only.','- Prefer the smallest target rate that materially preserves v165-pass recall and does not worsen operational return concentration.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L),flush=True)

if __name__=='__main__': main()
