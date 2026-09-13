#!/usr/bin/env python3
# canonical Waku10 re-audit trigger 2026-09-14; analysis logic unchanged
# Outcome-independent drift audit; target-period results are intentionally not loaded.
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from backtest import rows
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_v250_4head_rebuild_baseline as v250

ROOT=Path(__file__).resolve().parent
TRAIN_START=date(2025,12,1); TRAIN_END=date(2026,1,31); TEST_END=date(2026,8,31); PRELOAD=TRAIN_START-timedelta(days=120)
LO=.03; HI=.05
PRE_COLS=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
POST_COLS=PRE_COLS+['ex_st_rank4','ex_st_4','ex_st_edge_4v3','orig_straight4','orig_lap4','orig_turn4','tilt4']
DRIFT=ROOT/'analysis_4head_regime_drift_20260914.csv'; BINS=ROOT/'analysis_4head_pre_bins_20260914.csv'; AUD=ROOT/'audit_4head_regime_drift_20260914.json'; SUM=ROOT/'summary_4head_regime_drift_20260914.md'

def smd(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float);a=a[np.isfinite(a)];b=b[np.isfinite(b)]
    if not len(a) or not len(b): return None
    den=math.sqrt((np.var(a)+np.var(b))/2)
    return float((np.mean(b)-np.mean(a))/den) if den>0 else 0.0

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train=[]
    while d<=TRAIN_END:
        ymd=d.strftime('%Y/%m/%d');tkz=v250.by_code(f'data/previews/tkz/{ymd}.csv');stt=v250.by_code(f'data/previews/stt/{ymd}.csv');orig=v250.by_code(f'data/previews/original_exhibition/{ymd}.csv')
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            code=str(r['レースコード']).zfill(12);z={'date':str(d),'race_code':code};z.update(v250.pre_features(x,s4));z.update(v250.post_features(code,tkz,stt,orig));train.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    rms={}
    for z in train:
        ymd=z['date'].replace('-','/')
        if ymd not in rms:rms[ymd]={str(r['レースコード']).zfill(12):r for r in rows(f'data/results/realtime/{ymd}.csv')}
        try:z['y4head']=int(float(rms[ymd].get(z['race_code'],{}).get('1着_艇番',0))==4)
        except:z['y4head']=0
    tr=pd.DataFrame(train);pm=v250.make_model(PRE_COLS);qm=v250.make_model(POST_COLS);pm.fit(tr[PRE_COLS],tr.y4head);qm.fit(tr[POST_COLS],tr.y4head)
    rec=[]
    while d<=TEST_END:
        ymd=d.strftime('%Y/%m/%d');tkz=v250.by_code(f'data/previews/tkz/{ymd}.csv');stt=v250.by_code(f'data/previews/stt/{ymd}.csv');orig=v250.by_code(f'data/previews/original_exhibition/{ymd}.csv');today=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            code=str(r['レースコード']).zfill(12);z={'date':str(d),'race_code':code,'venue_code':code[4:6]};z.update(v250.pre_features(x,s4));z.update(v250.post_features(code,tkz,stt,orig));today.append(z)
        if today:
            q=pd.DataFrame(today);q['PRE']=pm.predict_proba(q[PRE_COLS])[:,1];q['POST']=qm.predict_proba(q[POST_COLS])[:,1];rec.extend(q.to_dict('records'))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    df=pd.DataFrame(rec);df['month']=df.date.str[:7];band=df[df.PRE.between(LO,HI,inclusive='both')].copy();base=band[band.month<='2026-06']
    out=[]
    for mon in sorted(band.month.unique()):
        g=band[band.month==mon]
        for c in PRE_COLS+['PRE','POST']:
            a=pd.to_numeric(base[c],errors='coerce').dropna();b=pd.to_numeric(g[c],errors='coerce').dropna();ks=ks_2samp(a,b) if len(a) and len(b) else None
            out.append({'month':mon,'feature':c,'n':len(b),'baseline_mean':float(a.mean()),'month_mean':float(b.mean()),'baseline_median':float(a.median()),'month_median':float(b.median()),'smd':smd(a,b),'ks':float(ks.statistic) if ks else None,'ks_p':float(ks.pvalue) if ks else None})
    pd.DataFrame(out).to_csv(DRIFT,index=False)
    edges=[0,.01,.02,.03,.05,.08,.12,.18,.28,1.01]; labels=['<.01','.01-.02','.02-.03','.03-.05','.05-.08','.08-.12','.12-.18','.18-.28','>=.28']
    df['pre_bin']=pd.cut(df.PRE,bins=edges,labels=labels,right=False,include_lowest=True)
    bt=df.groupby(['month','pre_bin'],observed=False).size().rename('R').reset_index(); totals=df.groupby('month').size().rename('all_R');bt=bt.join(totals,on='month');bt['share']=bt.R/bt.all_R;bt.to_csv(BINS,index=False)
    dr=pd.DataFrame(out);aug=dr[dr.month=='2026-08'].copy();aug['abs_smd']=aug.smd.abs();top=aug.sort_values('abs_smd',ascending=False).head(8)
    audit={'status':'COMPLETE','fit_cutoff':'2026-01-31','outcome_independent_drift_ranking':True,'target_outcomes_used_for_drift':False,'baseline':'2026-02..2026-06 PRE 0.03..0.05','jul_aug_non_pristine':True,'production_modified':False,'top_august_abs_smd':top[['feature','smd','ks']].to_dict('records')};AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    L=['# HEAD4 outcome-independent regime drift audit','', '- Drift ranking uses feature distributions only; target-period win/loss outcomes are not used.', '- Baseline: Feb-Jun PRE 0.03..0.05 under the Jan-31 frozen model.', '- July/August NON-PRISTINE; production unchanged.','','## Largest August shifts by absolute SMD','','|feature|SMD|KS|','|---|---:|---:|']
    for _,r in top.iterrows():L.append(f"|{r.feature}|{r.smd:.3f}|{r.ks:.3f}|")
    L+=['','## PRE-bin population shares','',bt.to_markdown(index=False)]
    SUM.write_text('\n'.join(L)+'\n');print(SUM.read_text())
if __name__=='__main__':main()
