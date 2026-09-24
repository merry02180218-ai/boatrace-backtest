#!/usr/bin/env python3
"""4HEAD frozen-v291 staking audit.

Ticket selection is fixed to the restored v291 production tickets.
Only staking changes. No ticket/outcome model is fitted.

Strategies:
- DUTCH: alpha=1 inverse-odds, current historical production baseline.
- EQUAL_FLOOR: equal JPY100 units, unused remainder left unbet.
- EQUAL_ORDER / EQUAL_LOW_ODDS / EQUAL_HIGH_ODDS: use full JPY10,000, differing only in
  deterministic placement of the remainder.
- POWER alpha grid: stake proportional to odds**(-alpha); alpha=0 equal, alpha=1 Dutch,
  negative alpha tilts toward longer odds. Grid is predeclared and reported without auto-selection.

June is shown as development context; July-August are holdout. September outcomes unread.
Research only; production staking is not changed here.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import audit_4head_ph5_live_walkforward as parent

OUT=Path("/tmp/head4_v291_staking_audit_v1"); OUT.mkdir(parents=True,exist_ok=True)
BASE=Path("/tmp/head4_ph5_live_walkforward/race_detail.csv")
BANK=10000
POWER_GRID=(-0.75,-0.50,-0.33,-0.20,0.0,0.20,0.50,0.75,1.0)

def round_power(odds,alpha,total=BANK):
    a=np.asarray(odds,float)
    if np.any(~np.isfinite(a)) or np.any(a<=0): raise RuntimeError("BAD_ODDS")
    w=a**(-float(alpha))
    raw=total*w/w.sum()
    units=np.floor(raw/100).astype(int)
    rem=total//100-int(units.sum())
    frac=raw/100-units
    order=np.argsort(-frac,kind="stable")
    for i in order[:rem]: units[i]+=1
    return units*100

def equal_stakes(plan,mode):
    n=len(plan); base=(BANK//(100*n))*100
    st=np.full(n,base,dtype=int)
    rem=(BANK-int(st.sum()))//100
    if mode=="floor": return st
    if mode=="order": order=list(range(n))
    elif mode=="low_odds": order=sorted(range(n),key=lambda i:(float(plan[i]["odds"]),i))
    elif mode=="high_odds": order=sorted(range(n),key=lambda i:(-float(plan[i]["odds"]),i))
    else: raise ValueError(mode)
    for i in order[:rem]: st[i]+=100
    return st

def maxdd(profits):
    eq=np.asarray(profits,float).cumsum()
    peak=np.maximum.accumulate(np.maximum(eq,0))
    return float(np.max(peak-eq)) if len(eq) else 0.0

def longest_losing(hit):
    cur=mx=0
    for h in hit:
        cur=0 if int(h) else cur+1; mx=max(mx,cur)
    return int(mx)

def main():
    d=pd.read_csv(BASE,dtype={"race_code":str})
    d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.production_bet.eq(1)].copy().sort_values(["date","race_code"])
    if len(d)!=163: raise RuntimeError(f"FROZEN_163_DRIFT_{len(d)}")

    # Freeze every staking plan first. No result/truth access is allowed above this point.
    frozen=[]
    for _,r in d.iterrows():
        plan=json.loads(r.stake_plan)
        odds=[float(x["odds"]) for x in plan]
        combos=[str(x["combo"]) for x in plan]
        strategies={
            "DUTCH_ALPHA1":round_power(odds,1.0),
            "EQUAL_FLOOR":equal_stakes(plan,"floor"),
            "EQUAL_FULL_ORDER":equal_stakes(plan,"order"),
            "EQUAL_FULL_LOW_ODDS":equal_stakes(plan,"low_odds"),
            "EQUAL_FULL_HIGH_ODDS":equal_stakes(plan,"high_odds"),
        }
        for a in POWER_GRID:
            strategies[f"POWER_{a:+.2f}"]=round_power(odds,a)

        for name,st in strategies.items():
            frozen.append({
                "date":str(r.date),"race_code":r.race_code,"month":str(r.date)[:7],
                "strategy":name,"ticket_count":len(plan),"stake":int(st.sum()),
                "combos_json":json.dumps(combos,ensure_ascii=False),
                "odds_json":json.dumps(odds),
                "stakes_json":json.dumps([int(x) for x in st]),
            })

    # Attach outcomes only after all strategies/stakes are frozen.
    truth=parent.truth()
    settled=[]
    for rec in frozen:
        a=truth.get(rec["race_code"])
        actual=f"{a[0]}-{a[1]}-{a[2]}" if a else ""
        combos=json.loads(rec["combos_json"])
        odds=json.loads(rec["odds_json"])
        stakes=json.loads(rec["stakes_json"])
        hit=int(actual in combos)
        payout=0.0
        winner_odds=np.nan
        winner_stake=0
        if hit:
            i=combos.index(actual)
            winner_odds=float(odds[i])
            winner_stake=int(stakes[i])
            payout=float(winner_stake)*winner_odds
        out=dict(rec)
        out.update({
            "actual":actual,
            "hit":hit,
            "payout":float(payout),
            "profit":float(payout-int(rec["stake"])),
            "winner_odds":winner_odds,
            "winner_stake":winner_stake,
        })
        settled.append(out)

    z=pd.DataFrame(settled)
    z.to_csv(OUT/"detail.csv",index=False)

    periods={
        "JUNE":lambda x:x.month.eq("2026-06"),
        "JUL_AUG_HOLDOUT":lambda x:x.month.isin(["2026-07","2026-08"]),
        "ALL":lambda x:pd.Series(True,index=x.index),
    }
    rows=[]
    for name,g in z.groupby("strategy"):
        for period,mask in periods.items():
            q=g[mask(g)].sort_values(["date","race_code"])
            rows.append({
                "strategy":name,"period":period,"R":len(q),"hits":int(q.hit.sum()),
                "stake":int(q.stake.sum()),"payout":float(q.payout.sum()),
                "profit":float(q.profit.sum()),"roi":float(100*q.payout.sum()/q.stake.sum()),
                "avg_winner_stake":float(q.loc[q.hit.eq(1),"winner_stake"].mean()) if q.hit.sum() else None,
                "max_drawdown":maxdd(q.profit.tolist()),
                "max_losing_streak":longest_losing(q.hit.tolist()),
                "payout_sd":float(q.payout.std()) if len(q)>1 else 0.0,
            })
    summary=pd.DataFrame(rows)
    summary.to_csv(OUT/"summary.csv",index=False)

    monthly=(z.groupby(["strategy","month"]).agg(
        R=("race_code","size"),hits=("hit","sum"),stake=("stake","sum"),payout=("payout","sum"),
        profit=("profit","sum"),avg_winner_stake=("winner_stake",lambda s:float(s[s.gt(0)].mean()) if s.gt(0).any() else np.nan)
    ).reset_index())
    monthly["roi"]=100*monthly.payout/monthly.stake
    monthly.to_csv(OUT/"monthly.csv",index=False)

    # Why Dutch differs: winning-odds decomposition for DUTCH vs full equal.
    dd=z[z.strategy.eq("DUTCH_ALPHA1")][["race_code","month","winner_odds","winner_stake","payout"]].rename(
        columns={"winner_stake":"dutch_winner_stake","payout":"dutch_payout"})
    ee=z[z.strategy.eq("EQUAL_FULL_ORDER")][["race_code","winner_stake","payout"]].rename(
        columns={"winner_stake":"equal_winner_stake","payout":"equal_payout"})
    h=dd.merge(ee,on="race_code",how="inner",validate="one_to_one")
    h=h[h.winner_odds.notna()].copy()
    h["delta_equal_minus_dutch"]=h.equal_payout-h.dutch_payout
    bins=[0,10,20,30,50,100,float("inf")]
    labels=["<10x","10-20x","20-30x","30-50x","50-100x","100x+"]
    h["odds_band"]=pd.cut(h.winner_odds,bins=bins,labels=labels,right=False)
    band=(h.groupby("odds_band",observed=False).agg(
        hits=("race_code","size"),avg_odds=("winner_odds","mean"),
        dutch_avg_stake=("dutch_winner_stake","mean"),equal_avg_stake=("equal_winner_stake","mean"),
        dutch_payout=("dutch_payout","sum"),equal_payout=("equal_payout","sum"),
        delta_equal_minus_dutch=("delta_equal_minus_dutch","sum")
    ).reset_index())
    band.to_csv(OUT/"winning_odds_band.csv",index=False)

    meta={
        "frozen_ticket_policy":"HEAD4_V291_COMP7_OPP_S011_T018",
        "ticket_selection_changed":False,
        "bank_per_race":BANK,
        "power_definition":"stake proportional to odds**(-alpha); alpha=0 equal; alpha=1 Dutch",
        "grid_auto_selected":False,
        "development":"June shown only",
        "holdout":"July-August",
        "SEPTEMBER_OUTCOMES_READ":False,
        "PRODUCTION_STAKING_CHANGED":False,
        "settlement":"truth joined only after all staking plans frozen",
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("V291_STAKING_SUMMARY",summary.to_json(orient="records",force_ascii=False))
    print("V291_STAKING_MONTHLY",monthly.to_json(orient="records",force_ascii=False))
    print("V291_STAKING_ODDS_BAND",band.to_json(orient="records",force_ascii=False))
    print("V291_STAKING_META",json.dumps(meta,ensure_ascii=False))
    print("V291_STAKING_AUDIT_V1_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":
    main()
