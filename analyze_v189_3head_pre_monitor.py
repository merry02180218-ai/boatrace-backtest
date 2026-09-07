#!/usr/bin/env python3
"""v189: pre-exhibition monitoring layer for canonical v165 -> v166 3-head production.

Purpose
- PRE is ONLY a monitoring shortlist before exhibition, never BUY / formal p3head.
- Label is whether the already-frozen monthly-WF v165 output later reaches p3head >= .30.
- PRE features are rebuilt with current-race TKZ/STT/original exhibition EMPTY, so no same-race
  exhibition/result/payout/odds enters PRE.
- Temporal validation: train June, choose the cutoff on July, untouched test August.
- Runtime 2026-09-09 uses BOAT RACE official racelist + strictly pre-public/prior-frame data.
- After exhibition the canonical decision remains actual v165 p3head>=.30 -> v166 Top10.
"""
from __future__ import annotations
import csv, io, re, requests
from pathlib import Path
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backtest import rows
from analyze_v108_1head_feasibility import feature_row, bycode

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
V165=ROOT/'analysis_v165_3head_monthly_walkforward.csv'
OUT_HIST=ROOT/'analysis_v189_3head_pre_monitor_validation.csv'
OUT_PRE=ROOT/'prediction_v189_20260909_3head_pre_monitor.csv'
SUMMARY=ROOT/'summary_v189_3head_pre_monitor.md'
HD=date(2026,9,9); HD8='20260909'
TARGET_RECALL=.85
PRE_FS=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all'
]
VENUES={'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖',
 '07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江',
 '13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山',
 '19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}
BASECSV='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-research/1.0)'}

def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def read_csv(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def pipe():
    pre=ColumnTransformer([
      ('n',StandardScaler(),PRE_FS),
      ('v',OneHotEncoder(handle_unknown='ignore'),['venue'])])
    return Pipeline([('pre',pre),('lr',LogisticRegression(C=.35,max_iter=1800,class_weight='balanced'))])

def frame(rs):
    return pd.DataFrame([{**{k:ff(r.get(k),0) for k in PRE_FS},'venue':str(r.get('venue','')).zfill(2)} for r in rs])

def fit(rs):
    m=pipe();m.fit(frame(rs),[ii(r['formal_v165_candidate']) for r in rs]);return m

def pred(m,rs):return m.predict_proba(frame(rs))[:,1] if rs else np.array([])

def metrics(rs,pp,cut):
    y=np.asarray([ii(r['formal_v165_candidate']) for r in rs]);sel=pp>=cut
    pos=int(y.sum());tp=int((sel&(y==1)).sum());nsel=int(sel.sum())
    recall=tp/pos if pos else 0; precision=tp/nsel if nsel else 0
    return {'R':len(rs),'positives':pos,'selected':nsel,'shortlist_rate':nsel/len(rs) if rs else 0,
            'recall':recall,'precision':precision}

def choose_cut(rs,pp):
    y=np.asarray([ii(r['formal_v165_candidate']) for r in rs]);pos=int(y.sum())
    if not pos:return .5
    vals=sorted(set(float(x) for x in pp))
    good=[]
    for t in vals:
        sel=pp>=t; rec=float((sel&(y==1)).sum())/pos
        if rec>=TARGET_RECALL:good.append(t)
    return max(good) if good else min(vals)

def fetch_hist(d):
    y=d.strftime('%Y/%m/%d')
    return d,rows(f'data/programs/race_cards/{y}.csv'),rows(f'data/programs/waku10/{y}.csv')

def build_historical_pre():
    src=pd.read_csv(SRC)
    lab=pd.read_csv(V165)
    # v165 source_index is the original row index in analysis_v108.
    wanted=[]
    for _,z in lab.iterrows():
        ix=int(z['source_index'])
        if ix<0 or ix>=len(src):continue
        s=src.iloc[ix]
        wanted.append({'source_index':ix,'date':str(z['date'])[:10],'month':str(z['month']),
                       'race_code':str(s.get('race_code','')),'p3head':float(z['p3head']),
                       'y3head':int(z.get('y3head',0)),
                       'formal_v165_candidate':int(float(z['p3head'])>=.30)})
    days=sorted({date.fromisoformat(z['date']) for z in wanted})
    got={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(fetch_hist,d) for d in days]
        for i,f in enumerate(as_completed(fs),1):
            try:d,c,w=f.result();got[d]=(c,bycode(w))
            except Exception as e:print('hist fetch fail',e,flush=True)
            if i%20==0:print('historical PRE days',i,'/',len(days),flush=True)
    out=[]; miss=0
    byday={}
    for d,(cards,wm) in got.items():
        byday[d]={c.get('レースコード',''):(c,wm.get(c.get('レースコード',''))) for c in cards}
    zeros={b:0.0 for b in range(1,7)}
    for z in wanted:
        d=date.fromisoformat(z['date']); pair=byday.get(d,{}).get(z['race_code'])
        if not pair or pair[1] is None:miss+=1;continue
        card,w=pair
        try:r=feature_row(z['date'],card,w,{},{},{},zeros)
        except Exception:r=None
        if r is None:miss+=1;continue
        q={k:r.get(k,0) for k in PRE_FS};q['venue']=r.get('venue','');q.update(z);out.append(q)
    return out,miss

def get_text(url,timeout=20):
    r=requests.get(url,headers=UA,timeout=timeout);r.raise_for_status();return r.text

def csv_rows(url):
    try:
        r=requests.get(url,headers=UA,timeout=15)
        if r.status_code!=200:return []
        return list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
    except Exception:return []

def racer_names():
    txt=get_text('https://raw.githubusercontent.com/ryuriki/boatrace-v2/main/config/racers_name.yaml')
    out={}
    for ln in txt.splitlines():
        mm=re.match(r"'?(\d{4})'?:\s*(.+?)\s*$",ln)
        if mm:out[int(mm.group(1))]=mm.group(2).strip()
    return out

def parse_race(jcd,rno,names):
    url=f'https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={HD8}'
    soup=BeautifulSoup(get_text(url),'html.parser');tables=soup.find_all('div',class_='table1')
    if len(tables)<2:raise ValueError('racelist table missing')
    tds=tables[0].find('tbody').find_all('td'); deadline=tds[rno].get_text(strip=True) if len(tds)>rno else ''
    bodies=tables[1].find_all('tbody')
    if len(bodies)<6:raise ValueError('lane bodies missing')
    lanes={}
    for lane in range(1,7):
        cells=bodies[lane-1].find_all('td');info=cells[2].find_all('div',class_='is-fs11')
        racer=info[0].get_text(strip=True);rid=ii(racer.split('/')[0].strip());grade=racer.split('/')[1].strip() if '/' in racer else ''
        c3=[x.strip() for x in cells[3].get_text('\n',strip=True).split('\n') if x.strip()]
        zn=[x.strip() for x in cells[4].get_text('\n',strip=True).split('\n') if x.strip()]
        jl=[x.strip() for x in cells[5].get_text('\n',strip=True).split('\n') if x.strip()]
        mo=[x.strip() for x in cells[6].get_text('\n',strip=True).split('\n') if x.strip()]
        lanes[lane]={'rid':rid,'name':names.get(rid,str(rid)),'grade':grade,
          'nst':ff(c3[2] if len(c3)>2 else .20,.20),'wr':ff(zn[0] if zn else 0),
          'local':ff(jl[0] if jl else 0),'motor2':ff(mo[1] if len(mo)>1 else 0),'motor3':ff(mo[2] if len(mo)>2 else 0)}
    return {'jcd':jcd,'rno':rno,'deadline':deadline,'lanes':lanes}

def discover(names):
    active=[]
    with ThreadPoolExecutor(max_workers=12) as ex:
        fs={ex.submit(parse_race,j,1,names):j for j in VENUES}
        for f in as_completed(fs):
            j=fs[f]
            try:f.result();active.append(j)
            except Exception:pass
    return sorted(active)

def fetch_prior_day(d):
    y=d.strftime('%Y/%m/%d');cards=csv_rows(BASECSV+f'data/programs/race_cards/{y}.csv');w10=csv_rows(BASECSV+f'data/programs/waku10/{y}.csv');wm=bycode(w10);out=[]
    for c in cards:
        w=wm.get(c.get('レースコード',''),{})
        for b in range(1,7):
            rid=ii(c.get(f'艇{b}_登録番号'))
            if not rid:continue
            z={'waku_wr':w.get(f'艇{b}_枠番別勝率',''),'waku_st':w.get(f'艇{b}_枠番別平均ST',''),'waku_sr':w.get(f'艇{b}_枠番別平均スタート順','')}
            for k in range(1,11):z[f'past{k}']=w.get(f'艇{b}_過去{k}走_着順','')
            out.append((rid,b,z))
    return d,out

def latest_same_frame(days=60):
    ds=[HD-timedelta(days=i) for i in range(1,days+1)];got={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(fetch_prior_day,d) for d in ds]
        for f in as_completed(fs):
            try:d,z=f.result();got[d]=z
            except Exception:pass
    lookup={}
    for d in sorted(got,reverse=True):
        for rid,b,z in got[d]:lookup.setdefault((rid,b),z)
    return lookup

def synthetic(r,lookup):
    code=f'{HD8}{r["jcd"]}{r["rno"]:02d}';card={'レースコード':code,'レース場コード':r['jcd'],'レース回':str(r['rno'])};w={'レースコード':code}
    for b,z in r['lanes'].items():
        card[f'艇{b}_登録番号']=str(z['rid']);card[f'艇{b}_選手名']=z['name'];card[f'艇{b}_級別']=z['grade'];card[f'艇{b}_全国平均ST']=str(z['nst']);card[f'艇{b}_全国勝率']=str(z['wr']);card[f'艇{b}_当地勝率']=str(z['local']);card[f'艇{b}_モーター2連対率']=str(z['motor2']);card[f'艇{b}_モーター3連対率']=str(z['motor3'])
        h=lookup.get((z['rid'],b),{});w[f'艇{b}_枠番別勝率']=h.get('waku_wr','') or str(z['wr']);w[f'艇{b}_枠番別平均ST']=h.get('waku_st','') or str(z['nst']);w[f'艇{b}_枠番別平均スタート順']=h.get('waku_sr','') or '3.5'
        for k in range(1,11):w[f'艇{b}_過去{k}走_着順']=h.get(f'past{k}','')
    return card,w

def runtime_scan(final_model,cut):
    names=racer_names();active=discover(names);races=[];errs=[]
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(parse_race,j,r,names):(j,r) for j in active for r in range(1,13)}
        for f in as_completed(fs):
            j,r=fs[f]
            try:races.append(f.result())
            except Exception as e:errs.append((j,r,str(e)))
    lookup=latest_same_frame();pre=[];meta=[];zeros={b:0.0 for b in range(1,7)}
    for r in races:
        card,w=synthetic(r,lookup)
        try:fr=feature_row(HD.isoformat(),card,w,{},{},{},zeros)
        except Exception:fr=None
        if fr is None:continue
        q={k:fr.get(k,0) for k in PRE_FS};q['venue']=r['jcd'];pre.append(q);meta.append(r)
    pp=pred(final_model,pre);out=[]
    for r,p in zip(meta,pp):
        out.append({'venue':r['jcd'],'venue_name':VENUES[r['jcd']],'race':r['rno'],'deadline':r['deadline'],
          'boat3_name':r['lanes'][3]['name'],'boat3_grade':r['lanes'][3]['grade'],'pre_monitor_prob':float(p),
          'pre_cut':cut,'pre_watch':int(p>=cut),'status':'PRE_WATCH_NOT_BUY' if p>=cut else 'PRE_SKIP'})
    out.sort(key=lambda z:(z['deadline'] or '99:99',z['venue'],z['race']))
    return out,active,errs

def main():
    hist,miss=build_historical_pre()
    if not hist:raise SystemExit('no historical PRE rows')
    june=[r for r in hist if r['month']=='2026-06'];july=[r for r in hist if r['month']=='2026-07'];aug=[r for r in hist if r['month']=='2026-08']
    if min(sum(ii(r['formal_v165_candidate']) for r in z) for z in [june,july,aug])<2:raise SystemExit('too few formal positives')
    m1=fit(june);pv=pred(m1,july);cut=choose_cut(july,pv);mv=metrics(july,pv,cut);pt=pred(m1,aug);mt=metrics(aug,pt,cut)
    # Conservative adoption gate for a monitoring layer: retain >=80% of unseen formal candidates
    # while asking to watch no more than 35% of all races.
    passed=mt['recall']>=.80 and mt['shortlist_rate']<=.35
    for r,p in zip(july,pv):r['pre_prob_eval']=float(p);r['eval_split']='validation'
    for r,p in zip(aug,pt):r['pre_prob_eval']=float(p);r['eval_split']='untouched_test'
    pd.DataFrame(july+aug).to_csv(OUT_HIST,index=False,encoding='utf-8-sig')
    # Runtime model may use all settled Jun-Aug labels; cutoff remains frozen from July.
    mf=fit(hist);runtime,active,errs=runtime_scan(mf,cut)
    pd.DataFrame(runtime).to_csv(OUT_PRE,index=False,encoding='utf-8-sig')
    cand=[z for z in runtime if z['pre_watch']]
    now=datetime.now(ZoneInfo('Asia/Tokyo'))
    L=['# v189 3号艇 v165-aligned PRE monitor','',
      '**PREは監視候補でありBUYではない。正式候補は展示後の actual v165 p3head>=30% のみ。**','',
      '## 時系列検証','',f'- historical PRE rows: **{len(hist):,}R** / join missing **{miss}R**',
      f'- PRE label: eventual monthly-WF **v165 p3head>=30%**',f'- cutoff selection target: July recall >= **{100*TARGET_RECALL:.0f}%**',f'- selected cutoff: **{cut:.6f}**',
      f'- July validation: R {mv["R"]}, formal {mv["positives"]}, watch {mv["selected"]} ({100*mv["shortlist_rate"]:.1f}%), recall {100*mv["recall"]:.1f}%, precision {100*mv["precision"]:.1f}%',
      f'- August untouched: R {mt["R"]}, formal {mt["positives"]}, watch {mt["selected"]} ({100*mt["shortlist_rate"]:.1f}%), recall {100*mt["recall"]:.1f}%, precision {100*mt["precision"]:.1f}%',
      f'- PRE validation gate: **{"PASS" if passed else "FAIL"}** (August recall>=80% and watch<=35%)','',
      '## 2026-09-09 公式サイト PRE監視候補','',f'- scan JST: **{now:%Y-%m-%d %H:%M:%S}**',f'- active venues: **{len(active)}** ({", ".join(VENUES[j] for j in active)})',f'- official races scored: **{len(runtime)}R**',f'- fetch errors: **{len(errs)}R**',f'- PRE watch: **{len(cand)}R**','',
      '|締切|場|R|3号艇|級|PRE monitor p|','|---|---|---:|---|---|---:|']
    for z in cand:L.append(f"|{z['deadline']}|{z['venue_name']}|{z['race']}R|{z['boat3_name']}|{z['boat3_grade']}|{100*z['pre_monitor_prob']:.1f}%|")
    if not cand:L.append('|-|-|-|-|-|-|')
    L += ['','### 運用','',
      '1. PRE_WATCHだけを展示後確認対象にする。PRE scoreはp3headではない。',
      '2. 展示進入で3号艇が3コースを外れたら除外。',
      '3. TKZ/STT/original exhibition取得後、実際のv165を通す。',
      '4. actual v165 p3head>=30%だけ正式候補。',
      '5. 正式候補だけv166 direct lambda=1.00でTop10。',
      '6. 結果・払戻を見る前にfreeze。','',
      '※ PRE段階は未計算の正式p3headなので、買い目は出さない。']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
