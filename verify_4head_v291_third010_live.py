#!/usr/bin/env python3
"""Offline synthetic verifier for HEAD4_V291_COMP7_THIRD010. No race results/network."""
from datetime import timedelta
import run_4head_v291_third010_live as r


def probs(close=True):
    p2={1:.40,2:.30,3:.15,5:.10,6:.05}; pc={}
    for s in r.BOATS:
        rem=[t for t in r.BOATS if t!=s]
        w=[.50,.25,.16,.09] if close else [.55,.30,.10,.05]
        for t,v in zip(rem,w): pc[(s,t)]=v
    return p2,pc


def inp(p2,pc):
    return {"race_code":"209901011403","PRE":r.PRE_CUT,"POST":r.POST_CUT,"ENV_ENTRY":r.ENV_ENTRY_CUT,"p2":p2,"cond":{f"{s}>{t}":v for (s,t),v in pc.items()},"v96_rank":1}


def meta(): return {"source":"OFFLINE_TEST","fetched_at_jst":r.now_jst().isoformat(),"result_endpoint_requested":False,"payout_endpoint_requested":False}


def main():
    # Non-close case remains exact frozen base Top4.
    p2,pc=probs(False); t4=r.production_tickets(p2,pc); assert len(t4)==4
    # Close gap .09 on both Top2 SECOND branches adds rank3 on each => 6 tickets.
    p2,pc=probs(True); t6=r.production_tickets(p2,pc); assert len(t6)==6 and len(set(t6))==6
    base=set(r.base.v283_top4(p2,pc)); assert base.issubset(set(t6))
    # Inclusive boundary exactly 0.10 must fire.
    s=sorted(r.BOATS,key=lambda x:(-p2[x],x))[0]; ts=sorted((t for t in r.BOATS if t!=s),key=lambda t:(-pc[(s,t)],t))
    pc[(s,ts[1])]=.26; pc[(s,ts[2])]=.16
    assert f"4-{s}-{ts[2]}" in r.production_tickets(p2,pc)
    # Variable-N composite boundary: N equal odds N*7 => composite exactly 7.
    ts=r.production_tickets(p2,pc); n=len(ts); odds={t:7.0*n for t in ts}; dl=r.now_jst()+timedelta(hours=1)
    row=r.evaluate_market(inp(p2,pc),odds,meta(),dl); assert row['decision']=='BET'; assert abs(row['composite_odds']-7.0)<1e-12
    assert row['ticket_count']==n; assert row['total_stake']==10000; assert all(x['stake']>0 and x['stake']%100==0 for x in row['tickets'])
    assert row['pair_model']['third_gap']==.10 and row['pair_model']['v96_used'] is False
    # Below comp floor passes with zero stake.
    odds={t:(7.0*n)-.001 for t in ts}; row=r.evaluate_market(inp(p2,pc),odds,meta(),dl); assert row['decision']=='PASS' and row['total_stake']==0
    # S gate still fail-closed.
    x=inp(p2,pc); x['PRE']=r.PRE_CUT-.001; row=r.evaluate_market(x,{}, {},dl); assert row['decision']=='NO_BET'
    print('PASS: HEAD4_V291_COMP7_THIRD010 production invariants')

if __name__=='__main__': main()
