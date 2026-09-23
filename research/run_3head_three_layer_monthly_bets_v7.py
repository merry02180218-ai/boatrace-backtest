#!/usr/bin/env python3
from __future__ import annotations
import sys,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_3head_a60_playerhistory_curve_v1 as base
import analyze_3head_player_history_3v2_ablation_v2 as ph
import run_3head_wave20_manual_gate as w20

OUT=Path("research_3head_three_layer_monthly_bets_v7.json"); CSV=Path("research_3head_three_layer_monthly_bets_v7.csv")
TARGETS=[30,40,50,60,70,80]
HIST_START=pd.Timestamp("2025-10-01")
def n(s):return pd.to_numeric(s,errors="coerce")

def main():
    # Build the same causal PRE/post universe used by frozen A+.60.
    raw={}
    ranges={"oct":("2025-10-01","2025-10-31"),"nov":("2025-11-01","2025-11-30"),"dec":("2025-12-01","2025-12-31"),"jan":("2026-01-01","2026-01-31"),"feb":("2026-02-01","2026-02-28"),"mar":("2026-03-01","2026-03-31"),"apr":("2026-04-01","2026-04-30"),"may":("2026-05-01","2026-05-31"),"jun":("2026-06-01","2026-06-30"),"jul":("2026-07-01","2026-07-31"),"aug":("2026-08-01","2026-08-31")}
    for k,(a,b) in ranges.items():
        x,r,audit=w20.build_pre_enhanced(a,b,True);raw[k]=(x,r)
    frames={k:w20.prep_month(x,r) for k,(x,r) in raw.items()}
    # make_pre_scores is hard-coded through Feb, so reproduce the same causal PRE scorer for Jul/Aug.
    _,enh,_=w20.make_pre_scores.__globals__['choose_features'](pd.concat(list(frames.values()),ignore_index=True,sort=False))
    hist_all=pd.concat(list(frames.values()),ignore_index=True,sort=False)
    scores={}
    for k in ["jul","aug"]:
        target=frames[k].sort_values(["date","rc"]).copy(); out=[]
        for dayv in sorted(target.date.dt.normalize().unique()):
            day=pd.Timestamp(dayv); today=target[target.date.dt.normalize()==day].copy()
            hist=pd.concat(list(frames.values()),ignore_index=True,sort=False)
            tr=hist[(hist.date<day)&(hist.date>=day-pd.Timedelta(days=42))].copy()
            if len(tr)<500 or tr.y.nunique()<2 or len(today)==0: continue
            model=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(C=.08,class_weight="balanced",solver="liblinear",max_iter=1800,random_state=161))
            model.fit(tr[enh],tr.y); ptr=model.predict_proba(tr[enh])[:,1]; pp=model.predict_proba(today[enh])[:,1]
            z=today[["rc","date","venue","race_no","y"]].copy(); z["pre_score"]=w20.make_pre_scores.__globals__['pct_ref'](ptr,pp); out.append(z)
        if not out: raise RuntimeError(f"NO_PRE_PREDICTIONS month={k} target={len(target)} hist42_max={max([len(hist_all[(hist_all.date<pd.Timestamp(v))&(hist_all.date>=pd.Timestamp(v)-pd.Timedelta(days=42))]) for v in target.date.dt.normalize().unique()] or [0])}")
        scores[k]=pd.concat(out,ignore_index=True).drop_duplicates("rc")
    # wave19 helper is frozen at Feb; extend its runtime end to Aug for this descriptive Jul/Aug audit.
    w20.prefetch_sources.__globals__['END']='2026-08-31'
    days,cache=w20.prefetch_sources();post,post_audit=w20.build_motor_exhibition(days,cache)
    print('POST_AUDIT',post_audit,'post_date_max',str(post.date.max()) if len(post) else None)
    allrows=[]
    for k in ["jul","aug"]:
        q=scores[k].merge(post,on=["rc","date"],how="left",validate="one_to_one")
        q["race_code"]=q.rc.astype("int64").astype(str).str.zfill(12);q["month"]=k
        allrows.append(q)
    d=pd.concat(allrows,ignore_index=True)
    print("PRE_POST_COVERAGE",{"rows":len(d),"months":d.month.value_counts().to_dict(),"motor_nonnull":int(n(d.post_motor_inner_rank_edge).notna().sum())})
    # Add independently defined strict-prior PLAYER_HISTORY; this reads outcomes only after each day's features are frozen.
    d=ph.add_player_history(d)
    names=ph.NAMES
    full=[]
    for k in names:
        rel=f"pl_rel3_2_{k}";d[rel]=n(d[f"b3_pl_{k}"])-n(d[f"b2_pl_{k}"])
        full += [f"b3_pl_{k}",f"b2_pl_{k}",rel]
    # Candidate pool deliberately only loosens A+.60 inner-motor threshold; all other A gate semantics stay frozen.
    rn=n(d.race_no);pre=n(d.pre_score)
    pool=(rn>=1)&(rn<=12)&(pre>=.925)&base.pg.mask(d,base.pg.A["conds"])&(n(d.post_motor_inner_rank_edge)>=0.0)
    d=d.loc[pool].copy()
    if d.empty: raise RuntimeError("EMPTY_CANDIDATE_POOL: inspect Jul/Aug post-feature coverage")
    # Causal rolling FULL_3V2 model. Training is strictly earlier dates.
    pred=[]
    for day in sorted(d.date.dt.normalize().unique()):
        te=d[d.date.dt.normalize()==day].copy();tr=d[(d.date<day)&(d.date>=HIST_START)].copy()
        if len(tr)<5 or tr.y.nunique()<2:continue
        model=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(C=.08,class_weight="balanced",solver="liblinear",max_iter=1800,random_state=322))
        model.fit(tr[full],tr.y.astype(int));te["ph_score"]=model.predict_proba(te[full])[:,1];pred.append(te)
    
    if not pred: raise RuntimeError(f"NO_PLAYER_HISTORY_PREDICTIONS pool={len(d)} months={d.month.value_counts().to_dict()} ph_nonnull={d[full].notna().sum().to_dict()}")
    p=pd.concat(pred,ignore_index=True)
    # CORE exact replay depends on a generated audit CSV that is not committed.
    # This audit therefore reports A+.60 -> FULL_3V2 exact pure-add counts for Jul/Aug.
    # CORE remains unchanged and is reported separately from its frozen production evidence.
    core_codes=set()
    rows=[]
    detail=[]
    for mon,g in p.groupby("month"):
        frozen=g[n(g.post_motor_inner_rank_edge)>=.60]
        g=g.copy(); g["race_code"]=g.rc.astype("int64").astype(str).str.zfill(12)
        c=g[g.race_code.isin(core_codes)].copy()
        a=frozen.copy(); a["race_code"]=a.rc.astype("int64").astype(str).str.zfill(12)
        a_only=a[~a.race_code.isin(set(c.race_code))].copy()
        # FULL expansion uses all ranked candidates available for the month; only non-A60, non-CORE races are pure additions.
        full=g.nlargest(len(g),"ph_score").copy()
        full_only=full[~full.race_code.isin(set(c.race_code)|set(a.race_code))].copy()
        union=set(c.race_code)|set(a.race_code)|set(full.race_code)
        rows.append({"month":mon,"variant":"CORE_PRIORITY","target_R":len(c),"R":len(c),"heads":int(c.y.sum()),"head_rate":float(c.y.mean()) if len(c) else None})
        rows.append({"month":mon,"variant":"A60_PURE_ADD","target_R":len(a_only),"R":len(a_only),"heads":int(a_only.y.sum()),"head_rate":float(a_only.y.mean()) if len(a_only) else None})
        rows.append({"month":mon,"variant":"FULL3V2_PURE_ADD","target_R":len(full_only),"R":len(full_only),"heads":int(full_only.y.sum()),"head_rate":float(full_only.y.mean()) if len(full_only) else None})
        rows.append({"month":mon,"variant":"TOTAL_UNION","target_R":len(union),"R":len(union),"heads":int(full[full.race_code.isin(union)].y.sum()),"head_rate":None})
        rows.append({"month":mon,"variant":"FROZEN_A60","target_R":len(frozen),"R":len(frozen),"heads":int(frozen.y.sum()),"head_rate":float(frozen.y.mean()) if len(frozen) else None})
        for target in TARGETS:
            z=g.nlargest(min(target,len(g)),"ph_score")
            rows.append({"month":mon,"variant":"FULL_3V2","target_R":target,"R":len(z),"heads":int(z.y.sum()),"head_rate":float(z.y.mean()) if len(z) else None})
            ov=z[n(z.post_motor_inner_rank_edge)>=.60]
            add=z[n(z.post_motor_inner_rank_edge)<.60]
            rows.append({"month":mon,"variant":"OVERLAP_A60_FULL3V2","target_R":target,"R":len(ov),"heads":int(ov.y.sum()),"head_rate":float(ov.y.mean()) if len(ov) else None})
            rows.append({"month":mon,"variant":"FULL3V2_INCREMENT_ONLY","target_R":target,"R":len(add),"heads":int(add.y.sum()),"head_rate":float(add.y.mean()) if len(add) else None})
    z=pd.DataFrame(rows);z.to_csv(CSV,index=False)
    out={"policy":{"core_unchanged":True,"full3v2_strict_prior":True,"history_start":"2025-10-01","rolling_window_days":None,"candidate_gate_except_inner_motor_frozen":True,"inner_motor_pool_min":0.0,"opponent_core":"native_v242_5to10","opponent_expanded":"V221_Top6_protected_SECOND4","sep2026_used":False,"jul_aug_non_pristine_descriptive_only":True,"priority":"A60>FULL3V2; CORE exact overlap pending generated v288 source","core_exact_overlap_available":False,"production_changed":False},"rows":rows}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+chr(10),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2));print("THREE_LAYER_MONTHLY_BETS_V7_OK");print("SEPTEMBER_UNREAD");print("PRODUCTION_UNCHANGED")
if __name__=="__main__":main()
