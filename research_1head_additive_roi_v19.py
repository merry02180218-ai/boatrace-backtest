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
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v19"
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
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")),
                        bycode(load_csv(root,f"data/results/payouts/{ymd}.csv")))
        cards,waku,pays=cache[day];card=cards.get(code,{});w=waku.get(code,{});pay=pays.get(code,{})
        if not card:continue
        xf=bt.race_features(card,w);p2order=sorted(BOATS,key=lambda b:p2[b],reverse=True)
        payout=int(float(pay.get("3連単_払戻金") or 0))
        z={"race_code":code,"month":m,"actual_combo":actual,"head1":head1,"actual2":actual2,
           "payout":payout,"formal":formal,"formal_hit":int(actual in [f"1-{s}-{t}" for s,t in formal]),
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
    h=df[df.head1.eq(1)].copy();fire=fn(h)&h.c5_already_second.eq(0);hits=res=dam=0
    for i,r in h.iterrows():
        old=int(r.second_baseline_hit);nh=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[i]) else old
        hits+=nh;res+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
    return {"hits":hits,"net":res-dam,"fired_R":int(fire.sum())}

def five_thirds(r):
    return sorted([t for t in BOATS if t!=5],key=lambda t:(-float(r.pc[(5,t)]),t))

def apply_add2(df,fn):
    fire=fn(df)&df.c5_already_ticket.eq(0)
    rec=[]
    for i,r in df.iterrows():
        formal=[f"1-{s}-{t}" for s,t in r.formal];tickets=list(formal);extras=[]
        if bool(fire.loc[i]):
            for t in five_thirds(r)[:2]:
                x=f"1-5-{t}"
                if x not in tickets:tickets.append(x);extras.append(x)
        new_hit=int(r.actual_combo in tickets)
        rec.append({"race_code":r.race_code,"month":r.month,"payout":int(r.payout),
                    "formal_hit":int(r.formal_hit),"new_hit":new_hit,"extra_count":len(extras),"extras":";".join(extras)})
    return pd.DataFrame(rec)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    q=build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)!=190 or int(q.formal_hit.sum())!=98:raise RuntimeError("sentinel drift")
    rules=specs();parts=[]
    for held in DEV:
        tr=q[q.month.ne(held)];te=q[q.month.eq(held)]
        base=int(tr[tr.head1.eq(1)].second_baseline_hit.sum())
        cand=[("NO_CHANGE",None,{"hits":base,"net":0,"fired_R":0})]
        for name,fn in rules:
            ev=eval_second(tr,fn)
            if ev["hits"]>base:cand.append((name,fn,ev))
        cand.sort(key=lambda x:(x[2]["hits"],x[2]["net"],-x[2]["fired_R"]),reverse=True)
        name,fn,ev=cand[0]
        if fn is None:
            z=te[["race_code","month","payout","formal_hit"]].copy();z["new_hit"]=z.formal_hit;z["extra_count"]=0;z["extras"]=""
        else:z=apply_add2(te,fn)
        z["selected_rule"]=name;parts.append(z)
    z=pd.concat(parts,ignore_index=True)
    def metric(hitcol,stake):
        ret=int(z.loc[z[hitcol].eq(1),"payout"].sum())
        return {"R":len(z),"hits":int(z[hitcol].sum()),"stake":int(stake),"return":ret,
                "profit":ret-int(stake),"roi":ret/int(stake)}
    base_stake=len(z)*300
    extra=int(z.extra_count.sum())*100
    baseline=metric("formal_hit",base_stake)
    add2=metric("new_hit",base_stake+extra)
    monthly=[]
    for m,g in z.groupby("month"):
        bs=len(g)*300;es=int(g.extra_count.sum())*100
        br=int(g.loc[g.formal_hit.eq(1),"payout"].sum());nr=int(g.loc[g.new_hit.eq(1),"payout"].sum())
        monthly.append({"month":m,"R":len(g),"baseline_hits":int(g.formal_hit.sum()),"add2_hits":int(g.new_hit.sum()),
                        "extra_tickets":int(g.extra_count.sum()),"baseline_roi":br/bs,
                        "add2_roi":nr/(bs+es),"baseline_return":br,"add2_return":nr})
    result={"population":"DEV nested additive 5-second top2 conditional tickets; 100 yen uniform payout audit",
            "baseline":baseline,"add2":add2,"extra_tickets":int(z.extra_count.sum()),
            "delta_hits":add2["hits"]-baseline["hits"],"delta_roi_pp":100*(add2["roi"]-baseline["roi"]),
            "monthly":monthly,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    z.to_csv(OUT/"rows.csv",index=False);pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_ADDITIVE_ROI_V19",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
