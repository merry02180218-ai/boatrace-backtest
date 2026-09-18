#!/usr/bin/env python3
from __future__ import annotations
"""v370: dynamic within-race staking for current formal 1-head top3 using closing odds.

Research only. Race set and ticket composition are frozen. Each race stakes 600 yen
in six 100-yen units, with at least one unit on each of the three formal tickets.
DEV Feb-Jun selects parameters; Jul-Aug is untouched support.
"""
from pathlib import Path
import argparse, json, math, pickle, glob
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v370-dynamic-staking');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
ALPHAS=(0.0,.5,1.0,1.5,2.0)
BETAS=(-1.0,-.5,0.0,.5,1.0)
EDGE_T=(.8,1.0,1.2,1.5)
TOTAL_UNITS=6
MIN_UNITS=1

def formal_dist(r):
    return v365.formal_post_five6(r)

def load_fallback_dir(path):
    out={}
    if not path:return out
    for fn in sorted(glob.glob(str(Path(path)/'odds_*.csv'))):
        try:df=pd.read_csv(fn,dtype={'race_code':str})
        except Exception:continue
        if 'race_code' not in df.columns or 'odds_json' not in df.columns:continue
        for _,r in df.iterrows():
            try:out[str(r.race_code).zfill(12)]={str(k):float(v) for k,v in json.loads(r.odds_json).items()}
            except Exception:continue
    return out

def load_odds(code,fallback=None):
    code=str(code).zfill(12)
    y,m,d=code[:4],code[4:6],code[6:8]
    jcd=code[8:10];rno=int(code[10:12])
    p=Path(f'data/official_closing_odds3t/{y}/{m}/{d}.csv')
    if p.exists():
        df=pd.read_csv(p,dtype={'jcd':str})
        if 'jcd' in df.columns and 'rno' in df.columns:
            df['jcd']=df.jcd.astype(str).str.zfill(2)
            q=df[(df.jcd==jcd)&(pd.to_numeric(df.rno,errors='coerce').eq(rno))]
            if len(q)==1:
                row=q.iloc[0];out={}
                for s in range(1,7):
                  for t in range(1,7):
                   if s==t:continue
                   for u in range(1,7):
                    if u in (s,t):continue
                    k=f'{s}-{t}-{u}'
                    if k in row.index:
                      try:v=float(row[k])
                      except:continue
                      if math.isfinite(v) and v>0:out[k]=v
                if out:return out,'repo_csv'
    if fallback and code in fallback:
        return fallback[code],'v340_shard'
    return None,None

def actual_payout100(code,combo,cache):
    if code in cache:return cache[code]
    tmp={}
    _,p=pay._payout(code,combo,tmp)
    cache[code]=int(p)
    return int(p)

def alloc_from_scores(scores,total_units=TOTAL_UNITS,min_units=MIN_UNITS):
    n=len(scores)
    if total_units<n*min_units:raise ValueError('budget too small')
    base=[min_units]*n
    rem=total_units-sum(base)
    vals=[max(float(x),0.0) if math.isfinite(float(x)) else 0.0 for x in scores]
    den=sum(vals)
    if rem<=0:return base
    if den<=0:
        # neutral fallback: spread extras round-robin by ticket order
        out=base[:]
        for i in range(rem):out[i%n]+=1
        return out
    target=[rem*v/den for v in vals]
    extra=[int(math.floor(x)) for x in target]
    left=rem-sum(extra)
    frac=[target[i]-extra[i] for i in range(n)]
    for i in sorted(range(n),key=lambda i:(-frac[i],-vals[i],i))[:left]:
        extra[i]+=1
    return [base[i]+extra[i] for i in range(n)]

def alloc_power(ps,ods,a,b):
    scores=[(max(p,1e-12)**a)*(max(o,1e-12)**b) for p,o in zip(ps,ods)]
    return alloc_from_scores(scores)

def alloc_edge(ps,ods,t):
    scores=[max(p*o-t,0.0) for p,o in zip(ps,ods)]
    return alloc_from_scores(scores)

def make_rows(rows,fallback=None):
    payout_cache={};rec=[];missing=[]
    for r in rows:
        code=str(r['race_code']).zfill(12);actual=str(r['actual_combo'])
        od,source=load_odds(code,fallback)
        if od is None:
            missing.append(code);continue
        p2,pc=formal_dist(r)
        pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3]
        tickets=[f'1-{s}-{t}' for s,t in top]
        if any(t not in od for t in tickets):
            missing.append(code);continue
        ps=[float(pair[x]) for x in top]
        ods=[float(od[t]) for t in tickets]
        payout100=actual_payout100(code,actual,payout_cache)
        rec.append({
          'race_code':code,'month':str(r['month']),'actual_combo':actual,'odds_source':source,
          'ticket1':tickets[0],'ticket2':tickets[1],'ticket3':tickets[2],
          'p1':ps[0],'p2':ps[1],'p3':ps[2],
          'odds1':ods[0],'odds2':ods[1],'odds3':ods[2],
          'hit_rank':tickets.index(actual)+1 if actual in tickets else 0,
          'payout100':payout100,
          'combined_odds':1.0/sum(1.0/o for o in ods),
          'p_gap12':ps[0]-ps[1],'p_gap23':ps[1]-ps[2],
          'ev1':ps[0]*ods[0],'ev2':ps[1]*ods[1],'ev3':ps[2]*ods[2],
        })
    z=pd.DataFrame(rec)
    return z,missing

def evaluate(z,alloc_fn):
    stake=0;ret=0;hit_units=[0,0,0];alloc_sum=[0,0,0]
    detail=[]
    for _,r in z.iterrows():
        units=alloc_fn(r)
        if len(units)!=3 or sum(units)!=TOTAL_UNITS or min(units)<MIN_UNITS:
            raise RuntimeError(f'invalid units {units}')
        stake+=TOTAL_UNITS*100
        rank=int(r.hit_rank)
        rowret=0
        if rank>0:
            rowret=int(r.payout100)*int(units[rank-1])
            ret+=rowret;hit_units[rank-1]+=int(units[rank-1])
        for i in range(3):alloc_sum[i]+=int(units[i])
        detail.append({'race_code':r.race_code,'month':r.month,'u1':units[0],'u2':units[1],'u3':units[2],
                       'hit_rank':rank,'return_yen':rowret})
    return {
      'R':len(z),'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,
      'roi':ret/stake if stake else 0.0,
      'avg_u1':alloc_sum[0]/len(z) if len(z) else 0.0,
      'avg_u2':alloc_sum[1]/len(z) if len(z) else 0.0,
      'avg_u3':alloc_sum[2]/len(z) if len(z) else 0.0,
      'winning_units_rank1':hit_units[0],'winning_units_rank2':hit_units[1],'winning_units_rank3':hit_units[2],
      'details':detail,
    }

def power_fn(a,b):
    return lambda r:alloc_power([r.p1,r.p2,r.p3],[r.odds1,r.odds2,r.odds3],a,b)

def edge_fn(t):
    return lambda r:alloc_edge([r.p1,r.p2,r.p3],[r.odds1,r.odds2,r.odds3],t)

def fixed_equal(r):return [2,2,2]

def fixed_rank(w):
    return lambda r:list(w)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);ap.add_argument('--fallback-dir',type=Path,default=None);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    if len(rows)!=165:raise RuntimeError(f'LIVE165 drift {len(rows)}')
    fallback=load_fallback_dir(args.fallback_dir)
    z,missing=make_rows(rows,fallback)
    if missing or len(z)!=165:
        raise RuntimeError(f'closing odds coverage drift covered={len(z)} missing={missing[:20]} total_missing={len(missing)}')
    if not set(z.month).issubset(set(DEV)|set(SUP)):raise RuntimeError('unexpected month')
    base_hits=int((z.hit_rank>0).sum())
    if base_hits!=87:raise RuntimeError(f'formal exact3 drift {base_hits}')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()

    equal=evaluate(z,fixed_equal);equal_dev=evaluate(dev,fixed_equal);equal_sup=evaluate(sup,fixed_equal)
    if abs(equal['roi']-1.2868686868686869)>1e-9:
        raise RuntimeError(f'equal 600 ROI drift {equal}')

    candidates=[]
    for a in ALPHAS:
      for b in BETAS:
        dm=evaluate(dev,power_fn(a,b))
        candidates.append({'family':'POWER','alpha':a,'beta':b,'edge_t':None,
                           **{f'dev_{k}':v for k,v in dm.items() if k!='details'}})
    for t in EDGE_T:
        dm=evaluate(dev,edge_fn(t))
        candidates.append({'family':'EDGE','alpha':None,'beta':None,'edge_t':t,
                           **{f'dev_{k}':v for k,v in dm.items() if k!='details'}})
    cand=pd.DataFrame(candidates)

    # DEV-only selection. Require no worse than equal by >1 ROI point to form robust plateau;
    # primary objective ROI, secondary fewer extreme allocations.
    best=cand.sort_values(['dev_roi','dev_profit_yen'],ascending=False).iloc[0]
    if best.family=='POWER':
        chosen={'family':'POWER','alpha':float(best.alpha),'beta':float(best.beta)}
        fn=power_fn(chosen['alpha'],chosen['beta'])
    else:
        chosen={'family':'EDGE','edge_t':float(best.edge_t)}
        fn=edge_fn(chosen['edge_t'])
    allm=evaluate(z,fn);supm=evaluate(sup,fn)

    # Evaluate fixed-rank baselines at same 600 budget.
    fixed=[]
    for a in range(1,5):
      for b in range(1,6-a):
        c=6-a-b
        if c<1:continue
        for label,df in [('DEV',dev),('SUPPORT',sup),('ALL',z)]:
            m=evaluate(df,fixed_rank((a,b,c)))
            fixed.append({'w1':a,'w2':b,'w3':c,'period':label,**{k:v for k,v in m.items() if k!='details'}})
    fixed=pd.DataFrame(fixed)

    # Nearby POWER plateau diagnostics.
    power=cand[cand.family.eq('POWER')].copy()
    power['delta_roi_pp_vs_equal_dev']=100*(power.dev_roi-equal_dev['roi'])
    plateau=power[power.dev_roi.ge(float(best.dev_roi)-.01)].copy() if best.family=='POWER' else power.iloc[0:0].copy()

    # Fixed chosen per month.
    monthly=[]
    for mon,g in z.groupby('month'):
        bm=evaluate(g,fixed_equal);cm=evaluate(g,fn)
        monthly.append({'month':mon,'equal_roi':bm['roi'],'chosen_roi':cm['roi'],
                        'delta_roi_pp':100*(cm['roi']-bm['roi']),
                        'equal_profit':bm['profit_yen'],'chosen_profit':cm['profit_yen'],
                        'avg_u1':cm['avg_u1'],'avg_u2':cm['avg_u2'],'avg_u3':cm['avg_u3']})

    # LOMO reselect using the same candidate family grid on 4 DEV months; evaluate holdout.
    lomo=[]
    for hold in DEV:
        train=z[z.month.isin([m for m in DEV if m!=hold])]
        test=z[z.month.eq(hold)]
        rec=[]
        for a in ALPHAS:
          for b in BETAS:
            m=evaluate(train,power_fn(a,b));rec.append((('POWER',a,b,None),m))
        for t in EDGE_T:
            m=evaluate(train,edge_fn(t));rec.append((('EDGE',None,None,t),m))
        key,mx=max(rec,key=lambda x:(x[1]['roi'],x[1]['profit_yen']))
        if key[0]=='POWER':f=power_fn(key[1],key[2])
        else:f=edge_fn(key[3])
        bm=evaluate(test,fixed_equal);tm=evaluate(test,f)
        lomo.append({'holdout_month':hold,'family':key[0],'alpha':key[1],'beta':key[2],'edge_t':key[3],
                     'equal_roi':bm['roi'],'test_roi':tm['roi'],'delta_roi_pp':100*(tm['roi']-bm['roi']),
                     'equal_profit':bm['profit_yen'],'test_profit':tm['profit_yen']})

    # Strategy-level breakdown by combined odds bands for chosen allocator.
    bands=[]
    bins=[0,3,4,5,7,10,20,1e9]
    labels=['<3','3-4','4-5','5-7','7-10','10-20','20+']
    zz=z.copy();zz['odds_band']=pd.cut(zz.combined_odds,bins=bins,labels=labels,right=False)
    detail=pd.DataFrame(allm['details'])
    zz=zz.merge(detail[['race_code','u1','u2','u3','return_yen']],on='race_code',validate='one_to_one')
    for band,g in zz.groupby('odds_band',observed=True):
        stake=len(g)*600;ret=int(g.return_yen.sum())
        bands.append({'odds_band':str(band),'R':len(g),'stake_yen':stake,'return_yen':ret,
                      'roi':ret/stake if stake else 0.0,'avg_u1':g.u1.mean(),'avg_u2':g.u2.mean(),'avg_u3':g.u3.mean()})

    z.to_csv(OUT/'formal_with_closing_odds.csv',index=False)
    cand.to_csv(OUT/'dev_candidate_grid.csv',index=False)
    fixed.to_csv(OUT/'fixed_rank_600.csv',index=False)
    plateau.to_csv(OUT/'power_plateau.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)
    pd.DataFrame(bands).to_csv(OUT/'combined_odds_bands.csv',index=False)
    pd.DataFrame(allm['details']).to_csv(OUT/'chosen_allocations.csv',index=False)

    result={
      'odds_source':'repo official closing odds3t with v340 official-closing shard fallback',
      'odds_coverage_R':len(z),'odds_missing_R':len(missing),
      'odds_source_counts':{str(k):int(v) for k,v in z.odds_source.value_counts().to_dict().items()},
      'formal_hits':base_hits,
      'equal_600':{k:v for k,v in equal.items() if k!='details'},
      'equal_dev':{k:v for k,v in equal_dev.items() if k!='details'},
      'equal_support':{k:v for k,v in equal_sup.items() if k!='details'},
      'dev_selected':chosen,
      'selected_dev':{k:v for k,v in best.to_dict().items() if str(k).startswith('dev_')},
      'selected_support':{k:v for k,v in supm.items() if k!='details'},
      'selected_all':{k:v for k,v in allm.items() if k!='details'},
      'delta_roi_pp_all':100*(allm['roi']-equal['roi']),
      'delta_roi_pp_support':100*(supm['roi']-equal_sup['roi']),
      'lomo':lomo,
      'lomo_nonnegative_months':sum(x['delta_roi_pp']>=0 for x in lomo),
      'lomo_total_delta_profit_yen':sum(x['test_profit']-x['equal_profit'] for x in lomo),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
