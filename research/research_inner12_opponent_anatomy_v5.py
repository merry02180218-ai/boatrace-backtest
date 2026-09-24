#!/usr/bin/env python3
"""Opponent anatomy for frozen INNER12 operational Shadow V4.

Decision is frozen BEFORE results are joined:
- A_only -> heads 3 and 4
- B_only + prior recent3 inner ST absdiff >= .04 -> head 3
- otherwise PASS

Then historical results are joined only for descriptive opponent anatomy.
This script must not mutate the head gate from outcome information.
September outcomes are never read.
"""
from __future__ import annotations
import csv, json, os
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

V2=Path(os.environ.get("INNER12_V2_ROWS","/tmp/v2/shadow_v2_all_base_rows.csv"))
BRC_ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
OUT=Path(os.environ.get("INNER12_OPP_OUTDIR","/tmp/inner12_opponent_anatomy_v5"))
OUT.mkdir(parents=True,exist_ok=True)

MONTHS=("2026-06","2026-07","2026-08")
B_STRONG_GAP=.04

def read_results(day:str):
    y,m,d=day.split("-")
    p=BRC_ROOT/f"data/results/realtime/{y}/{m}/{d}.csv"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8-sig",newline="") as fh:
        rs=list(csv.DictReader(fh))
    out={}
    for r in rs:
        code=str(r.get("レースコード","")).strip().zfill(12)
        if not code: continue
        try:
            out[code]=(int(float(r["1着_艇番"])),int(float(r["2着_艇番"])),int(float(r["3着_艇番"])))
        except Exception:
            continue
    return out

def freq(counter,total):
    return [{"boat":int(k),"N":int(v),"rate":float(v/total) if total else None}
            for k,v in sorted(counter.items(),key=lambda kv:(-kv[1],kv[0]))]

def pairfreq(counter,total):
    return [{"pair":k,"N":int(v),"rate":float(v/total) if total else None}
            for k,v in sorted(counter.items(),key=lambda kv:(-kv[1],kv[0]))]

def main():
    if not V2.exists():raise RuntimeError(f"MISSING_V2_{V2}")
    d=pd.read_csv(V2,dtype={"race_code":str})
    d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.month.isin(MONTHS)].copy()

    # Freeze decisions first.
    d["action"]="PASS"; d["heads"]=""
    d.loc[d.branch_name.eq("A_only"),"action"]="A_DUAL_3_4"
    d.loc[d.branch_name.eq("A_only"),"heads"]="3|4"
    gap=pd.to_numeric(d["pre_pair_absdiff_prior_recent3_st"],errors="coerce")
    bstrong=d.branch_name.eq("B_only") & gap.ge(B_STRONG_GAP)
    d.loc[bstrong,"action"]="B_3HEAD"
    d.loc[bstrong,"heads"]="3"
    frozen=d[d.action.ne("PASS")].copy()
    frozen["decision_frozen_before_results"]=1

    # Only after decisions are frozen, join top3 outcomes.
    cache={}
    actual=[]
    for r in frozen.itertuples():
        day=str(r.date)
        if day not in cache: cache[day]=read_results(day)
        z=cache[day].get(str(r.race_code))
        actual.append(z)
    frozen["actual_top3"]=actual
    frozen=frozen[frozen.actual_top3.notna()].copy()
    frozen["actual_head"]=frozen.actual_top3.map(lambda z:int(z[0]))
    frozen["actual_second"]=frozen.actual_top3.map(lambda z:int(z[1]))
    frozen["actual_third"]=frozen.actual_top3.map(lambda z:int(z[2]))
    frozen["head_hit"]=[
        int(str(h) in str(heads).split("|"))
        for h,heads in zip(frozen.actual_head,frozen.heads)
    ]

    groups={
        "A_head3": frozen[(frozen.action=="A_DUAL_3_4")&(frozen.actual_head==3)],
        "A_head4": frozen[(frozen.action=="A_DUAL_3_4")&(frozen.actual_head==4)],
        "B_head3": frozen[(frozen.action=="B_3HEAD")&(frozen.actual_head==3)],
        "A_miss": frozen[(frozen.action=="A_DUAL_3_4")&(~frozen.actual_head.isin([3,4]))],
        "B_miss": frozen[(frozen.action=="B_3HEAD")&(frozen.actual_head!=3)],
    }

    anatomy={}
    for name,g in groups.items():
        sec=Counter(int(x) for x in g.actual_second)
        thi=Counter(int(x) for x in g.actual_third)
        pair=Counter(f"{int(s)}-{int(t)}" for s,t in zip(g.actual_second,g.actual_third))
        anatomy[name]={
            "R":int(len(g)),
            "second":freq(sec,len(g)),
            "third":freq(thi,len(g)),
            "second_third_pair":pairfreq(pair,len(g)),
            "monthly":{m:int((g.month==m).sum()) for m in MONTHS},
        }

    # Head-hit rows only: how often each opponent boat appears anywhere in 2nd/3rd.
    headhit=frozen[frozen.head_hit.eq(1)].copy()
    opp_any=defaultdict(Counter)
    for r in headhit.itertuples():
        key="A" if r.action=="A_DUAL_3_4" else "B"
        opp_any[key][int(r.actual_second)]+=1
        opp_any[key][int(r.actual_third)]+=1
    any_summary={k:freq(v,2*int((headhit.action.eq("A_DUAL_3_4") if k=="A" else headhit.action.eq("B_3HEAD")).sum()))
                 for k,v in opp_any.items()}

    frozen.to_csv(OUT/"frozen_decisions_with_results.csv",index=False)
    meta={
        "model_id":"INNER12_OPPONENT_ANATOMY_SHADOW_V5",
        "status":"POSTHOC_DESCRIPTIVE_ONLY",
        "decision_rule":{
            "A_only":"heads 3 and 4",
            "B_only_strong":"head 3 when pre_pair_absdiff_prior_recent3_st >= .04",
        },
        "decision_frozen_before_results":True,
        "anatomy":anatomy,
        "opponent_any_top3_on_head_hits":any_summary,
        "september_outcomes_read":False,
        "production_changed":False,
        "note":"Descriptive opponent anatomy only. Do not use these outcome frequencies to retroactively alter the frozen head gate."
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_OPPONENT_ANATOMY_SHADOW_V5_OK")
    print("ANATOMY",json.dumps(anatomy,ensure_ascii=False))
    print("OPP_ANY",json.dumps(any_summary,ensure_ascii=False))
    print("DECISION_FROZEN_BEFORE_RESULTS")
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
