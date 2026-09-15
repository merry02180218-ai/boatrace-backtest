#!/usr/bin/env python3
"""Fetch only pre-deadline Boatcast exhibition inputs and report v351 readiness.

Readiness is venue-aware: original exhibition metrics are not uniformly
published at all 24 venues. Missing metrics that a venue does not publish must
never turn an otherwise complete pre-deadline probe into ERROR_NO_BET.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timedelta, timezone
import requests
import run_20260911_3head_v288_live as live3
import run_v326_1head_ticketaware_exhibition as v326

JST=timezone(timedelta(hours=9)); UA={'User-Agent':'Mozilla/5.0'}

# 2025-04 venue survey cross-checked against BOAT RACE official material.
# `avg` is the parser's first original-time channel: normally one-lap; at
# Kiryu/Mikuni it carries the venue's half-lap metric. Edogawa/Tsu do not
# publish original exhibition metrics.
ORIG_REQUIRED = {
    1: ('avg','turn','straight'), 2: ('avg','turn','straight'), 3: (),
    4: ('avg','turn','straight'), 5: ('avg','turn','straight'),
    6: ('avg','turn','straight'), 7: ('avg','turn','straight'),
    8: ('avg','turn','straight'), 9: (),
    10: ('avg','turn','straight'), 11: ('avg','turn','straight'),
    12: ('avg','turn'), 13: ('avg','turn'),
    14: ('avg','turn','straight'), 15: ('avg','turn','straight'),
    16: ('avg','turn','straight'), 17: ('avg','turn','straight'),
    18: ('avg','turn'), 19: ('avg','turn','straight'),
    20: ('avg','turn','straight'), 21: ('avg','turn','straight'),
    22: ('avg','turn','straight'), 23: ('avg','turn','straight'),
    24: ('avg','turn','straight'),
}
AUDIT_KEY={'avg':'orig_avg_all6','turn':'orig_turn_all6','straight':'orig_straight_all6'}

def get(url):
    r=requests.get(url,headers=UA,timeout=12);r.raise_for_status();return r.content.decode('utf-8',errors='replace')

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--jcd',type=int,required=True);ap.add_argument('--race',type=int,required=True);ap.add_argument('--deadline-jst',required=True);args=ap.parse_args()
    dl=datetime.fromisoformat(args.deadline_jst);dl=dl.replace(tzinfo=JST) if dl.tzinfo is None else dl.astimezone(JST)
    if datetime.now(JST)>=dl: raise SystemExit('deadline passed before exhibition probe')
    code=f'{args.date}{args.jcd:02d}{args.race:02d}';jo=f'{args.jcd:02d}';rr=f'{args.race:02d}'
    urls={'tkz':f'https://race.boatcast.jp/hp_txt/{jo}/bc_j_tkz_{args.date}_{jo}_{rr}.txt','stt':f'https://race.boatcast.jp/hp_txt/{jo}/bc_j_stt_{args.date}_{jo}_{rr}.txt','orig':f'https://race.boatcast.jp/txt/{jo}/bc_oriten_{args.date}_{jo}_{rr}.txt'}
    try:
        bodies={k:get(u) for k,u in urls.items()};tkz=live3.parse_tkz(bodies['tkz'],code)[code];stt=live3.parse_stt(bodies['stt'],code)[code];orig=live3.parse_orig(bodies['orig'],code)[code]
        audit=v326.raw_completeness(tkz,stt,orig)
        required_orig=ORIG_REQUIRED.get(args.jcd,('avg','turn','straight'))
        required_keys=['tkz_all6','stt_all6']+[AUDIT_KEY[x] for x in required_orig]
        ready=all(audit.get(k,False) for k in required_keys)
        obj={'race_code':code,'ready':bool(ready),'required_orig':list(required_orig),'required_audit_keys':required_keys,'audit':audit,'fetched_at_jst':datetime.now(JST).isoformat(),'sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in bodies.items()},'tkz':tkz,'stt':stt,'orig':orig,'result_or_payout_used':False}
        print(json.dumps(obj,ensure_ascii=False));return 0 if ready else 3
    except Exception as e:
        print(json.dumps({'race_code':code,'ready':False,'error':str(e),'result_or_payout_used':False},ensure_ascii=False),file=sys.stderr);return 3
if __name__=='__main__':raise SystemExit(main())
