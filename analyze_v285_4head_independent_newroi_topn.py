#!/usr/bin/env python3
"""v285: economic audit of independent 4-head opponent models with exact 10k Dutch.

Compares v283 and v284 opponent orders on the frozen S+A head-selector portfolio.
The independent opponent models are NOT retrained here and v96 is benchmark-only.

Settlement discipline
---------------------
* Every eligible S/A BET race costs exactly 10,000 yen.
* If boat 4 does not win, payout is 0 regardless of opponent order.
* If boat 4 wins, take model Top-N (N=4,6,8,10), freeze those tickets, then
  settle using archived trifecta odds with inverse-odds Dutch / 100-yen Hamilton.
* Miss payout 0 / profit -10,000 yen.
* Archived odds are retrospective proxy only, not claimed as immutable live odds.
* Jul/Aug excluded; September not read.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v96_4corner_monthly_walkforward_tiebreak as v96
import analyze_v251_4head_newroi_bridge as v251
import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v282_4head_conditional_third as v282
import analyze_v283_4head_conditional_pair_order as v283
import analyze_v284_4head_conditional_third_regime as v284
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v285_4head_independent_newroi_topn.csv'
MONTH=ROOT/'analysis_v285_4head_independent_newroi_topn_monthly.csv'
DETAIL=ROOT/'analysis_v285_4head_independent_newroi_topn_detail.csv'
SUM=ROOT/'summary_v285_4head_independent_newroi_topn.md'
BANK=10000
NS=(4,6,8,10)
PORT_MONTHS=('2026-04','2026-05','2026-06')


def ii(x,d=0):
    try:return int(float(x))
    except:return d


def selected_portfolio():
    s=pd.read_csv(v274.SEL,dtype={'race_code':str})
    s['race_code']=s.race_code.astype(str).str.zfill(12)
    for c in ('PRE','POST','a_score'):
        s[c]=pd.to_numeric(s[c],errors='coerce')
    is_s=s['is_S'].astype(str).str.lower().isin(('true','1'))
    is_a=(~is_s)&(s.PRE>=.18)&(s.POST>=.18)&(s.a_score>=.28)
    q=s[s.month.isin(PORT_MONTHS)&(is_s|is_a)].copy()
    q['layer']=np.where(is_s.loc[q.index],'S','A')
    return q[['date','month','race_code','layer']].drop_duplicates('race_code')


def actual_map():
    out={}
    for r in v96.read():
        code=str(r.get('race_code','')).zfill(12)
        out[code]=(ii(r.get('winner')),ii(r.get('second')),ii(r.get('third')),ii(r.get('valid_result')))
    return out


def load_model_rows(path):
    z=pd.read_csv(path,dtype={'race_code':str});z['race_code']=z.race_code.astype(str).str.zfill(12)
    return {str(r.race_code):r for _,r in z.iterrows()}


def order_v283(r):
    p2=v282.parse_p2(r.p2);pc=v282.parse_cond(r['cond'])
    # Frozen policy from v283: TOP2XTOP2, alpha=.60. Threshold is irrelevant for this mode.
    return v283.order_policy(p2,pc,.60,'TOP2XTOP2',1.50)


def order_v284(r):
    p2=v284.parse_p2(r.p2);pc=v284.parse_cond(r['cond'])
    # Frozen policy from v284: TOP2XTOP2, alpha=.60.
    return v284.order_policy(p2,pc,.60,'TOP2XTOP2')


def odds_row(oi,code):
    if code not in oi.index:return None
    r=oi.loc[code]
    if isinstance(r,pd.DataFrame):r=r.iloc[-1]
    return r


def settle_topn(order,n,odrow,actual):
    tickets=[f'4-{a}-{b}' for a,b in order[:n]]
    return v251.settle('',tickets,odrow,actual),tickets


def main():
    port=selected_portfolio();am=actual_map()
    p283=load_model_rows(v283.OUT);p284=load_model_rows(v284.OUT)
    od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
    rows=[]
    missing_actual=missing_win_model=missing_win_odds=0
    for _,r in port.iterrows():
        code=str(r.race_code).zfill(12);a=am.get(code)
        if not a or a[3]!=1:
            missing_actual+=1;continue
        for model,lookup,ofn in [('v283',p283,order_v283),('v284',p284,order_v284)]:
            order=None
            if a[0]==4:
                mr=lookup.get(code)
                if mr is None:
                    missing_win_model+=1;continue
                order=ofn(mr)
            for n in NS:
                hit=0;ret=0.0;comp=np.nan;tickets=''
                if a[0]==4:
                    odr=odds_row(oi,code)
                    if odr is None:
                        missing_win_odds+=1;continue
                    st,ts=settle_topn(order,n,odr,a)
                    if st is None:
                        missing_win_odds+=1;continue
                    hit,ret,comp=st;tickets='|'.join(ts)
                rows.append({'date':r.date,'month':r.month,'race_code':code,'layer':r.layer,'model':model,'n':n,
                             'winner':a[0],'second':a[1],'third':a[2],'head4_win':int(a[0]==4),'hit':int(hit),
                             'return_yen':float(ret),'profit_yen':float(ret-BANK),'comp_odds':comp,'tickets':tickets})
    z=pd.DataFrame(rows)
    if z.empty:raise RuntimeError('no settled portfolio rows')
    z.to_csv(DETAIL,index=False)

    def agg(g):
        cost=len(g)*BANK;ret=float(g.return_yen.sum())
        return {'R':len(g),'head4_wins':int(g.head4_win.sum()),'trifecta_hits':int(g.hit.sum()),
                'head4_rate_pct':100*g.head4_win.mean(),'hit_rate_pct':100*g.hit.mean(),
                'avg_comp_odds_on_head4':g.loc[g.head4_win==1,'comp_odds'].mean(),
                'cost_yen':cost,'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost}

    out=[]
    for (model,n),g in z.groupby(['model','n']):
        out.append({'scope':'S+A','model':model,'n':n,**agg(g)})
        for layer,gg in g.groupby('layer'):
            out.append({'scope':layer,'model':model,'n':n,**agg(gg)})
    O=pd.DataFrame(out);O.to_csv(OUT,index=False)

    mon=[]
    for (month,scope,model,n),g in pd.concat([
        z.assign(scope='S+A'),z.assign(scope=z.layer)
    ],ignore_index=True).groupby(['month','scope','model','n']):
        mon.append({'month':month,'scope':scope,'model':model,'n':n,**agg(g)})
    M=pd.DataFrame(mon);M.to_csv(MONTH,index=False)

    L=['# v285 independent 4-head opponent Top-N / exact 10k Dutch ROI','',
       '- Portfolio: frozen S priority + A outside S, Apr-Jun only.',
       '- v283/v284 opponent models are independent of v96; v96 is not used here for ranking or settlement.',
       '- Every settled BET race costs exactly 10,000 yen. Boat-4 loss => payout 0 / profit -10,000 yen.',
       '- Boat-4 wins use model Top-N tickets, then inverse-odds Dutch with 100-yen Hamilton rounding.',
       '- Archived historical odds are settlement proxy only; this is retrospective development evidence, not formal prospective OOS.',
       '- Jul/Aug excluded; September not read.','',
       f'- skipped invalid/missing actual rows: **{missing_actual}**',
       f'- missing model row on boat-4 win: **{missing_win_model}**',
       f'- missing/invalid odds settlements on boat-4 win: **{missing_win_odds}**','',
       '## S+A aggregate','',
       '|model|N|R|4-head wins|3連単 hits|hit rate|avg composite odds*|cost|return|profit|ROI|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    sa=O[O.scope=='S+A'].sort_values(['model','n'])
    for _,r in sa.iterrows():
        L.append(f'|{r.model}|{int(r.n)}|{int(r.R)}|{int(r.head4_wins)}|{int(r.trifecta_hits)}|{r.hit_rate_pct:.2f}%|{r.avg_comp_odds_on_head4:.3f}|{r.cost_yen:.0f}|{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    L += ['','\* average composite odds is descriptive on boat-4-win races only; ROI includes every S+A BET race, including boat-4 losses.','',
          '## S and A separately','',
          '|scope|model|N|R|3連単 hits|return|profit|ROI|','|---|---|---:|---:|---:|---:|---:|---:|']
    for _,r in O[O.scope.isin(['S','A'])].sort_values(['scope','model','n']).iterrows():
        L.append(f'|{r.scope}|{r.model}|{int(r.n)}|{int(r.R)}|{int(r.trifecta_hits)}|{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    L += ['','## Monthly S+A','',
          '|month|model|N|R|hits|return|profit|ROI|','|---|---|---:|---:|---:|---:|---:|---:|']
    for _,r in M[M.scope=='S+A'].sort_values(['model','n','month']).iterrows():
        L.append(f'|{r.month}|{r.model}|{int(r.n)}|{int(r.R)}|{int(r.trifecta_hits)}|{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    best=sa.sort_values(['roi_pct','R'],ascending=[False,False]).iloc[0]
    L += ['','## Descriptive result','',
          f'- Highest aggregate retrospective ROI among fixed Top4/6/8/10: **{best.model} Top{int(best.n)} = {best.roi_pct:.2f}%** ({int(best.R)} races, {int(best.trifecta_hits)} hits, profit {best.profit_yen:+.0f} yen).',
          '- Do not tune a production rule on Apr-Jun from this result alone. Use this as economic diagnostics for the already-frozen opponent rankings.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
