#!/usr/bin/env python3
"""Validate frozen INNER12 Stage-A Suminoe simultaneous-lag rule.

Frozen rule:
- venue = Suminoe (code 12)
- BOTH boats 1 and 2 have prior late18 rate >= 0.435
- prior late18 rate = smoothed prior-only proportion of actual ST >= .18
  with 4 pseudo-races at 35%.

Primary label:
- inner_vs_outer03 = min(actual ST1, ST2) - min(actual ST3, ST4) >= .03

Secondary diagnostics:
- dual_abs20
- dual_vs3_03
- 3-makuri / 4-makuri-sashi route

Leakage:
- every day's candidate state is frozen before that day's results are read;
- histories are updated only after the whole day is evaluated;
- September outcomes are never read;
- production unchanged.
"""
from __future__ import annotations
import csv, json, os
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from backtest import rows

HISTORY_START=date(2025,10,1)
EVAL_START=date(2026,3,1)
END=date(2026,8,31)
VENUE_CODE=12
LATE18_CUT=0.435
OUT=Path(os.environ.get("INNER12_STAGEA_OUTDIR","/tmp/inner12_stagea_suminoe_v1"))
OUT.mkdir(parents=True,exist_ok=True)

def ff(x,default=None):
    try:
        if x is None or str(x).strip()=="": return default
        return float(x)
    except Exception:return default

def ii(x,default=0):
    try:return int(float(str(x).strip()))
    except Exception:return default

def bycode(rs):
    return {str(r.get("レースコード","")).strip():r for r in rs if str(r.get("レースコード","")).strip()}

def name(s):return str(s or "").replace("　"," ").strip()

def actual_st_map(rr):
    out={}
    for c in range(1,7):
        b=ii(rr.get(f"{c}コース_艇番"))
        st=ff(rr.get(f"{c}コース_スタートタイミング"))
        if b in range(1,7) and st is not None:out[b]=st
    return out

def late18_rate(hist):
    n=len(hist)
    return (sum(v>=.18 for v in hist)+4*.35)/(n+4)

def metrics(rs):
    n=len(rs)
    def cnt(k):return sum(int(r[k]) for r in rs)
    return {
        "R":n,
        "inner_vs_outer03_H":cnt("inner_vs_outer03"),
        "inner_vs_outer03_rate":cnt("inner_vs_outer03")/n if n else 0,
        "dual_abs20_H":cnt("dual_abs20"),
        "dual_abs20_rate":cnt("dual_abs20")/n if n else 0,
        "dual_vs3_03_H":cnt("dual_vs3_03"),
        "dual_vs3_03_rate":cnt("dual_vs3_03")/n if n else 0,
        "route_H":cnt("route_target"),
        "route_rate":cnt("route_target")/n if n else 0,
        "target3_H":cnt("target3_makuri"),
        "target3_rate":cnt("target3_makuri")/n if n else 0,
        "target4_H":cnt("target4_makurisashi"),
        "target4_rate":cnt("target4_makurisashi")/n if n else 0,
    }

def main():
    hist=defaultdict(list)
    frozen=[]
    d=HISTORY_START
    while d<=END:
        if d.year==2026 and d.month==9:
            raise RuntimeError("September outcome access blocked")
        ymd=d.strftime("%Y/%m/%d")
        cards=bycode(rows(f"data/programs/race_cards/{ymd}.csv"))
        day=[]
        for rc,card in cards.items():
            if ii(card.get("レース場コード"))!=VENUE_CODE:
                continue
            n1=name(card.get("艇1_選手名",""));n2=name(card.get("艇2_選手名",""))
            if not n1 or not n2:continue
            r1=late18_rate(hist[n1]);r2=late18_rate(hist[n2])
            if d>=EVAL_START and min(r1,r2)>=LATE18_CUT:
                day.append({
                    "date":str(d),"month":str(d)[:7],"race_code":rc,
                    "venue":"住之江","race":ii(card.get("レース回")),
                    "b1_prior_n":len(hist[n1]),"b2_prior_n":len(hist[n2]),
                    "b1_prior_late18":r1,"b2_prior_late18":r2,
                    "pair_min_prior_late18":min(r1,r2),
                })

        # Same-day results are opened only after all candidates were frozen.
        res=bycode(rows(f"data/results/realtime/{ymd}.csv"))
        for rec in day:
            rr=res.get(rec["race_code"],{})
            am=actual_st_map(rr)
            if not all(b in am for b in (1,2,3,4)):continue
            st1,st2,st3,st4=(am[1],am[2],am[3],am[4])
            winner=ii(rr.get("1着_艇番"))
            kim=str(rr.get("決まり手","") or "").replace(" ","").replace("　","")
            rec.update({
                "st1":st1,"st2":st2,"st3":st3,"st4":st4,
                "inner_vs_outer03":int(min(st1,st2)-min(st3,st4)>=.03),
                "dual_abs20":int(st1>=.20 and st2>=.20),
                "dual_vs3_03":int(st1-st3>=.03 and st2-st3>=.03),
                "winner":winner,"kimarite":kim,
                "target3_makuri":int(winner==3 and kim=="まくり"),
                "target4_makurisashi":int(winner==4 and kim=="まくり差し"),
                "route_target":int((winner==3 and kim=="まくり") or (winner==4 and kim=="まくり差し")),
            })
            frozen.append(rec)

        # Update ALL player ST histories only after the whole date is frozen/evaluated.
        for rc,card in cards.items():
            rr=res.get(rc,{})
            am=actual_st_map(rr)
            for b in range(1,7):
                if b not in am:continue
                nm=name(card.get(f"艇{b}_選手名",""))
                if not nm:continue
                hist[nm].append(am[b])
                if len(hist[nm])>160:hist[nm]=hist[nm][-160:]
        d+=timedelta(days=1)

    if frozen:
        fields=sorted(set().union(*(r.keys() for r in frozen)))
        with (OUT/"selected_races.csv").open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(frozen)

    monthly=[]
    for mon in sorted({r["month"] for r in frozen}):
        q=[r for r in frozen if r["month"]==mon]
        monthly.append({"month":mon,**metrics(q)})
    if monthly:
        with (OUT/"monthly.csv").open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(monthly[0]));w.writeheader();w.writerows(monthly)

    overall=metrics(frozen)
    meta={
        "model_id":"INNER12_STAGEA_SUMINOE_V1",
        "status":"RESEARCH_ONLY_FROZEN_VALIDATION",
        "venue":"住之江","venue_code":VENUE_CODE,
        "late18_cut":LATE18_CUT,
        "rule":"min(b1_prior_late18_rate,b2_prior_late18_rate)>=0.435",
        "label":"min(actual_st1,actual_st2)-min(actual_st3,actual_st4)>=0.03",
        "history_start":str(HISTORY_START),"eval":[str(EVAL_START),str(END)],
        "same_day_results_used_for_features":False,
        "september_outcomes_read":False,
        "production_changed":False,
        "overall":overall,
        "monthly":monthly,
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print("INNER12_STAGEA_SUMINOE_V1_OK")
    print(json.dumps(meta,ensure_ascii=False))
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
