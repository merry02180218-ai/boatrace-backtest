#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,subprocess,sys
from datetime import date,timedelta
from pathlib import Path
import pandas as pd
from backtest import rows
import onehead_production_profile as prod
import run_v326_1head_ticketaware_exhibition as v326
import run_v332_1head_attack_first_redesign as v332
import run_1head_v351_live_finalize as fin
from probe_1head_v351_boatcast_exhibition import ORIG_REQUIRED,AUDIT_KEY


def bycode(rs):
 return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}


def write_cards(cards,path):
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  fs=sorted(set().union(*(r.keys() for r in cards)))
  w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(cards)


def st_state_until(target):
 sums={b:[] for b in range(1,7)};allv=[];d=date(2025,10,1)
 while d<target:
  v326.update_st(rows(f'data/previews/stt/{d:%Y/%m/%d}.csv'),sums,allv);d+=timedelta(days=1)
 return sums,allv


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--start-day',type=int,required=True);ap.add_argument('--end-day',type=int,required=True);ap.add_argument('--sep-source',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
 if not (1<=a.start_day<=a.end_day<=16):raise RuntimeError('audit range must stay within 2026-09-01..16')
 sep=pd.read_csv(a.sep_source,dtype={'race_code':str});sep.race_code=sep.race_code.astype(str).str.zfill(12)
 if (pd.to_datetime(sep.date).dt.date>=date(2026,9,17)).any():raise RuntimeError('Sep source contains 2026-09-17 or future rows')
 train=v332.load_all();train['date']=[f'{c[:4]}-{c[4:6]}-{c[6:8]}' for c in train.race_code.astype(str).str.zfill(12)]
 first_target=date(2026,9,a.start_day);sums,allv=st_state_until(first_target);allout=[]
 for day in range(a.start_day,a.end_day+1):
  target=date(2026,9,day);ymd=f'{target:%Y/%m/%d}';ymd8=f'{target:%Y%m%d}';work=Path(f'/tmp/v351_audit_d{day:02d}');work.mkdir(parents=True,exist_ok=True)
  cards=rows(f'data/programs/race_cards/{ymd}.csv')
  if not cards:continue
  cp=work/'race_cards.csv';write_cards(cards,cp);bases=[]
  if day==1:
   subprocess.run([sys.executable,'prepare_1head_v351_live_cache.py','--date',str(target),'--cards',str(cp),'--out',str(work)],check=True)
   bases=[json.load(open(p)) for p in work.glob(f'{ymd8}*.json') if p.name!='meta.json']
  else:
   prior=sep[pd.to_datetime(sep.date).dt.date<target].copy()
   if prior.empty or max(pd.to_datetime(prior.date).dt.date)>=target:raise RuntimeError(f'rolling chronology failure {target}')
   sp=work/'sep.csv';prior.to_csv(sp,index=False)
   subprocess.run([sys.executable,'prepare_1head_v351_rolling_models.py','--target-date',str(target),'--sep-source',str(sp),'--cards',str(cp),'--out-dir',str(work)],check=True)
   z=json.load(open(work/'rolling_models.json'));m=z['meta']
   if m.get('training_cutoff')!=str(target-timedelta(days=1)) or m.get('same_day_outcomes_read') is not False or m.get('target_or_future_rows')!=0 or m.get('chronology_guard') is not True:raise RuntimeError(f'rolling meta guard failed {target}: {m}')
   if m.get('ticket_strategy')!='HYBRID':raise RuntimeError(f'rolling ticket strategy mismatch {target}: {m.get("ticket_strategy")}')
   for r in z['races']:
    bases.append({**r,'pre_class':'RETRO','legacy_pre_p':r['final_head_p'],'production_profile':prod.PROFILE_NAME,'training_cutoff':str(target-timedelta(days=1)),'result_or_payout_used':False,'chronology_guard':True})
  tkz=bycode(rows(f'data/previews/tkz/{ymd}.csv'));strows=rows(f'data/previews/stt/{ymd}.csv');stt=bycode(strows);orig=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'));bias=v326.st_bias(sums,allv)
  res=bycode(rows(f'data/results/realtime/{ymd}.csv'));pay=bycode(rows(f'data/results/payouts/{ymd}.csv'))
  for b in bases:
   code=str(b['race_code']).zfill(12)
   if not code.startswith(ymd8):raise RuntimeError(f'cross-day candidate {code} for {target}')
   if float(b['final_head_p'])<prod.HEAD_CUTOFF or float(b['opp_mass'])<prod.OPPONENT_MASS_MIN:continue
   tr,sr,orr=tkz.get(code,{}),stt.get(code,{}),orig.get(code,{})
   audit=v326.raw_completeness(tr,sr,orr);req=ORIG_REQUIRED.get(int(code[8:10]),('avg','turn','straight'));keys=['tkz_all6','stt_all6']+[AUDIT_KEY[x] for x in req]
   if not all(audit.get(k,False) for k in keys):continue
   ex,st,os=v326.corrected_direct(code,{code:tr},{code:sr},{code:orr},bias)
   feat=v326.partial_feature_row({'tickets':b['base_tickets']},ex,st,os,audit);feat.update(audit)
   feat['attack_ready']=bool(audit['tkz_all6'] and audit['stt_all6'] and audit['orig_straight_all6'] and audit['orig_avg_all6']);feat['env_ready']=bool(audit['tkz_all6'] and audit['stt_all6'] and audit['orig_turn_all6'] and audit['orig_straight_all6'])
   feat['attack_core']=prod.ATTACK_CORE_W_ONE_EX*feat['one_ex']+prod.ATTACK_CORE_W_ONE_ST*feat['one_st']+prod.ATTACK_CORE_W_ONE_STRAIGHT*feat['one_straight']+prod.ATTACK_CORE_W_ONE_ORIG_AVG*feat['one_orig_avg']
   feat['env_pair']=.30*feat['sec_ex_mean_margin']+.30*feat['sec_st_mean_margin']+.20*feat['third_turn_mean_margin']+.20*feat['third_straight_mean_margin'] if feat['env_ready'] else float('nan')
   hist=train[pd.to_datetime(train.date).dt.date<=target-timedelta(days=1)].copy();test=pd.DataFrame([{**feat,'race_code':code,'head_hit':0,'hit':0}]);passed,_=v332.fit_apply(hist,test,{'family':'ATTACK_ENV_SOFT','env_w':prod.EXHIBITION_ENV_W,'q':prod.EXHIBITION_Q})
   if len(passed)!=1:continue
   core={bb:prod.ATTACK_CORE_W_ONE_EX*ex[bb]+prod.ATTACK_CORE_W_ONE_ST*st[bb]+prod.ATTACK_CORE_W_ONE_STRAIGHT*os[bb]['straight']+prod.ATTACK_CORE_W_ONE_ORIG_AVG*os[bb]['avg'] for bb in range(2,7)}
   p2,pc2=fin.adjust(b['p2'],b['pc'],core);pair=fin.v299.pair_prob(p2,pc2,prod.TICKET_ALPHA);top=fin.v299.STRATEGIES['HYBRID'](p2,pc2,pair)[:3];tickets=[f'1-{s}-{t}' for s,t in top]
   if len(tickets)!=3 or len(set(tickets))!=3:raise RuntimeError(f'invalid ticket set {code}: {tickets}')
   rr=res.get(code,{});pp=pay.get(code,{});winner=int(float(rr.get('1着_艇番') or 0));combo=str(pp.get('3連単_組番') or '').strip();payout=int(float(pp.get('3連単_払戻金') or 0));hit=combo in tickets
   allout.append({'date':str(target),'race_code':code,'tickets':'|'.join(tickets),'winner':winner,'head1':winner==1,'combo':combo,'payout100':payout,'hit':hit,'stake':300,'return':payout if hit else 0,'final_head_p':b['final_head_p'],'opp_mass':b['opp_mass']})
  v326.update_st(strows,sums,allv)
 a.out_dir.mkdir(parents=True,exist_ok=True);rp=a.out_dir/f'rows_{a.start_day:02d}_{a.end_day:02d}.csv'
 fields=['date','race_code','tickets','winner','head1','combo','payout100','hit','stake','return','final_head_p','opp_mass']
 with rp.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(allout)
 meta={'start_day':a.start_day,'end_day':a.end_day,'rows':len(allout),'production_profile':prod.PROFILE_NAME,'today_20260917_used':False,'chronology_guard':True}
 (a.out_dir/f'meta_{a.start_day:02d}_{a.end_day:02d}.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False))

if __name__=='__main__':main()
