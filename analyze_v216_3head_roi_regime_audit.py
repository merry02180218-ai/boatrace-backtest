#!/usr/bin/env python3
"""v216: audit why fixed v165->v166 Top10 ROI differs between Dec-Jun and Jul-Aug.

No model/rule retuning. Reads v215 strict-walkforward per-race output and uses only
fixed lambda=1.00 / Top10 rows. Decomposes ROI by p3head/composite-odds bands,
removes largest profitable hits, applies per-race return caps, and reports hit-return concentration.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v215_3head_strict_walkforward_overfit_audit.csv'
OUT=ROOT/'analysis_v216_3head_roi_regime_audit.csv'
SUM=ROOT/'summary_v216_3head_roi_regime_audit.md'

EARLY=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06']
LATE=['2026-07','2026-08']


def metrics(g, retcol='return_yen'):
    if g.empty:return dict(R=0,hits=0,hit=0,cost=0,ret=0,roi=0,profit=0,comp=np.nan,p=np.nan)
    c=float(g.cost.sum()); r=float(g[retcol].sum())
    return dict(R=len(g),hits=int(g.hit.sum()),hit=100*float(g.hit.mean()),cost=c,ret=r,
                roi=100*r/c if c else 0,profit=r-c,comp=float(g.composite_odds.mean()),p=float(g.p3head.mean()))

def add_table(L,title,rows,cols):
    L += ['',f'## {title}','|'+'|'.join(cols)+'|','|'+'|'.join(['---']+['---:']*(len(cols)-1))+'|']
    for row in rows:L.append('|'+'|'.join(str(row[c]) for c in cols)+'|')

def main():
    z=pd.read_csv(SRC)
    b=z[(z['lambda']==1.0)&(z.points==10)].copy()
    b['regime']=np.where(b.month.isin(EARLY),'Dec-Jun',np.where(b.month.isin(LATE),'Jul-Aug','other'))
    b=b[b.regime!='other'].copy()
    b['realized_profit']=b.return_yen-b.cost
    # Hit-only realized gross return, useful for concentration diagnostics.
    bh=b[b.hit==1].copy().sort_values('return_yen',ascending=False)

    L=['# v216 3-head ROI regime audit','',
       '- source: v215 fixed lambda=1.00 / Top10 per-race rows only',
       '- no model, threshold, lambda, point-count, or PRE rule is changed',
       '- comparison: Dec-2025..Jun-2026 vs Jul-Aug 2026',
       '- stake: 10,000 yen/race Dutch settlement from v215 odds series','']

    rows=[]
    for reg in ['Dec-Jun','Jul-Aug']:
        m=metrics(b[b.regime==reg])
        rows.append({'period':reg,'R':m['R'],'hits':m['hits'],'hit':f"{m['hit']:.2f}%",'avg_p3':f"{m['p']:.3f}",'avg_comp':f"{m['comp']:.3f}",'ROI':f"{m['roi']:.1f}%",'profit':f"{m['profit']:+.0f}"})
    add_table(L,'Baseline',rows,['period','R','hits','hit','avg_p3','avg_comp','ROI','profit'])

    # p3head bands, fixed ex ante numeric bins (diagnostic only, not selection proposal)
    pbins=[0.30,0.35,0.40,0.50,1.01]; plabs=['.30-.35','.35-.40','.40-.50','>=.50']
    b['p_band']=pd.cut(b.p3head,bins=pbins,labels=plabs,right=False,include_lowest=True)
    rows=[]
    for reg in ['Dec-Jun','Jul-Aug']:
        for lab in plabs:
            m=metrics(b[(b.regime==reg)&(b.p_band.astype(str)==lab)])
            rows.append({'period':reg,'p3head':lab,'R':m['R'],'hit':f"{m['hit']:.1f}%",'avg_comp':f"{m['comp']:.3f}" if m['R'] else '-','ROI':f"{m['roi']:.1f}%" if m['R'] else '-','profit':f"{m['profit']:+.0f}" if m['R'] else '-'})
    add_table(L,'p3head band decomposition',rows,['period','p3head','R','hit','avg_comp','ROI','profit'])

    # composite odds bands
    cbins=[0,3,4,5,7,999]; clabs=['<3','3-4','4-5','5-7','>=7']
    b['comp_band']=pd.cut(b.composite_odds,bins=cbins,labels=clabs,right=False,include_lowest=True)
    rows=[]
    for reg in ['Dec-Jun','Jul-Aug']:
        for lab in clabs:
            m=metrics(b[(b.regime==reg)&(b.comp_band.astype(str)==lab)])
            rows.append({'period':reg,'comp':lab,'R':m['R'],'hit':f"{m['hit']:.1f}%",'ROI':f"{m['roi']:.1f}%" if m['R'] else '-','profit':f"{m['profit']:+.0f}" if m['R'] else '-'})
    add_table(L,'Composite-odds band decomposition',rows,['period','comp','R','hit','ROI','profit'])

    # Remove top profitable winning races within each regime.
    rows=[]
    for reg in ['Dec-Jun','Jul-Aug']:
        g=b[b.regime==reg].copy()
        wins=g[g.hit==1].sort_values('realized_profit',ascending=False)
        for k in [0,1,3,5,10]:
            drop=set(wins.head(k).race_code.astype(str)) if k else set()
            gg=g[~g.race_code.astype(str).isin(drop)]
            m=metrics(gg)
            rows.append({'period':reg,'drop_top_hits':k,'R':m['R'],'ROI':f"{m['roi']:.1f}%",'profit':f"{m['profit']:+.0f}"})
    add_table(L,'Largest-hit removal stress test',rows,['period','drop_top_hits','R','ROI','profit'])

    # Cap gross return per race, preserving 10k cost.
    rows=[]
    for cap in [20000,30000,50000,100000,200000]:
        for reg in ['Dec-Jun','Jul-Aug']:
            g=b[b.regime==reg].copy(); g['capped_return']=np.minimum(g.return_yen,float(cap))
            m=metrics(g,'capped_return')
            rows.append({'cap':cap,'period':reg,'ROI':f"{m['roi']:.1f}%",'profit':f"{m['profit']:+.0f}"})
    add_table(L,'Per-race gross-return cap stress test',rows,['cap','period','ROI','profit'])

    # Return concentration: share of all gross returns from top N winners.
    rows=[]
    for reg in ['Dec-Jun','Jul-Aug']:
        g=b[b.regime==reg]; total=float(g.return_yen.sum()); wins=g[g.hit==1].sort_values('return_yen',ascending=False)
        for k in [1,3,5,10]:
            s=float(wins.head(k).return_yen.sum()); rows.append({'period':reg,'top_hits':k,'gross_return_share':f"{100*s/total:.1f}%" if total else '-'})
    add_table(L,'Gross-return concentration',rows,['period','top_hits','gross_return_share'])

    # Top Jul-Aug winning races for audit traceability.
    rows=[]
    for _,r in b[(b.regime=='Jul-Aug')&(b.hit==1)].sort_values('return_yen',ascending=False).head(15).iterrows():
        rows.append({'month':r.month,'race_code':r.race_code,'p3head':f"{r.p3head:.3f}",'comp':f"{r.composite_odds:.3f}",'actual':r.actual_combo,'return':f"{r.return_yen:.0f}",'profit':f"{r.realized_profit:+.0f}"})
    add_table(L,'Jul-Aug largest winning races',rows,['month','race_code','p3head','comp','actual','return','profit'])

    # Machine-readable annotated rows.
    b.to_csv(OUT,index=False)
    L += ['','## Interpretation rule','- A late-period ROI that collapses after removing only a few largest hits or under moderate return caps is payout-concentration evidence, not robust model improvement.','- Similar hit rates with materially different ROI and composite-odds mix indicates odds/payout regime is the main driver.','- This audit is diagnostic only; no production rule is adopted from these inspected periods.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__':main()
