#!/usr/bin/env python3
"""Clean 4HEAD six-month motor stability audit.
Reuses the frozen .36 card-model baseline, current exhibition ORIG>=-.06, and
chronological prior-only motor/player state. Jul-Aug is reporting only.
"""
from __future__ import annotations
import os,sys,json
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_4head_clean_long_dataset as ds
import research_4head_clean_6m_headmodel as hm
# Build long decision-time dataset to obtain prior-only motor state + exhibition.
os.environ["START_DATE"]="2026-03-01";os.environ["END_DATE"]="2026-08-31";os.environ["WARMUP_DATE"]="2025-10-01"
# execute builder, then read its frozen dataset
ds.START=pd.Timestamp("2026-03-01").date(); ds.END=pd.Timestamp("2026-08-31").date(); ds.WARMUP=pd.Timestamp("2025-10-01").date(); ds.main()
z=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",dtype={"race_code":str});z.race_code=z.race_code.str.zfill(12)
# get baseline scored rows from prior successful logic by invoking it
hm.main(); sc=pd.read_csv("/tmp/head4_clean_6m_headmodel/scored.csv",dtype={"race_code":str});sc.race_code=sc.race_code.str.zfill(12)
q=sc[sc.p>=.36][["race_code","p"]].merge(z,on="race_code",how="left",validate="one_to_one")
q["orig_ok"]=q.struct_ready.astype(bool)&pd.to_numeric(q.orig4_adv_inside,errors="coerce").ge(-.06)
WIN=-0.0299361318939513;REN2=-7.080000000000001;PLAYER=.215605
q["motor_current"]=pd.to_numeric(q.motor_win_diff_4v3,errors="coerce").ge(WIN)&pd.to_numeric(q.motor_2ren_diff_4v3,errors="coerce").ge(REN2)
q["pre_current"]=q.motor_current&pd.to_numeric(q.player4_all_win,errors="coerce").ge(PLAYER)
gates={"BASE":np.ones(len(q),bool),"ORIG_M006":q.orig_ok,"ORIG_M006_MOTOR":q.orig_ok&q.motor_current,"ORIG_M006_FULLPRE":q.orig_ok&q.pre_current}
rec=[]
for name,mask in gates.items():
 for m in ["2026-03","2026-04","2026-05","2026-06","2026-07","2026-08"]:
  s=q[mask&(q.month==m)];rec.append({"gate":name,"month":m,"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
 for per,months in [("DEV_MAR_MAY",{"2026-03","2026-04","2026-05"}),("VAL_JUN",{"2026-06"}),("HOLD_JUL_AUG",{"2026-07","2026-08"})]:
  s=q[mask&q.month.isin(months)];rec.append({"gate":name,"month":per,"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
out={"records":rec,"motor_thresholds_from_current_PRE":True,"holdout_used_for_tuning":False,"legacy_candidate_gate_used":False,"waku10_backfill_used":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
p=Path("/tmp/head4_clean_6m_motor");p.mkdir(exist_ok=True);pd.DataFrame(rec).to_csv(p/"compare.csv",index=False);q.to_csv(p/"detail.csv",index=False);(p/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("MOTOR_STABILITY_RESULT");print(pd.DataFrame(rec).to_string(index=False));print("HEAD4_CLEAN_6M_MOTOR_OK");print("SEPTEMBER_UNREAD")
