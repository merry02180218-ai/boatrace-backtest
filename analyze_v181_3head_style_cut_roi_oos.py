#!/usr/bin/env python3
"""v181: choose v180 style p3 cut on Mar-May only, then fixed Jun-Aug ROI test with v166 top10.
NO-LEAK: cut selection never sees Jun-Aug. Pair lambda follows v166 Mar-May tuning. Payout settlement only.
"""
import csv
from datetime import date
import numpy as np
import pandas as pd
from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read,ff,ii,combo,choose,score_month,pct
from analyze_v177_3head_historical_web_enrichment import reconstruct

OUT='analysis_v181_3head_style_cut_roi_oos.csv'; SUMMARY='summary_v181_3head_style_cut_roi_oos.md'
VAL=['2026-03','2026-04','2026-05']; TEST=['2026-06','2026-07','2026-08']
STYLE=['b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b1_escape_rate','b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head_rate','style_makuri_edge','style_makurisashi_edge']
CUTS=[.20,.225,.25,.275,.30,.325,.35,.375,.40,.425,.45]

def build_probs():
    src,df=load();dc=pc(df,['date','race_date','ymd']);vc=pc(df,['venue','jcd','stadium','place']);y,_=target(df);base=feats(df)
    raw=read(str(src));extra,cov=reconstruct(raw);d=df.copy();d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce');d['_y']=y
    for k in STYLE:d[k]=[float(extra.get(i,{}).get(k,0.0)) for i in range(len(d))]
    d=d[d._date.notna()&d._y.notna()].copy(); out={}
    for mon in VAL+TEST:
        m=pd.Timestamp(mon+'-01');e=m+pd.offsets.MonthBegin(1);tr=d[d._date<m].copy();te=d[(d._date>=m)&(d._date<e)].copy();fs=base+STYLE;nums=[]
        for c in fs:
            if pd.to_numeric(d[c],errors='coerce').notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
        cats=[vc] if vc and vc not in nums else [];mo=model(nums,cats);mo.fit(tr[nums+cats],tr._y.astype(int));p=mo.predict_proba(te[nums+cats])[:,1]
        for ix,pr in zip(te.index,p):out[int(ix)]=float(pr)
    return raw,out,cov

def stat(rs,cut):
    q=[r for r in rs if ff(r.get('p3style'))>=cut];h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    hit=[r for r in q if 0<ii(r.get('v166_rank20'))<=10];sett=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ff(r.get('payout100')) for r in sett if 0<ii(r.get('v166_rank20'))<=10)
    return len(q),pct(len(h),len(q)),pct(len(hit),len(q)),pct(sum(1 for r in h if 0<ii(r.get('v166_rank20'))<=10),len(h)),100*ret/(len(sett)*1000) if sett else 0

def main():
    src,p,cov=build_probs();lam,_=choose(src);allrows=[]
    for mon in VAL+TEST:allrows+=score_month(src,mon,lam)
    keyidx={(r['date'],r.get('race_code')):i for i,r in enumerate(src)}
    for r in allrows:
        i=keyidx.get((r['date'],r.get('race_code')),-1);r['p3style']=p.get(i,'')
    val=[r for r in allrows if r.get('v166_month') in VAL]
    tune=[]
    for c in CUTS:
        n,hr,hit,cv,roi=stat(val,c);tune.append((c,n,hr,hit,cv,roi))
    eligible=[x for x in tune if x[1]>=150 and x[2]>=30.0]
    if not eligible: eligible=[x for x in tune if x[1]>=100]
    cut=max(eligible,key=lambda x:(x[5],x[3],x[2],x[1]))[0]
    test=[r for r in allrows if r.get('v166_month') in TEST]
    fs=sorted(set().union(*(r.keys() for r in test)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(test)
    L=['# v181 v180-style cut固定 → v166 top10 ROI OOS','', '- style p3 cutはMar-Mayだけで選択。Jun-Augは完全固定OOS。',f'- v166 pair lambda = {lam:.2f}（v166ルールでMar-May選択）',f"- reconstruction matched: {cov['matched_src']}",'','## Mar-May cut tuning','|cut|R|③頭率|top10 hit|③頭coverage|ROI|','|---:|---:|---:|---:|---:|---:|']
    for x in tune:L.append(f'|{x[0]:.3f}|{x[1]}|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.2f}%|{x[5]:.1f}%|')
    L+=['',f'固定cut = **{cut:.3f}**','','## Jun-Aug fixed OOS','|month|R|③頭率|top10 hit|③頭coverage|ROI|','|---|---:|---:|---:|---:|---:|']
    for mon in TEST:
        x=stat([r for r in test if r.get('v166_month')==mon],cut);L.append(f'|{mon}|{x[0]}|{x[1]:.2f}%|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.1f}%|')
    x=stat(test,cut);L.append(f'|ALL|{x[0]}|{x[1]:.2f}%|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.1f}%|')
    L+=['','## Current v165+v166 reference','- p3>=0.30 / top10: Jun-Aug R270, ③頭率38.52%, hit29.26%, coverage75.96%, ROI103.2%.','', '## Decision','- ROIを最優先、次にhit・③頭率・月別安定性。Jun-Augを見てcutは変更しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
