#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

P=Path('/tmp/v343/race_level.csv'); O=Path('/tmp/v343out'); O.mkdir(parents=True,exist_ok=True)
d=pd.read_csv(P,dtype={'race_code':str})
assert len(d)==276 and int(d.head_hit.sum())==241 and int(d.baseline_hit.sum())==119
assert not d.month.astype(str).str.startswith('2026-09').any()
pr=d[d.month.isin(['2026-02','2026-03','2026-04','2026-05','2026-06'])].copy()
thresholds=[round(2.0+i*.05,2) for i in range(17)]
rows=[]; monthly=[]; lomo=[]
for t in thresholds:
  for scope,x in [('pristine_feb_jun',pr),('all_feb_aug',d)]:
    b=x[x.top3_combined>=t]; st=float(b.baseline_stake_yen.sum()); ret=float(b.baseline_return_yen.sum())
    rows.append({'threshold':t,'scope':scope,'population_R':len(x),'bought_R':len(b),'bet_rate_pct':100*len(b)/len(x),'hits':int(b.baseline_hit.sum()),'hit_rate_pct':100*float(b.baseline_hit.mean()) if len(b) else None,'stake_yen':st,'return_yen':ret,'profit_yen':ret-st,'roi_pct':100*ret/st if st else None})
  for m,g in pr.groupby('month',sort=True):
    b=g[g.top3_combined>=t]; st=float(b.baseline_stake_yen.sum()); ret=float(b.baseline_return_yen.sum())
    monthly.append({'threshold':t,'month':m,'bought_R':len(b),'hits':int(b.baseline_hit.sum()),'profit_yen':ret-st,'roi_pct':100*ret/st if st else None})
    x=pr[pr.month!=m]; bb=x[x.top3_combined>=t]; s=float(bb.baseline_stake_yen.sum()); rr=float(bb.baseline_return_yen.sum())
    lomo.append({'threshold':t,'excluded_month':m,'bought_R':len(bb),'hits':int(bb.baseline_hit.sum()),'profit_yen':rr-s,'roi_pct':100*rr/s if s else None})
# odds bins diagnose marginal bands
edges=[0,2.0,2.1,2.2,2.3,2.4,2.5,2.6,2.7,2.8,3.0,3.5,4.0,999]
pr['odds_bin']=pd.cut(pr.top3_combined,bins=edges,right=False)
bins=[]
for k,g in pr.groupby('odds_bin',observed=True):
 st=float(g.baseline_stake_yen.sum()); ret=float(g.baseline_return_yen.sum())
 bins.append({'odds_bin':str(k),'R':len(g),'hits':int(g.baseline_hit.sum()),'profit_yen':ret-st,'roi_pct':100*ret/st if st else None})
r=pd.DataFrame(rows); mm=pd.DataFrame(monthly); lm=pd.DataFrame(lomo); bn=pd.DataFrame(bins)
r.to_csv(O/'threshold_summary.csv',index=False); mm.to_csv(O/'threshold_monthly.csv',index=False); lm.to_csv(O/'threshold_lomo.csv',index=False); bn.to_csv(O/'odds_bins.csv',index=False)
p=r[r.scope=='pristine_feb_jun'].copy(); lmstat=lm.groupby('threshold').agg(lomo_min_roi=('roi_pct','min'),lomo_min_profit=('profit_yen','min')).reset_index(); p=p.merge(lmstat,on='threshold')
# volume-first candidates: ROI>=105 and maximize bought_R; secondary ROI>=110
c105=p[p.roi_pct>=105].sort_values(['bought_R','roi_pct'],ascending=[False,False]); c110=p[p.roi_pct>=110].sort_values(['bought_R','roi_pct'],ascending=[False,False])
res={'production_identity':{'R':276,'head':241,'exact3_top3':119,'sha256':'89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73'},'best_volume_roi_ge_105':c105.iloc[0].to_dict() if len(c105) else None,'best_volume_roi_ge_110':c110.iloc[0].to_dict() if len(c110) else None,'SEPTEMBER_OUTCOMES_READ':False}
(O/'result_v343.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); print(json.dumps(res,ensure_ascii=False,indent=2,default=str))
