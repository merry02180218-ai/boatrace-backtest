#!/usr/bin/env python3
"""Wave18b: recover actual outcomes for the full 3-head research universe.
Settlement is attached only after the frozen v243 feature table is loaded.
Sources: realtime results -> payout 3連単 -> archived actual_combo fallback for official rows.
No settlement field is a prediction feature. September is forbidden.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
import json,time
import pandas as pd
from backtest import rows

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('analysis_v289_3head_wave18b_full_universe_settled.csv')
OUTJ=Path('research_v289_3head_wave18b_settlement_recovery.json')
OUTM=Path('research_v289_3head_wave18b_settlement_recovery.md')

def norm(x):
 s=''.join(ch for ch in str(x or '') if ch.isdigit()); return s.zfill(6) if s else ''
def combo(x):
 s=str(x or '').strip().replace(' ','').replace('‐','-').replace('－','-')
 try:a=[int(z) for z in s.split('-')]
 except:return ''
 return '-'.join(map(str,a)) if len(a)==3 and len(set(a))==3 and all(1<=z<=6 for z in a) else ''
def ii(x):
 try:return int(float(x))
 except:return 0

def maps(day):
 ymd=day.strftime('%Y/%m/%d'); rt=rows(f'data/results/realtime/{ymd}.csv'); po=rows(f'data/results/payouts/{ymd}.csv')
 return ({norm(r.get('レースコード')):r for r in rt if norm(r.get('レースコード'))}, {norm(r.get('レースコード')):r for r in po if norm(r.get('レースコード'))})

def archive_map():
 # v243 already contains actual_combo where archived settlement was carried into the frozen audit.
 q=pd.read_csv(SRC,dtype={'race_code':str}); mp={}
 if 'actual_combo' in q.columns:
  for r in q.itertuples(index=False):
   c=combo(getattr(r,'actual_combo',''))
   if c:mp[(str(r.date),norm(r.race_code))]=c
 return mp

def main():
 q=pd.read_csv(SRC,dtype={'race_code':str});q['date']=q.date.astype(str);q['race_code']=q.race_code.map(norm)
 if q.date.max()>'2026-08-31':raise RuntimeError('September outcomes forbidden')
 q=q.drop_duplicates('race_code').copy(); days=sorted({date.fromisoformat(x) for x in q.date}); fetched={}
 with ThreadPoolExecutor(max_workers=10) as ex:
  fs={ex.submit(maps,d):d for d in days}
  for f in as_completed(fs): fetched[fs[f]]=f.result()
 # bounded retry for dates with weak official coverage
 for d in days:
  exp=set(q.loc[q.date==d.isoformat(),'race_code']);rt,po=fetched[d];best=len(exp&(set(rt)|set(po)))
  if exp and best/len(exp)<.98:
   for a in range(1,4):
    time.sleep(.15*a);nrt,npo=maps(d);n=len(exp&(set(nrt)|set(npo)))
    if n>best:rt,po,best=nrt,npo,n
    if best/len(exp)>=.98:break
   fetched[d]=(rt,po)
 arc=archive_map(); actual=[];official=[];src=[]
 for r in q.itertuples(index=False):
  d=date.fromisoformat(r.date);rt,po=fetched[d];rr=rt.get(r.race_code,{});pr=po.get(r.race_code,{});off=bool(rr or pr);c='';s=''
  a,b,c3=ii(rr.get('1着_艇番')),ii(rr.get('2着_艇番')),ii(rr.get('3着_艇番'))
  if len({a,b,c3})==3 and all(1<=z<=6 for z in (a,b,c3)):c=f'{a}-{b}-{c3}';s='realtime'
  if not c:
   pc=combo(pr.get('3連単_組番',''))
   if pc:c=pc;s='payout'
  if off and not c:
   ac=arc.get((r.date,r.race_code),'')
   if ac:c=ac;s='archive'
  actual.append(c);official.append(int(off));src.append(s)
 q['actual_combo_recovered']=actual;q['official_settlement_row']=official;q['settlement_source']=src
 q['winner_recovered']=q.actual_combo_recovered.str.split('-').str[0].map(ii);q['head3_actual']=(q.winner_recovered==3).astype(int)
 q.to_csv(OUT,index=False,encoding='utf-8-sig')
 n=len(q);off=int(q.official_settlement_row.sum());exact=int((q.actual_combo_recovered!='').sum());head3=int(q.head3_actual.sum())
 source=q.settlement_source.value_counts().to_dict();audit={'unique_races':n,'official_rows':off,'official_share':off/n,'exact_rows':exact,'exact_given_official':exact/off if off else 0,'head3_wins':head3,'sources':source,'max_date':q.date.max()}
 decision='SETTLED_SOURCE_READY' if off/n>=.98 and exact/off>=.999 else 'SETTLEMENT_AUDIT_FAIL_CLOSED'
 audit['decision']=decision;OUTJ.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 md=f'''# 3号艇 Wave18b — full-universe settlement recovery\n\n- unique races: **{n}**\n- official settlement rows: **{off} ({100*off/n:.2f}%)**\n- exact-order recovered: **{exact}**\n- exact / official: **{100*exact/off if off else 0:.3f}%**\n- actual 3-head wins: **{head3}**\n- sources: `{source}`\n- max date: **{q.date.max()}**\n\n## Decision\n**{decision}**\n'''
 OUTM.write_text(md,encoding='utf-8');print(md)
 if decision!='SETTLED_SOURCE_READY':raise RuntimeError(decision)
if __name__=='__main__':main()
