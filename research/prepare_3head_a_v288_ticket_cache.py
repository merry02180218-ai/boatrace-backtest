from __future__ import annotations
import argparse
import json
from pathlib import Path

import joblib

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",required=True,help="YYYY-MM-DD")
    ap.add_argument("--cache",required=True)
    ap.add_argument("--codes-json",default="research/3head_a_march_parity_codes.json")
    a=ap.parse_args()

    day8=a.date.replace("-","")
    spec=json.loads(Path(a.codes_json).read_text(encoding="utf-8"))
    codes=[str(x).zfill(12) for x in spec["race_codes"] if str(x).zfill(12).startswith(day8)]

    z=joblib.load(a.cache)
    if str(z.get("date"))!=day8:
        raise RuntimeError(f"cache date mismatch {z.get('date')} != {day8}")
    cur=z.get("current_rows")
    available=set(cur.race_code.astype(str).str.zfill(12)) if cur is not None else set()
    missing=[x for x in codes if x not in available]
    if missing:
        raise RuntimeError(f"A code missing from current rows: {missing}")

    z["original_v288_pre_candidates"]=z.get("pre_candidates",{})
    z["pre_candidates"]={
        code:{
            "pre_grade":"A_HEAD_GATE",
            "pre_score":None,
            "pre_pct":None,
            "pre_p3":None,
            "a_head_gate_frozen":True,
        }
        for code in codes
    }
    z["a_head_gate_ticket_audit"]=True
    z["a_head_gate_source_run"]=spec["source_run"]
    z["a_head_gate_source_marker"]=spec["marker"]
    joblib.dump(z,a.cache,compress=3)
    print(json.dumps({
        "date":a.date,
        "a_codes":codes,
        "count":len(codes),
        "target_result_or_payout_used":False,
    },ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
