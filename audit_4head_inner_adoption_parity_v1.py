#!/usr/bin/env python3
"""Audit the comparator used to adopt INNER_SURVIVE.

This audit proves whether the research 'baseline' reproduced frozen v291 production.
Key distinction:
- production v291 SECOND rescue uses raw p2 rank2-rank3 gap <= .11;
- the old research baseline used logit(p2) gap <= .11.

No production mutation. September outcomes unread.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import pandas as pd

import audit_4head_ph5_live_walkforward as parent
import research_4head_player_waku_soft_ablation_v23 as phsrc
import research_4head_waku10_rel43_v4 as wsrc
import run_4head_120r_lastminute_fast as inner

OUT=Path("/tmp/head4_inner_adoption_parity_v1"); OUT.mkdir(parents=True,exist_ok=True)
BASE=Path("/tmp/head4_ph5_live_walkforward/race_detail.csv")
BOATS=(1,2,3,5,6)
SECOND_GAP=.11
THIRD_GAP=.18

def logit(p):
    p=min(max(float(p),1e-6),1-1e-6)
    return math.log(p/(1-p))

def tickets(diag, gap_mode):
    p2={int(k):float(v) for k,v in diag["p2"].items()}
    pc={(int(k.split(">")[0]),int(k.split(">")[1])):float(v) for k,v in diag["pc"].items()}
    rank=sorted(BOATS,key=lambda b:(-p2[b],b))
    secs=rank[:2]
    if gap_mode=="raw_p2":
        gap=p2[rank[1]]-p2[rank[2]]
    elif gap_mode=="logit_p2":
        gap=logit(p2[rank[1]])-logit(p2[rank[2]])
    else:
        raise ValueError(gap_mode)
    if gap<=SECOND_GAP: secs=secs+[rank[2]]
    out=[]
    for s in secs:
        thirds=sorted((t for t in BOATS if t!=s),key=lambda t:(-pc[(s,t)],t))
        for t in thirds[:2]:
            x=f"4-{s}-{t}"
            if x not in out: out.append(x)
        if pc[(s,thirds[1])]-pc[(s,thirds[2])]<=THIRD_GAP:
            x=f"4-{s}-{thirds[2]}"
            if x not in out: out.append(x)
    return out

def main():
    d=pd.read_csv(BASE,dtype={"race_code":str}); d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.production_bet.eq(1)].copy()
    if len(d)!=163: raise RuntimeError(f"FROZEN_163_DRIFT_{len(d)}")

    ph=phsrc.build_ph(); ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
    w=wsrc.build_waku(d.race_code.tolist()); w["race_code"]=w.race_code.astype(str).str.zfill(12)
    q=d.merge(ph,on="race_code",how="left",validate="one_to_one").merge(w,on="race_code",how="left",validate="one_to_one")

    frozen=[]
    parity_mismatch=[]
    for _,r in q.iterrows():
        diag=json.loads(r.opponent_diag)
        prod=[x for x in str(r.tickets).split("|") if x]
        raw=tickets(diag,"raw_p2")
        bug=tickets(diag,"logit_p2")
        if set(raw)!=set(prod):
            parity_mismatch.append({"race_code":r.race_code,"stored":"|".join(prod),"raw":"|".join(raw)})
        p2={int(k):float(v) for k,v in diag["p2"].items()}
        pc={(int(k.split(">")[0]),int(k.split(">")[1])):float(v) for k,v in diag["pc"].items()}
        pflat={f"b{b}_pl_frame_p2":r.get(f"b{b}_pl_frame_p2") for b in BOATS}
        waku={k:r.get(k) for k in r.index if str(k).startswith("w10_")}
        inn=inner.production_tickets(p2,pc,pflat=pflat,waku=waku)
        frozen.append({"race_code":r.race_code,"date":r.date,"month":str(r.date)[:7],
                       "stored_v291":"|".join(prod),"correct_raw_baseline":"|".join(raw),
                       "buggy_logit_baseline":"|".join(bug),"inner_survive":"|".join(inn),
                       "stored_n":len(prod),"raw_n":len(raw),"bug_n":len(bug),"inner_n":len(inn),
                       "bug_matches_stored":int(set(bug)==set(prod)),
                       "raw_matches_stored":int(set(raw)==set(prod))})
    f=pd.DataFrame(frozen)
    f.to_csv(OUT/"frozen_ticket_parity.csv",index=False)
    if parity_mismatch:
        pd.DataFrame(parity_mismatch).to_csv(OUT/"raw_parity_mismatch.csv",index=False)
        raise RuntimeError(f"RAW_P2_BASELINE_NOT_PRODUCTION_PARITY_{len(parity_mismatch)}")

    # Only after all ticket variants are frozen attach outcomes.
    tr=parent.truth()
    rows=[]
    for _,r in f.iterrows():
        a=tr.get(r.race_code)
        if not a or a[0]!=4: continue
        actual=f"4-{a[1]}-{a[2]}"
        for name,col in [("STORED_V291","stored_v291"),("CORRECT_RAW_BASELINE","correct_raw_baseline"),
                         ("BUGGY_LOGIT_BASELINE","buggy_logit_baseline"),("INNER_SURVIVE","inner_survive")]:
            ts=[x for x in str(r[col]).split("|") if x]
            rows.append({"race_code":r.race_code,"month":r.month,"variant":name,
                         "hit":int(actual in ts),"ticket_count":len(ts),"actual":actual})
    e=pd.DataFrame(rows); e.to_csv(OUT/"head4_capture_detail.csv",index=False)
    monthly=e.groupby(["variant","month"]).agg(R=("race_code","size"),capture=("hit","sum"),avg_points=("ticket_count","mean")).reset_index()
    total=e.groupby("variant").agg(R=("race_code","size"),capture=("hit","sum"),avg_points=("ticket_count","mean")).reset_index()
    monthly.to_csv(OUT/"monthly.csv",index=False); total.to_csv(OUT/"total.csv",index=False)

    meta={"frozen_bet_R":163,"head4_R":int(e.race_code.nunique()),
          "raw_p2_baseline_matches_stored_v291_all_163":True,
          "buggy_logit_baseline_match_R":int(f.bug_matches_stored.sum()),
          "buggy_logit_baseline_mismatch_R":int((1-f.bug_matches_stored).sum()),
          "finding":"old research baseline applied SECOND_GAP=.11 in logit space, not raw p2 space",
          "SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("INNER_ADOPTION_PARITY_TOTAL",total.to_json(orient="records",force_ascii=False))
    print("INNER_ADOPTION_PARITY_MONTHLY",monthly.to_json(orient="records",force_ascii=False))
    print("INNER_ADOPTION_PARITY_META",json.dumps(meta,ensure_ascii=False))
    print("INNER_ADOPTION_PARITY_V1_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":
    main()
