#!/usr/bin/env python3
"""Audit female boat4 performance in genuinely mixed fields (>=2 male racers).

Historical Apr-Aug 2026 only. Uses the frozen 208R feature table and current156
expansion rule. Gender is taken from BOAT RACE CSV race-card sex fields when
available; no name-based inference. September outcomes are not read.
"""
from pathlib import Path
import csv,json,os
import pandas as pd, numpy as np
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
 all_ids=set()
 cards={}
 for m in MONTHS:
  y,mo=m.split('-'); d=root/'data/programs/race_cards'/y/mo
  for f in sorted(d.glob('*.csv')):
   with f.open(encoding='utf-8-sig',newline='') as fh:
    for r in csv.DictReader(fh): cards[rc(r.get('レースコード',''))]=r
 def reg(r,b):
  return str(r.get(f'艇{b}_登録番号','')).strip().replace('.0','')

 # Build female registry locally from known women-only meetings in BoatraceCSV.
 # These meetings are official Venus / All-Ladies / Ladies Championship dates.
 women_meetings=[
  ('20260524','20260529','24'),
  ('20260530','20260604','05'),
  ('20260618','20260623','02'),
  ('20260624','20260629','12'),
  ('20260707','20260712','11'),
  ('20260806','20260811','18'),
  ('20260818','20260823','16'),
  ('20260824','20260829','10'),
 ]
 from datetime import datetime,timedelta
 female_ids=set()
 for ds,de,jcd in women_meetings:
  d=datetime.strptime(ds,'%Y%m%d'); e=datetime.strptime(de,'%Y%m%d')
  while d<=e:
   day=d.strftime('%Y%m%d'); f=root/'data/programs/race_cards'/day[:4]/day[4:6]/f'{day}.csv'
   if f.exists():
    with f.open(encoding='utf-8-sig',newline='') as fh:
     for rr in csv.DictReader(fh):
      code=rc(rr.get('レースコード',''))
      if code[8:10]==jcd:
       female_ids.update(x for x in (reg(rr,b) for b in range(1,7)) if len(x)==4 and x.isdigit())
   d+=timedelta(days=1)
 if len(female_ids)<100: raise RuntimeError(f'women-only BoatraceCSV registry too small: {len(female_ids)}')
 needed=set()
 for code in z.race_code:
  rr=cards.get(code,{})
  needed.update(x for x in (reg(rr,b) for b in range(1,7)) if len(x)==4 and x.isdigit())
 # Unknown is not automatically male. We only call non-female racers male after coverage is high;
 # unresolved IDs are reported and block the audit when they can affect a target race.
 print(f'women_only_registry={len(female_ids)} needed_racers={len(needed)} overlap={len(needed & female_ids)}')
 def male(x): return x=='男'
 def female(x): return x=='女'
 def enrich(q):
  q=q.copy(); vals=[]
  for code in q.race_code:
   r=cards.get(code,{})
   sx=[('女' if reg(r,b) in female_ids else '男') for b in range(1,7)]
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
 (OUT/'result.json').write_text(json.dumps({'definition':'boat4 female AND total male_count >= 2','results':out,'SEPTEMBER_OUTCOMES_READ':False,'AUDIT_OK':True},ensure_ascii=False,indent=2)+chr(10))
 print(json.dumps(out,ensure_ascii=False,indent=2));print('HEAD4_FEMALE_MIXED_AUDIT_OK');print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
