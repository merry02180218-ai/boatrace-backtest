#!/usr/bin/env python3
"""Audit female boat4 performance in genuinely mixed fields (>=2 male racers).

Historical Apr-Aug 2026 only. Uses the frozen 208R feature table and current156
expansion rule. Gender is taken from BOAT RACE CSV race-card sex fields when
available; no name-based inference. September outcomes are not read.
"""
from pathlib import Path
import csv,json,os
import pandas as pd, numpy as np, requests
OUT=Path('/tmp/head4_female_mixed_audit');OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
def rc(x): return str(x).replace('.0','').zfill(12)
def metrics(q):
 n=len(q); pay=float(pd.to_numeric(q.payout_if_bet,errors='coerce').fillna(0).sum()) if n else 0
 return {'R':n,'head4':int(q.head4.sum()) if n else 0,'head4_rate':100*float(q.head4.mean()) if n else None,
 'mean_head_prob':100*float(q.head_prob.mean()) if n else None,'calibration_gap_pp':100*float(q.head4.mean()-q.head_prob.mean()) if n else None,
 'exact3':int(q.raw_hit.sum()) if n else 0,'stake':10000*n,'payout':pay,'ROI':100*pay/(10000*n) if n else None}
def main():
 p=os.environ['EXPANDED_FEATURES_208']; root=Path(os.environ['BOATRACECSV_LOCAL_ROOT'])
 z=pd.read_csv(p,dtype={'race_code':str});z.race_code=z.race_code.map(rc)
 z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
 nb=z[~z.base120].copy()
 add=(nb.composite_odds.ge(3.5)&nb.quality.ge(.75)&nb.head_prob.ge(.16)&nb.opponent_mass.ge(.30)&nb.st4_adv_inside.ge(-.80)&nb.orig4_adv_inside.ge(-.35))
 nb['extension36']=add.astype(int); ext=nb[add].copy(); comb=pd.concat([z[z.base120],ext],ignore_index=True)
 female_ids=set()
 for term in ('20261','20262'):
  html=requests.get(f'https://boatrace-db.net/trank/wracer/term/{term}/',timeout=30,headers={'User-Agent':'Mozilla/5.0'}).text
  found=0
  for t in pd.read_html(html):
   for col in t.columns:
    if str(col).strip() in ('登番','登録番号'):
     ids=pd.to_numeric(t[col],errors='coerce').dropna().astype(int)
     female_ids.update(str(x) for x in ids if 2000<=x<=6000); found+=len(ids)
  if not found: raise RuntimeError(f'female registry parse failed {term}')
 print(f'female_registry={len(female_ids)}')
 cards={}
 for m in MONTHS:
  y,mo=m.split('-'); d=root/'data/programs/race_cards'/y/mo
  for f in sorted(d.glob('*.csv')):
   with f.open(encoding='utf-8-sig',newline='') as fh:
    for r in csv.DictReader(fh): cards[rc(r.get('レースコード',''))]=r
 def reg(r,b):
  return str(r.get(f'艇{b}_登録番号','')).strip().replace('.0','')
 def enrich(q):
  q=q.copy(); vals=[]
  for code in q.race_code:
   r=cards.get(code,{})
   sx=[sexval(r,b) for b in range(1,7)]
   vals.append((sx[3],sum(male(x) for x in sx),sum(female(x) for x in sx),sum(bool(x) for x in sx)))
  q[['boat4_sex','male_count','female_count','sex_known_count']]=pd.DataFrame(vals,index=q.index)
  q['target_female_mixed']=(q.boat4_sex.eq('女')&q.male_count.ge(2)&q.sex_known_count.eq(6))
  return q
 out={}
 details=[]
 for name,q in [('base120',z[z.base120]),('extension36',ext),('combined156',comb)]:
  q=enrich(q); target=q[q.target_female_mixed]; other=q[~q.target_female_mixed]
  out[name]={'all':metrics(q),'female_mixed_male2plus':metrics(target),'other':metrics(other),
             'sex_complete_R':int(q.sex_known_count.eq(6).sum())}
  for males in range(2,6):
   g=q[q.target_female_mixed&q.male_count.eq(males)]
   out[name][f'female_mixed_male{males}']=metrics(g)
  t=target.copy();t['scope']=name;details.append(t)
 pd.concat(details,ignore_index=True).to_csv(OUT/'female_mixed_detail.csv',index=False)
 (OUT/'result.json').write_text(json.dumps({'definition':'boat4 female AND total male_count >= 2','results':out,'SEPTEMBER_OUTCOMES_READ':False,'AUDIT_OK':True},ensure_ascii=False,indent=2)+'
')
 print(json.dumps(out,ensure_ascii=False,indent=2));print('HEAD4_FEMALE_MIXED_AUDIT_OK');print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
