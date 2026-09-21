#!/usr/bin/env python3
"""Waku10 4HEAD v2: own boat4 + inside-wall relative Waku features. Train Mar-May, select on Jun, evaluate Jul-Aug only."""
import csv,json,os
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv")
OUT=Path("/tmp/head4_waku10_headmodel_v2"); OUT.mkdir(exist_ok=True)
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

def fit_score(tr,qs,feats):
    p=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))])
    p.fit(tr[feats],tr.head4)
    return [p.predict_proba(q[feats])[:,1] for q in qs]

def main():
    z=pd.read_csv(BASE,dtype={"race_code":str}); z["race_code"]=z.race_code.astype(str).str.zfill(12)
    z["month"]=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
    truth=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",usecols=["race_code","head4"],dtype={"race_code":str})
    truth["race_code"]=truth.race_code.astype(str).str.zfill(12); truth["head4"]=pd.to_numeric(truth.head4,errors="coerce")
    z=z.merge(truth,on="race_code",how="left",validate="one_to_one")
    z=z[z.head4.isin([0,1])].copy()
    w=build_waku(z.race_code.tolist())
    z=z.merge(w,on="race_code",how="left",validate="one_to_one")
    forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
    numeric=[c for c in z.columns if c not in {"head4","race_code","month"} and pd.to_numeric(z[c],errors="coerce").notna().mean()>=.25]
    numeric=[c for c in numeric if not any(k.lower() in c.lower() for k in forbidden)]
    # Baseline excludes every Waku10-derived primitive, including old v93 opponent Waku.
    waku=[c for c in numeric if c.startswith("w10_") or c.startswith("opp_waku_b")]
    base=[c for c in numeric if c not in waku]
    families={
      "BASE":base,
      "OWN4":base+[c for c in waku if c.startswith("w10_b4_")],
      "REL_INSIDE":base+[c for c in waku if c.startswith("w10_rel4_b1_") or c.startswith("w10_rel4_b2_") or c.startswith("w10_rel4_b3_") or c.startswith("w10_rel4_inside_")],
      "OWN4_REL_INSIDE":base+[c for c in waku if c.startswith("w10_b4_") or c.startswith("w10_rel4_b1_") or c.startswith("w10_rel4_b2_") or c.startswith("w10_rel4_b3_") or c.startswith("w10_rel4_inside_")],
      "ALL_WAKU":base+waku,
    }
    tr=z[z.month.isin(DEV)].copy(); va=z[z.month.isin(VAL)].copy(); ho=z[z.month.isin(HOLD)].copy()
    rows=[]
    for label,feats in families.items():
        ps=fit_score(tr,[tr,va,ho],feats)
        for q,p in zip((tr,va,ho),ps): q[label]=p
        cand=[]
        for cut in np.arange(.10,.501,.01):
            s=va[va[label]>=cut]
            if len(s)>=50:cand.append((float(s.head4.mean()),len(s),float(cut)))
        if not cand: raise RuntimeError("NO_VALID_THRESHOLD_"+label)
        chosen=sorted(cand,reverse=True)[0][2]
        for period,q in (("DEV",tr),("VAL",va),("HOLD",ho)):
            s=q[q[label]>=chosen]
            rows.append({"model":label,"period":period,"cut":chosen,"R":len(s),"head4":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
    comp=pd.DataFrame(rows); comp.to_csv(OUT/"comparison.csv",index=False)
    meta={"R":len(z),"base_features":len(base),"waku_features":len(waku),"waku_feature_names":waku,
          "families":{k:[c for c in v if c in waku] for k,v in families.items()},
          "selection":"June only; >=50 selections","holdout_used_for_selection":False,
          "target_source":"clean_dataset_head4_attached_after_pre_result_parent",
          "waku_source":"Boatcast shared historical Mar-Jul + BoatraceCSV existing Jul-Aug",
          "RESULT_FILES_READ":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print(comp.to_string(index=False)); print(json.dumps(meta,ensure_ascii=False)); print("WAKU10_HEADMODEL_V2_OK"); print("SEPTEMBER_UNREAD")

if __name__=="__main__":main()
