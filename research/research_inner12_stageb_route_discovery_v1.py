#!/usr/bin/env python3
"""INNER12 Stage-B route discovery V1.

Purpose:
Discover pre-race / post-exhibition factors that predict BOTH boat1 and boat2
starting late together. The search is intentionally broader than average-ST features
and includes environment, exhibition structure, prior player volatility, Waku10,
meeting context, motor/prior-exhibition context, venue/race timing, and selected raw
pre-race numeric fields.

No factor is selected using Jul-Aug holdout outcomes.

Splits:
- history bootstrap: 2025-10-01 onward
- train/search:      2026-04-01 .. 2026-05-31
- validation:        2026-06-01 .. 2026-06-30
- final holdout:     2026-07-01 .. 2026-08-31
- September outcomes: NEVER read

Primary labels:
- dual_abs20: boat1 actual ST >= .20 AND boat2 actual ST >= .20
- dual_vs3_03: both boat1 and boat2 are >= .03 slower than boat3 actual ST
- inner_vs_outer03: faster of boats1/2 is still >= .03 slower than faster of boats3/4

The route outcome (3 makuri OR 4 makuri-sashi) is recorded only as secondary
diagnostic and is NEVER used to select lag factors.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
from collections import defaultdict
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path

from backtest import rows, race_features, daynum
from backtest_v3 import ingest_motor, infer_day_from_slots
from backtest_v4 import ingest_prior_day_preview, add_features

HISTORY_START = date(2025, 10, 1)
RESEARCH_START = date(2026, 3, 1)
TRAIN_START = date(2026, 4, 1)
TRAIN_END = date(2026, 5, 31)
VAL_START = date(2026, 6, 1)
VAL_END = date(2026, 6, 30)
HOLD_START = date(2026, 7, 1)
END = date(2026, 8, 31)

OUTDIR = Path(os.environ.get("INNER12_STAGEB_OUTDIR", "/tmp/inner12_stageb_route_discovery_v1"))
OUTDIR.mkdir(parents=True, exist_ok=True)

VENUE = {
    1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',
    9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',
    17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'
}
STADIUM_FACING = {
    '桐生':90,'戸田':0,'江戸川':200,'平和島':270,'多摩川':180,'浜名湖':90,
    '蒲郡':90,'常滑':270,'津':90,'三国':270,'びわこ':0,'住之島':0,'住之江':0,
    '尼崎':0,'鳴門':0,'丸亀':0,'児島':0,'宮島':90,'徳山':0,
    '下関':0,'若松':0,'芦屋':0,'福岡':0,'唐津':0,'大村':0,
}
WIND_DEG = {1:0,2:45,3:90,4:135,5:180,6:225,7:270,8:315}

LABELS = (
    "route_1_escape",
    "route_3_makuri","route_3_makurisashi",
    "route_4_makuri","route_4_makurisashi",
    "route_5_makuri","route_5_makurisashi",
    "route_3_family","route_4_family","route_5_family",
    "route_outer_core","route_outer_wide",
)
META_KEYS = {
    "date","month","race_code","venue","venue_name","race_no","day_no","day_cat",
    "route_target","winner","kimarite",
    "actual_st1","actual_st2","actual_st3","actual_st4",
    "dual_abs20","dual_vs3_03","inner_vs_outer03",
    "stagea_suminoe_ultra",
    *LABELS
}

def ff(x, default=None):
    try:
        if x is None or str(x).strip() == "":
            return default
        v = float(str(x).replace("%","").strip())
        return v if math.isfinite(v) else default
    except Exception:
        return default

def ii(x, default=0):
    try:
        return int(float(str(x).strip()))
    except Exception:
        return default

def code(v):
    return str(v or "").strip()

def clean_name(v):
    return str(v or "").replace("　"," ").strip()

def bycode(rs):
    return {code(r.get("レースコード", r.get("race_code",""))): r
            for r in rs if code(r.get("レースコード", r.get("race_code","")))}

def actual_st_map(rr):
    out = {}
    for c in range(1,7):
        b = ii(rr.get(f"{c}コース_艇番"))
        st = ff(rr.get(f"{c}コース_スタートタイミング"))
        if b in range(1,7) and st is not None:
            out[b] = (c, st)
    return out

def ex_st_map(sr):
    out = {}
    for b in range(1,7):
        c = ii(sr.get(f"艇{b}_コース"), b)
        st = ff(sr.get(f"艇{b}_スタート展示"))
        if b in range(1,7) and c in range(1,7) and st is not None:
            out[b] = (c, st)
    return out

def qtile(vals, q):
    a = sorted(v for v in vals if v is not None and math.isfinite(v))
    if not a:
        return None
    pos = (len(a)-1)*q
    lo = int(pos)
    hi = min(lo+1, len(a)-1)
    w = pos-lo
    return a[lo]*(1-w) + a[hi]*w

def mean(vals, default=None):
    a = [float(v) for v in vals if v is not None and math.isfinite(float(v))]
    return (sum(a)/len(a)) if a else default

def stdev(vals, default=None):
    a = [float(v) for v in vals if v is not None and math.isfinite(float(v))]
    if len(a) < 2:
        return default
    m = sum(a)/len(a)
    return math.sqrt(sum((v-m)**2 for v in a)/(len(a)-1))

def player_stats(hist, global_hist):
    h = list(hist)
    gm = mean(global_hist, 0.17)
    n = len(h)
    full = (sum(h) + 12*gm)/(n+12)
    recent3 = mean(h[-3:], full)
    recent6 = mean(h[-6:], full)
    recent12 = mean(h[-12:], full)
    sd6 = stdev(h[-6:], 0.04)
    sdall = stdev(h, 0.04)
    late18 = (sum(v >= .18 for v in h) + 4*.35)/(n+4)
    late20 = (sum(v >= .20 for v in h) + 4*.25)/(n+4)
    last = h[-1] if h else full
    return {
        "prior_n": n,
        "prior_st_mean": full,
        "prior_recent3_st": recent3,
        "prior_recent6_st": recent6,
        "prior_recent12_st": recent12,
        "prior_st_sd6": sd6,
        "prior_st_sd_all": sdall,
        "prior_late18_rate": late18,
        "prior_late20_rate": late20,
        "prior_last_st": last,
        "prior_recent6_drift": recent6-full,
    }

def ex_bias(hist, global_bias):
    gm = mean(global_bias, 0.04)
    n = len(hist)
    return (sum(hist) + 10*gm)/(n+10)

def rank_score(vals, boat, lower=True):
    arr = [(b,v) for b,v in vals.items() if v is not None]
    if boat not in vals or vals[boat] is None or len(arr) < 2:
        return None
    s = sorted(arr, key=lambda z:z[1], reverse=not lower)
    pos = [j for j,(b,_) in enumerate(s) if b == boat][0]
    return 1 - pos/(len(s)-1)

def original_scores(r, boat):
    ret = {"lap":None,"turn":None,"straight":None,"avg":None}
    if not r:
        return ret
    labels = [r.get("計測項目1",""), r.get("計測項目2",""), r.get("計測項目3",""), r.get("計測項目4","")]
    scores = []
    for k,label in enumerate(labels,1):
        if not str(label).strip():
            continue
        vals = {b:ff(r.get(f"艇{b}_値{k}")) for b in range(1,7)}
        sc = rank_score(vals, boat, True)
        if sc is None:
            continue
        scores.append(sc)
        lab = str(label).replace(" ","").replace("　","")
        if "直線" in lab:
            ret["straight"] = sc
        elif "まわり" in lab or "回り" in lab or "ターン" in lab:
            ret["turn"] = sc
        elif "一周" in lab or "周" in lab or "ラップ" in lab:
            ret["lap"] = sc
    ret["avg"] = mean(scores, None)
    return ret

def relwind(venue_name, wind_code):
    wd = WIND_DEG.get(wind_code)
    face = STADIUM_FACING.get(venue_name)
    if wd is None or face is None:
        return "missing"
    rel = (wd-face)%360
    if rel < 45 or rel >= 315:
        return "追い"
    if rel < 135:
        return "右横"
    if rel < 225:
        return "向かい"
    return "左横"

def sanitize(s):
    s = re.sub(r"[^0-9A-Za-zぁ-んァ-ヶ一-龠_]+", "_", str(s))
    return s.strip("_")[:80]

def raw_numeric_boat_fields(card, boat):
    out = {}
    pre = f"艇{boat}_"
    for k,v in card.items():
        if not str(k).startswith(pre):
            continue
        suf = str(k)[len(pre):]
        if any(x in suf for x in ("登録番号","モーター番号","ボート番号","R番号","選手名","支部","級別")):
            continue
        # Broad but bounded whitelist: discover unexpected pre-race effects without
        # exploding memory on IDs / administrative numeric fields.
        allow = (
            "ST","スタート","勝率","連対率","事故","F","L","フライング",
            "体重","年齢","着順","展示","能力"
        )
        if not any(x in suf for x in allow):
            continue
        val = ff(v)
        if val is None:
            continue
        out["raw_"+sanitize(suf)] = val
    return out

def add_pair_features(rec, prefix, a, b):
    keys = sorted(set(a) & set(b))
    for k in keys:
        va, vb = ff(a.get(k)), ff(b.get(k))
        if va is None or vb is None:
            continue
        rec[f"{prefix}_b1_{k}"] = va
        rec[f"{prefix}_b2_{k}"] = vb
        rec[f"{prefix}_pair_min_{k}"] = min(va,vb)
        rec[f"{prefix}_pair_max_{k}"] = max(va,vb)
        rec[f"{prefix}_pair_mean_{k}"] = (va+vb)/2
        rec[f"{prefix}_pair_absdiff_{k}"] = abs(va-vb)

def period_name(ds):
    d = date.fromisoformat(ds)
    if TRAIN_START <= d <= TRAIN_END:
        return "train"
    if VAL_START <= d <= VAL_END:
        return "validation"
    if HOLD_START <= d <= END:
        return "holdout"
    return "other"

def label_rate(rs, label):
    if not rs:
        return 0.0
    return sum(int(r[label]) for r in rs)/len(rs)

def numeric_features(allrows):
    keys = set()
    for r in allrows:
        for k,v in r.items():
            if k in META_KEYS or k.startswith("cat_"):
                continue
            if isinstance(v,(int,float)) and v is not None and math.isfinite(float(v)):
                keys.add(k)
    return sorted(keys)

def is_st_family(name):
    n = name.lower()
    return any(x in n for x in (
        "st","スタート","late","waku_sr","ex_", "pred_actual",
        "prior_recent","prior_last","prior_late"
    ))

def evaluate_numeric(allrows):
    train = [r for r in allrows if period_name(r["date"])=="train"]
    val = [r for r in allrows if period_name(r["date"])=="validation"]
    hold = [r for r in allrows if period_name(r["date"])=="holdout"]
    out = []

    for label in LABELS:
        bt = label_rate(train,label)
        bv = label_rate(val,label)
        bh = label_rate(hold,label)
        for feat in numeric_features(allrows):
            tv = [ff(r.get(feat)) for r in train]
            tv = [v for v in tv if v is not None]
            if len(tv) < 300:
                continue
            q25, q75 = qtile(tv,.25), qtile(tv,.75)
            if q25 is None or q75 is None or abs(q75-q25) < 1e-12:
                continue

            train_low = [r for r in train if ff(r.get(feat)) is not None and float(r[feat]) <= q25]
            train_high = [r for r in train if ff(r.get(feat)) is not None and float(r[feat]) >= q75]
            rl = label_rate(train_low,label)
            rh = label_rate(train_high,label)
            direction = "HIGH" if rh >= rl else "LOW"
            cut = q75 if direction=="HIGH" else q25

            def pick(rs):
                z=[]
                for r in rs:
                    v=ff(r.get(feat))
                    if v is None:
                        continue
                    if (direction=="HIGH" and v>=cut) or (direction=="LOW" and v<=cut):
                        z.append(r)
                return z

            qt,qv,qh = pick(train),pick(val),pick(hold)
            if len(qt)<80 or len(qv)<25 or len(qh)<40:
                continue
            rt,rv,rh2 = label_rate(qt,label),label_rate(qv,label),label_rate(qh,label)
            lift_t = rt/bt if bt else 0
            lift_v = rv/bv if bv else 0
            lift_h = rh2/bh if bh else 0
            route_t = label_rate([{**r,label:r["route_target"]} for r in qt],label)
            route_v = label_rate([{**r,label:r["route_target"]} for r in qv],label)
            route_h = label_rate([{**r,label:r["route_target"]} for r in qh],label)
            out.append({
                "label":label,"feature":feat,"family":"ST" if is_st_family(feat) else "NON_ST",
                "direction":direction,"train_cut":cut,
                "train_base":bt,"train_R":len(qt),"train_rate":rt,"train_lift":lift_t,
                "val_base":bv,"val_R":len(qv),"val_rate":rv,"val_lift":lift_v,
                "hold_base":bh,"hold_R":len(qh),"hold_rate":rh2,"hold_lift":lift_h,
                "floor_train_val_lift":min(lift_t,lift_v),
                "stable_all3":int(lift_t>1 and lift_v>1 and lift_h>1),
                "route_rate_train":route_t,"route_rate_val":route_v,"route_rate_hold":route_h,
            })
    return out

def evaluate_categories(allrows):
    train = [r for r in allrows if period_name(r["date"])=="train"]
    val = [r for r in allrows if period_name(r["date"])=="validation"]
    hold = [r for r in allrows if period_name(r["date"])=="holdout"]
    catkeys = sorted({k for r in allrows for k in r if k.startswith("cat_")})
    out=[]

    for label in LABELS:
        bt,bv,bh = label_rate(train,label),label_rate(val,label),label_rate(hold,label)
        for feat in catkeys:
            cats=defaultdict(list)
            for r in train:
                v=str(r.get(feat,"") or "")
                if v and v!="missing":
                    cats[v].append(r)
            eligible=[(v,a) for v,a in cats.items() if len(a)>=80]
            eligible.sort(key=lambda za: label_rate(za[1],label), reverse=True)
            for v,qt in eligible[:8]:
                qv=[r for r in val if str(r.get(feat,"") or "")==v]
                qh=[r for r in hold if str(r.get(feat,"") or "")==v]
                if len(qv)<20 or len(qh)<30:
                    continue
                rt,rv,rh=label_rate(qt,label),label_rate(qv,label),label_rate(qh,label)
                out.append({
                    "label":label,"feature":feat,"category":v,
                    "train_base":bt,"train_R":len(qt),"train_rate":rt,"train_lift":rt/bt if bt else 0,
                    "val_base":bv,"val_R":len(qv),"val_rate":rv,"val_lift":rv/bv if bv else 0,
                    "hold_base":bh,"hold_R":len(qh),"hold_rate":rh,"hold_lift":rh/bh if bh else 0,
                    "floor_train_val_lift":min(rt/bt if bt else 0,rv/bv if bv else 0),
                    "stable_all3":int(rt>bt and rv>bv and rh>bh),
                })
    return out

def feature_condition(r, spec):
    v=ff(r.get(spec["feature"]))
    if v is None:
        return False
    return v>=spec["cut"] if spec["direction"]=="HIGH" else v<=spec["cut"]

def evaluate_interactions(allrows, numeric_eval):
    train=[r for r in allrows if period_name(r["date"])=="train"]
    val=[r for r in allrows if period_name(r["date"])=="validation"]
    hold=[r for r in allrows if period_name(r["date"])=="holdout"]
    out=[]

    for label in LABELS:
        base_t,base_v,base_h=label_rate(train,label),label_rate(val,label),label_rate(hold,label)
        pool=[x for x in numeric_eval if x["label"]==label and x["train_lift"]>1.10 and x["val_lift"]>1.05]
        pool.sort(key=lambda x:(x["floor_train_val_lift"],x["stable_all3"]),reverse=True)

        chosen=[]
        seen=set()
        # Mix ST and non-ST; retain at most 16 distinct factors.
        for x in pool:
            if x["feature"] in seen:
                continue
            seen.add(x["feature"])
            chosen.append({
                "feature":x["feature"],"direction":x["direction"],"cut":x["train_cut"],
                "family":x["family"],
            })
            if len(chosen)>=16:
                break

        for a,b in combinations(chosen,2):
            # avoid two aliases of almost same raw pair name when possible
            qt=[r for r in train if feature_condition(r,a) and feature_condition(r,b)]
            qv=[r for r in val if feature_condition(r,a) and feature_condition(r,b)]
            if len(qt)<35 or len(qv)<12:
                continue
            qh=[r for r in hold if feature_condition(r,a) and feature_condition(r,b)]
            if len(qh)<18:
                continue
            rt,rv,rh=label_rate(qt,label),label_rate(qv,label),label_rate(qh,label)
            out.append({
                "label":label,
                "feature1":a["feature"],"dir1":a["direction"],"cut1":a["cut"],"family1":a["family"],
                "feature2":b["feature"],"dir2":b["direction"],"cut2":b["cut"],"family2":b["family"],
                "train_R":len(qt),"train_rate":rt,"train_lift":rt/base_t if base_t else 0,
                "val_R":len(qv),"val_rate":rv,"val_lift":rv/base_v if base_v else 0,
                "hold_R":len(qh),"hold_rate":rh,"hold_lift":rh/base_h if base_h else 0,
                "floor_train_val_lift":min(rt/base_t if base_t else 0,rv/base_v if base_v else 0),
                "stable_all3":int(rt>base_t and rv>base_v and rh>base_h),
                "route_rate_hold":label_rate([{**r,label:r["route_target"]} for r in qh],label),
            })
    return out

def write_csv(path, rs):
    if not rs:
        return
    fields=sorted(set().union(*(r.keys() for r in rs)))
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader();w.writerows(rs)

def main():
    player_st=defaultdict(list)
    player_ex_bias=defaultdict(list)
    global_st=[]
    global_ex_bias=[]
    preview_cache={}
    motor_hist=defaultdict(list)
    motor_seen=set()
    frozen_rows=[]
    schemas={}

    d=HISTORY_START
    while d<=END:
        if d.year==2026 and d.month==9:
            raise RuntimeError("September outcome access blocked")

        ymd=d.strftime("%Y/%m/%d")
        cards=bycode(rows(f"data/programs/race_cards/{ymd}.csv"))
        w10=bycode(rows(f"data/programs/waku10/{ymd}.csv"))
        titles=bycode(rows(f"data/programs/title/{ymd}.csv"))
        stt=bycode(rows(f"data/previews/stt/{ymd}.csv"))
        tkz=bycode(rows(f"data/previews/tkz/{ymd}.csv"))
        orig=bycode(rows(f"data/previews/original_exhibition/{ymd}.csv"))
        sui=bycode(rows(f"data/previews/sui/{ymd}.csv"))

        if cards and not schemas.get("race_cards"):
            schemas["race_cards"]=sorted(next(iter(cards.values())).keys())
        for nm,src in (("waku10",w10),("title",titles),("stt",stt),("tkz",tkz),("original_exhibition",orig),("sui",sui)):
            if src and not schemas.get(nm):
                schemas[nm]=sorted(next(iter(src.values())).keys())

        day_frozen=[]
        for rc,card in cards.items():
            x=add_features(race_features(card,w10.get(rc,{})),card,preview_cache,motor_hist)
            if any(b not in x for b in (1,2,3,4)):
                continue

            venue_code=ii(card.get("レース場コード"))
            venue_name=VENUE.get(venue_code,str(venue_code))
            dn=daynum(titles.get(rc,{}).get("日次","")) or infer_day_from_slots(card)
            day_cat="初日" if dn==1 else ("2日目" if dn==2 else ("3日目以降" if dn>=3 else "不明"))

            rec={
                "date":str(d),"month":str(d)[:7],"race_code":rc,
                "venue":venue_code,"venue_name":venue_name,"race_no":ii(card.get("レース回")),
                "day_no":dn,"day_cat":day_cat,
                "cat_venue":venue_name,
                "cat_day_cat":day_cat,
                "cat_race_band":"1-4R" if ii(card.get("レース回"))<=4 else ("5-8R" if ii(card.get("レース回"))<=8 else "9-12R"),
                "cat_grade_pair":f"{x[1].get('grade','')}-{x[2].get('grade','')}",
                "cat_month":str(d)[:7],
            }

            bfeat={}
            pmeta={}
            for b in (1,2,3,4,5):
                z=x[b]
                name=clean_name(card.get(f"艇{b}_選手名",""))
                ps=player_stats(player_st[name],global_st)
                pmeta[b]=ps
                bfeat[b]={
                    "nst":z.get("nst"),"wr":z.get("wr"),"local":z.get("local"),
                    "motor2":z.get("motor2"),"motor3":z.get("motor3"),
                    "waku_st":z.get("waku_st"),"waku_wr":z.get("waku_wr"),"waku_sr":z.get("waku_sr"),
                    "past_win":z.get("past_win"),"meet_st":z.get("meet_st"),
                    "mhist":z.get("mhist"),"pexpo":z.get("pexpo"),"pturn":z.get("pturn"),
                    "pstraight":z.get("pstraight"),"pdisplay":z.get("pdisplay"),
                    "stretch":z.get("stretch"),"turnfoot":z.get("turnfoot"),
                    **ps,
                }
                rec[f"cat_b{b}_ptype"]=str(z.get("ptype","不明"))
                raw=raw_numeric_boat_fields(card,b)
                for k,v in raw.items():
                    rec[f"raw_b{b}_{k}"]=v

            # Inner-pair Stage-A aggregates.
            add_pair_features(rec,"pre",bfeat[1],bfeat[2])

            # Stage-B attacker features: keep boats 3/4/5 individually visible.
            # Generic strength is allowed here as a conversion diagnostic, but not forced
            # as a dominant score; the search decides whether it reproduces in validation.
            for b in (3,4,5):
                for k,v in bfeat[b].items():
                    vv=ff(v)
                    if vv is not None:
                        rec[f"attack_b{b}_{k}"]=vv
                rec[f"cat_b{b}_grade"]=str(x[b].get("grade","") or "不明")
                rec[f"cat_b{b}_ptype"]=str(x[b].get("ptype","不明") or "不明")

            # Relative attacker geometry. Signs are left raw; train-only threshold
            # direction selection decides which side is useful.
            common=set(bfeat[3]) & set(bfeat[4]) & set(bfeat[5])
            for k in common:
                v3,v4,v5=ff(bfeat[3].get(k)),ff(bfeat[4].get(k)),ff(bfeat[5].get(k))
                if v3 is None or v4 is None or v5 is None:
                    continue
                rec[f"attack_gap_3minus4_{k}"]=v3-v4
                rec[f"attack_gap_4minus5_{k}"]=v4-v5
                rec[f"attack_gap_3minus5_{k}"]=v3-v5

            em=ex_st_map(stt.get(rc,{}))
            if all(b in em for b in (1,2,3,4,5)):
                pred={}
                for b in (1,2,3,4):
                    name=clean_name(card.get(f"艇{b}_選手名",""))
                    bias=ex_bias(player_ex_bias[name],global_ex_bias)
                    pred[b]=em[b][1]+bias
                    rec[f"post_b{b}_ex_st"]=em[b][1]
                    rec[f"post_b{b}_pred_actual_st"]=pred[b]
                    rec[f"post_b{b}_ex_course"]=em[b][0]
                rec["post_pair_min_ex_st"]=min(em[1][1],em[2][1])
                rec["post_pair_mean_ex_st"]=(em[1][1]+em[2][1])/2
                rec["post_pair_absdiff_ex_st"]=abs(em[1][1]-em[2][1])
                rec["post_pair_min_pred_actual_st"]=min(pred[1],pred[2])
                rec["post_pair_mean_pred_actual_st"]=(pred[1]+pred[2])/2
                rec["post_gap_b2_vs_b3_pred"]=pred[2]-pred[3]
                rec["post_gap_b1_vs_b3_pred"]=pred[1]-pred[3]
                rec["post_inner_fast_vs_outer_fast_pred"]=min(pred[1],pred[2])-min(pred[3],pred[4])
                rec["post_inner_fast_vs_attack_fast_pred"]=min(pred[1],pred[2])-min(pred[3],pred[4],pred[5])
                rec["post_gap_b3_vs_b4_pred"]=pred[3]-pred[4]
                rec["post_gap_b4_vs_b5_pred"]=pred[4]-pred[5]
                rec["post_gap_b3_vs_b5_pred"]=pred[3]-pred[5]
                rec["cat_course_pattern"]="standard" if all(em[b][0]==b for b in (1,2,3,4,5)) else "changed"
                rec["cat_b1_course_changed"]="yes" if em[1][0]!=1 else "no"
                rec["cat_b2_course_changed"]="yes" if em[2][0]!=2 else "no"

            tr=tkz.get(rc,{})
            if tr:
                exvals={b:ff(tr.get(f"艇{b}_展示タイム")) for b in range(1,7)}
                for b in (1,2):
                    rec[f"post_b{b}_display_time"]=exvals.get(b)
                    rec[f"post_b{b}_display_rank_score"]=rank_score(exvals,b,True)
                if exvals.get(1) is not None and exvals.get(2) is not None:
                    rec["post_pair_mean_display_time"]=(exvals[1]+exvals[2])/2
                    rec["post_pair_min_display_rank_score"]=min(
                        rank_score(exvals,1,True) if rank_score(exvals,1,True) is not None else .5,
                        rank_score(exvals,2,True) if rank_score(exvals,2,True) is not None else .5
                    )
                for b in (1,2):
                    tilt=ff(tr.get(f"艇{b}_チルト"))
                    rec[f"post_b{b}_tilt"]=tilt
                if rec.get("post_b1_tilt") is not None and rec.get("post_b2_tilt") is not None:
                    rec["post_pair_mean_tilt"]=(rec["post_b1_tilt"]+rec["post_b2_tilt"])/2

            # Stage-B current display/tilt for attack boats.
            if tr:
                exvals={b:ff(tr.get(f"艇{b}_展示タイム")) for b in range(1,7)}
                for b in (3,4,5):
                    rec[f"post_b{b}_display_time"]=exvals.get(b)
                    rec[f"post_b{b}_display_rank_score"]=rank_score(exvals,b,True)
                    rec[f"post_b{b}_tilt"]=ff(tr.get(f"艇{b}_チルト"))

            orr=orig.get(rc,{})
            if orr:
                oscore={b:original_scores(orr,b) for b in (1,2,3,4,5)}
                for k in ("lap","turn","straight","avg"):
                    rec[f"post_b1_orig_{k}"]=oscore[1].get(k)
                    rec[f"post_b2_orig_{k}"]=oscore[2].get(k)
                    if oscore[1].get(k) is not None and oscore[2].get(k) is not None:
                        rec[f"post_pair_min_orig_{k}"]=min(oscore[1][k],oscore[2][k])
                        rec[f"post_pair_mean_orig_{k}"]=(oscore[1][k]+oscore[2][k])/2
                    for b in (3,4,5):
                        rec[f"post_b{b}_orig_{k}"]=oscore[b].get(k)

            sr=sui.get(rc,{})
            if sr:
                wind=ff(sr.get("風速(m)"))
                wave=ff(sr.get("波の高さ(cm)"))
                air=ff(sr.get("気温(℃)"))
                water=ff(sr.get("水温(℃)"))
                wd=ii(sr.get("風向"),0)
                rec["post_env_wind_m"]=wind
                rec["post_env_wave_cm"]=wave
                rec["post_env_air_c"]=air
                rec["post_env_water_c"]=water
                rec["cat_weather"]=str(sr.get("天候","") or "missing")
                rec["cat_relwind"]=relwind(venue_name,wd)
                rec["cat_wind_bin"]="0-2m" if wind is not None and wind<=2 else ("3-4m" if wind is not None and wind<=4 else ("5m+" if wind is not None else "missing"))
                rec["cat_relwind_speed"]=rec["cat_relwind"]+"_"+rec["cat_wind_bin"]

            if d>=RESEARCH_START:
                stagea_global=(
                    ff(rec.get("pre_pair_mean_waku_sr"),-9)>=3.7
                    and ff(rec.get("pre_pair_mean_prior_st_mean"),-9)>=0.17811274129319477
                    and ff(rec.get("pre_pair_min_prior_late18_rate"),-9)>=0.43497650793650783
                )
                if stagea_global:
                    rec["stagea_suminoe_ultra"]=int(
                        venue_code==12 and ff(rec.get("pre_pair_min_prior_late18_rate"),-9)>=0.435
                    )
                    day_frozen.append((rec,card,em))

        # Outcomes are loaded only after all target-day features are frozen.
        res=bycode(rows(f"data/results/realtime/{ymd}.csv"))

        for rec,card,em in day_frozen:
            rr=res.get(rec["race_code"],{})
            am=actual_st_map(rr)
            if not all(b in am for b in (1,2,3,4)):
                continue
            st1,st2,st3,st4=[am[b][1] for b in (1,2,3,4)]
            winner=ii(rr.get("1着_艇番"))
            kim=str(rr.get("決まり手","") or "").replace(" ","").replace("　","")
            r1=int(winner==1 and kim=="逃げ")
            r3m=int(winner==3 and kim=="まくり")
            r3ms=int(winner==3 and kim=="まくり差し")
            r4m=int(winner==4 and kim=="まくり")
            r4ms=int(winner==4 and kim=="まくり差し")
            r5m=int(winner==5 and kim=="まくり")
            r5ms=int(winner==5 and kim=="まくり差し")
            rec.update({
                "actual_st1":st1,"actual_st2":st2,"actual_st3":st3,"actual_st4":st4,
                "dual_abs20":int(st1>=.20 and st2>=.20),
                "dual_vs3_03":int((st1-st3)>=.03 and (st2-st3)>=.03),
                "inner_vs_outer03":int((min(st1,st2)-min(st3,st4))>=.03),
                "winner":winner,"kimarite":kim,
                "route_1_escape":r1,
                "route_3_makuri":r3m,"route_3_makurisashi":r3ms,
                "route_4_makuri":r4m,"route_4_makurisashi":r4ms,
                "route_5_makuri":r5m,"route_5_makurisashi":r5ms,
                "route_3_family":int(r3m or r3ms),
                "route_4_family":int(r4m or r4ms),
                "route_5_family":int(r5m or r5ms),
                "route_outer_core":int(r3m or r3ms or r4m or r4ms or r5ms),
                "route_outer_wide":int(r3m or r3ms or r4m or r4ms or r5m or r5ms),
                "route_target":int(r3m or r4ms),
            })
            frozen_rows.append(rec)

        # Update histories only after the entire day was frozen/evaluated.
        for rc,card in cards.items():
            rr=res.get(rc,{})
            am=actual_st_map(rr)
            em=ex_st_map(stt.get(rc,{}))
            for b in range(1,7):
                if b not in am:
                    continue
                name=clean_name(card.get(f"艇{b}_選手名",""))
                if not name:
                    continue
                ac,ast=am[b]
                player_st[name].append(ast)
                if len(player_st[name])>160:
                    player_st[name]=player_st[name][-160:]
                global_st.append(ast)
                if len(global_st)>30000:
                    del global_st[:5000]
                if b in em and em[b][0]==ac:
                    bias=ast-em[b][1]
                    player_ex_bias[name].append(bias)
                    if len(player_ex_bias[name])>100:
                        player_ex_bias[name]=player_ex_bias[name][-100:]
                    global_ex_bias.append(bias)
                    if len(global_ex_bias)>30000:
                        del global_ex_bias[:5000]

        ingest_prior_day_preview(preview_cache,d)
        ingest_motor(motor_hist,motor_seen,d)
        d+=timedelta(days=1)

    write_csv(OUTDIR/"factor_rows.csv",frozen_rows)

    num=evaluate_numeric(frozen_rows)
    num_sorted=sorted(num,key=lambda x:(x["floor_train_val_lift"],min(x["train_rate"],x["val_rate"]),x["train_R"]+x["val_R"]),reverse=True)
    write_csv(OUTDIR/"numeric_factor_ranking.csv",num_sorted)

    nonst=[x for x in num_sorted if x["family"]=="NON_ST"]
    write_csv(OUTDIR/"nonst_surprise_ranking.csv",nonst)

    cats=evaluate_categories(frozen_rows)
    cats_sorted=sorted(cats,key=lambda x:(x["floor_train_val_lift"],min(x["train_rate"],x["val_rate"]),x["train_R"]+x["val_R"]),reverse=True)
    write_csv(OUTDIR/"categorical_factor_ranking.csv",cats_sorted)

    inter=evaluate_interactions(frozen_rows,num)
    inter_sorted=sorted(inter,key=lambda x:(x["floor_train_val_lift"],min(x["train_rate"],x["val_rate"]),x["train_R"]+x["val_R"]),reverse=True)
    write_csv(OUTDIR/"interaction_ranking.csv",inter_sorted)

    baselines={}
    monthly=[]
    for label in LABELS:
        baselines[label]={}
        for p in ("train","validation","holdout"):
            z=[r for r in frozen_rows if period_name(r["date"])==p]
            baselines[label][p]={"R":len(z),"H":sum(r[label] for r in z),"rate":label_rate(z,label)}
        for mon in sorted({r["month"] for r in frozen_rows}):
            z=[r for r in frozen_rows if r["month"]==mon]
            monthly.append({"label":label,"month":mon,"R":len(z),"H":sum(r[label] for r in z),"rate":label_rate(z,label)})
    write_csv(OUTDIR/"label_monthly.csv",monthly)

    top_summary={}
    for label in LABELS:
        top_summary[label]={
            "numeric_top10":[x for x in num_sorted if x["label"]==label][:10],
            "nonst_top10":[x for x in nonst if x["label"]==label][:10],
            "categorical_top10":[x for x in cats_sorted if x["label"]==label][:10],
            "interaction_top10":[x for x in inter_sorted if x["label"]==label][:10],
        }

    meta={
        "model_id":"INNER12_STAGEB_ROUTE_DISCOVERY_V1",
        "status":"RESEARCH_ONLY",
        "target":"discover route conversion inside frozen GLOBAL Stage-A candidates",
        "history_start":str(HISTORY_START),
        "train":[str(TRAIN_START),str(TRAIN_END)],
        "validation":[str(VAL_START),str(VAL_END)],
        "holdout":[str(HOLD_START),str(END)],
        "holdout_used_for_selection":False,
        "stagea_rule_frozen":True,
        "stagea_gate":"GLOBAL_STAGEA_V1",
        "september_outcomes_read":False,
        "same_day_results_used_before_feature_freeze":False,
        "route_labels_are_primary_targets":True,
        "outcome_columns_excluded_from_features":True,
        "production_changed":False,
        "rows":len(frozen_rows),
        "labels":list(LABELS),
        "baselines":baselines,
        "schemas":schemas,
        "top_summary":top_summary,
    }
    (OUTDIR/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_STAGEB_ROUTE_DISCOVERY_V1_OK")
    print("ROWS",len(frozen_rows))
    print("BASELINES",json.dumps(baselines,ensure_ascii=False))
    for label in LABELS:
        print("TOP_NONST",label,json.dumps(top_summary[label]["nonst_top10"][:5],ensure_ascii=False))
        print("TOP_INTERACTION",label,json.dumps(top_summary[label]["interaction_top10"][:5],ensure_ascii=False))
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
