#!/usr/bin/env python3
"""INNER12 opponent V8 inspired by the latest formal 1HEAD opponent architecture.

Purpose
-------
Replace the rejected fixed-combo V6 tickets with per-race dynamic opponent ranking,
while keeping the frozen INNER12 V4 head gate unchanged.

Transferred from latest 1HEAD production (generic pieces only):
- separate SECOND and conditional THIRD models;
- candidate-level causal PLAYERHistory / Waku10 / motor / card / exhibition features;
- opponentCore = .40 EX + .25 corrected-ST + .15 orig-straight + .20 orig-avg;
- opponentCore SECOND coefficient = 0.45;
- opponentCore THIRD coefficient = 1.00;
- pair alpha = 0.70;
- HYBRID ordering starts with best pair, another pair with same second, best pair with another second; keep top 6 per head.

NOT transferred:
- 1HEAD wall3, 5->6, or 1->5 top-up rules; those are head-1-specific mechanisms.

Development:
- fit SECOND/THIRD on Jun-Aug GLOBAL Stage-A races whose actual winner is 3 or 4.
- September labels are never used for fitting, feature choice, coefficients, or thresholds.

Evaluation:
- replay the already-frozen V7 Sep1-24 V4 selected races.
- September is diagnostic here (it has already been opened by V7), not a fresh model-selection holdout.
- reserve future races after Sep24 for prospective shadow validation.

Production unchanged.
"""
from __future__ import annotations

import csv,json,math,os
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import logsumexp
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backtest import race_features,grade_score,clamp,pct_motor
from backtest_v51_lane_corrected_tickets import corrected_direct
import onehead_production_profile as oneprod
import research_inner12_ticket_roi_v6 as v6

BRC=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
STAGEB=Path(os.environ.get("INNER12_STAGEB_ROWS","/tmp/stageb/factor_rows.csv"))
SEP_V7=Path(os.environ.get("INNER12_SEP_V7_ROWS","/tmp/sepv7/all_stagea_frozen.csv"))
OUT=Path(os.environ.get("INNER12_V8_OUTDIR","/tmp/inner12_onehead_opponent_v8"))
OUT.mkdir(parents=True,exist_ok=True)

HISTORY_START=date(2025,10,1)
DEV_START=date(2026,6,1)
DEV_END=date(2026,8,31)
SEP_START=date(2026,9,1)
SEP_END=date(2026,9,24)
HEADS=(3,4)

ALPHA=float(oneprod.TICKET_ALPHA)
G2=float(oneprod.OPPONENT_CORE_SECOND_G2)
G3=float(oneprod.OPPONENT_CORE_THIRD_G3)
C_SECOND=.25
C_THIRD=.25

CORE_W={
    "ex":float(oneprod.ATTACK_CORE_W_ONE_EX),
    "st":float(oneprod.ATTACK_CORE_W_ONE_ST),
    "straight":float(oneprod.ATTACK_CORE_W_ONE_STRAIGHT),
    "avg":float(oneprod.ATTACK_CORE_W_ONE_ORIG_AVG),
}

def rows_local(rel):
    p=BRC/rel
    if not p.is_file():return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def bycode(rs):
    out={}
    for r in rs:
        s=str(r.get("レースコード",r.get("race_code","")) or "").strip()
        if not s:continue
        if s.endswith(".0"):s=s[:-2]
        out[s.zfill(12)]=r
    return out

def ff(x,d=np.nan):
    try:
        v=float(str(x).replace("%","").strip())
        return v if math.isfinite(v) else d
    except Exception:return d

def blank_ph():
    return {"n":0,"w":0,"p2":0,"nf":defaultdict(int),"wf":defaultdict(int),
            "p2f":defaultdict(int),"recent":deque(maxlen=30)}

def phstat(s,b):
    n=s["n"];nf=s["nf"][b];r=list(s["recent"])
    return {
        "pl_all_win":(s["w"]+2/6)/(n+2),
        "pl_all_p2":(s["p2"]+2/3)/(n+2),
        "pl_frame_win":(s["wf"][b]+3*.125)/(nf+3),
        "pl_frame_p2":(s["p2f"][b]+3*.25)/(nf+3),
        "pl_recent_p2":sum(r)/len(r) if r else 1/3,
    }

def lane_bias(st_sum,st_n,gs,gn):
    g=gs/gn if gn else .15
    return {b:(st_sum[b]/st_n[b]-g if st_n[b] else 0.0) for b in range(1,7)}

def complete_preview(code,tkz,stt):
    tr=tkz.get(code,{});sr=stt.get(code,{})
    return (
        all(math.isfinite(ff(tr.get(f"艇{b}_展示タイム"))) for b in range(1,7))
        and all(math.isfinite(ff(sr.get(f"艇{b}_スタート展示"))) for b in range(1,7))
    )

def update_states(cards,res,stt,ph,st_sum,st_n,gref):
    # PLAYERHistory exact causal update by registration number.
    for code in sorted(cards):
        c=cards[code];rr=res.get(code,{})
        try:w=int(float(rr.get("1着_艇番")));s2=int(float(rr.get("2着_艇番")))
        except Exception:w=s2=0
        if w in range(1,7) and s2 in range(1,7) and w!=s2:
            for b in range(1,7):
                reg=str(c.get(f"艇{b}_登録番号","")).strip()
                if not reg:continue
                z=ph[reg];z["n"]+=1;z["w"]+=int(w==b);z["p2"]+=int(w==b or s2==b)
                z["nf"][b]+=1;z["wf"][b]+=int(w==b);z["p2f"][b]+=int(w==b or s2==b)
                z["recent"].append(int(w==b or s2==b))
    # prior-only ST lane bias for next day.
    for r in stt.values():
        for b in range(1,7):
            v=ff(r.get(f"艇{b}_スタート展示"))
            if math.isfinite(v) and -.30<v<1:
                st_sum[b]+=v;st_n[b]+=1;gref[0]+=v;gref[1]+=1

def base_boat_features(x,b,ex,st,os,phs,head):
    z=x[b]
    motor=.62*pct_motor(z["motor2"])+.38*pct_motor(z["motor3"])
    national=clamp((z["wr"]-3.0)/5.0)
    local=clamp((z["local"]-2.5)/5.5)
    waku_wr=clamp(z["waku_wr"]/8.0)
    nst=clamp((.24-z["nst"])/.14)
    core=(CORE_W["ex"]*float(ex[b])+CORE_W["st"]*float(st[b])
          +CORE_W["straight"]*float(os[b]["straight"])+CORE_W["avg"]*float(os[b]["avg"]))
    return {
        "boat":float(b),
        "head":float(head),
        "pos_inside_head":float(b<head),
        "pos_outside_head":float(b>head),
        "pos_distance_head":float(abs(b-head)),
        "grade":float(grade_score(z["grade"])),
        "national":float(national),
        "local":float(local),
        "motor":float(motor),
        "waku_wr":float(waku_wr),
        "waku_st":float(ff(z.get("waku_st"),.18)),
        "waku_sr":float(ff(z.get("waku_sr"),3.5)),
        "nst":float(nst),
        "past_win":float(ff(z.get("past_win"),.0)),
        "ex":float(ex[b]),
        "st":float(st[b]),
        "orig_turn":float(os[b]["turn"]),
        "orig_straight":float(os[b]["straight"]),
        "orig_avg":float(os[b]["avg"]),
        "opponent_core":float(core),
        **{k:float(v) for k,v in phs.items()},
    }

SECOND_FEATURES=[
    "boat","head","pos_inside_head","pos_outside_head","pos_distance_head",
    "grade","national","local","motor","waku_wr","waku_st","waku_sr","nst","past_win",
    "ex","st","orig_turn","orig_straight","orig_avg","opponent_core",
    "pl_all_win","pl_all_p2","pl_frame_win","pl_frame_p2","pl_recent_p2",
    "rel_core_head","rel_national_head","rel_motor_head","rel_waku_st_head","rel_pl_p2_head",
]

THIRD_FEATURES=[
    *["third_"+x for x in SECOND_FEATURES],
    "second_boat","second_pos_inside_head","second_pos_outside_head","second_pos_distance_head",
    "second_opponent_core","second_national","second_motor","second_st","second_pl_all_p2","second_pl_frame_p2",
    "third_minus_second_core","third_minus_second_national","third_minus_second_motor",
    "third_minus_second_st","third_minus_second_pl_all_p2","same_side_of_head",
]

def candidate_map(card,waku,tkz,stt,orig,bias,ph,head):
    code=str(card.get("レースコード","")).zfill(12)
    if not complete_preview(code,tkz,stt):return None
    x=race_features(card,waku)
    if not x or any(b not in x for b in range(1,7)):return None
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    if any(b not in ex or b not in st or b not in os for b in range(1,7)):return None

    phm={}
    for b in range(1,7):
        reg=str(card.get(f"艇{b}_登録番号","")).strip()
        if not reg:return None
        phm[b]=phstat(ph[reg],b)

    raw={b:base_boat_features(x,b,ex,st,os,phm[b],head) for b in range(1,7)}
    h=raw[head]
    for b in range(1,7):
        raw[b]["rel_core_head"]=raw[b]["opponent_core"]-h["opponent_core"]
        raw[b]["rel_national_head"]=raw[b]["national"]-h["national"]
        raw[b]["rel_motor_head"]=raw[b]["motor"]-h["motor"]
        raw[b]["rel_waku_st_head"]=raw[b]["waku_st"]-h["waku_st"]
        raw[b]["rel_pl_p2_head"]=raw[b]["pl_all_p2"]-h["pl_all_p2"]
    return raw

def third_row(raw,head,s,t):
    tr={f"third_{k}":raw[t][k] for k in SECOND_FEATURES}
    tr.update({
        "second_boat":raw[s]["boat"],
        "second_pos_inside_head":raw[s]["pos_inside_head"],
        "second_pos_outside_head":raw[s]["pos_outside_head"],
        "second_pos_distance_head":raw[s]["pos_distance_head"],
        "second_opponent_core":raw[s]["opponent_core"],
        "second_national":raw[s]["national"],
        "second_motor":raw[s]["motor"],
        "second_st":raw[s]["st"],
        "second_pl_all_p2":raw[s]["pl_all_p2"],
        "second_pl_frame_p2":raw[s]["pl_frame_p2"],
        "third_minus_second_core":raw[t]["opponent_core"]-raw[s]["opponent_core"],
        "third_minus_second_national":raw[t]["national"]-raw[s]["national"],
        "third_minus_second_motor":raw[t]["motor"]-raw[s]["motor"],
        "third_minus_second_st":raw[t]["st"]-raw[s]["st"],
        "third_minus_second_pl_all_p2":raw[t]["pl_all_p2"]-raw[s]["pl_all_p2"],
        "same_side_of_head":float((t<head)==(s<head)),
    })
    return tr

def make_model(C):
    return Pipeline([
        ("imp",SimpleImputer(strategy="median")),
        ("sc",StandardScaler()),
        ("lr",LogisticRegression(C=C,max_iter=3000,class_weight="balanced")),
    ])

def softmax(vals):
    a=np.asarray(vals,dtype=float);p=np.exp(a-logsumexp(a));return p

def generic_pair_prob(p2,pc,boats,alpha):
    raw={}
    for s in boats:
        for t in boats:
            if t==s:continue
            raw[(s,t)]=math.exp(alpha*math.log(max(p2[s],1e-12))+(1-alpha)*math.log(max(pc[(s,t)],1e-12)))
    den=sum(raw.values());return {k:v/den for k,v in raw.items()}

def hybrid_order(prob):
    ordinary=sorted(prob,key=lambda x:(-prob[x],x[0],x[1]))
    first=ordinary[0];s=first[0]
    same=[x for x in ordinary if x[0]==s and x!=first]
    other=[x for x in ordinary if x[0]!=s]
    pre=[first]
    if same:pre.append(same[0])
    if other:pre.append(other[0])
    out=[]
    for x in pre+ordinary:
        if x not in out:out.append(x)
    return out

def normalize(q):
    den=sum(max(float(v),0.0) for v in q.values())
    if den<=0:raise RuntimeError("INVALID_NORM")
    return {k:max(float(v),0.0)/den for k,v in q.items()}

def score_head(raw,head,m2,m3,use_core=True):
    boats=[b for b in range(1,7) if b!=head]
    X2=pd.DataFrame([{k:raw[b][k] for k in SECOND_FEATURES} for b in boats])
    sc2=m2.decision_function(X2[SECOND_FEATURES])
    pp=softmax(sc2);p2={b:float(p) for b,p in zip(boats,pp)}

    pc={}
    for s in boats:
        thirds=[t for t in boats if t!=s]
        X3=pd.DataFrame([third_row(raw,head,s,t) for t in thirds])
        sc=m3.decision_function(X3[THIRD_FEATURES]);pr=softmax(sc)
        for t,p in zip(thirds,pr):pc[(s,t)]=float(p)

    if use_core:
        p2=normalize({b:p2[b]*math.exp(G2*(raw[b]["opponent_core"]-.5)) for b in boats})
        z={}
        for s in boats:
            q=normalize({t:pc[(s,t)]*math.exp(G3*(raw[t]["opponent_core"]-.5)) for t in boats if t!=s})
            for t,v in q.items():z[(s,t)]=v
        pc=z
    prob=generic_pair_prob(p2,pc,boats,ALPHA)
    pairs=hybrid_order(prob)[:6]
    return p2,pc,pairs

def load_odds_for(code):
    y,m,d=code[:4],code[4:6],code[6:8]
    p=BRC/f"data/previews/od3/{y}/{m}/{d}.csv"
    if not p.is_file():return None
    q=pd.read_csv(p,dtype={"レースコード":str})
    q["レースコード"]=q["レースコード"].astype(str).str.replace(".0","",regex=False).str.zfill(12)
    z=q[q["レースコード"].eq(code)]
    if len(z)!=1:return None
    r=z.iloc[0];out={}
    for a in range(1,7):
      for b in range(1,7):
       if b==a:continue
       for c in range(1,7):
        if c in (a,b):continue
        k=f"{a}-{b}-{c}";v=ff(r.get(f"3連単_{k}"))
        if math.isfinite(v) and v>0:out[k]=float(v)
    return out if len(out)==120 else None

def metric(z,stake_col,payout_col,hit_col):
    if not len(z):return {"R":0,"hits":0,"roi":None}
    st=float(z[stake_col].sum());pa=float(z[payout_col].sum())
    return {"R":int(len(z)),"hits":int(z[hit_col].sum()),"hit_rate":float(z[hit_col].mean()),
            "stake":st,"payout":pa,"profit":pa-st,"roi":100*pa/st if st else None}

def main():
    stage=pd.read_csv(STAGEB,dtype={"race_code":str});stage.race_code=stage.race_code.astype(str).str.zfill(12)
    train=stage[stage.month.isin(["2026-06","2026-07","2026-08"])].copy()
    sep=pd.read_csv(SEP_V7,dtype={"race_code":str});sep.race_code=sep.race_code.astype(str).str.zfill(12)
    sep_sel=sep[sep.action.ne("PASS")].copy()
    train_codes=set(train.race_code);sep_codes=set(sep.race_code);target_codes=train_codes|sep_codes

    ph=defaultdict(blank_ph);st_sum=defaultdict(float);st_n=defaultdict(int);gref=[0.0,0]
    feature_by_head={};truth={}

    d=HISTORY_START
    while d<=SEP_END:
        ymd=d.strftime("%Y/%m/%d")
        cards=bycode(rows_local(f"data/programs/race_cards/{ymd}.csv"))
        waku=bycode(rows_local(f"data/programs/waku10/{ymd}.csv"))
        tkz=bycode(rows_local(f"data/previews/tkz/{ymd}.csv"))
        stt=bycode(rows_local(f"data/previews/stt/{ymd}.csv"))
        orig=bycode(rows_local(f"data/previews/original_exhibition/{ymd}.csv"))
        bias=lane_bias(st_sum,st_n,gref[0],gref[1])

        # Freeze target features before opening today's outcomes.
        for code in sorted(set(cards)&target_codes):
            card=cards[code];wr=waku.get(code)
            if not wr:continue
            for head in HEADS:
                raw=candidate_map(card,wr,tkz,stt,orig,bias,ph,head)
                if raw is not None:feature_by_head[(code,head)]=raw

        # Outcomes only after all target features of this day are frozen.
        res=bycode(rows_local(f"data/results/realtime/{ymd}.csv"))
        for code in set(cards)&target_codes:
            rr=res.get(code,{})
            try:w=int(float(rr.get("1着_艇番")));s=int(float(rr.get("2着_艇番")));t=int(float(rr.get("3着_艇番")))
            except Exception:continue
            if len({w,s,t})==3 and all(x in range(1,7) for x in (w,s,t)):
                truth[code]=(w,s,t)
        update_states(cards,res,stt,ph,st_sum,st_n,gref)
        d+=timedelta(days=1)

    # Train from Jun-Aug Stage-A only, actual head 3 or 4.
    second_rows=[];third_rows=[];train_races=0
    for code in sorted(train_codes):
        a=truth.get(code)
        if not a or a[0] not in HEADS:continue
        head,s2,t3=a;raw=feature_by_head.get((code,head))
        if raw is None:continue
        train_races+=1
        boats=[b for b in range(1,7) if b!=head]
        for b in boats:
            r={k:raw[b][k] for k in SECOND_FEATURES};r["y"]=int(b==s2);second_rows.append(r)
        for t in boats:
            if t==s2:continue
            r=third_row(raw,head,s2,t);r["y"]=int(t==t3);third_rows.append(r)

    s2df=pd.DataFrame(second_rows);s3df=pd.DataFrame(third_rows)
    if train_races<80:raise RuntimeError(f"TOO_FEW_TRAIN_HEAD_RACES_{train_races}")
    if int(s2df.y.sum())!=train_races or int(s3df.y.sum())!=train_races:raise RuntimeError("LABEL_COUNT_DRIFT")

    m2=make_model(C_SECOND);m3=make_model(C_THIRD)
    m2.fit(s2df[SECOND_FEATURES],s2df.y.astype(int))
    m3.fit(s3df[THIRD_FEATURES],s3df.y.astype(int))

    model_meta={
        "train_period":"2026-06..2026-08 GLOBAL Stage-A; actual head3/4 only",
        "train_head_races":train_races,
        "second_rows":len(s2df),"third_rows":len(s3df),
        "second_features":SECOND_FEATURES,"third_features":THIRD_FEATURES,
        "C_second":C_SECOND,"C_third":C_THIRD,
        "onehead_transfer":{
            "alpha":ALPHA,"g2":G2,"g3":G3,"core_weights":CORE_W,
            "hybrid":"best + same-second + other-second",
        },
        "september_used_for_fit":False,
    }

    rec=[]
    rawrec=[]
    for _,r in sep_sel.sort_values(["date","race_code"]).iterrows():
        code=str(r.race_code).zfill(12);actual=truth.get(code)
        if not actual:continue
        heads=[3,4] if r.action=="A_DUAL_3_4" else [3]
        tickets=[];base_tickets=[];diag={}
        for head in heads:
            raw=feature_by_head.get((code,head))
            if raw is None:raise RuntimeError(f"MISSING_FEATURE_{code}_{head}")
            p2,pc,pairs=score_head(raw,head,m2,m3,True)
            for b in range(1,7):
                if b==head:
                    continue
                rr={"race_code":code,"action":r.action,"head":head,"boat":b}
                rr.update({k:raw[b][k] for k in SECOND_FEATURES})
                rr["v8_p2"]=p2[b]
                rawrec.append(rr)
            _,_,basepairs=score_head(raw,head,m2,m3,False)
            ts=[f"{head}-{s}-{t}" for s,t in pairs];bts=[f"{head}-{s}-{t}" for s,t in basepairs]
            tickets.extend(ts);base_tickets.extend(bts)
            diag[str(head)]={
                "p2":{str(k):v for k,v in p2.items()},
                "tickets":ts,
                "base_no_core":bts,
            }
        if len(tickets)!=(12 if r.action=="A_DUAL_3_4" else 6):raise RuntimeError("TICKET_COUNT_DRIFT")
        a1,a2,a3=actual;act=f"{a1}-{a2}-{a3}"
        hit=int(act in tickets);base_hit=int(act in base_tickets)
        head_hit=int(a1 in heads)
        second_top2=None;third_top2=None
        if head_hit:
            dhead=diag[str(a1)];p2m={int(k):float(v) for k,v in dhead["p2"].items()}
            sr=sorted(p2m,key=lambda b:(-p2m[b],b))
            second_top2=int(a2 in sr[:2])
            # recompute conditional THIRD for actual head/second for rank diagnostic
            raw=feature_by_head[(code,a1)];_,pc,_=score_head(raw,a1,m2,m3,True)
            tr=sorted([t for t in range(1,7) if t not in (a1,a2)],key=lambda t:(-pc[(a2,t)],t))
            third_top2=int(a3 in tr[:2])
        om=load_odds_for(code)
        if om is None or any(t not in om for t in tickets):raise RuntimeError(f"MISSING_SEP_ODDS_{code}")
        ovs=[om[t] for t in tickets];stakes=v6.dutch5000(ovs)
        payout_dutch=0.0
        if hit:
            j=tickets.index(act);payout_dutch=float(stakes[j])*float(ovs[j])
        flat_stake=len(tickets)*100
        flat_payout=100*float(om[act]) if hit else 0.0
        rec.append({
            "date":r.date,"race_code":code,"action":r.action,"heads":"|".join(map(str,heads)),
            "actual":act,"head_hit":head_hit,
            "ticket_count":len(tickets),"tickets":"|".join(tickets),"ticket_hit":hit,
            "base_no_core_tickets":"|".join(base_tickets),"base_no_core_hit":base_hit,
            "second_top2":second_top2,"third_top2":third_top2,
            "flat_stake":flat_stake,"flat_payout":flat_payout,"flat_profit":flat_payout-flat_stake,
            "dutch_stake":5000,"dutch_payout":payout_dutch,"dutch_profit":payout_dutch-5000,
            "diag":json.dumps(diag,ensure_ascii=False),
        })

    z=pd.DataFrame(rec)
    if len(z)!=len(sep_sel):raise RuntimeError(f"SEP_SELECTED_COVERAGE_{len(z)}/{len(sep_sel)}")
    z.to_csv(OUT/"sep_v8_detail.csv",index=False)
    pd.DataFrame(rawrec).to_csv(OUT/"sep_candidate_features.csv",index=False)
    s2df.to_csv(OUT/"train_second_rows.csv",index=False)
    s3df.to_csv(OUT/"train_third_rows.csv",index=False)

    h=z[z.head_hit.eq(1)]
    result={
        "model_id":"INNER12_ONEHEAD_STYLE_OPPONENT_V8_FEATURE_EXPORT",
        "status":"RESEARCH_SHADOW",
        "head_gate":"frozen V4 unchanged",
        "sep_period":"2026-09-01..2026-09-24",
        "sep_is_not_pristine_for_v8_selection":True,
        "future_unseen_start":"2026-09-25",
        "production_changed":False,
        "model":model_meta,
        "sep":{
            "R":len(z),"head_hits":int(z.head_hit.sum()),"head_rate":float(z.head_hit.mean()),
            "exact3_hits":int(z.ticket_hit.sum()),"exact3_rate":float(z.ticket_hit.mean()),
            "base_no_core_hits":int(z.base_no_core_hit.sum()),
            "headhit_second_top2":float(h.second_top2.mean()) if len(h) else None,
            "headhit_third_top2":float(h.third_top2.mean()) if len(h) else None,
            "flat100":metric(z,"flat_stake","flat_payout","ticket_hit"),
            "dutch5000":metric(z,"dutch_stake","dutch_payout","ticket_hit"),
            "A":{"R":int((z.action=="A_DUAL_3_4").sum()),"hits":int(z.loc[z.action.eq("A_DUAL_3_4"),"ticket_hit"].sum())},
            "B":{"R":int((z.action=="B_3HEAD").sum()),"hits":int(z.loc[z.action.eq("B_3HEAD"),"ticket_hit"].sum())},
        },
        "note":"Do not tune from Sep1-24. Use Sep25+ prospective shadow for the next untouched check.",
    }
    (OUT/"meta.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_ONEHEAD_STYLE_OPPONENT_V8_OK")
    print("TRAIN",json.dumps(model_meta,ensure_ascii=False))
    print("SEP",json.dumps(result["sep"],ensure_ascii=False))
    print("SEPTEMBER_USED_FOR_FIT_FALSE")
    print("FUTURE_UNSEEN_START_2026_09_25")
    print("V4_HEAD_GATE_UNCHANGED")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
