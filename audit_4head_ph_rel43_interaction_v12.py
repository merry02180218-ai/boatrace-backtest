#!/usr/bin/env python3
"""4HEAD v12 fixed interaction diagnostic: PLAYER_HISTORY x Waku10 REL43. No tuning."""
import json
from pathlib import Path
import numpy as np,pandas as pd
import audit_4head_waku10_rel43_regime_v6 as v6
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv")
OUT=Path("/tmp/head4_ph_rel43_interaction_v12");OUT.mkdir(exist_ok=True)
P2=[-1,.30,.40,.50,2]; WR=[-2,-.10,0,.10,2]; ST=[-2,-.01,0,.01,2]
def main():
 z=pd.read_csv(BASE,dtype={"race_code":str});z.race_code=z.race_code.astype(str).str.zfill(12);z["month"]=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",usecols=["race_code","head4"],dtype={"race_code":str});t.race_code=t.race_code.astype(str).str.zfill(12)
 z=z.merge(t,on="race_code",how="left",validate="one_to_one");z=z[z.head4.isin([0,1])].copy()
 z=z.merge(v6.build_waku(z.race_code.tolist()),on="race_code",how="left",validate="one_to_one")
 # Pure fixed interaction table. No fitted model, threshold search, odds or production changes.
 rows=[]
 for month,g in z.groupby("month"):
  for plo,phi in zip(P2[:-1],P2[1:]):
   for wlo,whi in zip(WR[:-1],WR[1:]):
    h=g[(g.b4_pl_all_p2>=plo)&(g.b4_pl_all_p2<phi)&(g.w10_rel4_b3_wr>=wlo)&(g.w10_rel4_b3_wr<whi)]
    if len(h): rows.append({"month":month,"p2_bin":f"{plo:.2f}_{phi:.2f}","rel43_wr_bin":f"{wlo:.2f}_{whi:.2f}","R":len(h),"head4":int(h.head4.sum()),"rate":float(h.head4.mean())})
 df=pd.DataFrame(rows);df.to_csv(OUT/"p2_x_rel43wr_monthly.csv",index=False)
 # Aggregate Mar-May vs Jun-Aug using identical fixed cells, descriptive only.
 z["period"]=np.where(z.month.isin(["2026-03","2026-04","2026-05"]),"MAR_MAY","JUN_AUG")
 agg=[]
 for per,g in z.groupby("period"):
  for plo,phi in zip(P2[:-1],P2[1:]):
   for wlo,whi in zip(WR[:-1],WR[1:]):
    h=g[(g.b4_pl_all_p2>=plo)&(g.b4_pl_all_p2<phi)&(g.w10_rel4_b3_wr>=wlo)&(g.w10_rel4_b3_wr<whi)]
    if len(h):agg.append({"period":per,"p2_bin":f"{plo:.2f}_{phi:.2f}","rel43_wr_bin":f"{wlo:.2f}_{whi:.2f}","R":len(h),"head4":int(h.head4.sum()),"rate":float(h.head4.mean())})
 ad=pd.DataFrame(agg);ad.to_csv(OUT/"p2_x_rel43wr_period.csv",index=False)
 meta={"p2_bins":P2,"rel43_wr_bins":WR,"retuned":False,"model_fit":False,"RESULT_FILES_USED_ONLY_AS_TARGET_AFTER_FEATURE_BUILD":True,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
 print("MONTHLY\n"+df.to_string(index=False));print("PERIOD\n"+ad.to_string(index=False));print(json.dumps(meta));print("HEAD4_PH_REL43_INTERACTION_V12_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
