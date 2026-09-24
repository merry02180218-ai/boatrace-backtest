#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v14"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan
def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def bycode(rs):return {str(r.get("レースコード","")).zfill(12):r for r in rs}

def build(prepared,root):
    x=pickle.load(open(prepared,"rb")); rr=x["rows"]; cache={}; rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12); m=code[:4]+"-"+code[4:6]
        if m not in DEV: continue
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1": continue
        actual2=int(p[1]); day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")))
        cards,waku=cache[day]; card=cards.get(code,{}); w=waku.get(code,{})
        if not card: continue
        xf=bt.race_features(card,w)
        p2,pc=v365.formal_post_five6(r); pv={b:ff(p2.get(b)) for b in BOATS}
        order=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        z={"race_code":code,"month":m,"actual2":actual2,"base1":order[0],"base2":order[1],
           "baseline_hit":int(actual2 in order[:2]),"c5_already":int(5 in order[:2]),
           "c5_ratio2":pv[5]/max(pv[order[1]],1e-12)}
        z["local_edge"]=ff(xf[5]["local"])-ff(xf[4]["local"])
        z["wr_edge"]=ff(xf[5]["wr"])-ff(xf[4]["wr"])
        for met in ("core","straight","avg"):
            e=ff(r.get(f"{met}5"))-ff(r.get(f"{met}4"))
            z[f"{met}_beat"]=int(np.isfinite(e) and e>0)
        z["foot_count"]=z["core_beat"]+z["straight_beat"]+z["avg_beat"]
        rows.append(z)
    return pd.DataFrame(rows)

def specs():
    out=[]
    for ratio in (.25,.35,.50,.65):
        out += [
          (f"LOCAL_FOOT2_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.foot_count>=2)&(d.c5_ratio2>=ratio)),
          (f"LOCAL_WR_FOOT2_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.wr_edge>0)&(d.foot_count>=2)&(d.c5_ratio2>=ratio)),
          (f"LOCAL_STRAIGHT_CORE_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.straight_beat==1)&(d.core_beat==1)&(d.c5_ratio2>=ratio)),
          (f"LOCAL_STRAIGHT_AVG_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.straight_beat==1)&(d.avg_beat==1)&(d.c5_ratio2>=ratio)),
          (f"LOCAL_WR_TRIPLE_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.wr_edge>0)&(d.foot_count==3)&(d.c5_ratio2>=ratio)),
        ]
    return out

def eval_rule(df,fn):
    fire=fn(df)&df.c5_already.eq(0)
    new=[];resc=dam=0
    for i,r in df.iterrows():
        old=int(r.baseline_hit)
        nh=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[i]) else old
        new.append(nh);resc+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
    return {"hits":int(sum(new)),"rate":float(np.mean(new)) if len(new) else None,
            "rescued":resc,"damaged":dam,"net":resc-dam,"fired_R":int(fire.sum()),"new":new}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--prepared",required=True,type=Path); a=ap.parse_args()
    q=build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)<160: raise RuntimeError(f"coverage {len(q)}")
    rules=specs()
    outer=[]
    total_base=total_new=resc_total=dam_total=0
    for held in DEV:
        tr=q[q.month.ne(held)].copy(); te=q[q.month.eq(held)].copy()
        base_train=int(tr.baseline_hit.sum())
        candidates=[("NO_CHANGE",None,{"hits":base_train,"net":0,"fired_R":0})]
        for name,fn in rules:
            ev=eval_rule(tr,fn)
            # Only permit a learned override when it improves training hits.
            if ev["hits"]>base_train:
                candidates.append((name,fn,ev))
        candidates.sort(key=lambda x:(x[2]["hits"],x[2]["net"],-x[2]["fired_R"]),reverse=True)
        name,fn,train_ev=candidates[0]
        if fn is None:
            held_ev={"hits":int(te.baseline_hit.sum()),"rescued":0,"damaged":0,"net":0,"fired_R":0}
        else:
            held_ev=eval_rule(te,fn)
        b=int(te.baseline_hit.sum())
        total_base+=b; total_new+=held_ev["hits"]; resc_total+=held_ev["rescued"]; dam_total+=held_ev["damaged"]
        outer.append({"held_month":held,"selected_rule":name,
                      "train_R":int(len(tr)),"train_baseline_hits":base_train,
                      "train_rule_hits":train_ev["hits"],"train_net":train_ev["net"],"train_fired":train_ev["fired_R"],
                      "held_R":int(len(te)),"held_baseline_hits":b,"held_rule_hits":held_ev["hits"],
                      "held_rescued":held_ev["rescued"],"held_damaged":held_ev["damaged"],
                      "held_net":held_ev["hits"]-b,"held_fired":held_ev["fired_R"]})
    result={"population":"DEV head1 wins; nested month-held-out selection for dedicated 5-second gate family",
            "baseline":{"R":int(len(q)),"hits":total_base,"rate":total_base/len(q)},
            "nested_oof":{"hits":total_new,"rate":total_new/len(q),"rescued":resc_total,"damaged":dam_total,"net":total_new-total_base},
            "folds":outer,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    pd.DataFrame(outer).to_csv(OUT/"folds.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_FIVE_NESTED_V14",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
