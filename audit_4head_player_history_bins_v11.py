#!/usr/bin/env python3
"""Fixed-bin monthly diagnostic for b4 player-history strength. No tuning."""
import json
from pathlib import Path
import pandas as pd,numpy as np
BASE="/tmp/head4_v93_all_parent/v93_all_parent.csv"
BINS=[-1,.20,.25,.30,.35,.40,.45,.50,.60,2]
def main():
 z=pd.read_csv(BASE,dtype={"race_code":str});z.race_code=z.race_code.astype(str).str.zfill(12);z["month"]=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",usecols=["race_code","head4"],dtype={"race_code":str});t.race_code=t.race_code.astype(str).str.zfill(12)
 z=z.merge(t,on="race_code",how="left",validate="one_to_one");z=z[z.head4.isin([0,1])].copy()
 rows=[]
 for feat in ["b4_pl_all_p2","b4_pl_all_win","b4_pl_frame_p2","b4_pl_recent_p2"]:
  x=pd.to_numeric(z[feat],errors="coerce")
  for m,g in z.assign(_x=x).groupby("month"):
   q=g._x
   rows.append({"feature":feat,"month":m,"kind":"DIST","bin":"ALL","R":len(g),"head4":int(g.head4.sum()),"rate":float(g.head4.mean()),"mean":float(q.mean()),"median":float(q.median()),"q25":float(q.quantile(.25)),"q75":float(q.quantile(.75))})
   for lo,hi in zip(BINS[:-1],BINS[1:]):
    h=g[(g._x>=lo)&(g._x<hi)]
    if len(h): rows.append({"feature":feat,"month":m,"kind":"BIN","bin":f"{lo:.2f}_{hi:.2f}","R":len(h),"head4":int(h.head4.sum()),"rate":float(h.head4.mean()),"mean":float(h._x.mean()),"median":float(h._x.median())})
 # Focused conditional: all_p2 fixed bins crossed with BASE-selected population is intentionally omitted to avoid circular score effects.
 out=Path("/tmp/head4_player_history_bins_v11");out.mkdir(exist_ok=True)
 df=pd.DataFrame(rows);df.to_csv(out/"monthly_bins.csv",index=False)
 meta={"bins":BINS,"features":["b4_pl_all_p2","b4_pl_all_win","b4_pl_frame_p2","b4_pl_recent_p2"],"retuned":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (out/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
 print("ALL_P2\n"+df[df.feature=="b4_pl_all_p2"].to_string(index=False));print(json.dumps(meta));print("HEAD4_PLAYER_HISTORY_BINS_V11_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
