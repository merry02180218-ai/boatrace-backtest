#!/usr/bin/env python3
"""Exact156 new-feature frontier around the expanded 208R universe.

Frozen base120 is never changed. Exactly 36 of 88 non-base candidates are
selected by a causal feature score. The score adds wall3 and motor features
to the previous head_prob/mass/ST/ORIG/market family.

This is NON-PRISTINE Apr-Aug retrospective research. Outcomes/payouts are used
only to evaluate score memberships, never as score inputs. September is absent.
Production remains unchanged.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, itertools, json, os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_156r_newfeature_frontier');OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
DEV=('2026-04','2026-05','2026-06');SUP=('2026-07','2026-08')

# Deterministic neighborhood around the promising feature balance.
W_HP=(0,1,2)
W_MASS=(4,5,6)
W_ST=(1,2,3)
W_ORIG=(0,1)
W_MKT=(0,1,2)
W_MWIN=(3,4,5)
W_M2=(1,2,3)
W_ATTACK=(2,3,4)
W_STWALL=(2,3,4)
W_WALL=(1,2,3)

CURRENT_ROI=128.58653846153845
CURRENT_FLOOR=91.575
CURRENT_SUPPORT_ROI=115.0453125

def rankpct(s,reverse=False,neutral_missing=True):
    x=pd.to_numeric(pd.Series(s),errors='coerce')
    ok=x.notna()
    out=np.full(len(x),.5,dtype=float)
    if ok.any():
        v=-x[ok] if reverse else x[ok]
        out[np.where(ok)[0]]=v.rank(method='average',pct=True).to_numpy(float)
    return out

def metrics(z,base,nb,sel):
    q=pd.concat([base,nb.iloc[list(sel)]],ignore_index=True)
    n=len(q); out={
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

def membership_hash(codes):
    return hashlib.sha256(';'.join(sorted(codes)).encode()).hexdigest()[:16]

def main():
    p=os.environ.get('EXPANDED_FEATURES_208')
    if not p:raise RuntimeError('EXPANDED_FEATURES_208 missing')
    z=pd.read_csv(p,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
    if len(z)!=208 or int(z.base120.sum())!=120:raise RuntimeError('208/base120 parity failed')
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')

    base=z[z.base120].copy()
    nb=z[~z.base120].copy().reset_index(drop=True)
    if len(nb)!=88:raise RuntimeError(f'nonbase drift {len(nb)}')

    current=(nb.composite_odds>=3.5)&(nb.quality>=.75)&(nb.head_prob>=.16)&(nb.opponent_mass>=.30)&(nb.st4_adv_inside>=-.80)&(nb.orig4_adv_inside>=-.35)
    if int(current.sum())!=36:raise RuntimeError('current expansion drift')
    cur=metrics(z,base,nb,np.where(current)[0])
    if cur['head4']!=65 or abs(cur['ROI']-CURRENT_ROI)>.02:raise RuntimeError(f'current156 parity {cur}')

    # causal ranks; missing wall values are neutral 0.5, never outcome-imputed.
    feat={
      'hp':rankpct(nb.head_prob),
      'mass':rankpct(nb.opponent_mass),
      'st':rankpct(nb.st4_adv_inside),
      'orig':rankpct(nb.orig4_adv_inside),
      'market_conf':rankpct(np.log(np.maximum(pd.to_numeric(nb.composite_odds,errors='coerce'),1e-9)),reverse=True),
      # In this parent universe lower 4v3 motor diffs are the research direction being tested.
      'motor_win_rev':rankpct(nb.motor_win_diff_4v3,reverse=True),
      'motor_2ren_rev':rankpct(nb.motor_2ren_diff_4v3,reverse=True),
      'attack4':rankpct(nb.attack4_score),
      # formal wall audit suggests the useful ST wall region is near slight 3-vs-4 positive balance.
      'stwall_center':rankpct(-(pd.to_numeric(nb.st_wall_gap,errors='coerce')-.10).abs()),
      'wall_rev':rankpct(nb.wall_score,reverse=True),
    }
    order_names=list(feat)
    F=np.column_stack([feat[k] for k in order_names])
    hp=np.asarray(nb.head_prob,float);mass=np.asarray(nb.opponent_mass,float);codes=np.asarray(nb.race_code,str)

    unique={}
    cells=0
    for w in itertools.product(W_HP,W_MASS,W_ST,W_ORIG,W_MKT,W_MWIN,W_M2,W_ATTACK,W_STWALL,W_WALL):
        cells+=1
        score=F@np.asarray(w,float)
        order=np.lexsort((codes,-mass,-hp,-score))
        sel=tuple(sorted(order[:36].tolist()))
        scodes=tuple(sorted(codes[list(sel)].tolist()))
        h=membership_hash(scodes)
        rec=unique.get(h)
        if rec is None:
            mm=metrics(z,base,nb,sel)
            unique[h]={
              'set_hash':h,'plateau_cells':1,
              'w_hp':w[0],'w_mass':w[1],'w_st':w[2],'w_orig':w[3],
              'w_market':w[4],'w_motor_win_rev':w[5],'w_motor_2ren_rev':w[6],
              'w_attack4':w[7],'w_stwall_center':w[8],'w_wall_rev':w[9],
              **mm,'codes':';'.join(scodes)
            }
        else:
            rec['plateau_cells']+=1

    g=pd.DataFrame(unique.values())
    roi=g[g.ROI>=cur['ROI']-1e-9].copy()
    robust=roi[
      (roi.monthly_floor_ROI>=cur['monthly_floor_ROI']-1e-9)&
      (roi.support_ROI>=cur['support_ROI']-1e-9)
    ].copy()

    def rank(df):
        if df.empty:return df
        return df.sort_values(
          ['head4_rate','exact3','ROI','plateau_cells','support_head4_rate'],
          ascending=[False,False,False,False,False]
        )
    roi=rank(roi);robust=rank(robust)
    floor90=rank(g[(g.ROI>=cur['ROI']-1e-9)&(g.monthly_floor_ROI>=90)])
    floor85=rank(g[(g.ROI>=cur['ROI']-1e-9)&(g.monthly_floor_ROI>=85)])

    # Dev-only freeze candidate: ranking does not use Jul-Aug outcome metrics.
    dev=g[
      (g.dev_ROI>=cur['dev_ROI']-1e-9)&
      (g.dev_monthly_floor_ROI if 'dev_monthly_floor_ROI' in g.columns else pd.Series(False,index=g.index))
    ].copy() if False else g.copy()
    dev=dev.sort_values(
      ['dev_head4_rate','dev_ROI','plateau_cells'],
      ascending=[False,False,False]
    )
    dev_best=dev.iloc[0].to_dict()

    # Ablation of the best robust weight vector without re-optimizing labels.
    ablations=[]
    if len(robust):
        b=robust.iloc[0]
        bw=np.asarray([
          b.w_hp,b.w_mass,b.w_st,b.w_orig,b.w_market,b.w_motor_win_rev,
          b.w_motor_2ren_rev,b.w_attack4,b.w_stwall_center,b.w_wall_rev
        ],float)
        for label,ixs in [
          ('FULL',()),
          ('NO_MOTOR',(5,6)),
          ('NO_WALL',(7,8,9)),
          ('NO_MOTOR_WIN',(5,)),
          ('NO_MOTOR_2REN',(6,)),
          ('NO_ATTACK4',(7,)),
          ('NO_STWALL_CENTER',(8,)),
          ('NO_WALL_SCORE',(9,)),
        ]:
            w=bw.copy()
            for ix in ixs:w[ix]=0
            score=F@w
            order=np.lexsort((codes,-mass,-hp,-score))
            mm=metrics(z,base,nb,tuple(sorted(order[:36].tolist())))
            ablations.append({'variant':label,**mm})

    cols_no_codes=[c for c in g.columns if c!='codes']
    g[cols_no_codes].to_csv(OUT/'unique_memberships.csv',index=False)
    roi[cols_no_codes].head(1000).to_csv(OUT/'roi_preserving_top1000.csv',index=False)
    robust[cols_no_codes].head(500).to_csv(OUT/'fully_robust_top500.csv',index=False)
    pd.DataFrame(ablations).to_csv(OUT/'best_robust_ablation.csv',index=False)

    best_robust=robust.iloc[0].to_dict() if len(robust) else None
    best_floor90=floor90.iloc[0].to_dict() if len(floor90) else None
    best_floor85=floor85.iloc[0].to_dict() if len(floor85) else None
    for x in (best_robust,best_floor90,best_floor85,dev_best):
        if isinstance(x,dict):x.pop('codes',None)

    result={
      'current156':cur,
      'score_features':order_names,
      'grid_cells':cells,
      'unique_memberships':int(len(g)),
      'roi_preserving_memberships':int(len(roi)),
      'floor85_memberships':int(len(floor85)),
      'floor90_memberships':int(len(floor90)),
      'fully_robust_memberships':int(len(robust)),
      'best_floor85':best_floor85,
      'best_floor90':best_floor90,
      'best_fully_robust':best_robust,
      'development_first_candidate':{k:v for k,v in dev_best.items() if k not in ('support_head4','support_head4_rate','support_exact3','support_ROI','2026-07_R','2026-07_head4','2026-07_head4_rate','2026-07_ROI','2026-08_R','2026-08_head4','2026-08_head4_rate','2026-08_ROI')},
      'development_first_support_report':{
        'support_R':dev_best.get('support_R'),'support_head4':dev_best.get('support_head4'),
        'support_head4_rate':dev_best.get('support_head4_rate'),'support_exact3':dev_best.get('support_exact3'),
        'support_ROI':dev_best.get('support_ROI'),
        'Jul_ROI':dev_best.get('2026-07_ROI'),'Aug_ROI':dev_best.get('2026-08_ROI'),
      },
      'best_robust_ablation':ablations,
      'SELECTION_SCORE_USES_OUTCOME':False,
      'SEARCH_EVALUATION_IS_NON_PRISTINE':True,
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    print('HEAD4_156R_NEWFEATURE_FRONTIER_OK',flush=True)
    print('SEPTEMBER_UNREAD',flush=True)

if __name__=='__main__':main()
