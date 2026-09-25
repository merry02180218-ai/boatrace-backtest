#!/usr/bin/env python3
"""Result-blind all-race PH5 replay for Sep 23-25, 2026.

Purpose: test whether the legacy monitoring_parent upstream gate hides races that
would satisfy the formally adopted PH5 final gate. Target-day outcomes/payouts and
odds are never read.
"""
from __future__ import annotations
import csv,json,os
from pathlib import Path
import pandas as pd

import run_4head_120r_lastminute_fast as fast
import run_v326_1head_ticketaware_exhibition as v326
from backtest_v51_lane_corrected_tickets import corrected_direct
from build_4head_v283_current_exhibition_live import _rank_strength
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import rank_scores

ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
DAYS=("20260923","20260924","20260925")

def rows(rel):
    p=ROOT/rel
    if not p.is_file(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def rc(x):
    s=str(x or "").strip()
    if s.endswith(".0"):s=s[:-2]
    return s.zfill(12)

def bycode(rs): return {rc(r.get("レースコード","")):r for r in rs if r.get("レースコード")}

def archived_exhibition(code,state):
    ds=f"{code[:4]}/{code[4:6]}/{code[6:8]}"
    tk=bycode(rows(f"data/previews/tkz/{ds}.csv"))
    st=bycode(rows(f"data/previews/stt/{ds}.csv"))
    og=bycode(rows(f"data/previews/original_exhibition/{ds}.csv"))
    if code not in tk or code not in st: raise RuntimeError("ARCHIVED_BASIC_EXHIBITION_MISSING")
    audit=v326.raw_completeness(tk.get(code,{}),st.get(code,{}),og.get(code,{}))
    if not audit["tkz_all6"] or not audit["stt_all6"]: raise RuntimeError("ARCHIVED_BASIC_EXHIBITION_INCOMPLETE")
    bias={int(k):float(v) for k,v in (state.get("st_bias") or {}).items()}
    exv,stv,osv=corrected_direct(code,tk,st,og,bias)
    st_raw={b:float(st[code][f"艇{b}_スタート展示"]) for b in range(1,7)}
    st_corr={b:st_raw[b]-bias.get(b,0.0) for b in range(1,7)}
    rr,rs=_rank_strength(st_raw); cr,cs=_rank_strength(st_corr)
    boats={}; sf={}
    for b in range(1,7):
        o=osv[b]
        boats[str(b)]={
          "cur_ex":float(exv[b]),"cur_st":float(cs[b]),
          "cur_orig_lap":float(o.get("lap",.5)),"cur_orig_turn":float(o.get("turn",.5)),
          "cur_orig_straight":float(o.get("straight",.5)),"cur_orig_avg":float(o.get("avg",.5)),
        }
        sf[f"st_raw_b{b}"]=st_raw[b]; sf[f"st_raw_rank_b{b}"]=rr[b]; sf[f"st_corr_rank_b{b}"]=cr[b]
        sf[f"st_raw_strength_b{b}"]=round(rs[b],4); sf[f"st_corr_strength_b{b}"]=round(cs[b],4)
    return {
      "schema":"head4_allrace_archived_exhibition_v1","race_code":code,
      "current_boats":boats,"st_flat":sf,
      "orig_avg_available":bool(audit["orig_avg_all6"]),
      "orig_turn_available":bool(audit["orig_turn_all6"]),
      "orig_straight_available":bool(audit["orig_straight_all6"]),
      "wall_exhibition_ready":bool(audit["orig_avg_all6"] and audit["orig_straight_all6"]),
      "result_blind":True,"odds_used":False,
    }

def load_day(day,seed):
    cards=fast.bycode(fast.rows_local(seed/"race_cards.csv"))
    waku=fast.bycode(fast.rows_local(seed/"waku10.csv"))
    state=json.loads((seed/"head4_daily_state.json").read_text(encoding="utf-8"))
    pre=pd.read_csv(seed/"pre_all.csv",dtype={"race_code":str})
    pre["race_code"]=pre.race_code.astype(str).str.zfill(12)
    pmap={r.race_code:r for _,r in pre.iterrows()}
    out=[]
    for code,card in cards.items():
        if not code.startswith(day) or code not in waku: continue
        rec={"date":day,"race_code":code,"monitoring_parent":int(getattr(pmap.get(code), "monitoring_parent",0)) if code in pmap else 0}
        try:
            exh=archived_exhibition(code,state)
            pf=fast.player_flat(card,state)
            hp=fast.ph5_head_prob_live(card,waku[code],exh,pf)
            sadv=fast.structural_advantages(exh)
            orig=sadv["orig4_adv_inside"]
            sel=bool(hp>=.36 and orig is not None and orig>=-.06)
            rec.update(status="OK",head_prob=float(hp),orig4_adv_inside=orig,ph5_selected=int(sel),
                       orig_avg_available=int(bool(exh.get("orig_avg_available"))))
        except Exception as e:
            rec.update(status="NOT_READY",head_prob=None,orig4_adv_inside=None,ph5_selected=0,
                       orig_avg_available=0,error=f"{type(e).__name__}: {e}")
        out.append(rec)
    return out

def main():
    allrows=[]
    for day in DAYS:
        seed=Path(os.environ[f"SEED_{day}"])
        allrows.extend(load_day(day,seed))
    d=pd.DataFrame(allrows)
    out={"profile":"HEAD4_PH5_ALLRACE_PARENT_COVERAGE_SEP23_25","result_or_payout_used":False,"odds_used":False,"by_day":{}}
    for day,g in d.groupby("date"):
        s=g[g.ph5_selected.eq(1)]
        missed=s[s.monitoring_parent.eq(0)]
        out["by_day"][day]={
          "all_card_R":int(len(g)),"scored_OK_R":int(g.status.eq("OK").sum()),
          "ph5_selected_R":int(len(s)),"selected_inside_parent_R":int(s.monitoring_parent.eq(1).sum()),
          "selected_outside_parent_R":int(len(missed)),
          "selected_outside_parent_codes":missed.race_code.tolist(),
          "max_head_prob":float(pd.to_numeric(g.head_prob,errors="coerce").max()) if g.head_prob.notna().any() else None,
        }
    s=d[d.ph5_selected.eq(1)]; missed=s[s.monitoring_parent.eq(0)]
    out["total"]={
      "all_card_R":int(len(d)),"scored_OK_R":int(d.status.eq("OK").sum()),"ph5_selected_R":int(len(s)),
      "selected_inside_parent_R":int(s.monitoring_parent.eq(1).sum()),
      "selected_outside_parent_R":int(len(missed)),
      "selected_outside_parent_codes":missed.race_code.tolist(),
    }
    od=Path("/tmp/head4_ph5_allrace_sep23_25");od.mkdir(parents=True,exist_ok=True)
    d.to_csv(od/"detail.csv",index=False)
    (od/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print("HEAD4_PH5_ALLRACE_PARENT_COVERAGE_OK")
    print("TARGET_DAY_RESULTS_UNREAD")

if __name__=="__main__": main()
