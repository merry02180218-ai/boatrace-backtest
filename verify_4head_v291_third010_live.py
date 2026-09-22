#!/usr/bin/env python3
"""Offline verifier for adopted 4HEAD opponent policy S011/T018. No results/network."""
from datetime import timedelta
import run_4head_v291_third010_live as r

def probs(second_close=False, third_close=False):
    p2={1:.40,2:.30,3:(.20 if second_close else .15),5:(.07 if second_close else .10),6:(.03 if second_close else .05)}
    pc={}
    for s in r.BOATS:
        rem=[t for t in r.BOATS if t!=s]
        w=[.50,.25,.08,.17] if not third_close else [.50,.25,.10,.15]
        for t,v in zip(rem,w): pc[(s,t)]=v
    return p2,pc

def inp(p2,pc):
    return {"race_code":"209901011403","PRE":r.PRE_CUT,"POST":r.POST_CUT,"ENV_ENTRY":r.ENV_ENTRY_CUT,"p2":p2,"cond":{f"{s}>{t}":v for (s,t),v in pc.items()}}

def meta(): return {"source":"OFFLINE_TEST","fetched_at_jst":r.now_jst().isoformat(),"result_endpoint_requested":False,"payout_endpoint_requested":False}

def main():
    assert r.SECOND_GAP==.11 and r.THIRD_GAP==.18 and r.MIN_TICKETS==4 and r.MAX_TICKETS==9
    p2,pc=probs(False,False); base=r.production_tickets(p2,pc); assert len(base)==4
    p2,pc=probs(True,False); t=r.production_tickets(p2,pc); assert len(t)==6
    p2,pc=probs(False,True); t=r.production_tickets(p2,pc); assert len(t)==6
    p2,pc=probs(True,True); t=r.production_tickets(p2,pc); assert 6<=len(t)<=9 and len(set(t))==len(t)
    assert set(r.base.v283_top4(p2,pc)).issubset(set(t))
    n=len(t); odds={x:7.0*n for x in t}; dl=r.now_jst()+timedelta(hours=1)
    row=r.evaluate_market(inp(p2,pc),odds,meta(),dl)
    assert row["decision"]=="BET" and abs(row["composite_odds"]-7.0)<1e-12
    assert row["total_stake"]==10000 and all(x["stake"]>0 and x["stake"]%100==0 for x in row["tickets"])
    assert row["pair_model"]["second_gap"]==.11 and row["pair_model"]["third_gap"]==.18
    x=inp(p2,pc); x["PRE"]=r.PRE_CUT-.001; assert r.evaluate_market(x,{}, {},dl)["decision"]=="NO_BET"
    print("PASS: HEAD4_V291_COMP7_OPP_S011_T018 production invariants")

if __name__=="__main__": main()
