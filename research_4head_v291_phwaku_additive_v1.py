#!/usr/bin/env python3
"""Additive PH/Waku research on the exact frozen v291 opponent baseline.

Rules:
- v291 stored tickets are immutable baseline; never delete/reorder them.
- Candidate rescue is ONLY the raw-p2 rank3 SECOND when v291 excluded it (gap > .11).
- PLAYERHistory/Waku10 supplies pre-race support only.
- June thresholds are feature-only q75 values computed from June production candidates;
  no June result is used to choose the threshold.
- Jul-Aug are holdout. September outcomes remain unread.
- Research only; no production mutation.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

import audit_4head_ph5_live_walkforward as parent
import research_4head_player_waku_soft_ablation_v23 as phsrc
import research_4head_waku10_rel43_v4 as wsrc
import run_4head_v291_third010_live as dutchmod

OUT=Path("/tmp/head4_v291_phwaku_additive_v1"); OUT.mkdir(parents=True,exist_ok=True)
BASE=Path("/tmp/head4_ph5_live_walkforward/race_detail.csv")
BOATS=(1,2,3,5,6)
SECOND_GAP=.11
MAX_TICKETS=dutchmod.MAX_TICKETS

def zmap(vals):
    a=np.asarray([float(vals[b]) if pd.notna(vals[b]) and math.isfinite(float(vals[b])) else np.nan for b in BOATS],float)
    med=float(np.nanmedian(a)) if np.isfinite(a).any() else 0.0
    a=np.where(np.isfinite(a),a,med)
    mu=float(a.mean()); sd=float(a.std(ddof=1))
    if not math.isfinite(sd) or sd<1e-9: sd=1.0
    return {b:(float(a[i])-mu)/sd for i,b in enumerate(BOATS)}

def fnum(v):
    try:
        x=float(v); return x if math.isfinite(x) else np.nan
    except:return np.nan

def main():
    d=pd.read_csv(BASE,dtype={"race_code":str}); d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.production_bet.eq(1)].copy()
    if len(d)!=163: raise RuntimeError(f"FROZEN_163_DRIFT_{len(d)}")

    ph=phsrc.build_ph(); ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
    w=wsrc.build_waku(d.race_code.tolist()); w["race_code"]=w.race_code.astype(str).str.zfill(12)
    q=d.merge(ph,on="race_code",how="left",validate="one_to_one").merge(w,on="race_code",how="left",validate="one_to_one")

    # Build all candidate/support fields before reading outcomes.
    pre=[]
    for _,r in q.iterrows():
        diag=json.loads(r.opponent_diag)
        p2={int(k):float(v) for k,v in diag["p2"].items()}
        pc={(int(k.split(">")[0]),int(k.split(">")[1])):float(v) for k,v in diag["pc"].items()}
        rank=sorted(BOATS,key=lambda b:(-p2[b],b))
        s3=rank[2]; raw_gap=p2[rank[1]]-p2[rank[2]]
        base=[x for x in str(r.tickets).split("|") if x]
        base_secs={int(x.split("-")[1]) for x in base}
        eligible=int(raw_gap>SECOND_GAP and s3 not in base_secs)

        pl_frame={b:fnum(r.get(f"b{b}_pl_frame_p2")) for b in BOATS}
        pl_recent={b:fnum(r.get(f"b{b}_pl_recent_p2")) for b in BOATS}
        wr={b:fnum(r.get(f"w10_b{b}_wr")) for b in BOATS}
        sr={b:fnum(r.get(f"w10_b{b}_sr")) for b in BOATS}
        rel={b:fnum(r.get(f"w10_rel4_b{b}_wr")) for b in BOATS}
        zpf,zpr,zwr,zsr,zrel=zmap(pl_frame),zmap(pl_recent),zmap(wr),zmap(sr),zmap(rel)
        inner_bonus=(zpf[s3]+zwr[s3]-zrel[s3])/3.0
        inner_bonus*=1.0 if s3 in (1,2,3) else -0.35
        combo_bonus=(zpf[s3]+zpr[s3]+zwr[s3]+zsr[s3]+zrel[s3])/5.0

        thirds=sorted((t for t in BOATS if t!=s3),key=lambda t:(-pc[(s3,t)],t))
        cand=[f"4-{s3}-{t}" for t in thirds[:2]]
        pre.append({"race_code":r.race_code,"date":str(r.date),"month":str(r.date)[:7],
                    "base_tickets":"|".join(base),"base_n":len(base),"candidate_second":s3,
                    "raw_gap23":raw_gap,"eligible":eligible,"inner_bonus":inner_bonus,
                    "combo_bonus":combo_bonus,"cand1":cand[0],"cand2":cand[1]})
    p=pd.DataFrame(pre)
    p.to_csv(OUT/"pre_result_candidates.csv",index=False)

    j=p[(p.month.eq("2026-06")) & p.eligible.eq(1)].copy()
    if len(j)<8: raise RuntimeError(f"TOO_FEW_JUNE_CANDIDATES_{len(j)}")
    inner_cut=float(j.inner_bonus.quantile(.75))
    combo_cut=float(j.combo_bonus.quantile(.75))

    variants=[
      ("V291_BASE",None,0),
      ("PHW_INNER_Q75_ADD1","inner_bonus",1),
      ("PHW_INNER_Q75_ADD2","inner_bonus",2),
      ("PHW_COMBO_Q75_ADD1","combo_bonus",1),
      ("PHW_COMBO_Q75_ADD2","combo_bonus",2),
    ]
    cuts={"inner_bonus":inner_cut,"combo_bonus":combo_cut}

    frozen=[]
    for _,r in p.iterrows():
        base=[x for x in r.base_tickets.split("|") if x]
        for name,sig,nadd in variants:
            ts=list(base)
            selected=False
            if sig is not None and int(r.eligible)==1 and float(r[sig])>=cuts[sig]:
                selected=True
                for x in [r.cand1,r.cand2][:nadd]:
                    if x not in ts and len(ts)<MAX_TICKETS: ts.append(x)
            frozen.append({"race_code":r.race_code,"date":r.date,"month":r.month,"variant":name,
                           "tickets":"|".join(ts),"ticket_count":len(ts),"modified":int(ts!=base),
                           "signal_selected":int(selected),"candidate_second":int(r.candidate_second),
                           "raw_gap23":float(r.raw_gap23),"inner_bonus":float(r.inner_bonus),
                           "combo_bonus":float(r.combo_bonus)})
    f=pd.DataFrame(frozen)
    if len(f)!=163*len(variants): raise RuntimeError("FROZEN_VARIANT_COUNT_DRIFT")

    # Outcomes are attached only after every variant is frozen.
    tr=parent.truth(); om=parent.od3()
    hits=[]; heads=[]; payouts=[]; stakes=[]; actuals=[]
    for _,r in f.iterrows():
        a=tr.get(r.race_code)
        actual=f"{a[0]}-{a[1]}-{a[2]}" if a else ""
        head=int(bool(a) and a[0]==4)
        ts=[x for x in r.tickets.split("|") if x]
        odds=om.get(r.race_code,{})
        if any(t not in odds for t in ts): raise RuntimeError(f"ODDS_MISSING_{r.race_code}_{r.variant}")
        plan=dutchmod.dutch(ts,[odds[t] for t in ts])
        stake=sum(int(x["stake"]) for x in plan)
        pay=0.0; hit=0
        if a:
            for x in plan:
                if x["combo"]==actual:
                    hit=1; pay=float(x["stake"])*float(x["odds"]); break
        hits.append(hit); heads.append(head); payouts.append(pay); stakes.append(stake); actuals.append(actual)
    f["head4"]=heads; f["hit"]=hits; f["payout"]=payouts; f["stake"]=stakes; f["actual"]=actuals
    f.to_csv(OUT/"detail.csv",index=False)

    rows=[]; monthly=[]; hold=[]
    basehit=f[f.variant.eq("V291_BASE")][["race_code","hit"]].rename(columns={"hit":"base_hit"})
    x=f.merge(basehit,on="race_code",how="left",validate="many_to_one")
    for name,g in x.groupby("variant"):
        rows.append({"variant":name,"R":len(g),"hits":int(g.hit.sum()),"stake":int(g.stake.sum()),
                     "payout":float(g.payout.sum()),"roi":float(100*g.payout.sum()/g.stake.sum()),
                     "avg_points":float(g.ticket_count.mean()),"modified_R":int(g.modified.sum()),
                     "gained":int(((g.hit==1)&(g.base_hit==0)).sum()),"lost":int(((g.hit==0)&(g.base_hit==1)).sum())})
        for mon,m in g.groupby("month"):
            monthly.append({"variant":name,"month":mon,"R":len(m),"hits":int(m.hit.sum()),
                            "roi":float(100*m.payout.sum()/m.stake.sum()),"avg_points":float(m.ticket_count.mean()),
                            "modified_R":int(m.modified.sum())})
        h=g[(g.month.isin(["2026-07","2026-08"])) & g.head4.eq(1)]
        hold.append({"variant":name,"holdout_head4_R":len(h),"capture":int(h.hit.sum()),
                     "capture_rate":float(h.hit.mean()) if len(h) else None,
                     "avg_points":float(h.ticket_count.mean()) if len(h) else None,
                     "modified_R":int(h.modified.sum())})
    odf=pd.DataFrame(rows); mdf=pd.DataFrame(monthly); hdf=pd.DataFrame(hold)
    odf.to_csv(OUT/"overall.csv",index=False); mdf.to_csv(OUT/"monthly.csv",index=False); hdf.to_csv(OUT/"holdout_head4.csv",index=False)

    meta={"baseline":"stored frozen v291 tickets, exact production parity",
          "candidate":"raw-p2 rank3 SECOND excluded because gap23 > .11",
          "threshold_source":"June production candidates, feature-only q75; no outcome tuning",
          "june_candidate_R":int(len(j)),"inner_q75":inner_cut,"combo_q75":combo_cut,
          "SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("V291_PHW_ADDITIVE_OVERALL",odf.to_json(orient="records",force_ascii=False))
    print("V291_PHW_ADDITIVE_MONTHLY",mdf.to_json(orient="records",force_ascii=False))
    print("V291_PHW_ADDITIVE_HOLDOUT",hdf.to_json(orient="records",force_ascii=False))
    print("V291_PHW_ADDITIVE_META",json.dumps(meta,ensure_ascii=False))
    print("V291_PHW_ADDITIVE_V1_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":
    main()
