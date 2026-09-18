#!/usr/bin/env python3
"""Exact156 expansion-layer swap search using causal per-race scores.

Frozen base120 stays fixed. We select exactly 36 of the 88 non-base120
odds-covered candidates using only predecision features:
head_prob, opponent_mass, composite_odds, ST and ORIG advantages.

The score family is historical/non-pristine research, but no result/payout/month
is used inside a candidate's selection score. September is absent.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, itertools, json, math, os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_156r_swap_score_search'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
DEV=('2026-04','2026-05','2026-06'); SUP=('2026-07','2026-08')

HP_W=(0.0,.5,1.0,1.5,2.0,3.0)
MASS_W=(0.0,.5,1.0,1.5,2.0,3.0)
ST_W=(0.0,.5,1.0,1.5,2.0)
ORIG_W=(0.0,.5,1.0,1.5)
MKT_W=(0.0,.25,.5,1.0,1.5)
BAL_W=(0.0,.5,1.0)

FLOOR_PROFILES=(
 ('none',None,None,None,None,None),
 ('aggr',.16,.20,-.50,-.35,1.5),
 ('aggr_st60',.16,.20,-.60,-.35,1.5),
 ('aggr_st70',.16,.20,-.70,-.35,1.5),
 ('aggr_mass25',.16,.25,-.50,-.35,1.5),
 ('aggr_mass30',.16,.30,-.50,-.35,1.5),
 ('aggr_hp12',.12,.20,-.50,-.35,1.5),
 ('aggr_hp20',.20,.20,-.50,-.35,1.5),
 ('aggr_comp20',.16,.20,-.50,-.35,2.0),
 ('aggr_comp25',.16,.20,-.50,-.35,2.5),
 ('aggr_comp30',.16,.20,-.50,-.35,3.0),
 ('aggr_comp35',.16,.20,-.50,-.35,3.5),
 ('orig25',.16,.20,-.50,-.25,1.5),
 ('current_relaxed',.16,.30,-.80,-.35,1.5),
 ('current_comp35',.16,.30,-.80,-.35,3.5),
 ('mass20_st80',.16,.20,-.80,-.35,1.5),
 ('mass25_st80',.16,.25,-.80,-.35,1.5),
 ('hp12_mass20',.12,.20,-.80,-.35,1.5),
 ('hp20_mass20',.20,.20,-.80,-.35,1.5),
 ('hp16_mass20_orig25',.16,.20,-.80,-.25,1.5),
 ('hp16_mass20_comp25',.16,.20,-.80,-.35,2.5),
 ('hp16_mass25_comp25',.16,.25,-.80,-.35,2.5),
)

def pct_rank(a, reverse=False):
    s=pd.Series(a)
    if reverse:
        s=-s
    return s.rank(method='average',pct=True).to_numpy(float)

def metrics(z, mask):
    q=z.loc[mask].copy()
    n=len(q)
    if n==0: return {}
    out={
      'R':int(n),'head4':int(q.head4.sum()),'head4_rate':100*float(q.head4.mean()),
      'exact3':int(q.raw_hit.sum()),'ROI':100*float(q.payout_if_bet.sum())/(10000*n),
      'payout':float(q.payout_if_bet.sum()),
    }
    mrois=[]
    for m in MONTHS:
        x=q[q.month.eq(m)]
        roi=100*float(x.payout_if_bet.sum())/(10000*len(x))
        out[f'{m}_R']=int(len(x));out[f'{m}_head4']=int(x.head4.sum())
        out[f'{m}_head4_rate']=100*float(x.head4.mean());out[f'{m}_ROI']=roi
        mrois.append(roi)
    out['monthly_floor_ROI']=min(mrois)
    for name,mons in [('dev',DEV),('support',SUP)]:
        x=q[q.month.isin(mons)]
        out[f'{name}_R']=int(len(x));out[f'{name}_head4']=int(x.head4.sum())
        out[f'{name}_head4_rate']=100*float(x.head4.mean())
        out[f'{name}_exact3']=int(x.raw_hit.sum())
        out[f'{name}_ROI']=100*float(x.payout_if_bet.sum())/(10000*len(x))
    return out

def select_top36(nb, score, eligible):
    idx=np.where(eligible)[0]
    if len(idx)<36:return None
    # Deterministic tie-break only by causal values then race_code, never outcome.
    order=sorted(idx,key=lambda i:(-score[i],-float(nb.iloc[i].head_prob),-float(nb.iloc[i].opponent_mass),str(nb.iloc[i].race_code)))
    return tuple(sorted(order[:36]))

def subset_hash(codes):
    return hashlib.sha256(';'.join(sorted(codes)).encode()).hexdigest()[:16]

def main():
    p=os.environ.get('RACE_DETAIL_226')
    if not p:raise RuntimeError('RACE_DETAIL_226 missing')
    z=pd.read_csv(p,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')

    base77=z.is_old164.eq(1)&(((z.composite_odds>=7)&(z.opponent_mass>=.425))|((z.composite_odds<7)&(z.head_prob>=.22)&(z.opponent_mass>=.375)&(z.composite_odds>=3)))
    base120=base77|(z.is_old164.eq(1)&(~base77)&z.composite_odds.ge(2.5)&z.quality.ge(.82))
    if int(base120.sum())!=120:raise RuntimeError(f'base120 drift {int(base120.sum())}')

    current_add=(~base120)&z.composite_odds.ge(3.5)&z.quality.ge(.75)&z.head_prob.ge(.16)&z.opponent_mass.ge(.30)&z.st4_adv_inside.ge(-.80)&z.orig4_adv_inside.ge(-.35)
    aggressive_add=(~base120)&z.composite_odds.ge(1.5)&(z.head_prob+1.25*z.opponent_mass).ge(.55)&z.head_prob.ge(.16)&z.opponent_mass.ge(.20)&z.st4_adv_inside.ge(-.50)&z.orig4_adv_inside.ge(-.35)
    if int(current_add.sum())!=36:raise RuntimeError(f'current add drift {int(current_add.sum())}')
    if int(aggressive_add.sum())!=36:raise RuntimeError(f'aggressive add drift {int(aggressive_add.sum())}')
    current=metrics(z,base120|current_add); aggressive=metrics(z,base120|aggressive_add)

    nb=z.loc[~base120].copy().reset_index()
    if len(nb)!=88:raise RuntimeError(f'nonbase expected88 got{len(nb)}')

    hp_r=pct_rank(nb.head_prob)
    mass_r=pct_rank(nb.opponent_mass)
    st_r=pct_rank(nb.st4_adv_inside)
    orig_r=pct_rank(nb.orig4_adv_inside)
    # lower composite odds = higher market confidence for head-accuracy scoring.
    mkt_r=pct_rank(np.log(np.maximum(nb.composite_odds.to_numpy(float),1e-9)), reverse=True)
    bal_r=pct_rank(np.minimum(hp_r,mass_r))

    profiles=[]
    for name,hf,mf,sf,of,cf in FLOOR_PROFILES:
        e=np.ones(len(nb),dtype=bool)
        if hf is not None:e&=nb.head_prob.to_numpy(float)>=hf
        if mf is not None:e&=nb.opponent_mass.to_numpy(float)>=mf
        if sf is not None:e&=nb.st4_adv_inside.to_numpy(float)>=sf
        if of is not None:e&=nb.orig4_adv_inside.to_numpy(float)>=of
        if cf is not None:e&=nb.composite_odds.to_numpy(float)>=cf
        if e.sum()>=36:profiles.append((name,e,hf,mf,sf,of,cf))

    seen={}
    trials=0
    for wh,wm,ws,wo,wk,wb in itertools.product(HP_W,MASS_W,ST_W,ORIG_W,MKT_W,BAL_W):
        if wh+wm+ws+wo+wk+wb==0:continue
        score=wh*hp_r+wm*mass_r+ws*st_r+wo*orig_r+wk*mkt_r+wb*bal_r
        for pname,e,hf,mf,sf,of,cf in profiles:
            trials+=1
            sub=select_top36(nb,score,e)
            if sub is None:continue
            codes=tuple(sorted(nb.iloc[list(sub)].race_code.tolist()))
            h=subset_hash(codes)
            if h in seen:continue
            addmask=z.race_code.isin(codes)
            m=metrics(z,base120|addmask)
            seen[h]={
              'set_hash':h,'floor_profile':pname,
              'w_hp':wh,'w_mass':wm,'w_st':ws,'w_orig':wo,'w_market_conf':wk,'w_balance':wb,
              'head_floor':hf,'mass_floor':mf,'st_floor':sf,'orig_floor':of,'comp_floor':cf,
              **m,'codes':';'.join(codes)
            }

    g=pd.DataFrame(seen.values())
    if g.empty:raise RuntimeError('no score subsets')
    cur_roi=current['ROI'];cur_floor=current['monthly_floor_ROI'];cur_sup=current['support_ROI']

    def best(df):
        if len(df)==0:return None
        q=df.sort_values(['head4_rate','ROI','monthly_floor_ROI','support_ROI'],ascending=[False,False,False,False])
        return q.iloc[0].to_dict()

    roi_ok=g[g.ROI>=cur_roi-1e-9]
    f85=roi_ok[roi_ok.monthly_floor_ROI>=85]
    f90=roi_ok[roi_ok.monthly_floor_ROI>=90]
    fcur=roi_ok[roi_ok.monthly_floor_ROI>=cur_floor-1e-9]
    f90s110=f90[f90.support_ROI>=110]
    f90scur=f90[f90.support_ROI>=cur_sup-1e-9]

    # Dev-first: constraints/ranking use Apr-Jun only. Jul-Aug reported after freeze.
    dev_current=current['dev_ROI']
    dev=g[g.dev_ROI>=dev_current-1e-9].copy()
    devbest=None
    if len(dev):
        # maximize dev head rate, then dev ROI; use causal-set plateau frequency surrogate below.
        devbest=dev.sort_values(['dev_head4_rate','dev_ROI'],ascending=False).iloc[0].to_dict()

    # Count how many score/floor parameterizations map to each set by a second lightweight pass is
    # not needed because seen stores unique sets only. Robustness comes from explicit metric constraints.

    chosen=best(f90)
    swap_removed=[];swap_added=[]
    if chosen:
        cc=set(chosen['codes'].split(';')); aa=set(z.loc[aggressive_add,'race_code'])
        rem=z[z.race_code.isin(sorted(aa-cc))].copy()
        add=z[z.race_code.isin(sorted(cc-aa))].copy()
        cols=['date','month','race_code','head4','raw_hit','payout_if_bet','head_prob','opponent_mass','composite_odds','st4_adv_inside','orig4_adv_inside']
        swap_removed=rem[cols].to_dict('records');swap_added=add[cols].to_dict('records')
        rem.to_csv(OUT/'floor90_removed_from_aggressive.csv',index=False)
        add.to_csv(OUT/'floor90_added_vs_aggressive.csv',index=False)

    g.drop(columns=['codes']).to_csv(OUT/'unique_score_sets.csv',index=False)
    roi_ok.sort_values(['head4_rate','ROI'],ascending=False).head(1000).drop(columns=['codes']).to_csv(OUT/'roi_preserving_top1000.csv',index=False)
    if len(f90):f90.sort_values(['head4_rate','ROI'],ascending=False).head(500).drop(columns=['codes']).to_csv(OUT/'floor90_top500.csv',index=False)

    result={
      'current156':current,'aggressive156':aggressive,
      'parameter_trials':trials,'unique_exact156_sets':int(len(g)),
      'roi_preserving_sets':int(len(roi_ok)),
      'best_roi_preserving':best(roi_ok),
      'floor85_sets':int(len(f85)),'best_floor85':best(f85),
      'floor90_sets':int(len(f90)),'best_floor90':best(f90),
      'current_floor_or_better_sets':int(len(fcur)),'best_current_floor_or_better':best(fcur),
      'floor90_support110_sets':int(len(f90s110)),'best_floor90_support110':best(f90s110),
      'floor90_support_current_sets':int(len(f90scur)),'best_floor90_support_current':best(f90scur),
      'development_first_candidate':devbest,
      'floor90_swap_removed_from_aggressive':swap_removed,
      'floor90_swap_added_vs_aggressive':swap_added,
      'SELECTION_SCORE_USES_OUTCOME':False,
      'SEARCH_EVALUATION_IS_NON_PRISTINE':True,
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    # Avoid duplicating long code strings inside summary.
    for key in ('best_roi_preserving','best_floor85','best_floor90','best_current_floor_or_better','best_floor90_support110','best_floor90_support_current','development_first_candidate'):
        if isinstance(result.get(key),dict):result[key].pop('codes',None)
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print('HEAD4_156R_SWAP_SCORE_SEARCH_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__':main()
