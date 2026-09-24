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
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v2"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except Exception:return np.nan

def cov(df,role):
    out=[]
    z=df[df.role.eq(role)]
    for metric,g in z.groupby("metric"):
        r=pd.to_numeric(g["rank"],errors="coerce")
        out.append({"role":role,"metric":metric,"R":int(r.notna().sum()),
                    "rank1":int((r==1).sum()),"rank1_rate":float((r==1).mean()),
                    "top2":int((r<=2).sum()),"top2_rate":float((r<=2).mean()),
                    "top3":int((r<=3).sum()),"top3_rate":float((r<=3).mean()),
                    "mean_rank":float(r.mean()) if r.notna().any() else None})
    return sorted(out,key=lambda x:(x["top2_rate"],x["rank1_rate"]),reverse=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--prepared",required=True,type=Path); a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb")); rr=x["rows"]
    if len(rr["H078_M375"])!=236: raise RuntimeError("frozen universe drift")
    dev=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
        if month in DEV: dev.append(r)
    codes=sorted({str(r["race_code"]).zfill(12) for r in dev})
    if any(c[:8]>="20260901" for c in codes): raise RuntimeError("September entered")

    # Same corrected pre-result exhibition builder used in prior v351 research.
    feat=w17.build_pre_result_strength(pd.DataFrame({"race_code":codes}))
    fi=feat.set_index(["race_code","boat"])

    rec=[]; pair_rows=[]; head1=0
    for r in dev:
        code=str(r["race_code"]).zfill(12); p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1": continue
        try: sec,third=int(p[1]),int(p[2])
        except: continue
        if sec not in BOATS or third not in BOATS or sec==third: continue
        if any((code,b) not in fi.index for b in BOATS): continue
        head1+=1
        p2,pc=v365.formal_post_five6(r)
        for role,b in (("SECOND",sec),("THIRD",third)):
            # model P2 / generic prepared metrics
            model_vals={bb:ff(p2.get(bb)) for bb in BOATS}
            prep_score={bb:ff(r.get(f"score{bb}")) for bb in BOATS}
            prep_st={bb:ff(r.get(f"st{bb}")) for bb in BOATS}
            for metric,vals,asc in (
                ("MODEL_P2",model_vals,False),
                ("PREP_SCORE",prep_score,False),
                ("PREP_ST_SCORE",prep_st,False),
            ):
                s=pd.Series(vals,dtype=float)
                rk=s.rank(method="average",ascending=asc)
                rec.append({"race_code":code,"role":role,"boat":b,"metric":metric,"rank":ff(rk.get(b))})
            f=fi.loc[(code,b)]
            for metric,col in (
                ("CORR_EXHIBITION","ex_rank"),
                ("CORR_EXHIBITION_ST","st_rank"),
                ("ORIG_TURN","turn_rank"),
                ("ORIG_STRAIGHT","straight_rank"),
                ("ORIG_AVG","orig_avg_rank"),
            ):
                rec.append({"race_code":code,"role":role,"boat":b,"metric":metric,"rank":ff(f[col])})
            rec.append({"race_code":code,"role":role,"boat":b,"metric":"EXHIBITION_COMPOSITE","rank":ff(f["strength_rank_mean"])})
        # conditional third probability rank after actual second (diagnostic only)
        cond={t:ff(pc.get((sec,t))) for t in BOATS if t!=sec}
        sr=pd.Series(cond,dtype=float).rank(method="average",ascending=False)
        rec.append({"race_code":code,"role":"THIRD","boat":third,"metric":"COND3_GIVEN_ACTUAL_SECOND","rank":ff(sr.get(third))})

        # pair-level: how often actual second/third are top2 in each family
        def rk(metric,role):
            for z in reversed(rec):
                if z["race_code"]==code and z["role"]==role and z["metric"]==metric:return z["rank"]
            return np.nan
        pair_rows.append({"race_code":code,"second":sec,"third":third,
            "second_p2_top2":int(rk("MODEL_P2","SECOND")<=2),
            "second_excomp_top2":int(rk("EXHIBITION_COMPOSITE","SECOND")<=2),
            "second_st_top2":int(rk("CORR_EXHIBITION_ST","SECOND")<=2),
            "second_turn_top2":int(rk("ORIG_TURN","SECOND")<=2),
            "second_straight_top2":int(rk("ORIG_STRAIGHT","SECOND")<=2),
            "third_cond_top2":int(rk("COND3_GIVEN_ACTUAL_SECOND","THIRD")<=2),
            "third_excomp_top2":int(rk("EXHIBITION_COMPOSITE","THIRD")<=2),
            "third_st_top2":int(rk("CORR_EXHIBITION_ST","THIRD")<=2),
            "third_turn_top2":int(rk("ORIG_TURN","THIRD")<=2),
            "third_straight_top2":int(rk("ORIG_STRAIGHT","THIRD")<=2),
        })

    rdf=pd.DataFrame(rec); q=pd.DataFrame(pair_rows)
    rdf.to_csv(OUT/"rank_records.csv",index=False); q.to_csv(OUT/"pair_level.csv",index=False)
    second=cov(rdf,"SECOND"); third=cov(rdf,"THIRD")

    # Overlap: does corrected exhibition add information beyond MODEL_P2?
    overlap={}
    for role in ("SECOND","THIRD"):
        z=rdf[rdf.role.eq(role)].pivot(index="race_code",columns="metric",values="rank")
        def cnt(mask): return int(mask.fillna(False).sum())
        if "MODEL_P2" in z and "EXHIBITION_COMPOSITE" in z:
            p=z.MODEL_P2<=2; e=z.EXHIBITION_COMPOSITE<=2
            overlap[role]={
              "R":int(len(z)),
              "p2_top2":cnt(p),"excomp_top2":cnt(e),
              "both":cnt(p&e),"p2_only":cnt(p&~e),"excomp_only":cnt(~p&e),"neither":cnt(~p&~e)
            }

    # If second is already P2 top2, how good is conditional third?
    q2=q[q.second_p2_top2.eq(1)]
    qbad=q[q.second_p2_top2.eq(0)]
    summary={
      "population":"DEV H078_M375 where boat1 actually won and corrected exhibition complete",
      "head1_R":int(head1),
      "second_metric_coverage":second,
      "third_metric_coverage":third,
      "overlap":overlap,
      "conditional_third_when_second_p2_top2":{
        "R":int(len(q2)),"third_cond_top2":int(q2.third_cond_top2.sum()),
        "rate":float(q2.third_cond_top2.mean()) if len(q2) else None},
      "conditional_third_when_second_p2_not_top2":{
        "R":int(len(qbad)),"third_cond_top2":int(qbad.third_cond_top2.sum()),
        "rate":float(qbad.third_cond_top2.mean()) if len(qbad) else None},
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False,
      "conditional_note":"COND3_GIVEN_ACTUAL_SECOND is diagnostic only because actual second is post-race information."
    }
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_MECHANISM_V2",json.dumps(summary,ensure_ascii=False))

if __name__=="__main__":main()
