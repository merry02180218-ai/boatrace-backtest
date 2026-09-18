#!/usr/bin/env python3
"""Temporal holdout audit for the exact156 new-feature ranker.

Selection of score weights uses Apr-Jun outcomes only.
Jul-Aug outcomes are never used to choose weights; they are reported only after
the weight vector is frozen.

To make a like-for-like 156R comparison, expansion quotas are held to the
current156 monthly counts:
Apr/May/Jun = 3/11/7 additions, Jul/Aug = 13/2 additions.
Frozen base120 remains unchanged.
"""
from __future__ import annotations
from pathlib import Path
import itertools,json,os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_156r_newfeature_temporal_holdout');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-04','2026-05','2026-06');SUP=('2026-07','2026-08');MONTHS=DEV+SUP
QUOTA={'2026-04':3,'2026-05':11,'2026-06':7,'2026-07':13,'2026-08':2}

W_HP=(0,1,2);W_MASS=(4,5,6);W_ST=(1,2,3);W_ORIG=(0,1);W_MKT=(0,1,2)
W_MWIN=(3,4,5);W_M2=(1,2,3);W_ATTACK=(2,3,4);W_STWALL=(2,3,4);W_WALL=(1,2,3)

def raw_features(df):
    def n(c):return pd.to_numeric(df[c],errors='coerce').to_numpy(float)
    return {
      'hp':n('head_prob'),
      'mass':n('opponent_mass'),
      'st':n('st4_adv_inside'),
      'orig':n('orig4_adv_inside'),
      'market_conf':-np.log(np.maximum(n('composite_odds'),1e-9)),
      'motor_win_rev':-n('motor_win_diff_4v3'),
      'motor_2ren_rev':-n('motor_2ren_diff_4v3'),
      'attack4':n('attack4_score'),
      'stwall_center':-np.abs(n('st_wall_gap')-.10),
      'wall_rev':-n('wall_score'),
    }

def ecdf_from_dev(arr,dev_idx):
    train=np.asarray(arr)[dev_idx]
    train=train[np.isfinite(train)]
    out=np.full(len(arr),.5,float)
    if not len(train):return out
    s=np.sort(train);ok=np.isfinite(arr)
    out[ok]=np.searchsorted(s,np.asarray(arr)[ok],side='right')/len(s)
    return out

def period_metrics(base,nb,sel,mons):
    q=pd.concat([base[base.month.isin(mons)],nb.iloc[list(sel)]],ignore_index=True)
    n=len(q);out={
      'R':int(n),'head4':int(q.head4.sum()),'head4_rate':100*float(q.head4.mean()),
      'exact3':int(q.raw_hit.sum()),'ROI':100*float(q.payout_if_bet.sum())/(10000*n),
    }
    ro=[]
    for m in mons:
        g=q[q.month.eq(m)]
        out[f'{m}_R']=int(len(g));out[f'{m}_head4']=int(g.head4.sum())
        out[f'{m}_head4_rate']=100*float(g.head4.mean())
        out[f'{m}_ROI']=100*float(g.payout_if_bet.sum())/(10000*len(g))
        ro.append(out[f'{m}_ROI'])
    out['monthly_floor_ROI']=min(ro)
    return out

def combined_metrics(base,nb,sel):
    q=pd.concat([base,nb.iloc[list(sel)]],ignore_index=True)
    n=len(q);out={
      'R':int(n),'head4':int(q.head4.sum()),'head4_rate':100*float(q.head4.mean()),
      'exact3':int(q.raw_hit.sum()),'ROI':100*float(q.payout_if_bet.sum())/(10000*n),
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

def choose_month(score,nb,month,k):
    ix=np.where(nb.month.astype(str).to_numpy()==month)[0]
    hp=pd.to_numeric(nb.head_prob,errors='coerce').to_numpy(float)
    ma=pd.to_numeric(nb.opponent_mass,errors='coerce').to_numpy(float)
    codes=nb.race_code.astype(str).to_numpy()
    o=np.lexsort((codes[ix],-ma[ix],-hp[ix],-score[ix]))
    return tuple(ix[o[:k]].tolist())

def main():
    p=os.environ.get('EXPANDED_FEATURES_208')
    if not p:raise RuntimeError('EXPANDED_FEATURES_208 missing')
    z=pd.read_csv(p,dtype={'race_code':str});z['race_code']=z.race_code.astype(str).str.zfill(12)
    z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
    if len(z)!=208 or int(z.base120.sum())!=120:raise RuntimeError('universe parity failed')
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')

    base=z[z.base120].copy();nb=z[~z.base120].copy().reset_index(drop=True)
    dev_idx=np.where(nb.month.isin(DEV))[0];sup_idx=np.where(nb.month.isin(SUP))[0]
    if (len(dev_idx),len(sup_idx))!=(50,38):raise RuntimeError(f'period candidate drift {(len(dev_idx),len(sup_idx))}')

    current=(nb.composite_odds>=3.5)&(nb.quality>=.75)&(nb.head_prob>=.16)&(nb.opponent_mass>=.30)&(nb.st4_adv_inside>=-.80)&(nb.orig4_adv_inside>=-.35)
    current_sel=np.where(current)[0]
    if len(current_sel)!=36:raise RuntimeError('current36 drift')
    for m,k in QUOTA.items():
        if int((current & nb.month.eq(m)).sum())!=k:raise RuntimeError(f'current monthly quota drift {m}')
    cur=combined_metrics(base,nb,current_sel)
    cur_dev=period_metrics(base,nb,np.where(current & nb.month.isin(DEV))[0],DEV)
    cur_sup=period_metrics(base,nb,np.where(current & nb.month.isin(SUP))[0],SUP)

    raw=raw_features(nb)
    names=list(raw)
    F=np.column_stack([ecdf_from_dev(raw[k],dev_idx) for k in names])

    # Collapse by Apr-Jun membership. When several weights produce the same dev
    # membership, freeze the lowest L1 weight sum, then lexicographically.
    sets={}
    cells=0
    for w in itertools.product(W_HP,W_MASS,W_ST,W_ORIG,W_MKT,W_MWIN,W_M2,W_ATTACK,W_STWALL,W_WALL):
        cells+=1
        score=F@np.asarray(w,float)
        ds=[]
        for m in DEV:ds.extend(choose_month(score,nb,m,QUOTA[m]))
        ds=tuple(sorted(ds))
        dm=period_metrics(base,nb,ds,DEV)
        rec=sets.get(ds)
        candidate=(sum(w),tuple(w))
        if rec is None:
            sets[ds]={'plateau_cells':1,'best_weight_key':candidate,'weights':tuple(w),'dev':dm}
        else:
            rec['plateau_cells']+=1
            if candidate<rec['best_weight_key']:
                rec['best_weight_key']=candidate;rec['weights']=tuple(w)

    rows=[]
    for sel,rec in sets.items():
        dm=rec['dev'];w=rec['weights']
        rows.append({
          'dev_selection':sel,'plateau_cells':rec['plateau_cells'],
          'weight_sum':sum(w),
          'w_hp':w[0],'w_mass':w[1],'w_st':w[2],'w_orig':w[3],'w_market':w[4],
          'w_motor_win_rev':w[5],'w_motor_2ren_rev':w[6],'w_attack4':w[7],
          'w_stwall_center':w[8],'w_wall_rev':w[9],
          **{f'dev_{k}':v for k,v in dm.items()}
        })
    g=pd.DataFrame(rows)
    eligible=g[
      (g.dev_ROI>=cur_dev['ROI']-1e-9)&
      (g.dev_monthly_floor_ROI>=cur_dev['monthly_floor_ROI']-1e-9)
    ].copy()
    if eligible.empty:raise RuntimeError('no dev-eligible weight membership')
    # Predeclared dev-only ranking: head rate, exact3, ROI, monthly floor,
    # plateau stability, then lower weight sum.
    eligible=eligible.sort_values(
      ['dev_head4_rate','dev_exact3','dev_ROI','dev_monthly_floor_ROI','plateau_cells','weight_sum'],
      ascending=[False,False,False,False,False,True]
    )
    freeze=eligible.iloc[0]
    w=np.asarray([
      freeze.w_hp,freeze.w_mass,freeze.w_st,freeze.w_orig,freeze.w_market,
      freeze.w_motor_win_rev,freeze.w_motor_2ren_rev,freeze.w_attack4,
      freeze.w_stwall_center,freeze.w_wall_rev
    ],float)
    score=F@w
    dev_sel=tuple(freeze.dev_selection)
    sup_sel=[]
    for m in SUP:sup_sel.extend(choose_month(score,nb,m,QUOTA[m]))
    sup_sel=tuple(sorted(sup_sel))
    combined=tuple(sorted(dev_sel+sup_sel))

    support=period_metrics(base,nb,sup_sel,SUP)
    allm=combined_metrics(base,nb,combined)

    # Month-quota selection lets us compare exactly 156R without support labels
    # participating in the weight freeze.
    detail=nb.iloc[list(combined)].copy()
    detail['selected_period']=np.where(detail.month.isin(DEV),'DEV_FROZEN','SUPPORT_UNREAD_AT_FREEZE')
    detail.to_csv(OUT/'frozen_selected_36.csv',index=False)
    eligible.drop(columns=['dev_selection']).head(500).to_csv(OUT/'dev_ranked_top500.csv',index=False)

    result={
      'current156':cur,
      'current_dev':cur_dev,
      'current_support':cur_sup,
      'feature_names':names,
      'grid_cells':cells,
      'unique_dev_memberships':int(len(g)),
      'dev_eligible_memberships':int(len(eligible)),
      'freeze_rule':'Apr-Jun only: ROI>=current dev AND dev monthly floor>=current dev; maximize dev head4 rate -> exact3 -> ROI -> floor -> plateau -> lower weight sum',
      'frozen_weights':{
        'hp':float(freeze.w_hp),'mass':float(freeze.w_mass),'st':float(freeze.w_st),'orig':float(freeze.w_orig),
        'market':float(freeze.w_market),'motor_win_rev':float(freeze.w_motor_win_rev),
        'motor_2ren_rev':float(freeze.w_motor_2ren_rev),'attack4':float(freeze.w_attack4),
        'stwall_center':float(freeze.w_stwall_center),'wall_rev':float(freeze.w_wall_rev),
        'weight_sum':int(freeze.weight_sum),'dev_plateau_cells':int(freeze.plateau_cells),
      },
      'frozen_dev_metrics':period_metrics(base,nb,dev_sel,DEV),
      'support_report_after_freeze':support,
      'combined_exact156':allm,
      'support_outcomes_used_to_choose_weights':False,
      'selection_score_uses_outcome':False,
      'SEARCH_DEV_IS_NON_PRISTINE':True,
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    print('HEAD4_156R_NEWFEATURE_TEMPORAL_HOLDOUT_OK',flush=True)
    print('SEPTEMBER_UNREAD',flush=True)

if __name__=='__main__':main()
