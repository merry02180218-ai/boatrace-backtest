#!/usr/bin/env python3
from __future__ import annotations
import sys, json, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_v288_operational_pre_replay as v288
import run_3head_a_purchase_gate_dev as pg
import run_3head_wave20_manual_gate as w20

SRC=Path("analysis_v243_3head_expand_feature_audit.csv")
OUT=Path("research_3head_v288_a60_overlap_strength.json")
CSV=Path("research_3head_v288_a60_overlap_strength.csv")
MONTHS=["feb"]
RANGES={"oct":("2025-10-01","2025-10-31"),"nov":("2025-11-01","2025-11-30"),
        "dec":("2025-12-01","2025-12-31"),"jan":("2026-01-01","2026-01-31"),"feb":("2026-02-01","2026-02-28")}

def n(s): return pd.to_numeric(s,errors="coerce")

def build_v288_codes():
    q=pd.read_csv(SRC,dtype={"race_code":str}); q["race_code"]=q.race_code.astype(str).str.zfill(12)
    q["date"]=q.date.astype(str); q["month"]=q.date.str[:7]; q["_target"]=v288.target(q).astype(int)
    ms=sorted(q.month.unique()); cs=v288.precols(q); pred=[]
    for i,m in enumerate(ms):
        if i<2: continue
        tr=q[q.month.isin(ms[:i])].copy(); te=q[q.month==m].copy()
        fs=v288.learned_features(tr,cs); tr_score=v288.score_with(tr,tr,fs)
        te["_score"]=v288.score_with(tr,te,fs)
        s_thr=float(tr_score.quantile(v288.S_Q)); a_thr=float(tr_score.quantile(v288.A_Q))
        te["grade"]=np.where(te._score>=s_thr,"S",np.where(te._score>=a_thr,"A","B")); pred.append(te)
    u=pd.concat(pred,ignore_index=True); u=u[u.grade.isin(["S","A"])].copy()
    final=u._target.eq(1)
    core=(n(u["f__c_b3_minus_b4_waku_st"])<=v288.WAKU34)&(n(u["f__c_b3_minus_b4_st"])>=v288.ST34)&(n(u["f__c_b3_meetst"])<=v288.MEETST)
    s=final&core; purch=u.bet.eq(1)
    a=purch&(~s)&(n(u["f__c_b3_minus_b4_st"])>=v288.A_ST34)&(n(u["f__c_wall12_weak"])<=v288.A_WALL)
    b=purch&(~s)&(~a)&(n(u["f__c_b3_minus_b2_motor"])>=v288.B_MOTOR)&(n(u["f__c_b3_inside_nst"])<=v288.B_NST)
    u["v288_route"]=np.where(s,"S",np.where(a,"A",np.where(b,"B","NO_BET")))
    return u[u.v288_route!="NO_BET"][["race_code","v288_route"]].drop_duplicates("race_code")

def build_a60():
    raw={}
    for k,(a,b) in RANGES.items():
        x,r,audit=w20.build_pre_enhanced(a,b,True); raw[k]=(x,r)
    frames={k:w20.prep_month(x,r) for k,(x,r) in raw.items()}
    scores,_=w20.make_pre_scores(frames)
    days,cache=w20.prefetch_sources(); post,_=w20.build_motor_exhibition(days,cache)
    rows=[]
    for k in MONTHS:
        q=scores[k].merge(post,on=["rc","date"],how="left",validate="one_to_one")
        rn=n(q.race_no); pre=n(q.pre_score)
        m=(rn>=1)&(rn<=12)&(pre>=.925)&pg.mask(q,pg.A["conds"])&(n(q.post_motor_inner_rank_edge)>=.60)
        z=q.loc[m,["rc","date","y","post_motor_inner_rank_edge"]].copy()
        z["race_code"]=z.rc.astype("int64").astype(str).str.zfill(12); z["a60_head"]=n(z.y).fillna(0).astype(int)
        rows.append(z[["race_code","date","a60_head","post_motor_inner_rank_edge"]])
    return pd.concat(rows,ignore_index=True).drop_duplicates("race_code")

def metric(z):
    r=len(z); h=int(z.a60_head.sum()) if r else 0
    return {"races":r,"boat3_wins":h,"head_rate":h/r if r else None}

def main():
    v=build_v288_codes(); a=build_a60()
    # Common period only. v288 frozen source starts Dec-2025; A+.60 frozen comparable cohort here is Dec-Feb.
    v=v[v.race_code.str[:8].between("20260201","20260228")].copy()
    a=a[a.race_code.str[:8].between("20260201","20260228")].copy()
    z=a.merge(v,on="race_code",how="outer",indicator=True)
    # Outcome is sourced only from the A+.60 causal cohort; v288-only outcomes are attached from official result files below.
    z["bucket"]=z["_merge"].map({"left_only":"A60_ONLY","right_only":"V288_ONLY","both":"BOTH"}).astype(str)
    # Attach official outcomes for V288_ONLY after membership is frozen. Hard stop Feb-28.
    from datetime import date,timedelta
    settled={}; day=date(2026,2,1)
    import analyze_v221_3head_scenario_pair as v221
    while day<=date(2026,2,28):
        try:
            for rr in v221.rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"):
                code=str(rr.get("レースコード","")).zfill(12); w=str(rr.get("1着_艇番","")).strip()
                if code.isdigit() and w in "123456" and len(w)==1: settled[code]=int(w)
        except Exception: pass
        day+=timedelta(days=1)
    z["winner"]=z.race_code.map(settled)
    # Cross-check A labels where available.
    chk=z[z.a60_head.notna()&z.winner.notna()].copy()
    if len(chk) and not ((chk.winner.eq(3)).astype(int).eq(chk.a60_head.astype(int))).all():
        raise RuntimeError("A60 outcome cross-check mismatch")
    z["a60_head"]=z.winner.eq(3).astype(int)
    if z.winner.isna().any(): raise RuntimeError(f"settlement missing {int(z.winner.isna().sum())}")
    out={"policy":{"window":"2026-02-01..2026-02-28","race_membership_frozen_before_settlement":True,
                   "v288_operational_semantics":True,"a60_frozen_gate":True,"sep2026_used":False,
                   "threshold_tuning":False},
         "counts":{"v288":int(len(v)),"a60":int(len(a)),"union":int(len(z))},
         "buckets":{b:metric(z[z.bucket==b]) for b in ["V288_ONLY","A60_ONLY","BOTH"]},
         "monthly":{}}
    z["month"]=z.race_code.str[:6]
    for m,g in z.groupby("month"):
        out["monthly"][m]={b:metric(g[g.bucket==b]) for b in ["V288_ONLY","A60_ONLY","BOTH"]}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    z[["race_code","month","bucket","v288_route","post_motor_inner_rank_edge","winner","a60_head"]].sort_values("race_code").to_csv(CSV,index=False)
    print(json.dumps(out,ensure_ascii=False,indent=2)); print("V288_A60_OVERLAP_STRENGTH_OK")
if __name__=="__main__": main()
