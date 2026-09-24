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
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v12"
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

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    x=pickle.load(a.prepared.open("rb"));rr=x["rows"];cache={};rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        actual2=int(p[1]);day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")))
        cards,waku=cache[day];card=cards.get(code,{});w=waku.get(code,{})
        if not card:continue
        xfeat=bt.race_features(card,w)
        p2,pc=v365.formal_post_five6(r);pv={b:ff(p2.get(b)) for b in BOATS}
        order=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        z={"race_code":code,"month":m,"actual2":actual2,"base1":order[0],"base2":order[1],
           "baseline_hit":int(actual2 in order[:2]),"c5_already":int(5 in order[:2]),
           "c5_ratio2":pv[5]/max(pv[order[1]],1e-12)}
        c,i=xfeat[5],xfeat[4]
        z["local_edge"]=ff(c["local"])-ff(i["local"]);z["wr_edge"]=ff(c["wr"])-ff(i["wr"])
        z["motor2_edge"]=ff(c["motor2"])-ff(i["motor2"]);z["motor3_edge"]=ff(c["motor3"])-ff(i["motor3"])
        for met in ("score","core","ex","straight","avg"):
            cv=ff(r.get(f"{met}5"));iv=ff(r.get(f"{met}4"))
            z[f"{met}_edge"]=cv-iv if np.isfinite(cv) and np.isfinite(iv) else np.nan
            z[f"{met}_beat"]=int(np.isfinite(z[f"{met}_edge"]) and z[f"{met}_edge"]>0)
        z["foot_count"]=z["core_beat"]+z["straight_beat"]+z["avg_beat"]
        rows.append(z)
    q=pd.DataFrame(rows)
    if len(q)<160:raise RuntimeError(f"coverage {len(q)}")
    q.to_csv(OUT/"dev_rows.csv",index=False)

    specs=[]
    for ratio in (.25,.35,.50,.65):
      specs += [
        (f"LOCAL_FOOT2_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.foot_count>=2)&(d.c5_ratio2>=ratio)),
        (f"LOCAL_WR_FOOT2_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.wr_edge>0)&(d.foot_count>=2)&(d.c5_ratio2>=ratio)),
        (f"LOCAL_STRAIGHT_CORE_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.straight_beat==1)&(d.core_beat==1)&(d.c5_ratio2>=ratio)),
        (f"LOCAL_STRAIGHT_AVG_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.straight_beat==1)&(d.avg_beat==1)&(d.c5_ratio2>=ratio)),
        (f"LOCAL_WR_TRIPLE_R{ratio:.2f}",lambda d,ratio=ratio:(d.local_edge>0)&(d.wr_edge>0)&(d.foot_count==3)&(d.c5_ratio2>=ratio)),
      ]
    rules=[]
    for name,fn in specs:
        fire=fn(q)&q.c5_already.eq(0)
        new=[];resc=dam=0
        for idx,r in q.iterrows():
            old=int(r.baseline_hit)
            nh=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[idx]) else old
            new.append(nh);resc+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
        month={}
        z=q.assign(fire=fire,new_hit=new)
        for m,g in z.groupby("month"):
            month[m]={"fired":int(g.fire.sum()),"rescued":int(((g.baseline_hit==0)&(g.new_hit==1)).sum()),
                      "damaged":int(((g.baseline_hit==1)&(g.new_hit==0)).sum()),"new_hits":int(g.new_hit.sum())}
        rules.append({"rule":name,"fired_R":int(fire.sum()),"rescued":resc,"damaged":dam,"net":resc-dam,
                      "hits":int(sum(new)),"rate":float(np.mean(new)),"monthly":month})
    rules.sort(key=lambda x:(x["hits"],x["net"],-x["fired_R"]),reverse=True)

    # Descriptive positive-vs-rest separation.
    pos=q[q.actual2.eq(5)];neg=q[q.actual2.ne(5)]
    desc={"positive_R":int(len(pos))}
    for c in ("local_edge","wr_edge","score_edge","core_edge","ex_edge","straight_edge","avg_edge","c5_ratio2"):
        ps=pd.to_numeric(pos[c],errors="coerce");ns=pd.to_numeric(neg[c],errors="coerce")
        desc[c]={"pos_mean":float(ps.mean()),"neg_mean":float(ns.mean()),
                 "pos_positive_rate":float((ps>0).mean()),"neg_positive_rate":float((ns>0).mean())}
    result={"population":"DEV head1 wins; dedicated 5-second local-strength+foot gates",
            "baseline":{"R":int(len(q)),"hits":int(q.baseline_hit.sum()),"rate":float(q.baseline_hit.mean())},
            "descriptive":desc,"top_rules":rules[:25],
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    pd.DataFrame([{k:v for k,v in r.items() if k!="monthly"} for r in rules]).to_csv(OUT/"rule_scan.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_FIVE_GATE_V12",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
