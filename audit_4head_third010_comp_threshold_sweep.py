#!/usr/bin/env python3
"""Retrospective closing-odds sweep for HEAD4 THIRD0.10 composite cutoff.
Mar-Aug only; September outcomes are blocked. This does not change production.
"""
from pathlib import Path
import math
import pandas as pd
import analyze_4head_v283_second_margin_rescue as src
import audit_4head_86r_v283_closing_odds as audit
import run_4head_v291_third010_live as live

OUT=Path('/tmp/head4_third010_comp_sweep'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-03-01'; END='2026-08-31'
CUTS=[0.0,6.0,6.25,6.5,6.75,7.0]

def main():
    if END >= '2026-09-01': raise RuntimeError('September outcome access blocked')
    df,_=src.build(START,END); df=df[(df.date>=START)&(df.date<=END)].copy()
    odds_cache={}; base=[]
    for _,r in df.iterrows():
        tickets=[f'4-{s}-{t}' for s,t in src.pairs(r,None,live.THIRD_GAP)]
        if tickets!=live.production_tickets(r.p2,r.pc): raise RuntimeError(f'TICKET_SEMANTICS_MISMATCH {r.race_code}')
        actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''
        raw_hit=bool(actual and actual in tickets)
        oq=odds_cache.setdefault(r.date,audit.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)] if len(oq) else oq
        if len(oo)!=1: raise RuntimeError(f'ODDS_MISSING {r.race_code}')
        odds=[]
        for t in tickets:
            v=pd.to_numeric(oo.iloc[0].get(t),errors='coerce')
            if pd.isna(v) or float(v)<=0: raise RuntimeError(f'ODDS_INVALID {r.race_code} {t}')
            odds.append(float(v))
        comp=live.composite_odds(odds)
        stakes={x['combo']:x['stake'] for x in live.dutch(tickets,odds)}
        payout=float(stakes.get(actual,0))*float(oo.iloc[0].get(actual,0)) if raw_hit else 0.0
        base.append({'date':r.date,'month':r.month,'race_code':r.race_code,'tickets':len(tickets),'raw_hit':int(raw_hit),'composite_odds':comp,'payout_if_bet':payout})
    rd=pd.DataFrame(base)
    apr=rd[rd.month>='2026-04']
    if len(apr)!=164 or int(apr.tickets.sum())!=817 or int(apr.raw_hit.sum())!=35: raise RuntimeError('LEGACY_GUARD_FAILED')
    periods=[('DEV_APR_JUN',rd[(rd.month>='2026-04')&(rd.month<='2026-06')]),('HOLDOUT_JUL_AUG',rd[(rd.month>='2026-07')&(rd.month<='2026-08')]),('APR_AUG',apr),('MAR_AUG',rd)]
    rows=[]
    for cut in CUTS:
        for period,q in periods:
            b=q if cut==0 else q[q.composite_odds>=cut]
            stake=10000*len(b); payout=float(b.payout_if_bet.sum()); hits=int(b.raw_hit.sum())
            rows.append({'cut':'NO_FILTER' if cut==0 else f'{cut:.2f}','period':period,'candidate_R':len(q),'bet_R':len(b),'hits':hits,'raw_hits_total':int(q.raw_hit.sum()),'discarded_raw_hits':int(q.raw_hit.sum())-hits,'stake':stake,'payout':payout,'profit':payout-stake,'roi_pct':(payout/stake*100 if stake else math.nan)})
    sm=pd.DataFrame(rows); sm.to_csv(OUT/'threshold_sweep.csv',index=False)
    monthly=[]
    for cut in CUTS:
        for month,q in rd[rd.month>='2026-04'].groupby('month'):
            b=q if cut==0 else q[q.composite_odds>=cut]; stake=10000*len(b); payout=float(b.payout_if_bet.sum())
            monthly.append({'cut':'NO_FILTER' if cut==0 else f'{cut:.2f}','month':month,'bet_R':len(b),'hits':int(b.raw_hit.sum()),'stake':stake,'payout':payout,'roi_pct':payout/stake*100 if stake else math.nan})
    pd.DataFrame(monthly).to_csv(OUT/'monthly_sweep.csv',index=False)
    rd.to_csv(OUT/'race_detail.csv',index=False)
    print('HEAD4_THIRD010_COMP_THRESHOLD_SWEEP_OK')
    print(sm.to_string(index=False)); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED_COMP7')
if __name__=='__main__': main()
