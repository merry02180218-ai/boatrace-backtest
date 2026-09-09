#!/usr/bin/env python3
from __future__ import annotations
import csv, io, time, urllib.request
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
SRC=ROOT/'analysis_v243_3head_expand_feature_audit.csv'; OUT=ROOT/'analysis_v245_3head_exclude_firstday_newmotor.csv'; SUM=ROOT/'summary_v245_3head_exclude_firstday_newmotor.md'
BANK=10000; START=date(2025,12,1); END=date(2026,8,31); LOOKBACK=120
CANON_KEEP_THR=-0.1999999999999999; CANON_RESCUE_THR=0.5672342857142857

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
    h=int(g.trifecta_hit.sum()); ret=float(g.ret.sum()); return dict(R=n,hits=h,hit=h/n,roi=ret/(n*BANK),ret=ret)
def code_of(r): return str(r.get('レースコード','')).strip().zfill(12)
def venue_of(code,r):
    v=str(r.get('レース場コード','')).strip(); return v.zfill(2) if v and v.lower()!='nan' else (code[8:10] if len(code)==12 else '')
def motor_ids(r):
    return [z for b in range(1,7) if (z:=str(r.get(f'艇{b}_モーター番号','')).strip()) and z.lower()!='nan']

def main():
    if not SRC.exists(): raise RuntimeError('canonical v243 artifact is required')
    q=pd.read_csv(SRC,dtype={'race_code':str}); q['race_code']=q.race_code.astype(str).str.zfill(12); q['date']=q.date.astype(str)
    base=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    keep=base&(pd.to_numeric(q['f__c_b3_minus_b5_st'],errors='coerce')>=CANON_KEEP_THR)
    rescue=(q.bet==1)&(~base)&(pd.to_numeric(q['f__c_attack3_stretch'],errors='coerce')<=CANON_RESCUE_THR)
    selected=q[keep|rescue].copy()
    if len(selected)!=182: raise RuntimeError(f'canonical policy mismatch: expected 182, got {len(selected)}')

    title_daily={}; card_daily={}; d=START-timedelta(days=LOOKBACK)
    while d<=END:
        y=d.strftime('%Y/%m/%d'); title_daily[d]=rows(f'data/programs/title/{y}.csv'); card_daily[d]=rows(f'data/programs/race_cards/{y}.csv'); d+=timedelta(days=1)

    meta=[]; known_starts={}
    for d in sorted(title_daily):
        for r in title_daily[d]:
            c=code_of(r); v=venue_of(c,r); lab=str(r.get('日次','')).strip(); dn=daynum(lab); title=str(r.get('タイトル','')).strip(); ms=None
            if dn:
                ms=d-timedelta(days=dn-1); known_starts.setdefault((v,title),[]).append(ms)
            meta.append({'race_code':c,'venue':v,'day_label':lab,'day_no':dn if dn else np.nan,'title':title,'date_obj':d,'meeting_start':str(ms) if ms else None})
    mm=pd.DataFrame(meta).drop_duplicates('race_code')
    for idx,r in mm[mm.meeting_start.isna()].iterrows():
        cand=[x for x in known_starts.get((r.venue,r.title),[]) if timedelta(0)<=r.date_obj-x<=timedelta(days=10)]
        if cand: mm.at[idx,'meeting_start']=str(max(cand))
    selected=selected.merge(mm[['race_code','venue','day_label','day_no','meeting_start']],on='race_code',how='left')
    coverage=float(selected.day_label.notna().mean())
    if coverage<0.95: raise RuntimeError(f'official title metadata coverage too low: {coverage:.1%}')
    selected['first_day']=(selected.day_label=='初日').astype(int)

    meeting_first={}; daily_motors={}
    for d,cs in card_daily.items():
        rec=[]; tmap={code_of(r):r for r in title_daily.get(d,[])}
        for r in cs:
            c=code_of(r); v=venue_of(c,r); ids=motor_ids(r); rec.append((v,ids)); t=tmap.get(c,{})
            if str(t.get('日次','')).strip()=='初日': meeting_first.setdefault((v,d),[]).extend(ids)
        daily_motors[d]=rec
    newrows=[]
    for (v,ms),mids in sorted(meeting_first.items(),key=lambda x:(x[0][1],x[0][0])):
        seen=set(); z=ms-timedelta(days=LOOKBACK)
        while z<ms:
            for vv,ids in daily_motors.get(z,[]):
                if vv==v: seen.update(ids)
            z+=timedelta(days=1)
        valid=[m for m in mids if m]; fresh=sum(m not in seen for m in valid)/len(valid) if valid else np.nan
        newrows.append({'venue':v,'meeting_start':str(ms),'fresh_share':fresh,'new_motor_meeting':int(np.isfinite(fresh) and fresh>=.80),'entries':len(valid)})
    fm=pd.DataFrame(newrows)
    if len(fm): selected=selected.merge(fm[['venue','meeting_start','fresh_share','new_motor_meeting']],on=['venue','meeting_start'],how='left')
    else: selected['fresh_share']=np.nan; selected['new_motor_meeting']=0
    selected['new_motor_meeting']=selected.new_motor_meeting.fillna(0).astype(int)

    variants={'ALL_182':pd.Series(True,index=selected.index),'EXCLUDE_FIRST_DAY':selected.first_day==0,'EXCLUDE_NEW_MOTOR_MEETING':selected.new_motor_meeting==0,'EXCLUDE_BOTH':(selected.first_day==0)&(selected.new_motor_meeting==0)}
    out=[]
    for name,mask in variants.items():
        g=selected[mask]
        out.append({'variant':name,'scope':'ALL','month':np.nan,'venue':np.nan,**metrics(g)})
        for mon,z in g.groupby(g.date.str[:7]): out.append({'variant':name,'scope':'MONTH','month':mon,'venue':np.nan,**metrics(z)})
        for ven,z in g.groupby('venue'): out.append({'variant':name,'scope':'VENUE','month':np.nan,'venue':ven,**metrics(z)})
    O=pd.DataFrame(out); O.to_csv(OUT,index=False)
    L=['# v245 corrected first-day / new-motor exclusion audit','', '- Canonical v243 policy reproduced: 182 races.', '- First day uses official title CSV `日次=初日`; title metadata coverage enforced >=95%.', f'- New-motor meeting proxy: >=80% of day-1 assigned motor numbers unseen at that venue in prior {LOOKBACK} days.', '- Dec2025-Aug2026 is in-sample / selection-contaminated, not pristine validation.','',f'- Official title metadata coverage: {coverage:.2%}','', '|variant|R|hit|ROI|','|---|---:|---:|---:|']
    for _,r in O[O.scope=='ALL'].iterrows(): L.append(f'|{r.variant}|{int(r.R)}|{100*r.hit:.2f}%|{100*r.roi:.2f}%|')
    L+=['','## Monthly EXCLUDE_BOTH','|month|R|hit|ROI|','|---|---:|---:|---:|']
    for _,r in O[(O.variant=='EXCLUDE_BOTH')&(O.scope=='MONTH')].iterrows(): L.append(f'|{r.month}|{int(r.R)}|{100*r.hit:.2f}%|{100*r.roi:.2f}%|')
    for name in variants:
        L+=['',f'## Venue breakdown: {name}','|venue|R|hit|ROI|','|---|---:|---:|---:|']
        for _,r in O[(O.variant==name)&(O.scope=='VENUE')].sort_values(['R','roi'],ascending=[False,False]).iterrows():
            L.append(f'|{r.venue}|{int(r.R)}|{100*r.hit:.2f}%|{100*r.roi:.2f}%|')
    L+=['','## Detected new-motor meetings','|venue|meeting start|fresh share|','|---|---|---:|']
    det=fm[fm.new_motor_meeting==1] if len(fm) else fm
    if len(det):
        for _,r in det.iterrows(): L.append(f'|{r.venue}|{r.meeting_start}|{100*r.fresh_share:.1f}%|')
    else: L.append('|none|-|-|')
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
