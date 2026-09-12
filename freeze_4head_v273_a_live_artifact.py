#!/usr/bin/env python3
"""Freeze the v273 A-rank model onto a single production LIVE score scale.

The v273 threshold 0.28 was frozen on Apr-Jun month-walk-forward OOF scores.
A single final model fitted through 2026-06-30 has a different probability
scale, so raw 0.28 must not be copied into LIVE.  This script reproduces the
frozen OOF scores, fits the final model using ONLY <=2026-06-30 outcomes, then
maps the frozen OOF selection semantics to the final score scale using only the
score DISTRIBUTION of the same pre-result A-eligible reference races.  No race
outcome is consulted by the mapping step.

July/August and September labels are prohibited.  The output serializes only
inference state (feature order, imputer, scaler, coefficients, intercept) plus
the outcome-blind mapped threshold and audit metadata.
"""
from __future__ import annotations
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd

import analyze_v264_4head_feature_exhaustive as v264
import analyze_v270_4head_win_feature_importance as v270
import analyze_v271_4head_arank_expansion as v271

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts'/'head4_v273_a_live_20260630.json'
REPORT=ROOT/'artifacts'/'head4_v273_a_live_mapping_20260630.json'
OLD_DETAIL=ROOT/'analysis_v271_4head_arank_races.csv'
CUTOFF=pd.Timestamp('2026-06-30')
CUTOFF_STR='2026-06-30'
POLICY='HEAD4_V273_A_LIVE_QMAP'
OOF_CUT=.28
A_PRE=.18
A_POST=.18
S_PRE=.28
S_POST=.25
S_ENV=.224790
A_FEATURES=tuple(v271.A_FEATURES)
EVAL_MONTHS=('2026-04','2026-05','2026-06')


def numdf(d,fs):return d[list(fs)].apply(lambda s:pd.to_numeric(s,errors='coerce'))


def state_from_pipe(m,features):
    imp=m.named_steps['imp'];sc=m.named_steps['sc'];lr=m.named_steps['lr']
    q={
      'kind':'standardized_logistic','features':list(features),
      'imputer_median':[float(x) for x in imp.statistics_],
      'scaler_mean':[float(x) for x in sc.mean_],
      'scaler_scale':[float(x) for x in sc.scale_],
      'coef':[float(x) for x in lr.coef_[0]],'intercept':float(lr.intercept_[0]),
    }
    for k in ('imputer_median','scaler_mean','scaler_scale','coef'):
        if len(q[k])!=len(features) or not np.isfinite(np.asarray(q[k],float)).all():raise RuntimeError(f'invalid frozen state {k}')
    if not math.isfinite(q['intercept']):raise RuntimeError('invalid intercept')
    if any(x<=0 for x in q['scaler_scale']):raise RuntimeError('non-positive scaler scale')
    return q


def main():
    # Reproduce the exact frozen v271 OOF semantics.  v271 itself hard-excludes
    # Jul/Aug in its prepare lineage; we additionally assert the final fit cutoff.
    oof=v271.oof_a_scores().copy()
    oof['race_code']=oof.race_code.astype(str).str.zfill(12)
    oof=oof[oof.month.astype(str).isin(EVAL_MONTHS)].copy()
    if set(oof.month.astype(str).unique())!=set(EVAL_MONTHS):raise RuntimeError('OOF reference months incomplete')

    parity={'available':False}
    if OLD_DETAIL.is_file():
        old=pd.read_csv(OLD_DETAIL,dtype={'race_code':str});old['race_code']=old.race_code.astype(str).str.zfill(12)
        z=oof[['race_code','a_score']].merge(old[['race_code','a_score']],on='race_code',suffixes=('_new','_old'))
        if len(z):
            mx=float((z.a_score_new-z.a_score_old).abs().max())
            parity={'available':True,'n':int(len(z)),'max_abs':mx,'status':'PASS' if mx<=1e-10 else 'FAIL'}
            if mx>1e-10:raise RuntimeError(f'v271 OOF parity failed max_abs={mx}')

    d,_,_=v270.prepare();d=d.copy();d['_date']=pd.to_datetime(d['_date'],errors='coerce')
    d=d[d._date<=CUTOFF].copy()
    if d.empty or d._date.max()>CUTOFF:raise RuntimeError('final-fit cutoff violation')
    missing=[c for c in A_FEATURES if c not in d.columns]
    if missing:raise RuntimeError('missing final A features: '+','.join(missing))
    weak=[c for c in A_FEATURES if not v264.goodcol(d,c,.55)]
    if weak:raise RuntimeError('A feature coverage failed: '+','.join(weak))
    m=v264.lr_model();m.fit(numdf(d,A_FEATURES),d.y4.astype(int))
    frozen=state_from_pipe(m,A_FEATURES)

    # Frozen A universe: broad PRE/POST gate and outside S.  Selection fraction
    # comes ONLY from the already-frozen OOF score threshold, not outcomes.
    elig=oof[(pd.to_numeric(oof.PRE,errors='coerce')>=A_PRE)&(pd.to_numeric(oof.POST,errors='coerce')>=A_POST)].copy()
    is_s=(pd.to_numeric(elig.PRE,errors='coerce')>=S_PRE)&(pd.to_numeric(elig.POST,errors='coerce')>=S_POST)&(pd.to_numeric(elig.ENV_ENTRY,errors='coerce')>=S_ENV)
    elig=elig[~is_s].copy()
    if len(elig)<20:raise RuntimeError('A mapping reference too small')
    k=int((pd.to_numeric(elig.a_score,errors='coerce')>=OOF_CUT).sum())
    if not (0<k<len(elig)):raise RuntimeError('invalid frozen OOF selected count')

    ref=d[['race_code',*A_FEATURES]].copy();ref['race_code']=ref.race_code.astype(str).str.zfill(12)
    z=elig[['race_code','month','a_score']].merge(ref,on='race_code',how='inner',validate='one_to_one')
    if len(z)!=len(elig):raise RuntimeError(f'final-score mapping rows missing {len(z)}/{len(elig)}')
    z['final_score']=m.predict_proba(numdf(z,A_FEATURES))[:,1]
    vals=np.sort(z.final_score.to_numpy(float))[::-1]
    hi=float(vals[k-1]);lo=float(vals[k])
    mapped=float((hi+lo)/2.0) if hi>lo else hi
    mapped_count=int((z.final_score>=mapped).sum())
    if mapped_count!=k:raise RuntimeError(f'quantile mapping tie prevented exact count {mapped_count}!={k}')

    month_audit=[]
    for mon in EVAL_MONTHS:
        g=z[z.month.astype(str)==mon]
        month_audit.append({'month':mon,'reference_R':int(len(g)),
                            'oof_selected_R':int((g.a_score>=OOF_CUT).sum()),
                            'mapped_final_selected_R':int((g.final_score>=mapped).sum())})

    mapping={
      'method':'OUTCOME_BLIND_SELECTED_FRACTION_QUANTILE',
      'reference_months':list(EVAL_MONTHS),'reference_universe':'outside_S AND PRE>=0.18 AND POST>=0.18',
      'oof_threshold':OOF_CUT,'reference_R':int(len(z)),'oof_selected_R':k,
      'selected_fraction':float(k/len(z)),'mapped_live_threshold':mapped,
      'mapped_selected_R':mapped_count,'month_count_audit':month_audit,
      'outcomes_used_by_mapping':False,
    }
    artifact={
      'schema':'head4_v273_a_live_artifact_v1','policy':POLICY,'frozen_training_cutoff':CUTOFF_STR,
      'production_inference_only':True,'jul_aug_labels_used':False,'september_labels_used':False,
      'v96_production_signal_used':False,'model_family':'median+standardscale+logistic_C0.18',
      'priority':'S_FIRST_A_ONLY_OUTSIDE_S','S_gate':{'PRE':S_PRE,'POST':S_POST,'ENV_ENTRY':S_ENV},
      'A_gate':{'PRE':A_PRE,'POST':A_POST,'A_SCORE_LIVE':mapped},'frozen_oof_A_cut':OOF_CUT,
      'mapping':mapping,'A_SCORE':frozen,'oof_parity':parity,
      'training':{'max_training_date':str(d._date.max().date()),'rows':int(len(d)),'features':len(A_FEATURES)},
    }
    report={'status':'PASS','policy':POLICY,'cutoff':CUTOFF_STR,'parity':parity,'mapping':mapping,
            'jul_aug_labels_used':False,'september_labels_used':False,'v96_production_signal_used':False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
