#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle
from pathlib import Path
from datetime import date
import numpy as np
import pandas as pd
import run_1head_player_history_expansion as phbase
import research_4head_waku10_rel43_v4 as wsrc
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v1"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x)
        return v if np.isfinite(v) else np.nan
    except Exception:return np.nan

def ranks(vals,higher=True):
    a=[(b,ff(v)) for b,v in vals.items() if np.isfinite(ff(v))]
    a.sort(key=lambda z:(-z[1],z[0]) if higher else (z[1],z[0]))
    return {b:i+1 for i,(b,_) in enumerate(a)}

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
    codes={str(r["race_code"]).zfill(12) for r in dev}
    if any(c[:8]>="20260901" for c in codes): raise RuntimeError("September entered")
    root=os.environ.get("BOATRACECSV_LOCAL_ROOT")
    ph=phbase.build_canonical_ph_snapshots(codes,date(2025,10,1),date(2026,6,30),root)
    w=wsrc.build_waku(sorted(codes)); w["race_code"]=w.race_code.astype(str).str.zfill(12)
    widx=w.set_index("race_code",drop=False)

    rranks=[]; races=[]; pairs=[]; raw_keys=set(); head1=0
    for r in dev:
        raw_keys.update(r.keys())
        code=str(r["race_code"]).zfill(12); parts=str(r.get("actual_combo","")).split("-")
        if len(parts)!=3 or parts[0]!="1": continue
        try: sec,third=int(parts[1]),int(parts[2])
        except: continue
        if sec not in BOATS or third not in BOATS or sec==third: continue
        head1+=1
        phr=ph.get(code,{})
        wr=widx.loc[code] if code in widx.index else {}
        if isinstance(wr,pd.DataFrame): wr=wr.iloc[-1]
        p2,pc=v365.formal_post_five6(r)
        third_mass={}
        for t in BOATS:
            third_mass[t]=sum(ff(p2.get(s))*ff(pc.get((s,t))) for s in BOATS if s!=t and np.isfinite(ff(p2.get(s))) and np.isfinite(ff(pc.get((s,t)))))
        metrics={
          "MODEL_P2":({b:ff(p2.get(b)) for b in BOATS},True),
          "MODEL_SCORE":({b:ff(r.get(f"score{b}")) for b in BOATS},True),
          "START_SCORE":({b:ff(r.get(f"st{b}")) for b in BOATS},True),
          "PH_RECENT_P2":({b:ff(phr.get(f"b{b}_pl_recent_p2")) for b in BOATS},True),
          "PH_FRAME_P2":({b:ff(phr.get(f"b{b}_pl_frame_p2")) for b in BOATS},True),
          "PH_ALL_P2":({b:ff(phr.get(f"b{b}_pl_all_p2")) for b in BOATS},True),
          "PH_FRAME_WIN":({b:ff(phr.get(f"b{b}_pl_frame_win")) for b in BOATS},True),
          "WAKU_WR":({b:ff(wr.get(f"w10_b{b}_wr")) for b in BOATS},True),
          "WAKU_ST":({b:ff(wr.get(f"w10_b{b}_st")) for b in BOATS},False),
          "WAKU_START_RANK":({b:ff(wr.get(f"w10_b{b}_sr")) for b in BOATS},False),
          "WAKU_PASTWIN":({b:ff(wr.get(f"w10_b{b}_pastwin")) for b in BOATS},True),
          "INNER_LANE":({b:-b for b in BOATS},True),
          "MODEL_THIRD_MARGINAL":(third_mass,True),
        }
        sec_r={}; third_r={}
        for name,(vals,hi) in metrics.items():
            rm=ranks(vals,hi)
            for role,b,dct in (("SECOND",sec,sec_r),("THIRD",third,third_r)):
                rranks.append({"race_code":code,"month":code[:4]+"-"+code[4:6],"role":role,"boat":b,
                               "metric":name,"rank":rm.get(b),"value":ff(vals.get(b))})
                dct[name]=rm.get(b)
        cond={t:ff(pc.get((sec,t))) for t in BOATS if t!=sec}
        rm=ranks(cond,True); third_r["COND3_GIVEN_ACTUAL_SECOND"]=rm.get(third)
        rranks.append({"race_code":code,"month":code[:4]+"-"+code[4:6],"role":"THIRD","boat":third,
                       "metric":"COND3_GIVEN_ACTUAL_SECOND","rank":rm.get(third),"value":ff(cond.get(third))})

        top2=lambda d,k:int(d.get(k) is not None and d.get(k)<=2)
        def outer(b):
            if b<=2:return (0,0,0)
            st,sti=ff(r.get(f"st{b}")),ff(r.get(f"st{b-1}"))
            sc,sci=ff(r.get(f"score{b}")),ff(r.get(f"score{b-1}"))
            return (1,int(np.isfinite(st) and np.isfinite(sti) and st>sti),int(np.isfinite(sc) and np.isfinite(sci) and sc>sci))
        so=outer(sec); to=outer(third)
        races.append({
          "race_code":code,"month":code[:4]+"-"+code[4:6],"second":sec,"third":third,
          "second_strength_top2":top2(sec_r,"MODEL_SCORE"),"second_start_top2":top2(sec_r,"START_SCORE"),
          "second_model_top2":top2(sec_r,"MODEL_P2"),
          "second_history_top2":int(top2(sec_r,"PH_RECENT_P2") or top2(sec_r,"PH_FRAME_P2")),
          "second_waku_start_top2":int(top2(sec_r,"WAKU_ST") or top2(sec_r,"WAKU_START_RANK")),
          "third_strength_top2":top2(third_r,"MODEL_SCORE"),"third_start_top2":top2(third_r,"START_SCORE"),
          "third_mass_top2":top2(third_r,"MODEL_THIRD_MARGINAL"),"third_conditional_top2":top2(third_r,"COND3_GIVEN_ACTUAL_SECOND"),
          "third_history_top2":int(top2(third_r,"PH_RECENT_P2") or top2(third_r,"PH_FRAME_P2")),
          "third_waku_start_top2":int(top2(third_r,"WAKU_ST") or top2(third_r,"WAKU_START_RANK")),
          "second_outer":so[0],"second_start_beats_inner":so[1],"second_score_beats_inner":so[2],
          "third_outer":to[0],"third_start_beats_inner":to[1],"third_score_beats_inner":to[2],
        })
        pairs.append({"race_code":code,"pair":f"{sec}-{third}","second":sec,"third":third})

    rdf=pd.DataFrame(rranks); q=pd.DataFrame(races); pdf=pd.DataFrame(pairs)
    rdf.to_csv(OUT/"rank_records.csv",index=False); q.to_csv(OUT/"race_patterns.csv",index=False); pdf.to_csv(OUT/"pair_patterns.csv",index=False)
    sec_bucket={"strength_and_start":0,"strength_only":0,"start_only":0,"history_without_both":0,"other":0}
    tri_bucket={"conditional_and_start":0,"conditional_only":0,"start_only":0,"history_without_both":0,"other":0}
    for _,g in q.iterrows():
        s,t,h=bool(g.second_strength_top2),bool(g.second_start_top2),bool(g.second_history_top2)
        sec_bucket["strength_and_start" if s and t else "strength_only" if s else "start_only" if t else "history_without_both" if h else "other"]+=1
        c,t,h=bool(g.third_conditional_top2),bool(g.third_start_top2),bool(g.third_history_top2)
        tri_bucket["conditional_and_start" if c and t else "conditional_only" if c else "start_only" if t else "history_without_both" if h else "other"]+=1
    os2=q[q.second_outer.eq(1)]; os3=q[q.third_outer.eq(1)]
    summary={
      "population":"DEV H078_M375 where boat1 actually won","head1_R":head1,
      "second_lane_counts":{str(k):int(v) for k,v in q.second.value_counts().sort_index().items()},
      "third_lane_counts":{str(k):int(v) for k,v in q.third.value_counts().sort_index().items()},
      "top_pairs":[{"pair":str(k),"R":int(v)} for k,v in pdf["pair"].value_counts().head(15).items()],
      "second_metric_coverage":cov(rdf,"SECOND"),"third_metric_coverage":cov(rdf,"THIRD"),
      "second_explanation_buckets":sec_bucket,"third_explanation_buckets":tri_bucket,
      "outer_second":{"R":int(len(os2)),"start_beats_inner":int(os2.second_start_beats_inner.sum()),"score_beats_inner":int(os2.second_score_beats_inner.sum())},
      "outer_third":{"R":int(len(os3)),"start_beats_inner":int(os3.third_start_beats_inner.sum()),"score_beats_inner":int(os3.third_score_beats_inner.sum())},
      "prepared_row_keys":sorted(raw_keys),
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False,
      "conditional_note":"COND3_GIVEN_ACTUAL_SECOND is diagnostic only; actual second is post-race information."
    }
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_MECHANISM_SUMMARY",json.dumps(summary,ensure_ascii=False))

if __name__=="__main__":main()
