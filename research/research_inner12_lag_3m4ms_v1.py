#!/usr/bin/env python3
"""INNER12_LAG v1

Research target:
- boat 3 wins by makuri, OR
- boat 4 wins by makuri-sashi.

Core hypothesis:
The primary driver is simultaneous start-lag risk for boats 1 and 2.
Boat 3/4 strength is intentionally NOT a primary feature in v1.

Leakage contract:
- Features for target day D are frozen before any D result file is read.
- Player actual-ST history and exhibition->actual ST bias use prior dates only.
- September 2026 outcomes are never read; research ends 2026-08-31.
- Production models are not modified by this script.
"""
from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from backtest import rows, race_features

HISTORY_START = date(2025, 10, 1)
RESEARCH_START = date(2026, 3, 1)
DEV_START = date(2026, 4, 1)
DEV_END = date(2026, 6, 30)
HOLD_START = date(2026, 7, 1)
END = date(2026, 8, 31)
OUTDIR = Path(os.environ.get("INNER12_OUTDIR", "/tmp/inner12_lag_3m4ms_v1"))
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

def threshold_grid(allrows, score_key, phase):
    dev = [r for r in allrows if DEV_START <= date.fromisoformat(r["date"]) <= DEV_END and r.get(score_key) is not None]
    hold = [r for r in allrows if HOLD_START <= date.fromisoformat(r["date"]) <= END and r.get(score_key) is not None]
    base_dev = metrics(dev)
    base_hold = metrics(hold)
    out = []
    for cut_i in range(45, 91, 5):
        cut = cut_i / 100.0
        qd = [r for r in dev if float(r[score_key]) >= cut]
        qh = [r for r in hold if float(r[score_key]) >= cut]
        md = metrics(qd)
        mh = metrics(qh)
        out.append({
            "phase": phase, "score": score_key, "cut": cut,
            **{f"dev_{k}": v for k, v in md.items()},
            **{f"hold_{k}": v for k, v in mh.items()},
            "dev_lift": (md["target_any_rate"] / base_dev["target_any_rate"]) if base_dev["target_any_rate"] else 0.0,
            "hold_lift": (mh["target_any_rate"] / base_hold["target_any_rate"]) if base_hold["target_any_rate"] else 0.0,
        })
    return out, base_dev, base_hold

def choose_dev_rule(grid):
    eligible = [r for r in grid if r["dev_R"] >= 90 and r["dev_target_any"] >= 12]
    if not eligible:
        eligible = [r for r in grid if r["dev_R"] >= 60 and r["dev_target_any"] >= 8]
    if not eligible:
        return None
    return sorted(eligible, key=lambda r: (r["dev_target_any_rate"], r["dev_target_any"], r["dev_R"]), reverse=True)[0]

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
            if 1 not in x or 2 not in x:
                continue

            bpre = {}
            prior_meta = {}
            for b in (1, 2, 3, 4):
                name = clean_name(card.get(f"艇{b}_選手名", ""))
                pmean, plate, pn = player_prior(player_st[name], global_st)
                prior_meta[b] = (pmean, plate, pn)
                if b in (1, 2):
                    bpre[b] = late_pre_score(late_pre_components(x[b], pmean, plate))

            late1, late2 = bpre[1], bpre[2]
            dual_pre = min(late1, late2)
            pair_mean = (late1 + late2) / 2.0
            pair_balance = 1.0 - abs(late1 - late2)

            inner_raw = [x[b].get("waku_st") for b in (1, 2)]
            outer_raw = [x[b].get("waku_st") for b in (3, 4)]
            inner_vs_34 = None
            if all(v is not None for v in inner_raw + outer_raw):
                inner_vs_34 = sum(inner_raw) / 2.0 - sum(outer_raw) / 2.0

            rec = {
                "date": str(d), "month": str(d)[:7], "race_code": rc,
                "venue": str(card.get("レース場コード", "")).zfill(2), "race": card.get("レース回", ""),
                "late1_pre": late1, "late2_pre": late2, "dual_late_pre": dual_pre,
                "pair_late_mean_pre": pair_mean, "pair_late_balance_pre": pair_balance,
                "inner12_minus_34_waku_st": inner_vs_34,
                "b1_prior_st_mean": prior_meta[1][0], "b2_prior_st_mean": prior_meta[2][0],
                "b1_prior_late_rate": prior_meta[1][1], "b2_prior_late_rate": prior_meta[2][1],
                "b1_prior_n": prior_meta[1][2], "b2_prior_n": prior_meta[2][2],
                "b1_waku_st": x[1].get("waku_st"), "b2_waku_st": x[2].get("waku_st"),
                "b1_nst": x[1].get("nst"), "b2_nst": x[2].get("nst"),
                "b1_meet_st": x[1].get("meet_st"), "b2_meet_st": x[2].get("meet_st"),
                "b1_waku_sr": x[1].get("waku_sr"), "b2_waku_sr": x[2].get("waku_sr"),
                "late1_post": None, "late2_post": None, "dual_late_post": None,
                "b1_ex_st": None, "b2_ex_st": None,
                "b1_pred_actual_st": None, "b2_pred_actual_st": None,
                "inner12_minus_34_pred_st": None,
            }

            em = exhibition_st_map(stt.get(rc, {}))
            if all(b in em for b in (1, 2)):
                pred = {}
                for b in (1, 2, 3, 4):
                    if b not in em:
                        continue
                    name = clean_name(card.get(f"艇{b}_選手名", ""))
                    bias, _ = ex_bias_prior(player_ex_bias[name], global_ex_bias)
                    pred[b] = em[b][1] + bias
                if 1 in pred and 2 in pred:
                    exslow1, exslow2 = slow_st_score(pred[1]), slow_st_score(pred[2])
                    rec["late1_post"] = 0.55 * late1 + 0.45 * exslow1
                    rec["late2_post"] = 0.55 * late2 + 0.45 * exslow2
                    rec["dual_late_post"] = min(rec["late1_post"], rec["late2_post"])
                    rec["b1_ex_st"], rec["b2_ex_st"] = em[1][1], em[2][1]
                    rec["b1_pred_actual_st"], rec["b2_pred_actual_st"] = pred[1], pred[2]
                    if all(b in pred for b in (1, 2, 3, 4)):
                        rec["inner12_minus_34_pred_st"] = (pred[1] + pred[2]) / 2.0 - (pred[3] + pred[4]) / 2.0

            if d >= RESEARCH_START:
                day_frozen.append((rec, card, em))

        res = bycode(rows(f"data/results/realtime/{ymd}.csv"))
        for rec, card, em in day_frozen:
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

    race_path = OUTDIR / "race_features.csv"
    fields = sorted(set().union(*(r.keys() for r in frozen_rows))) if frozen_rows else []
    if fields:
        with race_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(frozen_rows)

    pre_grid, pre_base_dev, pre_base_hold = threshold_grid(frozen_rows, "dual_late_pre", "PRE")
    post_grid, post_base_dev, post_base_hold = threshold_grid(frozen_rows, "dual_late_post", "POST")
    grid = pre_grid + post_grid
    if grid:
        with (OUTDIR / "threshold_grid.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(grid[0].keys()))
            w.writeheader()
            w.writerows(grid)

    chosen_pre = choose_dev_rule(pre_grid)
    chosen_post = choose_dev_rule(post_grid)
    monthly = []
    for phase, score_key, chosen in (("PRE", "dual_late_pre", chosen_pre), ("POST", "dual_late_post", chosen_post)):
        if not chosen:
            continue
        cut = float(chosen["cut"])
        for mon in sorted(set(r["month"] for r in frozen_rows if r.get(score_key) is not None)):
            q = [r for r in frozen_rows if r["month"] == mon and r.get(score_key) is not None and float(r[score_key]) >= cut]
            monthly.append({"phase": phase, "cut": cut, "month": mon, **metrics(q)})
    if monthly:
        with (OUTDIR / "monthly_selected.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(monthly[0].keys()))
            w.writeheader()
            w.writerows(monthly)

    meta = {
        "model_id": "INNER12_LAG_3M_4MS_V1",
        "status": "RESEARCH_ONLY",
        "target": "boat3 makuri OR boat4 makuri-sashi",
        "primary_mechanism": "simultaneous start-lag risk of boats 1 and 2",
        "boat3_boat4_strength_primary": False,
        "history_start": str(HISTORY_START),
        "research_start": str(RESEARCH_START),
        "development": [str(DEV_START), str(DEV_END)],
        "holdout": [str(HOLD_START), str(END)],
        "september_outcomes_read": False,
        "same_day_results_used_for_features": False,
        "production_changed": False,
        "dual_gate_semantics": "min(late_score_boat1, late_score_boat2)",
        "pre_base_dev": pre_base_dev, "pre_base_hold": pre_base_hold,
        "post_base_dev": post_base_dev, "post_base_hold": post_base_hold,
        "chosen_pre_dev_only": chosen_pre, "chosen_post_dev_only": chosen_post,
        "rows": len(frozen_rows),
    }
    (OUTDIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("INNER12_LAG_V1_OK")
    print(json.dumps(meta, ensure_ascii=False))
    if chosen_pre:
        print("CHOSEN_PRE", json.dumps(chosen_pre, ensure_ascii=False))
    if chosen_post:
        print("CHOSEN_POST", json.dumps(chosen_post, ensure_ascii=False))

if __name__ == "__main__":
    main()
