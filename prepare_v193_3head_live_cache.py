#!/usr/bin/env python3
from __future__ import annotations
import csv,json,joblib
from datetime import date
from pathlib import Path
import pandas as pd
from predict_v192_3head_live_manual import exact_prior_bias,fit_head,target
from analyze_v166_3head_pair_direct import fit as fit_pair

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
SCHEMA=ROOT/'analysis_v165_3head_schema.json'
CACHE=ROOT/'cache_v193_3head_live.joblib'
META=ROOT/'cache_v193_3head_live_meta.json'
HD=date(2026,9,8)

def main():
    schema=json.loads(SCHEMA.read_text(encoding='utf-8'))
    src=pd.read_csv(SRC)
    head,nums,cats,ntrain=fit_head(src,schema['features'],'venue' if 'venue' in src.columns else None,HD)
    hist=[]
    with SRC.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if r.get('date','')<HD.isoformat(): hist.append(r)
    pair,pair_n=fit_pair(hist)
    bias,bias_days=exact_prior_bias(HD)
    obj={'date':HD.isoformat(),'head_model':head,'head_nums':nums,'head_cats':cats,'pair_model':pair,'st_bias':bias}
    joblib.dump(obj,CACHE,compress=3)
    meta={'date':HD.isoformat(),'head_train_rows':ntrain,'pair_train_3wins':pair_n,'prior_st_bias_days':bias_days,'cut':0.30,'lambda':1.0}
    META.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False))
if __name__=='__main__': main()
