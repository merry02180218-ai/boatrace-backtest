#!/usr/bin/env python3
"""v199: stability check for 3-head turn_margin candidates before Jul/Aug.

Reuses freeze-complete strict walk-forward predictions from v198.
No model refit, no threshold search. Compare production baseline against only the
predeclared candidate cuts -0.2 and 0.0 over 2025-12..2026-06, with early/late,
monthly and venue(JCD) breakdowns. Descriptive only; not a production gate.
"""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v198_3head_long_history_base.csv'
CUTS=[None,-0.2,0.0]
PRE_END='2026-07'


def met(g):
    if len(g)==0:return dict(R=0,head=0.,hit=0.,cov=0.,cost=0.,ret=0.,roi=0.)
    h=g[g.y3head==1]
    s=g[g.valid_payout==1]
    cost=float(s.cost_yen.sum()); ret=float(s.return_yen.sum())
    return dict(R=len(g),head=100*g.y3head.mean(),hit=100*g.hit.mean(),
                cov=100*h.hit.mean() if len(h) else 0.,cost=cost,ret=ret,
                roi=100*ret/cost if cost else 0.)

def apply(g,cut):
    if cut is None:return g.copy()
    x=pd.to_numeric(g.turn_margin23,errors='coerce')
    return g[x>=cut].copy()

def label(c): return 'BASE' if c is None else f'turn>={c:.1f}'

def line(name,c,g):
    m=met(apply(g,c))
    return f"|{name}|{label(c)}|{m['R']}|{m['head']:.2f}%|{m['hit']:.2f}%|{m['cov']:.2f}%|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|"

def main():
    d=pd.read_csv(SRC,dtype={'race_code':str})
    d=d[d.month.astype(str)<PRE_END].copy()
    d['race_code']=d.race_code.astype(str).str.zfill(12)
    d['jcd']=d.race_code.str.slice(8,10)
    d['era']=d.month.map(lambda x:'EARLY 2025-12..2026-02' if str(x)<='2026-02' else 'LATE 2026-03..2026-06')

    L=['# v199 3号艇 PRE-Jul stability check','',
       '- source: v198 strict walk-forward frozen predictions',
       '- evaluation window: 2025-12 .. 2026-06 only (Jul/Aug excluded)',
       '- production baseline is unchanged: v165 p3>=.30 -> v166 lambda1 -> Top10',
       '- candidate turn cuts are predeclared only: -0.2 and 0.0',
       '- this analysis is descriptive/stability evidence, NOT a production adoption test',
       '', '## Early / late split',
       '|segment|rule|R|3-head|hit|Top10 cov|cost|return|ROI|',
       '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for era in ['EARLY 2025-12..2026-02','LATE 2026-03..2026-06']:
        g=d[d.era==era]
        for c in CUTS:L.append(line(era,c,g))

    L += ['','## Month-by-month','|month|rule|R|3-head|hit|Top10 cov|cost|return|ROI|',
          '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for mon in sorted(d.month.astype(str).unique()):
        g=d[d.month.astype(str)==mon]
        for c in CUTS:L.append(line(mon,c,g))

    L += ['','## Venue/JCD stability','',
          'Sorted by BASE race count. Small samples are shown but must not be treated as adoption evidence.',
          '', '|JCD|rule|R|3-head|hit|Top10 cov|cost|return|ROI|',
          '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    order=d.groupby('jcd').size().sort_values(ascending=False).index
    venue_rows=[]
    for j in order:
        g=d[d.jcd==j]
        for c in CUTS:
            m=met(apply(g,c)); venue_rows.append({'jcd':j,'rule':label(c),**m})
            L.append(line(j,c,g))

    # Compact CSV for downstream comparisons.
    rows=[]
    for scope,groups in [('era',[(e,d[d.era==e]) for e in d.era.unique()]),
                         ('month',[(m,d[d.month.astype(str)==m]) for m in sorted(d.month.astype(str).unique())]),
                         ('jcd',[(j,d[d.jcd==j]) for j in order])]:
        for key,g in groups:
            for c in CUTS: rows.append({'scope':scope,'key':key,'rule':label(c),**met(apply(g,c))})
    pd.DataFrame(rows).to_csv(ROOT/'analysis_v199_3head_prejul_stability.csv',index=False)
    (ROOT/'summary_v199_3head_prejul_stability.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__':main()
