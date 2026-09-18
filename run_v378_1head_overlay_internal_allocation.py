#!/usr/bin/env python3
from __future__ import annotations
"""v378: internal stake allocation inside already-defined formal overlay races.

Total stake is fixed to the current shadow policy:
- overlay (wall3 OR five6): 600 yen total
- non-overlay: 300 yen total
Only the distribution of the six 100-yen units across the 3 formal tickets is varied.
DEV Feb-Jun selects; Jul-Aug SUPPORT is untouched holdout.
"""
from pathlib import Path
import argparse,itertools,json
import numpy as np
import pandas as pd

OUT=Path('/tmp/v378-overlay-internal-allocation');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
SIGNALS={'EITHER':'either','FIVE6':'five6','WALL3':'wall3'}
BASE_W=(2,2,2)

def comps(total=6):
    out=[]
    for a in range(1,total-1):
        for b in range(1,total-a):
            c=total-a-b
            if c>=1:out.append((a,b,c))
    return out

def hit_rank(r):
    if not int(r.hit): return 0
    ts=str(r.tickets).split(';')
    actual=str(r.actual_combo)
    if actual not in ts: raise RuntimeError(f'hit row without actual in tickets {r.race_code}')
    return ts.index(actual)+1

def enrich(z):
    z=z.copy()
    z['hit_rank']=[hit_rank(r) for r in z.itertuples()]
    return z

def alloc_for(r,signal,w):
    # Preserve current EITHER 2x total stake. Only selected signal rows change internal weights.
    if int(r.either):
        if int(getattr(r,signal)):
            return w
        return BASE_W
    return (1,1,1)

def eval_cfg(z,signal,w):
    stake=ret=0;rows=[]
    for r in z.sort_values('race_code').itertuples():
        u=alloc_for(r,signal,w)
        s=100*sum(u)
        rank=int(r.hit_rank)
        rr=int(r.payout100)*u[rank-1] if rank>0 else 0
        stake+=s;ret+=rr
        rows.append({'race_code':str(r.race_code),'month':str(r.month),'overlay_cat':str(r.overlay_cat),
                     'hit_rank':rank,'u1':u[0],'u2':u[1],'u3':u[2],
                     'stake':s,'return':rr,'profit':rr-s})
    d=pd.DataFrame(rows)
    return {'R':len(d),'overlay_R':int(z.either.sum()),'stake':stake,'return':ret,'profit':ret-stake,
            'roi':ret/stake if stake else 0.0,'detail':d}

def rank_summary(z,label):
    q=z[z.either.eq(1)].copy()
    out={'label':label,'overlay_R':len(q),'overlay_hits':int(q.hit.sum())}
    hitq=q[q.hit.eq(1)]
    for rank in (1,2,3):
        r=hitq[hitq.hit_rank.eq(rank)]
        out[f'rank{rank}_hits']=len(r)
        out[f'rank{rank}_hit_share']=len(r)/len(hitq) if len(hitq) else 0.0
        out[f'rank{rank}_return100']=int(r.payout100.sum())
        out[f'rank{rank}_avg_payout100']=float(r.payout100.mean()) if len(r) else 0.0
    return out

def compare_months(z,signal,w):
    rows=[]
    for mon,g in z.groupby('month',sort=True):
        b=eval_cfg(g,'either',BASE_W)
        m=eval_cfg(g,signal,w)
        rows.append({'month':mon,'signal':signal,'w1':w[0],'w2':w[1],'w3':w[2],
                     'base_roi':b['roi'],'roi':m['roi'],'delta_roi_pp':100*(m['roi']-b['roi']),
                     'base_profit':b['profit'],'profit':m['profit'],'delta_profit':m['profit']-b['profit']})
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--v374-dir',required=True,type=Path);a=ap.parse_args()
    p=a.v374_dir/'rows_LIVE165.csv'
    z=pd.read_csv(p,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12)
    z=enrich(z)
    if (len(z),int(z.hit.sum()),int(z.loc[z.hit.eq(1),'payout100'].sum()),int(z.either.sum()))!=(165,87,63700,36):
        raise RuntimeError('LIVE165 formal/overlay sentinel drift')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()

    base_all=eval_cfg(z,'either',BASE_W)
    base_dev=eval_cfg(dev,'either',BASE_W)
    base_sup=eval_cfg(sup,'either',BASE_W)
    if (base_all['stake'],base_all['return'])!=(60300,81340):
        raise RuntimeError(f'EITHER2x baseline drift {base_all}')

    grid=[];full={}
    for sig,col in SIGNALS.items():
        for w in comps(6):
            dm=eval_cfg(dev,col,w);am=eval_cfg(z,col,w);sm=eval_cfg(sup,col,w)
            months=compare_months(dev,col,w)
            row={'signal':sig,'w1':w[0],'w2':w[1],'w3':w[2],
                 'dev_roi':dm['roi'],'dev_profit':dm['profit'],'dev_delta_roi_pp':100*(dm['roi']-base_dev['roi']),
                 'support_roi':sm['roi'],'support_profit':sm['profit'],'support_delta_roi_pp':100*(sm['roi']-base_sup['roi']),
                 'all_roi':am['roi'],'all_profit':am['profit'],'all_delta_roi_pp':100*(am['roi']-base_all['roi']),
                 'dev_month_nonnegative_R':sum(x['delta_roi_pp']>=0 for x in months),
                 'dev_month_positive_R':sum(x['delta_roi_pp']>0 for x in months),
                 'dev_worst_delta_roi_pp':min(x['delta_roi_pp'] for x in months)}
            grid.append(row);full[(sig,w)]=(dm,sm,am,months)
    g=pd.DataFrame(grid)

    selected=[]
    for sig in SIGNALS:
        q=g[g.signal.eq(sig)].copy()
        raw=q.sort_values(['dev_roi','dev_month_nonnegative_R'],ascending=False).iloc[0]
        qr=q[q.dev_month_nonnegative_R.ge(4)].copy()
        if len(qr)==0:qr=q
        robust=qr.sort_values(['dev_roi','dev_worst_delta_roi_pp'],ascending=[False,False]).iloc[0]
        for label,r in [('RAW_DEV',raw),('ROBUST_DEV',robust)]:
            w=(int(r.w1),int(r.w2),int(r.w3))
            dm,sm,am,months=full[(sig,w)]
            selected.append({'selector':label,'signal':sig,'w1':w[0],'w2':w[1],'w3':w[2],
                             'dev_roi':dm['roi'],'support_roi':sm['roi'],'all_roi':am['roi'],
                             'dev_profit':dm['profit'],'support_profit':sm['profit'],'all_profit':am['profit'],
                             'support_delta_roi_pp':100*(sm['roi']-base_sup['roi']),
                             'all_delta_roi_pp':100*(am['roi']-base_all['roi']),
                             'dev_month_nonnegative_R':int(r.dev_month_nonnegative_R),
                             'dev_worst_delta_roi_pp':float(r.dev_worst_delta_roi_pp)})
            am['detail'].to_csv(OUT/f"detail_{label}_{sig}.csv",index=False)

    # True LOMO: reselect one weight among 10 on four DEV months, test holdout month.
    lomo=[]
    for sig,col in SIGNALS.items():
        for hold in DEV:
            tr=dev[~dev.month.eq(hold)].copy();te=dev[dev.month.eq(hold)].copy()
            cand=[]
            for w in comps(6):
                mm=eval_cfg(tr,col,w)
                cand.append((mm['roi'],w))
            _,w=max(cand,key=lambda x:x[0])
            tm=eval_cfg(te,col,w);tb=eval_cfg(te,'either',BASE_W)
            lomo.append({'signal':sig,'holdout_month':hold,'w1':w[0],'w2':w[1],'w3':w[2],
                         'base_roi':tb['roi'],'test_roi':tm['roi'],'delta_roi_pp':100*(tm['roi']-tb['roi']),
                         'base_profit':tb['profit'],'test_profit':tm['profit'],'delta_profit':tm['profit']-tb['profit']})

    # Rank decomposition for overlay, by overall/dev/support and category.
    ranks=[rank_summary(z,'ALL'),rank_summary(dev,'DEV'),rank_summary(sup,'SUPPORT')]
    catrows=[]
    for period,df in [('ALL',z),('DEV',dev),('SUPPORT',sup)]:
        for cat,q in df[df.either.eq(1)].groupby('overlay_cat',sort=True):
            x=q.copy();x=enrich(x)
            s=rank_summary(x,f'{period}:{cat}')
            s['period']=period;s['category']=cat;catrows.append(s)

    pd.DataFrame(grid).to_csv(OUT/'weight_grid.csv',index=False)
    pd.DataFrame(selected).to_csv(OUT/'selected.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)
    pd.DataFrame(ranks).to_csv(OUT/'overlay_rank_summary.csv',index=False)
    pd.DataFrame(catrows).to_csv(OUT/'overlay_category_rank_summary.csv',index=False)

    result={
      'baseline_either_2x':{k:v for k,v in base_all.items() if k!='detail'},
      'baseline_dev':{k:v for k,v in base_dev.items() if k!='detail'},
      'baseline_support':{k:v for k,v in base_sup.items() if k!='detail'},
      'overlay_rank_summary':ranks,'selected':selected,'lomo':lomo,
      'grid_cells':len(g),'TOTAL_STAKE_HELD_FIXED':True,'NO_ODDS_FEATURE':True,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
