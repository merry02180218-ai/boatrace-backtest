#!/usr/bin/env python3
"""Exact causal v74/v83/v91 primitive builder for frozen HEAD4 ENV_ENTRY.

This module reproduces only semantics verified from the historical production
lineage. It never reads current/future results, payouts, or odds. The v83 HEAD4
wind +/-2 mapping is a frozen old-period artifact learned only on
2025-11-01..2026-05-31 and is replayed here without refitting.

Verified lineage:
- v74 strict replay: 649adb553cbc17df39719d1ca40821f5941dcbc5
- v83 wind/entry:    1cf29fddd2b5db088d810e5c32e412fa688713f9
- v83 results:       7c9a85ba492b07e4b5cd4d9c3623551a8ef52d4f
- v91 score variants:7075ae9dbe38748a22d71f049ff99f39f4aeb0b1
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

MODEL = "4カドまくり"
HEAD = 4
HIST_P = 2.0
TILT_BONUS = {-1.0: -1.19, 0.0: -0.04, 0.5: 3.00, 1.0: 1.59}
VENUE = {
    1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'
}
STADIUM_FACING = {
    '桐生':90,'戸田':0,'江戸川':200,'平和島':270,'多摩川':180,'浜名湖':90,
    '蒲郡':90,'常滑':270,'津':90,'三国':270,'びわこ':0,'住之江':0,
    '尼崎':0,'鳴門':0,'丸亀':0,'児島':0,'宮島':90,'徳山':0,
    '下関':0,'若松':0,'芦屋':0,'福岡':0,'唐津':0,'大村':0,
}
WIND_DEG = {1:0,2:45,3:90,4:135,5:180,6:225,7:270,8:315}

# Frozen from v83 old-period-only classification (2025-11-01..2026-05-31).
# Criteria in v83: n>=40 and head-rate lift >= +3pt => +2;
# n>=40 and lift <= -3pt => -2; every other HEAD4 cell => 0.
HEAD4_V83_WIND_POINTS = {
    '追い_0-2m': -2.0,
    '向かい_0-2m': -2.0,
    '左横_3-4m': 2.0,
}


class PrimitiveBuildError(RuntimeError):
    pass


def finite(name: str, v: Any) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError) as e:
        raise PrimitiveBuildError(f"invalid {name}") from e
    if not math.isfinite(x):
        raise PrimitiveBuildError(f"non-finite {name}")
    return x


def flag(name: str, v: Any) -> int:
    x = finite(name, v)
    if x not in (0.0, 1.0):
        raise PrimitiveBuildError(f"{name} must be 0/1")
    return int(x)


def tilt_band_exact(v: Any) -> float:
    x = finite("tilt", v)
    # Exact backtest_v51_lane_corrected_tickets.tilt_band semantics.
    if x <= -0.5:
        return -1.0
    if x < 0.5:
        return 0.0
    if x < 1.0:
        return 0.5
    return 1.0


def history_value(prior1: Any, prior2: Any, has2: Any) -> float:
    p1 = finite("history_prior1", prior1)
    p2 = finite("history_prior2", prior2)
    return .4*p1 + .6*p2 if flag("history_has2", has2) else p1


def pct_rank_online(x: float, vals: Sequence[Any]) -> float:
    a = [finite("history_population", v) for v in vals]
    return .5 if not a else sum(v <= x for v in a) / len(a)


def relative_deg(venue_code: Any, wind_code: Any) -> float:
    vc = int(finite("venue_code", venue_code))
    wc = int(finite("wind_code", wind_code))
    venue = VENUE.get(vc)
    wd = WIND_DEG.get(wc)
    face = STADIUM_FACING.get(venue or "")
    if venue is None or wd is None or face is None:
        raise PrimitiveBuildError("unsupported/missing venue_code or wind_code")
    return float((wd-face) % 360)


def relative_wind_exact(rdeg: Any) -> str:
    rel = finite("relative_deg", rdeg) % 360.0
    if rel < 45 or rel >= 315:
        return '追い'
    if rel < 135:
        return '右横'
    if rel < 225:
        return '向かい'
    return '左横'


def wind_speed_bin_exact(speed: Any) -> str:
    x = finite("wind_speed", speed)
    if x < 0:
        raise PrimitiveBuildError("wind_speed must be >= 0")
    return '0-2m' if x <= 2 else ('3-4m' if x <= 4 else '5m+')


def wind_adjust_points_v83_head4(rdeg: Any, speed: Any) -> float:
    cell = f"{relative_wind_exact(rdeg)}_{wind_speed_bin_exact(speed)}"
    return HEAD4_V83_WIND_POINTS.get(cell, 0.0)


def build(current: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, float]:
    if current.get("result_blind") is not True:
        raise PrimitiveBuildError("current exhibition must be result_blind=true")
    boats = current.get("current_boats") or {}
    b4 = boats.get("4") or {}
    flat = current.get("st_flat") or {}
    ex = finite("v91_ex", b4.get("cur_ex"))
    st_corr = finite("v91_st_corr", flat.get("st_corr_strength_b4"))
    st_raw = finite("v91_st_raw", flat.get("st_raw_strength_b4"))
    straight = finite("v91_straight", b4.get("cur_orig_straight"))
    avg = finite("v91_avg", b4.get("cur_orig_avg"))

    preview = .28*ex + .30*st_corr + .22*straight + .15*avg + .05*.5
    corr20 = .28*ex + .20*st_corr + .32*straight + .15*avg + .05*.5
    raw20 = .28*ex + .20*st_raw + .32*straight + .15*avg + .05*.5

    hv = history_value(context.get("history_prior1"), context.get("history_prior2"), context.get("history_has2"))
    population = context.get("history_population")
    if not isinstance(population, list):
        raise PrimitiveBuildError("history_population must be prior-only list")
    hp = pct_rank_online(hv, population)
    hadj = HIST_P*(2*hp-1)

    tilt = finite("tilt", context.get("tilt"))
    tb = TILT_BONUS[tilt_band_exact(tilt)]
    score_base = 100*preview + hadj + tb
    score_corr20 = score_base + 100*(corr20-preview)
    score_raw20 = score_base + 100*(raw20-preview)

    course = int(finite("entry_course_preview", context.get("entry_course_preview")))
    if course not in range(0,7):
        raise PrimitiveBuildError("entry_course_preview must be 0..6")
    same = int(course == HEAD)

    wind_speed = finite("wind_speed", context.get("wind_speed"))
    rdeg = relative_deg(context.get("venue_code"), context.get("wind_code"))
    wind_adj = wind_adjust_points_v83_head4(rdeg, wind_speed)

    out = {
        "preview_comp": preview,
        "relative_deg": rdeg,
        "wind_speed": wind_speed,
        "wind_adjust_points": wind_adj,
        "entry_confirmed_same": float(same),
        "entry_course_preview": float(course),
        "has_orig": float(flag("has_orig", context.get("has_orig"))),
        "has_stt": float(flag("has_stt", context.get("has_stt"))),
        "has_tkz": float(flag("has_tkz", context.get("has_tkz"))),
        "tilt": tilt,
        "tilt_bonus": tb,
        "v91_ex": ex,
        "v91_st_corr": st_corr,
        "v91_st_raw": st_raw,
        "v91_straight": straight,
        "score_BASE_v91": score_base,
        "score_CORR20_v91": score_corr20,
        "score_RAW20_v91": score_raw20,
        "score_wind_v83": score_base + wind_adj,
        "history_adjust_online": hadj,
        "history_pct_online": hp,
    }
    if any(not math.isfinite(v) for v in out.values()):
        raise PrimitiveBuildError("non-finite primitive output")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current-exhibition", required=True)
    ap.add_argument("--context-json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cur = json.loads(Path(a.current_exhibition).read_text(encoding="utf-8"))
    ctx = json.loads(Path(a.context_json).read_text(encoding="utf-8"))
    out = build(cur, ctx)
    payload = {
        "schema":"head4_env_v91_primitives_live_v2",
        "model":MODEL,
        "head":HEAD,
        "result_blind":True,
        "odds_used":False,
        "wind_mapping":"v83_old_20251101_20260531_frozen",
        "features":out,
    }
    Path(a.out).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"READY","out":a.out,"primitive_count":len(out)},ensure_ascii=False))

if __name__ == "__main__":
    main()
