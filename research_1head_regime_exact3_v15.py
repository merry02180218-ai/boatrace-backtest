#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle,math
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import onehead_production_profile as prod

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v15"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def bycode(rs): return {str(r.get("レースコード","")).zfill(12):r for r in rs}

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
    x=pickle.load(open(prepared,"rb")); rr=x["rows"]; cache={}; rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12); m=code[:4]+"-"+code[4:6]
        if m not in DEV: continue
        if code[:8]>="20260901": raise RuntimeError("September entered")
        p2,pc=v365.formal_post_five6(r)
        prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]
        if len(formal)!=3 or len(set(formal))!=3: raise RuntimeError("formal ticket drift")
        actual=str(r.get("actual_combo",""))
        parts=actual.split("-")
        head1=int(len(parts)==3 and parts[0]=="1")
        actual2=int(parts[1]) if head1 else None
        day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")))
        cards,waku=cache[day]; card=cards.get(code,{}); w=waku.get(code,{})
        if not card: continue
        xf=bt.race_features(card,w)
        p2order=sorted(BOATS,key=lambda b:p2[b],reverse=True)
        z={
          "race_code":code,"month":m,"actual_combo":actual,"head1":head1,"actual2":actual2,
          "formal":formal,"formal_hit":int(actual in [f"1-{s}-{t}" for s,t in formal]),
          "base1":p2order[0],"base2":p2order[1],
          "second_baseline_hit":int(head1 and actual2 in p2order[:2]),
          "c5_already_second":int(5 in p2order[:2]),
          "c5_already_ticket":int(any(s==5 for s,t in formal)),
          "c5_ratio2":float(p2[5])/max(float(p2[p2order[1]]),1e-12),
          "p2":p2,"pc":pc,"prob":prob
        }
        z["local_edge"]=ff(xf[5]["local"])-ff(xf[4]["local"])
        z["wr_edge"]=ff(xf[5]["wr"])-ff(xf[4]["wr"])
        for met in ("core","straight","avg"):
            e=ff(r.get(f"{met}5"))-ff(r.get(f"{met}4"))
            z[f"{met}_beat"]=int(np.isfinite(e) and e>0)
        z["foot_count"]=z["core_beat"]+z["straight_beat"]+z["avg_beat"]
        rows.append(z)
    return pd.DataFrame(rows)

def eval_second(df,fn):
    h=df[df.head1.eq(1)].copy()
    fire=fn(h)&h.c5_already_second.eq(0)
    new=[];resc=dam=0
    for i,r in h.iterrows():
        old=int(r.second_baseline_hit)
        nh=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[i]) else old
        new.append(nh); resc+=int(old==0 and nh==1); dam+=int(old==1 and nh==0)
    return {"R":len(h),"hits":int(sum(new)),"rescued":resc,"damaged":dam,"net":resc-dam,"fired_R":int(fire.sum())}

def regime_ticket(r):
    pc=r.pc
    thirds=sorted([t for t in BOATS if t!=5],key=lambda t:(-float(pc[(5,t)]),t))
    return (5,thirds[0])

def eval_exact(df,fn):
    fire=fn(df)&df.c5_already_ticket.eq(0)
    rec=[];resc=dam=0
    for i,r in df.iterrows():
        formal=list(r.formal); old=int(r.formal_hit); new=list(formal)
        cand=None
        if bool(fire.loc[i]):
            cand=regime_ticket(r)
            # New architecture: preserve primary HYBRID two tickets, replace only alternate-second ticket.
            new=[formal[0],formal[1],cand]
            # hard uniqueness fallback
            if len(set(new))<3:
                ordered=[x for x in v299.joint_order(r.prob) if x not in new]
                new=[formal[0],formal[1],ordered[0]]
        newstr=[f"1-{s}-{t}" for s,t in new]
        hit=int(r.actual_combo in newstr)
        rec.append({"race_code":r.race_code,"month":r.month,"actual_combo":r.actual_combo,
                    "formal":";".join(f"1-{s}-{t}" for s,t in formal),
                    "new":";".join(newstr),"fire":int(bool(fire.loc[i])),
                    "formal_hit":old,"new_hit":hit,
                    "candidate":"" if cand is None else f"1-{cand[0]}-{cand[1]}"})
        resc+=int(old==0 and hit==1);dam+=int(old==1 and hit==0)
    z=pd.DataFrame(rec)
    return z,{"R":len(z),"hits":int(z.new_hit.sum()),"rate":float(z.new_hit.mean()),
              "rescued":resc,"damaged":dam,"net":resc-dam,"fired_R":int(z.fire.sum())}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    q=build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)!=190: raise RuntimeError(f"DEV exact universe drift {len(q)}")
    if int(q.formal_hit.sum())!=98: raise RuntimeError(f"formal exact3 drift {int(q.formal_hit.sum())}")
    if int(q.head1.sum())!=163: raise RuntimeError(f"head1 drift {int(q.head1.sum())}")
    rules=specs()
    folds=[]; all_rows=[]
    for held in DEV:
        tr=q[q.month.ne(held)].copy(); te=q[q.month.eq(held)].copy()
        base_train=int(tr[tr.head1.eq(1)].second_baseline_hit.sum())
        candidates=[("NO_CHANGE",None,{"hits":base_train,"net":0,"fired_R":0})]
        for name,fn in rules:
            ev=eval_second(tr,fn)
            if ev["hits"]>base_train: candidates.append((name,fn,ev))
        candidates.sort(key=lambda x:(x[2]["hits"],x[2]["net"],-x[2]["fired_R"]),reverse=True)
        name,fn,sev=candidates[0]
        if fn is None:
            ez=te[["race_code","month","actual_combo","formal_hit"]].copy()
            ez["new_hit"]=ez.formal_hit;ez["fire"]=0;ez["candidate"]="";em={"R":len(te),"hits":int(ez.new_hit.sum()),"rate":float(ez.new_hit.mean()),"rescued":0,"damaged":0,"net":0,"fired_R":0}
        else:
            ez,em=eval_exact(te,fn)
        base_exact=int(te.formal_hit.sum())
        held_second=eval_second(te,fn) if fn is not None else {"hits":int(te[te.head1.eq(1)].second_baseline_hit.sum()),"rescued":0,"damaged":0,"net":0,"fired_R":0}
        folds.append({
          "held_month":held,"selected_rule":name,
          "train_second_baseline_hits":base_train,"train_second_rule_hits":sev["hits"],"train_second_net":sev["net"],"train_fired":sev["fired_R"],
          "held_R":len(te),"held_head1_R":int(te.head1.sum()),
          "held_second_baseline_hits":int(te[te.head1.eq(1)].second_baseline_hit.sum()),
          "held_second_rule_hits":held_second["hits"],"held_second_net":held_second["net"],
          "held_exact_baseline_hits":base_exact,"held_exact_rule_hits":em["hits"],
          "held_exact_rescued":em["rescued"],"held_exact_damaged":em["damaged"],
          "held_exact_net":em["hits"]-base_exact,"held_fired":em["fired_R"]
        })
        ez["selected_rule"]=name;all_rows.append(ez)
    folds_df=pd.DataFrame(folds); rows_df=pd.concat(all_rows,ignore_index=True)
    baseline=int(q.formal_hit.sum()); new=int(rows_df.new_hit.sum())
    # Diagnostics: if fire and actual second really is 5, how often conditional pc top1 gets third exactly.
    diag=[]
    for held in DEV:
        fr=folds_df[folds_df.held_month.eq(held)].iloc[0]
        name=fr.selected_rule
        fn=dict((n,f) for n,f in rules).get(name)
        if fn is None: continue
        te=q[q.month.eq(held)].copy();fire=fn(te)&te.c5_already_ticket.eq(0)
        g=te[fire & te.head1.eq(1) & te.actual2.eq(5)]
        exact_cond=0; total=0
        for _,r in g.iterrows():
            cand=regime_ticket(r); parts=r.actual_combo.split("-")
            total+=1; exact_cond+=int(int(parts[2])==cand[1])
        diag.append({"held_month":held,"actual5_fired_R":total,"conditional_third_top1_hits":exact_cond,
                     "conditional_third_top1_rate":exact_cond/total if total else None})
    result={
      "population":"DEV H078_M375 exact3; nested second-rule selection, held-month exact3 evaluation",
      "baseline":{"R":len(q),"hits":baseline,"rate":baseline/len(q)},
      "nested_regime_exact3":{"hits":new,"rate":new/len(q),"net":new-baseline,
                              "rescued":int(((rows_df.formal_hit==0)&(rows_df.new_hit==1)).sum()),
                              "damaged":int(((rows_df.formal_hit==1)&(rows_df.new_hit==0)).sum())},
      "folds":folds,"conditional_third_diag":diag,
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False
    }
    folds_df.to_csv(OUT/"folds.csv",index=False);rows_df.to_csv(OUT/"held_rows.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_REGIME_EXACT3_V15",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
