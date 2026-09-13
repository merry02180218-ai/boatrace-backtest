from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import pandas as pd
import analyze_v205_3head_operational_replay as v205
import run_v322_1head_composite_odds_backtest as v322

THRESHOLDS=[None,2.5,2.7,3.0,3.2,3.5]

def load_v321():
    p=Path('/tmp/v321/score/v321_1head_julaug_scored.csv')
    if not p.exists(): raise FileNotFoundError(p)
    return pd.read_csv(p,dtype={'race_code':str})

def main():
    df=load_v321()
    if len(df)!=55: raise AssertionError(f'v321 expected 55 selected, got {len(df)}')
    if int(pd.to_numeric(df.exact3,errors='coerce').fillna(0).sum())!=21: raise AssertionError('v321 exact3 must reconcile 21/55')
    odds=v205.load_odds()
    if odds.empty: raise RuntimeError('historical odds empty')
    odds['race_code']=odds.race_code.astype(str).str.replace('.0','',regex=False).str.zfill(12)
    oi=odds.set_index('race_code',drop=False)
    rows=[]
    for _,r in df.iterrows():
        code=str(r.race_code).replace('.0','').zfill(12)
        o=v322._odds_row(oi,code)
        tickets=[str(r.ticket1),str(r.ticket2),str(r.ticket3)]
        vals=[v322._safe_odds(o,t) if o is not None else None for t in tickets]
        complete=all(v is not None for v in vals)
        comp=v322.composite([float(v) for v in vals]) if complete else math.nan
        rows.append({'race_code':code,'month':str(r['month']),'hit':int(r.exact3),'ticket1':tickets[0],'ticket2':tickets[1],'ticket3':tickets[2],
                     'o1':vals[0],'o2':vals[1],'o3':vals[2],'composite_odds':comp,'odds_complete':complete})
    x=pd.DataFrame(rows)
    print('RECONCILE',len(x),int(x.hit.sum()),int(x.odds_complete.sum()))
    out=[]
    for scope,mask in [('JUL',x.month.astype(str).str.startswith('2026-07')),('AUG',x.month.astype(str).str.startswith('2026-08')),('JULAUG',x.month.astype(str).str.startswith(('2026-07','2026-08')))]:
        base=x[mask & x.odds_complete].copy()
        print(f'\n[{scope}] selected={int(mask.sum())} evaluable={len(base)} missing={int(mask.sum())-len(base)}')
        for th in THRESHOLDS:
            y=base if th is None else base[base.composite_odds>=th]
            n=len(y); h=int(y.hit.sum()) if n else 0
            ret=float((y.composite_odds*y.hit).sum()) if n else 0.0
            profit=ret-n; roi=100*ret/n if n else np.nan; hit=100*h/n if n else np.nan
            label='ALL' if th is None else f'>={th:.1f}'
            print(f'{label}: R={n} H={h} hit={hit:.2f}% return={ret:.3f} profit={profit:.3f} ROI={roi:.2f}%')
            out.append({'scope':scope,'threshold':label,'races':n,'hits':h,'hit_rate_pct':hit,'return_units':ret,'profit_units':profit,'roi_pct':roi})
    Path('/tmp/v324').mkdir(exist_ok=True)
    x.to_csv('/tmp/v324/v324_julaug_races.csv',index=False)
    pd.DataFrame(out).to_csv('/tmp/v324/v324_julaug_thresholds.csv',index=False)

if __name__=='__main__': main()
