#!/usr/bin/env python3
from __future__ import annotations
import csv, io, re, time, urllib.request
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
OFFICIAL='https://www.boatrace.jp/owpc/pc/race/raceindex'
SRC=ROOT/'analysis_v243_3head_expand_feature_audit.csv'; OUT=ROOT/'analysis_v245_3head_exclude_firstday_newmotor.csv'; SUM=ROOT/'summary_v245_3head_exclude_firstday_newmotor.md'
BANK=10000; START=date(2025,12,1); END=date(2026,8,31); LOOKBACK=120
CANON_KEEP_THR=-0.1999999999999999; CANON_RESCUE_THR=0.5672342857142857

FW=str.maketrans('０１２３４５６７８９','0123456789')

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
    z=(s or '').strip().replace(' ','').replace('　','').translate(FW)
    if z=='初日': return 1
    m=re.fullmatch(r'(\d+)日目',z)
    return int(m.group(1)) if m else 0
def metrics(g):
    n=len(g)
    if not n:return dict(R=0,hits=0,hit=np.nan,roi=np.nan,ret=0.)
    h=int(g.trifecta_hit.sum()); ret=float(g.ret.sum()); return dict(R=n,hits=h,hit=h/n,roi=ret/(n*BANK),ret=ret)
def code_of(r): return str(r.get('レースコード','')).strip().zfill(12)
def venue_of(code,r):
    v=str(r.get('レース場コード','')).strip(); return v.zfill(2) if v and v.lower()!='nan' else (code[8:10] if len(code)==12 else '')
def motor_ids(r):
    return [z for b in range(1,7) if (z:=str(r.get(f'艇{b}_モーター番号','')).strip()) and z.lower()!='nan']

def official_meeting_meta(venue:str,d:date):
    params={'jcd':venue,'hd':d.strftime('%Y%m%d')}
    headers={'User-Agent':'Mozilla/5.0'}
    for k in range(3):
        try:
            r=requests.get(OFFICIAL,params=params,headers=headers,timeout=20)
            r.raise_for_status()
            text=BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True).translate(FW)
            cur=None
            m=re.search(fr'{d.month}月\s*{d.day}日\s*(初日|\d+日目|最終日)',text)
            if m: cur=m.group(1)
            starts=[]
            for mm,dd in re.findall(r'(\d{1,2})月\s*(\d{1,2})日\s*初日',text):
                mm=int(mm); dd=int(dd)
                for yy in (d.year-1,d.year,d.year+1):
                    try: x=date(yy,mm,dd)
                    except ValueError: continue
                    if timedelta(0)<=d-x<=timedelta(days=10): starts.append(x)
            ms=max(starts) if starts else None
            if cur or ms: return cur,ms,'official_web'
        except Exception:
            if k<2: time.sleep(1.0+k)
    return None,None,None

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
            meta.append({'race_code':c,'venue':v,'day_label':lab,'day_no':dn if dn else np.nan,'title':title,'date_obj':d,'meeting_start':str(ms) if ms else None,'meta_source':'title_csv'})
    mm=pd.DataFrame(meta).drop_duplicates('race_code') if meta else pd.DataFrame(columns=['race_code','venue','day_label','day_no','meeting_start','meta_source'])
    selected=selected.merge(mm[['race_code','venue','day_label','day_no','meeting_start','meta_source']],on='race_code',how='left')

    cache={}; fallback_count=0
    for idx,r in selected.iterrows():
        need_label=pd.isna(r.day_label) or not str(r.day_label).strip()
        need_start=pd.isna(r.meeting_start) or not str(r.meeting_start).strip()
        if not (need_label or need_start): continue
        dd=date.fromisoformat(str(r.date)[:10]); vv=str(r.race_code)[8:10]
        key=(vv,dd)
        if key not in cache: cache[key]=official_meeting_meta(vv,dd)
        lab,ms,src=cache[key]
        if need_label and lab:
            selected.at[idx,'day_label']=lab; selected.at[idx,'day_no']=daynum(lab) if lab!='最終日' else np.nan
        if need_start and ms: selected.at[idx,'meeting_start']=str(ms)
        if src:
            selected.at[idx,'meta_source']=src; fallback_count+=1

    coverage=float(selected.day_label.notna().mean())
    start_coverage=float(selected.meeting_start.notna().mean())
    if coverage<0.95: raise RuntimeError(f'official day metadata coverage too low after fallback: {coverage:.1%}')
    if start_coverage<0.95: raise RuntimeError(f'official meeting-start coverage too low after fallback: {start_coverage:.1%}')
    selected['first_day']=(selected.day_label.astype(str).str.strip()=='初日').astype(int)

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
    else:
        selected['fresh_share']=np.nan; selected['new_motor_meeting']=np.nan
    selected['new_motor_known']=selected.new_motor_meeting.notna().astype(int)
    newmotor_coverage=float(selected.new_motor_known.mean())
    selected['new_motor_meeting']=selected.new_motor_meeting.fillna(0).astype(int)

    variants={'ALL_182':pd.Series(True,index=selected.index),'EXCLUDE_FIRST_DAY':selected.first_day==0,'EXCLUDE_NEW_MOTOR_MEETING':selected.new_motor_meeting==0,'EXCLUDE_BOTH':(selected.first_day==0)&(selected.new_motor_meeting==0)}
    out=[]
    for name,mask in variants.items():
        g=selected[mask]
        out.append({'variant':name,'scope':'ALL','month':np.nan,'venue':np.nan,**metrics(g)})
        for mon,z in g.groupby(g.date.str[:7]): out.append({'variant':name,'scope':'MONTH','month':mon,'venue':np.nan,**metrics(z)})
        for ven,z in g.groupby('venue'): out.append({'variant':name,'scope':'VENUE','month':np.nan,'venue':ven,**metrics(z)})
    O=pd.DataFrame(out); O.to_csv(OUT,index=False)
    L=['# v245 corrected first-day / new-motor exclusion audit','', '- Canonical v243 policy reproduced: 182 races.', '- First-day metadata uses BoatraceCSV title CSV when available and official BOAT RACE raceindex as fallback.', '- Day / meeting-start metadata coverage is enforced >=95%; missing metadata is never silently treated as non-first-day.', f'- New-motor proxy remains >=80% of day-1 assigned motor numbers unseen at that venue in prior {LOOKBACK} days when source history is available; unknown meetings are conservatively kept.', '- Dec2025-Aug2026 is in-sample / selection-contaminated, not pristine validation.','',f'- Day metadata coverage: {coverage:.2%}',f'- Meeting-start coverage: {start_coverage:.2%}',f'- Official-web fallback rows: {fallback_count}',f'- New-motor classification coverage: {newmotor_coverage:.2%}','', '|variant|R|hit|ROI|','|---|---:|---:|---:|']
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
