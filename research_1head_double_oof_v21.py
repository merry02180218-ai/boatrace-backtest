#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle,itertools
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import onehead_production_profile as prod

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
LS=(0.0,.5,1.0)
SS=(0.0,.10,.20)
CS=(0.0,.05,.10)
RS=(.25,.35,.50)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v21"
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

def build(prepared,root):
    x=pickle.load(open(prepared,"rb"));rr=x["rows"];cache={};rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p2,pc=v365.formal_post_five6(r);prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3];actual=str(r.get("actual_combo",""))
        parts=actual.split("-");head1=int(len(parts)==3 and parts[0]=="1");actual2=int(parts[1]) if head1 else None
        p2order=sorted(BOATS,key=lambda b:p2[b],reverse=True)
        day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")),
                        bycode(load_csv(root,f"data/results/payouts/{ymd}.csv")))
        card=cache[day][0].get(code,{});w=cache[day][1].get(code,{});pay=cache[day][2].get(code,{})
        if not card:continue
        xf=bt.race_features(card,w)
        rows.append({
          "race_code":code,"month":m,"actual_combo":actual,"head1":head1,"actual2":actual2,
          "formal":formal,"formal_hit":int(actual in [f"1-{s}-{t}" for s,t in formal]),
          "base1":p2order[0],"base2":p2order[1],"second_baseline_hit":int(head1 and actual2 in p2order[:2]),
          "c5_already_second":int(5 in p2order[:2]),"c5_already_ticket":int(any(s==5 for s,t in formal)),
          "ratio":float(p2[5])/max(float(p2[p2order[1]]),1e-12),
          "local":ff(xf[5]["local"])-ff(xf[4]["local"]),
          "straight":ff(r.get("straight5"))-ff(r.get("straight4")),
          "core":ff(r.get("core5"))-ff(r.get("core4")),
          "pc":pc,"payout":int(float(pay.get("3連単_払戻金") or 0))
        })
    return pd.DataFrame(rows)

def mask(df,cfg,already_col):
    l,s,c,r=cfg
    return (df.local>=l)&(df.straight>=s)&(df.core>=c)&(df.ratio>=r)&df[already_col].eq(0)

def second_eval(df,cfg):
    h=df[df.head1.eq(1)].copy();fire=mask(h,cfg,"c5_already_second")
    hits=res=dam=0
    for i,r in h.iterrows():
        old=int(r.second_baseline_hit);nh=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[i]) else old
        hits+=nh;res+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
    return {"hits":hits,"net":res-dam,"rescued":res,"damaged":dam,"fired":int(fire.sum())}

def inner_score(train,cfg):
    vals=[]
    months=sorted(train.month.unique())
    for hm in months:
        te=train[train.month.eq(hm)]
        ev=second_eval(te,cfg)
        base=int(te[te.head1.eq(1)].second_baseline_hit.sum())
        vals.append(ev["hits"]-base)
    return (sum(vals),min(vals),sum(1 for x in vals if x>=0),-second_eval(train,cfg)["fired"])

def five_thirds(r):
    return sorted([t for t in BOATS if t!=5],key=lambda t:(-float(r.pc[(5,t)]),t))

def exact_add2(df,cfg):
    fire=mask(df,cfg,"c5_already_ticket");recs=[]
    for i,r in df.iterrows():
        base=[f"1-{s}-{t}" for s,t in r.formal];extra=[]
        if bool(fire.loc[i]):
            for t in five_thirds(r)[:2]:
                x=f"1-5-{t}"
                if x not in base:extra.append(x)
        tickets=base+extra
        recs.append({"race_code":r.race_code,"month":r.month,"formal_hit":int(r.formal_hit),
                     "new_hit":int(r.actual_combo in tickets),"extra_count":len(extra),"payout":int(r.payout)})
    return pd.DataFrame(recs)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    q=build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)!=190 or int(q.formal_hit.sum())!=98 or int(q.head1.sum())!=163:raise RuntimeError("sentinel drift")
    cfgs=list(itertools.product(LS,SS,CS,RS))
    folds=[];parts=[]
    for held in DEV:
        tr=q[q.month.ne(held)].copy();te=q[q.month.eq(held)].copy()
        ranked=sorted(cfgs,key=lambda cfg:inner_score(tr,cfg),reverse=True)
        cfg=ranked[0]
        sev=second_eval(te,cfg);base_second=int(te[te.head1.eq(1)].second_baseline_hit.sum())
        ez=exact_add2(te,cfg);base_exact=int(te.formal_hit.sum())
        folds.append({"held_month":held,"local_min":cfg[0],"straight_min":cfg[1],"core_min":cfg[2],"ratio_min":cfg[3],
                      "inner_score":inner_score(tr,cfg)[0],"held_second_baseline":base_second,"held_second_hits":sev["hits"],
                      "held_second_net":sev["hits"]-base_second,"held_exact_baseline":base_exact,
                      "held_exact_hits":int(ez.new_hit.sum()),"held_exact_net":int(ez.new_hit.sum()-base_exact),
                      "held_extra_tickets":int(ez.extra_count.sum())})
        ez["held_month"]=held;parts.append(ez)
    z=pd.concat(parts,ignore_index=True)
    base_stake=190*300;new_stake=base_stake+int(z.extra_count.sum())*100
    br=int(z.loc[z.formal_hit.eq(1),"payout"].sum());nr=int(z.loc[z.new_hit.eq(1),"payout"].sum())
    result={"population":"DEV double-OOF 5-second margin gate; inner month selection on second-hit only, outer exact3/ROI",
            "grid":len(cfgs),
            "baseline":{"R":190,"hits":98,"stake":base_stake,"return":br,"roi":br/base_stake},
            "outer_oof":{"hits":int(z.new_hit.sum()),"net_hits":int(z.new_hit.sum()-98),
                         "extra_tickets":int(z.extra_count.sum()),"stake":new_stake,"return":nr,"roi":nr/new_stake,
                         "rescued":int(((z.formal_hit==0)&(z.new_hit==1)).sum())},
            "delta_roi_pp":100*(nr/new_stake-br/base_stake),"folds":folds,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    pd.DataFrame(folds).to_csv(OUT/"folds.csv",index=False);z.to_csv(OUT/"rows.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_DOUBLE_OOF_V21",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
