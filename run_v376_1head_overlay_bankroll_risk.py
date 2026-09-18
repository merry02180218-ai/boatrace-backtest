#!/usr/bin/env python3
from __future__ import annotations
"""v376: bankroll/drawdown audit for fixed formal-overlay stake multipliers.

No new gate or threshold is tuned. Uses v374 fixed formal-ticket rows.
"""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

OUT=Path('/tmp/v376-overlay-bankroll-risk');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
SIGNALS={'EITHER':'either','FIVE6':'five6','WALL3':'wall3'}
MULTS=(1,2,3,4)

def longest_true(xs):
    best=cur=0
    for x in xs:
        if bool(x):cur+=1;best=max(best,cur)
        else:cur=0
    return best

def run_curve(z,col,mult):
    z=z.sort_values('race_code').copy()
    stake=[];ret=[];profit=[];signal=[]
    for r in z.itertuples():
        active=bool(getattr(r,col))
        m=int(mult) if active else 1
        s=300*m
        rr=int(r.payout100)*m if int(r.hit) else 0
        stake.append(s);ret.append(rr);profit.append(rr-s);signal.append(int(active))
    a=z[['race_code','month','hit','payout100']].copy()
    a['signal']=signal;a['stake']=stake;a['return']=ret;a['profit']=profit
    a['cum_stake']=a.stake.cumsum();a['cum_return']=a['return'].cumsum()
    a['equity']=a.profit.cumsum()
    # Starting equity peak is zero so early losses count as drawdown.
    peaks=np.maximum.accumulate(np.r_[0,a.equity.to_numpy(dtype=float)])[1:]
    dd=peaks-a.equity.to_numpy(dtype=float)
    maxdd=float(dd.max()) if len(dd) else 0.0
    trough=int(dd.argmax()) if len(dd) else -1
    peak_equity=float(peaks[trough]) if trough>=0 else 0.0
    # Most recent index at that peak level before trough; -1 means starting point.
    prior=a.equity.to_numpy(dtype=float)[:trough+1] if trough>=0 else np.array([])
    matches=np.where(np.isclose(prior,peak_equity))[0]
    peak_idx=int(matches[-1]) if len(matches) else -1
    dd_races=(trough-peak_idx) if trough>=0 else 0
    roll10=float(a.profit.rolling(10).sum().min()) if len(a)>=10 else float(a.profit.sum())
    roll20=float(a.profit.rolling(20).sum().min()) if len(a)>=20 else float(a.profit.sum())
    monthly=a.groupby('month',sort=True).agg(stake=('stake','sum'),returns=('return','sum'),profit=('profit','sum'))
    monthly['roi']=monthly.returns/monthly.stake
    total_stake=int(a.stake.sum());total_ret=int(a['return'].sum());total_profit=total_ret-total_stake
    return {
      'R':len(a),'signal_R':int(a.signal.sum()),'hits':int(a.hit.sum()),
      'stake':total_stake,'return':total_ret,'profit':total_profit,'roi':total_ret/total_stake if total_stake else 0.0,
      'profit_per_10k_stake':10000*total_profit/total_stake if total_stake else 0.0,
      'max_drawdown_yen':maxdd,'max_drawdown_pct_total_stake':100*maxdd/total_stake if total_stake else 0.0,
      'drawdown_race_span':int(dd_races),
      'longest_losing_streak':int(longest_true(a.profit.lt(0).tolist())),
      'worst_10R_profit':roll10,'worst_20R_profit':roll20,
      'monthly_profit_std':float(monthly.profit.std(ddof=0)) if len(monthly) else 0.0,
      'monthly_worst_profit':int(monthly.profit.min()) if len(monthly) else 0,
      'monthly_best_profit':int(monthly.profit.max()) if len(monthly) else 0,
    },a,monthly.reset_index()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--v374-dir',required=True,type=Path);args=ap.parse_args()
    p=args.v374_dir/'rows_LIVE165.csv'
    z=pd.read_csv(p,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12)
    if (len(z),int(z.hit.sum()),int(z.loc[z.hit.eq(1),'payout100'].sum()))!=(165,87,63700):
        raise RuntimeError('formal LIVE165 sentinel drift')

    rows=[];monthly_rows=[];curve_files={}
    for sig,col in SIGNALS.items():
        base=None
        for mult in MULTS:
            for period,df in [('ALL',z),('DEV',z[z.month.isin(DEV)]),('SUPPORT',z[z.month.isin(SUP)])]:
                m,curve,monthly=run_curve(df,col,mult)
                if period=='ALL' and mult==1:base=m
                row={'signal':sig,'multiplier':mult,'period':period,**m}
                rows.append(row)
                if period=='ALL':
                    for _,x in monthly.iterrows():
                        monthly_rows.append({'signal':sig,'multiplier':mult,**x.to_dict()})
                    curve.to_csv(OUT/f'curve_{sig}_{mult}x.csv',index=False)
        # incremental efficiency vs 1x, using ALL
    res=pd.DataFrame(rows)
    allr=res[res.period.eq('ALL')].copy()
    base_by_sig={s:allr[(allr.signal.eq(s))&(allr.multiplier.eq(1))].iloc[0] for s in SIGNALS}
    inc=[]
    for _,r in allr.iterrows():
        b=base_by_sig[r.signal]
        ds=float(r.stake-b.stake);dp=float(r.profit-b.profit);dr=float(r['return']-b['return'])
        inc.append({'signal':r.signal,'multiplier':int(r.multiplier),
                    'extra_stake':ds,'extra_return':dr,'extra_profit':dp,
                    'incremental_return_on_extra_stake':dr/ds if ds>0 else None,
                    'incremental_profit_per_10k_extra_stake':10000*dp/ds if ds>0 else None,
                    'delta_roi_pp':100*(float(r.roi)-float(b.roi)),
                    'delta_maxdd_yen':float(r.max_drawdown_yen)-float(b.max_drawdown_yen)})
    incdf=pd.DataFrame(inc)

    # Risk efficiency: among non-baseline multipliers compare profit lift / added DD.
    risk=[]
    for _,x in incdf[incdf.multiplier.gt(1)].iterrows():
        risk.append({**x.to_dict(),
                     'profit_gain_per_added_dd':(x.extra_profit/x.delta_maxdd_yen if x.delta_maxdd_yen>0 else None)})
    riskdf=pd.DataFrame(risk)

    res.to_csv(OUT/'risk_metrics.csv',index=False)
    incdf.to_csv(OUT/'incremental_efficiency.csv',index=False)
    riskdf.to_csv(OUT/'risk_efficiency.csv',index=False)
    pd.DataFrame(monthly_rows).to_csv(OUT/'monthly.csv',index=False)

    # Natural lowest non-trivial candidate = 2x. Do not choose by outcome.
    two=res[(res.multiplier.eq(2))&(res.period.eq('ALL'))]
    result={
      'formal_baseline':res[(res.signal.eq('EITHER'))&(res.multiplier.eq(1))&(res.period.eq('ALL'))].iloc[0].to_dict(),
      'two_x_fixed_candidates':two.to_dict('records'),
      'incremental_efficiency':incdf.to_dict('records'),
      'NO_PARAMETER_SEARCH':True,
      'NATURAL_FORWARD_SHADOW_MULTIPLIER':2,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
