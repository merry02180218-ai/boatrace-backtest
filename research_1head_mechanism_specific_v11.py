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
import research_4head_waku10_rel43_v4 as wsrc

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v11";OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x);return v if np.isfinite(v) else np.nan
    except:return np.nan

def mdl(C=.15):
    return Pipeline([("imp",SimpleImputer(strategy="median",add_indicator=True)),("sc",StandardScaler()),
                     ("lr",LogisticRegression(C=C,max_iter=3000,class_weight="balanced"))])

def oof(df,features,target):
    out=[]
    for m in DEV:
        tr=df[df.month.ne(m)];te=df[df.month.eq(m)]
        p=mdl();p.fit(tr[features],tr[target].astype(int))
        q=te[["race_code","month","actual2","baseline_hit","best_inner","best56","best_outer",target]].copy()
        q["prob"]=p.predict_proba(te[features])[:,1];out.append(q)
    return pd.concat(out,ignore_index=True)

def eval_model(q,target,kind):
    y=q[target].to_numpy();p=q.prob.to_numpy()
    res={"R":len(q),"positive_R":int(y.sum()),"auc":float(roc_auc_score(y,p)),"ap":float(average_precision_score(y,p))}
    for frac in (.08,.10,.12,.15,.20):
        n=max(1,int(round(len(q)*frac)));idx=np.argsort(-p)[:n];flag=np.zeros(len(q),bool);flag[idx]=True
        hits=[];resc=dam=0
        for i,r in q.reset_index(drop=True).iterrows():
            bh=int(r.baseline_hit)
            if not flag[i]:nh=bh
            elif kind=="4":nh=int(r.actual2 in (int(r.best_inner),4))
            else:nh=int(r.actual2 in (int(r.best_inner),int(r.best56)))
            hits.append(nh);resc+=int(bh==0 and nh==1);dam+=int(bh==1 and nh==0)
        k=f"top{int(frac*100)}"
        res[k]={"flag_R":n,"precision":float((flag&(y==1)).sum()/n),"recall":float((flag&(y==1)).sum()/max(y.sum(),1)),
                "second_top2_hits":int(sum(hits)),"rate":float(np.mean(hits)),"rescues":resc,"damages":dam}
    return res

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb"));rr=x["rows"]
    base=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);month=code[:4]+"-"+code[4:6]
        if month not in DEV:continue
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        s=int(p[1]);p2,_=v365.formal_post_five6(r);pv={b:ff(p2.get(b)) for b in BOATS};top=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        z={"race_code":code,"month":month,"actual2":s,"y4":int(s==4),"y56":int(s in (5,6)),
           "baseline_hit":int(s in top[:2]),"best_inner":max((2,3),key=lambda b:pv[b]),
           "best56":max((5,6),key=lambda b:pv[b]),"best_outer":max((4,5,6),key=lambda b:pv[b])}
        for b in BOATS:z[f"p2_{b}"]=pv[b]
        for metric in ("score","core","ex","st","straight","avg"):
            for b in BOATS:z[f"{metric}_{b}"]=ff(r.get(f"{metric}{b}"))
        z["opp_mass"]=ff(r.get("opp_mass"));z["attack_core"]=ff(r.get("attack_core"))
        base.append(z)
    d=pd.DataFrame(base)
    w=wsrc.build_waku(d.race_code.tolist());w["race_code"]=w.race_code.astype(str).str.zfill(12)
    d=d.merge(w,on="race_code",how="left",validate="one_to_one")
    # Candidate-relative start/history gaps. Positive = 5/6 historical start advantage.
    inner_hist_st=d[["w10_b2_st","w10_b3_st"]].min(axis=1)
    inner_hist_sr=d[["w10_b2_sr","w10_b3_sr"]].min(axis=1)
    d["w56_hist_st_adv"]=inner_hist_st-d[["w10_b5_st","w10_b6_st"]].min(axis=1)
    d["w56_hist_sr_adv"]=inner_hist_sr-d[["w10_b5_sr","w10_b6_sr"]].min(axis=1)
    d["w4_hist_st_adv"]=inner_hist_st-d["w10_b4_st"]
    d["w4_hist_sr_adv"]=inner_hist_sr-d["w10_b4_sr"]
    # Prepared/exhibition start score: higher is better.
    d["exst56_adv"]=d[["st_5","st_6"]].max(axis=1)-d[["st_2","st_3"]].max(axis=1)
    d["exst4_adv"]=d["st_4"]-d[["st_2","st_3"]].max(axis=1)
    # Foot advantages for boat4.
    for m in ("score","core","ex","straight","avg"):
        d[f"{m}4_adv"]=d[f"{m}_4"]-d[[f"{m}_2",f"{m}_3"]].max(axis=1)
    d["p2_4_adv"]=d["p2_4"]-d[["p2_2","p2_3"]].max(axis=1)
    d["p2_56_adv"]=d[["p2_5","p2_6"]].max(axis=1)-d[["p2_2","p2_3"]].max(axis=1)

    four_foot=["p2_4","p2_4_adv","opp_mass","score4_adv","core4_adv","ex4_adv","straight4_adv","avg4_adv"]
    fs_start_base=["p2_5","p2_6","p2_56_adv","opp_mass","st_5","st_6","exst56_adv"]
    fs_start_waku=fs_start_base+["w10_b5_st","w10_b6_st","w10_b5_sr","w10_b6_sr","w56_hist_st_adv","w56_hist_sr_adv"]
    # Also test boat4 Waku start only as falsification against foot hypothesis.
    four_start=["p2_4","p2_4_adv","opp_mass","st_4","exst4_adv","w10_b4_st","w10_b4_sr","w4_hist_st_adv","w4_hist_sr_adv"]

    q4f=oof(d,four_foot,"y4");q4s=oof(d,four_start,"y4")
    q56b=oof(d,fs_start_base,"y56");q56w=oof(d,fs_start_waku,"y56")
    result={
      "population":"DEV head1 wins; mechanism-specific low-dimensional OOF",
      "baseline":{"R":len(d),"hits":int(d.baseline_hit.sum()),"rate":float(d.baseline_hit.mean())},
      "four_foot":eval_model(q4f,"y4","4"),"four_start":eval_model(q4s,"y4","4"),
      "five_six_start_base":eval_model(q56b,"y56","56"),"five_six_start_waku":eval_model(q56w,"y56","56"),
      "waku_coverage":{"b5_st":int(d.w10_b5_st.notna().sum()),"b6_st":int(d.w10_b6_st.notna().sum())},
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    pd.concat([q4f.assign(model="FOUR_FOOT"),q4s.assign(model="FOUR_START"),
               q56b.assign(model="56_START_BASE"),q56w.assign(model="56_START_WAKU")],ignore_index=True).to_csv(OUT/"oof_predictions.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_MECHANISM_SPECIFIC_V11",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
