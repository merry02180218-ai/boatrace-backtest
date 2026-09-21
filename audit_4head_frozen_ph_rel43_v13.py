#!/usr/bin/env python3
"""v13: fixed frozen p>=.36 + ORIG>=-.06 candidate stratification by PLAYER_HISTORY x REL43. No tuning."""
import json,os
from pathlib import Path
import numpy as np,pandas as pd
import audit_4head_clean_6m_exhibition as exa
import audit_4head_waku10_rel43_regime_v6 as w10
OUT=Path("/tmp/head4_frozen_ph_rel43_v13");OUT.mkdir(exist_ok=True)
P2=[-1,.30,.40,.50,2];WR=[-2,-.10,0,.10,2]
def main():
 exa.main()
 b=pd.read_csv("/tmp/head4_clean_6m_exhibition/detail.csv",dtype={"race_code":str});b.race_code=b.race_code.astype(str).str.zfill(12)
 b=b[pd.to_numeric(b.p,errors="coerce").ge(.36)&b.ready.astype(str).str.lower().isin(["true","1"])&pd.to_numeric(b.orig4_adv_inside,errors="coerce").ge(-.06)].copy()
 p=pd.read_csv("/tmp/head4_v93_all_parent/v93_all_parent.csv",dtype={"race_code":str},usecols=["race_code","b4_pl_all_p2"]);p.race_code=p.race_code.astype(str).str.zfill(12)
 b=b.merge(p,on="race_code",how="left",validate="one_to_one")
 b=b.merge(w10.build_waku(b.race_code.tolist())[["race_code","w10_rel4_b3_wr","w10_rel4_b3_st","w10_rel4_b3_sr"]],on="race_code",how="left",validate="one_to_one")
 rows=[]
 for per,months in [("DEV_MAR_MAY",["2026-03","2026-04","2026-05"]),("VAL_JUN",["2026-06"]),("HOLD_JUL_AUG",["2026-07","2026-08"])]:
  g=b[b.month.isin(months)]
  rows.append({"period":per,"cell":"ALL_FROZEN","R":len(g),"head4":int(g.head4.sum()),"rate":float(g.head4.mean()) if len(g) else None})
  for plo,phi in zip(P2[:-1],P2[1:]):
   for wlo,whi in zip(WR[:-1],WR[1:]):
    h=g[(g.b4_pl_all_p2>=plo)&(g.b4_pl_all_p2<phi)&(g.w10_rel4_b3_wr>=wlo)&(g.w10_rel4_b3_wr<whi)]
    if len(h):rows.append({"period":per,"cell":f"P2[{plo:.2f},{phi:.2f})_WR[{wlo:.2f},{whi:.2f})","R":len(h),"head4":int(h.head4.sum()),"rate":float(h.head4.mean())})
 df=pd.DataFrame(rows);df.to_csv(OUT/"fixed_cells.csv",index=False);b.to_csv(OUT/"frozen_detail.csv",index=False)
 meta={"frozen_gate":"p>=.36 + ready + orig4_adv_inside>=-.06","bins_predeclared_from_v12":True,"retuned":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
 print(df.to_string(index=False));print(json.dumps(meta));print("HEAD4_FROZEN_PH_REL43_V13_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
