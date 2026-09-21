#!/usr/bin/env python3
"""One-shot March 2026 validation of the frozen 3HEAD opponent rule.
Rule was frozen before March outcome reveal. March and Sep-2026 are never loaded.
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
MAR_START=pd.Timestamp('2026-03-01'); MAR_END=pd.Timestamp('2026-04-01')

def combo(x):
 z=str(x or '').strip().replace(' ','')
 for sep in ['-','>','_','/']:
  if sep in z:
   a=z.split(sep)
   if len(a)==3 and all(q in '123456' for q in a): return [int(q) for q in a]
 return []

def main():
 # Build frozen A+.60 March cohort from pre-settlement inputs only.
 rr={}
 # Historical labels end at Feb-28. March features are fetched outcome-free.
 for k,(a,b) in pg.DEV.items():
  x,r,audit=w20.build_pre_enhanced(a,b,True); rr[k]=(x,r)
 fr={k:w20.prep_month(x,r) for k,(x,r) in rr.items()}
 all_hist=pd.concat([fr[k] for k in ['oct','nov','dec','jan','feb']],ignore_index=True,sort=False)
 _,enh,_=w20.choose_features(all_hist)
 mx,mr,ma=w20.build_pre_enhanced('2026-03-01','2026-03-31',False)
 if len(mr): raise RuntimeError('March result rows unexpectedly loaded')
 rows=[]
 for dayv in sorted(mx.date.dt.normalize().unique()):
  day=pd.Timestamp(dayv); today=mx[mx.date.dt.normalize()==day].copy()
  tr=all_hist[(all_hist.date<day)&(all_hist.date>=day-pd.Timedelta(days=42))].copy()
  if len(tr)<500 or tr.y.nunique()<2: continue
  model=w20.make_pipeline(w20.SimpleImputer(strategy='median'),w20.StandardScaler(),
      w20.LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=1800,random_state=161))
  model.fit(tr[enh],tr.y)
  ptr=model.predict_proba(tr[enh])[:,1]; pred=model.predict_proba(today[enh])[:,1]
  z=today[['rc','date','venue','race_no']].copy(); z['pre_score']=w20.pct_ref(ptr,pred); rows.append(z)
 if not rows: raise RuntimeError('no outcome-free March PRE predictions')
 mar_pre=pd.concat(rows,ignore_index=True).drop_duplicates('rc')

 # Build motor state through Feb-28, then freeze it. March requests cards/previews only.
 import run_3head_wave19_motor_exhibition_gate as w19
 from collections import defaultdict
 w19.END='2026-02-28'
 days,cache=w19.prefetch_sources()
 state=defaultdict(w19.new_motor); global_venue=defaultdict(w19.new_motor)
 for day in sorted(days):
  cards=w19.bycode(cache.get((day.normalize(),'programs/race_cards'),[]))
  results=w19.bycode(cache.get((day.normalize(),'results/realtime'),[]))
  for code,rr0 in results.items():
   rc=cards.get(code)
   if rc is None: continue
   venue=str(rc.get('レース場コード','')).zfill(2); rm0=w19.rank_map(rr0); stm=w19.actual_st_by_boat(rr0)
   for b in range(1,7):
    mid=w19.ival(rc.get(f'艇{b}_モーター番号'))
    if mid is None: continue
    w19.update_motor(state[(venue,mid)],rm0.get(b),stm.get(b,float('nan')),day)
    w19.update_motor(global_venue[venue],rm0.get(b),stm.get(b,float('nan')),day)

 march_days=list(pd.date_range('2026-03-01','2026-03-31')); mcache={}
 from concurrent.futures import ThreadPoolExecutor,as_completed
 kinds=['programs/race_cards','previews/tkz','previews/stt','previews/original_exhibition']
 with ThreadPoolExecutor(max_workers=16) as ex:
  fut={ex.submit(w19.fetch,k,d.date()):(d.normalize(),k) for d in march_days for k in kinds}
  for ff in as_completed(fut):
   dd,kk=fut[ff]
   try: mcache[(dd,kk)]=ff.result()
   except Exception: mcache[(dd,kk)]=[]
 post_rows=[]
 for day in march_days:
  day=day.normalize(); cards=w19.bycode(mcache.get((day,'programs/race_cards'),[]))
  tkz=w19.bycode(mcache.get((day,'previews/tkz'),[])); stt=w19.bycode(mcache.get((day,'previews/stt'),[])); org=w19.bycode(mcache.get((day,'previews/original_exhibition'),[]))
  for code,rc in cards.items():
   venue=str(rc.get('レース場コード','')).zfill(2); z={'rc':int(code),'date':day}; per={}
   for b in range(1,7):
    mid=w19.ival(rc.get(f'艇{b}_モーター番号')); s=state[(venue,mid)] if mid is not None else w19.new_motor()
    sm=w19.motor_summary(s,global_venue[venue],day); per[b]=sm
    for k,v in sm.items(): z[f'post_motor_b{b}_{k}']=v
   for opp in [1,2,4]:
    z[f'post_motor_gap{opp}_top2']=per[3]['top2']-per[opp]['top2']; z[f'post_motor_gap{opp}_top3']=per[3]['top3']-per[opp]['top3']
    z[f'post_motor_rank_edge{opp}']=per[opp]['ewma_rank']-per[3]['ewma_rank']; z[f'post_motor_st_edge{opp}']=per[opp]['ewma_st']-per[3]['ewma_st']
   z['post_motor_inner_rank_edge']=((per[1]['ewma_rank']+per[2]['ewma_rank'])/2)-per[3]['ewma_rank']
   z['post_motor_inner_top2_gap']=per[3]['top2']-((per[1]['top2']+per[2]['top2'])/2)
   z.update(w19.exhibition_features(tkz.get(code,{}),stt.get(code,{}),org.get(code,{}))); post_rows.append(z)
 post=pd.DataFrame(post_rows).drop_duplicates('rc')
 q=mar_pre.merge(post,on=['rc','date'],how='left',validate='one_to_one')
 rn=pd.to_numeric(q.race_no,errors='coerce'); pre=pd.to_numeric(q.pre_score,errors='coerce')
 m=(rn>=1)&(rn<=12)&(pre>=.925)&pg.mask(q,pg.A['conds'])&(pd.to_numeric(q.post_motor_inner_rank_edge,errors='coerce')>=.60)
 codes=set(str(int(x)).zfill(12) for x in q.loc[m,'rc'])
 print('FROZEN_RULE',{'threshold':THRESHOLD,'protected_second4':True,'tickets':6},flush=True)
 print('MAR_PRESETTLEMENT_COHORT',{'selected_codes':len(codes)},flush=True)

 # Canonical V221 features; do not attach any settlement yet.
 raw=pd.read_csv(v221.SRC,dtype={'race_code':str}); dc=v221.v165.pc(raw,['date','race_date','ymd'])
 raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce')
 raw=raw[raw._date.notna()&(raw._date<MAR_END)].copy()
 # Hard-bound V221 fetches to Feb-28; March+ result files must never be fetched.
 from datetime import date,timedelta
 v221.END=date(2026,3,31)
 d=v221.build(raw,dc)
 d['race_code']=d.race_code.astype(str).str.zfill(12)
 d['_date']=pd.to_datetime(d.race_code.str.slice(0,8),format='%Y%m%d',errors='coerce')
 mar=d[(d._date>=MAR_START)&(d._date<MAR_END)&d.race_code.isin(codes)].copy()
 if len(mar)!=len(codes): raise RuntimeError(f'March feature coverage mismatch {len(mar)}/{len(codes)}')
 # Fit V221 direct pair using only rows strictly before March.
 train=d[d._date<MAR_START].copy()
 # V221 fit_pair requires historical settlement labels. Attach labels to TRAIN ONLY.
 from datetime import date,timedelta
 hist_settled=[]; day=date(2025,10,1)
 while day<=date(2026,2,28):
  try:
   for rr0 in v221.rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"):
    code=str(rr0.get('レースコード','')).zfill(12); a3=[str(rr0.get(f'{i}着_艇番','')).strip() for i in (1,2,3)]
    if code.isdigit() and all(x in '123456' and len(x)==1 for x in a3): hist_settled.append({'race_code':code,'actual_combo':'-'.join(a3),'valid_result':1})
  except Exception: pass
  day+=timedelta(days=1)
 hs=pd.DataFrame(hist_settled).drop_duplicates('race_code')
 train=train.drop(columns=['actual_combo','valid_result'],errors='ignore').merge(hs,on='race_code',how='left',validate='many_to_one')
 direct,ntrain=v221.fit_pair(train,True)
 if ntrain<100: raise RuntimeError(f'V221 training too small {ntrain}')
 decisions={}
 for _,r in mar.iterrows():
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
 print('MAR_DECISIONS_FROZEN_BEFORE_SETTLEMENT',{'n':len(decisions),'swaps':sum(v['promoted'] is not None for v in decisions.values())},flush=True)

 # DRY RUN STOPS HERE. March settlement must never be loaded in this script.
 for code,dec in decisions.items():
  if len(dec['base'])!=6 or len(dec['protected'])!=6: raise RuntimeError(f'non-six ticket set {code}')
  if any(not x.startswith('3-') for x in dec['protected']): raise RuntimeError(f'bad ticket format {code}')
 out={'policy':{'dry_run_only':True,'threshold':THRESHOLD,'tickets':6,'march_settlement_loaded':False,'sep2026_loaded':False},
      'march':{'selected_races':len(codes),'decisions':len(decisions),'swaps':sum(v['promoted'] is not None for v in decisions.values())},
      'decisions':decisions}
 Path('research_3head_a_opponent_mar_dryrun.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 rows=[{'race_code':k,**v} for k,v in decisions.items()]
 pd.DataFrame(rows).to_csv('research_3head_a_opponent_mar_dryrun.csv',index=False)
 print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': main()
