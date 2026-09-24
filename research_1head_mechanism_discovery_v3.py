#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365
import analyze_v351_mass_rescue_wave17_boat5_third_rescue as w17

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v3"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def rate_table(df, flags):
    out=[]
    for f in flags:
        if f not in df: continue
        for val,g in df.groupby(f):
            if pd.isna(val): continue
            out.append({"feature":f,"value":int(val) if float(val).is_integer() else float(val),
                        "R":int(len(g)),"outer_second":int(g.outer_second.sum()),
                        "outer_rate":float(g.outer_second.mean())})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--prepared",required=True,type=Path); a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb")); rr=x["rows"]
    dev=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
        if month in DEV: dev.append(r)
    codes=sorted({str(r["race_code"]).zfill(12) for r in dev})
    if any(c[:8]>="20260901" for c in codes): raise RuntimeError("September entered")
    feat=w17.build_pre_result_strength(pd.DataFrame({"race_code":codes}))
    fi=feat.set_index(["race_code","boat"])

    rows=[]
    for r in dev:
        code=str(r["race_code"]).zfill(12); p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1": continue
        try: sec=int(p[1])
        except: continue
        if sec not in BOATS or any((code,b) not in fi.index for b in BOATS): continue
        p2,pc=v365.formal_post_five6(r)
        inner=(2,3); outer=(4,5,6)
        score={b:ff(r.get(f"score{b}")) for b in BOATS}
        stscore={b:ff(r.get(f"st{b}")) for b in BOATS}
        p2v={b:ff(p2.get(b)) for b in BOATS}
        ex={b:ff(fi.loc[(code,b),"ex"]) for b in BOATS}
        cst={b:ff(fi.loc[(code,b),"st"]) for b in BOATS}
        turn={b:ff(fi.loc[(code,b),"turn"]) for b in BOATS}
        straight={b:ff(fi.loc[(code,b),"straight"]) for b in BOATS}
        oavg={b:ff(fi.loc[(code,b),"orig_avg"]) for b in BOATS}
        comp={b:ff(fi.loc[(code,b),"strength_rank_mean"]) for b in BOATS}

        def vmax(d,bs): return max((d[b] for b in bs if np.isfinite(d[b])),default=np.nan)
        def vmin(d,bs): return min((d[b] for b in bs if np.isfinite(d[b])),default=np.nan)
        def best_outer(d,higher=True):
            vals=[(b,d[b]) for b in outer if np.isfinite(d[b])]
            if not vals:return None
            return (max(vals,key=lambda z:z[1]) if higher else min(vals,key=lambda z:z[1]))[0]
        def edge_low(d,a,b):
            return ff(d[a]-d[b]) if np.isfinite(d[a]) and np.isfinite(d[b]) else np.nan
        row={
          "race_code":code,"month":code[:4]+"-"+code[4:6],"actual_second":sec,
          "outer_second":int(sec>=4),
          "attack_ready":int(bool(r.get("attack_ready",False))),"attack_core":ff(r.get("attack_core")),
          "opp_mass":ff(r.get("opp_mass")),
          "outer_p2_gap":vmax(p2v,outer)-vmax(p2v,inner),
          "outer_score_gap":vmax(score,outer)-vmax(score,inner),
          "outer_stscore_gap":vmax(stscore,outer)-vmax(stscore,inner),
          "outer_ex_gap":vmin(ex,outer)-vmin(ex,inner),
          "outer_cst_gap":vmin(cst,outer)-vmin(cst,inner),
          "outer_turn_gap":vmin(turn,outer)-vmin(turn,inner),
          "outer_straight_gap":vmin(straight,outer)-vmin(straight,inner),
          "outer_oavg_gap":vmin(oavg,outer)-vmin(oavg,inner),
          "outer_comp_gap":vmin(comp,outer)-vmin(comp,inner),
          "edge43_comp":edge_low(comp,4,3),"edge54_comp":edge_low(comp,5,4),"edge65_comp":edge_low(comp,6,5),
          "edge43_cst":edge_low(cst,4,3),"edge54_cst":edge_low(cst,5,4),"edge65_cst":edge_low(cst,6,5),
          "edge43_turn":edge_low(turn,4,3),"edge54_turn":edge_low(turn,5,4),"edge65_turn":edge_low(turn,6,5),
          "edge43_straight":edge_low(straight,4,3),"edge54_straight":edge_low(straight,5,4),"edge65_straight":edge_low(straight,6,5),
          "actual_is_best_outer_p2":int(sec>=4 and sec==best_outer(p2v,True)),
          "actual_is_best_outer_score":int(sec>=4 and sec==best_outer(score,True)),
          "actual_is_best_outer_stscore":int(sec>=4 and sec==best_outer(stscore,True)),
          "actual_is_best_outer_ex":int(sec>=4 and sec==best_outer(ex,False)),
          "actual_is_best_outer_cst":int(sec>=4 and sec==best_outer(cst,False)),
          "actual_is_best_outer_turn":int(sec>=4 and sec==best_outer(turn,False)),
          "actual_is_best_outer_straight":int(sec>=4 and sec==best_outer(straight,False)),
          "actual_is_best_outer_comp":int(sec>=4 and sec==best_outer(comp,False)),
        }
        # interpretable binary flags
        for k in ("p2","score","stscore"):
            row[f"{k}_outer_beats_inner"]=int(np.isfinite(row[f"outer_{k}_gap"]) and row[f"outer_{k}_gap"]>0)
        for k in ("ex","cst","turn","straight","oavg","comp"):
            row[f"{k}_outer_beats_inner"]=int(np.isfinite(row[f"outer_{k}_gap"]) and row[f"outer_{k}_gap"]<0)
        row["any_adjacent_outer_comp_edge"]=int(any(np.isfinite(row[k]) and row[k]<0 for k in ("edge43_comp","edge54_comp","edge65_comp")))
        row["any_adjacent_outer_cst_edge"]=int(any(np.isfinite(row[k]) and row[k]<0 for k in ("edge43_cst","edge54_cst","edge65_cst")))
        row["any_adjacent_outer_turn_edge"]=int(any(np.isfinite(row[k]) and row[k]<0 for k in ("edge43_turn","edge54_turn","edge65_turn")))
        row["any_adjacent_outer_straight_edge"]=int(any(np.isfinite(row[k]) and row[k]<0 for k in ("edge43_straight","edge54_straight","edge65_straight")))
        rows.append(row)

    q=pd.DataFrame(rows); q.to_csv(OUT/"race_rows.csv",index=False)
    flags=[c for c in q.columns if c.endswith("_beats_inner") or c.startswith("any_adjacent_") or c=="attack_ready"]
    binary=rate_table(q,flags)
    pd.DataFrame(binary).to_csv(OUT/"binary_rate_table.csv",index=False)

    outer=q[q.outer_second.eq(1)]
    best_outer={}
    for c in [x for x in q.columns if x.startswith("actual_is_best_outer_")]:
        best_outer[c]={"R":int(len(outer)),"hits":int(outer[c].sum()),"rate":float(outer[c].mean()) if len(outer) else None}

    # quantile direction scans, descriptive only
    scans=[]
    cont=["outer_p2_gap","outer_score_gap","outer_stscore_gap","outer_ex_gap","outer_cst_gap","outer_turn_gap","outer_straight_gap","outer_oavg_gap","outer_comp_gap","attack_core","opp_mass"]
    for c in cont:
        s=pd.to_numeric(q[c],errors="coerce")
        good=s.notna()
        if good.sum()<30: continue
        for quant in (.2,.4,.6,.8):
            t=float(s[good].quantile(quant))
            for side in ("ge","le"):
                m=good & ((s>=t) if side=="ge" else (s<=t))
                if m.sum()<10: continue
                scans.append({"feature":c,"q":quant,"side":side,"threshold":t,"R":int(m.sum()),
                              "outer_second":int(q.loc[m,"outer_second"].sum()),
                              "outer_rate":float(q.loc[m,"outer_second"].mean())})
    pd.DataFrame(scans).sort_values(["outer_rate","R"],ascending=[False,False]).to_csv(OUT/"quantile_scan.csv",index=False)

    monthly=[]
    for m,g in q.groupby("month"):
        monthly.append({"month":m,"R":int(len(g)),"outer_second":int(g.outer_second.sum()),"outer_rate":float(g.outer_second.mean())})
    summary={
      "population":"DEV head1 wins; classify SECOND as inner(2/3) vs outer(4/5/6)",
      "R":int(len(q)),"outer_second_R":int(q.outer_second.sum()),"outer_second_rate":float(q.outer_second.mean()),
      "actual_second_counts":{str(k):int(v) for k,v in q.actual_second.value_counts().sort_index().items()},
      "monthly":monthly,"binary_rate_table":binary,"best_outer_identity":best_outer,
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False
    }
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_OUTER_SECOND_V3",json.dumps(summary,ensure_ascii=False))

if __name__=="__main__":main()
