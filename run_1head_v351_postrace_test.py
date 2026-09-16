#!/usr/bin/env python3
"""Post-race test replay for v351.
Uses only PRE cache + exhibition fields. Never reads result/payout/odds.
This is explicitly TEST_REPLAY, not a historical LIVE judgment.
"""
import argparse,json,os,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--race-code',required=True);p.add_argument('--cache-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
code=str(a.race_code).zfill(12); base=os.path.join(a.cache_dir,code+'.json')
if not os.path.exists(base): raise SystemExit('race cache missing')
b=json.load(open(base));
if b.get('result_or_payout_used') is not False or not b.get('chronology_guard'): raise SystemExit('unsafe PRE cache')
# This wrapper is intentionally only a marker/guard. Workflow performs acquisition/gate/finalizer.
meta={'mode':'TEST_REPLAY','race_code':code,'result_or_payout_used':False,'odds_used':False,'chronology_guard':True,'note':'post-race execution; input restricted to PRE cache and exhibition only'}
json.dump(meta,open(a.out,'w'),ensure_ascii=False,indent=2);print(json.dumps(meta,ensure_ascii=False))
