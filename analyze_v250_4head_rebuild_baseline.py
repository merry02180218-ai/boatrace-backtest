#!/usr/bin/env python3
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backtest import rows,i
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview,score4v4,resistance12
from backtest_v5_ev import PRELOAD_START,process_features
from backtest_v18_core45 import features4,c01
from analyze_v23_20260902_daypreview import by_code,original_scores,rank_score
from analyze_v33_tilt_effect import tiltval

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
SUMMARY=ROOT/'summary_v250_4head_rebuild_baseline.md'
START=date(2025,12,1); END=date(2026,8,31)
MONTHS=[f'2026-{m:02d}' for m in range(2,9)]

# Research-only port of the canonical 3-head philosophy.
# PRE uses only features produced before the current race exhibition.
# POST adds current-race exhibition measurements, but results are loaded only after features are frozen.

def safe(v,default=0.0):
    try:
        x=float(v); return x if np.isfinite(x) else default
    except:return default

def pre_features(x,s4):
    fr=features4(x); b4=x[4]
    return {
        'legacy_score4':safe(s4),
        'racer4':safe(fr['4選手力']),
        'hist_st_edge_4v3':safe(fr['4_ST優位']),
        'wall3_weak':safe(fr['3壁弱さ']),
        'inner12_resistance':safe(resistance12(x)),
        'motor4_2ren':safe(b4.get('motor2')),
        'motor4_hist':safe(b4.get('mhist')),
        'turnfoot4_prior':safe(b4.get('turnfoot')),
        'past_win4':safe(b4.get('past_win')),
    }

def post_features(code,tkz,stt,orig):
    sr=stt.get(code,{});orr=orig.get(code,{});tr=tkz.get(code,{})
    stvals={b:safe(sr.get(f'艇{b}_スタート展示'),np.nan) for b in range(1,7)}
    st_rank=rank_score(stvals,4,True) if any(np.isfinite(v) for v in stvals.values()) else .5
    os=original_scores(orr,4)
    return {
        'ex_st_rank4':safe(st_rank,.5),
        'ex_st_4':safe(sr.get('艇4_スタート展示'),.20),
        'ex_st_edge_4v3':safe(sr.get('艇3_スタート展示'),.20)-safe(sr.get('艇4_スタート展示'),.20),
        'orig_straight4':safe(os.get('straight'),.5),
        'orig_lap4':safe(os.get('lap'),.5),
        'orig_turn4':safe(os.get('turn'),.5),
        'tilt4':safe(tiltval(tr.get('艇4_チルト')),0.0),
    }

def make_model(cols):
    prep=ColumnTransformer([('n',Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler())]),cols)])
    return Pipeline([('p',prep),('m',LogisticRegression(C=.35,max_iter=1800,class_weight=None))])

def auc(y,p):
    try:return roc_auc_score(y,p) if len(set(y))>1 else np.nan
    except:return np.nan

def main():
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
            code=r['レースコード'];z={'date':str(d),'race_code':code,'venue':str(r.get('レース場コード','')).zfill(2)}
            z.update(pre_features(x,s4));z.update(post_features(code,tkz,stt,orig));frozen.append(z)
        # Outcomes are joined only after all current-race features for the day are frozen.
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            rr=res.get(z['race_code'],{});z['y4head']=int(i(rr.get('1着_艇番'))==4);z['kimarite']=(rr.get('決まり手') or '').strip();data.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    df=pd.DataFrame(data);df['_date']=pd.to_datetime(df.date)
    pre_cols=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
    post_cols=pre_cols+['ex_st_rank4','ex_st_4','ex_st_edge_4v3','orig_straight4','orig_lap4','orig_turn4','tilt4']
    out=[];diag=[]
    for mon in MONTHS:
        m=pd.Timestamp(mon+'-01');e=m+pd.offsets.MonthBegin(1);tr=df[df._date<m].copy();te=df[(df._date>=m)&(df._date<e)].copy()
        if len(tr)<500 or len(te)<50 or tr.y4head.nunique()<2:continue
        for variant,cols in [('PRE',pre_cols),('POST',post_cols)]:
            mo=make_model(cols);mo.fit(tr[cols],tr.y4head);p=mo.predict_proba(te[cols])[:,1]
            for (_,r),pr in zip(te.iterrows(),p):out.append({'date':r.date,'race_code':r.race_code,'venue':r.venue,'month':mon,'variant':variant,'p4head':float(pr),'y4head':int(r.y4head),'kimarite':r.kimarite})
            diag.append({'month':mon,'variant':variant,'R':len(te),'base_rate':te.y4head.mean(),'auc':auc(te.y4head,p),'brier':brier_score_loss(te.y4head,p),'logloss':log_loss(te.y4head,p,labels=[0,1])})
    O=pd.DataFrame(out);O.to_csv(OUT,index=False);D=pd.DataFrame(diag)
    L=['# v250 4-head rebuild baseline','', '- 4号艇1着そのものを目的変数にした再構築の第一段階。旧4カドの決まり手限定ラベルは使わない。','- PRE: current-race exhibitionを使用しない。POST: 展示ST/オリジナル展示/チルトを追加。','- 各月はその月より前だけで学習するmonthly walk-forward。','- 結果は特徴量をfreezeした後にjoin。','- 2025-12〜2026-08は既存研究で繰り返し見ているため、すべてin-sample/model-selection evidence。pristine validationではない。','','## Monthly head probability','|month|variant|R|4-head rate|AUC|Brier|logloss|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in D.iterrows():L.append(f"|{r.month}|{r.variant}|{int(r.R)}|{100*r.base_rate:.2f}%|{r.auc:.4f}|{r.brier:.5f}|{r.logloss:.5f}|")
    L+=['','## Threshold diagnostics','|variant|cut|R|4-head hits|4-head rate|','|---|---:|---:|---:|---:|']
    for v in ['PRE','POST']:
        q=O[O.variant==v]
        for cut in [.10,.12,.15,.18,.20,.25,.30,.35,.40]:
            z=q[q.p4head>=cut]
            if len(z):L.append(f'|{v}|{cut:.2f}|{len(z)}|{int(z.y4head.sum())}|{100*z.y4head.mean():.2f}%|')
    L+=['','## Next step','- p4headが月別に有効なら、PRE候補をrolling S/A/B化する。','- POSTは4コース攻撃専用featureを拡張し、exact final gateを探索する。','- その後、4固定のordered-pair相手モデル → odds target探索 → 1R10,000円Hamilton Dutchへ進む。','- 3頭の3.00倍/5-10点は4頭へ自動流用せず、4頭専用に比較する。']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
