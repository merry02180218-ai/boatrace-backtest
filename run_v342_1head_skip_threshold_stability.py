#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

P=Path('/tmp/v342/race_level.csv'); O=Path('/tmp/v342out'); O.mkdir(parents=True,exist_ok=True)
d=pd.read_csv(P,dtype={'race_code':str})
assert len(d)==276 and int(d.head_hit.sum())==241 and int(d.baseline_hit.sum())==119
assert not d.month.astype(str).str.startswith('2026-09').any()
pr=d[d.month.isin(['2026-02','2026-03','2026-04','2026-05','2026-06'])].copy()
thresholds=[2.7,2.8,2.9,3.0,3.1,3.2,3.3]
rows=[]; monthly=[]
for t in thresholds:
  for scope,x in [('pristine_feb_jun',pr),('all_feb_aug',d)]:
    b=x[x.top3_combined>=t]
    st=float(b.baseline_stake_yen.sum()); ret=float(b.baseline_return_yen.sum())
    rows.append({'threshold':t,'scope':scope,'population_R':len(x),'bought_R':len(b),'hits':int(b.baseline_hit.sum()),'hit_rate_pct':100*float(b.baseline_hit.mean()) if len(b) else None,'stake_yen':st,'return_yen':ret,'profit_yen':ret-st,'roi_pct':100*ret/st if st else None})
  for m,g in pr.groupby('month',sort=True):
    b=g[g.top3_combined>=t]; st=float(b.baseline_stake_yen.sum()); ret=float(b.baseline_return_yen.sum())
    monthly.append({'threshold':t,'month':m,'bought_R':len(b),'hits':int(b.baseline_hit.sum()),'profit_yen':ret-st,'roi_pct':100*ret/st if st else None})
r=pd.DataFrame(rows); mm=pd.DataFrame(monthly)
r.to_csv(O/'threshold_summary.csv',index=False); mm.to_csv(O/'threshold_monthly_pristine.csv',index=False)
p=r[r.scope=='pristine_feb_jun'].copy(); p['positive_profit']=p.profit_yen>0
best_roi=p.sort_values(['roi_pct','bought_R'],ascending=[False,False]).iloc[0]
res={'production_identity':{'R':276,'head':241,'exact3_top3':119,'sha256':'89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73'},'thresholds':thresholds,'pristine_best_by_total_roi':{'threshold':float(best_roi.threshold),'bought_R':int(best_roi.bought_R),'hits':int(best_roi.hits),'profit_yen':float(best_roi.profit_yen),'roi_pct':float(best_roi.roi_pct)},'threshold_3_0':p[p.threshold==3.0].iloc[0].to_dict(),'SEPTEMBER_OUTCOMES_READ':False}
(O/'result_v342.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); print(json.dumps(res,ensure_ascii=False,indent=2,default=str))
