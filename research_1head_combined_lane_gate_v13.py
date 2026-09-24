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
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v13"
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
        xf=bt.race_features(card,w)
        p2,pc=v365.formal_post_five6(r);pv={b:ff(p2.get(b)) for b in BOATS}
        order=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        z={"race_code":code,"month":m,"actual2":actual2,"base1":order[0],"base2":order[1],
           "baseline_hit":int(actual2 in order[:2]),"c4_already":int(4 in order[:2]),"c5_already":int(5 in order[:2]),
           "c4_ratio2":pv[4]/max(pv[order[1]],1e-12),"c5_ratio2":pv[5]/max(pv[order[1]],1e-12)}
        # C4: foot3 vs 3
        c4cnt=0
        for met in ("core","straight","avg"):
            e=ff(r.get(f"{met}4"))-ff(r.get(f"{met}3"))
            z[f"c4_{met}_edge"]=e; c4cnt+=int(np.isfinite(e) and e>0)
        z["c4_foot3"]=c4cnt
        # C5: local + straight + core vs 4
        z["c5_local_edge"]=ff(xf[5]["local"])-ff(xf[4]["local"])
        z["c5_straight_edge"]=ff(r.get("straight5"))-ff(r.get("straight4"))
        z["c5_core_edge"]=ff(r.get("core5"))-ff(r.get("core4"))
        rows.append(z)
    q=pd.DataFrame(rows)
    if len(q)<160:raise RuntimeError(f"coverage {len(q)}")
    fire4=(q.c4_foot3==3)&(q.c4_ratio2>=.65)&q.c4_already.eq(0)
    fire5=(q.c5_local_edge>0)&(q.c5_straight_edge>0)&(q.c5_core_edge>0)&(q.c5_ratio2>=.25)&q.c5_already.eq(0)

    out=[]
    for mode in ("C4_ONLY","C5_ONLY","COMBINED"):
        new=[];resc=dam=both=0
        chosen4=chosen5=0
        for i,r in q.iterrows():
            old=int(r.baseline_hit);pair=[int(r.base1),int(r.base2)]
            f4=bool(fire4.loc[i]) and mode in ("C4_ONLY","COMBINED")
            f5=bool(fire5.loc[i]) and mode in ("C5_ONLY","COMBINED")
            if f4 and f5:
                both+=1
                if r.c4_ratio2>=r.c5_ratio2:
                    pair=[int(r.base1),4];chosen4+=1
                else:
                    pair=[int(r.base1),5];chosen5+=1
            elif f4:
                pair=[int(r.base1),4];chosen4+=1
            elif f5:
                pair=[int(r.base1),5];chosen5+=1
            nh=int(int(r.actual2) in pair);new.append(nh)
            resc+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
        z=q.assign(new_hit=new,fire4=fire4,fire5=fire5)
        monthly={}
        for m,g in z.groupby("month"):
            monthly[m]={"R":int(len(g)),"new_hits":int(g.new_hit.sum()),
                        "rescued":int(((g.baseline_hit==0)&(g.new_hit==1)).sum()),
                        "damaged":int(((g.baseline_hit==1)&(g.new_hit==0)).sum()),
                        "fire4":int(g.fire4.sum()),"fire5":int(g.fire5.sum())}
        out.append({"mode":mode,"hits":int(sum(new)),"rate":float(np.mean(new)),
                    "rescued":resc,"damaged":dam,"net":resc-dam,
                    "fire4":int(fire4.sum()) if mode!="C5_ONLY" else 0,
                    "fire5":int(fire5.sum()) if mode!="C4_ONLY" else 0,
                    "both":both,"chosen4":chosen4,"chosen5":chosen5,"monthly":monthly})
    result={"population":"DEV head1 wins; frozen best C4 + best C5 mechanism gates",
            "baseline":{"R":int(len(q)),"hits":int(q.baseline_hit.sum()),"rate":float(q.baseline_hit.mean())},
            "rules":{"C4":"foot3(core+straight+avg all beat 3) & P2 ratio>=.65",
                     "C5":"local>4 & straight>4 & core>4 & P2 ratio>=.25"},
            "results":out,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_COMBINED_LANE_GATE_V13",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
