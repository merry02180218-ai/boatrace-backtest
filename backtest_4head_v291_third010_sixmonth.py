#!/usr/bin/env python3
"""Mar-Aug retrospective audit for production HEAD4_V291_COMP7_THIRD010.
September 2026 outcomes are never read. Closing odds are diagnostic only.
The market layer replays production semantics: variable 4..6 tickets, comp>=7,
JPY10,000 Dutch in 100-yen units. Formal prospective ROI remains unavailable.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import analyze_4head_v283_second_margin_rescue as src
import audit_4head_86r_v283_closing_odds as audit
import run_4head_v291_third010_live as live
OUT=Path('/tmp/head4_third010_sixmonth'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-03-01'; END='2026-08-31'; REQUIRED=[f'2026-{m:02d}' for m in range(3,9)]

def main():
    if END >= '2026-09-01': raise RuntimeError('September outcome access blocked')
    df,_=src.build(START,END); df=df[(df.date>=START)&(df.date<=END)].copy()
    months=sorted(df.month.unique().tolist())
    if months != REQUIRED: raise RuntimeError(f'SIX_MONTH_FAIL_CLOSED required={REQUIRED} available={months}')
    # Strong invariants: same production policy and exact frozen ticket semantics.
    if live.POLICY!='HEAD4_V291_COMP7_THIRD010' or live.THIRD_GAP!=0.10 or live.COMP_CUT!=7.0 or live.BANK!=10000:
        raise RuntimeError('PRODUCTION_SEMANTICS_DRIFT')
    odds_cache={}; rows=[]
    for _,r in df.iterrows():
        pair_tuples=src.pairs(r,None,live.THIRD_GAP); tickets=[f'4-{s}-{t}' for s,t in pair_tuples]
        expected=live.production_tickets(r.p2,r.pc)
        if tickets!=expected: raise RuntimeError(f'TICKET_SEMANTICS_MISMATCH {r.race_code}')
        oq=odds_cache.setdefault(r.date,audit.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)] if len(oq) else oq
        odds=[]; covered=len(oo)==1
        if covered:
            for t in tickets:
                v=pd.to_numeric(oo.iloc[0].get(t),errors='coerce')
                if pd.isna(v) or float(v)<=0: covered=False; break
                odds.append(float(v))
        comp=live.composite_odds(odds) if covered else np.nan; bet=bool(covered and comp>=live.COMP_CUT)
        stakes={t:0 for t in tickets}
        if bet:
            plan=live.dutch(tickets,odds); stakes={x['combo']:int(x['stake']) for x in plan}
            if sum(stakes.values())!=live.BANK: raise RuntimeError('DUTCH_BANK_MISMATCH')
        actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''
        hit=bool(bet and actual in stakes and stakes[actual]>0)
        actual_odd=float(oo.iloc[0].get(actual)) if hit else np.nan
        payout=float(stakes[actual]*actual_odd) if hit else 0.0; stake=live.BANK if bet else 0
        rows.append({'date':r.date,'month':r.month,'race_code':r.race_code,'candidate':1,'ticket_count':len(tickets),'covered':int(covered),'composite_odds':comp,'decision':'BET' if bet else ('PASS' if covered else 'NO_ODDS'),'hit':int(hit),'stake':stake,'payout':payout,'profit':payout-stake})
    rd=pd.DataFrame(rows); summary=[]
    for period,q in list(rd.groupby('month'))+[('2026-03..08',rd)]:
        st=float(q.stake.sum()); pay=float(q.payout.sum()); bets=int((q.decision=='BET').sum())
        summary.append({'period':period,'candidate_R':len(q),'covered_R':int(q.covered.sum()),'bet_R':bets,'pass_R':int((q.decision=='PASS').sum()),'tickets_if_candidate':int(q.ticket_count.sum()),'hits':int(q.hit.sum()),'stake':st,'payout':pay,'profit':pay-st,'roi_pct':100*pay/st if st else np.nan})
    sm=pd.DataFrame(summary)
    if set(sm[sm.period.str.match(r'2026-\d\d')].period)!=set(REQUIRED): raise RuntimeError('MONTH_SUMMARY_INCOMPLETE')
    rd.to_csv(OUT/'race_detail.csv',index=False); sm.to_csv(OUT/'summary.csv',index=False)
    meta={'policy':live.POLICY,'window':[START,END],'months':REQUIRED,'third_gap':live.THIRD_GAP,'composite_cut':live.COMP_CUT,'bank_yen':live.BANK,'dutch_unit_yen':100,'odds_source':'closing odds; retrospective diagnostic only','formal_prospective_roi':'NOT_COMPUTABLE','candidate_selection':'frozen reconstruction; no threshold retuning','v96_used':False,'september_2026':'UNREAD'}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('HEAD4_THIRD010_SIXMONTH_OK'); print(sm.to_string(index=False)); print('FORMAL_PROSPECTIVE_ROI NOT_COMPUTABLE'); print('V96_USED False'); print('SEPTEMBER_UNREAD')
if __name__=='__main__': main()
