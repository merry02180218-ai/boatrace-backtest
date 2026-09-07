#!/usr/bin/env python3
"""v190: clean PRE-only monitor for canonical v165 -> v166 3-head production.

PRE is monitoring only, never formal p3head/BUY.
Training features use race-card + waku10 fields only; no TKZ/STT/original exhibition,
result, payout or odds. Label is eventual frozen monthly-WF v165 p3head >= 0.30.
Because BoatraceCSV June program files are currently unavailable, temporal evaluation is:
Jul 1-20 train -> Jul 21-31 cutoff tuning -> Aug untouched test.
Runtime target: 2026-09-09 official BOAT RACE racelist + prior same-frame waku history.
Canonical final remains actual v165 p3head>=.30 -> v166 lambda=1.00 Top10.
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

ROOT=Path(__file__).resolve().parent
V165=ROOT/'analysis_v165_3head_monthly_walkforward.csv'; SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v190_3head_clean_pre_validation.csv'; PRED=ROOT/'prediction_v190_20260909_3head_pre_monitor.csv'; SUMMARY=ROOT/'summary_v190_3head_clean_pre_monitor.md'
HD=date(2026,9,9); HD8='20260909'; TARGET_RECALL=.85
BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-research/1.0)'}
VENUES={f'{i:02d}':n for i,n in enumerate(['','桐生','戸田','江戸川','平和島','多摩川','浜名湖','蒲郡','常滑','津','三国','びわこ','住之江','尼崎','鳴門','丸亀','児島','宮島','徳山','下関','若松','芦屋','福岡','唐津','大村']) if i}
GRADE={'A1':1.0,'A2':.75,'B1':.45,'B2':.20}

def ff(x,d=0.0):
    try:return float(str(x).replace('%',''))
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def getcsv(url):
    try:
        r=requests.get(url,headers=UA,timeout=20)
        if r.status_code!=200:return []
        return list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
    except Exception:return []
def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def past_stats(w,b):
    vals=[]
    for k in range(1,11):
        s=str(w.get(f'艇{b}_過去{k}走_着順','')).strip()
        m=re.search(r'[1-6]',s)
        if m: vals.append(int(m.group()))
    if not vals:return .0,.0,0
    return sum(v==1 for v in vals)/len(vals),sum(v<=3 for v in vals)/len(vals),len(vals)

def raw_features(card,w):
    q={'venue':str(card.get('レース場コード','')).zfill(2)}
    for b in range(1,7):
        pre=f'b{b}_'
        q[pre+'grade']=GRADE.get(str(card.get(f'艇{b}_級別','')).strip(),.35)
        q[pre+'wr']=ff(card.get(f'艇{b}_全国勝率'))
        q[pre+'local']=ff(card.get(f'艇{b}_当地勝率'))
        q[pre+'nst']=ff(card.get(f'艇{b}_全国平均ST'),.20)
        q[pre+'m2']=ff(card.get(f'艇{b}_モーター2連対率'))
        q[pre+'m3']=ff(card.get(f'艇{b}_モーター3連対率'))
        q[pre+'wwr']=ff(w.get(f'艇{b}_枠番別勝率'),q[pre+'wr'])
        q[pre+'wst']=ff(w.get(f'艇{b}_枠番別平均ST'),q[pre+'nst'])
        q[pre+'wsr']=ff(w.get(f'艇{b}_枠番別平均スタート順'),3.5)
        p1,p3,n=past_stats(w,b);q[pre+'past1']=p1;q[pre+'past3']=p3;q[pre+'pastn']=n
    for b in [1,2,4,5,6]:
        q[f'd3{b}_wr']=q['b3_wr']-q[f'b{b}_wr'];q[f'd3{b}_local']=q['b3_local']-q[f'b{b}_local']
        q[f'd3{b}_nst']=q[f'b{b}_nst']-q['b3_nst'];q[f'd3{b}_m2']=q['b3_m2']-q[f'b{b}_m2']
        q[f'd3{b}_wwr']=q['b3_wwr']-q[f'b{b}_wwr'];q[f'd3{b}_wst']=q[f'b{b}_wst']-q['b3_wst']
    return q

NUM=[f'b{b}_{k}' for b in range(1,7) for k in ['grade','wr','local','nst','m2','m3','wwr','wst','wsr','past1','past3','pastn']]
NUM += [f'd3{b}_{k}' for b in [1,2,4,5,6] for k in ['wr','local','nst','m2','wwr','wst']]
def frame(rs):return pd.DataFrame([{**{k:ff(r.get(k)) for k in NUM},'venue':r.get('venue','')} for r in rs])
def fit(rs):
    pre=ColumnTransformer([('n',StandardScaler(),NUM),('v',OneHotEncoder(handle_unknown='ignore'),['venue'])])
    m=Pipeline([('pre',pre),('lr',LogisticRegression(C=.30,max_iter=1800,class_weight='balanced'))]);m.fit(frame(rs),[ii(r['label']) for r in rs]);return m
def pred(m,rs):return m.predict_proba(frame(rs))[:,1] if rs else np.array([])
def choose_cut(rs,p):
    y=np.array([ii(r['label']) for r in rs]);pos=y.sum()
    if not pos:return .5
    good=[]
    for t in sorted(set(map(float,p))):
        sel=p>=t; rec=((sel)&(y==1)).sum()/pos
        if rec>=TARGET_RECALL:good.append(t)
    return max(good) if good else min(map(float,p))
def metric(rs,p,cut):
    y=np.array([ii(r['label']) for r in rs]);sel=p>=cut;pos=int(y.sum());tp=int((sel&(y==1)).sum());ns=int(sel.sum())
    return len(rs),pos,ns,(tp/pos if pos else 0),(tp/ns if ns else 0),(ns/len(rs) if rs else 0)

def labels():
    lab=pd.read_csv(V165);src=pd.read_csv(SRC);out={}
    for _,z in lab.iterrows():
        ix=int(z.source_index)
        if 0<=ix<len(src):
            code=str(src.iloc[ix].get('race_code',''));out[code]={'p3head':float(z.p3head),'label':int(float(z.p3head)>=.30),'month':str(z.month),'date':str(z.date)[:10]}
    return out

def fetch_day(d):
    y=d.strftime('%Y/%m/%d');cards=getcsv(BASE+f'data/programs/race_cards/{y}.csv');wm=bycode(getcsv(BASE+f'data/programs/waku10/{y}.csv'));return d,cards,wm

def hist_rows():
    labs=labels();days=[];d=date(2026,7,1)
    while d<=date(2026,8,31):days.append(d);d+=timedelta(days=1)
    out=[];missing=0
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(fetch_day,d) for d in days]
        for f in as_completed(fs):
            d,cards,wm=f.result()
            for c in cards:
                code=c.get('レースコード','');lab=labs.get(code);w=wm.get(code)
                if not lab or not w:missing+=1;continue
                q=raw_features(c,w);q.update(lab);q['race_code']=code;out.append(q)
    return out,missing

def get_text(u):r=requests.get(u,headers=UA,timeout=20);r.raise_for_status();return r.text
def racer_names():
    txt=get_text('https://raw.githubusercontent.com/ryuriki/boatrace-v2/main/config/racers_name.yaml');o={}
    for ln in txt.splitlines():
        m=re.match(r"'?(\d{4})'?:\s*(.+?)\s*$",ln)
        if m:o[int(m.group(1))]=m.group(2).strip()
    return o

def parse_race(jcd,rno,names):
    u=f'https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={HD8}';s=BeautifulSoup(get_text(u),'html.parser');tabs=s.find_all('div',class_='table1')
    if len(tabs)<2:raise ValueError('no race')
    tds=tabs[0].find('tbody').find_all('td');dl=tds[rno].get_text(strip=True) if len(tds)>rno else ''
    bodies=tabs[1].find_all('tbody');lanes={}
    if len(bodies)<6:raise ValueError('lanes')
    for b in range(1,7):
        cells=bodies[b-1].find_all('td');info=cells[2].find_all('div',class_='is-fs11');rt=info[0].get_text(strip=True);rid=ii(rt.split('/')[0]);gr=rt.split('/')[1].strip() if '/' in rt else ''
        c3=[x.strip() for x in cells[3].get_text('\n',strip=True).split('\n') if x.strip()];zn=[x.strip() for x in cells[4].get_text('\n',strip=True).split('\n') if x.strip()];jl=[x.strip() for x in cells[5].get_text('\n',strip=True).split('\n') if x.strip()];mo=[x.strip() for x in cells[6].get_text('\n',strip=True).split('\n') if x.strip()]
        lanes[b]={'rid':rid,'name':names.get(rid,str(rid)),'grade':gr,'nst':ff(c3[2] if len(c3)>2 else .20,.20),'wr':ff(zn[0] if zn else 0),'local':ff(jl[0] if jl else 0),'m2':ff(mo[1] if len(mo)>1 else 0),'m3':ff(mo[2] if len(mo)>2 else 0)}
    return {'jcd':jcd,'rno':rno,'deadline':dl,'lanes':lanes}
def active(names):
    a=[]
    with ThreadPoolExecutor(max_workers=12) as ex:
        fs={ex.submit(parse_race,j,1,names):j for j in VENUES}
        for f,j in [(f,j) for f,j in fs.items()]:
            try:f.result();a.append(j)
            except:pass
    return sorted(a)
def prior_lookup(days=60):
    ds=[HD-timedelta(days=i) for i in range(1,days+1)];got={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(fetch_day,d) for d in ds]
        for f in as_completed(fs):
            d,cards,wm=f.result();vals=[]
            for c in cards:
                w=wm.get(c.get('レースコード',''),{})
                for b in range(1,7):
                    rid=ii(c.get(f'艇{b}_登録番号')); 
                    if rid: vals.append((rid,b,{k:v for k,v in w.items() if k.startswith(f'艇{b}_')}))
            got[d]=vals
    look={}
    for d in sorted(got,reverse=True):
        for rid,b,z in got[d]:look.setdefault((rid,b),z)
    return look
def synthetic(r,look):
    code=f'{HD8}{r["jcd"]}{r["rno"]:02d}';c={'レースコード':code,'レース場コード':r['jcd'],'レース回':str(r['rno'])};w={'レースコード':code}
    for b,z in r['lanes'].items():
        c[f'艇{b}_登録番号']=z['rid'];c[f'艇{b}_選手名']=z['name'];c[f'艇{b}_級別']=z['grade'];c[f'艇{b}_全国平均ST']=z['nst'];c[f'艇{b}_全国勝率']=z['wr'];c[f'艇{b}_当地勝率']=z['local'];c[f'艇{b}_モーター2連対率']=z['m2'];c[f'艇{b}_モーター3連対率']=z['m3']
        h=look.get((z['rid'],b),{});w.update(h);w[f'艇{b}_枠番別勝率']=h.get(f'艇{b}_枠番別勝率',z['wr']);w[f'艇{b}_枠番別平均ST']=h.get(f'艇{b}_枠番別平均ST',z['nst']);w[f'艇{b}_枠番別平均スタート順']=h.get(f'艇{b}_枠番別平均スタート順',3.5)
    return c,w

def runtime(model,cut):
    names=racer_names();avs=active(names);races=[];errs=[]
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(parse_race,j,r,names):(j,r) for j in avs for r in range(1,13)}
        for f in as_completed(fs):
            j,r=fs[f]
            try:races.append(f.result())
            except Exception as e:errs.append((j,r,str(e)))
    look=prior_lookup();xs=[];meta=[]
    for r in races:
        c,w=synthetic(r,look);xs.append(raw_features(c,w));meta.append(r)
    pp=pred(model,xs);out=[]
    for r,p in zip(meta,pp):out.append({'venue':r['jcd'],'venue_name':VENUES[r['jcd']],'race':r['rno'],'deadline':r['deadline'],'boat3_name':r['lanes'][3]['name'],'boat3_grade':r['lanes'][3]['grade'],'pre_monitor_prob':float(p),'pre_cut':cut,'pre_watch':int(p>=cut),'status':'PRE_WATCH_NOT_BUY' if p>=cut else 'PRE_SKIP'})
    out.sort(key=lambda z:(z['deadline'] or '99:99',z['venue'],z['race']));return out,avs,errs

def main():
    h,miss=hist_rows();tr=[r for r in h if r['date']<='2026-07-20'];tu=[r for r in h if '2026-07-21'<=r['date']<='2026-07-31'];te=[r for r in h if r['month']=='2026-08']
    if min(sum(r['label'] for r in z) for z in [tr,tu,te])<5:raise SystemExit(f'insufficient positives train/tune/test: {[sum(r["label"] for r in z) for z in [tr,tu,te]]}')
    m=fit(tr);pu=pred(m,tu);cut=choose_cut(tu,pu);mu=metric(tu,pu,cut);pe=pred(m,te);me=metric(te,pe,cut)
    passed=me[3]>=.80 and me[5]<=.35
    for r,p in zip(tu,pu):r['pre_prob_eval']=p;r['split']='tune'
    for r,p in zip(te,pe):r['pre_prob_eval']=p;r['split']='untouched_aug'
    pd.DataFrame(tu+te).to_csv(OUT,index=False,encoding='utf-8-sig')
    final=fit(h);rt,avs,errs=runtime(final,cut);pd.DataFrame(rt).to_csv(PRED,index=False,encoding='utf-8-sig');cand=[z for z in rt if z['pre_watch']]
    now=datetime.now(ZoneInfo('Asia/Tokyo'))
    L=['# v190 clean 3-head PRE monitor','', '**PREは監視候補のみ。正式候補は展示後 actual v165 p3head>=30%。**','', '## No-leak design','- race-card + waku10 only','- no current exhibition / result / payout / odds','- label: frozen monthly-WF v165 p3head>=30%','', '## Temporal validation',f'- historical rows: **{len(h)}** / missing {miss}',f'- train Jul1-20: R {len(tr)}, formal {sum(r["label"] for r in tr)}',f'- tune Jul21-31: R {mu[0]}, formal {mu[1]}, watch {mu[2]} ({100*mu[5]:.1f}%), recall {100*mu[3]:.1f}%, precision {100*mu[4]:.1f}%',f'- frozen cut: **{cut:.6f}**',f'- untouched Aug: R {me[0]}, formal {me[1]}, watch {me[2]} ({100*me[5]:.1f}%), recall {100*me[3]:.1f}%, precision {100*me[4]:.1f}%',f'- gate: **{"PASS" if passed else "FAIL"}** (Aug recall>=80%, watch<=35%)','', '## 2026-09-09 PRE monitor',f'- scan JST: **{now:%Y-%m-%d %H:%M:%S}**',f'- active venues: **{len(avs)}**',f'- scored: **{len(rt)}R** / errors {len(errs)}R',f'- PRE watch: **{len(cand)}R**','', '|締切|場|R|3号艇|級|PRE p|','|---|---|---:|---|---|---:|']
    for z in cand:L.append(f"|{z['deadline']}|{z['venue_name']}|{z['race']}R|{z['boat3_name']}|{z['boat3_grade']}|{100*z['pre_monitor_prob']:.1f}%|")
    if not cand:L.append('|-|-|-|-|-|-|')
    L += ['','## Canonical operation','PRE watch -> exhibition -> actual v165 p3head>=30% -> v166 lambda=1.00 Top10. PRE score is never p3head and never BUY.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
