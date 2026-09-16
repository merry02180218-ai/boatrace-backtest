#!/usr/bin/env python3
"""TEST_REPLAY-only Boatcast exhibition probe.
No deadline guard because execution is post-race. Never reads result/payout/odds.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime,timedelta,timezone
import requests
import run_20260911_3head_v288_live as live3
import run_v326_1head_ticketaware_exhibition as v326
from probe_1head_v351_boatcast_exhibition import ORIG_REQUIRED,AUDIT_KEY
JST=timezone(timedelta(hours=9)); UA={'User-Agent':'Mozilla/5.0'}
def get(url):
 r=requests.get(url,headers=UA,timeout=12);r.raise_for_status();return r.content.decode('utf-8',errors='replace')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--jcd',type=int,required=True);ap.add_argument('--race',type=int,required=True);a=ap.parse_args()
 code=f'{a.date}{a.jcd:02d}{a.race:02d}';jo=f'{a.jcd:02d}';rr=f'{a.race:02d}'
 urls={'tkz':f'https://race.boatcast.jp/hp_txt/{jo}/bc_j_tkz_{a.date}_{jo}_{rr}.txt','stt':f'https://race.boatcast.jp/hp_txt/{jo}/bc_j_stt_{a.date}_{jo}_{rr}.txt','orig':f'https://race.boatcast.jp/txt/{jo}/bc_oriten_{a.date}_{jo}_{rr}.txt'}
 try:
  bodies={k:get(u) for k,u in urls.items()};tkz=live3.parse_tkz(bodies['tkz'],code)[code];stt=live3.parse_stt(bodies['stt'],code)[code];orig=live3.parse_orig(bodies['orig'],code)[code]
  audit=v326.raw_completeness(tkz,stt,orig);req=ORIG_REQUIRED.get(a.jcd,('avg','turn','straight'));keys=['tkz_all6','stt_all6']+[AUDIT_KEY[x] for x in req];ready=all(audit.get(k,False) for k in keys)
  o={'mode':'TEST_REPLAY','race_code':code,'ready':bool(ready),'required_orig':list(req),'required_audit_keys':keys,'audit':audit,'fetched_at_jst':datetime.now(JST).isoformat(),'sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in bodies.items()},'tkz':tkz,'stt':stt,'orig':orig,'result_or_payout_used':False,'odds_used':False,'chronology_guard':True}
  print(json.dumps(o,ensure_ascii=False));return 0 if ready else 3
 except Exception as e:
  print(json.dumps({'mode':'TEST_REPLAY','race_code':code,'ready':False,'error':str(e),'result_or_payout_used':False,'odds_used':False},ensure_ascii=False),file=sys.stderr);return 3
if __name__=='__main__':raise SystemExit(main())
