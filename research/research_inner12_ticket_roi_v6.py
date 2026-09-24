#!/usr/bin/env python3
"""INNER12 fixed-ticket ROI shadow V6.

POSTHOC SHADOW ONLY.

Head routing was frozen before this study:
- A_only -> dual heads 3/4
- B-strong -> head3 only

Opponent tickets are frozen BEFORE odds/ROI evaluation as three fixed budgets:
- LEAN:     A 8 pts / B 4 pts
- BALANCED: A 10 pts / B 5 pts
- WIDE:     A 12 pts / B 7 pts

The sets were derived from V5 descriptive anatomy and are therefore posthoc.
This script does NOT tune tickets using odds or ROI.

Market evaluation:
- prefer BoatraceCSV historical pre-deadline OD3 snapshots;
- fallback to repository official closing odds only when snapshot is absent;
- JPY5,000 per BET, 100-yen inverse-odds Dutch;
- evaluate both ungated and frozen composite-odds >=5 gate.

September outcomes are not read. Production unchanged.
"""
from __future__ import annotations

import glob, json, math, os
from pathlib import Path
import numpy as np
import pandas as pd

V5=Path(os.environ.get("INNER12_V5_ROWS","/tmp/v5/frozen_decisions_with_results.csv"))
BRC=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
ROOT=Path(__file__).resolve().parent
OUT=Path(os.environ.get("INNER12_V6_OUTDIR","/tmp/inner12_ticket_roi_v6"))
OUT.mkdir(parents=True,exist_ok=True)

BANK=5000
COMP_CUT=5.0
MONTHS=("2026-06","2026-07","2026-08")

TICKETS={
    "LEAN":{
        "A":[
            "3-1-4","3-4-2",
            "4-1-2","4-1-5","4-2-5","4-2-6","4-5-1","4-6-1",
        ],
        "B":[
            "3-1-4","3-4-6","3-5-6","3-6-2",
        ],
    },
    "BALANCED":{
        "A":[
            "3-1-4","3-1-6","3-4-2",
            "4-1-2","4-1-5","4-2-5","4-2-6","4-3-6","4-5-1","4-6-1",
        ],
        "B":[
            "3-1-4","3-1-6","3-4-6","3-5-6","3-6-2",
        ],
    },
    "WIDE":{
        "A":[
            "3-1-4","3-1-5","3-1-6","3-4-2",
            "4-1-2","4-1-5","4-2-5","4-2-6","4-3-6","4-5-1","4-5-2","4-6-1",
        ],
        "B":[
            "3-1-4","3-1-6","3-4-6","3-5-2","3-5-6","3-6-1","3-6-2",
        ],
    },
}

EXPECTED_POINTS={
    "LEAN":{"A":8,"B":4},
    "BALANCED":{"A":10,"B":5},
    "WIDE":{"A":12,"B":7},
}

def rc(x):
    s=str(x or "").strip()
    return s.zfill(12) if s else ""

def ff(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def load_odds():
    out={}
    source={}
    # pre-deadline snapshots first
    for p in sorted(glob.glob(str(BRC/"data/previews/od3/2026/*/*.csv"))):
        try:q=pd.read_csv(p,dtype={"レースコード":str})
        except Exception:continue
        for _,r in q.iterrows():
            code=rc(r.get("レースコード"))
            if not ("202606010000" <= code <= "202608319999"):continue
            m={}
            for a in range(1,7):
                for b in range(1,7):
                    if b==a:continue
                    for c in range(1,7):
                        if c in (a,b):continue
                        k=f"{a}-{b}-{c}"
                        v=ff(r.get(f"3連単_{k}"))
                        if v and v>0:m[k]=v
            if len(m)==120:
                out[code]=m
                source[code]="predeadline_od3"
    # closing fallback
    for p in sorted(glob.glob(str(ROOT/"data/official_closing_odds3t/2026/*/*.csv"))):
        try:q=pd.read_csv(p,dtype={"jcd":str})
        except Exception:continue
        for _,r in q.iterrows():
            ds=str(r.get("date","")).replace("-","")
            try:rn=int(r.get("rno",0) or 0)
            except:rn=0
            j=str(r.get("jcd","")).zfill(2)
            if not ("20260601" <= ds <= "20260831") or rn<1:continue
            code=f"{ds}{j}{rn:02d}"
            if code in out:continue
            m={}
            for a in range(1,7):
                for b in range(1,7):
                    if b==a:continue
                    for c in range(1,7):
                        if c in (a,b):continue
                        k=f"{a}-{b}-{c}"
                        v=ff(r.get(k))
                        if v and v>0:m[k]=v
            if len(m)==120:
                out[code]=m
                source[code]="closing_fallback"
    return out,source

def composite(odds):
    vals=[float(x) for x in odds]
    if not vals or any(x<=0 for x in vals):return None
    return 1.0/sum(1.0/x for x in vals)

def dutch5000(odds):
    vals=np.asarray([float(x) for x in odds],dtype=float)
    inv=1.0/vals
    raw=BANK*inv/inv.sum()
    # at least 100 yen per ticket; then Hamilton in 100-yen units
    units=np.maximum(1,np.floor(raw/100).astype(int))
    target=BANK//100
    # if floors exceed target (should not for current point counts), remove from
    # tickets with smallest fractional claim while preserving >=1.
    while int(units.sum())>target:
        candidates=[i for i,u in enumerate(units) if u>1]
        if not candidates:raise RuntimeError("DUTCH_MINIMUM_EXCEEDS_BANK")
        i=min(candidates,key=lambda j:(raw[j]/100-units[j],raw[j]))
        units[i]-=1
    rem=target-int(units.sum())
    frac=raw/100-np.floor(raw/100)
    order=sorted(range(len(vals)),key=lambda i:(frac[i],raw[i]),reverse=True)
    for k in range(rem):
        units[order[k%len(order)]]+=1
    stakes=units*100
    if int(stakes.sum())!=BANK or np.any(stakes<100) or np.any(stakes%100):
        raise RuntimeError("DUTCH_INVARIANT")
    return stakes.astype(int).tolist()

def max_losing_streak(hit):
    cur=mx=0
    for h in hit:
        cur=0 if h else cur+1
        mx=max(mx,cur)
    return mx

def stats(z):
    if not len(z):
        return {"R":0,"hits":0,"stake":0,"payout":0.0,"profit":0.0,"roi":None}
    stake=int(z.stake.sum())
    payout=float(z.payout.sum())
    eq=z.profit.cumsum()
    peak=eq.cummax().clip(lower=0)
    return {
        "R":int(len(z)),
        "hits":int(z.hit.sum()),
        "hit_rate":float(z.hit.mean()),
        "stake":stake,
        "payout":payout,
        "profit":float(payout-stake),
        "roi":float(100*payout/stake) if stake else None,
        "avg_points":float(z.points.mean()),
        "avg_composite":float(z.composite.mean()),
        "max_drawdown":float((peak-eq).max()),
        "max_losing_streak":int(max_losing_streak(z.hit.tolist())),
        "predeadline_R":int((z.odds_source=="predeadline_od3").sum()),
        "closing_fallback_R":int((z.odds_source=="closing_fallback").sum()),
    }

def main():
    if not V5.exists():raise RuntimeError(f"MISSING_V5_{V5}")
    for name,branches in TICKETS.items():
        for branch,ts in branches.items():
            if len(ts)!=EXPECTED_POINTS[name][branch] or len(ts)!=len(set(ts)):
                raise RuntimeError(f"TICKET_SET_INVARIANT_{name}_{branch}")

    d=pd.read_csv(V5,dtype={"race_code":str})
    d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.month.isin(MONTHS)&d.action.isin(["A_DUAL_3_4","B_3HEAD"])].copy()
    if len(d)!=68:raise RuntimeError(f"EXPECTED_68_FROZEN_RACES_GOT_{len(d)}")

    odds,source=load_odds()
    records=[]
    for policy,branches in TICKETS.items():
        for r in d.itertuples():
            branch="A" if r.action=="A_DUAL_3_4" else "B"
            tickets=list(branches[branch])
            om=odds.get(str(r.race_code))
            if om is None or any(t not in om for t in tickets):
                records.append({
                    "policy":policy,"race_code":r.race_code,"month":r.month,"action":r.action,
                    "points":len(tickets),"tickets":"|".join(tickets),
                    "odds_available":0,"odds_source":source.get(str(r.race_code),"missing"),
                    "composite":np.nan,"actual_ticket":f"{int(r.actual_head)}-{int(r.actual_second)}-{int(r.actual_third)}",
                    "gate":"MISSING_ODDS","stake":0,"hit":0,"payout":0.0,"profit":0.0,
                })
                continue
            ovs=[float(om[t]) for t in tickets]
            comp=composite(ovs)
            stakes=dutch5000(ovs)
            actual=f"{int(r.actual_head)}-{int(r.actual_second)}-{int(r.actual_third)}"
            for gate_name,bet in (("ALL",True),("COMP5",bool(comp is not None and comp>=COMP_CUT))):
                hit=0;payout=0.0;stake=BANK if bet else 0
                if bet and actual in tickets:
                    idx=tickets.index(actual)
                    hit=1
                    payout=float(stakes[idx])*float(ovs[idx])
                records.append({
                    "policy":policy,"race_code":r.race_code,"month":r.month,"action":r.action,
                    "points":len(tickets),"tickets":"|".join(tickets),
                    "odds_available":1,"odds_source":source[str(r.race_code)],
                    "composite":float(comp),"actual_ticket":actual,
                    "gate":gate_name,"stake":stake,"hit":hit,"payout":payout,"profit":payout-stake,
                })

    z=pd.DataFrame(records)
    z.to_csv(OUT/"race_detail.csv",index=False)

    summary={}
    for policy in TICKETS:
        summary[policy]={}
        for gate in ("ALL","COMP5"):
            q=z[(z.policy==policy)&(z.gate==gate)&(z.odds_available==1)&(z.stake>0)].sort_values(["month","race_code"]).copy()
            x={"total":stats(q),"monthly":{},"branch":{}}
            for m in MONTHS:x["monthly"][m]=stats(q[q.month.eq(m)])
            for a in ("A_DUAL_3_4","B_3HEAD"):x["branch"][a]=stats(q[q.action.eq(a)])
            x["eligible_R_before_comp_gate"]=int(((z.policy==policy)&(z.gate=="ALL")&(z.odds_available==1)).sum())
            x["missing_odds_unique_R"]=int(d.race_code.nunique()-z[(z.policy==policy)&(z.odds_available==1)].race_code.nunique())
            summary[policy][gate]=x

    meta={
        "model_id":"INNER12_FIXED_TICKET_ROI_SHADOW_V6",
        "status":"POSTHOC_SHADOW_ONLY",
        "bank_per_bet_jpy":BANK,
        "dutch_rounding_jpy":100,
        "composite_gate":COMP_CUT,
        "tickets":TICKETS,
        "tickets_frozen_before_odds_roi":True,
        "odds_preference":["BoatraceCSV predeadline OD3","official closing fallback"],
        "summary":summary,
        "september_outcomes_read":False,
        "production_changed":False,
        "warning":"Ticket sets were derived from Jun-Aug outcome anatomy. ROI is descriptive/posthoc, not validation."
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_FIXED_TICKET_ROI_SHADOW_V6_OK")
    print("SUMMARY",json.dumps(summary,ensure_ascii=False))
    print("TICKETS_FROZEN_BEFORE_ODDS_ROI")
    print("POSTHOC_SHADOW_ONLY")
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
