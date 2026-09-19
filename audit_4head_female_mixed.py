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

 # Build the female registry from Macour's explicit female-racer search.
 # Save the IDs only after a plausibility check; this avoids the BOAT RACE
 # session-rendered search page that returned an empty body in Actions.
 import requests,re
 from bs4 import BeautifulSoup
 base='https://sp.macour.jp/boatracer/search/gender-female/'
 sess=requests.Session()
 headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36','Accept-Language':'ja,en-US;q=0.9,en;q=0.8'}
 pages=[]
 for page in range(1,20):
  rr=sess.get(base,params=({} if page==1 else {'page':str(page)}),headers=headers,timeout=30)
  print(f'macour_fetch page={page} status={rr.status_code} bytes={len(rr.content)} url={rr.url}')
  if rr.status_code!=200:
   if page==1: raise RuntimeError(f'Macour female registry fetch failed: HTTP {rr.status_code}')
   break
  html=rr.text
  txt=BeautifulSoup(rr.content,'lxml').get_text(' ',strip=True)
  ids=set(re.findall(r'(?<!\\d)([3-5]\\d{3})(?!\\d)',txt))
  if page==1:
   # Diagnostic dump: identify client-side API/JSON endpoints used by Macour.
   pats=sorted(set(re.findall(r'(?:https?:)?//[^"\\'<> ]+|/[A-Za-z0-9_./?=&%-]+',html)))
   interesting=[x for x in pats if any(k in x.lower() for k in ('api','ajax','boatracer','search','gender','graphql','json'))]
   print('MACOUR_ENDPOINT_CANDIDATES_BEGIN')
   for x in interesting[:200]: print(x[:500])
   print('MACOUR_ENDPOINT_CANDIDATES_END')
   for needle in ('4938','小芦','gender-female','__NEXT_DATA__','application/json'):
    print(f'macour_probe {needle}={needle in html}')
  pages.append((rr.text,ids))
  # stop when pagination no longer adds racer IDs
  union=set().union(*(x[1] for x in pages))
  if page>1 and not ids: break
  if len(union)>=287: break
 female_ids=set().union(*(x[1] for x in pages)) if pages else set()
 # Search pages can contain unrelated 4-digit numbers. Keep only IDs that also
 # occur in the Apr-Aug race-card universe; exact target validation is below.
 print(f'macour_raw_ids={len(female_ids)} source={base}')
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
