#!/usr/bin/env python3
"""Fast NON-PRISTINE 2026-09-10 two-race integration smoke test.

Speedups vs smoke_20260910_3head_live_bridge.py:
- reuse the frozen v234 restored-Waku10 artifact instead of reconstructing it;
- parallelize and day-index v224 national-form decomposition instead of O(days*races);
- keep the same target-day result blind protections and canonical v221/v242/v243 logic.
"""
from __future__ import annotations
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd

import smoke_20260910_3head_live_bridge as slow
import analyze_v224_3head_national_form_decompose as v224
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v234_3head_waku10_restored_replay as v234


def cached_reconstruct():
    """Require/downloaded canonical v234 restored tree; never rebuild it here."""
    cov=v234.COV
    if not cov.exists():
        raise RuntimeError(f'cached v234 coverage missing: {cov}; workflow must download artifact first')
    q=pd.read_csv(cov)
    if (q.source=='missing').any():
        raise RuntimeError('cached v234 artifact contains missing Waku10 days')
    # Spot-check the restored tree itself, not just coverage metadata.
    probe=v234.REST/'2026/08/31.csv'
    if not probe.exists():
        raise RuntimeError(f'cached restored Waku10 tree missing probe: {probe}')
    print(f'FAST_CACHE v234 coverage rows={len(q)} restored_probe={probe}')
    return q


def fast_add_decomp(d,dc):
    """Exact v224 feature formulas, but fetch days in parallel and avoid all-code scan per day."""
    byday=defaultdict(dict)
    for ix,r in d.iterrows():
        dt=pd.to_datetime(r[dc],errors='coerce')
        if pd.isna(dt) or dt>=v224.CONTAM:
            continue
        day=dt.date()
        code=str(r.get('race_code','')).zfill(12)
        byday[day].setdefault(code,[]).append(ix)

    def fetch(day):
        y=day.strftime('%Y/%m/%d')
        return day,v223.bycode(v223.rows(f'data/programs/recent_national/{y}.csv'))

    fetched={}
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs=[ex.submit(fetch,day) for day in byday]
        for n,f in enumerate(as_completed(fs),1):
            day,m=f.result(); fetched[day]=m
            if n%50==0: print('fast national days',n,'/',len(fs),flush=True)

    exrows={}
    for day,codes in byday.items():
        m=fetched.get(day,{})
        for code,ixes in codes.items():
            r=m.get(code,{})
            q={}
            for b in range(1,7):
                meets=[v224.places(r.get(f'艇{b}_前{k}節_着順列')) for k in range(1,6)]
                m1=v224.met(meets[0]);m2=v224.met(meets[1]);m12=v224.met(meets[0]+meets[1]);m35=v224.met(meets[2]+meets[3]+meets[4]);mall=v224.met(sum(meets,[]))
                for tag,z in [('m1',m1),('m2',m2),('m12',m12),('m35',m35),('all',mall)]:
                    for k,val in z.items(): q[f'f_b{b}_{tag}_{k}']=val
                q[f'f_b{b}_trend_mean']=(m35['mean']-m12['mean']) if np.isfinite(m35['mean']) and np.isfinite(m12['mean']) else np.nan
                q[f'f_b{b}_trend_win']=(m12['win']-m35['win']) if np.isfinite(m35['win']) and np.isfinite(m12['win']) else np.nan
                q[f'f_b{b}_trend_top2']=(m12['top2']-m35['top2']) if np.isfinite(m35['top2']) and np.isfinite(m12['top2']) else np.nan
                ends=[]; gs=[]
                for k in range(1,6):
                    ed=pd.to_datetime(r.get(f'艇{b}_前{k}節_終了日'),errors='coerce')
                    if pd.notna(ed): ends.append(max(0,(pd.Timestamp(day)-ed).days))
                    zz=v224.grade_score(r.get(f'艇{b}_前{k}節_グレード'))
                    if np.isfinite(zz): gs.append(zz)
                q[f'f_b{b}_layoff']=min(ends) if ends else np.nan
                q[f'f_b{b}_grade']=np.mean(gs) if gs else np.nan
                q[f'f_b{b}_m1_grade']=v224.grade_score(r.get(f'艇{b}_前1節_グレード'))
            for metric in ['m1_win','m1_top2','m12_win','m12_top2','trend_win','trend_top2','all_win','all_top2']:
                vv=q.get(f'f_b3_{metric}',np.nan)
                ins=[q.get(f'f_b1_{metric}',np.nan),q.get(f'f_b2_{metric}',np.nan)]
                outs=[q.get(f'f_b{b}_{metric}',np.nan) for b in [4,5,6]]
                ins=[x for x in ins if np.isfinite(x)]; outs=[x for x in outs if np.isfinite(x)]
                q[f'f_rel_in_{metric}']=vv-max(ins) if np.isfinite(vv) and ins else np.nan
                q[f'f_rel_out_{metric}']=vv-max(outs) if np.isfinite(vv) and outs else np.nan
            for ix in ixes: exrows[ix]=q
    return d.join(pd.DataFrame.from_dict(exrows,orient='index'),how='left')


def main():
    v234.reconstruct=cached_reconstruct
    v224.add_decomp=fast_add_decomp
    slow.v224.add_decomp=fast_add_decomp
    slow.main()

if __name__=='__main__':
    main()
