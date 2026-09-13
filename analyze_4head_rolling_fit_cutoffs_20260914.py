#!/usr/bin/env python3
# canonical Waku10 re-audit trigger 2026-09-14; analysis logic unchanged
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

# CI trigger: 2026-09-14 rolling fit-cutoff diagnostic
ROOT=Path(__file__).resolve().parent
TRAIN_START=date(2025,12,1); PRELOAD=TRAIN_START-timedelta(days=120); END=date(2026,8,31)
CUTOFFS=[date(2026,m,1)-timedelta(days=1) for m in range(2,9)]
PRE_COLS=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
POST_COLS=PRE_COLS+['ex_st_rank4','ex_st_4','ex_st_edge_4v3','orig_straight4','orig_lap4','orig_turn4','tilt4']
BINS=[-1,.01,.02,.03,.05,.08,.12,.18,.28,2]
LABELS=['<.01','.01-.02','.02-.03','.03-.05','.05-.08','.08-.12','.12-.18','.18-.28','>=.28']
OUT=ROOT/'analysis_4head_rolling_fit_cutoffs_20260914.csv'; AUD=ROOT/'audit_4head_rolling_fit_cutoffs_20260914.json'; SUM=ROOT/'summary_4head_rolling_fit_cutoffs_20260914.md'

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    all_rows=[]
    while d<=END:
        ymd=d.strftime('%Y/%m/%d');tkz=v250.by_code(f'data/previews/tkz/{ymd}.csv');stt=v250.by_code(f'data/previews/stt/{ymd}.csv');orig=v250.by_code(f'data/previews/original_exhibition/{ymd}.csv');today=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            code=str(r['レースコード']).zfill(12);z={'date':str(d),'race_code':code};z.update(v250.pre_features(x,s4));z.update(v250.post_features(code,tkz,stt,orig));today.append(z)
        rm={str(r['レースコード']).zfill(12):r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in today:
            z['y4head']=int(i(rm.get(z['race_code'],{}).get('1着_艇番'))==4);all_rows.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    df=pd.DataFrame(all_rows);df['dt']=pd.to_datetime(df.date); rec=[]
    for cutoff in CUTOFFS:
        cut=pd.Timestamp(cutoff);tr=df[(df.dt>=pd.Timestamp(TRAIN_START))&(df.dt<=cut)].copy()
        pm=v250.make_model(PRE_COLS);qm=v250.make_model(POST_COLS);pm.fit(tr[PRE_COLS],tr.y4head);qm.fit(tr[POST_COLS],tr.y4head)
        te=df[df.dt>cut].copy();te['PRE']=pm.predict_proba(te[PRE_COLS])[:,1];te['POST']=qm.predict_proba(te[POST_COLS])[:,1];te['month']=te.date.str[:7]
        for mon,g in te.groupby('month'):
            if mon<'2026-02' or mon>'2026-08': continue
            bins=pd.cut(g.PRE,BINS,labels=LABELS,right=False,include_lowest=True).value_counts().reindex(LABELS,fill_value=0)
            z={'fit_cutoff':str(cutoff),'test_month':mon,'train_R':len(tr),'all_R':len(g),'pre_mean':float(g.PRE.mean()),'pre_median':float(g.PRE.median()),'post_mean':float(g.POST.mean()),'post_median':float(g.POST.median()),'post_ge_018':int((g.POST>=.18).sum()),'post_ge_025':int((g.POST>=.25).sum())}
            for lab in LABELS:z['pre_'+lab]=int(bins[lab]);z['share_'+lab]=float(bins[lab]/len(g))
            rec.append(z)
    out=pd.DataFrame(rec);out.to_csv(OUT,index=False)
    focus=out[out.test_month=='2026-08'].copy()
    audit={'status':'COMPLETE','purpose':'diagnose whether progressively later causal fit cutoffs restore July/August score distributions','production_modified':False,'jul_aug_non_pristine':True,'target_outcomes_used_for_distribution_ranking':False,'fit_cutoffs':[str(x) for x in CUTOFFS],'pre_bins':LABELS,'august':focus.to_dict('records')}
    AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    L=['# HEAD4 rolling fit-cutoff distribution diagnostic','', '- Diagnostic only. Production unchanged.', '- Each model is fit only through its stated cutoff and scores strictly later dates.', '- July/August remain NON-PRISTINE; the 2026-07-31 -> August comparison cannot select production logic.','','## August score distribution by fit cutoff','','|fit cutoff|train R|Aug R|PRE<.01|PRE .03-.05|PRE>=.28|PRE mean|POST mean|POST>=.18|POST>=.25|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,x in focus.iterrows():L.append(f"|{x.fit_cutoff}|{int(x.train_R)}|{int(x.all_R)}|{100*x['share_<.01']:.2f}%|{100*x['share_.03-.05']:.2f}%|{100*x['share_>=.28']:.2f}%|{x.pre_mean:.5f}|{x.post_mean:.5f}|{int(x.post_ge_018)}|{int(x.post_ge_025)}|")
    L+=['','## Full month/cutoff table','','See `analysis_4head_rolling_fit_cutoffs_20260914.csv` for all fixed PRE-bin counts/shares and PRE/POST summaries.']
    SUM.write_text('\n'.join(L)+'\n');print(SUM.read_text())
if __name__=='__main__':main()
