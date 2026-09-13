#!/usr/bin/env python3
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from backtest import rows
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_v250_4head_rebuild_baseline as v250

ROOT=Path(__file__).resolve().parent
START=date(2026,6,20); END=date(2026,7,20); WARM=date(2026,2,1)
PRECOLS=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
FOCUS=['inner12_resistance','wall3_weak','past_win4','racer4','hist_st_edge_4v3','legacy_score4','motor4_hist']
OUT=ROOT/'analysis_4head_july_boundary_daily_20260914.csv'; AUD=ROOT/'audit_4head_july_boundary_20260914.json'; SUM=ROOT/'summary_4head_july_boundary_20260914.md'

def model():
    return Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler()),('m',LogisticRegression(C=.35,max_iter=1800))])

def main():
    cache={}; hist=defaultdict(list); seen=set(); d=WARM; train=[]; daily=[]; first_source=None; first_effective=None
    # Warm causal state and collect pre-boundary training labels only through 2026-06-19.
    while d<=END:
        ymd=d.strftime('%Y/%m/%d'); mh_rows=len(rows(f'data/programs/motor_history/{ymd}.csv'))
        before=len(hist); feats=process_features(d,cache,hist)
        frozen=[]
        for r,x,s4,_s5,_dc in feats:
            z={'date':str(d),'race_code':r['レースコード']}; z.update(v250.pre_features(x,s4)); frozen.append(z)
        if d<START:
            res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
            for z in frozen:
                rr=res.get(z['race_code'],{}); z['y']=int(str(rr.get('1着_艇番','')).strip()=='4'); train.append(z)
        if d>=START:
            rec={'date':str(d),'motor_hist_keys_before_score':before,'motor_history_source_rows_today':mh_rows,'preview_cache_keys_before_score':len(cache),'feature_rows':len(frozen)}
            for f in FOCUS:
                a=np.array([float(z[f]) for z in frozen],float) if frozen else np.array([])
                rec[f+'_mean']=float(a.mean()) if len(a) else None; rec[f+'_median']=float(np.median(a)) if len(a) else None; rec[f+'_zero_share']=float((a==0).mean()) if len(a) else None
            daily.append(rec)
        if mh_rows and first_source is None:first_source=str(d)
        ingest_prior_day_preview(cache,d); old=len(hist); ingest_motor(hist,seen,d)
        if len(hist)>old and first_effective is None:first_effective=str(d+timedelta(days=1))
        d+=timedelta(days=1)
    tr=pd.DataFrame(train); mo=model(); mo.fit(tr[PRECOLS],tr.y)
    # Replay again to attach fixed pre-boundary model PRE bins to target days.
    cache={};hist=defaultdict(list);seen=set();d=WARM; byday={r['date']:r for r in daily}
    bins=[0,.01,.02,.03,.05,.08,.12,.18,.28,1.01]; names=['<.01','.01-.02','.02-.03','.03-.05','.05-.08','.08-.12','.12-.18','.18-.28','>=.28']
    while d<=END:
        feats=process_features(d,cache,hist)
        if d>=START:
            X=pd.DataFrame([v250.pre_features(x,s4) for _r,x,s4,_s5,_dc in feats]); p=mo.predict_proba(X[PRECOLS])[:,1] if len(X) else np.array([]); r=byday[str(d)]
            r['PRE_mean']=float(p.mean()) if len(p) else None; r['PRE_median']=float(np.median(p)) if len(p) else None
            for lo,hi,n in zip(bins[:-1],bins[1:],names):r['PRE_'+n+'_share']=float(((p>=lo)&(p<hi)).mean()) if len(p) else None
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    D=pd.DataFrame(daily);D.to_csv(OUT,index=False)
    # Find largest day-over-day jumps for focal means and PRE<.01.
    jumps=[]
    for c in [f+'_mean' for f in FOCUS]+['PRE_<.01_share']:
        vals=pd.to_numeric(D[c],errors='coerce'); dif=vals.diff().abs(); ix=dif.idxmax() if dif.notna().any() else None
        if ix is not None:jumps.append({'metric':c,'date':D.loc[ix,'date'],'abs_change':float(dif.loc[ix]),'from':float(vals.loc[ix-1]),'to':float(vals.loc[ix])})
    audit={'status':'COMPLETE','outcome_blind_target_window':True,'production_modified':False,'first_motor_history_source_date':first_source,'first_motor_history_effective_score_date':first_effective,'train_end':'2026-06-19','target_start':str(START),'target_end':str(END),'largest_daily_jumps':jumps}
    AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# HEAD4 July 2026 day-level pipeline boundary audit','',f'- First motor-history source date: **{first_source}**',f'- First scoring date that can use newly ingested motor history: **{first_effective}**','- Fixed PRE model is trained only on rows before 2026-06-20; target-window outcomes are not loaded.','- Production unchanged.','','## Largest day-over-day changes','',pd.DataFrame(jumps).to_markdown(index=False),'','Full daily data: `analysis_4head_july_boundary_daily_20260914.csv`.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print(SUM.read_text())
if __name__=='__main__':main()
