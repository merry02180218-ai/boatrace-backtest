#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from collections import Counter
import pandas as pd

import run_v299_1head_trifecta3_policy_search as v299
import run_v312_1head_opponent_outer_gate as v312
import run_v320_1head_exact3_ticket_policy as v320

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v320_1head_exact3_ticket_policy_best_race.csv'
OUT=Path('/tmp/v328'); OUT.mkdir(parents=True,exist_ok=True)


def pct(n,d): return 100.0*n/d if d else float('nan')

def parse_combo(s):
    x=[int(z) for z in str(s).split('-')]
    if len(x)!=3: raise ValueError(s)
    return tuple(x)

def covered_seconds(ticket_str):
    return {int(t.split('-')[1]) for t in str(ticket_str).split(';') if t}

def summarize(g):
    R=len(g); head=int(g.head_hit.sum()); exact=int(g.hit.sum())
    h=g[g.head_hit==1]
    return {
        'R':R,'head_H':head,'head_rate':pct(head,R),'exact3_H':exact,'exact3_rate':pct(exact,R),
        'headwin_R':len(h),
        'second_top1_H':int((h.second_rank==1).sum()),'second_top1_rate_on_head':pct(int((h.second_rank==1).sum()),len(h)),
        'second_top2_H':int((h.second_rank<=2).sum()),'second_top2_rate_on_head':pct(int((h.second_rank<=2).sum()),len(h)),
        'third_top1_H':int((h.third_cond_rank==1).sum()),'third_top1_rate_on_head':pct(int((h.third_cond_rank==1).sum()),len(h)),
        'third_top2_H':int((h.third_cond_rank<=2).sum()),'third_top2_rate_on_head':pct(int((h.third_cond_rank<=2).sum()),len(h)),
        'pair_top3_H':int((h.hybrid_pair_rank<=3).sum()),'pair_top3_rate_on_head':pct(int((h.hybrid_pair_rank<=3).sum()),len(h)),
        'pair_top4_H':int((h.hybrid_pair_rank<=4).sum()),'pair_top4_rate_on_head':pct(int((h.hybrid_pair_rank<=4).sum()),len(h)),
        'pair_top5_H':int((h.hybrid_pair_rank<=5).sum()),'pair_top5_rate_on_head':pct(int((h.hybrid_pair_rank<=5).sum()),len(h)),
        'pair_top6_H':int((h.hybrid_pair_rank<=6).sum()),'pair_top6_rate_on_head':pct(int((h.hybrid_pair_rank<=6).sum()),len(h)),
    }

def main():
    frozen=pd.read_csv(SRC,dtype={'race_code':str})
    frozen.race_code=frozen.race_code.astype(str).str.zfill(12)
    frozen['hit']=pd.to_numeric(frozen.hit,errors='coerce').fillna(0).astype(int)
    frozen['head_hit']=pd.to_numeric(frozen.head_hit,errors='coerce').fillna(0).astype(int)
    if len(frozen)!=345 or int(frozen.head_hit.sum())!=290 or int(frozen.hit.sum())!=139:
        raise AssertionError('frozen identity drift')

    d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
    ids=set(frozen.race_code)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise AssertionError('causal cache identity drift')
    p2,pc=v320.build_factorized(d,p3,p4)

    rows=[]
    for _,r in frozen.iterrows():
        code=r.race_code; month=str(r['month'])
        actual=parse_combo(r.actual_combo)
        a=p2[month][code]; c=pc[month][code]
        prob=v299.pair_prob(a,c,.70)
        order=v299.STRATEGIES['HYBRID'](a,c,prob)
        calc=';'.join(f'1-{s}-{t}' for s,t in order[:3])
        if calc!=str(r.tickets): raise AssertionError(f'ticket identity drift {code}: {calc} != {r.tickets}')
        sec_order=sorted(a,key=lambda b:(-a[b],b))
        sec_rank={b:i+1 for i,b in enumerate(sec_order)}
        pair_rank={pair:i+1 for i,pair in enumerate(order)}
        cs=covered_seconds(r.tickets)
        if int(r.head_hit)==1:
            s,t=actual[1],actual[2]
            thirds=sorted([x for x in a if x!=s],key=lambda x:(-c[(s,x)],x))
            third_rank=thirds.index(t)+1
            hrank=pair_rank[(s,t)]
            srank=sec_rank[s]
            second_covered=s in cs
            if int(r.hit)==1:
                error='HIT'
            elif not second_covered:
                error='HEAD_OK_SECOND_NOT_COVERED'
            else:
                error='HEAD_OK_SECOND_COVERED_THIRD_MISS'
        else:
            s=t=None; third_rank=hrank=srank=None; second_covered=False; error='HEAD_LOSS'
        rows.append({
            'month':month,'race_code':code,'head_hit':int(r.head_hit),'hit':int(r.hit),'actual_combo':r.actual_combo,'tickets':r.tickets,
            'error_class':error,'actual_second':s,'actual_third':t,'second_rank':srank,'third_cond_rank':third_rank,
            'hybrid_pair_rank':hrank,'actual_second_covered_by_3tickets':int(second_covered),
            'covered_second_count':len(cs)
        })
    z=pd.DataFrame(rows)
    z.to_csv(OUT/'v328_ticket_error_races.csv',index=False)

    periods={
        'FEB_APR':z[z.month.isin(['2026-02','2026-03','2026-04'])],
        'MAY':z[z.month.eq('2026-05')],
        'JUN':z[z.month.eq('2026-06')],
        'ALL':z,
    }
    summary=[]
    errrows=[]
    for name,g in periods.items():
        s=summarize(g); s['period']=name; summary.append(s)
        cnt=Counter(g.error_class)
        for cls,n in sorted(cnt.items()):
            errrows.append({'period':name,'error_class':cls,'R':n,'rate_all':pct(n,len(g))})
    sm=pd.DataFrame(summary); er=pd.DataFrame(errrows)
    sm.to_csv(OUT/'v328_period_summary.csv',index=False); er.to_csv(OUT/'v328_error_classes.csv',index=False)

    # Rank-band diagnostics among correct-head races only. These are oracle diagnostics, not promotion rules.
    h=z[z.head_hit==1].copy()
    bands=[]
    for period,g in [('FEB_APR',h[h.month.isin(['2026-02','2026-03','2026-04'])]),('MAY',h[h.month.eq('2026-05')]),('JUN',h[h.month.eq('2026-06')]),('ALL',h)]:
        for lo,hi in [(1,3),(4,4),(5,5),(6,6),(7,10),(11,20)]:
            x=g[(g.hybrid_pair_rank>=lo)&(g.hybrid_pair_rank<=hi)]
            bands.append({'period':period,'rank_band':f'{lo}-{hi}','R':len(x),'rate_on_head':pct(len(x),len(g))})
    pd.DataFrame(bands).to_csv(OUT/'v328_pair_rank_bands.csv',index=False)

    lines=['# v328 ticket-selection error audit','', '- RECONCILE 345 / 290 head / 139 exact3', '- Jul/Aug not inspected; September outcomes unread.','']
    for _,r in sm.iterrows():
        lines += [f"## {r.period}",
                  f"- R={int(r.R)} head={int(r.head_H)} ({r.head_rate:.2f}%) exact3={int(r.exact3_H)} ({r.exact3_rate:.2f}%)",
                  f"- SECOND top1/top2 on head wins: {int(r.second_top1_H)} ({r.second_top1_rate_on_head:.2f}%) / {int(r.second_top2_H)} ({r.second_top2_rate_on_head:.2f}%)",
                  f"- conditional THIRD top1/top2 on head wins: {int(r.third_top1_H)} ({r.third_top1_rate_on_head:.2f}%) / {int(r.third_top2_H)} ({r.third_top2_rate_on_head:.2f}%)",
                  f"- HYBRID ordered-pair oracle coverage top3/top4/top5/top6 on head wins: {int(r.pair_top3_H)} ({r.pair_top3_rate_on_head:.2f}%) / {int(r.pair_top4_H)} ({r.pair_top4_rate_on_head:.2f}%) / {int(r.pair_top5_H)} ({r.pair_top5_rate_on_head:.2f}%) / {int(r.pair_top6_H)} ({r.pair_top6_rate_on_head:.2f}%)",'']
        ee=er[er.period==r.period]
        for _,x in ee.iterrows(): lines.append(f"- error {x.error_class}: {int(x.R)} ({x.rate_all:.2f}% of all selected)")
        lines.append('')
    (OUT/'summary_v328.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
