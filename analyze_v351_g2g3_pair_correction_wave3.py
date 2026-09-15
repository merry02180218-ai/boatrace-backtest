#!/usr/bin/env python3
"""Wave3: decompose current v351 G2/G3 ticket-pair errors before correction research.
Historical-only: September 2026 outcomes are hard excluded.
This does not change production; it measures KEEP / REPLACE_ONE / REPLACE_BOTH.
"""
from __future__ import annotations
import pandas as pd

IN='analysis_v351_schema_correct_rebuild.csv'
OUT='analysis_v351_g2g3_pair_correction_wave3.csv'
SUM='analysis_v351_g2g3_pair_correction_wave3_summary.csv'
SCHEMAS={'lap+turn+straight','lap+turn','half+turn+straight','base'}

def combo(x):
    p=str(x).replace('>','-').replace(' ','').split('-')
    return tuple(map(int,p[:3])) if len(p)>=3 and all(v.isdigit() for v in p[:3]) else None

def tickets(x):
    out=[]
    for q in str(x).replace('|',';').replace(',',';').split(';'):
        c=combo(q)
        if c and c[0]==1: out.append(c)
    return out

def main():
    d=pd.read_csv(IN,dtype={'race_code':str}); d.race_code=d.race_code.astype(str).str.zfill(12)
    d=d[(d.race_code.str[:8]<'20260901') & d.schema.isin(SCHEMAS) & d.schema_ready.eq(1)].copy()
    ac=next(c for c in ['actual_combo','actual','result_combo'] if c in d.columns)
    tc=next(c for c in ['tickets','ticket_set','base_tickets'] if c in d.columns)
    rows=[]
    for _,r in d.iterrows():
        a=combo(r[ac]); ts=tickets(r[tc])
        if not a or a[0]!=1 or not ts: continue
        actual=frozenset(a[1:])
        # Current policy emits three ordered tickets. Pair baseline is correct if any emitted ticket contains actual unordered pair.
        pairs=[]
        for t in ts:
            p=frozenset(t[1:])
            if p not in pairs:pairs.append(p)
        pair_hit=actual in pairs
        # For correction diagnosis use the highest-priority/current first ticket pair as the pair to KEEP or replace.
        current=frozenset(ts[0][1:]); common=len(actual & current)
        kind='KEEP' if current==actual else ('REPLACE_ONE' if common==1 else 'REPLACE_BOTH')
        rows.append({'race_code':r.race_code,'date':r.race_code[:8],'schema':r.schema,'actual_combo': '-'.join(map(str,a)),
                     'current_first_pair':'-'.join(map(str,sorted(current))),'actual_pair':'-'.join(map(str,sorted(actual))),
                     'pair_union_hit':int(pair_hit),'correction_kind':kind,'common_boats':common,'ticket_count':len(ts),
                     'tickets_raw':str(r[tc])})
    q=pd.DataFrame(rows).sort_values('race_code');q.to_csv(OUT,index=False,encoding='utf-8-sig')
    s=q.groupby(['schema','correction_kind']).size().rename('R').reset_index()
    totals=q.groupby('schema').size().rename('schema_R').reset_index();s=s.merge(totals,on='schema');s['rate_pct']=100*s.R/s.schema_R
    s.to_csv(SUM,index=False,encoding='utf-8-sig')
    print('DATE_RANGE',q.date.min(),q.date.max(),'R',len(q))
    print('PAIR_UNION_HIT',int(q.pair_union_hit.sum()),100*q.pair_union_hit.mean())
    print('CORRECTION_KIND_TOTAL')
    print(q.correction_kind.value_counts().to_string())
    print('CORRECTION_KIND_SCHEMA')
    print(s.to_string(index=False))
    # rescue ceiling: replacing one boat can only directly rescue REPLACE_ONE; KEEP is the preservation target.
    vc=q.correction_kind.value_counts();keep=int(vc.get('KEEP',0));one=int(vc.get('REPLACE_ONE',0));both=int(vc.get('REPLACE_BOTH',0))
    print('FIRST_PAIR_KEEP',keep,'REPLACE_ONE',one,'REPLACE_BOTH',both,'ONE_RESCUE_CEILING_PCT',100*(keep+one)/len(q))
    print('SEPTEMBER_OUTCOMES_USED',False)
if __name__=='__main__':main()
