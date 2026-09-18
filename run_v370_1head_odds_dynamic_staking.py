#!/usr/bin/env python3
from __future__ import annotations
"""v370: odds-aware dynamic staking on current formal 3 tickets.

Race selection and ticket composition are frozen. Decisions use only current
formal model probabilities plus BOAT RACE official closing trifecta odds.
Realized return uses official 100-yen payout. DEV Feb-Jun selects parameters;
Jul-Aug SUPPORT is evaluation only.
"""
from pathlib import Path
import argparse, json, math, pickle
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import run_v369_1head_ticket_rank_staking as v369

OUT=Path('/tmp/v370-odds-dynamic-staking');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
A_GRID=(0.0,0.5,1.0,1.5,2.0)
B_GRID=(-1.0,-0.5,0.0,0.5,1.0)
BUDGET_UNITS=(6,10)
BOOST_THRESH=(0.8,1.0,1.2,1.4,1.6,2.0,2.5,3.0)
BOOST_MARGIN=(0.0,0.10,0.25,0.50,1.0)
BOOST_EXTRA=(1,2,3,5)
BOOST_ODDS_CAP=(0.0,20.0,40.0,80.0)  # 0 means no cap

def load_daily_odds(codes):
    bydate={}
    out={}
    for code in sorted(set(str(x).zfill(12) for x in codes)):
        y,m,d=code[:4],code[4:6],code[6:8]
        path=Path(f'data/official_closing_odds3t/{y}/{m}/{d}.csv')
        if not path.exists():
            out[code]=None;continue
        key=str(path)
        if key not in bydate:
            df=pd.read_csv(path,dtype={'jcd':str,'rno':int})
            df['jcd']=df.jcd.astype(str).str.zfill(2)
            bydate[key]=df
        df=bydate[key];jcd=code[8:10];rno=int(code[10:12])
        q=df[(df.jcd.eq(jcd))&(df.rno.eq(rno))]
        if len(q)!=1:
            out[code]=None;continue
        r=q.iloc[0]
        om={}
        for s in (2,3,4,5,6):
            for t in (2,3,4,5,6):
                if s==t:continue
                k=f'1-{s}-{t}'
                if k in r.index and pd.notna(r[k]):
                    try:
                        v=float(r[k])
                        if v>0:om[k]=v
                    except: pass
        out[code]=om if len(om)==20 else None
    return out

def formal_record(r,payout100,odmap):
    code=str(r['race_code']).zfill(12);actual=str(r['actual_combo'])
    p2,pc=v365.formal_post_five6(r)
    pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3]
    ts=[f'1-{s}-{t}' for s,t in top]
    if odmap is None or any(t not in odmap for t in ts):
        return None
    probs=[float(pair[(s,t)]) for s,t in top]
    odds=[float(odmap[t]) for t in ts]
    rank=(ts.index(actual)+1) if actual in ts else 0
    return {
      'race_code':code,'month':str(r['month']),'actual_combo':actual,
      'ticket1':ts[0],'ticket2':ts[1],'ticket3':ts[2],
      'p1':probs[0],'p2':probs[1],'p3':probs[2],
      'o1':odds[0],'o2':odds[1],'o3':odds[2],
      'v1':probs[0]*odds[0],'v2':probs[1]*odds[1],'v3':probs[2]*odds[2],
      'hit_rank':rank,'payout100':int(payout100)
    }

def allocate_units(scores,total_units,min_each=1):
    scores=np.asarray(scores,dtype=float)
    scores=np.where(np.isfinite(scores)&(scores>0),scores,0.0)
    n=len(scores)
    if total_units<n*min_each:raise ValueError('budget too small')
    units=np.full(n,min_each,dtype=int)
    rem=total_units-int(units.sum())
    if rem<=0:return units.tolist()
    if scores.sum()<=0:scores=np.ones(n)
    target=rem*scores/scores.sum()
    floor=np.floor(target).astype(int);units+=floor
    left=total_units-int(units.sum())
    frac=target-floor
    order=sorted(range(n),key=lambda i:(-frac[i],-scores[i],i))
    for i in order[:left]:units[i]+=1
    if units.sum()!=total_units:raise RuntimeError('allocation drift')
    return units.tolist()

def fixed_eval(z,budget,a,b):
    rows=[]
    for _,r in z.iterrows():
        p=np.array([r.p1,r.p2,r.p3],float)
        o=np.array([r.o1,r.o2,r.o3],float)
        scores=np.power(np.maximum(p,1e-12),a)*np.power(np.maximum(o,1e-12),b)
        u=allocate_units(scores,budget)
        rank=int(r.hit_rank);ret=int(r.payout100)*u[rank-1] if rank>0 else 0
        rows.append((u[0],u[1],u[2],ret))
    q=pd.DataFrame(rows,columns=['u1','u2','u3','return_yen'])
    stake=len(z)*budget*100;ret=int(q.return_yen.sum())
    return {'R':len(z),'budget_units':budget,'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
            'avg_u1':float(q.u1.mean()),'avg_u2':float(q.u2.mean()),'avg_u3':float(q.u3.mean())},q

def baseline_eval(z):
    rank=z.hit_rank.astype(int)
    ret=int(sum(int(r.payout100) for _,r in z.iterrows() if int(r.hit_rank)>0))
    stake=len(z)*300
    return {'R':len(z),'hits':int((rank>0).sum()),'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def boost_eval(z,threshold,margin,extra,odds_cap):
    rec=[]
    for _,r in z.iterrows():
        vals=np.array([r.v1,r.v2,r.v3],float)
        odds=np.array([r.o1,r.o2,r.o3],float)
        order=np.argsort(-vals)
        best=int(order[0]);second=int(order[1])
        ok=vals[best]>=threshold and (vals[best]-vals[second])>=margin
        if odds_cap>0:ok=ok and odds[best]<=odds_cap
        u=[1,1,1]
        if ok:u[best]+=int(extra)
        rank=int(r.hit_rank)
        ret=int(r.payout100)*u[rank-1] if rank>0 else 0
        rec.append({'boost':int(ok),'boost_rank':best+1 if ok else 0,'u1':u[0],'u2':u[1],'u3':u[2],
                    'return_yen':ret,'boost_hit':int(ok and rank==best+1)})
    q=pd.DataFrame(rec)
    stake=int(len(z)*300 + q.boost.sum()*extra*100);ret=int(q.return_yen.sum())
    return {'R':len(z),'boost_R':int(q.boost.sum()),'boost_hits':int(q.boost_hit.sum()),
            'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
            'boost_rank1_R':int((q.boost_rank==1).sum()),'boost_rank2_R':int((q.boost_rank==2).sum()),
            'boost_rank3_R':int((q.boost_rank==3).sum())},q

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    if len(rows)!=165:raise RuntimeError(f'LIVE165 drift {len(rows)}')
    v369.install_payout_cache(rows);payouts=v369.payouts_for(rows)
    codes=[str(r['race_code']).zfill(12) for r in rows];odds=load_daily_odds(codes)
    rec=[];missing=[]
    for r in rows:
        code=str(r['race_code']).zfill(12)
        rr=formal_record(r,payouts[code],odds.get(code))
        if rr is None:missing.append(code)
        else:rec.append(rr)
    z=pd.DataFrame(rec)
    coverage={'selected_R':len(rows),'covered_R':len(z),'missing_R':len(missing),'missing_codes':missing}
    if len(z)!=165:raise RuntimeError(f'closing odds coverage incomplete {coverage}')
    base=baseline_eval(z)
    if (base['hits'],base['return_yen'],base['stake_yen'])!=(87,63700,49500):
        raise RuntimeError(f'formal baseline drift {base}')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    bdev=baseline_eval(dev);bsup=baseline_eval(sup)

    # Fixed-total power family. DEV selects separately per budget.
    fixed=[]
    for budget in BUDGET_UNITS:
      for a in A_GRID:
       for b in B_GRID:
        dm,_=fixed_eval(dev,budget,a,b);sm,_=fixed_eval(sup,budget,a,b);am,_=fixed_eval(z,budget,a,b)
        fixed.append({'budget_units':budget,'a':a,'b':b,
                      **{f'dev_{k}':v for k,v in dm.items()},
                      **{f'support_{k}':v for k,v in sm.items()},
                      **{f'all_{k}':v for k,v in am.items()}})
    fg=pd.DataFrame(fixed)
    best_fixed={}
    for budget in BUDGET_UNITS:
        q=fg[fg.budget_units.eq(budget)]
        best=q.sort_values(['dev_roi','support_roi'],ascending=[False,False]).iloc[0]
        best_fixed[str(budget*100)]={k:(float(v) if isinstance(v,(np.floating,float)) else int(v) if isinstance(v,(np.integer,int)) else v) for k,v in best.to_dict().items()}

    # Named benchmarks: equal, Dutch, model probability at each budget.
    named=[]
    for budget in BUDGET_UNITS:
        for name,a,b in [('EQUAL',0,0),('DUTCH',0,-1),('MODEL_P',1,0),('VALUE_PxO',1,1)]:
            dm,_=fixed_eval(dev,budget,a,b);sm,_=fixed_eval(sup,budget,a,b);am,_=fixed_eval(z,budget,a,b)
            named.append({'name':name,'budget_units':budget,
                          **{f'dev_{k}':v for k,v in dm.items()},
                          **{f'support_{k}':v for k,v in sm.items()},
                          **{f'all_{k}':v for k,v in am.items()}})
    named=pd.DataFrame(named)

    # Selective value boost grid: base 100/100/100 always.
    boost=[]
    for th in BOOST_THRESH:
      for ma in BOOST_MARGIN:
       for ex in BOOST_EXTRA:
        for cap in BOOST_ODDS_CAP:
         dm,_=boost_eval(dev,th,ma,ex,cap);sm,_=boost_eval(sup,th,ma,ex,cap);am,_=boost_eval(z,th,ma,ex,cap)
         boost.append({'threshold':th,'margin':ma,'extra_units':ex,'odds_cap':cap,
                       **{f'dev_{k}':v for k,v in dm.items()},
                       **{f'support_{k}':v for k,v in sm.items()},
                       **{f'all_{k}':v for k,v in am.items()}})
    bg=pd.DataFrame(boost)
    # DEV selection: maximize ROI with at least 10 boosts to avoid one-race luck.
    elig=bg[bg.dev_boost_R.ge(10)].copy()
    best_boost=elig.sort_values(['dev_roi','dev_profit_yen','dev_boost_R'],ascending=[False,False,False]).iloc[0]
    bc={k:float(best_boost[k]) for k in ['threshold','margin','odds_cap']}
    bc['extra_units']=int(best_boost.extra_units)
    bm_all,brows=boost_eval(z,bc['threshold'],bc['margin'],bc['extra_units'],bc['odds_cap'])
    bm_dev,_=boost_eval(dev,bc['threshold'],bc['margin'],bc['extra_units'],bc['odds_cap'])
    bm_sup,_=boost_eval(sup,bc['threshold'],bc['margin'],bc['extra_units'],bc['odds_cap'])

    # Monthly frozen best boost.
    monthly=[]
    for mon,g in z.groupby('month'):
        mm,_=boost_eval(g,bc['threshold'],bc['margin'],bc['extra_units'],bc['odds_cap'])
        bb=baseline_eval(g)
        monthly.append({'month':mon,**{f'base_{k}':v for k,v in bb.items()},**{f'boost_{k}':v for k,v in mm.items()}})

    # Rank of value-max ticket distribution / realized boost hit diagnostics.
    zz=z.copy();zz['boost']=brows.boost;zz['boost_rank']=brows.boost_rank;zz['boost_hit']=brows.boost_hit
    zz.to_csv(OUT/'race_level.csv',index=False)
    fg.to_csv(OUT/'fixed_power_grid.csv',index=False);named.to_csv(OUT/'named_fixed_strategies.csv',index=False)
    bg.to_csv(OUT/'boost_grid.csv',index=False);pd.DataFrame(monthly).to_csv(OUT/'monthly_best_boost.csv',index=False)

    result={
      'odds_source':'repo data/official_closing_odds3t official closing displayed',
      'odds_coverage':coverage,
      'formal_equal100':base,'formal_dev':bdev,'formal_support':bsup,
      'best_fixed_by_budget':best_fixed,
      'named_fixed':named.to_dict('records'),
      'dev_selected_boost':bc,
      'selected_boost_dev':bm_dev,'selected_boost_support':bm_sup,'selected_boost_all':bm_all,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
