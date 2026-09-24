#!/usr/bin/env python3
"""Pristine September validation for frozen INNER12 Shadow V4/V6.

This is the FIRST INNER12 read of September outcomes, explicitly authorized by
the user after all Jun-Aug head gates and tickets were frozen.

Frozen logic, unchanged:
Stage-A GLOBAL gate:
- mean Waku10 start-rank(1,2) >= 3.7
- mean prior actual-ST(1,2) >= 0.17811274129319477
- min prior late18(1,2) >= 0.43497650793650783

Exact existing 4HEAD exclusion:
- frozen HEAD4_PH5_PRODUCTION_V31_20260831 head probability
- production selected iff hp >= .36 AND orig4_adv_inside >= -.06

Shadow V1:
- existing 4HEAD NONFIRE
- boat4 prior_late20 <= .20 OR boat5 prior_late20 >= .40

Shadow V2:
A = Waku10 ST3 - ST4 >= .038
B = corrected predicted actual ST3 - ST5 <= -.09
- A_only = A and not B
- B_only = B and not A
- both/neither = PASS

Operational V4:
- A_only -> heads 3 and 4
- B_only AND inner recent3-ST absdiff >= .04 -> head 3
- otherwise PASS

Tickets V6:
- exact frozen LEAN/BALANCED/WIDE sets imported from research_inner12_ticket_roi_v6.py
- JPY5,000 inverse-odds Dutch
- report ALL and composite>=5 exactly as frozen

Causality:
For each target day, all features/decisions/tickets are frozen using history through
target_date-1 plus target-day pre-race/current-exhibition data. Only AFTER every
race decision for that day is frozen are target-day results joined and histories
updated. No September outcome is used to tune any threshold, route, ticket, or gate.
"""
from __future__ import annotations

import csv, json, math, os
from collections import defaultdict, deque
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

from backtest import race_features
from backtest_v51_lane_corrected_tickets import corrected_direct
import run_4head_120r_lastminute_fast as h4
from research_inner12_stageb_route_discovery_v1 import (
    player_stats, ex_bias, ex_st_map, actual_st_map, clean_name, ff, ii
)
import research_inner12_ticket_roi_v6 as v6

ROOT = Path(__file__).resolve().parents[1]
BRC = Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
OUT = Path(os.environ.get("INNER12_SEP_OUTDIR","/tmp/inner12_unseen_sep_v7"))
OUT.mkdir(parents=True,exist_ok=True)

HISTORY_START=date(2025,10,1)
VALIDATE_START=date(2026,9,1)
VALIDATE_END=date.fromisoformat(os.environ.get("INNER12_SEP_END","2026-09-24"))

STAGEA_WAKU_SR=3.7
STAGEA_PRIOR_ST=0.17811274129319477
STAGEA_LATE18=0.43497650793650783
B4_LATE20_MAX=.20
B5_LATE20_MIN=.40
A_GAP34_WAKU_ST=.038
B_PRED35_MAX=-.09
B_STRONG_RECENT3_GAP=.04

def rows_local(rel:str):
    p=BRC/rel
    if not p.is_file(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def bycode(rs):
    out={}
    for r in rs:
        s=str(r.get("レースコード",r.get("race_code","")) or "").strip()
        if not s: continue
        if s.endswith(".0"): s=s[:-2]
        out[s.zfill(12)]=r
    return out

def num(v):
    try:
        x=float(str(v).replace("%","").strip())
        return x if math.isfinite(x) else None
    except Exception:return None

def blank_ph():
    return {
        "n":0,"w":0,"p2":0,
        "nf":defaultdict(int),"wf":defaultdict(int),"p2f":defaultdict(int),
        "recent_p2":deque(maxlen=30),
    }

def pflat_for_card(card,ph_state):
    out={}
    for b in range(1,7):
        reg=str(card.get(f"艇{b}_登録番号","")).strip()
        s=ph_state[reg] if reg else blank_ph()
        n=s["n"]; nf=s["nf"][str(b)]; recent=list(s["recent_p2"])
        vals={
            "all_win":(s["w"]+2/6)/(n+2),
            "all_p2":(s["p2"]+2/3)/(n+2),
            "frame_win":(s["wf"][str(b)]+3*.125)/(nf+3),
            "frame_p2":(s["p2f"][str(b)]+3*.25)/(nf+3),
            "recent_p2":sum(recent)/len(recent) if recent else 1/3,
        }
        for k,v in vals.items(): out[f"b{b}_pl_{k}"]=round(float(v),12)
    return out

def orig_avg_ready(orr):
    if not orr:return False
    used=0
    for k in range(1,5):
        label=str(orr.get(f"計測項目{k}","") or "").strip()
        vals=[num(orr.get(f"艇{b}_値{k}")) for b in range(1,7)]
        if not label and not any(v is not None for v in vals): continue
        if not any(v is not None for v in vals): continue
        used+=1
        if not all(v is not None for v in vals): return False
    return used>0

def st_bias(st_sum,st_n,global_sum,global_n):
    g=(global_sum/global_n) if global_n else .15
    return {b:((st_sum[b]/st_n[b])-g if st_n[b] else 0.0) for b in range(1,7)}

def build_h4_exhibition(code,tkz,stt,orig,bias):
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    if any(b not in ex or b not in st or b not in os for b in range(1,7)):
        return None
    sr=stt.get(code,{})
    raw={}
    for b in range(1,7):
        v=num(sr.get(f"艇{b}_スタート展示"))
        if v is None:return None
        raw[b]=v
    raw_order=sorted(raw,key=lambda b:(raw[b],b))
    raw_rank={b:i+1 for i,b in enumerate(raw_order)}
    raw_strength={b:1-i/5 for i,b in enumerate(raw_order)}
    corr={b:raw[b]-bias[b] for b in range(1,7)}
    corr_order=sorted(corr,key=lambda b:(corr[b],b))
    corr_rank={b:i+1 for i,b in enumerate(corr_order)}
    corr_strength={b:1-i/5 for i,b in enumerate(corr_order)}
    boats={}
    sf={}
    for b in range(1,7):
        boats[str(b)]={
            "cur_ex":float(ex[b]),
            "cur_st":float(st[b]),
            "cur_orig_lap":float(os[b]["lap"]),
            "cur_orig_turn":float(os[b]["turn"]),
            "cur_orig_straight":float(os[b]["straight"]),
            "cur_orig_avg":float(os[b]["avg"]),
        }
        sf[f"st_raw_b{b}"]=float(raw[b])
        sf[f"st_raw_rank_b{b}"]=int(raw_rank[b])
        sf[f"st_corr_rank_b{b}"]=int(corr_rank[b])
        sf[f"st_raw_strength_b{b}"]=round(float(raw_strength[b]),4)
        sf[f"st_corr_strength_b{b}"]=round(float(corr_strength[b]),4)
    return {
        "schema":"historical_replay_head4_exhibition_v1",
        "race_code":code,
        "current_boats":boats,
        "st_flat":sf,
        "orig_avg_available":orig_avg_ready(orig.get(code,{})),
        "result_blind":True,
        "odds_used":False,
    }

def load_day_odds(d:date):
    out={};source={}
    p=BRC/f"data/previews/od3/{d:%Y/%m/%d}.csv"
    if p.is_file():
        try:q=pd.read_csv(p,dtype={"レースコード":str})
        except Exception:q=pd.DataFrame()
        for _,r in q.iterrows():
            code=str(r.get("レースコード","")).strip()
            if code.endswith(".0"):code=code[:-2]
            code=code.zfill(12)
            m={}
            for a in range(1,7):
                for b in range(1,7):
                    if b==a:continue
                    for c in range(1,7):
                        if c in (a,b):continue
                        k=f"{a}-{b}-{c}";v=num(r.get(f"3連単_{k}"))
                        if v is not None and v>0:m[k]=v
            if len(m)==120:
                out[code]=m;source[code]="predeadline_od3"
    cp=ROOT/f"data/official_closing_odds3t/{d:%Y/%m/%d}.csv"
    if cp.is_file():
        try:q=pd.read_csv(cp,dtype={"jcd":str})
        except Exception:q=pd.DataFrame()
        for _,r in q.iterrows():
            try:rn=int(float(r.get("rno",0)))
            except Exception:rn=0
            j=str(r.get("jcd","")).zfill(2)
            code=f"{d:%Y%m%d}{j}{rn:02d}"
            if rn<1 or code in out:continue
            m={}
            for a in range(1,7):
                for b in range(1,7):
                    if b==a:continue
                    for c in range(1,7):
                        if c in (a,b):continue
                        k=f"{a}-{b}-{c}";v=num(r.get(k))
                        if v is not None and v>0:m[k]=v
            if len(m)==120:
                out[code]=m;source[code]="closing_fallback"
    return out,source

def update_histories(cards,res,stt,stage_st,global_st,ex_bias_state,global_ex_bias,ph_state):
    # result-based histories are updated only AFTER today's decisions were frozen.
    for code,card in cards.items():
        rr=res.get(code,{})
        try:w=int(float(rr.get("1着_艇番"))); sec=int(float(rr.get("2着_艇番")))
        except Exception:w=sec=0
        if w in range(1,7) and sec in range(1,7) and w!=sec:
            for b in range(1,7):
                reg=str(card.get(f"艇{b}_登録番号","")).strip()
                if reg:
                    s=ph_state[reg];s["n"]+=1;s["w"]+=int(w==b);s["p2"]+=int(w==b or sec==b)
                    s["nf"][str(b)]+=1;s["wf"][str(b)]+=int(w==b);s["p2f"][str(b)]+=int(w==b or sec==b)
                    s["recent_p2"].append(int(w==b or sec==b))
        am=actual_st_map(rr); em=ex_st_map(stt.get(code,{}))
        for b in range(1,7):
            if b not in am:continue
            name=clean_name(card.get(f"艇{b}_選手名",""))
            if not name:continue
            ac,ast=am[b]
            stage_st[name].append(ast)
            if len(stage_st[name])>160:stage_st[name]=stage_st[name][-160:]
            global_st.append(ast)
            if len(global_st)>30000:del global_st[:5000]
            if b in em and em[b][0]==ac:
                z=ast-em[b][1]
                ex_bias_state[name].append(z)
                if len(ex_bias_state[name])>100:ex_bias_state[name]=ex_bias_state[name][-100:]
                global_ex_bias.append(z)
                if len(global_ex_bias)>30000:del global_ex_bias[:5000]

def update_stt_bias(stt,st_sum,st_n,global_ref):
    for r in stt.values():
        for b in range(1,7):
            v=num(r.get(f"艇{b}_スタート展示"))
            if v is not None and -.30<v<1.0:
                st_sum[b]+=v;st_n[b]+=1;global_ref[0]+=v;global_ref[1]+=1

def summarize_roi(df):
    if not len(df):return {"R":0,"hits":0,"stake":0,"payout":0.0,"profit":0.0,"roi":None}
    stake=int(df.stake.sum());payout=float(df.payout.sum())
    return {
        "R":int(len(df)),"hits":int(df.ticket_hit.sum()),
        "hit_rate":float(df.ticket_hit.mean()),"stake":stake,"payout":payout,
        "profit":float(payout-stake),"roi":float(100*payout/stake) if stake else None,
        "predeadline_R":int((df.odds_source=="predeadline_od3").sum()),
        "closing_fallback_R":int((df.odds_source=="closing_fallback").sum()),
    }

def main():
    if VALIDATE_END<VALIDATE_START or VALIDATE_END>=date(2026,9,25):
        raise RuntimeError(f"INVALID_VALIDATE_END_{VALIDATE_END}")

    stage_st=defaultdict(list);global_st=[]
    ex_bias_state=defaultdict(list);global_ex_bias=[]
    ph_state=defaultdict(blank_ph)
    st_sum=defaultdict(float);st_n=defaultdict(int);global_stt=[0.0,0]

    frozen=[];settled=[];market_rows=[]
    audit={
        "history_start":str(HISTORY_START),"validate_start":str(VALIDATE_START),"validate_end":str(VALIDATE_END),
        "thresholds_frozen_before_september_read":True,
        "tickets_frozen_before_september_read":True,
        "september_used_for_tuning":False,
    }

    d=HISTORY_START
    while d<=VALIDATE_END:
        ymd=d.strftime("%Y/%m/%d")
        cards=bycode(rows_local(f"data/programs/race_cards/{ymd}.csv"))
        w10=bycode(rows_local(f"data/programs/waku10/{ymd}.csv"))
        stt=bycode(rows_local(f"data/previews/stt/{ymd}.csv"))
        tkz=bycode(rows_local(f"data/previews/tkz/{ymd}.csv"))
        orig=bycode(rows_local(f"data/previews/original_exhibition/{ymd}.csv"))

        day_decisions=[]
        if d>=VALIDATE_START:
            bias=st_bias(st_sum,st_n,global_stt[0],global_stt[1])
            for code,card in cards.items():
                wr=w10.get(code)
                if not wr:continue
                x=race_features(card,wr)
                if any(b not in x for b in (1,2,3,4,5)):continue

                pmeta={}
                for b in (1,2,3,4,5):
                    name=clean_name(card.get(f"艇{b}_選手名",""))
                    pmeta[b]=player_stats(stage_st[name],global_st)

                stagea=(
                    (x[1]["waku_sr"]+x[2]["waku_sr"])/2 >= STAGEA_WAKU_SR and
                    (pmeta[1]["prior_st_mean"]+pmeta[2]["prior_st_mean"])/2 >= STAGEA_PRIOR_ST and
                    min(pmeta[1]["prior_late18_rate"],pmeta[2]["prior_late18_rate"]) >= STAGEA_LATE18
                )
                if not stagea:continue

                exh=build_h4_exhibition(code,tkz,stt,orig,bias)
                if exh is None:continue
                pflat=pflat_for_card(card,ph_state)
                hp=h4.ph5_head_prob_live(card,wr,exh,pflat)
                sadv=h4.structural_advantages(exh)
                existing4=bool(hp>=.36 and sadv["orig4_adv_inside"] is not None and sadv["orig4_adv_inside"]>=-.06)

                em=ex_st_map(stt.get(code,{}))
                pred35=None
                if all(b in em for b in (3,5)):
                    n3=clean_name(card.get("艇3_選手名",""));n5=clean_name(card.get("艇5_選手名",""))
                    pred3=em[3][1]+ex_bias(ex_bias_state[n3],global_ex_bias)
                    pred5=em[5][1]+ex_bias(ex_bias_state[n5],global_ex_bias)
                    pred35=pred3-pred5

                base=(not existing4) and (
                    pmeta[4]["prior_late20_rate"]<=B4_LATE20_MAX or
                    pmeta[5]["prior_late20_rate"]>=B5_LATE20_MIN
                )
                gap34=float(x[3]["waku_st"])-float(x[4]["waku_st"])
                A=bool(base and gap34>=A_GAP34_WAKU_ST)
                B=bool(base and pred35 is not None and pred35<=B_PRED35_MAX)
                branch="neither"
                if A and not B:branch="A_only"
                elif B and not A:branch="B_only"
                elif A and B:branch="both"

                recent3gap=abs(float(pmeta[1]["prior_recent3_st"])-float(pmeta[2]["prior_recent3_st"]))
                action="PASS";heads=""
                if branch=="A_only":
                    action="A_DUAL_3_4";heads="3|4"
                elif branch=="B_only" and recent3gap>=B_STRONG_RECENT3_GAP:
                    action="B_3HEAD";heads="3"

                rec={
                    "date":str(d),"race_code":code,"venue":code[8:10],"rno":int(code[10:12]),
                    "stagea":1,"head4_hp":hp,"orig4_adv_inside":sadv["orig4_adv_inside"],
                    "existing4_production_bet":int(existing4),
                    "b4_prior_late20":pmeta[4]["prior_late20_rate"],
                    "b5_prior_late20":pmeta[5]["prior_late20_rate"],
                    "gap34_waku_st":gap34,"pred3_vs5":pred35,
                    "inner_recent3_absdiff":recent3gap,
                    "branch":branch,"action":action,"heads":heads,
                    "decision_frozen_before_result":1,
                }
                frozen.append(rec);day_decisions.append(rec)

        # Odds are market-time information; load after head/ticket decision freeze.
        day_odds,day_oddsrc=load_day_odds(d) if d>=VALIDATE_START else ({},{})
        # NOW open same-day outcomes, after every decision for this day is frozen.
        res=bycode(rows_local(f"data/results/realtime/{ymd}.csv"))

        if d>=VALIDATE_START:
            for rec in day_decisions:
                if rec["action"]=="PASS":continue
                rr=res.get(rec["race_code"],{})
                try:
                    w=int(float(rr.get("1着_艇番")));s=int(float(rr.get("2着_艇番")));t=int(float(rr.get("3着_艇番")))
                except Exception:
                    continue
                actual=f"{w}-{s}-{t}"
                heads=rec["heads"].split("|")
                z=dict(rec)
                z.update({"winner":w,"second":s,"third":t,"actual_ticket":actual,
                          "head_hit":int(str(w) in heads)})
                settled.append(z)
                branch_key="A" if rec["action"]=="A_DUAL_3_4" else "B"
                om=day_odds.get(rec["race_code"])
                for pol,branches in v6.TICKETS.items():
                    tickets=list(branches[branch_key])
                    exact=int(actual in tickets)
                    if om is None or any(k not in om for k in tickets):
                        market_rows.append({
                            "policy":pol,"date":str(d),"race_code":rec["race_code"],"action":rec["action"],
                            "gate":"MISSING_ODDS","odds_available":0,"odds_source":"missing","points":len(tickets),
                            "head_hit":z["head_hit"],"ticket_hit":exact,"stake":0,"payout":0.0,"profit":0.0,
                            "composite":None,"actual_ticket":actual,
                        })
                        continue
                    ovs=[float(om[k]) for k in tickets]
                    comp=v6.composite(ovs);stakes=v6.dutch5000(ovs)
                    for gate,bet in (("ALL",True),("COMP5",bool(comp is not None and comp>=v6.COMP_CUT))):
                        stake=v6.BANK if bet else 0;payout=0.0;hit=0
                        if bet and actual in tickets:
                            idx=tickets.index(actual);hit=1;payout=float(stakes[idx])*ovs[idx]
                        market_rows.append({
                            "policy":pol,"date":str(d),"race_code":rec["race_code"],"action":rec["action"],
                            "gate":gate,"odds_available":1,"odds_source":day_oddsrc[rec["race_code"]],
                            "points":len(tickets),"head_hit":z["head_hit"],"ticket_hit":hit,
                            "stake":stake,"payout":payout,"profit":payout-stake,
                            "composite":comp,"actual_ticket":actual,
                        })

        update_histories(cards,res,stt,stage_st,global_st,ex_bias_state,global_ex_bias,ph_state)
        update_stt_bias(stt,st_sum,st_n,global_stt)
        d+=timedelta(days=1)

    fd=pd.DataFrame(frozen);sd=pd.DataFrame(settled);md=pd.DataFrame(market_rows)
    fd.to_csv(OUT/"all_stagea_frozen.csv",index=False)
    sd.to_csv(OUT/"selected_settled.csv",index=False)
    md.to_csv(OUT/"market_detail.csv",index=False)

    selected_frozen=fd[fd.action.ne("PASS")] if len(fd) else fd
    head_summary={
        "stagea_R":int(len(fd)),
        "existing4_overlap_R":int(fd.existing4_production_bet.sum()) if len(fd) else 0,
        "selected_frozen_R":int(len(selected_frozen)),
        "settled_R":int(len(sd)),
        "head_hits":int(sd.head_hit.sum()) if len(sd) else 0,
        "head_hit_rate":float(sd.head_hit.mean()) if len(sd) else None,
        "A_R":int((sd.action=="A_DUAL_3_4").sum()) if len(sd) else 0,
        "A_head_hits":int(sd.loc[sd.action.eq("A_DUAL_3_4"),"head_hit"].sum()) if len(sd) else 0,
        "A_head_rate":float(sd.loc[sd.action.eq("A_DUAL_3_4"),"head_hit"].mean()) if len(sd) and (sd.action=="A_DUAL_3_4").any() else None,
        "B_R":int((sd.action=="B_3HEAD").sum()) if len(sd) else 0,
        "B_head_hits":int(sd.loc[sd.action.eq("B_3HEAD"),"head_hit"].sum()) if len(sd) else 0,
        "B_head_rate":float(sd.loc[sd.action.eq("B_3HEAD"),"head_hit"].mean()) if len(sd) and (sd.action=="B_3HEAD").any() else None,
    }
    roi={}
    for pol in v6.TICKETS:
        roi[pol]={}
        for gate in ("ALL","COMP5"):
            q=md[(md.policy==pol)&(md.gate==gate)&(md.odds_available.eq(1))&(md.stake>0)].copy()
            roi[pol][gate]=summarize_roi(q)
            roi[pol][gate]["odds_missing_selected_R"]=int(
                md[(md.policy==pol)&(md.gate=="MISSING_ODDS")].race_code.nunique()
            )

    meta={
        "model_id":"INNER12_PRISTINE_SEPTEMBER_VALIDATION_V7",
        "status":"UNSEEN_VALIDATION",
        "validation_period":[str(VALIDATE_START),str(VALIDATE_END)],
        "frozen_logic_source":{
            "head":"Operational Shadow V4",
            "tickets":"Fixed-ticket ROI Shadow V6",
            "existing4":"HEAD4_PH5_PRODUCTION_V31_20260831",
        },
        "thresholds_or_tickets_changed_after_september_read":False,
        "september_outcomes_read":True,
        "september_used_for_tuning":False,
        "decision_frozen_before_same_day_result":True,
        "production_changed":False,
        "head_summary":head_summary,
        "roi":roi,
        "audit":audit,
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_PRISTINE_SEPTEMBER_VALIDATION_V7_OK")
    print("PERIOD",str(VALIDATE_START),str(VALIDATE_END))
    print("HEAD_SUMMARY",json.dumps(head_summary,ensure_ascii=False))
    print("ROI",json.dumps(roi,ensure_ascii=False))
    print("SEPTEMBER_OUTCOMES_READ_TRUE")
    print("SEPTEMBER_USED_FOR_TUNING_FALSE")
    print("DECISIONS_FROZEN_BEFORE_SAME_DAY_RESULTS")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
