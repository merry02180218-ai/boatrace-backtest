#!/usr/bin/env python3
"""Reconcile raw THIRD0.10 ticket hits vs production comp>=7 market filter.
Mar-Aug only. September outcomes are never read.
"""
from pathlib import Path
import pandas as pd
import analyze_4head_v283_second_margin_rescue as src
import audit_4head_86r_v283_closing_odds as audit
import run_4head_v291_third010_live as live

OUT=Path('/tmp/head4_third010_raw_reconcile'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-03-01'; END='2026-08-31'

def main():
    if END >= '2026-09-01': raise RuntimeError('September outcome access blocked')
    df,_=src.build(START,END); df=df[(df.date>=START)&(df.date<=END)].copy()
    odds_cache={}; rows=[]
    for _,r in df.iterrows():
        tickets=[f'4-{s}-{t}' for s,t in src.pairs(r,None,live.THIRD_GAP)]
        expected=live.production_tickets(r.p2,r.pc)
        if tickets!=expected: raise RuntimeError(f'TICKET_SEMANTICS_MISMATCH {r.race_code}')
        actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''
        raw_hit=bool(actual and actual in tickets)
        oq=odds_cache.setdefault(r.date,audit.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)] if len(oq) else oq
        covered=len(oo)==1; odds=[]
        if covered:
            for t in tickets:
                v=pd.to_numeric(oo.iloc[0].get(t),errors='coerce')
                if pd.isna(v) or float(v)<=0: covered=False; break
                odds.append(float(v))
        comp=live.composite_odds(odds) if covered else float('nan')
        bet=bool(covered and comp>=live.COMP_CUT)
        rows.append({'date':r.date,'month':r.month,'race_code':r.race_code,'ticket_count':len(tickets),'head4':int(r.head4),'actual':actual,'raw_ticket_hit':int(raw_hit),'covered':int(covered),'composite_odds':comp,'decision':'BET' if bet else ('PASS' if covered else 'NO_ODDS'),'bet_hit':int(raw_hit and bet),'pass_discarded_hit':int(raw_hit and covered and not bet)})
    rd=pd.DataFrame(rows)
    rd.to_csv(OUT/'raw_hit_reconcile.csv',index=False)
    rec=[]
    for period,q in list(rd.groupby('month'))+[('2026-03..08',rd),('2026-04..08',rd[rd.month>='2026-04'])]:
        rec.append({'period':period,'R':len(q),'tickets':int(q.ticket_count.sum()),'head4':int(q.head4.sum()),'raw_hits':int(q.raw_ticket_hit.sum()),'bet_R':int((q.decision=='BET').sum()),'bet_hits':int(q.bet_hit.sum()),'pass_R':int((q.decision=='PASS').sum()),'discarded_correct_hits':int(q.pass_discarded_hit.sum())})
    sm=pd.DataFrame(rec); sm.to_csv(OUT/'reconcile_summary.csv',index=False)
    apr=sm[sm.period.eq('2026-04..08')].iloc[0]
    if int(apr.R)!=164 or int(apr.tickets)!=817 or int(apr.raw_hits)!=35:
        raise RuntimeError(f'LEGACY_RECONCILE_MISMATCH R={apr.R} tickets={apr.tickets} raw_hits={apr.raw_hits}')
    print('HEAD4_THIRD010_RAW_RECONCILE_OK'); print(sm.to_string(index=False))
    print('\nDISCARDED_CORRECT_HITS'); print(rd[rd.pass_discarded_hit.eq(1)][['date','month','race_code','actual','ticket_count','composite_odds']].to_string(index=False))
    print('SEPTEMBER_UNREAD')
if __name__=='__main__': main()
