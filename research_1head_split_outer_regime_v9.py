#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,average_precision_score
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v9"; OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def build():
    x=pickle.load(open(ARGS.prepared,"rb")); rr=x["rows"]; rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);month=code[:4]+"-"+code[4:6]
        if month not in DEV:continue
        if code[:8]>="20260901":raise RuntimeError("September entered")
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        s=int(p[1])
        if s not in BOATS:continue
        p2,_=v365.formal_post_five6(r); pv={b:ff(p2.get(b)) for b in BOATS}
        top=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        z={"race_code":code,"month":month,"actual2":s,
           "y4":int(s==4),"y56":int(s in (5,6)),"ynormal":int(s in (2,3)),
           "baseline_hit":int(s in top[:2]),"best_inner":max((2,3),key=lambda b:pv[b]),
           "best56":max((5,6),key=lambda b:pv[b]),"best_outer":max((4,5,6),key=lambda b:pv[b])}
        for b in BOATS:z[f"p2_{b}"]=pv[b]
        z["p2_4_minus_innermax"]=pv[4]-max(pv[2],pv[3])
        z["p2_56max_minus_innermax"]=max(pv[5],pv[6])-max(pv[2],pv[3])
        z["p2_outermax_minus_innermax"]=max(pv[4],pv[5],pv[6])-max(pv[2],pv[3])
        for k in ("p_head","opp_mass","env_pair","attack_core","v332_score","one_ex","one_st","one_straight","one_orig_avg",
                  "sec_ex_mean_margin","sec_st_mean_margin","sec_straight_mean_margin","sec_turn_mean_margin",
                  "third_orig_mean_margin","third_straight_mean_margin","third_turn_mean_margin",
                  "covered_balance_min","covered_straight_weak_margin","covered_turn_weak_margin",
                  "uncovered_straight_dominance","uncovered_turn_dominance"):
            z[k]=ff(r.get(k))
        for metric in ("score","core","ex","st","straight","avg"):
            d={b:ff(r.get(f"{metric}{b}")) for b in BOATS}
            for b in BOATS:z[f"{metric}{b}"]=d[b]
            im=max(d[2],d[3]) if np.isfinite(d[2]) and np.isfinite(d[3]) else np.nan
            z[f"{metric}4_minus_innermax"]=d[4]-im if np.isfinite(im) and np.isfinite(d[4]) else np.nan
            z[f"{metric}56max_minus_innermax"]=max(d[5],d[6])-im if np.isfinite(im) and np.isfinite(d[5]) and np.isfinite(d[6]) else np.nan
        rows.append(z)
    return pd.DataFrame(rows)

def mdl():
    return Pipeline([("imp",SimpleImputer(strategy="median",add_indicator=True)),
                     ("sc",StandardScaler()),
                     ("lr",LogisticRegression(C=.2,max_iter=3000,class_weight="balanced"))])

def oof(df,features,target):
    out=[]
    for m in DEV:
        tr=df[df.month.ne(m)];te=df[df.month.eq(m)]
        p=mdl();p.fit(tr[features],tr[target].astype(int))
        q=te[["race_code","month","actual2","baseline_hit","best_inner","best56","best_outer",target]].copy()
        q["prob"]=p.predict_proba(te[features])[:,1];out.append(q)
    return pd.concat(out,ignore_index=True)

def eval_target(q,target,kind):
    y=q[target].to_numpy();p=q.prob.to_numpy()
    res={"R":len(q),"positive_R":int(y.sum()),"auc":float(roc_auc_score(y,p)),
         "ap":float(average_precision_score(y,p))}
    for frac in (.10,.15,.20,.25):
        n=max(1,int(round(len(q)*frac))); idx=np.argsort(-p)[:n]; flag=np.zeros(len(q),bool);flag[idx]=True
        tp=int((flag&(y==1)).sum())
        hits=[];resc=dam=0
        for i,r in q.reset_index(drop=True).iterrows():
            bh=int(r.baseline_hit)
            if not flag[i]:nh=bh
            elif kind=="4":nh=int(r.actual2 in (int(r.best_inner),4))
            else:nh=int(r.actual2 in (int(r.best_inner),int(r.best56)))
            hits.append(nh);resc+=int(bh==0 and nh==1);dam+=int(bh==1 and nh==0)
        k=f"top{int(frac*100)}"
        res[k]={"flag_R":n,"precision":tp/n,"recall":tp/max(int(y.sum()),1),
                "second_top2_hits":int(sum(hits)),"second_top2_rate":float(np.mean(hits)),
                "rescues":resc,"damages":dam}
    return res

def main():
    df=build()
    if (len(df),int(df.y4.sum()),int(df.y56.sum()))!=(163,24,17):raise RuntimeError("sentinel drift")
    meta={"race_code","month","actual2","y4","y56","ynormal","baseline_hit","best_inner","best56","best_outer"}
    fs=[c for c in df.columns if c not in meta and pd.api.types.is_numeric_dtype(df[c])]
    q4=oof(df,fs,"y4");q56=oof(df,fs,"y56")
    q4["target_name"]="FOUR";q56["target_name"]="FIVE_SIX"
    pd.concat([q4,q56],ignore_index=True).to_csv(OUT/"oof_predictions.csv",index=False)
    result={"population":"DEV head1 wins, separate 4-second vs 5/6-second OOF regimes",
            "baseline":{"R":163,"second_top2_hits":int(df.baseline_hit.sum()),"rate":float(df.baseline_hit.mean())},
            "four":eval_target(q4,"y4","4"),"five_six":eval_target(q56,"y56","56"),
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_SPLIT_OUTER_REGIME_V9",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);ARGS=ap.parse_args();main()
