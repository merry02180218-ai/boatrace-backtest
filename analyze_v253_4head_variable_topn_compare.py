#!/usr/bin/env python3
"""v253 research: compare 4-head ticket rules under the same POST p4 gate.

Rules compared per race after POST gate:
A FIXED2: top 2 pair tickets.
B FLOOR3_5TO10: among TopN N=5..10, choose the composite odds closest to 3.00 from ABOVE (>=3.00); if none, NO BET.
C COPY3HEAD: evaluate raw N=2..20, choose composite odds closest to 3.00; raw N<5 => NO BET, raw N 5..10 => buy raw N, raw N>10 => buy Top10.

All settlement uses exact 10,000-yen inverse-odds Dutch with 100-yen Hamilton rounding.
This is historical/model-selection research only. Jul/Aug are NON-PRISTINE.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v253_4head_variable_topn_compare.csv'
DETAIL=ROOT/'analysis_v253_4head_variable_topn_detail.csv'
SUM=ROOT/'summary_v253_4head_variable_topn_compare.md'
BANK=10000
POST_CUTS=(.25,.28,.30,.32,.35,.38,.40)
TARGET=3.0

def comp_for(ts,o):
    vals=[]
    for t in ts:
        try:x=float(o[t])
        except:return None
        if not np.isfinite(x) or x<=1:return None
        vals.append(x)
    return 1.0/sum(1.0/x for x in vals)

def choose_rule(rule, order, o):
    all_ts=[f'4-{a}-{b}' for a,b in order]
    if rule=='FIXED2': return all_ts[:2],2,2
    comps={}
    for n in range(2,21):
        c=comp_for(all_ts[:n],o)
        if c is not None: comps[n]=c
    if not comps:return None,None,None
    if rule=='FLOOR3_5TO10':
        cand=[n for n in range(5,11) if n in comps and comps[n]>=TARGET]
        if not cand:return None,None,None
        n=min(cand,key=lambda k:(comps[k]-TARGET,k))
        return all_ts[:n],n,n
    if rule=='COPY3HEAD':
        raw=min(comps,key=lambda k:(abs(comps[k]-TARGET),k))
        if raw<5:return None,raw,None
        buy=min(raw,10)
        return all_ts[:buy],raw,buy
    raise ValueError(rule)

def main():
    p=pd.read_csv(PRED,dtype={'race_code':str});p['race_code']=p.race_code.str.zfill(12)
    p=p[p.variant=='POST'].copy()
    rs=c4.read();orders=v251.pair_orders(rs);am=v251.actual_map(rs)
    od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
    base=[]
    for _,r in p.iterrows():
        code=str(r.race_code).zfill(12);k=(str(r.date),code);order=orders.get(k);a=am.get(k)
        if not order or not a or a[3]!=1 or code not in oi.index:continue
        o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        base.append((r,code,order,a,o))
    details=[]
    for cut in POST_CUTS:
      for r,code,order,a,o in base:
        if float(r.p4head)<cut:continue
        for rule in ('FIXED2','FLOOR3_5TO10','COPY3HEAD'):
            ts,raw_n,buy_n=choose_rule(rule,order,o)
            if not ts:continue
            s=v251.settle(code,ts,o,a)
            if s is None:continue
            hit,ret,comp=s
            details.append({'post_cut':cut,'rule':rule,'date':r.date,'month':r.month,'race_code':code,'p4head':r.p4head,'raw_n':raw_n,'buy_n':buy_n,'comp_odds':comp,'hit':hit,'return_yen':ret,'profit_yen':ret-BANK,'head4':int(a[0]==4)})
    z=pd.DataFrame(details);z.to_csv(DETAIL,index=False)
    rows=[]
    for (cut,rule),g in z.groupby(['post_cut','rule']):
        cost=len(g)*BANK;ret=g.return_yen.sum();pre6=g[g.month<='2026-06'];c6=len(pre6)*BANK;r6=pre6.return_yen.sum()
        rows.append({'post_cut':cut,'rule':rule,'R':len(g),'head4_rate_pct':100*g.head4.mean(),'trifecta_hits':int(g.hit.sum()),'trifecta_hit_rate_pct':100*g.hit.mean(),'avg_buy_n':g.buy_n.mean(),'avg_comp_odds':g.comp_odds.mean(),'cost_yen':cost,'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,'feb_jun_R':len(pre6),'feb_jun_hit_pct':100*pre6.hit.mean() if len(pre6) else np.nan,'feb_jun_roi_pct':100*r6/c6 if c6 else np.nan})
    d=pd.DataFrame(rows).sort_values(['post_cut','rule']);d.to_csv(OUT,index=False)
    L=['# v253 4-head variable TopN direct comparison','',
       '- FIXED2 = 上位2点固定。','- FLOOR3_5TO10 = 5〜10点の中で合成オッズ3.00以上を満たし、3.00に最も近い点数。満たさなければNO BET。','- COPY3HEAD = 2〜20点で合成オッズ3.00に最も近いraw Nを選び、raw<5 NO BET / 5〜10そのまま / >10 Top10。','- 全て1R10,000円、inverse-odds Dutch、100円Hamilton。外れは払戻0 / -10,000円。','- archived oddsはticket freeze後のsettlementにのみ利用し、live pre-deadline oddsとは呼ばない。','- Feb-Augはmodel-selection evidence、Jul/AugはNON-PRISTINE。','',
       '## Comparison','|POST p4|rule|R|4-head|3連単 hit|avg N|avg comp|profit|ROI|Feb-Jun R|Feb-Jun hit|Feb-Jun ROI|','|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in d.iterrows():
        L.append(f'|{r.post_cut:.2f}|{r.rule}|{int(r.R)}|{r.head4_rate_pct:.2f}%|{r.trifecta_hit_rate_pct:.2f}%|{r.avg_buy_n:.2f}|{r.avg_comp_odds:.3f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{int(r.feb_jun_R)}|{r.feb_jun_hit_pct:.2f}%|{r.feb_jun_roi_pct:.2f}%|')
    L += ['','## Monthly at POST p4>=0.30','|rule|month|R|hit|avg N|avg comp|profit|ROI|','|---|---|---:|---:|---:|---:|---:|---:|']
    q=z[np.isclose(z.post_cut,.30)]
    for (rule,mon),g in q.groupby(['rule','month']):
        cost=len(g)*BANK;ret=g.return_yen.sum();L.append(f'|{rule}|{mon}|{len(g)}|{100*g.hit.mean():.2f}%|{g.buy_n.mean():.2f}|{g.comp_odds.mean():.3f}|{ret-cost:+.0f}|{100*ret/cost:.2f}%|')
    L += ['','## Interpretation rule','- ROIだけでなく、購入R数・3連単的中率・Feb-Jun安定性を同時に比較する。','- 最高セルをそのまま正式採用せず、採用候補はv254でfreezeして月別監査する。']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
