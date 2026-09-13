#!/usr/bin/env python3
"""Wave19a: enrich the full 678R settled source with official trifecta payout.
Outcome/payout fields are settlement-only and never prediction features.
Also creates a transparent JPY10,000/race 20-combo 3-head equal-stake benchmark:
500 yen on every trifecta starting with boat 3 (20 combinations).
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date
from pathlib import Path
import json,time
import pandas as pd
from backtest import rows

SRC=Path('analysis_v289_3head_wave18b_full_universe_settled.csv')
OUT=Path('analysis_v289_3head_wave19_full_universe_payout_enriched.csv')
OUTJ=Path('research_v289_3head_wave19_payout_enrichment.json')
OUTM=Path('research_v289_3head_wave19_payout_enrichment.md')

def norm(x):
 s=''.join(ch for ch in str(x or '') if ch.isdigit());return s.zfill(12) if s else ''
def combo(x):
 s=str(x or '').strip().replace(' ','').replace('‐','-').replace('－','-')
 try:a=[int(z) for z in s.split('-')]
 except:return ''
 return '-'.join(map(str,a)) if len(a)==3 and len(set(a))==3 and all(1<=z<=6 for z in a) else ''
def money(x):
 try:return int(float(str(x).replace(',','').replace('円','').strip()))
 except:return 0

def pmap(day):
 rs=rows(f"data/results/payouts/{day.strftime('%Y/%m/%d')}.csv")
 return {norm(r.get('レースコード','')):r for r in rs if norm(r.get('レースコード',''))}

def main():
 q=pd.read_csv(SRC,dtype={'race_code':str});q['date']=q.date.astype(str);q['race_code_norm']=q.race_code.map(norm)
 if q.date.max()>'2026-08-31':raise RuntimeError('September outcomes forbidden')
 if len(q)!=678:raise RuntimeError(f'unexpected source rows {len(q)}')
 days=sorted({date.fromisoformat(x) for x in q.date});maps={}
 with ThreadPoolExecutor(max_workers=10) as ex:
  fs={ex.submit(pmap,d):d for d in days}
  for f in as_completed(fs):maps[fs[f]]=f.result()
 for d in days:
  exp=set(q.loc[q.date==d.isoformat(),'race_code_norm']);mp=maps[d];best=len(exp&set(mp))
  if exp and best/len(exp)<.98:
   for a in range(1,4):
    time.sleep(.15*a);nm=pmap(d);n=len(exp&set(nm))
    if n>best:mp,best=nm,n
    if best/len(exp)>=.98:break
   maps[d]=mp
 payouts=[];matches=[];present=[]
 for r in q.itertuples(index=False):
  pr=maps[date.fromisoformat(r.date)].get(r.race_code_norm,{})
  present.append(int(bool(pr)))
  pc=combo(pr.get('3連単_組番',''));ac=combo(getattr(r,'actual_combo_recovered',''))
  payouts.append(money(pr.get('3連単_払戻金','')))
  matches.append(int(bool(pc and ac and pc==ac)))
 q['payout_row_present']=present;q['trifecta_payout_100_yen']=payouts;q['payout_combo_matches_actual']=matches
 q['head3_equal20_stake_yen']=10000
 q['head3_equal20_payout_yen']=q.apply(lambda r:int(r.trifecta_payout_100_yen*5) if int(r.head3_actual)==1 else 0,axis=1)
 q['head3_equal20_profit_yen']=q.head3_equal20_payout_yen-q.head3_equal20_stake_yen
 q.to_csv(OUT,index=False,encoding='utf-8-sig')
 n=len(q);pres=int(q.payout_row_present.sum());mat=int(q.payout_combo_matches_actual.sum());positive=int((q.trifecta_payout_100_yen>0).sum())
 stake=int(q.head3_equal20_stake_yen.sum());pay=int(q.head3_equal20_payout_yen.sum());roi=100*pay/stake
 audit={'unique_races':n,'payout_rows':pres,'payout_row_share':pres/n,'positive_trifecta_payout_rows':positive,'combo_match_rows':mat,'combo_match_share':mat/n,'max_date':q.date.max(),'benchmark_equal20':{'stake_yen':stake,'payout_yen':pay,'profit_yen':pay-stake,'roi_pct':roi}}
 decision='PAYOUT_SOURCE_READY' if pres/n>=.98 and mat/n>=.999 and positive/n>=.98 else 'PAYOUT_AUDIT_FAIL_CLOSED';audit['decision']=decision
 OUTJ.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 md=f'''# 3号艇 Wave19a — payout enrichment\n\n- unique races: **{n}**\n- payout rows: **{pres} ({100*pres/n:.2f}%)**\n- exact payout combo matches recovered outcome: **{mat} ({100*mat/n:.3f}%)**\n- positive trifecta payout rows: **{positive}**\n- max date: **{q.date.max()}**\n\n## Transparent 3-head 20-combo benchmark\n- stake: **{stake:,} yen**\n- payout: **{pay:,} yen**\n- profit: **{pay-stake:+,} yen**\n- ROI: **{roi:.2f}%**\n\n## Decision\n**{decision}**\n'''
 OUTM.write_text(md,encoding='utf-8');print(md)
 if decision!='PAYOUT_SOURCE_READY':raise RuntimeError(decision)
if __name__=='__main__':main()
