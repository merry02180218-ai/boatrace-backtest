#!/usr/bin/env python3
"""Production restore audit: 4HEAD LIVE opponent tickets must equal frozen v291.

Uses the frozen PH5 163-bet replay output generated earlier in the same workflow.
No fitting or threshold selection is performed. September outcomes are not used.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

import run_4head_120r_lastminute_fast as live_fast
import run_4head_v291_third010_live as frozen_v291

ROOT=Path("/tmp/head4_ph5_live_walkforward")
OUT=Path("/tmp/head4_live_v291_restore_audit_v1"); OUT.mkdir(parents=True,exist_ok=True)
BOATS=(1,2,3,5,6)

def main():
    p=ROOT/"race_detail.csv"
    if not p.is_file():
        raise RuntimeError("MISSING_PH5_RACE_DETAIL")
    d=pd.read_csv(p,dtype={"race_code":str})
    d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.production_bet.eq(1)].copy()
    if len(d)!=163:
        raise RuntimeError(f"FROZEN_163_DRIFT_{len(d)}")

    rows=[]
    mismatch=[]
    for _,r in d.iterrows():
        diag=json.loads(r.opponent_diag)
        p2={int(k):float(v) for k,v in diag["p2"].items()}
        pc={(int(k.split(">")[0]),int(k.split(">")[1])):float(v) for k,v in diag["pc"].items()}

        expected=frozen_v291.production_tickets(p2,pc)
        actual=live_fast.production_tickets(p2,pc,None,None)
        stored=[x for x in str(r.tickets).split("|") if x]

        rec={
            "race_code":r.race_code,
            "month":str(r.date)[:7],
            "expected":"|".join(expected),
            "live":"|".join(actual),
            "stored":"|".join(stored),
            "expected_n":len(expected),
            "live_n":len(actual),
            "stored_n":len(stored),
            "live_equals_expected":int(actual==expected),
            "stored_equals_expected":int(stored==expected),
        }
        rows.append(rec)
        if actual!=expected or stored!=expected:
            mismatch.append(rec)

    z=pd.DataFrame(rows)
    z.to_csv(OUT/"parity_detail.csv",index=False)
    if mismatch:
        pd.DataFrame(mismatch).to_csv(OUT/"mismatch.csv",index=False)
        raise RuntimeError(f"V291_RESTORE_PARITY_MISMATCH_{len(mismatch)}")

    by_month=(z.groupby("month").agg(
        R=("race_code","size"),
        live_match=("live_equals_expected","sum"),
        stored_match=("stored_equals_expected","sum"),
        avg_points=("live_n","mean")
    ).reset_index())
    by_month.to_csv(OUT/"monthly.csv",index=False)

    meta={
        "R":int(len(z)),
        "live_matches_frozen_v291_R":int(z.live_equals_expected.sum()),
        "stored_matches_frozen_v291_R":int(z.stored_equals_expected.sum()),
        "policy":frozen_v291.POLICY,
        "SECOND_GAP":float(frozen_v291.SECOND_GAP),
        "THIRD_GAP":float(frozen_v291.THIRD_GAP),
        "PLAYERHistory_used_for_opponent_selection":False,
        "Waku10_used_for_opponent_selection":False,
        "September_outcomes_read":False,
        "PRODUCTION_CHANGED":True,
        "change":"restore frozen v291 opponent selector in run_4head_120r_lastminute_fast.py",
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    print("LIVE_V291_RESTORE_MONTHLY",by_month.to_json(orient="records",force_ascii=False))
    print("LIVE_V291_RESTORE_META",json.dumps(meta,ensure_ascii=False))
    print("LIVE_V291_RESTORE_PARITY_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":
    main()
