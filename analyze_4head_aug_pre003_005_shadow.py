#!/usr/bin/env python3
"""Exploratory August 2026 shadow cohort for frozen HEAD4 v291/VARN.

Guardrails:
- August is NON-PRISTINE; this script is descriptive only.
- Fit labels stop at 2026-06-30. July/August outcomes never enter fitting/tuning.
- The only selection rule is the pre-declared inclusive PRE band 0.03..0.05.
- Production v291/VARN thresholds/policy are not modified.
- Betting/VARN settlement is intentionally omitted unless exact historical
  pre-deadline trifecta-odds lineage is separately proven available.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json
import numpy as np
import pandas as pd

from backtest import rows,i
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_v250_4head_rebuild_baseline as v250
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221
import analyze_v264_4head_feature_exhaustive as v264
from head4_v291_downstream_inference import load_artifact,score_post,score_env_entry
from head4_v273_a_live_inference import load_artifact as load_a_artifact,score_a

ROOT=Path(__file__).resolve().parent
START=date(2026,8,1); END=date(2026,8,31)
TRAIN_START=date(2025,12,1); TRAIN_END=date(2026,6,30)
PRELOAD=TRAIN_START-timedelta(days=120)
PRE_COLS=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4']
BAND_LO=.03; BAND_HI=.05
POST_S=.25; ENV_S=.224790; POST_A=.18
OUT=ROOT/'analysis_4head_aug_pre003_005_shadow.csv'
SUMMARY=ROOT/'summary_4head_aug_pre003_005_shadow.md'
AUDIT=ROOT/'audit_4head_aug_pre003_005_shadow.json'


def build_train_and_aug_features():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train=[]
    while d<=TRAIN_END:
        ymd=d.strftime('%Y/%m/%d'); frozen=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            z={'race_code':str(r['レースコード']).zfill(12)};z.update(v250.pre_features(x,s4));frozen.append(z)
        rr={str(r['レースコード']).zfill(12):r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            z['y4head']=int(i(rr.get(z['race_code'],{}).get('1着_艇番'))==4);train.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    # July updates causal PRE state only. No July result is read.
    while d<START:
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    model=v250.make_model(PRE_COLS);tr=pd.DataFrame(train);model.fit(tr[PRE_COLS],tr.y4head.astype(int))
    artifact=load_artifact(); rec=[]
    while d<=END:
        ymd=d.strftime('%Y/%m/%d')
        tkz=v250.by_code(f'data/previews/tkz/{ymd}.csv');stt=v250.by_code(f'data/previews/stt/{ymd}.csv');orig=v250.by_code(f'data/previews/original_exhibition/{ymd}.csv')
        today=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            code=str(r['レースコード']).zfill(12);z={'date':str(d),'race_code':code}
            z.update(v250.pre_features(x,s4));z.update(v250.post_features(code,tkz,stt,orig));today.append(z)
        if today:
            q=pd.DataFrame(today);q['PRE']=model.predict_proba(q[PRE_COLS])[:,1]
            q['POST']=[score_post(r,artifact) for r in q.to_dict('records')]
            rec.extend(q.to_dict('records'))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    return pd.DataFrame(rec),len(tr),float(tr.y4head.mean())


def historical_safe_frame(pred):
    # analysis_v93 rows contain historical outcome columns too, but those are never
    # passed into inference. Explicit feature-only copy is created before scoring.
    raw=pd.DataFrame(c4.read());raw['race_code']=raw.race_code.astype(str).str.zfill(12)
    raw=raw[raw.date.astype(str).str[:7].eq('2026-08')].copy()
    raw=v221.build(raw,'date');raw=v264.add_rel(raw)
    q=raw.merge(pred[['race_code','PRE','POST']],on='race_code',how='inner',validate='one_to_one')
    q['p4_joint']=pd.to_numeric(q.PRE,errors='coerce')*pd.to_numeric(q.POST,errors='coerce')
    q['post_x_entry_same']=pd.to_numeric(q.POST,errors='coerce')*pd.to_numeric(q.get('entry_confirmed_same'),errors='coerce')
    return q


def result_map():
    out={};d=START
    while d<=END:
        ymd=d.strftime('%Y/%m/%d')
        for r in rows(f'data/results/realtime/{ymd}.csv'):
            code=str(r.get('レースコード','')).zfill(12);out[code]=int(i(r.get('1着_艇番'))==4)
        d+=timedelta(days=1)
    return out


def stats(s):
    s=pd.to_numeric(s,errors='coerce').dropna()
    if s.empty:return {'n':0}
    return {'n':int(len(s)),'min':float(s.min()),'p25':float(s.quantile(.25)),'median':float(s.median()),'p75':float(s.quantile(.75)),'max':float(s.max()),'mean':float(s.mean())}


def main():
    pred,train_rows,train_rate=build_train_and_aug_features()
    if pred.empty:raise RuntimeError('no August frozen PRE/POST rows')
    band=pred[pred.PRE.between(BAND_LO,BAND_HI,inclusive='both')].copy()
    safe=historical_safe_frame(pred)
    art=load_artifact();aa=load_a_artifact()
    # Restrict to artifact feature keys + identifiers before scoring, preventing
    # historical winner/result columns from entering downstream inference.
    envfs=list(art['ENV_ENTRY']['features']);afs=list(aa['A_SCORE']['features'])
    need=list(dict.fromkeys(['race_code','PRE','POST']+envfs+afs))
    missing=[c for c in need if c not in safe.columns]
    if missing:raise RuntimeError('missing historical safe feature keys: '+','.join(missing[:20]))
    sf=safe[need].copy()
    sf['ENV_ENTRY']=[score_env_entry(r,art) for r in sf.to_dict('records')]
    sf['A_SCORE_LIVE']=[score_a(r,aa) for r in sf.to_dict('records')]
    b=band.merge(sf[['race_code','ENV_ENTRY','A_SCORE_LIVE']],on='race_code',how='left',validate='one_to_one')
    if b.ENV_ENTRY.isna().any() or b.A_SCORE_LIVE.isna().any():raise RuntimeError('shadow cohort missing downstream score')
    # Only now join August outcomes, after frozen scores and cohort identity exist.
    rm=result_map();b['y4head']=[rm.get(c,np.nan) for c in b.race_code]
    b['post_s_pass']=(b.POST>=POST_S).astype(int);b['env_s_pass']=(b.ENV_ENTRY>=ENV_S).astype(int)
    b['shadow_s_downstream_pass']=((b.POST>=POST_S)&(b.ENV_ENTRY>=ENV_S)).astype(int)
    acut=float(aa['A_gate']['A_SCORE_LIVE'])
    b['shadow_a_downstream_pass']=((b.POST>=POST_A)&(b.A_SCORE_LIVE>=acut)).astype(int)
    b=b.sort_values(['PRE','race_code']).reset_index(drop=True);b.to_csv(OUT,index=False)
    n=len(b);wins=int(pd.to_numeric(b.y4head).fillna(0).sum())
    audit={
      'status':'COMPLETE','scope':'AUG_2026_NON_PRISTINE_EXPLORATORY_ONLY','band_inclusive':[BAND_LO,BAND_HI],
      'fit_label_start':str(TRAIN_START),'fit_label_cutoff':str(TRAIN_END),'jul_aug_labels_used_for_fit':False,
      'production_policy_modified':False,'v96_used_as_production_signal':False,'train_rows':train_rows,'train_head4_rate':train_rate,
      'aug_all_rows':int(len(pred)),'cohort_rows':n,'cohort_head4_wins':wins,'cohort_head4_rate':float(wins/n) if n else None,
      'post_s_pass':int(b.post_s_pass.sum()),'env_s_pass':int(b.env_s_pass.sum()),'shadow_s_downstream_pass':int(b.shadow_s_downstream_pass.sum()),
      'shadow_a_downstream_pass_bypassing_pre_floor_only':int(b.shadow_a_downstream_pass.sum()),
      'mapped_a_score_cut':acut,'betting_metrics_status':'NOT_COMPUTED_EXACT_PREDEADLINE_ODDS_LINEAGE_NOT_PROVEN_IN_THIS_RUN',
      'varn_n_status':'NOT_COMPUTED_EXACT_PREDEADLINE_ODDS_LINEAGE_NOT_PROVEN_IN_THIS_RUN',
      'PRE_stats':stats(b.PRE),'POST_stats':stats(b.POST),'ENV_ENTRY_stats':stats(b.ENV_ENTRY),'A_SCORE_LIVE_stats':stats(b.A_SCORE_LIVE),
    }
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# HEAD4 August 2026 PRE 0.03-0.05 shadow cohort','',
       '- **NON-PRISTINE exploratory description only. Production policy is unchanged.**',
       '- Frozen fit labels end at **2026-06-30**; July/August outcomes are not used for fitting/tuning.',
       '- Cohort is fixed only by inclusive `0.03 <= PRE <= 0.05` before outcome join.',
       f'- August all frozen-PRE rows: **{len(pred)}**',f'- Cohort: **{n}R**',f'- 4-head wins: **{wins}/{n} ({(100*wins/n if n else 0):.2f}%)**','',
       '## Frozen downstream shadow diagnostics',
       f'- POST >= {POST_S:.2f}: **{int(b.post_s_pass.sum())}R**',f'- ENV_ENTRY >= {ENV_S:.6f}: **{int(b.env_s_pass.sum())}R**',
       f'- Both S downstream gates (PRE floor intentionally bypassed): **{int(b.shadow_s_downstream_pass.sum())}R**',
       f'- A downstream gates POST >= {POST_A:.2f} and mapped A_SCORE >= {acut:.6f} (PRE floor intentionally bypassed): **{int(b.shadow_a_downstream_pass.sum())}R**','',
       '## Score distributions','|score|n|min|p25|median|p75|max|mean|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in ['PRE','POST','ENV_ENTRY','A_SCORE_LIVE']:
        x=audit[name+'_stats'];L.append(f"|{name}|{x.get('n',0)}|{x.get('min',float('nan')):.6f}|{x.get('p25',float('nan')):.6f}|{x.get('median',float('nan')):.6f}|{x.get('p75',float('nan')):.6f}|{x.get('max',float('nan')):.6f}|{x.get('mean',float('nan')):.6f}|")
    L += ['','## Betting/VARN','- Not computed in this run. Exact historical **pre-deadline** 120-way trifecta odds lineage must be proven before ROI, payout, or VARN N is reported. No post-hoc/closing substitute is allowed.','',
          '## Interpretation','- Because the frozen production A floor is PRE >= 0.18 and S floor is PRE >= 0.28, this 0.03-0.05 cohort has **0 production bets by construction**.','- These diagnostics may describe the shadow cohort but must not be used to tune/promote thresholds from August outcomes.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print(SUMMARY.read_text(encoding='utf-8'))

if __name__=='__main__':main()
