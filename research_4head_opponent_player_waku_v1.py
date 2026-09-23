#!/usr/bin/env python3
"""Opponent research v1: diagnose PH/Waku10 signal on frozen PH5 production selections.
Research only. No production mutation. September outcomes are never read.
PLAYER_HISTORY is causal prior-day via build_ph(). Waku10 is pre-race program data.
"""
import json, os
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_player_waku_soft_ablation_v23 as phsrc
import research_4head_waku10_rel43_v4 as wsrc

ROOT=Path("/tmp/head4_ph5_live_walkforward")
OUT=Path("/tmp/head4_opponent_player_waku_v1"); OUT.mkdir(parents=True,exist_ok=True)
BOATS=(1,2,3,5,6)

def main():
    d=pd.read_csv(ROOT/"decisions.csv",dtype={"race_code":str})
    d.race_code=d.race_code.astype(str).str.zfill(12)
    d=d[d.production_bet.eq(1)].copy()
    if d.empty: raise RuntimeError("NO_FROZEN_PRODUCTION_BETS")
    # Outcome fields exist only because the parent audit freezes decisions before truth join.
    h=d[d.head4.eq(1)].copy()
    ph=phsrc.build_ph()
    ph.race_code=ph.race_code.astype(str).str.zfill(12)
    w=wsrc.build_waku(d.race_code.tolist())
    w.race_code=w.race_code.astype(str).str.zfill(12)
    z=d[["race_code","date","head4","hit","tickets","opponent_diag"]].merge(ph,on="race_code",how="left",validate="one_to_one").merge(w,on="race_code",how="left",validate="one_to_one")
    # Descriptive miss analysis only: compare causal pre-race features for covered vs missed 4-head races.
    rows=[]
    for _,r in z[z.head4.eq(1)].iterrows():
        diag=json.loads(r.opponent_diag); actual_hit=int(r.hit)
        for b in BOATS:
            rec={"race_code":r.race_code,"date":r.date,"boat":b,"covered":actual_hit}
            for k in ("all_win","all_p2","frame_win","frame_p2","recent_p2"):
                rec["pl_"+k]=pd.to_numeric(pd.Series([r.get(f"b{b}_pl_{k}")]),errors="coerce").iloc[0]
            # Keep any canonical per-boat Waku10 fields exposed by builder.
            for c in w.columns:
                if c=="race_code": continue
                if f"b{b}" in c.lower() or f"_{b}_" in c.lower():
                    rec[c]=pd.to_numeric(pd.Series([r.get(c)]),errors="coerce").iloc[0]
            rows.append(rec)
    q=pd.DataFrame(rows); q.to_csv(OUT/"head4_opponent_causal_features.csv",index=False)
    summ=[]
    for c in q.columns:
        if c in {"race_code","date","boat","covered"}: continue
        x=pd.to_numeric(q[c],errors="coerce")
        if x.notna().sum()<20: continue
        a=x[q.covered.eq(1)]; b=x[q.covered.eq(0)]
        summ.append({"feature":c,"covered_mean":float(a.mean()),"miss_mean":float(b.mean()),"delta":float(a.mean()-b.mean()),"n":int(x.notna().sum())})
    pd.DataFrame(summ).sort_values("delta",key=lambda s:s.abs(),ascending=False).to_csv(OUT/"feature_miss_deltas.csv",index=False)
    meta={"production_bets":int(len(d)),"head4_R":int(len(h)),"covered":int(h.hit.sum()),"missed":int(len(h)-h.hit.sum()),"PLAYER_HISTORY":"causal prior-day","Waku10":"pre-race only","SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(meta,ensure_ascii=False)); print("HEAD4_OPPONENT_PLAYER_WAKU_V1_OK"); print("SEPTEMBER_UNREAD")

if __name__=="__main__": main()
