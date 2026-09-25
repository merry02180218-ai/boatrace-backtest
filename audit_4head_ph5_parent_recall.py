#!/usr/bin/env python3
"""Audit whether the legacy HEAD4 monitoring_parent PRE gate drops frozen PH5 production selections.

Decision-time only. Jun-Aug 2026. September outcomes are never read.
"""
from __future__ import annotations
import json, math, os
from pathlib import Path
import numpy as np
import pandas as pd
import research_4head_player_waku_soft_ablation_v23 as v23
import audit_4head_ph5_live_walkforward as liveaudit

ROOT=Path(__file__).resolve().parent
V93=Path(os.environ.get("V93_ROWS","/tmp/head4_v93_all_parent/v93_all_parent.csv"))
CLEAN=Path(os.environ.get("STRICT_ROWS","/tmp/head4_clean_long_dataset/dataset.csv"))
ART=ROOT/"artifacts/head4_ph5_production_v31_20260831.json"
OUT=Path("/tmp/head4_ph5_parent_recall"); OUT.mkdir(parents=True,exist_ok=True)

def score_rows(z:pd.DataFrame,a:dict)->np.ndarray:
    feats=a["features"]
    x=z.reindex(columns=feats).apply(pd.to_numeric,errors="coerce").to_numpy(dtype=float)
    med=np.asarray(a["imputer_median"],dtype=float)
    mean=np.asarray(a["scaler_mean"],dtype=float)
    scale=np.asarray(a["scaler_scale"],dtype=float)
    coef=np.asarray(a["coef"],dtype=float)
    bad=~np.isfinite(x)
    if bad.any():
        x[bad]=np.take(med,np.where(bad)[1])
    xs=(x-mean)/scale
    logit=float(a["intercept"])+xs@coef
    return 1/(1+np.exp(-logit))

def main():
    a=json.loads(ART.read_text())
    assert a["id"]=="HEAD4_PH5_PRODUCTION_V31_20260831"
    assert a["cut"]==.36 and a["september_labels_used"] is False and a["same_day_results_used"] is False

    v=pd.read_csv(V93,dtype={"race_code":str}); v["race_code"]=v.race_code.astype(str).str.zfill(12)
    v["month"]=v.race_code.str[:4]+"-"+v.race_code.str[4:6]
    v=v[v.month.isin(["2026-06","2026-07","2026-08"])].copy()

    # Exactly mirror freeze_v31: remove any inherited PH columns and rebuild causal PH.
    inherited=[c for c in v.columns if "_pl_" in c]
    if inherited: v=v.drop(columns=inherited)
    ph=v23.build_ph(); ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
    ph=ph[[c for c in ph.columns if c=="race_code" or c.startswith("b4_pl_")]]
    v=v.merge(ph,on="race_code",how="left",validate="one_to_one")
    v["head_prob"]=score_rows(v,a)

    clean=pd.read_csv(CLEAN,dtype={"race_code":str}); clean["race_code"]=clean.race_code.astype(str).str.zfill(12)
    keep=["race_code","orig4_adv_inside","orig_avg_available"]
    v=v.merge(clean[keep],on="race_code",how="left",validate="one_to_one")
    v["orig4_adv_inside"]=pd.to_numeric(v.orig4_adv_inside,errors="coerce")
    v["ph5_selected"]=(v.head_prob.ge(.36)&v.orig4_adv_inside.ge(-.06))

    parent=liveaudit.monitoring_parent_snapshots()
    v["monitoring_parent"]=v.race_code.map(lambda c:int((parent.get(c) or {}).get("monitoring_parent",0)))
    v["parent_feature_missing"]=v.race_code.map(lambda c:int((parent.get(c) or {}).get("parent_feature_missing",1)))

    rows=[]
    for mon,g in v.groupby("month"):
        sel=g.ph5_selected
        overlap=sel & g.monitoring_parent.eq(1)
        outside=sel & g.monitoring_parent.eq(0)
        rows.append({
            "month":mon,
            "scored_R":int(len(g)),
            "ph5_hp_ge036_R":int(g.head_prob.ge(.36).sum()),
            "ph5_selected_with_orig_R":int(sel.sum()),
            "monitoring_parent_R":int(g.monitoring_parent.sum()),
            "selected_inside_parent_R":int(overlap.sum()),
            "selected_outside_parent_R":int(outside.sum()),
            "parent_recall_pct":100*float(overlap.sum())/int(sel.sum()) if sel.sum() else None,
            "selected_outside_parent_codes":g.loc[outside,"race_code"].tolist(),
        })
    allsel=v.ph5_selected
    allover=allsel & v.monitoring_parent.eq(1)
    allout=allsel & v.monitoring_parent.eq(0)
    out={
      "profile":"HEAD4_PH5_PARENT_RECALL_AUDIT_V1",
      "gate":"hp>=0.36 AND orig4_adv_inside>=-0.06",
      "period":"2026-06..2026-08",
      "ph5_selected_R":int(allsel.sum()),
      "selected_inside_parent_R":int(allover.sum()),
      "selected_outside_parent_R":int(allout.sum()),
      "parent_recall_pct":100*float(allover.sum())/int(allsel.sum()) if allsel.sum() else None,
      "monthly":rows,
      "outside_parent_codes":v.loc[allout,"race_code"].tolist(),
      "SEPTEMBER_OUTCOMES_READ":False,
      "PRODUCTION_CHANGED":False,
    }
    v[["race_code","month","head_prob","orig4_adv_inside","ph5_selected","monitoring_parent","parent_feature_missing"]].to_csv(OUT/"detail.csv",index=False)
    (OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print("HEAD4_PH5_PARENT_RECALL_AUDIT_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":
    main()
