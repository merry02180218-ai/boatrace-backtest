#!/usr/bin/env python3
from __future__ import annotations
import csv, io, urllib.request
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
START=date(2025,12,1); END=date(2026,8,31)


def fetch(path):
    try:
        with urllib.request.urlopen(BASE+path, timeout=20) as r:
            return r.read().decode('utf-8-sig')
    except Exception:
        return ''

def rows(path):
    s=fetch(path)
    return list(csv.DictReader(io.StringIO(s))) if s else []

def daynum(s):
    mp={'初日':1,'２日目':2,'３日目':3,'４日目':4,'５日目':5,'６日目':6,'７日目':7,'８日目':8,'９日目':9}
    return mp.get((s or '').strip(),0)

def ff(x):
    try:return float(str(x).replace('%','').strip())
    except:return np.nan

def metrics(g):
    n=len(g)
    if n==0:return dict(R=0,hits=0,hit=np.nan,roi=np.nan,ret=0.)
    h=int(g.trifecta_hit.sum()); ret=float(g.ret.sum())
    return dict(R=n,hits=h,hit=h/n,roi=ret/(n*BANK),ret=ret)

def main():
    if not SRC.exists(): raise RuntimeError('run v243 first')
    q=pd.read_csv(SRC,dtype={'race_code':str})
    q['race_code']=q.race_code.astype(str).str.zfill(12)
    q['date']=q.date.astype(str)

    # Exact v243 182R policy: baseline keep rule + rescue rule.
    base=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    keep=base & (pd.to_numeric(q['f__c_b3_minus_b5_st'],errors='coerce')>=-0.2)
    pool=(q.bet==1)&(~base)
    rescue=pool & (pd.to_numeric(q['f__c_attack3_stretch'],errors='coerce')<=0.5672342857142857)
    selected=q[keep|rescue].copy()

    # Build exact meeting-day map from title CSV and detect first meeting with brand-new motors.
    meta=[]; firstday_motor=[]
    d=START
    while d<=END:
        y=d.strftime('%Y/%m/%d')
        titles={str(r.get('レースコード','')).zfill(12):r for r in rows(f'data/programs/title/{y}.csv')}
        cards=rows(f'data/programs/race_cards/{y}.csv')
        byvenue={}
        for r in cards:
            code=str(r.get('レースコード','')).zfill(12)
            jo=str(r.get('レース場コード','')).zfill(2)
            t=titles.get(code,{})
            dn=daynum(t.get('日次',''))
            if dn:
                start=d-timedelta(days=dn-1)
                meta.append({'race_code':code,'venue':jo,'day_no':dn,'meeting_start':str(start)})
            if dn==1:
                byvenue.setdefault(jo,[]).append(r)
        for jo,rs in byvenue.items():
            vals=[]
            for r in rs:
                for b in range(1,7):
                    a=ff(r.get(f'艇{b}_モーター2連対率'))
                    c=ff(r.get(f'艇{b}_モーター3連対率'))
                    vals.append((a,c))
            if vals:
                # On a motor's debut meeting, official pre-race motor rates are blank/zero for almost all entries.
                fresh=np.mean([((not np.isfinite(a)) or abs(a)<1e-9) and ((not np.isfinite(c)) or abs(c)<1e-9) for a,c in vals])
                firstday_motor.append({'venue':jo,'meeting_start':str(d),'fresh_share':fresh,'new_motor_meeting':int(fresh>=0.80),'entries':len(vals)})
        d+=timedelta(days=1)

    mm=pd.DataFrame(meta).drop_duplicates('race_code')
    fm=pd.DataFrame(firstday_motor)
    selected=selected.merge(mm,on='race_code',how='left')
    if len(fm): selected=selected.merge(fm[['venue','meeting_start','fresh_share','new_motor_meeting']],on=['venue','meeting_start'],how='left')
    else:
        selected['fresh_share']=np.nan; selected['new_motor_meeting']=0
    selected['new_motor_meeting']=selected['new_motor_meeting'].fillna(0).astype(int)
    selected['first_day']=(selected['day_no']==1).astype(int)

    rowsout=[]
    variants={
      'ALL_182':pd.Series(True,index=selected.index),
      'EXCLUDE_FIRST_DAY':selected.first_day==0,
      'EXCLUDE_NEW_MOTOR_MEETING':selected.new_motor_meeting==0,
      'EXCLUDE_BOTH':(selected.first_day==0)&(selected.new_motor_meeting==0),
    }
    for name,mask in variants.items():
        g=selected[mask].copy(); m=metrics(g)
        rowsout.append({'variant':name,**m})
        for mon,z in g.groupby(g.date.str[:7]):
            mmx=metrics(z); rowsout.append({'variant':name,'month':mon,**mmx})
    pd.DataFrame(rowsout).to_csv(OUT,index=False)

    L=['# v245 first-day / new-motor exclusion audit','',
       '- Base selection is the exact v243 182R in-sample policy.',
       '- First day is read from official title CSV `日次=初日`.',
       '- New-motor meeting is detected on the meeting first day when >=80% of all six-boat motor 2/3-ren rates are blank or zero; the whole meeting is then excluded.',
       '- Historical settlement remains the v243 exact 10,000-yen Dutch result; no odds are re-used for selection.',
       '- Dec2025-Aug2026 includes non-pristine/in-sample months and is not clean validation.','',
       '|variant|R|hit|ROI|','|---|---:|---:|---:|']
    out=pd.DataFrame(rowsout)
    for _,r in out[out.month.isna()].iterrows():L.append(f"|{r.variant}|{int(r.R)}|{100*r.hit:.2f}%|{100*r.roi:.2f}%|")
    L += ['','## Monthly EXCLUDE_BOTH','|month|R|hit|ROI|','|---|---:|---:|---:|']
    for _,r in out[(out.variant=='EXCLUDE_BOTH')&out.month.notna()].iterrows():L.append(f"|{r.month}|{int(r.R)}|{100*r.hit:.2f}%|{100*r.roi:.2f}%|")
    L += ['','## Detected new-motor meetings','|venue|meeting start|fresh share|','|---|---|---:|']
    if len(fm):
        for _,r in fm[fm.new_motor_meeting==1].sort_values(['meeting_start','venue']).iterrows():L.append(f"|{r.venue}|{r.meeting_start}|{100*r.fresh_share:.1f}%|")
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__': main()
