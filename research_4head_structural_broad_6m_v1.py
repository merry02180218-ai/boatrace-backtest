#!/usr/bin/env python3
"""Broad six-month structural audit for 4HEAD opponent regimes.

Purpose:
- Increase sample size beyond the frozen 81 head4 production subset.
- Build branch scores on ALL struct-ready Mar-Aug races.
- Fit feature scaling and structural cuts from Mar-May pre-race features only.
- Freeze branches before attaching top-3 outcomes.
- Evaluate only after freeze on actual 4-head races from Mar-Aug.
- September outcomes remain unread. Research only; no production mutation.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

import audit_4head_ph5_live_walkforward as parent
import research_4head_player_waku_soft_ablation_v23 as phsrc
import research_4head_waku10_rel43_v4 as wsrc

OUT=Path("/tmp/head4_structural_broad_6m_v1"); OUT.mkdir(parents=True,exist_ok=True)
PARENT=Path("/tmp/head4_6m_parent/parent.csv")
V93=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv")
BOATS=(1,2,3,5,6)
CAL_MONTHS={"2026-03","2026-04","2026-05"}

def wilson(k,n,z=1.96):
    if not n: return (np.nan,np.nan)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d
    return (max(0.0,c-h),min(1.0,c+h))

def main():
    strict=pd.read_csv(PARENT,dtype={"race_code":str})
    strict["race_code"]=strict.race_code.astype(str).str.zfill(12)
    strict=strict[(strict.month>="2026-03")&(strict.month<="2026-08")].copy()
    v=pd.read_csv(V93,dtype={"race_code":str})
    v["race_code"]=v.race_code.astype(str).str.zfill(12)
    v=v[v.race_code.isin(set(strict.race_code))].copy()
    if set(v.race_code)!=set(strict.race_code):
        raise RuntimeError(f"V93_COVERAGE_{v.race_code.nunique()}/{len(strict)}")

    # Build current opponent SECOND probabilities for every struct-ready race.
    long=parent.v283build.build_long_all(v)
    long=parent.add_start_features(long)
    art=parent.load_artifact()
    sf=list(art["v283_SECOND"]["features"])
    p2rows=[]
    for code,g in long.groupby("race_code",sort=False):
        sr=[]
        for _,r in g.iterrows():
            x={"boat":int(r.boat)}
            for f in sf:
                if f not in r: raise RuntimeError(f"SECOND_FEATURE_MISSING_{f}")
                x[f]=r[f]
            sr.append(x)
        p2=parent.score_second(sr,art)
        rec={"race_code":code}
        for b in BOATS: rec[f"b{b}_p2"]=float(p2[b])
        p2rows.append(rec)
    p2wide=pd.DataFrame(p2rows)

    # Causal pre-race PLAYERHistory and Waku10.
    ph=phsrc.build_ph(); ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
    w=wsrc.build_waku(strict.race_code.tolist()); w["race_code"]=w.race_code.astype(str).str.zfill(12)

    # Branch construction universe is all races. No head4/top3 filtering here.
    x=strict[["race_code","date","month"]].merge(p2wide,on="race_code",how="left",validate="one_to_one")
    x=x.merge(ph,on="race_code",how="left",validate="one_to_one").merge(w,on="race_code",how="left",validate="one_to_one")
    if len(x)!=len(strict): raise RuntimeError("STRUCTURAL_UNIVERSE_DRIFT")

    lane_metrics=["p2","pl_frame_p2","pl_recent_p2","w10_wr","w10_sr","w10_rel4_wr"]
    rawcols={}
    for b in (1,2,3):
        rawcols[(b,"p2")]=f"b{b}_p2"
        rawcols[(b,"pl_frame_p2")]=f"b{b}_pl_frame_p2"
        rawcols[(b,"pl_recent_p2")]=f"b{b}_pl_recent_p2"
        rawcols[(b,"w10_wr")]=f"w10_b{b}_wr"
        rawcols[(b,"w10_sr")]=f"w10_b{b}_sr"
        rawcols[(b,"w10_rel4_wr")]=f"w10_rel4_b{b}_wr"

    cal=x[x.month.isin(CAL_MONTHS)].copy()
    if not len(cal): raise RuntimeError("NO_MAR_MAY_CALIBRATION")
    stats={}
    for key,col in rawcols.items():
        s=pd.to_numeric(cal[col],errors="coerce")
        med=float(s.median()) if s.notna().any() else 0.0
        q=s.fillna(med); mu=float(q.mean()); sd=float(q.std())
        if not math.isfinite(sd) or sd<1e-9: sd=1.0
        stats[col]={"median":med,"mean":mu,"std":sd}
        a=pd.to_numeric(x[col],errors="coerce").fillna(med)
        x[f"z_{col}"]=(a-mu)/sd

    for b in (1,2,3):
        zcols=[f"z_{rawcols[(b,m)]}" for m in lane_metrics]
        x[f"wall_b{b}_strength"]=x[zcols].mean(axis=1)
        x[f"wall_b{b}_collapse"]=-x[f"wall_b{b}_strength"]
    x["wall_32break"]=(x.wall_b3_collapse+x.wall_b2_collapse)/2

    # Cuts are feature-only and frozen from Mar-May ALL races, not outcome-conditioned.
    cal=x[x.month.isin(CAL_MONTHS)]
    strong3_cut=float(cal.wall_b3_strength.quantile(.75))
    break32_cut=float(cal.wall_32break.quantile(.50))
    def branch(r):
        if r.wall_b3_strength>=strong3_cut: return "THREE_SURVIVES"
        if r.wall_32break>=break32_cut: return "THREE_TWO_BREAK"
        return "MIXED_INNER"
    x["struct_branch"]=x.apply(branch,axis=1)

    # Only after branch freeze do we attach top-3 outcomes.
    truth=parent.truth()
    trows=[]
    for code,a in truth.items():
        trows.append({"race_code":code,"winner":int(a[0]),"actual_second":int(a[1]),"actual_third":int(a[2])})
    t=pd.DataFrame(trows)
    e=x.merge(t,on="race_code",how="left",validate="one_to_one")
    e=e[e.winner.eq(4)].copy()
    if not len(e): raise RuntimeError("NO_HEAD4_TRUTH")

    e["three_second"]=e.actual_second.eq(3).astype(int)
    e["three_any"]=((e.actual_second.eq(3))|(e.actual_third.eq(3))).astype(int)
    e["five_second"]=e.actual_second.eq(5).astype(int)
    e["five_any"]=((e.actual_second.eq(5))|(e.actual_third.eq(5))).astype(int)

    rows=[]
    for mon,g0 in e.groupby("month"):
        for br,g in g0.groupby("struct_branch"):
            r={"month":mon,"branch":br,"R":len(g)}
            for name in ("three_second","three_any","five_second","five_any"):
                k=int(g[name].sum()); lo,hi=wilson(k,len(g))
                r[name+"_R"]=k; r[name+"_rate"]=k/len(g); r[name+"_lo95"]=lo; r[name+"_hi95"]=hi
            rows.append(r)
    monthly=pd.DataFrame(rows)
    monthly.to_csv(OUT/"branch_monthly.csv",index=False)

    allrows=[]
    for label,q in [
        ("MAR_MAY",e[e.month.isin(CAL_MONTHS)]),
        ("JUNE",e[e.month.eq("2026-06")]),
        ("JUL_AUG",e[e.month.isin(["2026-07","2026-08"])]),
        ("MAR_AUG",e),
    ]:
        for br,g in q.groupby("struct_branch"):
            allrows.append({"period":label,"branch":br,"R":len(g),
                "three_second_R":int(g.three_second.sum()),"three_second_rate":float(g.three_second.mean()),
                "three_any_R":int(g.three_any.sum()),"three_any_rate":float(g.three_any.mean()),
                "five_second_R":int(g.five_second.sum()),"five_second_rate":float(g.five_second.mean()),
                "five_any_R":int(g.five_any.sum()),"five_any_rate":float(g.five_any.mean())})
    summary=pd.DataFrame(allrows)
    summary.to_csv(OUT/"branch_period_summary.csv",index=False)

    # Direct branch contrast, useful for checking whether the signal has the same sign by month.
    contrasts=[]
    for mon,g in e.groupby("month"):
        b=g[g.struct_branch.eq("THREE_TWO_BREAK")]
        o=g[~g.struct_branch.eq("THREE_TWO_BREAK")]
        s=g[g.struct_branch.eq("THREE_SURVIVES")]
        ns=g[~g.struct_branch.eq("THREE_SURVIVES")]
        contrasts.append({"month":mon,"head4_R":len(g),
            "break_R":len(b),"break_5second":float(b.five_second.mean()) if len(b) else np.nan,
            "other_5second":float(o.five_second.mean()) if len(o) else np.nan,
            "break_5second_lift":float(b.five_second.mean()-o.five_second.mean()) if len(b) and len(o) else np.nan,
            "survive_R":len(s),"survive_3second":float(s.three_second.mean()) if len(s) else np.nan,
            "other_3second":float(ns.three_second.mean()) if len(ns) else np.nan,
            "survive_3second_lift":float(s.three_second.mean()-ns.three_second.mean()) if len(s) and len(ns) else np.nan})
    contrast=pd.DataFrame(contrasts)
    contrast.to_csv(OUT/"monthly_contrast.csv",index=False)

    meta={"universe_R":int(len(x)),"head4_R":int(len(e)),
          "calibration":"Mar-May ALL struct-ready races; pre-race features only",
          "strong3_q":.75,"strong3_cut":strong3_cut,"break32_q":.50,"break32_cut":break32_cut,
          "scaler_fit":"Mar-May ALL races, before top3 truth join",
          "feature_stats":stats,"RESULT_ATTACHED_AFTER_BRANCH_FREEZE":True,
          "SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("STRUCTURAL_BROAD_6M_MONTHLY",monthly.to_json(orient="records",force_ascii=False))
    print("STRUCTURAL_BROAD_6M_SUMMARY",summary.to_json(orient="records",force_ascii=False))
    print("STRUCTURAL_BROAD_6M_CONTRAST",contrast.to_json(orient="records",force_ascii=False))
    print("STRUCTURAL_BROAD_6M_META",json.dumps({k:v for k,v in meta.items() if k!="feature_stats"},ensure_ascii=False))
    print("STRUCTURAL_BROAD_6M_V1_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":
    main()
