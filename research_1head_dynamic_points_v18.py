#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os
from pathlib import Path
import pandas as pd
import numpy as np

import research_1head_add_points_v17 as v17
import run_v365_1head_exact3_hit_push as v365

DEV=v17.DEV
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v18"
OUT.mkdir(parents=True,exist_ok=True)

def apply_portfolio(df,fn,n,payouts):
    fire=(fn(df)&df.c5_already_second.eq(0)) if fn is not None else pd.Series(False,index=df.index)
    stake=ret=hits=resc=added_tickets=added_return=0
    rows=[]
    for i,r in df.iterrows():
        extras=v17.extras_for_row(r,n) if bool(fire.loc[i]) and n>0 else []
        all_tickets=set(r.formal_str.split(";"))|set(extras)
        hit=int(r.actual_combo in all_tickets)
        p=int(payouts[str(r.race_code).zfill(12)]) if hit else 0
        st=(3+len(extras))*100
        base=int(r.formal_hit); rescue=int(base==0 and hit==1)
        stake+=st;ret+=p;hits+=hit;resc+=rescue
        added_tickets+=len(extras)
        if rescue: added_return+=p
        rows.append({"race_code":r.race_code,"month":r.month,"fire":int(bool(fire.loc[i])),
                     "n":n,"extras":";".join(extras),"formal_hit":base,"hit":hit,"rescue":rescue,
                     "stake":st,"payout":p})
    add_stake=added_tickets*100
    return pd.DataFrame(rows),{
      "R":len(df),"hits":hits,"stake":stake,"return":ret,"profit":ret-stake,
      "roi":ret/stake if stake else None,"rescues":resc,
      "fires":int(fire.sum()),"added_tickets":added_tickets,
      "added_stake":add_stake,"added_return":added_return,
      "marginal_profit":added_return-add_stake,
      "marginal_roi":added_return/add_stake if add_stake else None
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    q,x=v17.build(a.prepared,os.environ["BOATRACECSV_LOCAL_ROOT"])
    if len(q)!=190 or int(q.formal_hit.sum())!=98 or int(q.head1.sum())!=163:
        raise RuntimeError("sentinel drift")
    dev_rows=[r for r in x["rows"]["H078_M375"] if str(r["month"]) in DEV]
    v365.install_payout_cache(dev_rows);payouts=v365.payouts_for(dev_rows)
    rules=v17.specs()

    fold_rows=[];held_rows=[]
    for held in DEV:
        tr=q[q.month.ne(held)].copy();te=q[q.month.eq(held)].copy()

        # Stage 1: select 5-second regime rule from second-place accuracy only.
        base_train=int(tr[tr.head1.eq(1)].second_baseline_hit.sum())
        candidates=[("NO_CHANGE",None,{"hits":base_train,"net":0,"fired_R":0})]
        for name,fn in rules:
            ev=v17.eval_second(tr,fn)
            if ev["hits"]>base_train:candidates.append((name,fn,ev))
        candidates.sort(key=lambda z:(z[2]["hits"],z[2]["net"],-z[2]["fired_R"]),reverse=True)
        rule_name,fn,second_train=candidates[0]

        # Stage 2: choose point count ONLY on the other four months.
        train_base_df,train_base=apply_portfolio(tr,fn,0,payouts)
        point_candidates=[]
        for n in (0,1,2,3,4):
            _,m=apply_portfolio(tr,fn,n,payouts)
            added_profit=m["return"]-train_base["return"]-(m["stake"]-train_base["stake"])
            point_candidates.append((n,m,added_profit))
        # Primary: incremental profit. Tie: more hits, then fewer added tickets.
        point_candidates.sort(key=lambda z:(z[2],z[1]["hits"],-z[1]["added_tickets"]),reverse=True)
        nsel,train_port,train_added_profit=point_candidates[0]

        held_base_df,held_base=apply_portfolio(te,fn,0,payouts)
        held_df,held_port=apply_portfolio(te,fn,nsel,payouts)
        held_df["held_month"]=held;held_df["selected_rule"]=rule_name
        held_rows.append(held_df)
        fold_rows.append({
          "held_month":held,"selected_rule":rule_name,"selected_add_n":nsel,
          "train_second_baseline_hits":base_train,"train_second_rule_hits":second_train["hits"],
          "train_point_hits":train_port["hits"],"train_point_roi":train_port["roi"],
          "train_added_profit":train_added_profit,"train_added_tickets":train_port["added_tickets"],
          "held_R":len(te),"held_base_hits":held_base["hits"],"held_hits":held_port["hits"],
          "held_delta_hits":held_port["hits"]-held_base["hits"],
          "held_base_stake":held_base["stake"],"held_stake":held_port["stake"],
          "held_base_return":held_base["return"],"held_return":held_port["return"],
          "held_base_roi":held_base["roi"],"held_roi":held_port["roi"],
          "held_added_tickets":held_port["added_tickets"],
          "held_added_stake":held_port["added_stake"],"held_added_return":held_port["added_return"],
          "held_marginal_roi":held_port["marginal_roi"]
        })

    folds=pd.DataFrame(fold_rows);rows=pd.concat(held_rows,ignore_index=True)
    base_stake=sum(f["held_base_stake"] for f in fold_rows)
    base_ret=sum(f["held_base_return"] for f in fold_rows)
    stake=sum(f["held_stake"] for f in fold_rows);ret=sum(f["held_return"] for f in fold_rows)
    base_hits=sum(f["held_base_hits"] for f in fold_rows);hits=sum(f["held_hits"] for f in fold_rows)
    add_stake=stake-base_stake;add_ret=ret-base_ret
    result={
      "population":"DEV exact3 nested OOF: select 5-second rule by second accuracy, then add-N by train-only incremental profit",
      "baseline":{"R":len(q),"hits":base_hits,"stake":base_stake,"return":base_ret,"roi":base_ret/base_stake},
      "nested_dynamic":{"hits":hits,"hit_rate":hits/len(q),"delta_hits":hits-base_hits,
                        "stake":stake,"return":ret,"profit":ret-stake,"roi":ret/stake,
                        "delta_roi_pp":100*(ret/stake-base_ret/base_stake),
                        "added_stake":add_stake,"added_return":add_ret,
                        "marginal_roi":add_ret/add_stake if add_stake else None},
      "selected_n_counts":{str(k):int(v) for k,v in folds.selected_add_n.value_counts().sort_index().items()},
      "folds":fold_rows,
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False
    }
    folds.to_csv(OUT/"folds.csv",index=False);rows.to_csv(OUT/"held_rows.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_DYNAMIC_POINTS_V18",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
