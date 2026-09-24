#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

def norm(x):
    s=x.astype(str).str.replace(r'\.0$','',regex=True).str.replace(r'\D','',regex=True)
    return s.str.zfill(12)

core=pd.read_csv('core107/accepted_core_fast_v20.csv',dtype=str)
core['race_code_n']=norm(core['race_code'])
# infer date from explicit date if present, otherwise race code prefix
if 'date' in core.columns:
    core['date_n']=pd.to_datetime(core['date'],errors='coerce')
else:
    core['date_n']=pd.to_datetime(core['race_code_n'].str[:8],format='%Y%m%d',errors='coerce')

# Rebuild candidate universe using same v12 runner helpers, but stop before model fitting.
import sys
sys.path.insert(0,'research'); sys.path.insert(0,'.')
import run_3head_wave20_manual_gate as w20
raw={}
ranges={'jul':('2026-07-01','2026-07-31'),'aug':('2026-08-01','2026-08-31')}
for k,(a,b) in ranges.items():
    x,r,audit=w20.build_pre_enhanced(a,b,True); raw[k]=(x,r)
    print('BUILD',k,len(x),audit)
frames={k:w20.prep_month(x,r) for k,(x,r) in raw.items()}
cand=pd.concat([v.assign(month=k) for k,v in frames.items()],ignore_index=True)
# inspect every plausible identity representation
for col in ['rc','race_code']:
    if col in cand.columns:
        cand[col+'_n']=norm(cand[col])
        print('CAND_SAMPLE',col,cand[[col,col+'_n']].head(10).to_dict('records'))

print('CORE_COLS',list(core.columns))
print('CORE_SAMPLE',core[['race_code','race_code_n','date_n']].head(20).to_dict('records'))
for mon,mnum in [('jul',7),('aug',8)]:
    cc=core[core.date_n.dt.month.eq(mnum)].copy()
    print('CORE_MONTH',mon,'R',len(cc),'sample',cc.race_code_n.head(30).tolist())
    g=cand[cand.month.eq(mon)]
    for col in ['rc_n','race_code_n']:
        if col in g:
            ov=set(cc.race_code_n)&set(g[col])
            print('OVERLAP',mon,col,len(ov),sorted(ov)[:30])
            miss=cc[~cc.race_code_n.isin(set(g[col]))]
            print('MISSING',mon,col,len(miss),miss[['race_code','race_code_n']].head(30).to_dict('records'))
print('IDENTITY_AUDIT_OK')
