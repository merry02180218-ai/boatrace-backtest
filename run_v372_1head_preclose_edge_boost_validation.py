#!/usr/bin/env python3
from __future__ import annotations
"""v372: validate fixed v371 edge-boost staking with true pre-close T-10 odds.

The staking rule is frozen from v371 (.70 conditional edge, max two +100 boosts).
This script does NOT tune on Jul/Aug. It only swaps the odds decision input from
official closing odds to verified BoatraceCSV od3 snapshots acquired before cutoff.
"""
from pathlib import Path
import argparse,json
from datetime import datetime
import numpy as np
import pandas as pd

import analyze_v112_1head_preclose_ev as v112

OUT=Path('/tmp/v372-preclose-edge-boost');OUT.mkdir(parents=True,exist_ok=True)
THRESH=.70
MAX_EXTRA=2
START='2026-07-19'
END='2026-08-31'

def date_from_code(code):
    s=str(code).zfill(12)
    return f'{s[:4]}-{s[4:6]}-{s[6:8]}'

def preclose_odds_for_row(orow,tickets):
    out=[]
    for t in tickets:
        try:v=float(orow.get('3連単_'+t,0) or 0)
        except:v=0.0
        if not np.isfinite(v) or v<=1.0:return None
        out.append(v)
    return out

def units(ps,ods):
    edge=[float(p)*float(o) for p,o in zip(ps,ods)]
    u=[1,1,1];added=0
    for i in sorted(range(3),key=lambda i:(-edge[i],i)):
        if added>=MAX_EXTRA:break
        if edge[i]>=THRESH:
            u[i]+=1;added+=1
    return u,edge

def settle(df,prefix):
    stake=ret=extra=0
    for r in df.itertuples():
        u=[int(getattr(r,f'{prefix}_u1')),int(getattr(r,f'{prefix}_u2')),int(getattr(r,f'{prefix}_u3'))]
        stake+=sum(u)*100;extra+=sum(u)-3
        rank=int(r.hit_rank)
        if rank>0:ret+=int(r.payout100)*u[rank-1]
    return {'R':len(df),'extra_units':extra,'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def equal(df):
    stake=len(df)*300
    ret=int(df.loc[df.hit_rank.gt(0),'payout100'].sum())
    return {'R':len(df),'extra_units':0,'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def block(df,label):
    b=equal(df);c=settle(df,'closing');p=settle(df,'preclose')
    same=int((df[['closing_u1','closing_u2','closing_u3']].to_numpy()==
              df[['preclose_u1','preclose_u2','preclose_u3']].to_numpy()).all(axis=1).sum())
    ticket_same=int((df[['closing_u1','closing_u2','closing_u3']].to_numpy()==
                     df[['preclose_u1','preclose_u2','preclose_u3']].to_numpy()).sum())
    total_ticket=len(df)*3
    return {'period':label,'coverage_R':len(df),
            'avg_lead_min':float(df.lead_min.mean()) if len(df) else None,
            'median_lead_min':float(df.lead_min.median()) if len(df) else None,
            'allocation_same_R':same,'allocation_same_rate':same/len(df) if len(df) else 0.0,
            'ticket_decision_same':ticket_same,'ticket_decision_same_rate':ticket_same/total_ticket if total_ticket else 0.0,
            **{f'equal_{k}':v for k,v in b.items()},
            **{f'closing_{k}':v for k,v in c.items()},
            **{f'preclose_{k}':v for k,v in p.items()},
            'preclose_delta_roi_pp_vs_equal':100*(p['roi']-b['roi']) if len(df) else 0.0,
            'preclose_delta_profit_vs_equal':p['profit_yen']-b['profit_yen'],
            'preclose_delta_roi_pp_vs_closing':100*(p['roi']-c['roi']) if len(df) else 0.0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--v370-csv',required=True,type=Path);args=ap.parse_args()
    z=pd.read_csv(args.v370_csv,dtype={'race_code':str})
    z.race_code=z.race_code.astype(str).str.zfill(12)
    z['date']=z.race_code.map(date_from_code)
    q=z[(z.date>=START)&(z.date<=END)].copy()
    if len(q)==0:raise RuntimeError('no current formal rows in preclose period')
    dates=set(q.date)
    om,leads=v112.load_odds_map(dates)

    rows=[];missing=[]
    for r in q.itertuples():
        code=str(r.race_code).zfill(12)
        orow=om.get(code)
        if not orow:
            missing.append({'race_code':code,'reason':'no_preclose_snapshot'});continue
        tickets=[str(r.ticket1),str(r.ticket2),str(r.ticket3)]
        pod=preclose_odds_for_row(orow,tickets)
        if pod is None:
            missing.append({'race_code':code,'reason':'missing_top3_preclose_odds'});continue
        ps=[float(r.p1),float(r.p2),float(r.p3)]
        cod=[float(r.odds1),float(r.odds2),float(r.odds3)]
        cu,ce=units(ps,cod);pu,pe=units(ps,pod)
        rows.append({'race_code':code,'date':r.date,'month':str(r.month),'actual_combo':str(r.actual_combo),
                     'ticket1':tickets[0],'ticket2':tickets[1],'ticket3':tickets[2],
                     'p1':ps[0],'p2':ps[1],'p3':ps[2],
                     'closing_odds1':cod[0],'closing_odds2':cod[1],'closing_odds3':cod[2],
                     'preclose_odds1':pod[0],'preclose_odds2':pod[1],'preclose_odds3':pod[2],
                     'closing_edge1':ce[0],'closing_edge2':ce[1],'closing_edge3':ce[2],
                     'preclose_edge1':pe[0],'preclose_edge2':pe[1],'preclose_edge3':pe[2],
                     'closing_u1':cu[0],'closing_u2':cu[1],'closing_u3':cu[2],
                     'preclose_u1':pu[0],'preclose_u2':pu[1],'preclose_u3':pu[2],
                     'hit_rank':int(r.hit_rank),'payout100':int(r.payout100),
                     'lead_min':float(leads.get(code,0.0))})
    a=pd.DataFrame(rows)
    if len(a)==0:raise RuntimeError('zero preclose coverage')

    # Integrity: snapshots must all be strictly pre-close and within the historical T-10 archive behavior.
    if (a.lead_min<=0).any():raise RuntimeError('non-causal preclose snapshot')
    if (a.lead_min>15).any():raise RuntimeError(f'unexpectedly early snapshots max={a.lead_min.max()}')

    blocks=[block(a,'ALL_PRECLOSE_COVERED')]
    jul=a[a.date<='2026-07-31']
    aug=a[a.date>='2026-08-01']
    if len(jul):blocks.append(block(jul,'JUL19_31'))
    if len(aug):blocks.append(block(aug,'AUG'))

    # allocation difference rows
    a['allocation_same']=((a.closing_u1==a.preclose_u1)&(a.closing_u2==a.preclose_u2)&(a.closing_u3==a.preclose_u3)).astype(int)
    a['closing_return']=0;a['preclose_return']=0
    for idx,r in a.iterrows():
        rank=int(r.hit_rank)
        if rank>0:
            a.at[idx,'closing_return']=int(r.payout100)*int(r[f'closing_u{rank}'])
            a.at[idx,'preclose_return']=int(r.payout100)*int(r[f'preclose_u{rank}'])

    pd.DataFrame(missing).to_csv(OUT/'missing.csv',index=False)
    a.to_csv(OUT/'race_level.csv',index=False)
    pd.DataFrame(blocks).to_csv(OUT/'periods.csv',index=False)
    result={'fixed_policy':{'edge':'formal pair_prob * odds','threshold':THRESH,'max_extra':MAX_EXTRA,
                            'base':'100 yen on each formal ticket'},
            'current_formal_rows_in_period':len(q),'preclose_coverage_R':len(a),'preclose_missing_R':len(missing),
            'coverage_rate':len(a)/len(q),'snapshot_lead':{
                'mean_min':float(a.lead_min.mean()),'median_min':float(a.lead_min.median()),
                'min_min':float(a.lead_min.min()),'max_min':float(a.lead_min.max())},
            'periods':blocks,'threshold_reselected':False,
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)

if __name__=='__main__':main()
