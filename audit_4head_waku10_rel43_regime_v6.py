#!/usr/bin/env python3
"""Waku10 4HEAD v4: isolate boat4-vs-boat3 Waku10 differences. Train Mar-May, select on Jun, evaluate Jul-Aug only."""
import csv,json,os
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv")
OUT=Path("/tmp/head4_waku10_headmodel_v4"); OUT.mkdir(exist_ok=True)
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

def fit_model(train,feats):
    p=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))])
    p.fit(train[feats],train.head4); return p

def main():
    z=pd.read_csv(BASE,dtype={"race_code":str}); z["race_code"]=z.race_code.astype(str).str.zfill(12)
    z["month"]=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
    truth=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",usecols=["race_code","head4"],dtype={"race_code":str})
    truth["race_code"]=truth.race_code.astype(str).str.zfill(12); truth["head4"]=pd.to_numeric(truth.head4,errors="coerce")
    z=z.merge(truth,on="race_code",how="left",validate="one_to_one"); z=z[z.head4.isin([0,1])].copy()
    z=z.merge(build_waku(z.race_code.tolist()),on="race_code",how="left",validate="one_to_one")
    forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
    numeric=[c for c in z.columns if c not in {"head4","race_code","month"} and pd.to_numeric(z[c],errors="coerce").notna().mean()>=.25]
    numeric=[c for c in numeric if not any(k.lower() in c.lower() for k in forbidden)]
    waku=[c for c in numeric if c.startswith("w10_") or c.startswith("opp_waku_b")]; base=[c for c in numeric if c not in waku]
    families={
      "BASE":(base,.35),
      "REL43_WR_ST":(base+["w10_rel4_b3_wr","w10_rel4_b3_st"],.36),
      "OWN4_WR_SR_PLUS_REL43_WR_SR":(base+["w10_b4_wr","w10_b4_sr","w10_rel4_b3_wr","w10_rel4_b3_sr"],.37),
    }
    tr=z[z.month.isin(DEV)].copy(); rows=[]; selected={}
    for label,(feats,cut) in families.items():
        p=fit_model(tr,feats); z[label]=p.predict_proba(z[feats])[:,1]
        s=z[z[label]>=cut].copy(); selected[label]=s
        for month,g in s.groupby("month"):
            rows.append({"model":label,"month":month,"R":len(g),"head4":int(g.head4.sum()),"rate":float(g.head4.mean())})
    monthly=pd.DataFrame(rows)
    venues=[]
    for label,s in selected.items():
        s=s.copy();s["venue"]=s.race_code.str[8:10]
        for venue,g in s.groupby("venue"):
            venues.append({"model":label,"venue":venue,"R":len(g),"head4":int(g.head4.sum()),"rate":float(g.head4.mean())})
    venue=pd.DataFrame(venues)
    diffs=[]
    b=set(selected["BASE"].race_code)
    for label in ("REL43_WR_ST","OWN4_WR_SR_PLUS_REL43_WR_SR"):
        s=selected[label]; only=s[~s.race_code.isin(b)]
        baseonly=selected["BASE"][~selected["BASE"].race_code.isin(set(s.race_code))]
        for group,g in ((label+"_ONLY",only),(label+"_BASE_ONLY",baseonly)):
            diffs.append({"group":group,"R":len(g),"head4":int(g.head4.sum()),"rate":float(g.head4.mean()) if len(g) else None})
    # Diagnose regime shift without tuning: monthly distributions and fixed BASE-score bands.
    diag=[]
    bands=[(-1,.30),(.30,.35),(.35,.40),(.40,.45),(.45,2)]
    for month,g in z.groupby("month"):
        for metric in ("w10_b4_wr","w10_b3_wr","w10_rel4_b3_wr","w10_b4_st","w10_b3_st","w10_rel4_b3_st","w10_b4_sr","w10_b3_sr","w10_rel4_b3_sr","BASE"):
            x=pd.to_numeric(g[metric],errors="coerce")
            diag.append({"month":month,"metric":metric,"N":int(x.notna().sum()),"mean":float(x.mean()),"median":float(x.median()),"q25":float(x.quantile(.25)),"q75":float(x.quantile(.75))})
    bandrows=[]
    for month,g in z.groupby("month"):
        for lo,hi in bands:
            q=g[(g.BASE>=lo)&(g.BASE<hi)]
            if len(q):
                bandrows.append({"month":month,"band":f"{lo:.2f}_{hi:.2f}","R":len(q),"head4":int(q.head4.sum()),"rate":float(q.head4.mean()),
                  "rel43_wr_mean":float(q.w10_rel4_b3_wr.mean()),"rel43_st_mean":float(q.w10_rel4_b3_st.mean()),"rel43_sr_mean":float(q.w10_rel4_b3_sr.mean())})
    pd.DataFrame(diag).to_csv("/tmp/rel43_diag.csv",index=False)
    pd.DataFrame(bandrows).to_csv("/tmp/rel43_bands.csv",index=False)
    out=Path("/tmp/head4_waku10_rel43_stability_v5");out.mkdir(exist_ok=True)
    monthly.to_csv(out/"monthly.csv",index=False);venue.to_csv(out/"venue.csv",index=False);pd.DataFrame(diffs).to_csv(out/"diff.csv",index=False);pd.DataFrame(diag).to_csv(out/"diagnostics.csv",index=False);pd.DataFrame(bandrows).to_csv(out/"base_bands.csv",index=False)
    meta={"frozen":{"BASE":.35,"REL43_WR_ST":.36,"OWN4_WR_SR_PLUS_REL43_WR_SR":.37},"selection_source":"v4 June-only; v5 no retuning","holdout_used_for_selection":False,"RESULT_FILES_READ":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (out/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("MONTHLY\n"+monthly.to_string(index=False));print("DIAGNOSTICS\n"+pd.DataFrame(diag).to_string(index=False));print("BASE_BANDS\n"+pd.DataFrame(bandrows).to_string(index=False));print("VENUE\n"+venue.to_string(index=False));print("DIFF\n"+pd.DataFrame(diffs).to_string(index=False));print(json.dumps(meta));print("REL43_STABILITY_V5_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
