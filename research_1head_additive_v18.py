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
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v18"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x);return v if np.isfinite(v) else np.nan
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
        p2,pc=v365.formal_post_five6(r);prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]
        actual=str(r.get("actual_combo",""));parts=actual.split("-")
        head1=int(len(parts)==3 and parts[0]=="1");actual2=int(parts[1]) if head1 else None
        day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")))
        cards,waku=cache[day];card=cards.get(code,{});w=waku.get(code,{})
        if not card:continue
        xf=bt.race_features(card,w);p2order=sorted(BOATS,key=lambda b:p2[b],reverse=True)
        z={"race_code":code,"month":m,"actual_combo":actual,"head1":head1,"actual2":actual2,
           "formal":formal,"formal_hit":int(actual in [f"1-{s}-{t}" for s,t in formal]),
           "base1":p2order[0],"base2":p2order[1],"second_baseline_hit":int(head1 and actual2 in p2order[:2]),
           "c5_already_second":int(5 in p2order[:2]),"c5_already_ticket":int(any(s==5 for s,t in formal)),
           "c5_ratio2":float(p2[5])/max(float(p2[p2order[1]]),1e-12),"pc":pc}
        z["local_edge"]=ff(xf[5]["local"])-ff(xf[4]["local"]);z["wr_edge"]=ff(xf[5]["wr"])-ff(xf[4]["wr"])
        for met in ("core","straight","avg"):
            e=ff(r.get(f"{met}5"))-ff(r.get(f"{met}4"))
            z[f"{met}_beat"]=int(np.isfinite(e) and e>0)
        z["foot_count"]=z["core_beat"]+z["straight_beat"]+z["avg_beat"]
        rows.append(z)
    return pd.DataFrame(rows)

def eval_second(df,fn):
    h=df[df.head1.eq(1)].copy();fire=fn(h)&h.c5_already_second.eq(0);hits=0;res=dam=0
    for i,r in h.iterrows():
        old=int(r.second_baseline_hit);nh=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[i]) else old
        hits+=nh;res+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
    return {"hits":hits,"net":res-dam,"rescued":res,"damaged":dam,"fired_R":int(fire.sum())}

def five_thirds(r):
    return sorted([t for t in BOATS if t!=5],key=lambda t:(-float(r.pc[(5,t)]),t))

def eval_add(df,fn,n_extra):
    fire=fn(df)&df.c5_already_ticket.eq(0)
    hits=resc=0;added=0;rows=[]
    for i,r in df.iterrows():
        formal=[f"1-{s}-{t}" for s,t in r.formal];tickets=list(formal);extras=[]
        if bool(fire.loc[i]):
            th=five_thirds(r)
            for t in th[:n_extra]:
                x=f"1-5-{t}"
                if x not in tickets:
                    tickets.append(x);extras.append(x)
        old=int(r.formal_hit);hit=int(r.actual_combo in tickets)
        hits+=hit;resc+=int(old==0 and hit==1);added+=len(extras)
        rows.append({"race_code":r.race_code,"month":r.month,"formal_hit":old,"new_hit":hit,
                     "fire":int(bool(fire.loc[i])),"extra_count":len(extras),"extras":";".join(extras)})
    z=pd.DataFrame(rows)
    return {"hits":hits,"rescued":resc,"added_tickets":added,"fired_R":int(z.fire.sum()),"rows":z}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    q=build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)!=190 or int(q.formal_hit.sum())!=98 or int(q.head1.sum())!=163:raise RuntimeError("sentinel drift")
    rules=specs();folds=[];allrows1=[];allrows2=[]
    for held in DEV:
        tr=q[q.month.ne(held)].copy();te=q[q.month.eq(held)].copy()
        base_second=int(tr[tr.head1.eq(1)].second_baseline_hit.sum())
        cand=[("NO_CHANGE",None,{"hits":base_second,"net":0,"fired_R":0})]
        for name,fn in rules:
            ev=eval_second(tr,fn)
            if ev["hits"]>base_second:cand.append((name,fn,ev))
        cand.sort(key=lambda x:(x[2]["hits"],x[2]["net"],-x[2]["fired_R"]),reverse=True)
        name,fn,sev=cand[0]
        if fn is None:
            e1={"hits":int(te.formal_hit.sum()),"rescued":0,"added_tickets":0,"fired_R":0,
                "rows":te.assign(new_hit=te.formal_hit,fire=0,extra_count=0,extras="")[["race_code","month","formal_hit","new_hit","fire","extra_count","extras"]]}
            e2=e1
        else:
            e1=eval_add(te,fn,1);e2=eval_add(te,fn,2)
        base=int(te.formal_hit.sum())
        folds.append({"held_month":held,"selected_rule":name,
                      "held_R":len(te),"baseline_hits":base,
                      "add1_hits":e1["hits"],"add1_rescued":e1["rescued"],"add1_tickets":e1["added_tickets"],"add1_fired":e1["fired_R"],
                      "add2_hits":e2["hits"],"add2_rescued":e2["rescued"],"add2_tickets":e2["added_tickets"],"add2_fired":e2["fired_R"]})
        z1=e1["rows"].copy();z1["held_month"]=held;z1["selected_rule"]=name;allrows1.append(z1)
        z2=e2["rows"].copy();z2["held_month"]=held;z2["selected_rule"]=name;allrows2.append(z2)
    z1=pd.concat(allrows1,ignore_index=True);z2=pd.concat(allrows2,ignore_index=True)
    result={"population":"DEV H078_M375 nested second-rule selection; additive 5-second conditional tickets",
            "baseline":{"R":190,"hits":98,"tickets":570},
            "add1":{"hits":int(z1.new_hit.sum()),"net_hits":int(z1.new_hit.sum()-98),
                    "rescued":int(((z1.formal_hit==0)&(z1.new_hit==1)).sum()),"extra_tickets":int(z1.extra_count.sum()),
                    "total_tickets":570+int(z1.extra_count.sum())},
            "add2":{"hits":int(z2.new_hit.sum()),"net_hits":int(z2.new_hit.sum()-98),
                    "rescued":int(((z2.formal_hit==0)&(z2.new_hit==1)).sum()),"extra_tickets":int(z2.extra_count.sum()),
                    "total_tickets":570+int(z2.extra_count.sum())},
            "folds":folds,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    pd.DataFrame(folds).to_csv(OUT/"folds.csv",index=False);z1.to_csv(OUT/"add1_rows.csv",index=False);z2.to_csv(OUT/"add2_rows.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_ADDITIVE_V18",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
