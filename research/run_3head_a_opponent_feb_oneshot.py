#!/usr/bin/env python3
"""One-shot February 2026 validation of the frozen 3HEAD opponent rule.
Rule was frozen before February outcome reveal. March and Sep-2026 are never loaded.
"""
from __future__ import annotations
import json, sys, pandas as pd
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analyze_v221_3head_scenario_pair as v221
import run_3head_a_purchase_gate_dev as pg
import run_3head_wave20_manual_gate as w20

THRESHOLD=.50
FEB_START=pd.Timestamp('2026-02-01'); FEB_END=pd.Timestamp('2026-03-01')

def combo(x):
 z=str(x or '').strip().replace(' ','')
 for sep in ['-','>','_','/']:
  if sep in z:
   a=z.split(sep)
   if len(a)==3 and all(q in '123456' for q in a): return [int(q) for q in a]
 return []

def main():
 # Build frozen A+.60 February cohort from pre-settlement inputs only.
 rr={}
 # make_pre_scores has a fixed causal walk-forward contract: oct is history and nov-feb are scored.
 # Build all five months, but do not inspect any outcome here; labels are only internal prior-day model training inputs.
 for k,(a,b) in pg.DEV.items():
  x,r,audit=w20.build_pre_enhanced(a,b,True); rr[k]=(x,r)
 fr={k:w20.prep_month(x,r) for k,(x,r) in rr.items()}
 missing=[k for k in ['oct','nov','dec','jan','feb'] if k not in fr]
 if missing: raise RuntimeError(f'make_pre_scores frame contract missing {missing}')
 scores,_=w20.make_pre_scores(fr)
 days,cache=w20.prefetch_sources(); post,_=w20.build_motor_exhibition(days,cache)
 q=scores['feb'].merge(post,on=['rc','date'],how='left',validate='one_to_one')
 rn=pd.to_numeric(q.race_no,errors='coerce'); pre=pd.to_numeric(q.pre_score,errors='coerce')
 m=(rn>=1)&(rn<=12)&(pre>=.925)&pg.mask(q,pg.A['conds'])&(pd.to_numeric(q.post_motor_inner_rank_edge,errors='coerce')>=.60)
 codes=set(str(int(x)).zfill(12) for x in q.loc[m,'rc'])
 print('FROZEN_RULE',{'threshold':THRESHOLD,'protected_second4':True,'tickets':6},flush=True)
 print('FEB_PRESETTLEMENT_COHORT',{'selected_codes':len(codes)},flush=True)

 # Canonical V221 features; do not attach any settlement yet.
 raw=pd.read_csv(v221.SRC,dtype={'race_code':str}); dc=v221.v165.pc(raw,['date','race_date','ymd'])
 y,_=v221.v165.target(raw); raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce'); raw['_y']=y
 raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<v221.CONTAM)].copy(); d=v221.build(raw,dc)
 d['race_code']=d.race_code.astype(str).str.zfill(12)
 d['_date']=pd.to_datetime(d.race_code.str.slice(0,8),format='%Y%m%d',errors='coerce')
 feb=d[(d._date>=FEB_START)&(d._date<FEB_END)&d.race_code.isin(codes)].copy()
 if len(feb)!=len(codes): raise RuntimeError(f'February feature coverage mismatch {len(feb)}/{len(codes)}')
 # Fit V221 direct pair using only rows strictly before February.
 train=d[d._date<FEB_START].copy()
 # V221 fit_pair requires historical settlement labels. Attach labels to TRAIN ONLY; February stays unlabeled until decisions freeze.\n from datetime import date,timedelta\n hist_settled=[]; day=date(2025,10,1)\n while day<=date(2026,1,31):\n  try:\n   for rr0 in v221.rows(f\"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv\"):\n    code=str(rr0.get('レースコード','')).zfill(12); a=[str(rr0.get(f'{i}着_艇番','')).strip() for i in (1,2,3)]\n    if code.isdigit() and all(x in '123456' and len(x)==1 for x in a): hist_settled.append({'race_code':code,'actual_combo':'-'.join(a),'valid_result':1})\n  except Exception: pass\n  day+=timedelta(days=1)\n hs=pd.DataFrame(hist_settled).drop_duplicates('race_code')\n train=train.drop(columns=['actual_combo','valid_result'],errors='ignore').merge(hs,on='race_code',how='left',validate='many_to_one')\n direct,ntrain=v221.fit_pair(train,True)\n if ntrain<100: raise RuntimeError(f'V221 training too small {ntrain}')
 decisions={}
 for _,r in feb.iterrows():
  order=v221.order(r,direct,True)
  old=order[:6]; new=list(old)
  turn4=pd.to_numeric(pd.Series([v221.xtra(r,4,'vh_p12_turn')]),errors='coerce').iloc[0]
  promoted=dropped=None
  if pd.notna(turn4) and turn4>=THRESHOLD:
   cand=[x for x in order if x.startswith('3-4-') and x not in old]
   drop_idx=[i for i,x in enumerate(new) if not x.startswith('3-4-')]
   if cand and drop_idx:
    promoted=cand[0]; di=drop_idx[-1]; dropped=new[di]; new[di]=promoted
  decisions[str(r.race_code)]={'base':old,'protected':new,'turn4':None if pd.isna(turn4) else float(turn4),'promoted':promoted,'dropped':dropped}
 print('FEB_DECISIONS_FROZEN_BEFORE_SETTLEMENT',{'n':len(decisions),'swaps':sum(v['promoted'] is not None for v in decisions.values())},flush=True)

 # Only now reveal February settlement. Hard stop at Feb-28: March is never requested.
 from datetime import date,timedelta
 settled={}; day=date(2026,2,1)
 while day<=date(2026,2,28):
  try:
   for rr in v221.rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"):
    code=str(rr.get('レースコード','')).zfill(12); a=[str(rr.get(f'{i}着_艇番','')).strip() for i in (1,2,3)]
    if code in codes and all(x in '123456' and len(x)==1 for x in a): settled[code]='-'.join(a)
  except Exception: pass
  day+=timedelta(days=1)
 if len(settled)!=len(codes): print('WARNING_SETTLEMENT_COVERAGE',{'settled':len(settled),'selected':len(codes)},flush=True)
 headwins=basehits=newhits=rescued=lost=0; rows=[]
 for code,dec in decisions.items():
  actual=settled.get(code)
  if not actual: continue
  ishead=actual.startswith('3-')
  if not ishead: continue
  headwins+=1; bh=actual in dec['base']; nh=actual in dec['protected']
  basehits+=int(bh); newhits+=int(nh); rescued+=int((not bh) and nh); lost+=int(bh and (not nh))
  rows.append({'race_code':code,'actual':actual,'base_hit':bh,'protected_hit':nh,'turn4':dec['turn4'],'promoted':dec['promoted'],'dropped':dec['dropped']})
 out={'policy':{'rule_frozen_before_feb_reveal':True,'threshold':THRESHOLD,'tickets':6,'march_loaded':False,'sep2026_loaded':False,'threshold_tuning_on_feb':False},
      'feb':{'selected_races':len(codes),'settled_races':len(settled),'boat3_wins':headwins,'base_hits':basehits,'protected_hits':newhits,
             'base_capture':basehits/headwins if headwins else None,'protected_capture':newhits/headwins if headwins else None,
             'rescued':rescued,'lost':lost,'net':newhits-basehits},'rows':rows}
 Path('research_3head_a_opponent_feb_oneshot.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 pd.DataFrame(rows).to_csv('research_3head_a_opponent_feb_oneshot.csv',index=False)
 print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': main()
