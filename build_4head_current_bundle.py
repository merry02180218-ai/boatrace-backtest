#!/usr/bin/env python3
"""Build the result-blind upstream bundle for frozen HEAD4 v291 VARN.

This adapter converts the repo's proven flat pre-result feature schema plus the
six current exhibition rows into the bundle consumed by
run_4head_v291_varn_auto_live.py.  It never reads outcomes, payouts or odds.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from typing import Any,Mapping

class BundleBuildError(RuntimeError): pass

A_DIRECT=("v91_ex","score_CORR20_v91","score_wind_v83","score_RAW20_v91","score_BASE_v91","preview_comp",
          "opp_grade_b1_v93","opp_score_b1_v93","opp_national_b1_v93","b1_pl_all_win","b1_pl_all_p2","b1_pl_frame_win","b4_pl_recent_p2")
CUR=("cur_ex","cur_st","cur_orig_lap","cur_orig_turn","cur_orig_straight","cur_orig_avg")
V93=("grade","national","local","motor","nst")
PL=("all_p2","all_win","frame_p2","recent_p2","frame_win")
ST=("raw","raw_strength","raw_rank","corr_strength","corr_rank")
FORBID=("winner","second","third","payout","kimarite","result","profit","return","odds")

def _num(name:str,v:Any)->float:
    try:x=float(v)
    except (TypeError,ValueError) as e: raise BundleBuildError(f"invalid {name}") from e
    if not math.isfinite(x): raise BundleBuildError(f"non-finite {name}")
    return x

def _need(r:Mapping[str,Any],k:str)->float:
    if k not in r: raise BundleBuildError(f"missing flat feature {k}")
    return _num(k,r[k])

def _relative(r:Mapping[str,Any],tail:str,a:int,b:int)->float:
    return _need(r,f"b{a}_pl_{tail}")-_need(r,f"b{b}_pl_{tail}")

def build_a(r:Mapping[str,Any])->dict[str,float]:
    a={k:_need(r,k) for k in A_DIRECT}
    a.update({
      "rel_pl_all_win_4v1":_relative(r,"all_win",4,1),
      "rel_pl_all_p2_4v1":_relative(r,"all_p2",4,1),
      "rel_pl_recent_p2_4v1":_relative(r,"recent_p2",4,1),
      "rel_pl_recent_p2_4v3":_relative(r,"recent_p2",4,3),
    })
    # Exact artifact order.
    order=("v91_ex","score_CORR20_v91","score_wind_v83","score_RAW20_v91","score_BASE_v91","preview_comp",
      "rel_pl_all_win_4v1","rel_pl_all_p2_4v1","rel_pl_recent_p2_4v1","opp_grade_b1_v93","opp_score_b1_v93",
      "opp_national_b1_v93","b1_pl_all_win","b1_pl_all_p2","b1_pl_frame_win","rel_pl_recent_p2_4v3","b4_pl_recent_p2")
    return {k:a[k] for k in order}

def build_boats(r:Mapping[str,Any],current:Mapping[str,Any])->dict[str,dict[str,float]]:
    out={}
    for b in range(1,7):
        c=current.get(str(b),current.get(b))
        if not isinstance(c,Mapping): raise BundleBuildError(f"missing current exhibition boat {b}")
        z={k:_num(f"boat{b}.{k}",c.get(k)) for k in CUR}
        if b!=4:
            for k in V93:z[f"v93_{k}"]=_need(r,f"opp_{k}_b{b}_v93")
            z["pos_boat_number"]=float(b);z["pos_inside4"]=float(b<4);z["pos_outside4"]=float(b>4);z["pos_distance4"]=float(abs(b-4))
            for k in PL:z[f"pref_pl_{k}"]=_need(r,f"b{b}_pl_{k}")
            for k in ST:z[f"suf_st_{k}"]=_need(r,f"st_{k}_b{b}")
        out[str(b)]=z
    return out

def build(src:Mapping[str,Any])->dict[str,Any]:
    r=src.get("flat_row") or {}
    if not isinstance(r,Mapping): raise BundleBuildError("flat_row must be mapping")
    bad=[k for k in r if any(x in str(k).lower() for x in FORBID)]
    # Presence of result-like columns in a wide historical row is allowed only if
    # caller explicitly strips them; fail closed so LIVE callers cannot leak them.
    if bad: raise BundleBuildError("forbidden result/market columns present: "+",".join(sorted(map(str,bad))[:12]))
    code=str(src.get("race_code","")).zfill(12)
    if len(code)!=12 or not code.isdigit(): raise BundleBuildError("invalid race_code")
    env=src.get("env_primitives")
    if not isinstance(env,Mapping): raise BundleBuildError("env_primitives must be mapping")
    return {"race_code":code,"PRE":_num("PRE",src.get("PRE")),"POST":_num("POST",src.get("POST")),
            "env_primitives":dict(env),"a_features":build_a(r),"boats":build_boats(r,src.get("current_boats") or {}),
            "_source_meta":{"result_blind":True,"odds_used":False,"jul_aug_labels_used":False,"september_labels_used":False,"v96_used":False}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input-json',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    out=build(json.loads(Path(a.input_json).read_text(encoding='utf-8')))
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'READY','race_code':out['race_code'],'out':a.out},ensure_ascii=False))
if __name__=='__main__':main()
