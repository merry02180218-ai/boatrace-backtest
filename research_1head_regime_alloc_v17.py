#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import onehead_production_profile as prod

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v17"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file():return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def bycode(rs):return {str(r.get("レースコード","")).zfill(12):r for r in rs}

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

def build(prepared,root):
    x=pickle.load(open(prepared,"rb"));rr=x["rows"];cache={};rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        if code[:8]>="20260901":raise RuntimeError("September entered")
        p2,pc=v365.formal_post_five6(r);prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]
        actual=str(r.get("actual_combo",""));parts=actual.split("-")
        head1=int(len(parts)==3 and parts[0]=="1");actual2=int(parts[1]) if head1 else None
        day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")))
        card=cache[day][0].get(code,{});w=cache[day][1].get(code,{})
        if not card:continue
        xf=bt.race_features(card,w);p2order=sorted(BOATS,key=lambda b:p2[b],reverse=True)
        z={"race_code":code,"month":m,"actual_combo":actual,"head1":head1,"actual2":actual2,
           "formal":formal,"formal_hit":int(actual in [f"1-{s}-{t}" for s,t in formal]),
           "base1":p2order[0],"base2":p2order[1],
           "second_baseline_hit":int(head1 and actual2 in p2order[:2]),
           "c5_already_second":int(5 in p2order[:2]),"c5_already_ticket":int(any(s==5 for s,t in formal)),
           "c5_ratio2":float(p2[5])/max(float(p2[p2order[1]]),1e-12),"pc":pc}
        z["local_edge"]=ff(xf[5]["local"])-ff(xf[4]["local"])
        z["wr_edge"]=ff(xf[5]["wr"])-ff(xf[4]["wr"])
        for met in ("core","straight","avg"):
            e=ff(r.get(f"{met}5"))-ff(r.get(f"{met}4"))
            z[f"{met}_beat"]=int(np.isfinite(e) and e>0)
        z["foot_count"]=z["core_beat"]+z["straight_beat"]+z["avg_beat"]
        rows.append(z)
    return pd.DataFrame(rows)

def eval_second(df,fn):
    h=df[df.head1.eq(1)].copy();fire=fn(h)&h.c5_already_second.eq(0)
    new=[];resc=dam=0
    for i,r in h.iterrows():
        old=int(r.second_baseline_hit)
        nh=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[i]) else old
        new.append(nh);resc+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
    return {"hits":int(sum(new)),"rescued":resc,"damaged":dam,"net":resc-dam,"fired_R":int(fire.sum())}

def five_thirds(r):
    return sorted([t for t in BOATS if t!=5],key=lambda t:(-float(r.pc[(5,t)]),t))

def tickets_for(r,arch):
    formal=list(r.formal)
    if arch=="NO_CHANGE":return formal
    th=five_thirds(r)
    if arch=="FIVE1":
        new=[formal[0],formal[1],(5,th[0])]
    elif arch=="FIVE2":
        new=[formal[0],(5,th[0]),(5,th[1])]
    elif arch=="FIVE3":
        new=[(5,th[0]),(5,th[1]),(5,th[2])]
    else:raise RuntimeError(arch)
    # uniqueness safety
    out=[]
    for x in new:
        if x not in out:out.append(x)
    for x in formal:
        if len(out)>=3:break
        if x not in out:out.append(x)
    return out[:3]

def eval_exact(df,fn,arch):
    fire=(fn(df)&df.c5_already_ticket.eq(0)) if fn is not None else pd.Series(False,index=df.index)
    rec=[];resc=dam=0
    for i,r in df.iterrows():
        formal=list(r.formal);new=tickets_for(r,arch) if bool(fire.loc[i]) else formal
        old=int(r.formal_hit);hit=int(r.actual_combo in [f"1-{s}-{t}" for s,t in new])
        rec.append({"race_code":r.race_code,"month":r.month,"formal_hit":old,"new_hit":hit,"fire":int(bool(fire.loc[i]))})
        resc+=int(old==0 and hit==1);dam+=int(old==1 and hit==0)
    z=pd.DataFrame(rec)
    return {"hits":int(z.new_hit.sum()),"rescued":resc,"damaged":dam,"net":resc-dam,"fired_R":int(z.fire.sum()),"rows":z}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    q=build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)!=190 or int(q.formal_hit.sum())!=98 or int(q.head1.sum())!=163:raise RuntimeError("sentinel drift")
    rules=specs();folds=[];allrows=[]
    for held in DEV:
        tr=q[q.month.ne(held)].copy();te=q[q.month.eq(held)].copy()
        base_second=int(tr[tr.head1.eq(1)].second_baseline_hit.sum())
        rcands=[("NO_CHANGE",None,{"hits":base_second,"net":0,"fired_R":0})]
        for name,fn in rules:
            ev=eval_second(tr,fn)
            if ev["hits"]>base_second:rcands.append((name,fn,ev))
        rcands.sort(key=lambda x:(x[2]["hits"],x[2]["net"],-x[2]["fired_R"]),reverse=True)
        rname,fn,sev=rcands[0]

        # architecture selection on training exact3 only after second rule is frozen.
        acands=[]
        for arch in ("NO_CHANGE","FIVE1","FIVE2","FIVE3"):
            ev=eval_exact(tr,fn,arch)
            acands.append((arch,ev))
        base_exact=int(tr.formal_hit.sum())
        # allow NO_CHANGE; choose max exact hits, then fewer damage, then fewer fires, then less aggressive architecture.
        order_pref={"NO_CHANGE":0,"FIVE1":1,"FIVE2":2,"FIVE3":3}
        acands.sort(key=lambda x:(x[1]["hits"],-x[1]["damaged"],-x[1]["fired_R"],-order_pref[x[0]]),reverse=True)
        arch,train_exact=acands[0]

        held_exact=eval_exact(te,fn,arch)
        held_second=eval_second(te,fn) if fn is not None else {"hits":int(te[te.head1.eq(1)].second_baseline_hit.sum()),"net":0,"fired_R":0}
        base_held=int(te.formal_hit.sum())
        folds.append({
          "held_month":held,"selected_rule":rname,"selected_arch":arch,
          "train_second_baseline":base_second,"train_second_rule":sev["hits"],
          "train_exact_baseline":base_exact,"train_exact_rule":train_exact["hits"],
          "held_R":len(te),"held_exact_baseline":base_held,"held_exact_rule":held_exact["hits"],
          "held_exact_net":held_exact["hits"]-base_held,"held_rescued":held_exact["rescued"],"held_damaged":held_exact["damaged"],
          "held_second_rule":held_second["hits"],"held_fired":held_exact["fired_R"]
        })
        hz=held_exact["rows"].copy();hz["selected_rule"]=rname;hz["selected_arch"]=arch;allrows.append(hz)
    f=pd.DataFrame(folds);z=pd.concat(allrows,ignore_index=True)
    result={"population":"DEV H078_M375 nested: select 5-second rule, then ticket allocation, then held exact3",
            "baseline":{"R":190,"hits":98,"rate":98/190},
            "nested":{"hits":int(z.new_hit.sum()),"rate":float(z.new_hit.mean()),"net":int(z.new_hit.sum()-98),
                      "rescued":int(((z.formal_hit==0)&(z.new_hit==1)).sum()),
                      "damaged":int(((z.formal_hit==1)&(z.new_hit==0)).sum())},
            "folds":folds,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    f.to_csv(OUT/"folds.csv",index=False);z.to_csv(OUT/"held_rows.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_REGIME_ALLOC_V17",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
