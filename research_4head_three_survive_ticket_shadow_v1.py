#!/usr/bin/env python3
"""Ticket-level shadow for the adopted INNER_SURVIVE opponent policy plus 3-survival overlay.

The structural branch is imported from the clean broad audit:
- scaler fit on Mar-May ALL struct-ready races;
- q=.75 THREE_SURVIVES cut frozen before result join.

This script:
1) rebuilds the adopted INNER_SURVIVE tickets for the frozen 163 production bets;
2) freezes three minimal 4-3 overlay variants;
3) only then joins outcomes and evaluates JPY10,000 Dutch ROI.

September outcomes remain unread. Research only; production unchanged.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

import audit_4head_ph5_live_walkforward as parent
import research_4head_player_waku_soft_ablation_v23 as phsrc
import research_4head_waku10_rel43_v4 as wsrc
import run_4head_120r_lastminute_fast as inner
import run_4head_v291_third010_live as dutchmod

OUT=Path("/tmp/head4_three_survive_ticket_shadow_v1"); OUT.mkdir(parents=True,exist_ok=True)
BASE=Path("/tmp/head4_ph5_live_walkforward/race_detail.csv")
BRANCH=Path("/tmp/head4_structural_broad_6m_v1/branch_map.csv")
BANK=10000
BOATS=(1,2,3,5,6)

def metrics(q):
    q=q.sort_values(["date","race_code"]).copy()
    eq=(q.payout-q.stake).cumsum()
    peak=eq.cummax().clip(lower=0)
    dd=peak-eq
    cur=mx=0
    for h in q.hit:
        cur=0 if h else cur+1
        mx=max(mx,cur)
    return {
        "R":int(len(q)),"hits":int(q.hit.sum()),"hit_rate":float(q.hit.mean()) if len(q) else None,
        "stake":int(q.stake.sum()),"payout":float(q.payout.sum()),
        "roi":float(100*q.payout.sum()/q.stake.sum()) if q.stake.sum() else None,
        "avg_points":float(q.ticket_count.mean()) if len(q) else None,
        "max_drawdown":float(dd.max()) if len(q) else 0.0,"max_losing_streak":int(mx)
    }

def main():
    d=pd.read_csv(BASE,dtype={"race_code":str}); d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.production_bet.eq(1)].copy()
    if len(d)!=163: raise RuntimeError(f"FROZEN_163_DRIFT {len(d)}")

    bm=pd.read_csv(BRANCH,dtype={"race_code":str}); bm["race_code"]=bm.race_code.astype(str).str.zfill(12)
    keep=["race_code","struct_branch","wall_b3_strength","wall_32break"]
    d=d.merge(bm[keep],on="race_code",how="left",validate="one_to_one")
    if d.struct_branch.isna().any(): raise RuntimeError("MISSING_STRUCT_BRANCH")

    ph=phsrc.build_ph(); ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
    w=wsrc.build_waku(d.race_code.tolist()); w["race_code"]=w.race_code.astype(str).str.zfill(12)
    d=d.merge(ph,on="race_code",how="left",validate="one_to_one").merge(w,on="race_code",how="left",validate="one_to_one")

    om=parent.od3()
    frozen=[]
    for _,r in d.iterrows():
        diag=json.loads(r.opponent_diag)
        p2={int(k):float(v) for k,v in diag["p2"].items()}
        pc={(int(k.split(">")[0]),int(k.split(">")[1])):float(v) for k,v in diag["pc"].items()}
        pflat={f"b{b}_pl_frame_p2":r.get(f"b{b}_pl_frame_p2") for b in BOATS}
        waku={k:r.get(k) for k in r.index if str(k).startswith("w10_")}
        current=inner.production_tickets(p2,pc,pflat=pflat,waku=waku)
        if not (dutchmod.MIN_TICKETS<=len(current)<=dutchmod.MAX_TICKETS):
            raise RuntimeError("INNER_CURRENT_TICKET_INVARIANT")

        thirds3=sorted((t for t in BOATS if t!=3),key=lambda t:(-float(pc[(3,t)]),t))
        t1=f"4-3-{thirds3[0]}"; t2=f"4-3-{thirds3[1]}"
        variants={"INNER_CURRENT":list(current)}

        add1=list(current)
        if r.struct_branch=="THREE_SURVIVES" and t1 not in add1 and len(add1)<dutchmod.MAX_TICKETS:
            add1.append(t1)
        variants["THREE_ADD1_CAP9"]=add1

        add2=list(current)
        if r.struct_branch=="THREE_SURVIVES":
            for t in (t1,t2):
                if t not in add2 and len(add2)<dutchmod.MAX_TICKETS: add2.append(t)
        variants["THREE_ADD2_CAP9"]=add2

        repl=list(current)
        if r.struct_branch=="THREE_SURVIVES" and t1 not in repl:
            repl[-1]=t1
            repl=list(dict.fromkeys(repl))
        variants["THREE_REPLACE1"]=repl

        for name,ts in variants.items():
            if not (dutchmod.MIN_TICKETS<=len(ts)<=dutchmod.MAX_TICKETS):
                raise RuntimeError(f"{name}_TICKET_INVARIANT_{len(ts)}")
            if any(t not in om.get(r.race_code,{}) for t in ts):
                raise RuntimeError(f"ODDS_MISSING_{r.race_code}_{name}")
            ovs=[om[r.race_code][t] for t in ts]
            plan=dutchmod.dutch(ts,ovs)
            frozen.append({
                "date":str(r.date),"race_code":r.race_code,"month":str(r.date)[:7],
                "variant":name,"branch":r.struct_branch,
                "tickets":"|".join(ts),"ticket_count":len(ts),
                "stake":sum(int(x["stake"]) for x in plan),
                "stake_plan":json.dumps(plan,ensure_ascii=False),
                "modified":int(ts!=current),"target43_top1":t1,"target43_top2":t2
            })

    f=pd.DataFrame(frozen)
    if len(f)!=163*4: raise RuntimeError("FROZEN_VARIANT_COUNT_DRIFT")
    # No outcome fields above this line.
    tr=parent.truth()

    hits=[]; pays=[]; heads=[]; actuals=[]
    for _,r in f.iterrows():
        a=tr.get(r.race_code)
        actual=f"{a[0]}-{a[1]}-{a[2]}" if a else ""
        head=int(bool(a) and a[0]==4)
        pay=float(r.stake) if not a else 0.0
        hit=0
        if a:
            for x in json.loads(r.stake_plan):
                if x["combo"]==actual and int(x["stake"])>0:
                    hit=1; pay=float(x["stake"])*float(x["odds"]); break
        hits.append(hit); pays.append(pay); heads.append(head); actuals.append(actual)
    f["head4"]=heads; f["hit"]=hits; f["payout"]=pays; f["actual"]=actuals
    f.to_csv(OUT/"detail.csv",index=False)

    overall=[]
    monthly=[]
    headrows=[]
    branchrows=[]
    for name,g in f.groupby("variant"):
        overall.append({"variant":name,**metrics(g)})
        for mon,m in g.groupby("month"):
            monthly.append({"variant":name,"month":mon,**metrics(m)})
        h=g[g.head4.eq(1)]
        headrows.append({"variant":name,"head4_R":len(h),"capture":int(h.hit.sum()),
                         "capture_rate":float(h.hit.mean()),"avg_points":float(h.ticket_count.mean())})
        s=h[h.branch.eq("THREE_SURVIVES")]
        branchrows.append({"variant":name,"branch":"THREE_SURVIVES","R":len(s),"capture":int(s.hit.sum()),
                           "capture_rate":float(s.hit.mean()) if len(s) else None,
                           "modified_R":int(s.modified.sum()),"avg_points":float(s.ticket_count.mean()) if len(s) else None})
    odf=pd.DataFrame(overall); mdf=pd.DataFrame(monthly); hdf=pd.DataFrame(headrows); bdf=pd.DataFrame(branchrows)

    # Direct gain/loss against adopted INNER_CURRENT on the exact same races.
    base=f[f.variant.eq("INNER_CURRENT")][["race_code","hit"]].rename(columns={"hit":"base_hit"})
    delta=f.merge(base,on="race_code",how="left",validate="many_to_one")
    gains=(delta[(delta.variant.ne("INNER_CURRENT"))&(delta.hit.eq(1))&(delta.base_hit.eq(0))]
           .groupby("variant").size().rename("gained").reset_index())
    losses=(delta[(delta.variant.ne("INNER_CURRENT"))&(delta.hit.eq(0))&(delta.base_hit.eq(1))]
            .groupby("variant").size().rename("lost").reset_index())
    changes=gains.merge(losses,on="variant",how="outer").fillna(0)
    odf=odf.merge(changes,on="variant",how="left").fillna({"gained":0,"lost":0})

    # Keep the legacy 163 audit visible as reference, but do not treat it as current opponent policy.
    legacy={"R":int(len(d)),"hits":int(pd.to_numeric(d.hit,errors="coerce").fillna(0).sum()),
            "payout":float(pd.to_numeric(d.payout,errors="coerce").fillna(0).sum()),
            "stake":float(pd.to_numeric(d.stake,errors="coerce").fillna(0).sum())}
    legacy["roi"]=100*legacy["payout"]/legacy["stake"]

    odf.to_csv(OUT/"overall.csv",index=False); mdf.to_csv(OUT/"monthly.csv",index=False)
    hdf.to_csv(OUT/"head4_capture.csv",index=False); bdf.to_csv(OUT/"three_survives_capture.csv",index=False)
    meta={"frozen_bet_R":163,"legacy_v291_reference":legacy,
          "current_policy":"HEAD4_OPP_INNER_SURVIVE_ALWAYS_V1 + .11/.18",
          "structural_cut_source":"broad audit: Mar-May ALL races, q=.75, frozen before truth",
          "odds":"BoatraceCSV pre-deadline OD3 preferred; official closing fallback",
          "SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("THREE_SURVIVE_TICKET_SHADOW_OVERALL",odf.to_json(orient="records",force_ascii=False))
    print("THREE_SURVIVE_TICKET_SHADOW_MONTHLY",mdf.to_json(orient="records",force_ascii=False))
    print("THREE_SURVIVE_TICKET_SHADOW_HEAD4",hdf.to_json(orient="records",force_ascii=False))
    print("THREE_SURVIVE_TICKET_SHADOW_BRANCH",bdf.to_json(orient="records",force_ascii=False))
    print("THREE_SURVIVE_TICKET_SHADOW_META",json.dumps(meta,ensure_ascii=False))
    print("THREE_SURVIVE_TICKET_SHADOW_V1_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":
    main()
