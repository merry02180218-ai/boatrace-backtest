#!/usr/bin/env python3
"""Manual live runner for current 3-head production rule.

Input: live_input_3head.json populated from a pre-deadline screenshot.
Flow: raw exhibition/ST/original values -> v108 feature_row -> v165 refit through prior settled data
-> BUY iff p3head>=0.30 -> v166 direct ordered-pair lambda=1.00 -> Top10.
No result/payout/odds from target race are read.
"""
from __future__ import annotations
import csv,json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from backtest import rows
from analyze_v108_1head_feasibility import feature_row,bycode,st_bias,update_st
from analyze_v166_3head_pair_direct import fit as fit_pair,order as pair_order

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'live_input_3head.json'; SRC=ROOT/'analysis_v108_1head_feasibility.csv'; SCHEMA=ROOT/'analysis_v165_3head_schema.json'
OUT=ROOT/'prediction_v192_3head_live_manual.json'; SUMMARY=ROOT/'summary_v192_3head_live_manual.md'
CUT=.30

def ff(x):
    try:return float(x)
    except:return np.nan

def target(df):
    for c in ['three_head','boat3_win','lane3_win','is_3head','y3']:
        if c in df:return pd.to_numeric(df[c],errors='coerce')
    for c in ['first','winner','first_lane','result_1','head']:
        if c in df:return (pd.to_numeric(df[c],errors='coerce')==3).astype(float)
    raise RuntimeError('no 3-head target')

def exact_prior_bias(hd):
    days=[];d=date(2025,10,1)
    while d<hd:days.append(d);d+=timedelta(days=1)
    got={}
    def one(dd):return dd,rows(f"data/previews/stt/{dd.strftime('%Y/%m/%d')}.csv")
    with ThreadPoolExecutor(max_workers=14) as ex:
        fs=[ex.submit(one,d) for d in days]
        for f in as_completed(fs):
            try:dd,z=f.result();got[dd]=z
            except:pass
    sums=defaultdict(list);allv=[]
    for d in sorted(got):update_st(got[d],sums,allv)
    return st_bias(sums,allv),len(got)

def build_manual_maps(code,j):
    ex=j['exhibition']; st=j['st']; lap=j['lap']; turn=j['turn']; straight=j['straight']; courses=j.get('courses',[1,2,3,4,5,6])
    tk={code:{f'艇{b}_展示タイム':ex[b-1] for b in range(1,7)}}
    sr={f'艇{b}_スタート展示':st[b-1] for b in range(1,7)}
    sr.update({f'艇{b}_コース':courses[b-1] for b in range(1,7)})
    stt={code:sr}
    o={'計測項目1':'一周','計測項目2':'まわり足','計測項目3':'直線'}
    for b in range(1,7):
        o[f'艇{b}_値1']=lap[b-1];o[f'艇{b}_値2']=turn[b-1];o[f'艇{b}_値3']=straight[b-1]
    return tk,stt,{code:o}

def fit_head(src,features,venue_col,hd):
    d=src.copy();d['_date']=pd.to_datetime(d['date'],errors='coerce');d['_y']=target(d)
    d=d[d['_date'].notna() & d['_y'].notna() & (d['_date']<pd.Timestamp(hd))].copy()
    nums=[]
    for c in features:
        if c not in d:continue
        q=pd.to_numeric(d[c],errors='coerce')
        if q.notna().mean()>=.8:d[c]=q;nums.append(c)
    cats=[venue_col] if venue_col and venue_col in d and venue_col not in nums else []
    tr=[]
    if nums:tr.append(('n',Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler())]),nums))
    if cats:tr.append(('c',Pipeline([('i',SimpleImputer(strategy='most_frequent')),('o',OneHotEncoder(handle_unknown='ignore'))]),cats))
    m=Pipeline([('p',ColumnTransformer(tr)),('m',LogisticRegression(C=.35,max_iter=1800))])
    m.fit(d[nums+cats],d['_y'].astype(int));return m,nums,cats,len(d)

def main():
    j=json.loads(INPUT.read_text(encoding='utf-8'));hd=date.fromisoformat(j['date']);venue=str(j['venue']).zfill(2);rno=int(j['race'])
    code=f"{hd:%Y%m%d}{venue}{rno:02d}"; y=hd.strftime('%Y/%m/%d')
    cards=bycode(rows(f'data/programs/race_cards/{y}.csv')); waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    if code not in cards or code not in waku:raise RuntimeError(f'card/waku not available for {code}')
    bias,bias_days=exact_prior_bias(hd);tk,stt,orig=build_manual_maps(code,j)
    row=feature_row(hd.isoformat(),cards[code],waku[code],tk,stt,orig,bias)
    if row is None:raise RuntimeError('entry changed/excluded')
    schema=json.loads(SCHEMA.read_text(encoding='utf-8'));src=pd.read_csv(SRC)
    m,nums,cats,ntrain=fit_head(src,schema['features'],'venue' if 'venue' in src.columns else None,hd)
    x=pd.DataFrame([{c:row.get(c,np.nan) for c in nums+cats}]);p=float(m.predict_proba(x)[0,1])
    hist=[]
    with SRC.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if r.get('date','')<hd.isoformat():hist.append(r)
    pm,pair_n=fit_pair(hist);top10=pair_order(row,pm,1.0)[:10] if p>=CUT else []
    res={'date':hd.isoformat(),'venue':venue,'race':rno,'race_code':code,'boat3':cards[code].get('艇3_選手名',''),'p3head':p,'cut':CUT,'decision':'BUY' if p>=CUT else 'SKIP','v166_lambda':1.0,'top10':top10,'head_train_rows':ntrain,'pair_train_3wins':pair_n,'prior_st_bias_days':bias_days,'manual_input':j}
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
    L=[f"# v192 live 3-head {hd} {venue} {rno}R",'',f"- boat3: **{res['boat3']}**",f"- v165 p3head: **{100*p:.2f}%**",f"- decision: **{res['decision']}** (cut 30%)",f"- v166 lambda: **1.00**",f"- head train rows: {ntrain}",f"- pair train 3-head wins: {pair_n}",f"- prior ST-bias days: {bias_days}",'','## Top10']
    L += [f"{i}. {t}" for i,t in enumerate(top10,1)] if top10 else ['- SKIP: no tickets']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
