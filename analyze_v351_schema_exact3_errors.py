#!/usr/bin/env python3
"""Result-blind-before-race research audit for v351 schema exact3 misses.
Uses historical audit rows only; September 2026 outcomes are hard excluded.
Decomposes HEAD-hit exact3 misses into unordered opponent-pair miss vs order miss.
"""
from __future__ import annotations
import pandas as pd

SRC='analysis_v351_schema_correct_rebuild.csv'
SCHEMAS={'lap+turn+straight','lap+turn','half+turn+straight','base'}

def parse_combo(x):
    s=str(x).replace(' ','').replace('>','-')
    p=s.split('-')
    return tuple(int(v) for v in p[:3]) if len(p)>=3 and all(v.isdigit() for v in p[:3]) else None

def parse_tickets(x):
    out=[]
    for q in str(x).replace('|',';').replace(',',';').split(';'):
        c=parse_combo(q)
        if c and c[0]==1: out.append(c)
    return out

def main():
    d=pd.read_csv(SRC,dtype={'race_code':str}); d['race_code']=d.race_code.astype(str).str.zfill(12)
    d=d[(d.race_code.str[:8]<'20260901') & d.schema.isin(SCHEMAS) & d.schema_ready.eq(1)].copy()
    actual_col=next((c for c in ['actual_combo','actual','result_combo'] if c in d.columns),None)
    ticket_col=next((c for c in ['tickets','ticket_set','base_tickets'] if c in d.columns),None)
    if actual_col is None: raise RuntimeError('actual combo column not found')
    if ticket_col is None:
        # Existing exact3 hit still permits aggregate miss count, but not decomposition.
        raise RuntimeError('ticket column not found; rebuild audit with ticket serialization before decomposition')
    rows=[]
    for _,r in d.iterrows():
        a=parse_combo(r[actual_col]); ts=parse_tickets(r[ticket_col])
        if not a or a[0]!=1 or not ts: continue
        exact=a in ts
        actual_pair=frozenset(a[1:])
        pair_present=any(frozenset(t[1:])==actual_pair for t in ts)
        if exact: kind='EXACT3_HIT'
        elif pair_present: kind='ORDER_MISS'
        else: kind='OPPONENT_PAIR_MISS'
        rows.append({'race_code':r.race_code,'jcd':r.get('jcd'),'schema':r.schema,'actual_combo':'-'.join(map(str,a)),'tickets':';'.join('-'.join(map(str,t)) for t in ts),'error_kind':kind})
    z=pd.DataFrame(rows)
    z.to_csv('analysis_v351_schema_exact3_errors.csv',index=False,encoding='utf-8-sig')
    if z.empty: print('NO_ROWS'); return
    s=z.groupby(['schema','error_kind']).size().rename('R').reset_index()
    s.to_csv('analysis_v351_schema_exact3_error_summary.csv',index=False,encoding='utf-8-sig')
    print(s.to_string(index=False))
if __name__=='__main__': main()
