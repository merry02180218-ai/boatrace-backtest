#!/usr/bin/env python3
"""v16: descriptive environment x Waku SR/ST audit in frozen candidates. Result CSV env columns only; no threshold tuning."""
import csv,json,os
from pathlib import Path
import numpy as np,pandas as pd
import audit_4head_waku_sr_st_v15 as v15
OUT=Path("/tmp/head4_env_waku_v16");OUT.mkdir(exist_ok=True);ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
def rows(p):
 q=ROOT/p
 if not q.is_file():return []
 with q.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
 v15.main();z=pd.read_csv("/tmp/head4_frozen_ph_rel43_v13/frozen_detail.csv",dtype={"race_code":str});z.race_code=z.race_code.str.zfill(12)
 w=v15.v13.w10.build_waku(z.race_code.tolist());cols=["race_code","w10_b4_sr","w10_rel4_b1_sr","w10_rel4_b3_sr","w10_rel4_b3_st"];z=z.merge(w[cols],on="race_code",how="left",validate="one_to_one",suffixes=("","_new"))
 # Strict whitelist: copy ONLY environmental columns from result rows; no finish/ST/kimarite fields enter features.
 env=[]
 for d in sorted(z.date.unique()):
  y=str(d).replace("-","/"); 
  for r in rows(f"data/results/realtime/{y}.csv"):
   code=str(r.get("レースコード","")).split(".")[0].zfill(12)
   if code in set(z.race_code):
    env.append({"race_code":code,"weather":r.get("天候"),"wind_dir":r.get("風向"),"wind_m":r.get("風速(m)"),"wave_cm":r.get("波の高さ(cm)"),"air_c":r.get("気温(℃)"),"water_c":r.get("水温(℃)")})
 e=pd.DataFrame(env).drop_duplicates("race_code");z=z.merge(e,on="race_code",how="left",validate="one_to_one")
 for c in ["wind_m","wave_cm","air_c","water_c"]:z[c]=pd.to_numeric(z[c],errors="coerce")
 z["water_bin"]=pd.cut(z.water_c,[-99,20,25,30,99],right=False,labels=["<20","20-25","25-30","30+"])
 z["air_bin"]=pd.cut(z.air_c,[-99,20,25,30,99],right=False,labels=["<20","20-25","25-30","30+"])
 rec=[]
 for typ in ["water_bin","air_bin"]:
  for b,g in z.groupby(typ,observed=True):
   rec.append({"axis":typ,"bin":str(b),"R":len(g),"H":int(g.head4.sum()),"rate":float(g.head4.mean()),"water_mean":float(g.water_c.mean()),"air_mean":float(g.air_c.mean())})
   for c in ["w10_rel4_b3_sr","w10_rel4_b3_st"]:
    med=float(pd.to_numeric(g[c],errors="coerce").median())
    for side,m in [("LOW",pd.to_numeric(g[c],errors="coerce")<med),("HIGH",pd.to_numeric(g[c],errors="coerce")>=med)]:
     h=g[m];rec.append({"axis":typ,"bin":f"{b}|{c}|{side}","R":len(h),"H":int(h.head4.sum()),"rate":float(h.head4.mean()) if len(h) else None,"water_mean":float(h.water_c.mean()) if len(h) else None,"air_mean":float(h.air_c.mean()) if len(h) else None})
 pd.DataFrame(rec).to_csv(OUT/"environment_interactions.csv",index=False);z.to_csv(OUT/"detail.csv",index=False)
 monthly=z.groupby("month").agg(R=("head4","size"),H=("head4","sum"),water_mean=("water_c","mean"),air_mean=("air_c","mean"),wind_mean=("wind_m","mean"),wave_mean=("wave_cm","mean")).reset_index();monthly["rate"]=monthly.H/monthly.R;monthly.to_csv(OUT/"monthly_env.csv",index=False)
 meta={"environment_source":"BoatraceCSV realtime result rows","environment_whitelist":["天候","風向","風速(m)","波の高さ(cm)","気温(℃)","水温(℃)"],"result_fields_used_as_features":False,"descriptive_only":True,"threshold_tuning":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n");print(monthly.to_string(index=False));print(pd.DataFrame(rec).to_string(index=False));print(json.dumps(meta,ensure_ascii=False));print("HEAD4_ENV_WAKU_V16_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
