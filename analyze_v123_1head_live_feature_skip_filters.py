"""v123: test simple exhibition-feature skip gates inside frozen v121 PRE-top5 operation.

Design:
- PRE watch list is exactly the v121 PRE-top5 selection. No new race picking after exhibition.
- Baseline LIVE BUY is v121 p109>=72% and course1.
- Candidate skip gates use only current LIVE/exhibition-derived fields already frozen in v108.
- Discovery/tuning on Mar-May only. Freeze one simple gate. Evaluate once on clean Jun-Aug.
- No odds. No result/payout in the gate.
"""
import csv
from collections import defaultdict

SRC_DETAIL='analysis_v121_1head_six_month_top5.csv'
SRC_FULL='analysis_v108_1head_feasibility.csv'
OUT='summary_v123_1head_live_feature_skip_filters.md'

DEV={'2026-03','2026-04','2026-05'}
HOLD={'2026-06','2026-07','2026-08'}

# LIVE features where larger is interpreted as better for boat1 / safer.
FEATURES=[
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23'
]


def f(x):
    try:return float(x)
    except:return 0.0


def i(x):
    try:return int(float(x))
    except:return 0


def pct(a,b):return 100*a/b if b else 0.0


def read(path):
    with open(path,encoding='utf-8-sig',newline='') as z:return list(csv.DictReader(z))


def metric(rs):
    n=len(rs); h=sum(i(r.get('head_hit')) for r in rs)
    hits=[r for r in rs if 0<i(r.get('rank_l50'))<=7]
    inv=n*700; ret=sum(i(r.get('payout100')) for r in hits)
    return {'n':n,'head':pct(h,n),'hit':pct(len(hits),n),'roi':pct(ret,inv)}


def quantile(vals,q):
    a=sorted(vals)
    if not a:return 0.0
    x=(len(a)-1)*q; lo=int(x); hi=min(lo+1,len(a)-1); w=x-lo
    return a[lo]*(1-w)+a[hi]*w


def apply(rows,feat,thr):
    return [r for r in rows if f(r.get(feat))>=thr]


def main():
    det=read(SRC_DETAIL); full=read(SRC_FULL)
    key={(r.get('date'),r.get('race_code')):r for r in full}
    rows=[]
    for d in det:
        if i(d.get('live_buy'))!=1:continue
        r=dict(key.get((d.get('date'),d.get('race_code')),{}) )
        if not r:continue
        r.update({k:d.get(k,'') for k in ['date','month','race_code','head_hit','rank_l50','payout100','p109_live','entry_course']})
        rows.append(r)
    dev=[r for r in rows if r.get('month') in DEV]
    hold=[r for r in rows if r.get('month') in HOLD]
    baseD=metric(dev); baseH=metric(hold)

    qs=[.05,.10,.15,.20,.25,.30,.35,.40]
    candidates=[]
    for feat in FEATURES:
        vals=[f(r.get(feat)) for r in dev]
        for q in qs:
            thr=quantile(vals,q)
            md=metric(apply(dev,feat,thr))
            kept=md['n']/baseD['n'] if baseD['n'] else 0
            candidates.append({'feat':feat,'q':q,'thr':thr,'m':md,'kept':kept})

    eligible=[c for c in candidates if c['kept']>=.60 and c['m']['roi']>=baseD['roi'] and c['m']['hit']>=baseD['hit']]
    chosen=max(eligible,key=lambda c:(c['m']['roi']-baseD['roi'],c['m']['hit']-baseD['hit'],c['m']['n'],-c['q'])) if eligible else None

    L=['# v123 1-head LIVE exhibition-feature skip validation','',
       '- Frozen PRE operation: **v121 PRE top5/day**. No race is added after exhibition.',
       '- Baseline LIVE BUY: v121 p109>=72% and boat1 course1.',
       '- Discovery: Mar-May only. Clean one-shot evaluation: Jun-Aug.',
       '- Candidate gates use only LIVE/exhibition features; no odds/result/payout in filtering.','',
       '## Baseline','|period|R|①頭率|7点的中率|7点ROI|','|---|---:|---:|---:|---:|',
       f'|Mar-May dev|{baseD["n"]}|{baseD["head"]:.1f}%|{baseD["hit"]:.1f}%|{baseD["roi"]:.1f}%|',
       f'|Jun-Aug holdout|{baseH["n"]}|{baseH["head"]:.1f}%|{baseH["hit"]:.1f}%|{baseH["roi"]:.1f}%|','',
       '## Development search top candidates','|feature|skip lower tail|threshold|R|①頭率|7点的中率|7点ROI|','|---|---:|---:|---:|---:|---:|---:|']
    top=sorted(candidates,key=lambda c:(c['m']['roi']-baseD['roi'],c['m']['hit']-baseD['hit']),reverse=True)[:20]
    for c in top:
        m=c['m']; L.append(f'|{c["feat"]}|{c["q"]*100:.0f}%|{c["thr"]:.5f}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["roi"]:.1f}%|')

    if chosen:
        chD=chosen['m']; chH=metric(apply(hold,chosen['feat'],chosen['thr']))
        L+=['', '## Frozen selected gate',
            f'- **Keep only {chosen["feat"]} >= {chosen["thr"]:.5f}** (development lower-tail skip {chosen["q"]*100:.0f}%).',
            f'- Dev: {chD["n"]}R / ①頭 {chD["head"]:.1f}% / hit {chD["hit"]:.1f}% / ROI {chD["roi"]:.1f}%.','',
            '## Clean Jun-Aug holdout result','|rule|R|①頭率|7点的中率|7点ROI|','|---|---:|---:|---:|---:|',
            f'|baseline|{baseH["n"]}|{baseH["head"]:.1f}%|{baseH["hit"]:.1f}%|{baseH["roi"]:.1f}%|',
            f'|v123 frozen gate|{chH["n"]}|{chH["head"]:.1f}%|{chH["hit"]:.1f}%|{chH["roi"]:.1f}%|','',
            '## Decision rule',
            '- PASS only if Jun-Aug ROI improves AND hit rate does not worsen. Otherwise FAIL; do not adopt.',
            f'- **V123 = {"PASS" if chH["roi"]>baseH["roi"] and chH["hit"]>=baseH["hit"] else "FAIL"}**']
    else:
        L+=['','## Result','- No development gate met the conservative selection requirements.','- **V123 = FAIL**']
    L+=['','## Guardrail','- This is still one-dimensional filtering to reduce overfit risk. If FAIL, do not start combinatorial feature mining on the same holdout. Move to prospective Sep validation or a new untouched time block.']
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
