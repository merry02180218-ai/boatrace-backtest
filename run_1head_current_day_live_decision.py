#!/usr/bin/env python3
from __future__ import annotations

"""Final result-blind LIVE decision for the promoted 1HEAD production lanes.

Lanes kept distinct:
- existing LIVE: HEAD >= .790
- promoted PLAYER_HISTORY expansion: .780 <= HEAD < .790 + b1 recent_p2
- promoted relaxed volume expansion: .750 <= HEAD < .780 + relaxed exhibition + env_pair

The existing v351 finalizer remains the single ticket-policy implementation.
For an accepted expansion lane we only bridge its already-promoted head gate into
that finalizer; the original HEAD probability is restored in the emitted result.

Target-race result and payout data are never read here.
"""

import argparse
import csv
import json
import math
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

import onehead_production_profile as prod
import run_v326_1head_ticketaware_exhibition as v326
import run_v332_1head_attack_first_redesign as v332
from boatrace_live_odds3t import fetch_odds3t

JST=ZoneInfo("Asia/Tokyo")
BUDGET_YEN=5000
UNIT_YEN=100
RELAXED_ENV_W=0.10
RELAXED_Q=0.65


def _load_json(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _cards_by_code(path:Path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    return {str(r.get("レースコード","")).zfill(12):r for r in rows}


def _recent_p2_from_state(state:dict, card:dict, boat:int=1)->float:
    reg=str(card.get(f"艇{boat}_登録番号","")).strip()
    if not reg:
        raise RuntimeError(f"missing registration number boat={boat}")
    s=(state.get("players") or {}).get(reg)
    if not isinstance(s,dict):
        raise RuntimeError(f"player-history state missing registration={reg}")
    r=list(s.get("recent_p2") or [])
    return float(sum(float(x) for x in r)/len(r)) if r else 1.0/3.0


def _score_from_pars(feat:dict, pars:dict, env_w:float)->float|None:
    try:
        attack=(float(feat["attack_core"])-float(pars["attack_mean"]))/float(pars["attack_sd"])
        env=0.0
        if bool(feat.get("env_ready")) and math.isfinite(float(feat.get("env_pair",float("nan")))):
            env=(float(feat["env_pair"])-float(pars["env_mean"]))/float(pars["env_sd"])
        return float(attack+float(env_w)*env)
    except Exception:
        return None


def _build_exhibition(base:dict, probe:dict, state:dict, train_path:Path):
    code=str(base["race_code"]).zfill(12)
    if str(probe.get("race_code","")).zfill(12)!=code:
        raise RuntimeError("probe/base race_code mismatch")
    if probe.get("result_or_payout_used") is not False or not probe.get("ready"):
        raise RuntimeError("unsafe or unready exhibition probe")
    if state.get("target_date_results_used") is not False or state.get("payout_used") is not False:
        raise RuntimeError("unsafe daily state")

    audit=dict(probe["audit"])
    bias={int(k):float(v) for k,v in (state.get("st_bias") or {}).items()}
    if set(bias)!=set(range(1,7)):
        raise RuntimeError("daily-state ST bias incomplete")

    tkz={code:probe["tkz"]}; stt={code:probe["stt"]}; orig={code:probe["orig"]}
    ex,st,os=v326.corrected_direct(code,tkz,stt,orig,bias)
    feat=v326.partial_feature_row({"tickets":base["base_tickets"]},ex,st,os,audit)
    feat.update(audit)
    feat["attack_ready"]=bool(audit["tkz_all6"] and audit["stt_all6"] and audit["orig_straight_all6"] and audit["orig_avg_all6"])
    feat["env_ready"]=bool(audit["tkz_all6"] and audit["stt_all6"] and audit["orig_turn_all6"] and audit["orig_straight_all6"])
    feat["attack_core"]=(
        prod.ATTACK_CORE_W_ONE_EX*float(feat["one_ex"])
        + prod.ATTACK_CORE_W_ONE_ST*float(feat["one_st"])
        + prod.ATTACK_CORE_W_ONE_STRAIGHT*float(feat["one_straight"])
        + prod.ATTACK_CORE_W_ONE_ORIG_AVG*float(feat["one_orig_avg"])
    )
    feat["env_pair"]=(
        .30*float(feat["sec_ex_mean_margin"])
        + .30*float(feat["sec_st_mean_margin"])
        + .20*float(feat["third_turn_mean_margin"])
        + .20*float(feat["third_straight_mean_margin"])
        if feat["env_ready"] else float("nan")
    )

    cutoff=date.fromisoformat(str(state["history_end"]))
    train=pd.read_csv(train_path,dtype={"race_code":str})
    if "date" not in train:
        train["date"]=[f"{str(c).zfill(12)[:4]}-{str(c).zfill(12)[4:6]}-{str(c).zfill(12)[6:8]}" for c in train.race_code]
    train=train[pd.to_datetime(train["date"]).dt.date<=cutoff].copy()
    if train.empty:
        raise RuntimeError("empty exhibition training cache")

    test=pd.DataFrame([{**feat,"race_code":code,"head_hit":0,"hit":0}])
    standard,standard_pars=v332.fit_apply(
        train,test,{"family":"ATTACK_ENV_SOFT","env_w":prod.LIVE_EXHIBITION_ENV_W,"q":prod.LIVE_EXHIBITION_Q}
    )
    relaxed,relaxed_pars=v332.fit_apply(
        train,test,{"family":"ATTACK_ENV_SOFT","env_w":RELAXED_ENV_W,"q":RELAXED_Q}
    )
    return {
        "standard_pass":bool(len(standard)==1),
        "relaxed_pass":bool(len(relaxed)==1),
        "standard_params":standard_pars,
        "relaxed_params":relaxed_pars,
        "standard_score":_score_from_pars(feat,standard_pars,prod.LIVE_EXHIBITION_ENV_W),
        "relaxed_score":_score_from_pars(feat,relaxed_pars,RELAXED_ENV_W),
        "feat":feat,
        "corrected_ex":{str(b):float(ex[b]) for b in range(2,7)},
        "corrected_st":{str(b):float(st[b]) for b in range(2,7)},
        "corrected_straight":{str(b):float(os[b]["straight"]) for b in range(2,7)},
        "corrected_orig_avg":{str(b):float(os[b]["avg"]) for b in range(2,7)},
        "exhibition_hashes":probe.get("sha256",{}),
    }


def _select_lane(base:dict, ex:dict, b1_recent_p2:float):
    hp=float(base["final_head_p"]); mass=float(base["opp_mass"])
    mass_ok=mass>=float(prod.LIVE_OPPONENT_MASS_MIN)

    if hp>=float(prod.LIVE_HEAD_CUTOFF) and mass_ok and ex["standard_pass"]:
        return "FORMAL_LIVE",True,"HEAD_MASS_STANDARD_EXHIBITION"

    if (
        bool(prod.PLAYER_HISTORY_EXPANSION_PROMOTED)
        and float(prod.PLAYER_HISTORY_EXPANSION_HEAD_MIN)<=hp<float(prod.PLAYER_HISTORY_EXPANSION_HEAD_MAX)
        and mass>=float(prod.PLAYER_HISTORY_EXPANSION_OPPONENT_MASS_MIN)
        and b1_recent_p2>=float(prod.PLAYER_HISTORY_EXPANSION_THRESHOLD)
        and ex["standard_pass"]
    ):
        return "PLAYER_HISTORY_EXPANSION",True,"PH_RECENT_P2_STANDARD_EXHIBITION"

    env=float(ex["feat"].get("env_pair",float("nan")))
    if (
        bool(prod.HEAD_VOLUME_EXPANSION_PROMOTED)
        and float(prod.HEAD_VOLUME_EXPANSION_HEAD_MIN)<=hp<float(prod.HEAD_VOLUME_EXPANSION_HEAD_MAX)
        and mass_ok
        and ex["relaxed_pass"]
        and math.isfinite(env)
        and env<=float(prod.HEAD_VOLUME_EXPANSION_ENV_PAIR_MAX)
    ):
        return "HEAD_VOLUME_EXPANSION",True,"RELAXED_EXHIBITION_ENV_PAIR"

    return "DROP",False,"PROMOTED_HEAD_GATE_NOT_SATISFIED"


def _dutch(tickets:list[str],odds_map:dict[str,float],budget:int=BUDGET_YEN,unit:int=UNIT_YEN):
    if not tickets:
        return []
    odds=[float(odds_map[t]) for t in tickets]
    if any((not math.isfinite(o) or o<=0) for o in odds):
        raise RuntimeError("invalid ticket odds")
    if len(tickets)*unit>budget:
        raise RuntimeError("too many tickets for minimum unit")
    inv=[1.0/o for o in odds]; denom=sum(inv)
    raw=[budget*x/denom for x in inv]
    alloc=[max(unit,int(x//unit)*unit) for x in raw]
    total=sum(alloc)
    while total>budget:
        cand=[i for i,a in enumerate(alloc) if a>unit]
        if not cand:
            raise RuntimeError("cannot reduce allocation to budget")
        i=max(cand,key=lambda j:(alloc[j],odds[j]))
        alloc[i]-=unit; total-=unit
    while total+unit<=budget:
        i=max(range(len(tickets)),key=lambda j:(raw[j]-alloc[j],-odds[j]))
        alloc[i]+=unit; total+=unit
    return alloc


def _call_existing_finalizer(base:dict,ex:dict,selected:bool,lane:str,deadline:str,out_path:Path):
    actual_hp=float(base["final_head_p"])
    scoring_hp=max(actual_hp,float(prod.LIVE_HEAD_CUTOFF)) if selected and lane!="FORMAL_LIVE" else actual_hp
    merged=dict(base)
    merged.update({
        "deadline_jst":deadline,
        "evaluated_at_jst":datetime.now(JST).isoformat(),
        "minutes_to_deadline":None,
        "exhibition_ready":True,
        "head_exhibition_pass":bool(selected),
        "corrected_ex":ex["corrected_ex"],
        "corrected_st":ex["corrected_st"],
        "corrected_straight":ex["corrected_straight"],
        "corrected_orig_avg":ex["corrected_orig_avg"],
        "exhibition_hashes":ex["exhibition_hashes"],
        "final_head_p":scoring_hp,
        "result_or_payout_used":False,
        "chronology_guard":True,
    })
    tmp_in=out_path.with_suffix(".formal-input.json")
    tmp_out=out_path.with_suffix(".formal-output.json")
    tmp_in.parent.mkdir(parents=True,exist_ok=True)
    tmp_in.write_text(json.dumps(merged,ensure_ascii=False,indent=2),encoding="utf-8")
    cp=subprocess.run(
        [sys.executable,"run_1head_v351_live_finalize.py","--input",str(tmp_in),"--out",str(tmp_out)],
        check=False,text=True,capture_output=True
    )
    if cp.returncode != 0:
        raise RuntimeError(
            "existing v351 finalizer failed "
            f"rc={cp.returncode} stdout={cp.stdout[-2000:]} stderr={cp.stderr[-4000:]}"
        )
    formal=_load_json(tmp_out)
    if selected and formal.get("status")!="PASS":
        raise RuntimeError(f"selected promoted lane failed existing finalizer: {formal.get('status')} {cp.stdout[-500:]}")
    formal["final_head_p"]=actual_hp
    formal["head_scoring_bridge_p"]=scoring_hp
    return formal


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True,type=Path)
    ap.add_argument("--probe",required=True,type=Path)
    ap.add_argument("--train",required=True,type=Path)
    ap.add_argument("--daily-state",required=True,type=Path)
    ap.add_argument("--race-cards",required=True,type=Path)
    ap.add_argument("--deadline-jst",required=True)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--odds-json",type=Path,default=None,help="test-only current odds mapping")
    a=ap.parse_args()

    base=_load_json(a.base); probe=_load_json(a.probe); state=_load_json(a.daily_state)
    if base.get("result_or_payout_used") is not False or not base.get("chronology_guard"):
        raise RuntimeError("unsafe base cache")
    code=str(base.get("race_code","")).zfill(12)
    if len(code)!=12 or not code.isdigit():
        raise RuntimeError("invalid race_code")
    if state.get("target_date")!=f"{code[:4]}-{code[4:6]}-{code[6:8]}":
        raise RuntimeError("daily state target-date mismatch")
    if str(base.get("training_cutoff"))!=str(state.get("history_end")):
        raise RuntimeError("base/state cutoff mismatch")

    cards=_cards_by_code(a.race_cards)
    if code not in cards:
        raise RuntimeError("target race missing from current race cards")
    b1_recent=_recent_p2_from_state(state,cards[code],1)
    ex=_build_exhibition(base,probe,state,a.train)
    lane,selected,reason=_select_lane(base,ex,b1_recent)
    formal=_call_existing_finalizer(base,ex,selected,lane,a.deadline_jst,a.out)

    feat=ex["feat"]
    pickup=bool(
        selected and lane=="HEAD_VOLUME_EXPANSION" and bool(prod.HEAD_VOLUME_PICKUP_PROMOTED)
        and math.isfinite(float(feat.get("sec_ex_mean_margin",float("nan"))))
        and float(feat["sec_ex_mean_margin"])<=float(prod.HEAD_VOLUME_PICKUP_SEC_EX_MEAN_MARGIN_MAX)
    )
    opp_pickup=bool(
        selected and lane=="HEAD_VOLUME_EXPANSION" and bool(prod.HEAD_VOLUME_OPPONENT_PICKUP_PROMOTED)
        and (
            float(feat.get("covered_turn_weak_margin",float("-inf")))>=float(prod.HEAD_VOLUME_OPPONENT_PICKUP_TURNWEAK_MIN)
            or (ex["relaxed_score"] is not None and ex["relaxed_score"]>=float(prod.HEAD_VOLUME_OPPONENT_PICKUP_V332_MIN))
        )
    )

    out=dict(formal)
    out.update({
        "schema":"1head-current-live-decision-v1",
        "decision":"PASS" if not selected else "PENDING_ODDS",
        "head_selection_lane":lane,
        "head_selection_reason":reason,
        "head_prob":float(base["final_head_p"]),
        "opponent_mass":float(base["opp_mass"]),
        "b1_pl_recent_p2":b1_recent,
        "player_history_threshold":float(prod.PLAYER_HISTORY_EXPANSION_THRESHOLD),
        "standard_exhibition_pass":bool(ex["standard_pass"]),
        "relaxed_exhibition_pass":bool(ex["relaxed_pass"]),
        "standard_exhibition_score":ex["standard_score"],
        "relaxed_exhibition_score":ex["relaxed_score"],
        "env_pair":float(feat["env_pair"]) if math.isfinite(float(feat.get("env_pair",float("nan")))) else None,
        "sec_ex_mean_margin":float(feat["sec_ex_mean_margin"]) if math.isfinite(float(feat.get("sec_ex_mean_margin",float("nan")))) else None,
        "covered_turn_weak_margin":float(feat["covered_turn_weak_margin"]) if math.isfinite(float(feat.get("covered_turn_weak_margin",float("nan")))) else None,
        "head_volume_pickup":pickup,
        "head_volume_opponent_pickup":opp_pickup,
        "target_race_result_used":False,
        "payout_used":False,
        "result_or_payout_used":False,
        "chronology_guard":True,
    })

    if not selected:
        out["decision"]="PASS"
        out["tickets"]=[]
        out["ticket_odds"]={}
        out["live_stakes_yen"]=[]
        out["live_total_stake_yen"]=0
    else:
        tickets=list(formal.get("tickets") or [])
        if not tickets:
            raise RuntimeError("selected lane has no tickets")
        try:
            if a.odds_json:
                raw=_load_json(a.odds_json)
                odds_map=raw.get("odds",raw)
                fetched=raw.get("fetched_at_jst") if isinstance(raw,dict) else None
                source="provided_test_odds"
            else:
                market=fetch_odds3t(code[:8],code[8:10],int(code[10:12]))
                odds_map=market["odds"]; fetched=market.get("fetched_at_jst"); source=market.get("source","boatrace_official_live")
            miss=[t for t in tickets if t not in odds_map or float(odds_map[t])<=0]
            if miss:
                raise RuntimeError(f"current odds missing selected tickets {miss}")
            ticket_odds={t:float(odds_map[t]) for t in tickets}
            stakes=_dutch(tickets,ticket_odds)
            out.update({
                "decision":"BET",
                "ticket_odds":ticket_odds,
                "live_stakes_yen":stakes,
                "live_stake_map_yen":{t:int(s) for t,s in zip(tickets,stakes)},
                "live_total_stake_yen":int(sum(stakes)),
                "estimated_payout_yen":{t:round(float(ticket_odds[t])*int(s)) for t,s in zip(tickets,stakes)},
                "composite_odds":1.0/sum(1.0/float(ticket_odds[t]) for t in tickets),
                "odds_source":source,
                "odds_fetched_at_jst":fetched,
                "odds_used":True,
            })
        except Exception as e:
            out.update({
                "decision":"NO_BET_DATA_NOT_READY",
                "ticket_odds":{},
                "live_stakes_yen":[],
                "live_total_stake_yen":0,
                "odds_error":str(e),
                "odds_used":False,
            })

    out["decision_time_jst"]=datetime.now(JST).isoformat()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print("ONEHEAD_CURRENT_LIVE_DECISION",json.dumps({
        "race_code":code,"decision":out["decision"],"lane":lane,"head_prob":out["head_prob"],
        "opp_mass":out["opponent_mass"],"env_pair":out["env_pair"],"tickets":out.get("tickets",[]),
        "live_total_stake_yen":out.get("live_total_stake_yen",0),
        "target_race_result_used":False,"payout_used":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
