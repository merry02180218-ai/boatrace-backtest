#!/usr/bin/env python3
"""Focused fast exact156 swap search (vectorized).

Frozen base120 stays fixed. Exactly 36 additions are selected using only causal
predecision features. Search evaluation is Apr-Aug NON-PRISTINE retrospective;
September is absent and production is unchanged.
"""
from pathlib import Path
import itertools, json, os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_156r_swap_score_fast');OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
DEV=('2026-04','2026-05','2026-06');SUP=('2026-07','2026-08')

def rankpct(x,rev=False):
    s=pd.Series(x)
    if rev:s=-s
    return s.rank(method='average',pct=True).to_numpy(float)

def main():
    p=os.environ['RACE_DETAIL_226']
    z=pd.read_csv(p,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')

    b120=z.base120.astype(bool).to_numpy()
    if int(b120.sum())!=120:raise RuntimeError(f'base120 drift {int(b120.sum())}')
    cur=(~b120)&z.composite_odds.ge(3.5).to_numpy()&z.quality.ge(.75).to_numpy()&z.head_prob.ge(.16).to_numpy()&z.opponent_mass.ge(.30).to_numpy()&z.st4_adv_inside.ge(-.80).to_numpy()&z.orig4_adv_inside.ge(-.35).to_numpy()
    aggressive=(~b120)&z.composite_odds.ge(1.5).to_numpy()&(z.head_prob+1.25*z.opponent_mass).ge(.55).to_numpy()&z.head_prob.ge(.16).to_numpy()&z.opponent_mass.ge(.20).to_numpy()&z.st4_adv_inside.ge(-.50).to_numpy()&z.orig4_adv_inside.ge(-.35).to_numpy()
    if int(cur.sum())!=36 or int(aggressive.sum())!=36:raise RuntimeError('reference expansion drift')

    nb=z.loc[~b120].copy().reset_index()
    if len(nb)!=88:raise RuntimeError(f'nonbase expected88 got{len(nb)}')
    global_idx=nb['index'].to_numpy(int)

    head=z.head4.to_numpy(int);hit=z.raw_hit.to_numpy(int);pay=z.payout_if_bet.to_numpy(float);mon=z.month.to_numpy(str)
    base_idx=np.where(b120)[0]
    base_head=head[base_idx].sum();base_hit=hit[base_idx].sum();base_pay=pay[base_idx].sum()
    base_mon={}
    for m in MONTHS:
        bi=base_idx[mon[base_idx]==m]
        base_mon[m]=(len(bi),head[bi].sum(),hit[bi].sum(),pay[bi].sum())

    nb_head=head[global_idx];nb_hit=hit[global_idx];nb_pay=pay[global_idx];nb_mon=mon[global_idx]

    def met_local(sel):
        sel=np.asarray(sel,dtype=int)
        d={
          'R':156,
          'head4':int(base_head+nb_head[sel].sum()),
          'head4_rate':100*float(base_head+nb_head[sel].sum())/156,
          'exact3':int(base_hit+nb_hit[sel].sum()),
          'ROI':100*float(base_pay+nb_pay[sel].sum())/1560000,
        }
        ro=[]
        for m in MONTHS:
            br,bh,bx,bp=base_mon[m];sm=(nb_mon[sel]==m)
            rr=br+int(sm.sum());pp=bp+float(nb_pay[sel][sm].sum())
            roi=100*pp/(10000*rr)
            d[f'{m}_R']=rr;d[f'{m}_ROI']=roi;ro.append(roi)
        d['monthly_floor_ROI']=min(ro)
        for nm,mons in [('dev',DEV),('support',SUP)]:
            br=sum(base_mon[m][0] for m in mons);bh=sum(base_mon[m][1] for m in mons);bp=sum(base_mon[m][3] for m in mons)
            sm=np.isin(nb_mon[sel],mons)
            rr=br+int(sm.sum());hh=bh+int(nb_head[sel][sm].sum());pp=bp+float(nb_pay[sel][sm].sum())
            d[f'{nm}_R']=rr;d[f'{nm}_head4']=hh;d[f'{nm}_head4_rate']=100*hh/rr;d[f'{nm}_ROI']=100*pp/(10000*rr)
        return d

    local_of_global={g:i for i,g in enumerate(global_idx)}
    cur_local=[local_of_global[g] for g in np.where(cur)[0]]
    ag_local=[local_of_global[g] for g in np.where(aggressive)[0]]
    current=met_local(cur_local);aggr=met_local(ag_local)

    hpv=nb.head_prob.to_numpy(float);mav=nb.opponent_mass.to_numpy(float)
    stv=nb.st4_adv_inside.to_numpy(float);ogv=nb.orig4_adv_inside.to_numpy(float);compv=nb.composite_odds.to_numpy(float)
    hp=rankpct(hpv);ma=rankpct(mav);st=rankpct(stv);og=rankpct(ogv);mk=rankpct(np.log(np.maximum(compv,1e-9)),True)
    bal=rankpct(np.minimum(hp,ma));codes=nb.race_code.to_numpy(str)

    floor_profiles=[
      ('none',0,0,-99,-99,0),('a',.16,.20,-.50,-.35,1.5),('a60',.16,.20,-.60,-.35,1.5),
      ('a70',.16,.20,-.70,-.35,1.5),('a80',.16,.20,-.80,-.35,1.5),
      ('m25',.16,.25,-.80,-.35,1.5),('m30',.16,.30,-.80,-.35,1.5),
      ('c20',.16,.20,-.80,-.35,2.0),('c25',.16,.20,-.80,-.35,2.5),('c30',.16,.20,-.80,-.35,3.0),
      ('h12',.12,.20,-.80,-.35,1.5),('h20',.20,.20,-.80,-.35,1.5),('o25',.16,.20,-.80,-.25,1.5),
    ]
    profiles=[]
    for name,hf,mf,sf,of,cf in floor_profiles:
        e=(hpv>=hf)&(mav>=mf)&(stv>=sf)&(ogv>=of)&(compv>=cf)
        if int(e.sum())>=36:profiles.append((name,e))

    weights=list(itertools.product((1,1.5,2,2.5,3),(.5,1,1.5,2),(.5,1,1.5,2,3),(0,.5,1),(0,.25,.5,1),(0,.5,1)))
    seen={}
    for wh,wm,ws,wo,wk,wb in weights:
        score=wh*hp+wm*ma+ws*st+wo*og+wk*mk+wb*bal
        order=sorted(range(88),key=lambda i:(-score[i],-hpv[i],-mav[i],codes[i]))
        for pname,e in profiles:
            sel=tuple(sorted([i for i in order if e[i]][:36]))
            if len(sel)<36 or sel in seen:continue
            seen[sel]={'floor_profile':pname,'w_hp':wh,'w_mass':wm,'w_st':ws,'w_orig':wo,'w_mkt':wk,'w_bal':wb,**met_local(sel)}

    g=pd.DataFrame(seen.values())
    roi=g[g.ROI>=current['ROI']-1e-9].copy()
    def best(df):
        if len(df)==0:return None
        return df.sort_values(['head4_rate','ROI','monthly_floor_ROI','support_ROI'],ascending=[False,False,False,False]).iloc[0].to_dict()

    buckets={}
    for label,floor in [('80',80),('85',85),('90',90),('current_floor',current['monthly_floor_ROI'])]:
        q=roi[roi.monthly_floor_ROI>=floor]
        buckets[label]={'count':int(len(q)),'best':best(q)}

    result={
      'current156':current,'aggressive156':aggr,
      'weight_cells':len(weights),'eligible_profiles':len(profiles),
      'unique_exact156_sets':int(len(g)),'roi_preserving_sets':int(len(roi)),
      'best_roi_preserving':best(roi),'floor_buckets':buckets,
      'SELECTION_SCORE_USES_OUTCOME':False,'SEARCH_EVALUATION_IS_NON_PRISTINE':True,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True,
    }
    g.to_csv(OUT/'unique_sets.csv',index=False)
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print('HEAD4_156R_SWAP_SCORE_FAST_OK');print('SEPTEMBER_UNREAD')

if __name__=='__main__':main()
