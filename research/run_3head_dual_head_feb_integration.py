#!/usr/bin/env python3
"""Frozen February integration audit for dual 3HEAD head models.
CORE=v288 operational semantics. EXPANDED=A+.60 frozen gate.
Head membership is frozen before settlement. September 2026 is never loaded.
This first integration pass measures head union and EXPANDED protected V221 exact-six capture.
CORE native ticket/staking ROI remains a separate downstream replay.
"""
from __future__ import annotations
import json, sys, pandas as pd
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_3head_v288_a60_overlap_strength as ov
import run_3head_a_opponent_feb_oneshot as opp

OUT=Path("research_3head_dual_head_feb_integration.json")

def main():
    v=ov.build_v288_codes()
    v=v[v.race_code.str[:8].between("20260201","20260228")].copy()
    a=ov.build_a60()
    a=a[a.race_code.str[:8].between("20260201","20260228")].copy()
    vc=set(v.race_code); ac=set(a.race_code)
    overlap=vc&ac
    if overlap:
        print("OVERLAP_CORE_PRIORITY",sorted(overlap),flush=True)
    # Rebuild the already-frozen EXPANDED opponent decisions before settlement.
    # Keep implementation identical to the frozen February one-shot.
    import analyze_v221_3head_scenario_pair as v221
    raw=pd.read_csv(v221.SRC,dtype={"race_code":str}); dc=v221.v165.pc(raw,["date","race_date","ymd"])
    raw["_date"]=pd.to_datetime(raw[dc].astype(str),errors="coerce")
    raw=raw[raw._date.notna()&(raw._date<pd.Timestamp("2026-03-01"))].copy()
    from datetime import date,timedelta
    v221.END=date(2026,2,28)
    d=v221.build(raw,dc); d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d["_date"]=pd.to_datetime(d.race_code.str[:8],format="%Y%m%d",errors="coerce")
    train=d[d._date<pd.Timestamp("2026-02-01")].copy()
    hist=[]; day=date(2025,10,1)
    while day<=date(2026,1,31):
        try:
            for rr in v221.rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"):
                code=str(rr.get("レースコード","")).zfill(12)
                aa=[str(rr.get(f"{i}着_艇番","")).strip() for i in (1,2,3)]
                if code.isdigit() and all(x in "123456" and len(x)==1 for x in aa):
                    hist.append({"race_code":code,"actual_combo":"-".join(aa),"valid_result":1})
        except Exception: pass
        day+=timedelta(days=1)
    hs=pd.DataFrame(hist).drop_duplicates("race_code")
    train=train.drop(columns=["actual_combo","valid_result"],errors="ignore").merge(hs,on="race_code",how="left",validate="many_to_one")
    direct,ntrain=v221.fit_pair(train,True)
    feb=d[(d._date>=pd.Timestamp("2026-02-01"))&(d._date<pd.Timestamp("2026-03-01"))&d.race_code.isin(ac)].copy()
    if len(feb)!=len(ac): raise RuntimeError(f"expanded feature coverage {len(feb)}/{len(ac)}")
    decisions={}
    for _,r in feb.iterrows():
        order=v221.order(r,direct,True); old=order[:6]; new=list(old)
        turn4=pd.to_numeric(pd.Series([v221.xtra(r,4,"vh_p12_turn")]),errors="coerce").iloc[0]
        promoted=dropped=None
        if pd.notna(turn4) and turn4>=opp.THRESHOLD:
            cand=[x for x in order if x.startswith("3-4-") and x not in old]
            drop_idx=[i for i,x in enumerate(new) if not x.startswith("3-4-")]
            if cand and drop_idx:
                promoted=cand[0]; di=drop_idx[-1]; dropped=new[di]; new[di]=promoted
        decisions[str(r.race_code)]={"tickets":new,"turn4":None if pd.isna(turn4) else float(turn4),"promoted":promoted,"dropped":dropped}
    # Membership/tickets are now frozen. Reveal February only.
    settled={}; day=date(2026,2,1)
    while day<=date(2026,2,28):
        try:
            for rr in v221.rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"):
                code=str(rr.get("レースコード","")).zfill(12)
                aa=[str(rr.get(f"{i}着_艇番","")).strip() for i in (1,2,3)]
                if code in (vc|ac) and all(x in "123456" and len(x)==1 for x in aa): settled[code]="-".join(aa)
        except Exception: pass
        day+=timedelta(days=1)
    def head(c): return settled.get(c,"").startswith("3-")
    exp_head=[c for c in ac if head(c)]
    exp_hit=[c for c in exp_head if settled[c] in decisions[c]["tickets"]]
    out={"policy":{"window":"2026-02","core":"v288 operational frozen","expanded":"A+.60 frozen + V221 Top6 + protected SECOND4 .50 exact-six","overlap":"CORE priority","threshold_tuning":False,"sep2026_used":False,"membership_frozen_before_settlement":True},
         "counts":{"core":len(vc),"expanded":len(ac),"overlap":len(overlap),"union":len(vc|ac)},
         "head":{"core_wins":sum(head(c) for c in vc),"expanded_wins":len(exp_head),"union_wins":sum(head(c) for c in vc|ac)},
         "expanded_opponent":{"head_wins":len(exp_head),"protected_six_hits":len(exp_hit),"capture":len(exp_hit)/len(exp_head) if exp_head else None,"swaps":sum(x["promoted"] is not None for x in decisions.values())},
         "note":"CORE native variable 5-10 ticket Dutch settlement is intentionally not approximated here; use exact native replay in next stage."}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+chr(10),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2)); print("DUAL_HEAD_FEB_INTEGRATION_OK")
if __name__=="__main__": main()
