#!/usr/bin/env python3
"""v200: robustness diagnostics for the predeclared 3-head turn>=-0.2 candidate.

Uses v198 frozen strict walk-forward predictions only. Evaluation is PRE-Jul (2025-12..2026-06).
This is robustness/diagnostic evidence, not a production adoption test.
"""
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v198_3head_long_history_base.csv'
CUT=-0.2
CAPS=[3000,5000,10000]

def metrics(g, ret_col='return_yen'):
    s=g[g.valid_payout==1].copy(); cost=s.cost_yen.sum(); ret=s[ret_col].sum()
    h=g[g.y3head==1]
    return dict(R=len(g), head=100*g.y3head.mean() if len(g) else 0, hit=100*g.hit.mean() if len(g) else 0,
                cov=100*h.hit.mean() if len(h) else 0, cost=cost, ret=ret, roi=100*ret/cost if cost else 0)

def fmt(label,g,ret_col='return_yen'):
    m=metrics(g,ret_col); return f"|{label}|{m['R']}|{m['head']:.2f}%|{m['hit']:.2f}%|{m['cov']:.2f}%|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|"

def streak_and_dd(g):
    s=g[g.valid_payout==1].sort_values(['date','race_code']).copy()
    longest=cur=0; eq=peak=maxdd=0.; dd_start=dd_end=''
    peak_label=''
    for _,r in s.iterrows():
        if int(r.hit)==0: cur+=1; longest=max(longest,cur)
        else: cur=0
        eq += float(r.return_yen)-float(r.cost_yen)
        label=f"{r.date}/{r.race_code}"
        if eq>peak: peak=eq; peak_label=label
        dd=peak-eq
        if dd>maxdd: maxdd=dd; dd_start=peak_label or 'start'; dd_end=label
    return longest,maxdd,dd_start,dd_end,eq

def leave_one_hit_out(g):
    s=g[g.valid_payout==1].copy(); hits=s[s.return_yen>0].copy()
    vals=[]
    for ix,r in hits.iterrows():
        q=s.drop(ix); c=q.cost_yen.sum(); ret=q.return_yen.sum(); vals.append((100*ret/c if c else 0,r.date,r.race_code,r.return_yen))
    return sorted(vals)

def main():
    d=pd.read_csv(SRC); d=d[(d.month>='2025-12')&(d.month<='2026-06')].copy()
    g=d[pd.to_numeric(d.turn_margin23,errors='coerce')>=CUT].copy()
    # capped-return sensitivity: cap payout return on a winning race, zero otherwise
    for cap in CAPS:
        g[f'ret_cap_{cap}']=np.where(g.return_yen>0,np.minimum(g.return_yen,cap),0.)
    L=['# v200 3号艇 turn>=-0.2 robustness diagnostics','',
       '- source: v198 strict walk-forward frozen predictions',
       '- window: 2025-12 .. 2026-06 only (Jul/Aug excluded)',
       '- candidate: turn_margin23 >= -0.2 (predeclared in v199)',
       '- production remains unchanged; this is NOT an adoption test','',
       '## Overall','|rule|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|',fmt('BASE',d),fmt('turn>=-0.2',g),'',
       '## Payout-cap sensitivity','|cap per hit|R|cost|capped return|ROI|','|---:|---:|---:|---:|---:|']
    for cap in CAPS:
        m=metrics(g,f'ret_cap_{cap}'); L.append(f"|{cap}|{m['R']}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|")
    loo=leave_one_hit_out(g)
    L += ['','## Leave-one-winning-hit-out sensitivity','|case|ROI|removed date|race|removed return|','|---|---:|---|---|---:|']
    if loo:
        worst=loo[0]; best=loo[-1]
        L.append(f'|worst remaining ROI|{worst[0]:.1f}%|{worst[1]}|{worst[2]}|{worst[3]:.0f}|')
        L.append(f'|best remaining ROI|{best[0]:.1f}%|{best[1]}|{best[2]}|{best[3]:.0f}|')
        # top five most influential hits by removed return
        top=sorted(loo,key=lambda x:x[3],reverse=True)[:5]
        L += ['','### Five largest winning returns','|date|race|return|ROI after removal|','|---|---|---:|---:|']
        for roi,dt,rc,ret in top:L.append(f'|{dt}|{rc}|{ret:.0f}|{roi:.1f}%|')
    L += ['','## Monthly ROI distribution','|month|R|ROI|','|---|---:|---:|']
    rois=[]
    for mon in sorted(g.month.unique()):
        m=metrics(g[g.month==mon]); rois.append(m['roi']); L.append(f"|{mon}|{m['R']}|{m['roi']:.1f}%|")
    L += ['',f'- monthly median ROI: {np.median(rois):.1f}%',f'- months ROI >=100%: {sum(x>=100 for x in rois)}/{len(rois)}',f'- months ROI >=80%: {sum(x>=80 for x in rois)}/{len(rois)}']
    longest,maxdd,ds,de,profit=streak_and_dd(g)
    L += ['','## Sequence risk',f'- longest losing streak: {longest} settled races',f'- max drawdown (100 yen x Top10 accounting): {maxdd:.0f} yen',f'- max drawdown span: {ds} -> {de}',f'- ending cumulative profit: {profit:.0f} yen']
    (ROOT/'summary_v200_3head_turn_robustness.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__':main()
