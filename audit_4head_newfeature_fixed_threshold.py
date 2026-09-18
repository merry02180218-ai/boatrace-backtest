#!/usr/bin/env python3
"""Operational fixed-threshold audit for the temporal 4HEAD new-feature score.

The score weights and ECDF reference distribution are frozen from Apr-Jun only.
The PRIMARY threshold is selected without Jul-Aug data:
- keep frozen base120;
- among Apr-Jun non-base candidates, choose a score threshold that selects
  exactly the same number of expansion races as current156 selects in Apr-Jun.

The single numeric threshold is then applied unchanged to Jul-Aug.
Sensitivity rows are diagnostic only and are never used to choose PRIMARY.

Research only; September outcomes are absent; production remains unchanged.
"""
from __future__ import annotations
from pathlib import Path
import json, math, os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_newfeature_fixed_threshold'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
MONTHS=DEV+SUP
WEIGHTS={
  'hp':2.0,'mass':4.0,'st':1.0,'orig':1.0,'market_conf':2.0,
  'motor_win_rev':4.0,'motor_2ren_rev':3.0,'attack4':3.0,
  'stwall_center':2.0,'wall_rev':1.0,
}

def numeric(s):
    return pd.to_numeric(s,errors='coerce').to_numpy(float)

def raw_features(df):
    comp=numeric(df.composite_odds)
    return {
      'hp':numeric(df.head_prob),
      'mass':numeric(df.opponent_mass),
      'st':numeric(df.st4_adv_inside),
      'orig':numeric(df.orig4_adv_inside),
      'market_conf':-np.log(np.maximum(comp,1e-9)),
      'motor_win_rev':-numeric(df.motor_win_diff_4v3),
      'motor_2ren_rev':-numeric(df.motor_2ren_diff_4v3),
      'attack4':numeric(df.attack4_score),
      'stwall_center':-np.abs(numeric(df.st_wall_gap)-.10),
      'wall_rev':-numeric(df.wall_score),
    }

def frozen_ecdf(values,train_values):
    tr=np.asarray(train_values,float)
    tr=np.sort(tr[np.isfinite(tr)])
    out=np.full(len(values),.5,float)
    v=np.asarray(values,float); ok=np.isfinite(v)
    if len(tr):
        out[ok]=np.searchsorted(tr,v[ok],side='right')/len(tr)
    return out,tr

def metrics(q):
    n=len(q); pay=float(q.payout_if_bet.sum())
    out={
      'R':int(n),'head4':int(q.head4.sum()),'head4_rate':100*float(q.head4.mean()),
      'exact3':int(q.raw_hit.sum()),'ROI':100*pay/(10000*n),
    }
    ro=[]
    for m in MONTHS:
        g=q[q.month.eq(m)]
        out[f'{m}_R']=int(len(g));out[f'{m}_head4']=int(g.head4.sum())
        out[f'{m}_head4_rate']=100*float(g.head4.mean())
        out[f'{m}_ROI']=100*float(g.payout_if_bet.sum())/(10000*len(g))
        ro.append(out[f'{m}_ROI'])
    out['monthly_floor_ROI']=min(ro)
    for name,mons in [('dev',DEV),('support',SUP)]:
        g=q[q.month.isin(mons)]
        out[f'{name}_R']=int(len(g));out[f'{name}_head4']=int(g.head4.sum())
        out[f'{name}_head4_rate']=100*float(g.head4.mean())
        out[f'{name}_exact3']=int(g.raw_hit.sum())
        out[f'{name}_ROI']=100*float(g.payout_if_bet.sum())/(10000*len(g))
    return out

def threshold_for_topk(scores,indices,k):
    idx=list(indices)
    idx=sorted(idx,key=lambda i:(-float(scores[i]),i))
    if not (1<=k<len(idx)): raise RuntimeError(f'invalid topk {k}/{len(idx)}')
    hi=float(scores[idx[k-1]]); lo=float(scores[idx[k]])
    if hi>lo:
        return (hi+lo)/2.0,hi,lo
    # Deterministic ties are a research warning. A pure numeric threshold cannot
    # split equal scores without non-score information.
    return hi,hi,lo

def main():
    p=os.environ.get('EXPANDED_FEATURES_208')
    if not p: raise RuntimeError('EXPANDED_FEATURES_208 missing')
    z=pd.read_csv(p,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
    if len(z)!=208 or int(z.base120.sum())!=120: raise RuntimeError('208/base120 parity failed')
    if any(z.month.astype(str).str.startswith('2026-09')): raise RuntimeError('SEPTEMBER ACCESS')

    base=z[z.base120].copy()
    nb=z[~z.base120].copy().reset_index(drop=True)
    if len(nb)!=88: raise RuntimeError(f'nonbase drift {len(nb)}')

    current_add=(
      nb.composite_odds.ge(3.5)&nb.quality.ge(.75)&nb.head_prob.ge(.16)&
      nb.opponent_mass.ge(.30)&nb.st4_adv_inside.ge(-.80)&nb.orig4_adv_inside.ge(-.35)
    )
    if int(current_add.sum())!=36: raise RuntimeError(f'current expansion drift {int(current_add.sum())}')
    current=pd.concat([base,nb[current_add]],ignore_index=True)
    current_m=metrics(current)

    dev_mask=nb.month.isin(DEV).to_numpy()
    sup_mask=nb.month.isin(SUP).to_numpy()
    dev_idx=np.where(dev_mask)[0]
    if (int(dev_mask.sum()),int(sup_mask.sum()))!=(50,38):
        raise RuntimeError(f'nonbase period drift {int(dev_mask.sum())}/{int(sup_mask.sum())}')

    raw=raw_features(nb)
    transformed={}
    ecdf_refs={}
    for name,vals in raw.items():
        trvals=np.asarray(vals)[dev_idx]
        transformed[name],sorted_ref=frozen_ecdf(vals,trvals)
        ecdf_refs[name]=[float(x) for x in sorted_ref]

    score=np.zeros(len(nb),float)
    for name,w in WEIGHTS.items():
        score+=float(w)*transformed[name]
    nb['newfeature_score']=score

    current_dev_add=int((current_add & nb.month.isin(DEV)).sum())
    if current_dev_add!=21:
        raise RuntimeError(f'expected current dev additions 21 got {current_dev_add}')

    primary_thr,dev_k_score,next_score=threshold_for_topk(score,dev_idx,current_dev_add)
    primary_add=score>=primary_thr
    primary=pd.concat([base,nb[primary_add]],ignore_index=True)
    primary_m=metrics(primary)

    # Sensitivity is indexed only by Apr-Jun top-k; Jul-Aug labels/volume never
    # enter threshold definition or row ordering.
    rows=[]
    for k in range(18,31):
        thr,ks,ns=threshold_for_topk(score,dev_idx,k)
        add=score>=thr
        q=pd.concat([base,nb[add]],ignore_index=True)
        mm=metrics(q)
        rows.append({
          'dev_target_k':k,'threshold':thr,'dev_k_score':ks,'dev_next_score':ns,
          'selected_add_R':int(add.sum()),'selected_dev_add_R':int((add&dev_mask).sum()),
          'selected_support_add_R':int((add&sup_mask).sum()),
          **mm,
        })
    sens=pd.DataFrame(rows)
    sens.to_csv(OUT/'threshold_sensitivity.csv',index=False)

    nb_out=nb.copy()
    for name in WEIGHTS:
        nb_out[f'ecdf_{name}']=transformed[name]
    nb_out['primary_selected']=primary_add.astype(int)
    nb_out['current156_expansion']=current_add.astype(int)
    nb_out.to_csv(OUT/'nonbase88_scored.csv',index=False)

    artifact={
      'profile':'HEAD4_NEWFEATURE_TEMPORAL_SHADOW_V1',
      'research_only':True,
      'production_applied':False,
      'source_temporal_run_id':35362985518,
      'feature_table_run_id':35361685459,
      'fit_period':['2026-04','2026-05','2026-06'],
      'weights':WEIGHTS,
      'score_transform':{
        'type':'frozen_empirical_cdf',
        'missing_value_rank':0.5,
        'market_conf':'-log(composite_odds)',
        'motor_win_rev':'-motor_win_diff_4v3',
        'motor_2ren_rev':'-motor_2ren_diff_4v3',
        'stwall_center':'-abs(st_wall_gap-0.10)',
        'wall_rev':'-wall_score',
      },
      'ecdf_sorted_reference':ecdf_refs,
      'primary_threshold_rule':'Apr-Jun threshold selecting same 21 expansion races count as current156 dev period',
      'primary_threshold':float(primary_thr),
      'threshold_boundary':{'dev_k':current_dev_add,'k_score':dev_k_score,'next_score':next_score},
      'selection':'base120 OR (not base120 AND newfeature_score >= primary_threshold)',
      'target_result_used':False,
      'payout_used_for_live_score':False,
      'september_outcomes_used':False,
    }
    (OUT/'shadow_artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    result={
      'current156':current_m,
      'frozen_weights':WEIGHTS,
      'primary_threshold':float(primary_thr),
      'primary_threshold_dev_target_k':current_dev_add,
      'primary_threshold_dev_k_score':dev_k_score,
      'primary_threshold_dev_next_score':next_score,
      'primary_fixed_threshold':primary_m,
      'primary_selected_add_R':int(primary_add.sum()),
      'primary_selected_dev_add_R':int((primary_add&dev_mask).sum()),
      'primary_selected_support_add_R':int((primary_add&sup_mask).sum()),
      'sensitivity_rows':int(len(sens)),
      'threshold_selection_used_support_data':False,
      'score_uses_outcomes':False,
      'SEARCH_DEV_IS_NON_PRISTINE':True,
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    print('\nTHRESHOLD SENSITIVITY',flush=True)
    print(sens.to_string(index=False),flush=True)
    print('HEAD4_NEWFEATURE_FIXED_THRESHOLD_OK',flush=True)
    print('SEPTEMBER_UNREAD',flush=True)

if __name__=='__main__': main()
