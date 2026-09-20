#!/usr/bin/env python3
"""Diagnose weak months for clean 4HEAD. Descriptive only; no holdout tuning."""
from pathlib import Path
import json,sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_4head_clean_long_dataset as ds
import research_4head_clean_6m_headmodel as hm

ds.START=pd.Timestamp("2026-03-01").date();ds.END=pd.Timestamp("2026-08-31").date();ds.WARMUP=pd.Timestamp("2025-10-01").date();ds.main()
z=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",dtype={"race_code":str});z.race_code=z.race_code.str.zfill(12)
hm.main();sc=pd.read_csv("/tmp/head4_clean_6m_headmodel/scored.csv",dtype={"race_code":str});sc.race_code=sc.race_code.str.zfill(12)
d=sc[["race_code","p"]].merge(z,on="race_code",how="left",validate="one_to_one")
base=d.p.ge(.36)&d.orig4_adv_inside.ge(-.06)
x=d[base].copy()
# venue is encoded in race_code positions 8:10 in this repo.
x["venue"]=x.race_code.str[8:10]
x["pband"]=pd.cut(x.p,[.36,.38,.40,.45,1.01],right=False,labels=["36_38","38_40","40_45","45p"])
x["origband"]=pd.cut(x.orig4_adv_inside,[-.06,0,.1,.2,.4,2],right=False,labels=["m06_0","0_10","10_20","20_40","40p"])
x["mwband"]=pd.cut(x.motor_win_diff_4v3,[-99,-.05,0,.05,.1,99],right=False,labels=["ltm05","m05_0","0_05","05_10","10p"])
x["m2band"]=pd.cut(x.motor_2ren_diff_4v3,[-999,-10,-5,0,5,10,999],right=False,labels=["ltm10","m10_m5","m5_0","0_5","5_10","10p"])
x["stband"]=pd.cut(x.st4_adv_inside,[-99,-.6,-.3,0,.3,99],right=False,labels=["ltm6","m6_m3","m3_0","0_3","3p"])
recs=[]
def add(dim):
 for (mo,v),s in x.groupby(["month",dim],observed=True):
  recs.append({"dimension":dim,"month":mo,"value":str(v),"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean())})
for dim in ["venue","pband","origband","mwband","m2band","stband"]:add(dim)
# May vs other pre-hold months effect table; descriptive, minimum support 5 in May.
may=x[x.month.eq("2026-05")]
other=x[x.month.isin(["2026-03","2026-04","2026-06"])]
effects=[]
for dim in ["venue","pband","origband","mwband","m2band","stband"]:
 vals=set(may[dim].dropna().astype(str))|set(other[dim].dropna().astype(str))
 for v in vals:
  a=may[may[dim].astype(str).eq(v)];b=other[other[dim].astype(str).eq(v)]
  if len(a)>=5 and len(b)>=5:
   effects.append({"dimension":dim,"value":v,"may_R":len(a),"may_H":int(a.head4.sum()),"may_rate":float(a.head4.mean()),"other_R":len(b),"other_H":int(b.head4.sum()),"other_rate":float(b.head4.mean()),"delta":float(a.head4.mean()-b.head4.mean())})
ef=pd.DataFrame(effects).sort_values(["delta","may_R"])
out=Path("/tmp/head4_clean_month_diagnosis");out.mkdir(exist_ok=True)
pd.DataFrame(recs).to_csv(out/"strata.csv",index=False);ef.to_csv(out/"may_effects.csv",index=False)
monthly=x.groupby("month").head4.agg(["size","sum","mean"]).reset_index().to_dict("records")
result={"monthly":monthly,"worst_may_effects":ef.head(20).to_dict("records"),"descriptive_only":True,"holdout_used_for_selection":False,"continuous_warmup_from":"2025-10-01","SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
(out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
print("MONTH_DIAG_RESULT");print(json.dumps(result,indent=2));print("SEPTEMBER_UNREAD")
