#!/usr/bin/env python3
# trigger: 20260914-head4-boat3-waku10-decomposition-cache
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backtest import rows,i
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview,resistance12
from backtest_v5_ev import process_features
from backtest_v18_core45 import features4
from analyze_v23_20260902_daypreview import by_code,original_scores,rank_score
from analyze_v33_tilt_effect import tiltval

ROOT=Path(__file__).resolve().parent
START=date(2025,12,1); END=date(2026,8,31)
PRELOAD_START=START-timedelta(days=120)
MONTHS=[f'2026-{m:02d}' for m in range(2,9)]
VARIANTS=('FULL_WAKU10','NO_WAKU10','CORE_WAKU10','B3_ONLY','B4_ONLY','WR_ONLY','ST_ONLY','SR_ONLY','WR_ST','WR_SR','ST_SR','B3_WR_ONLY','B3_ST_ONLY','B3_SR_ONLY','B3_WR_ST','B3_WR_SR','B3_ST_SR','B3_ALL')

def safe(v,default=0.0):
    try:
        x=float(v); return x if np.isfinite(x) else default
    except:return default

def raw_features(x,s4):
    fr=features4(x); b1,b2,b3,b4=x[1],x[2],x[3],x[4]
    return {'legacy_score4':safe(s4),'racer4':safe(fr['4選手力']),'hist_st_edge_4v3':safe(fr['4_ST優位']),'wall3_weak':safe(fr['3壁弱さ']),'inner12_resistance':safe(resistance12(x)),'motor4_2ren':safe(b4.get('motor2')),'motor4_hist':safe(b4.get('mhist')),'turnfoot4_prior':safe(b4.get('turnfoot')),'past_win4':safe(b4.get('past_win')),'b3_waku_wr':safe(b3.get('waku_wr'),np.nan),'b3_waku_st':safe(b3.get('waku_st'),np.nan),'b3_waku_sr':safe(b3.get('waku_sr'),np.nan),'b4_waku_wr':safe(b4.get('waku_wr'),np.nan),'b4_waku_st':safe(b4.get('waku_st'),np.nan),'b4_waku_sr':safe(b4.get('waku_sr'),np.nan),'b1_waku_wr':safe(b1.get('waku_wr'),np.nan),'b2_waku_wr':safe(b2.get('waku_wr'),np.nan)}

def post_features(code,tkz,stt,orig):
    sr=stt.get(code,{});orr=orig.get(code,{});tr=tkz.get(code,{})
    stvals={b:safe(sr.get(f'艇{b}_スタート展示'),np.nan) for b in range(1,7)}
    st_rank=rank_score(stvals,4,True) if any(np.isfinite(v) for v in stvals.values()) else .5
    os=original_scores(orr,4)
    return {'ex_st_rank4':safe(st_rank,.5),'ex_st_4':safe(sr.get('艇4_スタート展示'),.20),'ex_st_edge_4v3':safe(sr.get('艇3_スタート展示'),.20)-safe(sr.get('艇4_スタート展示'),.20),'orig_straight4':safe(os.get('straight'),.5),'orig_lap4':safe(os.get('lap'),.5),'orig_turn4':safe(os.get('turn'),.5),'tilt4':safe(tiltval(tr.get('艇4_チルト')),0.0)}

def cols_for(variant):
    base=['racer4','motor4_2ren','motor4_hist','turnfoot4_prior']
    full=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
    groups={'B3_ONLY':['b3_waku_wr','b3_waku_st','b3_waku_sr'],'B4_ONLY':['b4_waku_wr','b4_waku_st','b4_waku_sr'],'WR_ONLY':['b3_waku_wr','b4_waku_wr'],'ST_ONLY':['b3_waku_st','b4_waku_st'],'SR_ONLY':['b3_waku_sr','b4_waku_sr'],'WR_ST':['b3_waku_wr','b4_waku_wr','b3_waku_st','b4_waku_st'],'WR_SR':['b3_waku_wr','b4_waku_wr','b3_waku_sr','b4_waku_sr'],'ST_SR':['b3_waku_st','b4_waku_st','b3_waku_sr','b4_waku_sr'],'CORE_WAKU10':['b3_waku_wr','b3_waku_st','b3_waku_sr','b4_waku_wr','b4_waku_st','b4_waku_sr'],'B3_WR_ONLY':['b3_waku_wr'],'B3_ST_ONLY':['b3_waku_st'],'B3_SR_ONLY':['b3_waku_sr'],'B3_WR_ST':['b3_waku_wr','b3_waku_st'],'B3_WR_SR':['b3_waku_wr','b3_waku_sr'],'B3_ST_SR':['b3_waku_st','b3_waku_sr'],'B3_ALL':['b3_waku_wr','b3_waku_st','b3_waku_sr']}
    if variant=='FULL_WAKU10': pre=full
    elif variant=='NO_WAKU10': pre=base
    elif variant in groups: pre=base+groups[variant]
    else: raise ValueError(variant)
    post=pre+['ex_st_rank4','ex_st_4','ex_st_edge_4v3','orig_straight4','orig_lap4','orig_turn4','tilt4']
    return pre,post

def make_model(cols):
    prep=ColumnTransformer([('n',Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler())]),cols)])
    return Pipeline([('p',prep),('m',LogisticRegression(C=.35,max_iter=1800,class_weight=None))])

def build_data():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<START:
        ingest_motor(hist,seen,d)
        if d>=START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    data=[]
    while d<=END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        tkz=by_code(f'data/previews/tkz/{ymd}.csv');stt=by_code(f'data/previews/stt/{ymd}.csv');orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
        frozen=[]
        for r,x,s4,s5,dc in feats:
            z={'date':str(d),'race_code':r['レースコード'],'venue':str(r.get('レース場コード','')).zfill(2)};z.update(raw_features(x,s4));z.update(post_features(r['レースコード'],tkz,stt,orig));frozen.append(z)
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            rr=res.get(z['race_code'],{});z['y4head']=int(i(rr.get('1着_艇番'))==4);z['kimarite']=(rr.get('決まり手') or '').strip();data.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    df=pd.DataFrame(data);df['_date']=pd.to_datetime(df.date);return df

def load_or_build_data(cache_path):
    if not cache_path:
        return build_data()
    p=Path(cache_path)
    if p.is_file():
        df=pd.read_pickle(p)
        if '_date' not in df.columns: df['_date']=pd.to_datetime(df.date)
        print(f'common feature cache HIT: {p} rows={len(df)}')
        return df
    df=build_data();p.parent.mkdir(parents=True,exist_ok=True);df.to_pickle(p)
    print(f'common feature cache MISS->WRITE: {p} rows={len(df)}')
    return df

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--variant',choices=VARIANTS,required=True);ap.add_argument('--out',default='analysis_v250_4head_rebuild_baseline.csv');ap.add_argument('--meta',default=None);ap.add_argument('--data-cache',default=None);a=ap.parse_args()
    pre_cols,post_cols=cols_for(a.variant);df=load_or_build_data(a.data_cache);out=[];diag=[]
    for mon in MONTHS:
        m=pd.Timestamp(mon+'-01');e=m+pd.offsets.MonthBegin(1);tr=df[df._date<m].copy();te=df[(df._date>=m)&(df._date<e)].copy()
        if len(tr)<500 or len(te)<50 or tr.y4head.nunique()<2:continue
        for vn,cols in [('PRE',pre_cols),('POST',post_cols)]:
            mo=make_model(cols);mo.fit(tr[cols],tr.y4head);p=mo.predict_proba(te[cols])[:,1]
            for (_,r),pr in zip(te.iterrows(),p):out.append({'date':r.date,'race_code':r.race_code,'venue':r.venue,'month':mon,'variant':vn,'p4head':float(pr),'y4head':int(r.y4head),'kimarite':r.kimarite,'ablation_variant':a.variant})
            diag.append({'month':mon,'score':vn,'R':len(te),'base_rate':float(te.y4head.mean()),'mean_p':float(np.mean(p))})
    pd.DataFrame(out).to_csv(a.out,index=False)
    meta={'variant':a.variant,'pre_cols':pre_cols,'post_cols':post_cols,'direct_core_definition':'boat3/4 direct waku_wr, waku_st, waku_sr decomposition on identical minimal non-Waku base','production_modified':False,'common_data_cache':a.data_cache}
    mp=Path(a.meta or f'audit_4head_waku10_ablation_{a.variant}.json');import json;mp.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    pd.DataFrame(diag).to_csv(f'diagnostics_4head_waku10_ablation_{a.variant}.csv',index=False);print(meta)
if __name__=='__main__':main()
