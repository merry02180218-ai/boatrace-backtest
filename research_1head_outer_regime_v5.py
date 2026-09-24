#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle,math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
INNER=(2,3); OUTER=(4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v5"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def entropy(vals):
    a=np.array([max(ff(x),0.0) for x in vals if np.isfinite(ff(x))],dtype=float)
    if not len(a) or a.sum()<=0:return np.nan
    a=a/a.sum(); return float(-(a*np.log(np.clip(a,1e-12,None))).sum())

def build():
    x=pickle.load(open(ARGS.prepared,"rb")); rr=x["rows"]
    rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
        if month not in DEV:continue
        if code[:8]>="20260901":raise RuntimeError("September entered")
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        try:actual2=int(p[1])
        except:continue
        if actual2 not in BOATS:continue
        p2,pc=v365.formal_post_five6(r)
        pv={b:ff(p2.get(b)) for b in BOATS}
        top=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        z={"race_code":code,"month":month,"actual2":actual2,"y_outer":int(actual2 in OUTER),
           "baseline_hit":int(actual2 in top[:2]),"best_inner":max(INNER,key=lambda b:pv[b]),
           "best_outer":max(OUTER,key=lambda b:pv[b]),
           "p2_outer_sum":sum(pv[b] for b in OUTER),"p2_inner_sum":sum(pv[b] for b in INNER),
           "p2_outer_max":max(pv[b] for b in OUTER),"p2_inner_max":max(pv[b] for b in INNER),
           "p2_outermax_minus_innermax":max(pv[b] for b in OUTER)-max(pv[b] for b in INNER),
           "p2_top2_outer_count":sum(int(b in OUTER) for b in top[:2]),
           "p2_entropy":entropy(pv.values())}
        # Safe prepared race-context scalars.
        for k in ("p_head","opp_mass","env_pair","attack_core","v332_score","one_ex","one_st","one_straight","one_orig_avg",
                  "sec_ex_mean_margin","sec_st_mean_margin","sec_straight_mean_margin","sec_turn_mean_margin",
                  "third_orig_mean_margin","third_straight_mean_margin","third_turn_mean_margin",
                  "covered_balance_min","covered_straight_weak_margin","covered_turn_weak_margin",
                  "uncovered_straight_dominance","uncovered_turn_dominance"):
            z[k]=ff(r.get(k))
        for k in ("attack_ready","env_ready","ex_ready","has_orig","has_stt","source_complete","tkz_all6","stt_all6",
                  "orig_avg_all6","orig_straight_all6","orig_turn_all6","orig_turn_straight_all6"):
            z[k]=int(bool(r.get(k,False)))
        for metric in ("score","core","ex","st","straight","avg"):
            d={b:ff(r.get(f"{metric}{b}")) for b in BOATS}
            for b in BOATS:z[f"{metric}{b}"]=d[b]
            iv=[d[b] for b in INNER if np.isfinite(d[b])]; ov=[d[b] for b in OUTER if np.isfinite(d[b])]
            z[f"{metric}_outermax_minus_innermax"]=(max(ov)-max(iv)) if ov and iv else np.nan
            z[f"{metric}_outermean_minus_innermean"]=(float(np.mean(ov))-float(np.mean(iv))) if ov and iv else np.nan
            z[f"{metric}_bestouter_minus_b2"]=(max(ov)-d[2]) if ov and np.isfinite(d[2]) else np.nan
            z[f"{metric}_bestouter_minus_b3"]=(max(ov)-d[3]) if ov and np.isfinite(d[3]) else np.nan
        rows.append(z)
    return pd.DataFrame(rows)

def model():
    return Pipeline([("imp",SimpleImputer(strategy="median",add_indicator=True)),
                     ("sc",StandardScaler()),
                     ("lr",LogisticRegression(C=.3,max_iter=3000,class_weight="balanced"))])

def oof(df,features,label):
    preds=[]
    for m in DEV:
        tr=df[df.month.ne(m)].copy(); te=df[df.month.eq(m)].copy()
        pipe=model();pipe.fit(tr[features],tr.y_outer.astype(int))
        p=pipe.predict_proba(te[features])[:,1]
        q=te[["race_code","month","actual2","y_outer","baseline_hit","best_inner","best_outer"]].copy()
        q["p_outer"]=p;q["family"]=label;preds.append(q)
    return pd.concat(preds,ignore_index=True)

def metrics(q):
    y=q.y_outer.to_numpy();p=q.p_outer.to_numpy()
    out={"R":int(len(q)),"outer_R":int(y.sum()),"base_rate":float(y.mean()),
         "auc":float(roc_auc_score(y,p)),"average_precision":float(average_precision_score(y,p)),
         "brier":float(brier_score_loss(y,p))}
    for frac in (.20,.25,.30,.35,.40):
        n=max(1,int(round(len(q)*frac)))
        idx=np.argsort(-p)[:n];flag=np.zeros(len(q),dtype=bool);flag[idx]=True
        tp=int((flag&(y==1)).sum()); fp=int((flag&(y==0)).sum())
        out[f"top{int(frac*100)}_flag_R"]=n
        out[f"top{int(frac*100)}_precision"]=tp/n
        out[f"top{int(frac*100)}_recall"]=tp/max(int(y.sum()),1)
        # Regime policy: flagged => best inner + best outer; unflagged => formal P2 top2.
        second_hit=[]; rescue=damage=0
        bycode={str(r["race_code"]):r for _,r in q.iterrows()}
        # Baseline top2 membership is already recorded; for flagged, actual is covered iff it equals best inner or best outer.
        for i,r in q.reset_index(drop=True).iterrows():
            bh=int(r.baseline_hit)
            nh=int(r.actual2 in (int(r.best_inner),int(r.best_outer))) if flag[i] else bh
            second_hit.append(nh); rescue+=int(bh==0 and nh==1);damage+=int(bh==1 and nh==0)
        out[f"top{int(frac*100)}_second_top2_hits"]=int(sum(second_hit))
        out[f"top{int(frac*100)}_second_top2_rate"]=float(np.mean(second_hit))
        out[f"top{int(frac*100)}_rescues"]=rescue;out[f"top{int(frac*100)}_damages"]=damage
    return out

def main():
    df=build()
    if len(df)!=163 or int(df.y_outer.sum())!=41:raise RuntimeError(f"DEV sentinel drift {len(df)} {int(df.y_outer.sum())}")
    meta={"race_code","month","actual2","y_outer","baseline_hit","best_inner","best_outer"}
    p2f=["p2_outer_sum","p2_inner_sum","p2_outer_max","p2_inner_max","p2_outermax_minus_innermax","p2_top2_outer_count","p2_entropy"]
    structure=p2f+[c for c in df.columns if any(c.startswith(x+"_") for x in ("score","core","ex","st","straight","avg")) and c not in meta]
    full=[c for c in df.columns if c not in meta and c not in ("baseline_hit",) and pd.api.types.is_numeric_dtype(df[c])]
    fams={"P2_ONLY":p2f,"P2_PLUS_STRUCTURE":structure,"FULL_SAFE":full}
    allpred=[];summary={}
    for name,fs in fams.items():
        q=oof(df,fs,name);allpred.append(q);summary[name]=metrics(q)
        # Fit full DEV only for descriptive standardized coefficients.
        pipe=model();pipe.fit(df[fs],df.y_outer.astype(int))
        lr=pipe.named_steps["lr"];imp=pipe.named_steps["imp"]
        names=list(fs)+[f"MISSING_{fs[i]}" for i in getattr(imp,"indicator_",type("X",(),{"features_":[]})()).features_]
        coef=lr.coef_[0]
        top=sorted([{"feature":str(n),"coef":float(v)} for n,v in zip(names,coef)],key=lambda z:abs(z["coef"]),reverse=True)[:20]
        summary[name]["top_coefficients"]=top
    pred=pd.concat(allpred,ignore_index=True);pred.to_csv(OUT/"oof_predictions.csv",index=False)
    df.to_csv(OUT/"dev_rows.csv",index=False)
    baseline={"R":len(df),"hits":int(df.baseline_hit.sum()),"rate":float(df.baseline_hit.mean())}
    result={"population":"DEV head1 wins; OOF outer-vs-inner SECOND regime","baseline_p2_top2":baseline,
            "families":summary,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_OUTER_REGIME_V5",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);ARGS=ap.parse_args();main()
