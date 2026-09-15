#!/usr/bin/env python3
"""Wave7: Kiryu(JCD01) boat-2 opponent audit for v351 historical pair population.
Hard excludes September 2026 outcomes. Diagnostic only; production unchanged.
"""
from __future__ import annotations
import pandas as pd

IN='analysis_v351_g2g3_pair_correction_wave3.csv'
OUT='analysis_v351_kiryu_boat2_wave7.csv'

def pairset(x):
    try:return frozenset(int(v) for v in str(x).split('-'))
    except:return frozenset()

def parse_combo(x):
    p=str(x).replace('>','-').replace(' ','').split('-')
    return tuple(map(int,p[:3])) if len(p)>=3 and all(v.isdigit() for v in p[:3]) else None

def parse_tickets(x):
    out=[]
    for q in str(x).replace('|',';').replace(',',';').split(';'):
        c=parse_combo(q)
        if c and c[0]==1:out.append(c)
    return out

def main():
    d=pd.read_csv(IN,dtype={'race_code':str});d.race_code=d.race_code.astype(str).str.zfill(12)
    d=d[(d.race_code.str[:8]<'20260901') & d.race_code.str[8:10].eq('01') & d.schema.eq('half+turn+straight')].copy()
    rows=[]
    for _,r in d.iterrows():
        actual=pairset(r.actual_pair); current=pairset(r.current_first_pair);ts=parse_tickets(r.tickets_raw)
        actual2=2 in actual;current2=2 in current;union2=any(2 in t[1:] for t in ts)
        a=parse_combo(r.actual_combo)
        pos2=(2 if a and a[1]==2 else (3 if a and a[2]==2 else 0))
        # Counterfactual diagnostic: force boat2 into first pair only when absent.
        # Without a ranking rule for which current boat to drop, report oracle rescue ceiling and possible damage exposure separately.
        rows.append({**r.to_dict(),'actual_has_2':int(actual2),'current_has_2':int(current2),'union_has_2':int(union2),
                     'boat2_finish_pos':pos2,'current_pair_hit':int(actual==current),
                     'missed_2_by_first':int(actual2 and not current2),'false_2_in_first':int(current2 and not actual2),
                     'missed_2_by_union':int(actual2 and not union2),'false_2_in_union':int(union2 and not actual2)})
    q=pd.DataFrame(rows).sort_values('race_code');q.to_csv(OUT,index=False,encoding='utf-8-sig')
    n=len(q)
    print('KIRYU_SCHEMA half+turn+straight R',n)
    print('ACTUAL_HAS_2',int(q.actual_has_2.sum()),100*q.actual_has_2.mean() if n else 0)
    print('BOAT2_AS_SECOND',int((q.boat2_finish_pos==2).sum()),'BOAT2_AS_THIRD',int((q.boat2_finish_pos==3).sum()))
    print('CURRENT_HAS_2',int(q.current_has_2.sum()),100*q.current_has_2.mean() if n else 0)
    print('CURRENT_PAIR_HIT',int(q.current_pair_hit.sum()),100*q.current_pair_hit.mean() if n else 0)
    print('MISSED_2_BY_FIRST',int(q.missed_2_by_first.sum()),'FALSE_2_IN_FIRST',int(q.false_2_in_first.sum()))
    print('UNION_HAS_2',int(q.union_has_2.sum()),100*q.union_has_2.mean() if n else 0)
    print('MISSED_2_BY_UNION',int(q.missed_2_by_union.sum()),'FALSE_2_IN_UNION',int(q.false_2_in_union.sum()))
    print('CROSS_FIRST')
    print(pd.crosstab(q.actual_has_2,q.current_has_2,rownames=['actual2'],colnames=['current2']).to_string())
    print('CASES_MISSED_2_FIRST')
    cols=['race_code','actual_combo','current_first_pair','tickets_raw','correction_kind']
    print(q.loc[q.missed_2_by_first.eq(1),cols].to_string(index=False))
    print('SEPTEMBER_OUTCOMES_USED',False)
    print('PRODUCTION_CHANGED',False)
if __name__=='__main__':main()
