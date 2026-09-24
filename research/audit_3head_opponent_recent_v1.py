#!/usr/bin/env python3
from __future__ import annotations
import csv,io,urllib.request
from collections import Counter
import pandas as pd
BASE='https://boatracecsv.github.io/data'

def fetch_results(day):
    u=f"{BASE}/results/realtime/{day:%Y/%m/%d}.csv"
    try:
        with urllib.request.urlopen(u,timeout=30) as r:
            return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
    except Exception as e:
        print('FETCH_FAIL',day.date(),repr(e)); return []

def norm(v):
    s=''.join(c for c in str(v) if c.isdigit())
    return s.zfill(12) if s else ''

core=pd.read_csv('core107/accepted_core_fast_v20.csv',dtype=str)
core['race_code']=core.race_code.map(norm)
core_codes=set(core.race_code)
# v14 union output does not persist race identities, so reconstruct the exact Jul/Aug union by importing its causal builder.
import sys
sys.path.insert(0,'research');sys.path.insert(0,'.')
import run_3head_three_layer_independent_core_v14 as v14
# Instrument by reusing result universe only: analyze all accepted CORE hits plus Jul/Aug 3-winner results;
# exact union membership audit will be added after distribution baseline.
rows=[]
for day in pd.date_range('2026-07-01','2026-08-31'):
    for rr in fetch_results(day):
        rc=norm(rr.get('レースコード',''))
        first=str(rr.get('1着_艇番','')).strip()
        if first!='3': continue
        second=str(rr.get('2着_艇番','')).strip()
        third=str(rr.get('3着_艇番','')).strip()
        if second not in '12456' or third not in '12456': continue
        rows.append({'date':day.date(),'race_code':rc,'second':int(second),'third':int(third),'core':rc in core_codes})
d=pd.DataFrame(rows)
print('RESULT_COL_BASELINE_ROWS',len(d))
for label,g in [('JUL',d[pd.to_datetime(d.date).dt.month.eq(7)]),('AUG',d[pd.to_datetime(d.date).dt.month.eq(8)]),('JUL_AUG',d)]:
    c=Counter(g.second)
    print('SECOND_DIST',label,'N',len(g),dict(sorted(c.items())))
    print('SECOND_RATE',label,{k:round(v/len(g),4) for k,v in sorted(c.items())} if len(g) else {})
    c2=Counter((g.second.astype(str)+'-'+g.third.astype(str)))
    print('ORDER23_TOP',label,c2.most_common(15))
# Exact CORE head-hit second-place distribution is directly available and causal-selection-safe.
ch=d[d.core]
for label,g in [('CORE_JUL',ch[pd.to_datetime(ch.date).dt.month.eq(7)]),('CORE_AUG',ch[pd.to_datetime(ch.date).dt.month.eq(8)]),('CORE_JUL_AUG',ch)]:
    c=Counter(g.second)
    print('CORE_SECOND',label,'N',len(g),dict(sorted(c.items())))
    print('CORE_23',label,Counter((g.second.astype(str)+'-'+g.third.astype(str))).most_common())
print('OPPONENT_BASELINE_OK')
