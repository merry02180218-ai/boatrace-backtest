#!/usr/bin/env python3
"""Extend fixed-threshold temporal new-feature volume frontier beyond 165R.

Weights and Apr-Jun ECDF are frozen. Each threshold is defined by Apr-Jun top-k
only (k=31..45) and then applied unchanged to Jul-Aug. Jul-Aug outcomes never
select the threshold. Production is not changed by this audit.
"""
from __future__ import annotations
from pathlib import Path
import json, os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_newfeature_volume_extension');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-04','2026-05','2026-06');SUP=('2026-07','2026-08');MONTHS=DEV+SUP
WEIGHTS={'hp':2.0,'mass':4.0,'st':1.0,'orig':1.0,'market_conf':2.0,'motor_win_rev':4.0,'motor_2ren_rev':3.0,'attack4':3.0,'stwall_center':2.0,'wall_rev':1.0}

def n(s):return pd.to_numeric(s,errors='coerce').to_numpy(float)
def raw(df):
    comp=n(df.composite_odds)
    return {'hp':n(df.head_prob),'mass':n(df.opponent_mass),'st':n(df.st4_adv_inside),'orig':n(df.orig4_adv_inside),
      'market_conf':-np.log(np.maximum(comp,1e-9)),'motor_win_rev':-n(df.motor_win_diff_4v3),
      'motor_2ren_rev':-n(df.motor_2ren_diff_4v3),'attack4':n(df.attack4_score),
      'stwall_center':-np.abs(n(df.st_wall_gap)-.10),'wall_rev':-n(df.wall_score)}

def ecdf(vals,train):
    tr=np.sort(np.asarray(train)[np.isfinite(train)])
    out=np.full(len(vals),.5,float);ok=np.isfinite(vals)
    out[ok]=np.searchsorted(tr,np.asarray(vals)[ok],side='right')/len(tr)
    return out

def met(q):
    out={'R':len(q),'head4':int(q.head4.sum()),'head4_rate':100*float(q.head4.mean()),'exact3':int(q.raw_hit.sum()),'ROI':100*float(q.payout_if_bet.sum())/(10000*len(q))}
    ro=[]
    for m in MONTHS:
        g=q[q.month.eq(m)];r=100*float(g.payout_if_bet.sum())/(10000*len(g));out[f'{m}_R']=len(g);out[f'{m}_ROI']=r;ro.append(r)
    out['monthly_floor_ROI']=min(ro)
    for nm,mons in [('dev',DEV),('support',SUP)]:
        g=q[q.month.isin(mons)];out[f'{nm}_R']=len(g);out[f'{nm}_head4']=int(g.head4.sum());out[f'{nm}_head4_rate']=100*float(g.head4.mean());out[f'{nm}_exact3']=int(g.raw_hit.sum());out[f'{nm}_ROI']=100*float(g.payout_if_bet.sum())/(10000*len(g))
    return out

def threshold(scores,idx,k):
    o=sorted(idx,key=lambda i:(-float(scores[i]),i))
    return (float(scores[o[k-1]])+float(scores[o[k]]))/2

def main():
    p=os.environ['EXPANDED_FEATURES_208'];z=pd.read_csv(p,dtype={'race_code':str});z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
    if len(z)!=208 or int(z.base120.sum())!=120:raise RuntimeError('parity')
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')
    base=z[z.base120].copy();nb=z[~z.base120].copy().reset_index(drop=True)
    dev=np.where(nb.month.isin(DEV))[0]
    R=raw(nb);score=np.zeros(len(nb))
    for name,w in WEIGHTS.items():score+=w*ecdf(R[name],R[name][dev])
    rows=[]
    for k in range(31,46):
        t=threshold(score,dev,k);add=score>=t;q=pd.concat([base,nb[add]],ignore_index=True);rows.append({'dev_target_k':k,'threshold':t,'selected_add_R':int(add.sum()),**met(q)})
    g=pd.DataFrame(rows);g.to_csv(OUT/'volume_extension.csv',index=False)
    # practical frontiers, ranking does not alter thresholds; diagnostics only.
    result={
      'rows':rows,
      'max_R_with_ROI_ge130':int(g[g.ROI>=130].R.max()) if (g.ROI>=130).any() else None,
      'max_R_with_head_ge44_and_ROI_ge130':int(g[(g.head4_rate>=44)&(g.ROI>=130)].R.max()) if ((g.head4_rate>=44)&(g.ROI>=130)).any() else None,
      'max_R_with_head_ge43_and_ROI_ge125':int(g[(g.head4_rate>=43)&(g.ROI>=125)].R.max()) if ((g.head4_rate>=43)&(g.ROI>=125)).any() else None,
      'threshold_selection_used_support_data':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str));print('HEAD4_NEWFEATURE_VOLUME_EXTENSION_OK');print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
