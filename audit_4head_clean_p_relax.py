#!/usr/bin/env python3
"""Expand clean 4HEAD volume by relaxing p with fixed ORIG gate.
No new thresholds are chosen from Jul-Aug: grid is reported by month/period.
September blocked; production unchanged.
"""
from __future__ import annotations
import os,sys,json
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_4head_clean_6m_exhibition as src
# Rebuild the same scored+exhibition dataset used by the verified audit by running it.
src.main()
# detail contains only p>=.36, so reproduce source script with a small safe transform:
# Read its module source inputs by monkey-patching the fixed baseline selection is not practical.
# Instead use headmodel scored output + exhibition builder.
import research_4head_clean_6m_headmodel as hm
hm.main(); z=pd.read_csv("/tmp/head4_clean_6m_headmodel/scored.csv",dtype={"race_code":str});z.race_code=z.race_code.str.zfill(12)
ef=src.ex.build_ex(set(z.race_code));ef["race_code"]=ef.race_code.astype(str).str.zfill(12);z=z.merge(ef,on="race_code",how="left")
z["orig_ok"]=pd.to_numeric(z.basic_complete,errors="coerce").fillna(0).eq(1)&pd.to_numeric(z.orig_avg_available,errors="coerce").fillna(0).eq(1)&pd.to_numeric(z.orig4_adv_inside,errors="coerce").ge(-.06)
cuts=[.36,.35,.34,.33,.32,.31,.30]
rec=[]
for cut in cuts:
 mask=z.orig_ok&z.p.ge(cut)
 for m in ["2026-03","2026-04","2026-05","2026-06","2026-07","2026-08"]:
  s=z[mask&(z.month==m)];rec.append({"p_cut":cut,"period":m,"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
 for name,months in [("DEV_MAR_MAY",{"2026-03","2026-04","2026-05"}),("VAL_JUN",{"2026-06"}),("HOLD_JUL_AUG",{"2026-07","2026-08"})]:
  s=z[mask&z.month.isin(months)];rec.append({"p_cut":cut,"period":name,"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
out={"orig_gate":-0.06,"p_grid":cuts,"records":rec,"grid_predeclared":True,"holdout_used_for_selection":False,"legacy_candidate_gate_used":False,"waku10_backfill_used":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
p=Path("/tmp/head4_clean_p_relax");p.mkdir(exist_ok=True);pd.DataFrame(rec).to_csv(p/"compare.csv",index=False);z.to_csv(p/"detail.csv",index=False);(p/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("P_RELAX_RESULT");print(pd.DataFrame(rec).to_string(index=False));print("HEAD4_CLEAN_P_RELAX_OK");print("SEPTEMBER_UNREAD")
