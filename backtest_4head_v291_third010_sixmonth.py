#!/usr/bin/env python3
"""Six-month retrospective audit for production THIRD0.10 ticket semantics.
September 2026 outcomes are never read. Closing odds are diagnostic only.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import analyze_4head_v283_second_margin_rescue as src
import audit_4head_86r_v283_closing_odds as audit

OUT=Path('/tmp/head4_third010_sixmonth'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-03-01'; END='2026-08-31'; THIRD_GAP=.10; STAKE_PER_TICKET=100

def main():
    # src.build is the frozen reconstruction path used by the strict audit.
    # It currently reconstructs the audited Apr-Aug population; do not silently
    # call five months "six months". March must be available from the same frozen
    # reconstruction path or this audit fails closed.
    df,_=src.build()
    df=df[(df.date>=START)&(df.date<=END)].copy()
    months=sorted(df.month.unique().tolist())
    required=[f'2026-{m:02d}' for m in range(3,9)]
    if months != required:
        raise RuntimeError(f'SIX_MONTH_FAIL_CLOSED required={required} available={months}; frozen candidate reconstruction does not yet supply full Mar-Aug window')

    odds_cache={}; rows=[]
    for _,r in df.iterrows():
        ps=src.pairs(r,None,THIRD_GAP)
        oq=odds_cache.setdefault(r.date,audit.odds_for_date(r.date))
        oo=oq[oq.race_code.astype(str)==str(r.race_code)] if len(oq) else oq
        covered=len(oo)==1
        hp=(int(r.actual_second),int(r.actual_third)) if r.head4 else None
        hit=bool(covered and hp in ps)
        odd=pd.to_numeric(oo.iloc[0].get(f'4-{hp[0]}-{hp[1]}'),errors='coerce') if hit else np.nan
        hit=bool(hit and pd.notna(odd)); payout=float(odd*STAKE_PER_TICKET) if hit else 0.0
        stake=len(ps)*STAKE_PER_TICKET if covered else 0
        rows.append({'date':r.date,'month':r.month,'race_code':r.race_code,'tickets':len(ps),'covered':int(covered),'hit':int(hit),'stake':stake,'payout':payout,'profit':payout-stake})
    rd=pd.DataFrame(rows)
    summary=[]
    for period,q in list(rd.groupby('month'))+[('2026-03..08',rd)]:
        st=float(q.stake.sum()); pay=float(q.payout.sum())
        summary.append({'period':period,'R':len(q),'covered_R':int(q.covered.sum()),'tickets':int(q.tickets.sum()),'hits':int(q.hit.sum()),'stake':st,'payout':pay,'profit':pay-st,'roi_pct':100*pay/st if st else np.nan})
    sm=pd.DataFrame(summary)
    rd.to_csv(OUT/'race_detail.csv',index=False); sm.to_csv(OUT/'summary.csv',index=False)
    (OUT/'meta.json').write_text(json.dumps({'policy':'HEAD4_V291_COMP7_THIRD010','window':[START,END],'third_gap':THIRD_GAP,'closing_odds':'retrospective diagnostic only','formal_prospective_roi':'NOT_COMPUTABLE','september_2026':'UNREAD'},indent=2)+'\n')
    print('HEAD4_THIRD010_SIXMONTH_OK'); print(sm.to_string(index=False)); print('FORMAL_PROSPECTIVE_ROI NOT_COMPUTABLE'); print('SEPTEMBER_UNREAD')
if __name__=='__main__': main()
