#!/usr/bin/env python3
"""Generic result-blind PRE scanner for frozen HEAD4_V291_COMP7 S layer."""
from __future__ import annotations
import argparse, csv, hashlib, json, os
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from backtest import rows, i, race_features
from backtest_v3 import ingest_motor
from backtest_v4 import add_features, score4v4, ingest_prior_day_preview
from analyze_v250_4head_rebuild_baseline import pre_features, make_model

TRAIN_START=date(2025,12,1)
TRAIN_END=date(2026,6,30)
PRELOAD_START=TRAIN_START-timedelta(days=120)
PRE_CUT=.28
PRE_COLS=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']


def resolve_date(arg):
    s=arg or os.environ.get('TARGET_DATE','').strip()
    if not s:s=datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d')
    return datetime.strptime(s,'%Y-%m-%d').date()

def local_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def digest(path):
    h=hashlib.sha256();
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def training_and_state(day):
    if day<=TRAIN_END:raise RuntimeError('target date must be after frozen fit cutoff 2026-06-30')
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train=[];d=TRAIN_START
    from backtest_v5_ev import process_features
    while d<=TRAIN_END:
        ymd=d.strftime('%Y/%m/%d'); frozen=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            z={'race_code':str(r['レースコード']).zfill(12)};z.update(pre_features(x,s4));frozen.append(z)
        res={str(r['レースコード']).zfill(12):r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            z['y4head']=int(i(res.get(z['race_code'],{}).get('1着_艇番'))==4);train.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    d=TRAIN_END+timedelta(days=1)
    while d<day:
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    return pd.DataFrame(train),cache,hist

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date');a=ap.parse_args();day=resolve_date(a.date)
    day8=day.strftime('%Y%m%d'); inp=Path('current_input/v291')/day8
    cards_path=inp/'race_cards.csv';waku_path=inp/'waku10.csv'
    if not cards_path.exists() or not waku_path.exists():raise RuntimeError(f'missing PRE inputs: {inp}')
    tr,cache,hist=training_and_state(day)
    cards=local_rows(cards_path);waku={str(r.get('レースコード','')).zfill(12):r for r in local_rows(waku_path)}
    cur=[]
    for r in cards:
        code=str(r.get('レースコード','')).zfill(12);w=waku.get(code,{})
        x=add_features(race_features(r,w),r,cache,hist);s4=score4v4(x)
        z={'date':str(day),'race_code':code,'jcd':int(code[8:10]),'rno':int(code[10:12]),'venue':str(r.get('レース場コード','')).zfill(2)}
        z.update(pre_features(x,s4));cur.append(z)
    cur=pd.DataFrame(cur)
    if tr.empty or cur.empty or tr.y4head.nunique()<2:raise RuntimeError('invalid train/current data')
    model=make_model(PRE_COLS);model.fit(tr[PRE_COLS],tr.y4head.astype(int))
    cur['PRE']=model.predict_proba(cur[PRE_COLS])[:,1];cur['pre_eligible']=(cur.PRE>=PRE_CUT).astype(int)
    cur=cur.sort_values(['PRE','race_code'],ascending=[False,True]).reset_index(drop=True);q=cur[cur.pre_eligible==1]
    outdir=Path('live_outputs/v291')/day8;outdir.mkdir(parents=True,exist_ok=True)
    csvp=outdir/'pre_scan.csv';mdp=outdir/'pre_scan.md';audp=outdir/'pre_scan_audit.json';cur.to_csv(csvp,index=False)
    audit={'policy':'HEAD4_V291_COMP7','layer':'S_PRE_STAGE_ONLY','target_date':str(day),'result_blind_target_day':True,'pre_cut_inclusive':PRE_CUT,'model_recipe':'analyze_v250_4head_rebuild_baseline.py::PRE','fit_label_start':str(TRAIN_START),'fit_label_cutoff':str(TRAIN_END),'jul_aug_labels_used':False,'september_labels_used':False,'current_exhibition_used':False,'pre_features':PRE_COLS,'train_rows':len(tr),'train_head4_rate':float(tr.y4head.mean()),'current_rows':len(cur),'eligible_rows':len(q),'cards_sha256':digest(cards_path),'waku_sha256':digest(waku_path),'logistic_C':.35}
    audp.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=[f'# {day} 4-head v291 PRE scan','',f'- Current race rows: {len(cur)}',f'- PRE >= {PRE_CUT:.2f}: {len(q)}','- Final S still requires POST >= 0.25 and ENV_ENTRY >= 0.224790.','','|race|PRE|legacy4|racer4|motor4 hist|turnfoot4 prior|','|---|---:|---:|---:|---:|---:|']
    for _,r in q.iterrows():L.append(f"|JCD{int(r.jcd):02d} {int(r.rno)}R|{r.PRE:.6f}|{r.legacy_score4:.3f}|{r.racer4:.3f}|{r.motor4_hist:.3f}|{r.turnfoot4_prior:.3f}|")
    mdp.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
