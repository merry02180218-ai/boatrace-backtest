#!/usr/bin/env python3
"""Inference-only scorer for frozen HEAD4_V273 A-rank LIVE artifact.

No fitting, outcomes, payout data, network, or v96 fallback.  S always has
priority; A is evaluated only outside S.  Missing feature keys fail closed;
present NaN values use the frozen median imputer.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any,Mapping
import json,math
import numpy as np

ROOT=Path(__file__).resolve().parent
DEFAULT_ARTIFACT=ROOT/'artifacts'/'head4_v273_a_live_20260630.json'
POLICY='HEAD4_V273_A_LIVE_QMAP'
CUTOFF='2026-06-30'

class FrozenARankError(RuntimeError):pass

def _f(x):
    try:return float(x)
    except (TypeError,ValueError):return float('nan')

def validate_artifact(a:Mapping[str,Any])->None:
    if a.get('schema')!='head4_v273_a_live_artifact_v1':raise FrozenARankError('A artifact schema mismatch')
    if a.get('policy')!=POLICY or a.get('frozen_training_cutoff')!=CUTOFF:raise FrozenARankError('A artifact policy/cutoff mismatch')
    if a.get('production_inference_only') is not True:raise FrozenARankError('A artifact not inference-only')
    for k in ('jul_aug_labels_used','september_labels_used','v96_production_signal_used'):
        if a.get(k) is not False:raise FrozenARankError(f'prohibited metadata {k}')
    mp=a.get('mapping') or {}
    if mp.get('method')!='OUTCOME_BLIND_SELECTED_FRACTION_QUANTILE' or mp.get('outcomes_used_by_mapping') is not False:raise FrozenARankError('A score mapping is not frozen outcome-blind')
    gate=a.get('A_gate') or {};sg=a.get('S_gate') or {}
    expa={'PRE':.18,'POST':.18};exps={'PRE':.28,'POST':.25,'ENV_ENTRY':.224790}
    for k,v in expa.items():
        if abs(float(gate.get(k,float('nan')))-v)>1e-12:raise FrozenARankError(f'A gate mismatch {k}')
    for k,v in exps.items():
        if abs(float(sg.get(k,float('nan')))-v)>1e-12:raise FrozenARankError(f'S gate mismatch {k}')
    cut=float(gate.get('A_SCORE_LIVE',float('nan')))
    if not math.isfinite(cut) or not 0<cut<1:raise FrozenARankError('invalid mapped A threshold')
    st=a.get('A_SCORE') or {};fs=list(st.get('features') or [])
    if len(fs)!=17 or len(set(fs))!=17:raise FrozenARankError('A feature order invalid')
    n=len(fs)
    for k in ('imputer_median','scaler_mean','scaler_scale','coef'):
        x=np.asarray(st.get(k,[]),float)
        if len(x)!=n or not np.isfinite(x).all():raise FrozenARankError(f'invalid A frozen state {k}')
    if (np.asarray(st['scaler_scale'],float)<=0).any():raise FrozenARankError('invalid scaler scale')
    if not math.isfinite(float(st.get('intercept',float('nan')))):raise FrozenARankError('invalid intercept')

def load_artifact(path: str|Path=DEFAULT_ARTIFACT):
    p=Path(path)
    if not p.is_file():raise FrozenARankError(f'missing A artifact {p}')
    a=json.loads(p.read_text(encoding='utf-8'));validate_artifact(a);return a

def score_a(row:Mapping[str,Any],a:Mapping[str,Any])->float:
    validate_artifact(a);st=a['A_SCORE'];fs=st['features'];missing=[c for c in fs if c not in row]
    if missing:raise FrozenARankError('missing LIVE A features: '+','.join(missing[:12]))
    x=np.asarray([_f(row[c]) for c in fs],float);med=np.asarray(st['imputer_median'],float)
    x=np.where(np.isnan(x),med,x)
    if not np.isfinite(x).all():raise FrozenARankError('non-finite A input after frozen imputation')
    x=(x-np.asarray(st['scaler_mean'],float))/np.asarray(st['scaler_scale'],float)
    z=float(st['intercept'])+float(x@np.asarray(st['coef'],float))
    if z>=0:return 1/(1+math.exp(-z))
    e=math.exp(z);return e/(1+e)

def classify(pre:float,post:float,env_entry:float,a_row:Mapping[str,Any],artifact:Mapping[str,Any])->dict[str,Any]:
    validate_artifact(artifact);pre=float(pre);post=float(post);env=float(env_entry)
    if not all(math.isfinite(x) for x in (pre,post,env)):raise FrozenARankError('non-finite S/A gate input')
    sg=artifact['S_gate'];ag=artifact['A_gate']
    if pre>=sg['PRE'] and post>=sg['POST'] and env>=sg['ENV_ENTRY']:
        return {'layer':'S','eligible':True,'A_SCORE_LIVE':None,'policy':POLICY,'reason':'S_PRIORITY'}
    if pre<ag['PRE'] or post<ag['POST']:
        return {'layer':'NONE','eligible':False,'A_SCORE_LIVE':None,'policy':POLICY,'reason':'A_PRE_POST_FAIL'}
    p=score_a(a_row,artifact);ok=p>=float(ag['A_SCORE_LIVE'])
    return {'layer':'A' if ok else 'NONE','eligible':bool(ok),'A_SCORE_LIVE':p,'A_SCORE_LIVE_CUT':float(ag['A_SCORE_LIVE']),
            'policy':POLICY,'reason':'A_PASS' if ok else 'A_SCORE_FAIL'}

if __name__=='__main__':
    a=load_artifact();print(json.dumps({'status':'ARTIFACT_VALID','policy':a['policy'],'mapped_A_cut':a['A_gate']['A_SCORE_LIVE']},ensure_ascii=False,indent=2))
