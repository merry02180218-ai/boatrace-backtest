#!/usr/bin/env python3
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json
import pandas as pd
from backtest import rows,i
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_v250_4head_rebuild_baseline as v250

ROOT=Path(__file__).resolve().parent
TRAIN_START=date(2025,12,1); TRAIN_END=date(2026,1,31); TEST_START=date(2026,2,1); TEST_END=date(2026,8,31)
PRELOAD=TRAIN_START-timedelta(days=120); LO=.03; HI=.05
PRE_COLS=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
POST_COLS=PRE_COLS+['ex_st_rank4','ex_st_4','ex_st_edge_4v3','orig_straight4','orig_lap4','orig_turn4','tilt4']
OUT=ROOT/'analysis_4head_common_frozen_20260131.csv'; AUD=ROOT/'audit_4head_common_frozen_20260131.json'; SUM=ROOT/'summary_4head_common_frozen_20260131.md'

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train=[]
    while d<=TRAIN_END:
        ymd=d.strftime('%Y/%m/%d');tkz=v250.by_code(f'data/previews/tkz/{ymd}.csv');stt=v250.by_code(f'data/previews/stt/{ymd}.csv');orig=v250.by_code(f'data/previews/original_exhibition/{ymd}.csv');f=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            code=str(r['レースコード']).zfill(12);z={'date':str(d),'race_code':code};z.update(v250.pre_features(x,s4));z.update(v250.post_features(code,tkz,stt,orig));f.append(z)
        rm={str(r['レースコード']).zfill(12):r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in f:z['y4head']=int(i(rm.get(z['race_code'],{}).get('1着_艇番'))==4);train.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    tr=pd.DataFrame(train);pm=v250.make_model(PRE_COLS);qm=v250.make_model(POST_COLS);pm.fit(tr[PRE_COLS],tr.y4head);qm.fit(tr[POST_COLS],tr.y4head)
    rec=[]
    while d<=TEST_END:
        ymd=d.strftime('%Y/%m/%d');tkz=v250.by_code(f'data/previews/tkz/{ymd}.csv');stt=v250.by_code(f'data/previews/stt/{ymd}.csv');orig=v250.by_code(f'data/previews/original_exhibition/{ymd}.csv');today=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            code=str(r['レースコード']).zfill(12);z={'date':str(d),'race_code':code};z.update(v250.pre_features(x,s4));z.update(v250.post_features(code,tkz,stt,orig));today.append(z)
        if today:
            q=pd.DataFrame(today);q['PRE']=pm.predict_proba(q[PRE_COLS])[:,1];q['POST']=qm.predict_proba(q[POST_COLS])[:,1]
            rm={str(r['レースコード']).zfill(12):r for r in rows(f'data/results/realtime/{ymd}.csv')}
            for z in q.to_dict('records'):z['y4head']=int(i(rm.get(z['race_code'],{}).get('1着_艇番'))==4);rec.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    df=pd.DataFrame(rec);df['month']=df.date.str[:7];band=df[df.PRE.between(LO,HI,inclusive='both')].copy();band.to_csv(OUT,index=False)
    months=[]
    for mon,g in band.groupby('month'):
        allr=int((df.month==mon).sum());months.append({'month':mon,'all_R':allr,'band_R':len(g),'wins':int(g.y4head.sum()),'rate':float(g.y4head.mean()),'post_ge_018':int((g.POST>=.18).sum()),'post_ge_025':int((g.POST>=.25).sum()),'pre_mean':float(g.PRE.mean()),'post_mean':float(g.POST.mean())})
    audit={'status':'COMPLETE','fit_cutoff':'2026-01-31','single_model_refit_after_cutoff':False,'target_months':'2026-02..2026-08','band':[LO,HI],'train_rows':len(tr),'train_rate':float(tr.y4head.mean()),'months':months,'jul_aug_non_pristine':True,'production_modified':False,'roi':'NOT_COMPUTED_NO_VERIFIED_ARCHIVED_CLOSING_ODDS_FOR_2026_02_08'};AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    L=['# HEAD4 common frozen model (fit cutoff 2026-01-31)','', '- One PRE and one POST model fit once through 2026-01-31 and reused unchanged for every target month.', '- July/August are NON-PRISTINE descriptive only. Production unchanged.','','|month|all R|band R|wins|rate|POST>=.18|POST>=.25|PRE mean|POST mean|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in months:L.append(f"|{x['month']}|{x['all_R']}|{x['band_R']}|{x['wins']}|{100*x['rate']:.2f}%|{x['post_ge_018']}|{x['post_ge_025']}|{x['pre_mean']:.5f}|{x['post_mean']:.5f}|")
    SUM.write_text('\n'.join(L)+'\n');print(SUM.read_text())
if __name__=='__main__':main()
