#!/usr/bin/env python3
"""INNER12_LAG high-precision V2.

Goal:
- raise precision for:
  * boat3 wins by makuri, OR
  * boat4 wins by makuri-sashi
- prioritize >=40% precision even at lower volume.

Leakage contract:
- Daily features are frozen before same-day results are read.
- Apr-May 2026 = search/train.
- Jun 2026 = validation used for candidate selection.
- Jul-Aug 2026 = final holdout only; never used to choose rules.
- September outcomes are never read.
- Production models are untouched.

Mechanism:
1) both boats 1 and 2 have independent start-lag evidence;
2) boat3 has a concrete start edge over 1/2;
3) boat4 is close enough to boat3 to follow the attack / use the opened lane;
4) boat3/4 generic class/motor strength is NOT part of the search.
"""
from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from datetime import date, timedelta
from itertools import product
from pathlib import Path

from backtest import rows, race_features

HISTORY_START = date(2025, 10, 1)
RESEARCH_START = date(2026, 3, 1)
TRAIN_START = date(2026, 4, 1)
TRAIN_END = date(2026, 5, 31)
VAL_START = date(2026, 6, 1)
VAL_END = date(2026, 6, 30)
HOLD_START = date(2026, 7, 1)
END = date(2026, 8, 31)

OUTDIR = Path(os.environ.get("INNER12_V2_OUTDIR", "/tmp/inner12_lag_high_precision_v2"))
OUTDIR.mkdir(parents=True, exist_ok=True)

def ff(x, default=None):
    try:
        if x is None or str(x).strip() == "":
            return default
        v = float(x)
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
    return str(v or "").replace("　", " ").strip()

def bycode(rs):
    out = {}
    for r in rs:
        c = code(r.get("レースコード", r.get("race_code", "")))
        if c:
            out[c] = r
    return out

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(v)))

def weighted_mean(items, default=0.5):
    vals = [(float(v), float(w)) for v, w in items if v is not None and w > 0]
    if not vals:
        return default
    den = sum(w for _, w in vals)
    return sum(v * w for v, w in vals) / den if den else default

def slow_st_score(v):
    if v is None:
        return None
    return clamp((float(v) - 0.12) / 0.12)

def slow_start_rank_score(v):
    if v is None:
        return None
    return clamp((float(v) - 2.5) / 3.0)

def player_prior(hist, global_st):
    n = len(hist)
    gm = sum(global_st) / len(global_st) if global_st else 0.17
    mean = (sum(hist) + 12.0 * gm) / (n + 12.0)
    late_n = sum(1 for v in hist if v > 0.20)
    late_rate = (late_n + 6.0 * 0.25) / (n + 6.0)
    return mean, late_rate, n

def ex_bias_prior(hist, global_bias):
    n = len(hist)
    gm = sum(global_bias) / len(global_bias) if global_bias else 0.04
    return (sum(hist) + 10.0 * gm) / (n + 10.0), n

def actual_st_map(rr):
    out = {}
    for c in range(1, 7):
        b = ii(rr.get(f"{c}コース_艇番"))
        st = ff(rr.get(f"{c}コース_スタートタイミング"))
        if b in range(1, 7) and st is not None:
            out[b] = (c, st)
    return out

def exhibition_st_map(sr):
    out = {}
    for b in range(1, 7):
        c = ii(sr.get(f"艇{b}_コース"), b)
        st = ff(sr.get(f"艇{b}_スタート展示"))
        if b in range(1, 7) and c in range(1, 7) and st is not None:
            out[b] = (c, st)
    return out

def late_pre_components(z, pmean, plate):
    return {
        "waku_st": slow_st_score(z.get("waku_st")),
        "national_st": slow_st_score(z.get("nst")),
        "meet_st": slow_st_score(z.get("meet_st")),
        "waku_start_rank": slow_start_rank_score(z.get("waku_sr")),
        "prior_actual_st": slow_st_score(pmean),
        "prior_late_rate": clamp(plate),
    }

def late_pre_score(comp):
    return weighted_mean([
        (comp["waku_st"], 0.30),
        (comp["national_st"], 0.20),
        (comp["meet_st"], 0.15),
        (comp["waku_start_rank"], 0.10),
        (comp["prior_actual_st"], 0.15),
        (comp["prior_late_rate"], 0.10),
    ])

def evidence_count(z, pmean, plate, pred):
    tests = [
        ff(z.get("waku_st")) is not None and float(z["waku_st"]) >= 0.17,
        ff(z.get("nst")) is not None and float(z["nst"]) >= 0.16,
        ff(z.get("meet_st")) is not None and float(z["meet_st"]) >= 0.17,
        pmean is not None and float(pmean) >= 0.18,
        plate is not None and float(plate) >= 0.30,
        pred is not None and float(pred) >= 0.18,
    ]
    return sum(bool(v) for v in tests)

def rate(n, d):
    return n / d if d else 0.0

def metrics(q):
    n = len(q)
    t3 = sum(int(r["target3_makuri"]) for r in q)
    t4 = sum(int(r["target4_makurisashi"]) for r in q)
    ta = sum(int(r["target_any"]) for r in q)
    return {
        "R": n,
        "target_any": ta,
        "target_any_rate": rate(ta, n),
        "target3": t3,
        "target3_rate": rate(t3, n),
        "target4": t4,
        "target4_rate": rate(t4, n),
    }

def in_period(r, a, b):
    d = date.fromisoformat(r["date"])
    return a <= d <= b

def rule_match(r, rule):
    if r.get("dual_late_post") is None:
        return False
    needed = (
        "inner_min_pred", "margin_23", "margin_13", "gap_34",
        "evidence_min", "course_standard_1234"
    )
    if any(r.get(k) is None for k in needed):
        return False

    if float(r["dual_late_post"]) < rule["dual_cut"]:
        return False
    if float(r["inner_min_pred"]) < rule["inner_min_pred_cut"]:
        return False
    if float(r["margin_23"]) < rule["margin23_cut"]:
        return False
    if float(r["margin_13"]) < rule["margin13_cut"]:
        return False
    if int(r["evidence_min"]) < rule["evidence_min_cut"]:
        return False
    if rule["standard_only"] and int(r["course_standard_1234"]) != 1:
        return False
    g34 = float(r["gap_34"])
    if g34 < rule["gap34_lo"] or g34 > rule["gap34_hi"]:
        return False
    return True

def build_rules():
    dual_cuts = [0.60, 0.65, 0.70, 0.75]
    inner_min_cuts = [0.18, 0.20, 0.22]
    margin23_cuts = [0.04, 0.06, 0.08, 0.10]
    margin13_cuts = [0.00, 0.03, 0.06]
    ev_cuts = [2, 3]
    gap_bands = [
        (-0.03, 0.05),
        (-0.02, 0.08),
        (0.00, 0.08),
        (0.00, 0.12),
    ]
    standard_flags = [True, False]
    out = []
    rid = 0
    for dual, imin, m23, m13, ev, (glo, ghi), std in product(
        dual_cuts, inner_min_cuts, margin23_cuts, margin13_cuts, ev_cuts, gap_bands, standard_flags
    ):
        rid += 1
        out.append({
            "rule_id": rid,
            "dual_cut": dual,
            "inner_min_pred_cut": imin,
            "margin23_cut": m23,
            "margin13_cut": m13,
            "evidence_min_cut": ev,
            "gap34_lo": glo,
            "gap34_hi": ghi,
            "standard_only": std,
        })
    return out

def evaluate_rules(allrows):
    train = [r for r in allrows if in_period(r, TRAIN_START, TRAIN_END)]
    val = [r for r in allrows if in_period(r, VAL_START, VAL_END)]
    hold = [r for r in allrows if in_period(r, HOLD_START, END)]

    scored = []
    for rule in build_rules():
        qt = [r for r in train if rule_match(r, rule)]
        qv = [r for r in val if rule_match(r, rule)]
        mt, mv = metrics(qt), metrics(qv)
        scored.append({
            **rule,
            **{f"train_{k}": v for k, v in mt.items()},
            **{f"val_{k}": v for k, v in mv.items()},
            "floor_rate": min(mt["target_any_rate"], mv["target_any_rate"]) if mt["R"] and mv["R"] else 0.0,
        })

    stable = [x for x in scored if x["train_R"] >= 24 and x["val_R"] >= 10]
    aggressive = [x for x in scored if x["train_R"] >= 12 and x["val_R"] >= 6]

    def select(pool):
        if not pool:
            return None
        meets40 = [
            x for x in pool
            if x["train_target_any_rate"] >= 0.40 and x["val_target_any_rate"] >= 0.40
        ]
        q = meets40 if meets40 else pool
        return sorted(
            q,
            key=lambda x: (
                x["floor_rate"],
                (x["train_target_any_rate"] + x["val_target_any_rate"]) / 2.0,
                x["val_target_any"],
                x["train_target_any"],
                x["val_R"] + x["train_R"],
            ),
            reverse=True,
        )[0]

    chosen_stable = select(stable)
    chosen_aggr = select(aggressive)

    def attach_hold(chosen):
        if not chosen:
            return None
        qh = [r for r in hold if rule_match(r, chosen)]
        mh = metrics(qh)
        out = dict(chosen)
        out.update({f"hold_{k}": v for k, v in mh.items()})
        out["meets40_train_val"] = (
            out["train_target_any_rate"] >= 0.40 and out["val_target_any_rate"] >= 0.40
        )
        return out

    return scored, attach_hold(chosen_stable), attach_hold(chosen_aggr)

def main():
    player_st = defaultdict(list)
    player_ex_bias = defaultdict(list)
    global_st = []
    global_ex_bias = []
    frozen_rows = []

    d = HISTORY_START
    while d <= END:
        if d.year == 2026 and d.month == 9:
            raise RuntimeError("September outcome access blocked")

        ymd = d.strftime("%Y/%m/%d")
        cards = bycode(rows(f"data/programs/race_cards/{ymd}.csv"))
        w10 = bycode(rows(f"data/programs/waku10/{ymd}.csv"))
        stt = bycode(rows(f"data/previews/stt/{ymd}.csv"))

        day_frozen = []
        for rc, card in cards.items():
            x = race_features(card, w10.get(rc, {}))
            if any(b not in x for b in (1, 2, 3, 4)):
                continue

            prior_meta = {}
            pre = {}
            for b in (1, 2, 3, 4):
                name = clean_name(card.get(f"艇{b}_選手名", ""))
                pmean, plate, pn = player_prior(player_st[name], global_st)
                prior_meta[b] = (pmean, plate, pn)
                if b in (1, 2):
                    pre[b] = late_pre_score(late_pre_components(x[b], pmean, plate))

            rec = {
                "date": str(d),
                "month": str(d)[:7],
                "race_code": rc,
                "venue": str(card.get("レース場コード", "")).zfill(2),
                "race": card.get("レース回", ""),
                "late1_pre": pre[1],
                "late2_pre": pre[2],
                "dual_late_pre": min(pre[1], pre[2]),
                "dual_late_post": None,
                "inner_min_pred": None,
                "margin_23": None,
                "margin_13": None,
                "gap_34": None,
                "evidence1": None,
                "evidence2": None,
                "evidence_min": None,
                "course_standard_1234": None,
            }

            for b in (1, 2):
                rec[f"b{b}_waku_st"] = x[b].get("waku_st")
                rec[f"b{b}_nst"] = x[b].get("nst")
                rec[f"b{b}_meet_st"] = x[b].get("meet_st")
                rec[f"b{b}_prior_st_mean"] = prior_meta[b][0]
                rec[f"b{b}_prior_late_rate"] = prior_meta[b][1]

            em = exhibition_st_map(stt.get(rc, {}))
            pred = {}
            if all(b in em for b in (1, 2, 3, 4)):
                for b in (1, 2, 3, 4):
                    name = clean_name(card.get(f"艇{b}_選手名", ""))
                    bias, _ = ex_bias_prior(player_ex_bias[name], global_ex_bias)
                    pred[b] = em[b][1] + bias
                    rec[f"b{b}_ex_course"] = em[b][0]
                    rec[f"b{b}_ex_st"] = em[b][1]
                    rec[f"b{b}_pred_actual_st"] = pred[b]

                exslow1, exslow2 = slow_st_score(pred[1]), slow_st_score(pred[2])
                late1_post = 0.55 * pre[1] + 0.45 * exslow1
                late2_post = 0.55 * pre[2] + 0.45 * exslow2
                rec["late1_post"] = late1_post
                rec["late2_post"] = late2_post
                rec["dual_late_post"] = min(late1_post, late2_post)

                rec["inner_min_pred"] = min(pred[1], pred[2])
                rec["margin_23"] = pred[2] - pred[3]
                rec["margin_13"] = pred[1] - pred[3]
                rec["gap_34"] = pred[4] - pred[3]
                rec["course_standard_1234"] = int(all(em[b][0] == b for b in (1, 2, 3, 4)))

                ev1 = evidence_count(x[1], prior_meta[1][0], prior_meta[1][1], pred[1])
                ev2 = evidence_count(x[2], prior_meta[2][0], prior_meta[2][1], pred[2])
                rec["evidence1"] = ev1
                rec["evidence2"] = ev2
                rec["evidence_min"] = min(ev1, ev2)

            if d >= RESEARCH_START:
                day_frozen.append((rec, card))

        res = bycode(rows(f"data/results/realtime/{ymd}.csv"))

        for rec, card in day_frozen:
            rr = res.get(rec["race_code"], {})
            winner = ii(rr.get("1着_艇番"))
            kim = str(rr.get("決まり手", "") or "").replace("　", "").replace(" ", "")
            rec["winner"] = winner
            rec["kimarite"] = kim
            rec["target3_makuri"] = int(winner == 3 and kim == "まくり")
            rec["target4_makurisashi"] = int(winner == 4 and kim == "まくり差し")
            rec["target_any"] = int(rec["target3_makuri"] or rec["target4_makurisashi"])
            frozen_rows.append(rec)

        for rc, card in cards.items():
            rr = res.get(rc, {})
            am = actual_st_map(rr)
            em = exhibition_st_map(stt.get(rc, {}))
            for b in range(1, 7):
                if b not in am:
                    continue
                name = clean_name(card.get(f"艇{b}_選手名", ""))
                if not name:
                    continue
                actual_course, actual_st = am[b]
                player_st[name].append(actual_st)
                if len(player_st[name]) > 120:
                    player_st[name] = player_st[name][-120:]
                global_st.append(actual_st)
                if len(global_st) > 20000:
                    del global_st[:5000]

                if b in em and em[b][0] == actual_course:
                    bias = actual_st - em[b][1]
                    player_ex_bias[name].append(bias)
                    if len(player_ex_bias[name]) > 80:
                        player_ex_bias[name] = player_ex_bias[name][-80:]
                    global_ex_bias.append(bias)
                    if len(global_ex_bias) > 20000:
                        del global_ex_bias[:5000]

        d += timedelta(days=1)

    fields = sorted(set().union(*(r.keys() for r in frozen_rows))) if frozen_rows else []
    if fields:
        with (OUTDIR / "race_features_v2.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(frozen_rows)

    scored, stable, aggressive = evaluate_rules(frozen_rows)

    if scored:
        top = sorted(
            scored,
            key=lambda x: (x["floor_rate"], x["val_target_any_rate"], x["train_target_any_rate"]),
            reverse=True,
        )[:1000]
        with (OUTDIR / "rule_search_top1000.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(top[0].keys()))
            w.writeheader()
            w.writerows(top)

    monthly = []
    for label, chosen in (("STABLE", stable), ("AGGRESSIVE", aggressive)):
        if not chosen:
            continue
        rule = {k: chosen[k] for k in (
            "dual_cut", "inner_min_pred_cut", "margin23_cut", "margin13_cut",
            "evidence_min_cut", "gap34_lo", "gap34_hi", "standard_only"
        )}
        for mon in ("2026-04", "2026-05", "2026-06", "2026-07", "2026-08"):
            q = [r for r in frozen_rows if r["month"] == mon and rule_match(r, rule)]
            monthly.append({"track": label, "month": mon, **metrics(q)})

    if monthly:
        with (OUTDIR / "monthly_selected.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(monthly[0].keys()))
            w.writeheader()
            w.writerows(monthly)

    meta = {
        "model_id": "INNER12_LAG_HIGH_PRECISION_V2",
        "status": "RESEARCH_ONLY",
        "target": "boat3 makuri OR boat4 makuri-sashi",
        "precision_goal": 0.40,
        "generic_boat3_boat4_strength_used": False,
        "history_start": str(HISTORY_START),
        "train": [str(TRAIN_START), str(TRAIN_END)],
        "validation": [str(VAL_START), str(VAL_END)],
        "holdout": [str(HOLD_START), str(END)],
        "holdout_used_for_selection": False,
        "september_outcomes_read": False,
        "same_day_results_used_for_features": False,
        "production_changed": False,
        "rows": len(frozen_rows),
        "chosen_stable": stable,
        "chosen_aggressive": aggressive,
    }
    (OUTDIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("INNER12_LAG_HIGH_PRECISION_V2_OK")
    print(json.dumps(meta, ensure_ascii=False))
    if stable:
        print("CHOSEN_STABLE", json.dumps(stable, ensure_ascii=False))
    if aggressive:
        print("CHOSEN_AGGRESSIVE", json.dumps(aggressive, ensure_ascii=False))

if __name__ == "__main__":
    main()
