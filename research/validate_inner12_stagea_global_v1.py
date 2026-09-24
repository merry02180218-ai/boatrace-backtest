#!/usr/bin/env python3
"""Validate frozen global INNER12 Stage-A rule.

Frozen dev-selected rule:
- mean Waku10 start rank of boats1+2 >= 3.7
- mean prior-only player actual-ST mean >= 0.17811274129319477
- min prior late18 rate of boats1+2 >= 0.43497650793650783

Primary label:
- inner_vs_outer03 = min(actual ST1, ST2) - min(actual ST3, ST4) >= .03

All player history features are prior-date only. Same-day results update histories
only after every race on the date has been frozen/evaluated.
September outcomes are never read. Production unchanged.
"""
from __future__ import annotations
import csv, json, os
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from backtest import rows, race_features

HISTORY_START=date(2025,10,1)
EVAL_START=date(2026,3,1)
END=date(2026,8,31)
CUT_WAKU_SR_MEAN=3.7
CUT_PRIOR_ST_MEAN=0.17811274129319477
CUT_MIN_LATE18=0.43497650793650783
OUT=Path(os.environ.get("INNER12_STAGEA_GLOBAL_OUTDIR","/tmp/inner12_stagea_global_v1"))
OUT.mkdir(parents=True,exist_ok=True)

def ff(x,default=None):
    try:
        if x is None or str(x).strip()=="":return default
        return float(x)
    except Exception:return default

def ii(x,default=0):
    try:return int(float(str(x).strip()))
    except Exception:return default

def bycode(rs):
    return {str(r.get("レースコード","")).strip():r for r in rs if str(r.get("レースコード","")).strip()}

def nm(s):return str(s or "").replace("　"," ").strip()

def actual_st_map(rr):
    out={}
    for c in range(1,7):
        b=ii(rr.get(f"{c}コース_艇番"))
        st=ff(rr.get(f"{c}コース_スタートタイミング"))
        if b in range(1,7) and st is not None:out[b]=st
    return out

def player_prior(hist,global_hist):
    gm=(sum(global_hist)/len(global_hist)) if global_hist else .17
    n=len(hist)
    st_mean=(sum(hist)+12*gm)/(n+12)
    late18=(sum(v>=.18 for v in hist)+4*.35)/(n+4)
    return st_mean,late18,n

def met(rs):
    n=len(rs)
    def c(k):return sum(int(r[k]) for r in rs)
    return {
        "R":n,
        "inner_vs_outer03_H":c("inner_vs_outer03"),
        "inner_vs_outer03_rate":c("inner_vs_outer03")/n if n else 0,
        "dual_abs20_H":c("dual_abs20"),
        "dual_abs20_rate":c("dual_abs20")/n if n else 0,
        "dual_vs3_03_H":c("dual_vs3_03"),
        "dual_vs3_03_rate":c("dual_vs3_03")/n if n else 0,
        "route_H":c("route_target"),
        "route_rate":c("route_target")/n if n else 0,
        "target3_H":c("target3_makuri"),
        "target3_rate":c("target3_makuri")/n if n else 0,
        "target4_H":c("target4_makurisashi"),
        "target4_rate":c("target4_makurisashi")/n if n else 0,
    }

def main():
    hist=defaultdict(list)
    global_hist=[]
    selected=[]
    d=HISTORY_START
    while d<=END:
        if d.year==2026 and d.month==9:
            raise RuntimeError("September outcome access blocked")
        ymd=d.strftime("%Y/%m/%d")
        cards=bycode(rows(f"data/programs/race_cards/{ymd}.csv"))
        w10=bycode(rows(f"data/programs/waku10/{ymd}.csv"))
        day=[]

        for rc,card in cards.items():
            x=race_features(card,w10.get(rc,{}))
            if 1 not in x or 2 not in x:continue
            n1=nm(card.get("艇1_選手名",""));n2=nm(card.get("艇2_選手名",""))
            if not n1 or not n2:continue
            p1,l1,nc1=player_prior(hist[n1],global_hist)
            p2,l2,nc2=player_prior(hist[n2],global_hist)
            w1=ff(x[1].get("waku_sr"));w2=ff(x[2].get("waku_sr"))
            if w1 is None or w2 is None:continue
            mean_waku=(w1+w2)/2
            mean_st=(p1+p2)/2
            min_late=min(l1,l2)
            if d>=EVAL_START and mean_waku>=CUT_WAKU_SR_MEAN and mean_st>=CUT_PRIOR_ST_MEAN and min_late>=CUT_MIN_LATE18:
                day.append({
                    "date":str(d),"month":str(d)[:7],"race_code":rc,
                    "venue":str(card.get("レース場コード","")).zfill(2),
                    "race":ii(card.get("レース回")),
                    "pair_mean_waku_sr":mean_waku,
                    "pair_mean_prior_st_mean":mean_st,
                    "pair_min_prior_late18_rate":min_late,
                    "b1_prior_n":nc1,"b2_prior_n":nc2,
                })

        # Results are opened only after all target-day candidates are frozen.
        res=bycode(rows(f"data/results/realtime/{ymd}.csv"))
        for rec in day:
            rr=res.get(rec["race_code"],{})
            am=actual_st_map(rr)
            if not all(b in am for b in (1,2,3,4)):continue
            s1,s2,s3,s4=(am[1],am[2],am[3],am[4])
            winner=ii(rr.get("1着_艇番"))
            kim=str(rr.get("決まり手","") or "").replace(" ","").replace("　","")
            rec.update({
                "st1":s1,"st2":s2,"st3":s3,"st4":s4,
                "inner_vs_outer03":int(min(s1,s2)-min(s3,s4)>=.03),
                "dual_abs20":int(s1>=.20 and s2>=.20),
                "dual_vs3_03":int(s1-s3>=.03 and s2-s3>=.03),
                "winner":winner,"kimarite":kim,
                "target3_makuri":int(winner==3 and kim=="まくり"),
                "target4_makurisashi":int(winner==4 and kim=="まくり差し"),
                "route_target":int((winner==3 and kim=="まくり") or (winner==4 and kim=="まくり差し")),
            })
            selected.append(rec)

        # Update histories only after whole day was frozen/evaluated.
        for rc,card in cards.items():
            rr=res.get(rc,{})
            am=actual_st_map(rr)
            for b in range(1,7):
                if b not in am:continue
                name=nm(card.get(f"艇{b}_選手名",""))
                if not name:continue
                hist[name].append(am[b])
                if len(hist[name])>160:hist[name]=hist[name][-160:]
                global_hist.append(am[b])
                if len(global_hist)>30000:del global_hist[:5000]
        d+=timedelta(days=1)

    if selected:
        fs=sorted(set().union(*(r.keys() for r in selected)))
        with (OUT/"selected_races.csv").open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(selected)

    monthly=[]
    for mon in sorted({r["month"] for r in selected}):
        q=[r for r in selected if r["month"]==mon]
        monthly.append({"month":mon,**met(q)})
    if monthly:
        with (OUT/"monthly.csv").open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(monthly[0]));w.writeheader();w.writerows(monthly)

    dev=[r for r in selected if "2026-04"<=r["month"]<="2026-06"]
    confirm=[r for r in selected if "2026-07"<=r["month"]<="2026-08"]
    meta={
        "model_id":"INNER12_STAGEA_GLOBAL_V1",
        "status":"RESEARCH_ONLY_FROZEN_VALIDATION",
        "rule":{
            "pair_mean_waku_sr_min":CUT_WAKU_SR_MEAN,
            "pair_mean_prior_st_mean_min":CUT_PRIOR_ST_MEAN,
            "pair_min_prior_late18_rate_min":CUT_MIN_LATE18,
        },
        "primary_label":"inner_vs_outer03",
        "history_start":str(HISTORY_START),"eval":[str(EVAL_START),str(END)],
        "same_day_results_used_for_features":False,
        "september_outcomes_read":False,
        "production_changed":False,
        "dev_apr_jun":met(dev),
        "confirm_jul_aug":met(confirm),
        "monthly":monthly,
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print("INNER12_STAGEA_GLOBAL_V1_OK")
    print(json.dumps(meta,ensure_ascii=False))
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
