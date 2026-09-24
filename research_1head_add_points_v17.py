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
        formal_str=[f"1-{s}-{t}" for s,t in formal]
        z={
          "race_code":code,"month":m,"actual_combo":actual,"head1":head1,"actual2":actual2,
          "formal":formal,"formal_str":";".join(formal_str),
          "formal_hit":int(actual in formal_str),
          "base1":p2order[0],"base2":p2order[1],
          "second_baseline_hit":int(head1 and actual2 in p2order[:2]),
          "c5_already_second":int(5 in p2order[:2]),
          "c5_ratio2":float(p2[5])/max(float(p2[p2order[1]]),1e-12),
          "pc":pc
        }
        z["local_edge"]=ff(xf[5]["local"])-ff(xf[4]["local"])
        z["wr_edge"]=ff(xf[5]["wr"])-ff(xf[4]["wr"])
        for met in ("core","straight","avg"):
            e=ff(r.get(f"{met}5"))-ff(r.get(f"{met}4"))
            z[f"{met}_beat"]=int(np.isfinite(e) and e>0)
        z["foot_count"]=z["core_beat"]+z["straight_beat"]+z["avg_beat"]
        rows.append(z)
    return pd.DataFrame(rows), x

def eval_second(df,fn):
    h=df[df.head1.eq(1)].copy()
    fire=fn(h)&h.c5_already_second.eq(0)
    hits=resc=dam=0
    for i,r in h.iterrows():
        old=int(r.second_baseline_hit)
        new=int(int(r.actual2) in (int(r.base1),5)) if bool(fire.loc[i]) else old
        hits+=new;resc+=int(old==0 and new==1);dam+=int(old==1 and new==0)
    return {"hits":hits,"rescued":resc,"damaged":dam,"net":resc-dam,"fired_R":int(fire.sum())}

def extras_for_row(r,n):
    formal=set(r.formal_str.split(";"))
    thirds=sorted([t for t in BOATS if t!=5],key=lambda t:(-float(r.pc[(5,t)]),t))
    out=[]
    for t in thirds:
        ticket=f"1-5-{t}"
        if ticket not in formal and ticket not in out:
            out.append(ticket)
        if len(out)>=n: break
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    q,x=build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)!=190 or int(q.formal_hit.sum())!=98 or int(q.head1.sum())!=163:
        raise RuntimeError(f"sentinel drift R={len(q)} hit={int(q.formal_hit.sum())} head1={int(q.head1.sum())}")
    # payouts only for DEV rows; no Jul/Aug/September outcome access.
    dev_rows=[r for r in x["rows"]["H078_M375"] if str(r["month"]) in DEV]
    v365.install_payout_cache(dev_rows)
    payouts=v365.payouts_for(dev_rows)

    rules=specs()
    held_parts=[]
    fold_meta=[]
    for held in DEV:
        tr=q[q.month.ne(held)].copy(); te=q[q.month.eq(held)].copy()
        base_train=int(tr[tr.head1.eq(1)].second_baseline_hit.sum())
        cand=[("NO_CHANGE",None,{"hits":base_train,"net":0,"fired_R":0})]
        for name,fn in rules:
            ev=eval_second(tr,fn)
            if ev["hits"]>base_train: cand.append((name,fn,ev))
        cand.sort(key=lambda x:(x[2]["hits"],x[2]["net"],-x[2]["fired_R"]),reverse=True)
        name,fn,train_ev=cand[0]
        if fn is None:
            fire=pd.Series(False,index=te.index)
        else:
            fire=fn(te)&te.c5_already_second.eq(0)
        part=te.copy()
        part["selected_rule"]=name
        part["fire"]=fire.astype(int)
        held_parts.append(part)
        fold_meta.append({"held_month":held,"selected_rule":name,
                          "train_second_baseline_hits":base_train,
                          "train_second_rule_hits":train_ev["hits"],
                          "train_second_net":train_ev["net"],
                          "train_fired":train_ev["fired_R"],
                          "held_fire_R":int(fire.sum())})
    z=pd.concat(held_parts,ignore_index=True)

    baseline_return=sum(payouts[str(r.race_code).zfill(12)] for _,r in z.iterrows() if int(r.formal_hit))
    baseline_stake=len(z)*300
    baseline={"R":len(z),"hits":int(z.formal_hit.sum()),"stake":baseline_stake,
              "return":baseline_return,"profit":baseline_return-baseline_stake,
              "roi":baseline_return/baseline_stake}
    modes=[]
    row_records=[]
    for n in (1,2,3,4):
        total_stake=0;total_return=0;hits=0;resc=0;added_tickets=0;added_return=0
        monthly={}
        for _,r in z.iterrows():
            extras=extras_for_row(r,n) if int(r.fire) else []
            all_tickets=set(r.formal_str.split(";"))|set(extras)
            hit=int(r.actual_combo in all_tickets)
            payout=payouts[str(r.race_code).zfill(12)] if hit else 0
            stake=(3+len(extras))*100
            base_hit=int(r.formal_hit)
            rescue=int(base_hit==0 and hit==1)
            incr_return=payout if rescue else 0
            total_stake+=stake; total_return+=payout; hits+=hit; resc+=rescue
            added_tickets+=len(extras); added_return+=incr_return
            row_records.append({"mode":f"ADD{n}","race_code":r.race_code,"month":r.month,
                                "selected_rule":r.selected_rule,"fire":int(r.fire),
                                "formal":r.formal_str,"extras":";".join(extras),
                                "actual_combo":r.actual_combo,"formal_hit":base_hit,"hit":hit,
                                "rescue":rescue,"payout":payout,"stake":stake})
        rz=pd.DataFrame([x for x in row_records if x["mode"]==f"ADD{n}"])
        for m,g in rz.groupby("month"):
            stake=int(g.stake.sum());ret=int(g.payout.sum())
            monthly[m]={"R":int(len(g)),"fires":int(g.fire.sum()),"added_tickets":int(g.extras.apply(lambda s:0 if not s else len(s.split(";"))).sum()),
                        "hits":int(g.hit.sum()),"rescues":int(g.rescue.sum()),"stake":stake,"return":ret,
                        "roi":ret/stake if stake else None}
        add_stake=added_tickets*100
        modes.append({
          "mode":f"ADD{n}","R":len(z),"fires":int(z.fire.sum()),"added_tickets":added_tickets,
          "hits":hits,"hit_rate":hits/len(z),"rescues":resc,
          "stake":total_stake,"return":total_return,"profit":total_return-total_stake,
          "roi":total_return/total_stake if total_stake else None,
          "delta_hits":hits-baseline["hits"],"delta_roi_pp":100*(total_return/total_stake-baseline["roi"]),
          "added_stake":add_stake,"added_return":added_return,
          "marginal_roi":added_return/add_stake if add_stake else None,
          "monthly":monthly
        })
    pd.DataFrame(fold_meta).to_csv(OUT/"folds.csv",index=False)
    pd.DataFrame(row_records).to_csv(OUT/"rows.csv",index=False)
    result={"population":"DEV H078_M375; nested 5-second regime; preserve formal HYBRID3 and add 1-5 conditional-third tickets",
            "baseline":baseline,"modes":modes,"folds":fold_meta,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_ADD_POINTS_V17",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
