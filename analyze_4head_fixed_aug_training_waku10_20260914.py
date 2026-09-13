#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import csv, hashlib, io, json, urllib.request

import numpy as np
import pandas as pd

import backtest
import backtest_v5_ev as v5
from backtest import i
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
import analyze_v250_4head_rebuild_baseline as v250

ROOT=Path(__file__).resolve().parent
TRAIN_START=date(2025,12,1); TRAIN_END=date(2026,1,31)
TARGET_START=date(2026,8,1); TARGET_END=date(2026,8,31)
PRELOAD=TRAIN_START-timedelta(days=120)
PRE_COLS=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
BINS=[-1,.01,.02,.03,.05,.08,.12,.18,.28,2]
LABELS=['<.01','.01-.02','.02-.03','.03-.05','.05-.08','.08-.12','.12-.18','.18-.28','>=.28']
OUT=ROOT/'analysis_4head_fixed_aug_training_waku10_20260914.csv'
TRAIN_DIFF=ROOT/'analysis_4head_training_feature_diff_20260914.csv'
AUD=ROOT/'audit_4head_fixed_aug_training_waku10_20260914.json'
SUM=ROOT/'summary_4head_fixed_aug_training_waku10_20260914.md'

PUBLIC_BASE=backtest.BASE
_public_counts={}

def public_only_rows(path):
    if path.startswith('data/programs/waku10/'):
        try:
            with urllib.request.urlopen(PUBLIC_BASE+path,timeout=30) as r:
                s=r.read().decode('utf-8-sig')
            rr=list(csv.DictReader(io.StringIO(s))) if s else []
        except Exception:
            rr=[]
        _public_counts[path]=len(rr)
        return rr
    return backtest.rows(path)

def canonical_rows(path):
    return backtest.rows(path)

def replay_features(start,end,waku_mode='canonical'):
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD;rows_out=[]
    original_rows=v5.rows
    v5.rows = canonical_rows if waku_mode=='canonical' else public_only_rows
    try:
        while d<start:
            ingest_motor(hist,seen,d)
            if d>=start-timedelta(days=12): ingest_prior_day_preview(cache,d)
            d+=timedelta(days=1)
        while d<=end:
            feats=v5.process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
            for r,x,s4,_s5,_dc in feats:
                z={'date':str(d),'race_code':str(r['レースコード']).zfill(12)}
                z.update(v250.pre_features(x,s4));rows_out.append(z)
            ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    finally:
        v5.rows=original_rows
    return pd.DataFrame(rows_out)

def add_labels(df):
    out=df.copy(); labels=[]; cache={}
    for dt,g in out.groupby('date',sort=False):
        ymd=dt.replace('-','/')
        rm={str(r['レースコード']).zfill(12):r for r in backtest.rows(f'data/results/realtime/{ymd}.csv')}
        for code in g.race_code: labels.append((code,int(i(rm.get(code,{}).get('1着_艇番'))==4)))
        cache.update({(dt,c):y for c,y in labels[-len(g):]})
    out['y4head']=[cache[(d,c)] for d,c in zip(out.date,out.race_code)]
    return out

def model_stats(model,tag):
    scaler=model.named_steps['p'].named_transformers_['n'].named_steps['s']
    coef=model.named_steps['m'].coef_[0]
    return [{'model':tag,'feature':c,'scaler_mean':float(mu),'scaler_scale':float(sc),'coef_std':float(co)} for c,mu,sc,co in zip(PRE_COLS,scaler.mean_,scaler.scale_,coef)]

def hash_target(df):
    q=df[['date','race_code']+PRE_COLS].sort_values(['date','race_code']).copy()
    s=q.to_csv(index=False,float_format='%.12g')
    return hashlib.sha256(s.encode()).hexdigest()

def main():
    # Canonical replay once through August. This single target matrix is reused by both fitted models.
    canon_all=replay_features(TRAIN_START,TARGET_END,'canonical')
    canon_train=canon_all[canon_all.date<=str(TRAIN_END)].copy()
    target=canon_all[(canon_all.date>=str(TARGET_START))&(canon_all.date<=str(TARGET_END))].copy()
    target_hash=hash_target(target)

    # Public-only Waku10 is used ONLY to reconstruct the old training feature lineage.
    public_train=replay_features(TRAIN_START,TRAIN_END,'public')

    # Race identity/labels must be identical.
    canon_codes=canon_train[['date','race_code']].sort_values(['date','race_code']).reset_index(drop=True)
    public_codes=public_train[['date','race_code']].sort_values(['date','race_code']).reset_index(drop=True)
    if not canon_codes.equals(public_codes):
        raise RuntimeError('training race identities differ; fail closed')
    canon_train=add_labels(canon_train); public_train=add_labels(public_train)
    if not canon_train[['date','race_code','y4head']].sort_values(['date','race_code']).reset_index(drop=True).equals(public_train[['date','race_code','y4head']].sort_values(['date','race_code']).reset_index(drop=True)):
        raise RuntimeError('training labels differ; fail closed')

    m_can=v250.make_model(PRE_COLS); m_pub=v250.make_model(PRE_COLS)
    m_can.fit(canon_train[PRE_COLS],canon_train.y4head); m_pub.fit(public_train[PRE_COLS],public_train.y4head)

    # Exact same frozen target matrix scored twice.
    target=add_labels(target)
    target['PRE_CANONICAL_TRAIN']=m_can.predict_proba(target[PRE_COLS])[:,1]
    target['PRE_PUBLIC_ONLY_TRAIN']=m_pub.predict_proba(target[PRE_COLS])[:,1]
    target['delta_PRE']=target.PRE_CANONICAL_TRAIN-target.PRE_PUBLIC_ONLY_TRAIN
    target['band_can']=target.PRE_CANONICAL_TRAIN.between(.03,.05,inclusive='both')
    target['band_pub']=target.PRE_PUBLIC_ONLY_TRAIN.between(.03,.05,inclusive='both')
    target.to_csv(OUT,index=False)

    td=[]
    for c in PRE_COLS:
        a=pd.to_numeric(canon_train[c],errors='coerce');b=pd.to_numeric(public_train[c],errors='coerce')
        td.append({'feature':c,'canonical_mean':float(a.mean()),'public_mean':float(b.mean()),'mean_delta':float(a.mean()-b.mean()),'canonical_zero_share':float((a==0).mean()),'public_zero_share':float((b==0).mean()),'changed_rows':int((~np.isclose(a.fillna(-999999),b.fillna(-999999),rtol=0,atol=1e-12)).sum())})
    tdf=pd.DataFrame(td)
    coefdf=pd.DataFrame(model_stats(m_can,'CANONICAL_TRAIN')+model_stats(m_pub,'PUBLIC_ONLY_TRAIN'))
    merged=tdf.merge(coefdf[coefdf.model=='CANONICAL_TRAIN'][['feature','scaler_mean','scaler_scale','coef_std']].rename(columns={'scaler_mean':'can_scaler_mean','scaler_scale':'can_scaler_scale','coef_std':'can_coef_std'}),on='feature').merge(coefdf[coefdf.model=='PUBLIC_ONLY_TRAIN'][['feature','scaler_mean','scaler_scale','coef_std']].rename(columns={'scaler_mean':'pub_scaler_mean','scaler_scale':'pub_scaler_scale','coef_std':'pub_coef_std'}),on='feature')
    merged['coef_delta']=merged.can_coef_std-merged.pub_coef_std
    merged.to_csv(TRAIN_DIFF,index=False)

    def dist(col):
        p=target[col]
        cut=pd.cut(p,BINS,labels=LABELS,right=False,include_lowest=True).value_counts().reindex(LABELS,fill_value=0)
        band=target[p.between(.03,.05,inclusive='both')]
        return {'mean':float(p.mean()),'median':float(p.median()),'bins':{lab:int(cut[lab]) for lab in LABELS},'band_R':int(len(band)),'band_wins':int(band.y4head.sum()),'band_rate':float(band.y4head.mean()) if len(band) else None}
    can=dist('PRE_CANONICAL_TRAIN');pub=dist('PRE_PUBLIC_ONLY_TRAIN')
    both=int((target.band_can & target.band_pub).sum()); gained=int((target.band_can & ~target.band_pub).sum()); lost=int((~target.band_can & target.band_pub).sum())
    # Current public source coverage for training period, as actually observed during replay.
    pub_days=[]
    d=TRAIN_START
    while d<=TRAIN_END:
        p=f"data/programs/waku10/{d.strftime('%Y/%m/%d')}.csv"; pub_days.append({'date':str(d),'rows':int(_public_counts.get(p,0))}); d+=timedelta(days=1)
    audit={'status':'COMPLETE','purpose':'hold canonical August features fixed and isolate Jan31 training Waku10 lineage','production_modified':False,'jul_aug_non_pristine':True,'target_matrix_reused_exactly':True,'target_hash_sha256':target_hash,'target_R':int(len(target)),'train_R':int(len(canon_train)),'train_labels_identical':True,'public_training_waku10_days_with_rows':int(sum(x['rows']>0 for x in pub_days)),'public_training_waku10_rows':int(sum(x['rows'] for x in pub_days)),'canonical_train':can,'public_only_train':pub,'band_overlap_R':both,'band_gained_by_canonical_train':gained,'band_lost_by_canonical_train':lost,'mean_abs_PRE_shift':float(target.delta_PRE.abs().mean()),'max_abs_PRE_shift':float(target.delta_PRE.abs().max()),'training_feature_diffs':td,'public_training_daily_coverage':pub_days}
    AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')

    L=['# HEAD4 fixed-August-input / training-only Waku10 audit','',
       '- August canonical feature matrix is built once and scored unchanged by both models.',
       '- Only Dec-2025..Jan-2026 Waku10 lineage differs between fits.',
       '- July/August are NON-PRISTINE descriptive only. Production unchanged.','',
       f'- Frozen August target hash: `{target_hash}`','',
       '## August distribution','',
       '|training Waku10|PRE mean|PRE median|PRE .03-.05 R|wins|rate|','|---|---:|---:|---:|---:|---:|',
       f"|canonical restored|{can['mean']:.5f}|{can['median']:.5f}|{can['band_R']}|{can['band_wins']}|{100*can['band_rate']:.2f}%|",
       f"|public-only historical|{pub['mean']:.5f}|{pub['median']:.5f}|{pub['band_R']}|{pub['band_wins']}|{100*pub['band_rate']:.2f}%|",
       '',f'- Band overlap: {both} R; gained under canonical training: {gained} R; lost: {lost} R.',
       f"- Mean absolute PRE shift: {audit['mean_abs_PRE_shift']:.5f}; max: {audit['max_abs_PRE_shift']:.5f}.",
       f"- Public-only training Waku10 coverage observed now: {audit['public_training_waku10_days_with_rows']}/62 days, {audit['public_training_waku10_rows']} rows.",
       '', '## Training feature changes','',
       merged[['feature','canonical_mean','public_mean','mean_delta','canonical_zero_share','public_zero_share','changed_rows','can_coef_std','pub_coef_std','coef_delta']].to_markdown(index=False)]
    SUM.write_text('\n'.join(L)+'\n');print(SUM.read_text())

if __name__=='__main__': main()
