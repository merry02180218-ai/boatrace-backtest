#!/usr/bin/env python3
from __future__ import annotations
"""v373: model-only dynamic +100 boost research on current formal 3 tickets.

No odds are used. Every race keeps 100 yen on each of the three formal tickets.
A simple causal rule may add one 100-yen unit to up to two tickets. DEV Feb-Jun
selects the rule with month/sample guards; Jul-Aug is untouched support.
"""
from pathlib import Path
import argparse,json,pickle,itertools
import numpy as np
import pandas as pd

OUT=Path('/tmp/v373-model-only-boost');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

RANKSETS=((1,),(2,),(3,),(1,2),(1,3),(2,3),(1,2,3))
GE_THRESH=(.075,.085,.095,.105,.115,.125,.135)
LE_THRESH=(.075,.085,.095,.105,.115,.125)
GAPS=('ANY','CLOSE12_010','CLOSE12_020','CLOSE23_010','CLOSE23_020',
      'CLEAR12_020','CLEAR12_030','CLEAR23_015','CLEAR23_025')
MASS_MIN=(.375,.400,.425)
OVERLAY=('ANY','WALL3','FIVE6','EITHER','NONE')
MAX_EXTRA=(1,2)

def build(v370,prepared):
    z=pd.read_csv(v370,dtype={'race_code':str})
    z.race_code=z.race_code.astype(str).str.zfill(12)
    x=pickle.load(open(prepared,'rb'))
    rr={str(r['race_code']).zfill(12):r for r in x['rows']['LIVE165']}
    rec=[]
    for r in z.itertuples():
        q=rr[str(r.race_code)]
        wall=(float(q['opp_mass'])>=.425 and bool(q.get('ex_ready',False))
              and float(q['score4'])>=.60 and float(q['score4'])>float(q['score3']))
        five=(bool(q.get('ex_ready',False)) and float(q['score6'])>=.60
              and float(q['st6'])-float(q['st5'])>=.40)
        rec.append({'race_code':str(r.race_code),'month':str(r.month),'hit_rank':int(r.hit_rank),
                    'payout100':int(r.payout100),'p1':float(r.p1),'p2':float(r.p2),'p3':float(r.p3),
                    'p_head':float(q['p_head']),'opp_mass':float(q['opp_mass']),
                    'gap12':float(r.p1)-float(r.p2),'gap23':float(r.p2)-float(r.p3),
                    'wall3_applied':int(wall),'five6_applied':int(five)})
    a=pd.DataFrame(rec)
    if len(a)!=165 or int((a.hit_rank>0).sum())!=87:raise RuntimeError('formal identity drift')
    return a

def gap_ok(r,g):
    if g=='ANY':return True
    if g=='CLOSE12_010':return r.gap12<=.010
    if g=='CLOSE12_020':return r.gap12<=.020
    if g=='CLOSE23_010':return r.gap23<=.010
    if g=='CLOSE23_020':return r.gap23<=.020
    if g=='CLEAR12_020':return r.gap12>=.020
    if g=='CLEAR12_030':return r.gap12>=.030
    if g=='CLEAR23_015':return r.gap23>=.015
    if g=='CLEAR23_025':return r.gap23>=.025
    raise ValueError(g)

def overlay_ok(r,o):
    w=bool(r.wall3_applied);f=bool(r.five6_applied)
    if o=='ANY':return True
    if o=='WALL3':return w
    if o=='FIVE6':return f
    if o=='EITHER':return w or f
    if o=='NONE':return not (w or f)
    raise ValueError(o)

def cfg(rankset,direction,pth,gap,mass,overlay,mx):
    return {'ranks':','.join(map(str,rankset)),'direction':direction,'p_thresh':float(pth),
            'gap_mode':gap,'mass_min':float(mass),'overlay':overlay,'max_extra':int(mx)}

def select_boosts(r,c):
    if float(r.opp_mass)<c['mass_min'] or not gap_ok(r,c['gap_mode']) or not overlay_ok(r,c['overlay']):
        return []
    ranks={int(x) for x in c['ranks'].split(',')}
    ps=[float(r.p1),float(r.p2),float(r.p3)]
    cand=[]
    for i,p in enumerate(ps,1):
        if i not in ranks:continue
        ok=(p>=c['p_thresh']) if c['direction']=='GE' else (p<=c['p_thresh'])
        if ok:cand.append((p,i))
    if c['direction']=='GE':
        cand.sort(key=lambda x:(-x[0],x[1]))
    else:
        cand.sort(key=lambda x:(x[0],-x[1]))
    return [i for _,i in cand[:c['max_extra']]]

def evaluate(df,c,detail=False):
    base_stake=len(df)*300
    base_ret=int(df.loc[df.hit_rank.gt(0),'payout100'].sum())
    extra_units=extra_ret=0;months={};details=[]
    for r in df.itertuples():
        boosted=select_boosts(r,c)
        n=len(boosted);extra_units+=n
        er=int(r.payout100) if int(r.hit_rank) in boosted else 0
        extra_ret+=er
        m=months.setdefault(str(r.month),{'extra_units':0,'extra_return':0})
        m['extra_units']+=n;m['extra_return']+=er
        if detail and n:
            details.append({'race_code':r.race_code,'month':r.month,'boosted_ranks':','.join(map(str,boosted)),
                            'hit_rank':int(r.hit_rank),'extra_return':er,'p1':r.p1,'p2':r.p2,'p3':r.p3,
                            'gap12':r.gap12,'gap23':r.gap23,'opp_mass':r.opp_mass,
                            'wall3_applied':r.wall3_applied,'five6_applied':r.five6_applied})
    stake=base_stake+extra_units*100;ret=base_ret+extra_ret
    month_rows=[]
    for mon in sorted(set(df.month)):
        g=df[df.month.eq(mon)]
        bs=len(g)*300;br=int(g.loc[g.hit_rank.gt(0),'payout100'].sum())
        q=months.get(mon,{'extra_units':0,'extra_return':0})
        es=q['extra_units']*100;er=q['extra_return']
        broi=br/bs if bs else 0;roi=(br+er)/(bs+es) if bs+es else 0
        month_rows.append({'month':mon,'extra_units':q['extra_units'],'extra_return':er,
                           'base_roi':broi,'roi':roi,'delta_roi_pp':100*(roi-broi),
                           'delta_profit':er-es})
    inc_roi=extra_ret/(extra_units*100) if extra_units else 0.0
    return {'R':len(df),'base_stake':base_stake,'base_return':base_ret,
            'extra_units':extra_units,'extra_stake':extra_units*100,'extra_return':extra_ret,
            'incremental_roi':inc_roi,'stake':stake,'return':ret,'profit':ret-stake,'roi':ret/stake if stake else 0.0,
            'boosted_months':sum(x['extra_units']>0 for x in month_rows),
            'nonnegative_profit_months':sum(x['delta_profit']>=0 for x in month_rows),
            'worst_month_delta_profit':min((x['delta_profit'] for x in month_rows),default=0),
            'worst_month_delta_roi_pp':min((x['delta_roi_pp'] for x in month_rows),default=0),
            'month_rows':month_rows,'details':details}

def configs():
    for ranks in RANKSETS:
      for direction,ths in (('GE',GE_THRESH),('LE',LE_THRESH)):
       for pth in ths:
        for gap in GAPS:
         for mass in MASS_MIN:
          for ov in OVERLAY:
           for mx in MAX_EXTRA:
            yield cfg(ranks,direction,pth,gap,mass,ov,mx)

def choose(df,min_extra=20):
    rows=[];full=[]
    for c in configs():
        m=evaluate(df,c)
        row={**c,**{k:v for k,v in m.items() if k not in ('month_rows','details')}}
        rows.append(row);full.append((c,m))
    grid=pd.DataFrame(rows)
    # Preserve/improve current ROI: incremental stake should itself clear ~current ROI.
    eligible=[(c,m) for c,m in full if m['extra_units']>=min_extra and m['boosted_months']>=4
              and m['nonnegative_profit_months']>=4 and m['worst_month_delta_profit']>=-500
              and m['incremental_roi']>=1.25 and m['roi']>=(m['base_return']/m['base_stake'])]
    if not eligible:
        eligible=[(c,m) for c,m in full if m['extra_units']>=min_extra and m['boosted_months']>=4
                  and m['nonnegative_profit_months']>=4 and m['roi']>=(m['base_return']/m['base_stake'])]
    if not eligible:eligible=full
    # robust first: worst monthly ROI delta, then total ROI, incremental ROI, sample size.
    c,m=max(eligible,key=lambda cm:(cm[1]['worst_month_delta_roi_pp'],cm[1]['roi'],
                                    cm[1]['incremental_roi'],cm[1]['extra_units']))
    return c,m,grid

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--v370-csv',required=True,type=Path);ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    z=build(args.v370_csv,args.prepared);dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    base_stake=len(z)*300;base_ret=int(z.loc[z.hit_rank.gt(0),'payout100'].sum())
    if (base_stake,base_ret)!=(49500,63700):raise RuntimeError('baseline drift')

    chosen,dm,grid=choose(dev,20)
    sm=evaluate(sup,chosen,True);am=evaluate(z,chosen,True)

    # Fixed chosen monthly.
    monthly=am['month_rows']

    # LOMO reselect with same causal grid/guards.
    lomo=[]
    for hold in DEV:
        tr=z[z.month.isin([m for m in DEV if m!=hold])]
        te=z[z.month.eq(hold)]
        c,m,_=choose(tr,15)
        tm=evaluate(te,c)
        broi=tm['base_return']/tm['base_stake'] if tm['base_stake'] else 0
        lomo.append({'holdout_month':hold,**c,'base_roi':broi,'test_roi':tm['roi'],
                     'delta_roi_pp':100*(tm['roi']-broi),'extra_units':tm['extra_units'],
                     'incremental_roi':tm['incremental_roi'],'delta_profit':tm['extra_return']-tm['extra_stake']})

    # Neighborhood = same structural rule, nearby probability/mass thresholds.
    ranks=chosen['ranks'];direction=chosen['direction'];gap=chosen['gap_mode'];ov=chosen['overlay'];mx=chosen['max_extra']
    near=grid[(grid.ranks.eq(ranks))&(grid.direction.eq(direction))&(grid.gap_mode.eq(gap))&
              (grid.overlay.eq(ov))&(grid.max_extra.eq(mx))&
              (grid.p_thresh.sub(chosen['p_thresh']).abs()<=.02+1e-12)&
              (grid.mass_min.sub(chosen['mass_min']).abs()<=.025+1e-12)].copy()

    grid.to_csv(OUT/'dev_grid.csv',index=False);near.to_csv(OUT/'neighborhood.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly.csv',index=False);pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)
    pd.DataFrame(am['details']).to_csv(OUT/'chosen_boosts_all.csv',index=False)
    pd.DataFrame(sm['details']).to_csv(OUT/'chosen_boosts_support.csv',index=False)

    result={'formal_equal':{'stake':base_stake,'return':base_ret,'profit':base_ret-base_stake,'roi':base_ret/base_stake},
            'grid_cells':len(grid),'dev_selected':chosen,
            'selected_dev':{k:v for k,v in dm.items() if k not in ('month_rows','details')},
            'selected_support':{k:v for k,v in sm.items() if k not in ('month_rows','details')},
            'selected_all':{k:v for k,v in am.items() if k not in ('month_rows','details')},
            'delta_roi_pp_all':100*(am['roi']-base_ret/base_stake),
            'delta_profit_all':am['profit']-(base_ret-base_stake),
            'lomo':lomo,'lomo_nonnegative_months':sum(x['delta_roi_pp']>=0 for x in lomo),
            'lomo_total_delta_profit':sum(x['delta_profit'] for x in lomo),
            'neighborhood_cells':len(near),
            'neighborhood_nonnegative_roi_share':float((near.roi>=near.base_return/near.base_stake).mean()) if len(near) else 0.0,
            'ODDS_USED_AS_FEATURE':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
