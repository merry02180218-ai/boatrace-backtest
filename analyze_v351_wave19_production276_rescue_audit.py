#!/usr/bin/env python3
"""Wave19: apply frozen Wave17/18 rescue to current production 276R only."""
from __future__ import annotations
import numpy as np
import pandas as pd
import analyze_v351_mass_rescue_wave17_boat5_third_rescue as w17


def main():
    base=pd.read_csv(w17.SRC,dtype={'race_code':str})
    base.race_code=base.race_code.astype(str).str.zfill(12)
    if (base.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
    # Current production opponent cutoff is .375. Keep current production schemas.
    base=base[(base.opp_mass>=.375)&base.schema.isin(w17.SCHEMAS)].copy()
    feat=w17.build_pre_result_strength(base)
    d=w17.make_rows(base,feat)
    d=d[d.race_code.str[:8]<'20260901'].copy()
    if (d.race_code.str[:8]>='20260901').any(): raise RuntimeError('September evaluated row detected')
    # HEAD production eligibility must already be represented by Wave10 source rows.
    # Audit exact current population count to prevent silently testing a different population.
    if len(d)!=276:
        raise RuntimeError(f'production population drift: expected 276R, got {len(d)}')
    # Frozen Wave17/18 policy: only BOAT3_STRONGER eligible; SECOND=3; replace slot2 (1-indexed).
    q=w17.eval_policy(d,3,1)
    q['month']=q.race_code.str[:6]
    q['strength_bucket']=pd.cut(q.strength2_minus3,[-np.inf,.75,1.0,1.5,np.inf],right=False).astype(str)
    q.to_csv('analysis_v351_wave19_production276_rows.csv',index=False,encoding='utf-8-sig')
    def s(scope,key,g):
        return dict(scope=scope,key=str(key),R=len(g),baseline_hits=int(g.baseline_hit.sum()),fixed3_hits=int(g.fixed3_hit.sum()),rescues=int(g.fixed3_rescue.sum()),damages=int(g.fixed3_damage.sum()),net=int(g.fixed3_rescue.sum()-g.fixed3_damage.sum()),overrides=int(g.fixed3_override.sum()))
    out=[s('all','276R',q)]
    for m,g in q.groupby('month'): out.append(s('month',m,g))
    for j,g in q.groupby('jcd'): out.append(s('jcd',j,g))
    for z,g in q.groupby('schema'): out.append(s('schema',z,g))
    for b,g in q.groupby('strength_bucket',observed=True): out.append(s('strength_bucket',b,g))
    sm=pd.DataFrame(out); sm.to_csv('analysis_v351_wave19_production276_summary.csv',index=False,encoding='utf-8-sig')
    print('SEPTEMBER_OUTCOMES_USED False')
    print('PRODUCTION_CHANGED False')
    print('POPULATION',len(q))
    print(sm.to_string(index=False))
if __name__=='__main__': main()
