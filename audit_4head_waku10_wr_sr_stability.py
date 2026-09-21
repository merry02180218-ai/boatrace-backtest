#!/usr/bin/env python3
"""Waku10 4HEAD v3: decompose boat4 own Waku10 primitives. Train Mar-May, select on Jun, evaluate Jul-Aug only."""
import csv,json,os
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv")
OUT=Path("/tmp/head4_waku10_headmodel_v3"); OUT.mkdir(exist_ok=True)
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
DEV={"2026-03","2026-04","2026-05"}; VAL={"2026-06"}; HOLD={"2026-07","2026-08"}

def rc(x):
    s=str(x).strip()
    return (s[:-2] if s.endswith(".0") else s).zfill(12)

def ff(x,d=np.nan):
    try:return float(x)
    except:return d

def past_win(row,b):
    vals=[]
    for k in range(1,11):
        s=str(row.get(f"艇{b}_過去{k}走_着順","")).strip()
        if s.isdigit(): vals.append(int(s))
    return sum(v==1 for v in vals)/len(vals) if vals else np.nan

def load_csv(day):
    p=ROOT/"data/programs/waku10"/day[:4]/day[4:6]/(day[6:8]+".csv")
    if not p.is_file(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def load_shared(day):
    root=Path("data/shared_historical/waku10_boatcast")/day[:4]/day[4:6]/day[6:8]
    if not root.is_dir(): return []
    out=[]
    for fp in sorted(root.glob("*.txt")):
        lines=fp.read_text(encoding="utf-8-sig",errors="ignore").splitlines()
        if len(lines)<8 or not lines[0].startswith("data="): continue
        jo,rr=map(int,fp.stem.split("_"))
        row={"レースコード":f"{day}{jo:02d}{rr:02d}"}
        for b,line in enumerate(lines[2:8],1):
            a=line.split("\t")
            if len(a)<34: continue
            row[f"艇{b}_枠番別勝率"]=a[1]
            row[f"艇{b}_枠番別平均ST"]=a[2]
            row[f"艇{b}_枠番別平均スタート順"]=a[3]
            for k in range(10):
                q=4+k*3
                row[f"艇{b}_過去{k+1}走_着順"]=a[q]
                row[f"艇{b}_過去{k+1}走_進入"]=a[q+1]
                row[f"艇{b}_過去{k+1}走_グレード"]=a[q+2]
        out.append(row)
    return out

def build_waku(codes):
    byday={}
    for code in codes:
        day=code[:8]
        if day in byday: continue
        rows=load_csv(day)
        if not rows and "20260301"<=day<="20260731": rows=load_shared(day)
        byday[day]={rc(r.get("レースコード","")):r for r in rows}
    rec=[]
    for code in codes:
        w=byday.get(code[:8],{}).get(code,{})
        q={"race_code":code}
        for b in range(1,7):
            q[f"w10_b{b}_wr"]=ff(w.get(f"艇{b}_枠番別勝率"))
            q[f"w10_b{b}_st"]=ff(w.get(f"艇{b}_枠番別平均ST"))
            q[f"w10_b{b}_sr"]=ff(w.get(f"艇{b}_枠番別平均スタート順"))
            q[f"w10_b{b}_pastwin"]=past_win(w,b)
        # Boat4 own strength and relative attack/wall structure versus inside 1-3.
        for metric in ("wr","st","sr","pastwin"):
            for b in (1,2,3,5,6):
                # Positive means boat4 is stronger/faster/better rank than opponent.
                if metric in ("st","sr"):
                    q[f"w10_rel4_b{b}_{metric}"]=q[f"w10_b{b}_{metric}"]-q[f"w10_b4_{metric}"]
                else:
                    q[f"w10_rel4_b{b}_{metric}"]=q[f"w10_b4_{metric}"]-q[f"w10_b{b}_{metric}"]
        for metric in ("wr","st","sr","pastwin"):
            vals=[q[f"w10_rel4_b{b}_{metric}"] for b in (1,2,3)]
            q[f"w10_rel4_inside_mean_{metric}"]=float(np.nanmean(vals)) if np.isfinite(vals).any() else np.nan
            q[f"w10_rel4_inside_min_{metric}"]=float(np.nanmin(vals)) if np.isfinite(vals).any() else np.nan
        rec.append(q)
    return pd.DataFrame(rec)

def main():
    z=pd.read_csv(BASE,dtype={"race_code":str}); z["race_code"]=z.race_code.astype(str).str.zfill(12)
    z["month"]=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
    truth=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",usecols=["race_code","head4"],dtype={"race_code":str})
    truth["race_code"]=truth.race_code.astype(str).str.zfill(12); truth["head4"]=pd.to_numeric(truth.head4,errors="coerce")
    z=z.merge(truth,on="race_code",how="left",validate="one_to_one")
    z=z[z.head4.isin([0,1])].copy().merge(build_waku(z.race_code.tolist()),on="race_code",how="left",validate="one_to_one")
    forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
    numeric=[c for c in z.columns if c not in {"head4","race_code","month"} and pd.to_numeric(z[c],errors="coerce").notna().mean()>=.25]
    numeric=[c for c in numeric if not any(k.lower() in c.lower() for k in forbidden)]
    waku=[c for c in numeric if c.startswith("w10_") or c.startswith("opp_waku_b")]
    base=[c for c in numeric if c not in waku]
    feats=base+["w10_b4_wr","w10_b4_sr"]
    train=z[z.month.isin(DEV)].copy(); val=z[z.month.isin(VAL)].copy()
    pipe=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))])
    pipe.fit(train[feats],train.head4)
    for q in (z,val): q["p_wr_sr"]=pipe.predict_proba(q[feats])[:,1]
    # Frozen from v3: WR+SR family and cut .37 were selected using June only.
    CUT=.37
    sel=z[z.p_wr_sr>=CUT].copy()
    monthly=sel.groupby("month").head4.agg(["size","sum","mean"]).reset_index()
    monthly.columns=["month","R","head4","rate"]
    # Venue is encoded in race_code positions YYYYMMDDJJRR.
    sel["venue"]=sel.race_code.str[8:10]
    venue=sel.groupby("venue").head4.agg(["size","sum","mean"]).reset_index()
    venue.columns=["venue","R","head4","rate"]
    # Coefficients are standardized-feature logistic coefficients.
    coef=pd.DataFrame({"feature":feats,"coef":pipe.named_steps["lr"].coef_[0]})
    focus=coef[coef.feature.isin(["w10_b4_wr","w10_b4_sr"])].copy()
    # Fixed-cut BASE comparison; BASE model trained on same DEV. No threshold retuning.
    bp=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))])
    bp.fit(train[base],train.head4); z["p_base"]=bp.predict_proba(z[base])[:,1]
    base_sel=z[z.p_base>=.35][["race_code","month","head4"]].copy()
    wrsr_sel=sel[["race_code","month","head4"]].copy()
    only_w=wrsr_sel[~wrsr_sel.race_code.isin(set(base_sel.race_code))]
    only_b=base_sel[~base_sel.race_code.isin(set(wrsr_sel.race_code))]
    diff=pd.DataFrame([
      {"group":"WR_SR_ONLY","R":len(only_w),"head4":int(only_w.head4.sum()),"rate":float(only_w.head4.mean()) if len(only_w) else None},
      {"group":"BASE_ONLY","R":len(only_b),"head4":int(only_b.head4.sum()),"rate":float(only_b.head4.mean()) if len(only_b) else None},
    ])
    out=Path("/tmp/head4_waku10_wr_sr_stability");out.mkdir(exist_ok=True)
    monthly.to_csv(out/"monthly.csv",index=False);venue.to_csv(out/"venue.csv",index=False);focus.to_csv(out/"coefficients.csv",index=False);diff.to_csv(out/"diff.csv",index=False)
    meta={"family":"OWN4_WR_SR","frozen_cut":CUT,"base_cut":.35,"selection_source":"v3 June-only selection; no v4 retuning",
          "holdout_used_for_selection":False,"RESULT_FILES_READ":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (out/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("MONTHLY\n"+monthly.to_string(index=False));print("VENUE\n"+venue.to_string(index=False))
    print("COEF\n"+focus.to_string(index=False));print("DIFF\n"+diff.to_string(index=False))
    print(json.dumps(meta,ensure_ascii=False));print("WAKU10_WR_SR_STABILITY_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
