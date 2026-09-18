#!/usr/bin/env python3
from __future__ import annotations
"""v371: robustness and concentration audit for odds-aware dynamic staking.

Input is v370 race_inputs.csv only: frozen formal tickets, model pair probabilities,
official closing odds, hit rank, and official payout100. No odds/result refetch.
DEV Feb-Jun selects. Jul-Aug SUPPORT remains untouched holdout.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
import pandas as pd

OUT=Path('/tmp/v371-staking-robustness');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
BUDGETS=(600,900,1200)
ALPHAS=(0.0,.25,.5,.75,1.0,1.25)
BETAS=(.5,.75,1.0,1.25,1.5)
MODES=('TOP','TOP2','PROP','CAP67')

def allocate_prop(scores,total_units):
    s=[max(float(x),0.0) for x in scores]
    if sum(s)<=0:s=[1,1,1]
    target=[total_units*x/sum(s) for x in s]
    u=[max(1,int(math.floor(x))) for x in target]
    while sum(u)>total_units:
        cand=[i for i,x in enumerate(u) if x>1]
        i=max(cand,key=lambda k:(u[k]-target[k],k));u[i]-=1
    while sum(u)<total_units:
        i=max(range(3),key=lambda k:(target[k]-u[k],s[k],-k));u[i]+=1
    return tuple(u)

def score_order(scores):
    return sorted(range(3),key=lambda i:(-float(scores[i]),i))

def units(scores,budget,mode):
    total=budget//100
    order=score_order(scores)
    if mode=='PROP':return allocate_prop(scores,total)
    u=[1,1,1];extra=total-3
    if mode=='TOP':
        u[order[0]]+=extra
    elif mode=='TOP2':
        a=(2*extra+2)//3
        b=extra-a
        u[order[0]]+=a;u[order[1]]+=b
    elif mode=='CAP67':
        cap=max(1,int(math.floor(total*2/3)))
        add1=min(extra,cap-1)
        u[order[0]]+=add1
        remain=extra-add1
        if remain>0:u[order[1]]+=remain
    else:raise ValueError(mode)
    if sum(u)!=total or min(u)<1:raise RuntimeError((mode,budget,u))
    return tuple(u)

def equal_units(budget):
    total=budget//100
    if total%3:raise RuntimeError('budget must divide equally')
    return (total//3,)*3

def eval_cfg(z,budget,mode,alpha,beta,detail=False):
    stake=ret=0;profits=[];returns=[];targets=[];all_units=[];rows=[]
    for _,r in z.sort_values('race_code').iterrows():
        p=[float(r.p1),float(r.p2),float(r.p3)]
        o=[float(r.odds1),float(r.odds2),float(r.odds3)]
        sc=[(max(p[i],1e-12)**alpha)*(max(o[i],1e-12)**beta) for i in range(3)]
        u=units(sc,budget,mode)
        rank=int(r.hit_rank);rr=int(r.payout100)*u[rank-1] if rank>0 else 0
        pr=rr-budget;stake+=budget;ret+=rr;profits.append(pr);returns.append(rr)
        tar=score_order(sc)[0]+1;targets.append(tar);all_units.append(u)
        if detail:
            rows.append({'race_code':r.race_code,'month':r.month,'hit_rank':rank,
                         'target_rank':tar,'u1':u[0],'u2':u[1],'u3':u[2],
                         'return_yen':rr,'profit_yen':pr,
                         'score1':sc[0],'score2':sc[1],'score3':sc[2]})
    cum=np.cumsum(profits) if profits else np.array([])
    peak=np.maximum.accumulate(np.r_[0,cum]) if len(cum) else np.array([0])
    dd=peak[1:]-cum if len(cum) else np.array([0])
    maxdd=int(dd.max()) if len(dd) else 0
    streak=mx=0
    for rr in returns:
        if rr==0:streak+=1;mx=max(mx,streak)
        else:streak=0
    arr=np.array(profits,dtype=float)
    unit_arr=np.array(all_units,dtype=float) if all_units else np.zeros((0,3))
    target_arr=np.array(targets,dtype=int) if targets else np.array([],dtype=int)
    return {
      'R':len(z),'hits':int((z.hit_rank>0).sum()),'stake_yen':stake,'return_yen':ret,
      'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
      'max_drawdown_yen':maxdd,'max_zero_return_streak':mx,
      'profit_std_yen':float(arr.std(ddof=0)) if len(arr) else 0.0,
      'avg_u1':float(unit_arr[:,0].mean()) if len(unit_arr) else 0.0,
      'avg_u2':float(unit_arr[:,1].mean()) if len(unit_arr) else 0.0,
      'avg_u3':float(unit_arr[:,2].mean()) if len(unit_arr) else 0.0,
      'target_rank1_R':int((target_arr==1).sum()),'target_rank2_R':int((target_arr==2).sum()),'target_rank3_R':int((target_arr==3).sum()),
      'detail':rows,
    }

def eval_equal(z,budget):
    u=equal_units(budget)
    stake=len(z)*budget;ret=0;profits=[];returns=[]
    for _,r in z.sort_values('race_code').iterrows():
        rank=int(r.hit_rank);rr=int(r.payout100)*u[rank-1] if rank>0 else 0
        ret+=rr;profits.append(rr-budget);returns.append(rr)
    cum=np.cumsum(profits) if profits else np.array([])
    peak=np.maximum.accumulate(np.r_[0,cum]) if len(cum) else np.array([0])
    dd=peak[1:]-cum if len(cum) else np.array([0])
    streak=mx=0
    for rr in returns:
        if rr==0:streak+=1;mx=max(mx,streak)
        else:streak=0
    return {'R':len(z),'hits':int((z.hit_rank>0).sum()),'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
            'max_drawdown_yen':int(dd.max()) if len(dd) else 0,
            'max_zero_return_streak':mx,'profit_std_yen':float(np.std(profits)) if profits else 0.0}

def key(c):
    return f"{c['mode']}|B{c['budget']}|A{c['alpha']:.2f}|O{c['beta']:.2f}"

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--race-inputs',required=True,type=Path);args=ap.parse_args()
    z=pd.read_csv(args.race_inputs,dtype={'race_code':str})
    z.race_code=z.race_code.str.zfill(12)
    if len(z)!=165 or int((z.hit_rank>0).sum())!=87 or int(z.loc[z.hit_rank.gt(0),'payout100'].sum())!=63700:
        raise RuntimeError('v370 frozen input sentinel drift')
    if any(z.race_code.str.startswith('202609')):raise RuntimeError('September entered')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()

    configs=[{'budget':b,'mode':m,'alpha':a,'beta':o} for b in BUDGETS for m in MODES for a in ALPHAS for o in BETAS]
    rows=[]
    monthly_cache={}
    for c in configs:
        dm=eval_cfg(dev,**c)
        eq=eval_equal(dev,c['budget'])
        month_deltas=[];nonneg=0
        for mon in DEV:
            q=dev[dev.month.eq(mon)]
            mm=eval_cfg(q,**c);ee=eval_equal(q,c['budget'])
            delta=100*(mm['roi']-ee['roi']);month_deltas.append(delta);nonneg+=int(delta>=0)
        rows.append({**c,'key':key(c),
                     **{f'dev_{k}':v for k,v in dm.items() if k!='detail'},
                     'dev_delta_roi_pp':100*(dm['roi']-eq['roi']),
                     'dev_month_nonnegative_R':nonneg,
                     'dev_month_worst_delta_pp':min(month_deltas),
                     'dev_month_mean_delta_pp':float(np.mean(month_deltas))})
    g=pd.DataFrame(rows)

    raw=[];robust=[]
    for budget in BUDGETS:
        q=g[g.budget.eq(budget)].copy()
        raw.append(q.sort_values(['dev_roi','dev_month_nonnegative_R'],ascending=False).iloc[0])
        qr=q[q.dev_month_nonnegative_R.ge(3)].copy()
        if len(qr)==0:qr=q
        robust.append(qr.sort_values(['dev_roi','dev_month_worst_delta_pp','dev_max_drawdown_yen'],
                                     ascending=[False,False,True]).iloc[0])
    raw=pd.DataFrame(raw);robust=pd.DataFrame(robust)

    selected=[]
    for label,df in [('RAW_DEV',raw),('ROBUST_DEV',robust)]:
        for _,r in df.iterrows():
            c={k:(int(r[k]) if k=='budget' else str(r[k]) if k=='mode' else float(r[k])) for k in ['budget','mode','alpha','beta']}
            sm=eval_cfg(sup,**c);am=eval_cfg(z,**c,detail=True);eqs=eval_equal(sup,c['budget']);eqa=eval_equal(z,c['budget'])
            selected.append({'selector':label,**c,
                             **{f'support_{k}':v for k,v in sm.items() if k!='detail'},
                             **{f'all_{k}':v for k,v in am.items() if k!='detail'},
                             'support_delta_roi_pp':100*(sm['roi']-eqs['roi']),
                             'all_delta_roi_pp':100*(am['roi']-eqa['roi'])})
            pd.DataFrame(am['detail']).to_csv(OUT/f"detail_{label}_B{c['budget']}.csv",index=False)

    # True LOMO: reselect separately on 4 DEV months, evaluate held month.
    lomo=[]
    for budget in BUDGETS:
      bcfg=[c for c in configs if c['budget']==budget]
      for hold in DEV:
        train=dev[~dev.month.eq(hold)].copy();test=dev[dev.month.eq(hold)].copy()
        cand=[]
        for c in bcfg:
            m=eval_cfg(train,**c);eq=eval_equal(train,budget)
            # prefer ROI; tie lower drawdown.
            cand.append((m['roi'], -m['max_drawdown_yen'], c))
        sel=max(cand,key=lambda x:(x[0],x[1]))[2]
        hm=eval_cfg(test,**sel);he=eval_equal(test,budget)
        lomo.append({'budget':budget,'holdout_month':hold,**sel,
                     'roi':hm['roi'],'equal_roi':he['roi'],'delta_roi_pp':100*(hm['roi']-he['roi']),
                     'profit_yen':hm['profit_yen'],'equal_profit_yen':he['profit_yen'],
                     'max_drawdown_yen':hm['max_drawdown_yen']})

    # Plateau around v370 core alpha=.5 beta=1 TOP, using same budget:
    plateau=[]
    for budget in BUDGETS:
        q=g[(g.budget.eq(budget))&(g['mode'].eq('TOP'))].copy()
        best=float(q.dev_roi.max())
        p=q[q.dev_roi.ge(best-.02)].copy()
        plateau.append({'budget':budget,'cells':len(p),
                        'alpha_min':float(p.alpha.min()),'alpha_max':float(p.alpha.max()),
                        'beta_min':float(p.beta.min()),'beta_max':float(p.beta.max()),
                        'dev_roi_min':float(p.dev_roi.min()),'dev_roi_max':float(p.dev_roi.max())})

    g.to_csv(OUT/'dev_grid.csv',index=False)
    raw.to_csv(OUT/'raw_dev_selected.csv',index=False);robust.to_csv(OUT/'robust_dev_selected.csv',index=False)
    pd.DataFrame(selected).to_csv(OUT/'selected_support_all.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo_reselected.csv',index=False)
    pd.DataFrame(plateau).to_csv(OUT/'top_plateau.csv',index=False)

    result={
      'input':'v370 Artifact 10553791049 race_inputs.csv',
      'grid_cells':len(g),'raw_dev_selected':raw.to_dict('records'),'robust_dev_selected':robust.to_dict('records'),
      'selected_support_all':selected,'lomo':lomo,'top_plateau':plateau,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
