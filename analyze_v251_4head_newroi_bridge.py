#!/usr/bin/env python3
"""v251 research bridge: v250 p4head -> walk-forward 4-x-y pair rank -> exact 10k Dutch ROI.

Purpose: answer whether the rebuilt 4-head signal can translate into trifecta hit-rate / realized ROI.
This is NOT production adoption. It deliberately keeps threshold/N as a grid; no winner/result is
used for selection/ranking. Archived target-race odds are used only after ticket freeze for Dutch
settlement, so this does NOT claim historical live/pre-deadline odds availability.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds,round_dutch

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v251_4head_newroi_bridge.csv'
SUM=ROOT/'summary_v251_4head_newroi_bridge.md'
CUTS=(.15,.18,.20,.25,.30,.35,.40)
NS=tuple(range(2,21))
BANK=10000
BOATS=(1,2,3,5,6)

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def pair_orders(rs):
    out={}
    for mon in [f'2026-{m:02d}' for m in range(2,9)]:
        tr=c4.headrows_before(rs,mon)
        if len(tr)<40:continue
        mu,sd=c4.scalers(tr);w2=c4.fit(tr,'second',mu,sd);w3=c4.fit(tr,'third',mu,sd)
        for r in rs:
            if r.get('date','')[:7]!=mon:continue
            # Pair model only requires frozen v93 opponent features. Do not apply the old 4C score gate.
            s2,s3=c4.role_scores(r,w2,w3,mu,sd)
            ps=[(a,b) for a in BOATS for b in BOATS if a!=b]
            ps.sort(key=lambda p:s2[p[0]]+s3[p[1]],reverse=True)
            out[(r.get('date',''),str(r.get('race_code','')).zfill(12))]=ps
    return out

def actual_map(rs):
    d={}
    for r in rs:
        k=(r.get('date',''),str(r.get('race_code','')).zfill(12))
        d[k]=(ii(r.get('winner')),ii(r.get('second')),ii(r.get('third')),ii(r.get('valid_result')))
    return d

def settle(code,tickets,odrow,actual):
    vals=[]
    for t in tickets:
        try:o=float(odrow[t])
        except:return None
        if not np.isfinite(o) or o<=1:return None
        vals.append(o)
    stakes=round_dutch(vals,BANK)
    combo=f'{actual[0]}-{actual[1]}-{actual[2]}'
    ret=0.0;hit=0
    if combo in tickets:
        j=tickets.index(combo)
        if stakes[j]>0: hit=1;ret=float(stakes[j])*vals[j]
    comp=1.0/sum(1.0/x for x in vals)
    return hit,ret,comp

def main():
    p=pd.read_csv(PRED,dtype={'race_code':str});p['race_code']=p.race_code.str.zfill(12)
    rs=c4.read();orders=pair_orders(rs);am=actual_map(rs)
    od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
    frozen=[]
    for _,r in p.iterrows():
        k=(str(r.date),str(r.race_code).zfill(12));order=orders.get(k);a=am.get(k)
        if not order or not a or a[3]!=1 or str(r.race_code) not in oi.index:continue
        o=oi.loc[str(r.race_code)];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        for n in NS:
            ts=[f'4-{x}-{y}' for x,y in order[:n]]
            s=settle(str(r.race_code),ts,o,a)
            if s is None:continue
            hit,ret,comp=s
            frozen.append({'date':r.date,'month':r.month,'race_code':r.race_code,'variant':r.variant,'p4head':r.p4head,'n':n,'hit':hit,'return_yen':ret,'comp_odds':comp,'actual_head4':int(a[0]==4)})
    z=pd.DataFrame(frozen)
    if z.empty:raise RuntimeError('no settled rows')
    detail=[]
    for v in ('PRE','POST'):
      for cut in CUTS:
       for n in NS:
        q=z[(z.variant==v)&(z.n==n)&(z.p4head>=cut)]
        if q.empty:continue
        cost=len(q)*BANK;ret=q.return_yen.sum()
        detail.append({'variant':v,'cut':cut,'n':n,'R':len(q),'head4':int(q.actual_head4.sum()),'trifecta_hits':int(q.hit.sum()),'trifecta_hit_rate_pct':100*q.hit.mean(),'head4_rate_pct':100*q.actual_head4.mean(),'avg_comp_odds':q.comp_odds.mean(),'cost_yen':cost,'return_yen':ret,'profit_yen':ret-cost,'realized_roi_pct':100*ret/cost})
    d=pd.DataFrame(detail);d.to_csv(OUT,index=False)
    # descriptive best by ROI with minimum sample sizes; explicitly model-selection only
    L=['# v251 4-head trifecta / new ROI bridge','',
       '- v250 p4head + monthly prior-only v96-lineage 4-x-y role pair rank + exact 10,000-yen Dutch.','- Dutch: inverse odds, 100-yen Hamilton rounding, exactly 10,000 yen/race; misses are payout 0 / profit -10,000 yen.','- Archived odds are used only after tickets are frozen for settlement. They are not claimed to be live pre-deadline snapshots.','- All Feb-Aug results are historical/model-selection evidence; Jul/Aug are NON-PRISTINE.','- This grid is exploratory and is NOT a frozen production rule.','',
       '## Best descriptive cells (minimum 50 races)','|variant|p4 cut|N|R|4-head rate|3連単 hit|avg comp|cost|return|profit|new ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    good=d[d.R>=50].sort_values(['realized_roi_pct','R'],ascending=[False,False]).head(20)
    for _,r in good.iterrows():L.append(f"|{r.variant}|{r.cut:.2f}|{int(r.n)}|{int(r.R)}|{r.head4_rate_pct:.2f}%|{r.trifecta_hit_rate_pct:.2f}%|{r.avg_comp_odds:.3f}|{r.cost_yen:.0f}|{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.realized_roi_pct:.2f}%|")
    L+=['','## Monthly breakdown of best >=100R cell']
    g100=d[d.R>=100]
    if len(g100):
        b=g100.sort_values('realized_roi_pct',ascending=False).iloc[0]
        L += [f'- descriptive cell: {b.variant}, p4>={b.cut:.2f}, N={int(b.n)}','|month|R|3連単 hit|4-head rate|return|profit|new ROI|','|---|---:|---:|---:|---:|---:|---:|']
        q=z[(z.variant==b.variant)&(z.n==int(b.n))&(z.p4head>=b.cut)]
        for mon,g in q.groupby('month'):
            cost=len(g)*BANK;ret=g.return_yen.sum();L.append(f'|{mon}|{len(g)}|{100*g.hit.mean():.2f}%|{100*g.actual_head4.mean():.2f}%|{ret:.0f}|{ret-cost:+.0f}|{100*ret/cost:.2f}%|')
    L+=['','## Next','- v252 should separate PRE candidate optimization from POST final gate and then search a 4-head-specific odds/TopN rule without copying the 3-head 3.00 / 5-10 rule.','- Any chosen threshold/TopN must be frozen as a new research version before prospective validation.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
