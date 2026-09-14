#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd
import run_v340_1head_adaptive_odds_dutch as v
P=Path('/tmp/v340prep'); O=Path('/tmp/v340shard'); R=Path('/tmp/v340final'); R.mkdir(parents=True,exist_ok=True)
s=pd.read_csv(P/'selected.csv',dtype={'race_code':str}); s.race_code=s.race_code.str.zfill(12)
ranks=json.loads((P/'rankings.json').read_text()); ident=json.loads((P/'identity.json').read_text())
omaps={}; missing=[]
for k in range(6):
    f=O/f'odds_{k}.csv'
    if f.exists() and f.stat().st_size:
        try:
            d=pd.read_csv(f,dtype={'race_code':str})
            for _,x in d.iterrows(): omaps[str(x.race_code).zfill(12)]=json.loads(x.odds_json)
        except pd.errors.EmptyDataError: pass
    m=O/f'missing_{k}.csv'
    if m.exists() and m.stat().st_size:
        try: missing += pd.read_csv(m).to_dict('records')
        except pd.errors.EmptyDataError: pass
rows=[]
for _,x in s.iterrows():
    code=str(x.race_code).zfill(12)
    if code not in omaps: continue
    q={'month':str(x.month),'race_code':code,'actual_combo':str(x.actual_combo),'head_hit':int(x.head_hit)}
    q.update(v.baseline_one(x,ranks[code],omaps[code])); q.update(v.evaluate_one(x,ranks[code],omaps[code])); rows.append(q)
z=pd.DataFrame(rows); assert len(z)>0; z.to_csv(R/'race_level.csv',index=False); pd.DataFrame(missing).to_csv(R/'odds_missing.csv',index=False)
b=z[z.stake_yen>0].copy(); st=float(b.stake_yen.sum()); ret=float(b.return_yen.sum()); bst=float(z.baseline_stake_yen.sum()); br=float(z.baseline_return_yen.sum())
mo=b.groupby('month',as_index=False).agg(R=('race_code','size'),hits=('hit','sum'),stake=('stake_yen','sum'),returns=('return_yen','sum')); mo['hit_rate']=mo.hits/mo.R; mo['roi_pct']=100*mo.returns/mo.stake; mo['profit']=mo.returns-mo.stake; mo.to_csv(R/'monthly.csv',index=False)
d=b.groupby('n_tickets').size().reset_index(name='R'); d.to_csv(R/'ticket_count_distribution.csv',index=False)
res={'production_identity':ident,'odds_source':'BOAT RACE official closing trifecta odds','odds_coverage_R':len(z),'odds_missing_R':len(s)-len(z),'actions':z.action.value_counts().to_dict(),'adaptive':{'bought_R':len(b),'hits':int(b.hit.sum()),'hit_rate_pct':100*float(b.hit.mean()),'total_stake_yen':st,'total_return_yen':ret,'profit_yen':ret-st,'roi_pct':100*ret/st,'avg_final_combined':float(b.final_combined.mean()),'median_final_combined':float(b.final_combined.median())},'baseline_top3_all_covered':{'R':len(z),'hits':int(z.baseline_hit.sum()),'hit_rate_pct':100*float(z.baseline_hit.mean()),'total_stake_yen':bst,'total_return_yen':br,'profit_yen':br-bst,'roi_pct':100*br/bst},'ticket_count_distribution':{str(int(x.n_tickets)):int(x.R) for _,x in d.iterrows()},'SEPTEMBER_OUTCOMES_READ':False}
(R/'result_v340.json').write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding='utf-8'); print(json.dumps(res,indent=2,ensure_ascii=False),flush=True)
