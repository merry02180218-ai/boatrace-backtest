#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import pandas as pd,requests
import run_v340_1head_adaptive_odds_dutch as v

P=Path('/tmp/v340shard'); P.mkdir(parents=True,exist_ok=True)

def odds(shard,n):
    s=pd.read_csv('/tmp/v340prep/selected.csv',dtype={'race_code':str}); s.race_code=s.race_code.str.zfill(12)
    ranks=json.loads(Path('/tmp/v340prep/rankings.json').read_text())
    sess=requests.Session(); out=[]; miss=[]
    w=s.iloc[shard::n]
    for i,(_,r) in enumerate(w.iterrows(),1):
        code=str(r.race_code).zfill(12); om,u=v.fetch_odds(code,sess)
        if om is None: miss.append({'race_code':code,'detail':u}); continue
        req=ranks[code]; bad=[x for x in req if x not in om]
        if bad: miss.append({'race_code':code,'detail':'missing '+','.join(bad)}); continue
        out.append({'race_code':code,'odds_json':json.dumps({x:om[x] for x in req})})
        if i%10==0: print('progress',shard,i,len(w),flush=True)
    pd.DataFrame(out).to_csv(P/f'odds_{shard}.csv',index=False)
    pd.DataFrame(miss).to_csv(P/f'missing_{shard}.csv',index=False)

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('--shard',type=int,required=True); a.add_argument('--n',type=int,default=6); x=a.parse_args(); odds(x.shard,x.n)
