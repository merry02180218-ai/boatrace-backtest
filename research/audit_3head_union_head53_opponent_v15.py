#!/usr/bin/env python3
from __future__ import annotations
import csv,io,urllib.request,runpy
from collections import Counter
import pandas as pd

# Run exact accepted v14 builder, then read its globals is not sufficient for identities.
# Patch a copy at runtime to persist the exact union/head race codes from local variables.
src=open('research/run_3head_three_layer_independent_core_v14.py',encoding='utf-8').read()
needle='yu=yy[yy.race_code.isin(union)]'
repl=needle+"\n        # audit-only exact identity dump\n        _aud=yu.copy(); _aud['month']=mon; _aud['models']=_aud.race_code.map(lambda rc:'+'.join(membership.get(rc,[]))); detail.extend(_aud[['month','race_code','y','models']].to_dict('records'))"
assert needle in src
src=src.replace(needle,repl,1)
needle2='z=pd.DataFrame(rows);z.to_csv(CSV,index=False)'
repl2=needle2+"\n    pd.DataFrame(detail).to_csv('accepted_union_identity_v15.csv',index=False)"
assert needle2 in src
src=src.replace(needle2,repl2,1)
open('/tmp/v15_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v15_builder.py',run_name='__main__')

ids=pd.read_csv('accepted_union_identity_v15.csv',dtype={'race_code':str})
ids.race_code=ids.race_code.str.zfill(12)
heads=ids[pd.to_numeric(ids.y,errors='coerce').eq(1)].copy()
assert len(heads)==53, f'HEAD53_ASSERT_FAIL {len(heads)}'

BASE='https://boatracecsv.github.io/data'
def fetch(day):
    u=f"{BASE}/results/realtime/{day:%Y/%m/%d}.csv"
    with urllib.request.urlopen(u,timeout=30) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
res={}
for day in pd.date_range('2026-07-01','2026-08-31'):
    try: rows=fetch(day)
    except Exception as e:
        print('FETCH_FAIL',day.date(),repr(e)); continue
    for rr in rows:
        rc=''.join(c for c in str(rr.get('レースコード','')) if c.isdigit()).zfill(12)
        if rc in set(heads.race_code):
            res[rc]=(str(rr.get('2着_艇番','')).strip(),str(rr.get('3着_艇番','')).strip())
heads['second']=heads.race_code.map(lambda x:res.get(x,('',''))[0])
heads['third']=heads.race_code.map(lambda x:res.get(x,('',''))[1])
ok=heads.second.isin(list('12456')) & heads.third.isin(list('12456'))
assert ok.all(), f'RESULT_COVERAGE_FAIL missing={heads.loc[~ok,"race_code"].tolist()}'
heads.second=heads.second.astype(int);heads.third=heads.third.astype(int)
heads.to_csv('accepted_union_head53_opponents_v15.csv',index=False)

for label,g in [('JUL',heads[heads.month.eq('jul')]),('AUG',heads[heads.month.eq('aug')]),('ALL',heads)]:
    c=Counter(g.second); n=len(g)
    print('UNION_SECOND',label,'N',n,dict(sorted(c.items())))
    print('UNION_RATE',label,{k:round(v/n,4) for k,v in sorted(c.items())})
    print('UNION_23',label,Counter(zip(g.second,g.third)).most_common())
print('UNION_HEAD53_OPPONENT_OK')
