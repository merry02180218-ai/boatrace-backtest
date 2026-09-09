#!/usr/bin/env python3
from __future__ import annotations
import csv, io, time, urllib.request
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
SRC=ROOT/'analysis_v243_3head_expand_feature_audit.csv'
OUT=ROOT/'analysis_v245_3head_exclude_firstday_newmotor.csv'
SUM=ROOT/'summary_v245_3head_exclude_firstday_newmotor.md'
BANK=10000
START=date(2025,12,1); END=date(2026,8,31); LOOKBACK=120

def fetch(path):
    for k in range(3):
        try:
            with urllib.request.urlopen(BASE+path,timeout=30) as r:return r.read().decode('utf-8-sig')
        except Exception:
            if k<2: time.sleep(1.0+k)
    return ''

def rows(path):
    s=fetch(path); return list(csv.DictReader(io.StringIO(s))) if s else []

def daynum(s):
    z=(s or '').strip().replace(' ','').replace('　','')
    mp={'初日':1,'２日目':2,'2日目':2,'３日目':3,'3日目':3,'４日目':4,'4日目':4,'５日目':5,'5日目':5,'６日目':6,'6日目':6,'７日目':7,'7日目':7,'８日目':8,'8日目':8,'９日目':9,'9日目':9}
    return mp.get(z,0)

def metrics(g):
    n=len(g)
    if not n:return dict(R=0,hits=0,hit=np.nan,roi=np.nan,ret=0.)
    h=int(g.trifecta_hit.sum()); ret=float(g.ret.sum())
    return dict(R=n,hits=h,hit=h/n,roi=ret/(n*BANK),ret=ret)

def code_of(r): return str(r.get('レースコード','')).strip().zfill(12)
def venue_of(code,r):
    v=str(r.get('レース場コード','')).strip()
    if v and v.lower()!='nan': return v.zfill(2)
    return code[8:10] if len(code)==12 else ''
def motor_ids(r):
    out=[]
    for b in range(1,7):
        z=str(r.get(f'艇{b}_モーター番号','')).strip()
        if z and z.lower()!='nan': out.append(z)
    return out

def main():
    if not SRC.exists(): raise RuntimeError('canonical v243 artifact is required')
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['race_code']=q.race_code.astype(str).str.zfill(12); q['date']=q.date.astype(str)
    base=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    keep=base&(pd.to_numeric(q['f__c_b3_minus_b5_st'],errors='coerce')>=-0.2)
    rescue=(q.bet==1)&(~base)&(pd.to_numeric(q['f__c_attack3_stretch'],errors='coerce')<=0.5672342857142857)
    selected=q[keep|rescue].copy()
    if len(selected)!=182: raise RuntimeError(f'canonical policy mismatch: expected 182, got {len(selected)}')

    # Read official title/card data. Include 120 days before study start so a motor is
    # considered new only if its number has not appeared at that venue in the lookback.
    daily={}; d=START-timedelta(days=LOOKBACK)
    while d<=END:
        y=d.strftime('%Y/%m/%d'); ts=rows(f'data/programs/title/{y}.csv'); cs=rows(f'data/programs/race_cards/{y}.csv')
        tmap={code_of(r):r for r in ts}; rec=[]
        for r in cs:
            c=code_of(r); t=tmap.get(c,{})
            rec.append((c,venue_of(c,r),daynum(t.get('日次','')),motor_ids(r)))
        daily[d]=rec; d+=timedelta(days=1)

    meta=[]; meeting_first={}
    for d in sorted(x for x in daily if x>=START):
        for c,v,dn,mids in daily[d]:
            if dn:
                ms=d-timedelta(days=dn-1); meta.append({'race_code':c,'venue':v,'day_no':dn,'meeting_start':str(ms)})
                if dn==1: meeting_first.setdefault((v,d),[]).extend(mids)
    mm=pd.DataFrame(meta).drop_duplicates('race_code')
    selected=selected.merge(mm,on='race_code',how='left')
    coverage=float(selected.day_no.notna().mean())
    if coverage<0.95: raise RuntimeError(f'official day metadata coverage too low: {coverage:.1%}')
    selected['first_day']=(selected.day_no==1).astype(int)

    # New-motor meeting proxy: on official day 1, >=80% of motor assignments have not
    # appeared at that venue during the preceding 120 calendar days.
    newrows=[]
    for (v,ms),mids in sorted(meeting_first.items(),key=lambda x:(x[0][1],x[0][0])):
        seen=set(); a=max(START-timedelta(days=LOOKBACK),ms-timedelta(days=LOOKBACK)); z=a
        while z<ms:
            for _,vv,_,ids in daily.get(z,[]):
                if vv==v: seen.update(ids)
            z+=timedelta(days=1)
        valid=[m for m in mids if m]; fresh=sum(m not in seen for m in valid)/len(valid) if valid else np.nan
        newrows.append({'venue':v,'meeting_start':str(ms),'fresh_share':fresh,'new_motor_meeting':int(np.isfinite(fresh) and fresh>=.80),'entries':len(valid)})
    fm=pd.DataFrame(newrows)
    selected=selected.merge(fm[['venue','meeting_start','fresh_share','new_motor_meeting']],on=['venue','meeting_start'],how='left')
    selected['new_motor_meeting']=selected.new_motor_meeting.fillna(0).astype(int)

    variants={'ALL_182':pd.Series(True,index=selected.index),'EXCLUDE_FIRST_DAY':selected.first_day==0,'EXCLUDE_NEW_MOTOR_MEETING':selected.new_motor_meeting==0,'EXCLUDE_BOTH':(selected.first_day==0)&(selected.new_motor_meeting==0)}
    out=[]
    for name,mask in variants.items():
        g=selected[mask]; out.append({'variant':name,'month':np.nan,**metrics(g)})
        for mon,z in g.groupby(g.date.str[:7]):out.append({'variant':name,'month':mon,**metrics(z)})
    pd.DataFrame(out).to_csv(OUT,index=False)
    O=pd.DataFrame(out)
    L=['# v245 corrected first-day / new-motor exclusion audit','',f'- Canonical v243 policy reproduced: 182 races.','- First day: official title CSV `日次=初日`; join coverage is enforced at >=95% (no silent unknown-day pass-through).',f'- New-motor meeting: operational proxy = on official day 1, >=80% of assigned motor numbers were unseen at that venue in the prior {LOOKBACK} days.','- Dec2025-Aug2026 is in-sample / selection-contaminated, not pristine validation.','',f'- Official day metadata coverage on selected races: {coverage:.2%}','', '|variant|R|hit|ROI|','|---|---:|---:|---:|']
    for _,r in O[O.month.isna()].iterrows():L.append(f'|{r.variant}|{int(r.R)}|{100*r.hit:.2f}%|{100*r.roi:.2f}%|')
    L+=['','## Monthly EXCLUDE_BOTH','|month|R|hit|ROI|','|---|---:|---:|---:|']
    for _,r in O[(O.variant=='EXCLUDE_BOTH')&O.month.notna()].iterrows():L.append(f'|{r.month}|{int(r.R)}|{100*r.hit:.2f}%|{100*r.roi:.2f}%|')
    L+=['','## Detected new-motor meetings','|venue|meeting start|fresh share|','|---|---|---:|']
    det=fm[fm.new_motor_meeting==1] if len(fm) else fm
    if len(det):
        for _,r in det.iterrows():L.append(f'|{r.venue}|{r.meeting_start}|{100*r.fresh_share:.1f}%|')
    else:L.append('|none|-|-|')
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__':main()
