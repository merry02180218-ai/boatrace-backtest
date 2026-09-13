from __future__ import annotations
import math
from pathlib import Path
import pandas as pd
import run_v322_1head_composite_odds_backtest as v322

THRESHOLDS=[None,2.5,2.7,3.0,3.2,3.5]

def load_v321():
    candidates=[
        Path('/tmp/v321/score/v321_1head_julaug_scored.csv'),
        Path('/tmp/v321/v321_1head_julaug_scored.csv'),
        Path('v321_1head_julaug_scored.csv'),
    ]
    for p in candidates:
        if p.exists(): return pd.read_csv(p)
    raise FileNotFoundError('v321 scored csv not found')

def main():
    df=load_v321()
    # tolerate current v321 column names; require date/place/race, exact3, and three tickets.
    print('COLUMNS',list(df.columns))
    ticket_cols=[c for c in df.columns if c.lower() in {'ticket1','ticket2','ticket3','ticket_1','ticket_2','ticket_3','t1','t2','t3'}]
    if len(ticket_cols)<3:
        ticket_cols=[c for c in df.columns if 'ticket' in c.lower()][:3]
    if len(ticket_cols)!=3: raise AssertionError(f'need 3 ticket cols, got {ticket_cols}')
    date_col=next(c for c in df.columns if c.lower() in {'date','race_date'})
    place_col=next(c for c in df.columns if c.lower() in {'place','jcd','stadium'})
    race_col=next(c for c in df.columns if c.lower() in {'race','race_no','rno'})
    hit_col=next(c for c in df.columns if c.lower() in {'exact3','hit','exact3_hit','ticket_hit'})
    if len(df)!=55: raise AssertionError(f'v321 expected 55 selected, got {len(df)}')
    if int(pd.to_numeric(df[hit_col],errors='coerce').fillna(0).sum())!=21: raise AssertionError('v321 exact3 must reconcile 21/55')

    odds=v322.load_odds()
    rows=[]
    for _,r in df.iterrows():
        key_date=str(r[date_col]).replace('-','')[:8]
        try: place=int(r[place_col]); race=int(r[race_col])
        except Exception: continue
        os=[]
        for tc in ticket_cols:
            t=str(r[tc]).replace('-','')
            val=odds.get((key_date,place,race,t), math.nan)
            os.append(float(val) if val is not None else math.nan)
        complete=all(math.isfinite(x) and x>0 for x in os)
        comp=1.0/sum(1.0/x for x in os) if complete else math.nan
        rows.append({'date':key_date,'month':key_date[:6],'place':place,'race':race,'hit':int(r[hit_col]),'o1':os[0],'o2':os[1],'o3':os[2],'composite_odds':comp,'odds_complete':complete})
    x=pd.DataFrame(rows)
    print('RECONCILE',len(x),int(x.hit.sum()),int(x.odds_complete.sum()))
    out=[]
    for scope,mask in [('JUL',x.month=='202607'),('AUG',x.month=='202608'),('JULAUG',x.month.isin(['202607','202608']))]:
        base=x[mask & x.odds_complete].copy()
        print(f'\n[{scope}] selected={int(mask.sum())} evaluable={len(base)} missing={int(mask.sum())-len(base)}')
        for th in THRESHOLDS:
            y=base if th is None else base[base.composite_odds>=th]
            n=len(y); h=int(y.hit.sum()) if n else 0
            ret=float((y.composite_odds*y.hit).sum()) if n else 0.0
            profit=ret-n
            roi=100*ret/n if n else math.nan
            hit=100*h/n if n else math.nan
            label='ALL' if th is None else f'>={th:.1f}'
            print(f'{label}: R={n} H={h} hit={hit:.2f}% return={ret:.3f} profit={profit:.3f} ROI={roi:.2f}%')
            out.append({'scope':scope,'threshold':label,'races':n,'hits':h,'hit_rate_pct':hit,'return_units':ret,'profit_units':profit,'roi_pct':roi})
    Path('/tmp/v324').mkdir(exist_ok=True)
    x.to_csv('/tmp/v324/v324_julaug_races.csv',index=False)
    pd.DataFrame(out).to_csv('/tmp/v324/v324_julaug_thresholds.csv',index=False)

if __name__=='__main__': main()
