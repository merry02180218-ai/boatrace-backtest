#!/usr/bin/env python3
"""v217: temporal audit of p3head .30-.35 x higher composite-odds region.

Discovery/diagnostic uses Dec-2025..Jun-2026 only. Jul-Aug are reported only as
already-inspected reference, never used to choose a rule. No production change.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v216_3head_roi_regime_audit.csv'
OUT=ROOT/'analysis_v217_3head_lowp_highcomp_temporal_audit.csv'
SUM=ROOT/'summary_v217_3head_lowp_highcomp_temporal_audit.md'
EARLY=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06']
LATE=['2026-07','2026-08']
TH=[3,4,5,7]

def met(g):
    if g.empty:return (0,0,0,0,0,0)
    c=float(g.cost.sum()); r=float(g.return_yen.sum())
    return len(g),int(g.hit.sum()),100*g.hit.mean(),100*r/c if c else 0,r-c,float(g.composite_odds.mean())

def row(label,g):
    R,h,hr,roi,p,co=met(g)
    return [label,R,h,f'{hr:.1f}%',f'{co:.3f}' if R else '-',f'{roi:.1f}%' if R else '-',f'{p:+.0f}' if R else '-']

def table(L,title,rows):
    L += ['',f'## {title}','|slice|R|hits|hit|avg_comp|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|']
    L += ['|'+'|'.join(map(str,r))+'|' for r in rows]

def main():
    z=pd.read_csv(SRC)
    z=z[(z['lambda']==1.0)&(z.points==10)].copy() if 'lambda' in z.columns else z.copy()
    low=z[(z.p3head>=.30)&(z.p3head<.35)].copy()
    L=['# v217 p3head .30-.35 x composite-odds temporal audit','',
       '- source: v216 annotated fixed v165->v166 lambda=1.00 / Top10 rows',
       '- no PRE/model/threshold/lambda/points change',
       '- Dec-2025..Jun-2026 is the only discovery/temporal-audit window',
       '- Jul-Aug is already inspected and shown only as reference; it is not a validation set for any rule selected here',
       '- stake: 10,000 yen/race Dutch settlement']

    # Month-by-month low-p baseline and thresholds.
    rows=[]
    for m in EARLY:
        g=low[low.month==m]
        rows.append(row(f'{m} all .30-.35',g))
        for t in TH: rows.append(row(f'{m} comp>={t}',g[g.composite_odds>=t]))
    table(L,'Dec-Jun month-by-month',rows)

    # Chronological split: Dec-Feb discovery, Mar-Jun forward check.
    d=low[low.month.isin(EARLY[:3])]; f=low[low.month.isin(EARLY[3:])]
    rows=[]
    for name,g in [('Dec-Feb discovery',d),('Mar-Jun forward',f)]:
        rows.append(row(name,g))
        for t in TH: rows.append(row(f'{name} comp>={t}',g[g.composite_odds>=t]))
    table(L,'Chronological split inside pre-Jul history',rows)

    # Rolling prior-only choice among fixed thresholds: choose best ROI with >=15 races from all prior early months, apply next month.
    roll=[]
    for i in range(1,len(EARLY)):
        train=low[low.month.isin(EARLY[:i])]
        cand=[]
        for t in TH:
            gg=train[train.composite_odds>=t]; R,h,hr,roi,p,co=met(gg)
            if R>=15:cand.append((roi,R,t))
        if not cand: continue
        cand.sort(reverse=True); t=cand[0][2]
        test=low[(low.month==EARLY[i])&(low.composite_odds>=t)]
        R,h,hr,roi,p,co=met(test)
        roll.append({'month':EARLY[i],'chosen_comp':t,'R':R,'hits':h,'hit':hr,'roi':roi,'profit':p,'avg_comp':co})
    rows=[[r['month']+f" chosen>={r['chosen_comp']}",r['R'],r['hits'],f"{r['hit']:.1f}%",f"{r['avg_comp']:.3f}" if r['R'] else '-',f"{r['roi']:.1f}%" if r['R'] else '-',f"{r['profit']:+.0f}" if r['R'] else '-'] for r in roll]
    table(L,'Rolling prior-only threshold selection',rows)
    if roll:
        rr=pd.DataFrame(roll); cost=rr.R.sum()*10000; ret=cost+rr.profit.sum()
        L += ['',f'- rolling aggregate: R={int(rr.R.sum())}, ROI={100*ret/cost:.1f}%, profit={rr.profit.sum():+.0f} yen' if cost else '- rolling aggregate: no races']

    # Already-inspected late reference, all thresholds, explicitly not validation.
    rows=[]
    late=low[low.month.isin(LATE)]
    rows.append(row('Jul-Aug reference all .30-.35',late))
    for t in TH: rows.append(row(f'Jul-Aug reference comp>={t}',late[late.composite_odds>=t]))
    table(L,'Jul-Aug reference only (NOT validation)',rows)

    # Robustness: each threshold early aggregate and leave-one-month-out worst ROI.
    rows=[]
    early=low[low.month.isin(EARLY)]
    for t in TH:
        g=early[early.composite_odds>=t]; R,h,hr,roi,p,co=met(g)
        loo=[]
        for m in EARLY:
            q=g[g.month!=m]; loo.append(met(q)[3] if len(q) else np.nan)
        rows.append([f'comp>={t}',R,h,f'{hr:.1f}%',f'{co:.3f}',f'{roi:.1f}%',f'{p:+.0f} (LOO worst {np.nanmin(loo):.1f}%)'])
    table(L,'Pre-Jul robustness summary',rows)

    low.to_csv(OUT,index=False)
    L += ['','## Interpretation guardrails',
          '- A threshold is not robust merely because aggregate ROI exceeds 100%; month-by-month and forward/rolling behavior must agree.',
          '- Jul-Aug cannot be used as pristine validation because it has already been inspected repeatedly.',
          '- This is a diagnostic audit only. No production rule is adopted automatically.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__':main()
