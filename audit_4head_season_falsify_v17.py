#!/usr/bin/env python3
"""v17: fixed seasonal falsification. No threshold tuning. Tests Jul-Aug within water bands and 2025 environment coverage."""
import csv,json,os
from pathlib import Path
import pandas as pd
import audit_4head_env_waku_v16 as v16
OUT=Path("/tmp/head4_season_falsify_v17");OUT.mkdir(exist_ok=True);ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
def main():
 v16.main();z=pd.read_csv("/tmp/head4_env_waku_v16/detail.csv",dtype={"race_code":str});z.race_code=z.race_code.str.zfill(12)
 z["water_band"]=pd.cut(pd.to_numeric(z.water_c,errors="coerce"),[-99,25,30,99],right=False,labels=["<25","25-30","30+"])
 rec=[]
 for scope,g in [("ALL",z),("JUL_AUG",z[z.month.isin(["2026-07","2026-08"])])]:
  for wb,h in g.groupby("water_band",observed=True):
   rec.append({"scope":scope,"water_band":str(wb),"split":"BASE","R":len(h),"H":int(h.head4.sum()),"rate":float(h.head4.mean())})
   for c in ["w10_rel4_b3_sr","w10_rel4_b3_st"]:
    # fixed zero sign split, not data-tuned median
    x=pd.to_numeric(h[c],errors="coerce")
    for side,m in [("LE0",x<=0),("GT0",x>0)]:
     q=h[m];rec.append({"scope":scope,"water_band":str(wb),"split":c+"_"+side,"R":len(q),"H":int(q.head4.sum()),"rate":float(q.head4.mean()) if len(q) else None})
 pd.DataFrame(rec).to_csv(OUT/"within_season_water.csv",index=False)
 # Venue descriptive table, only cells >=5.
 vr=[]
 for (wb,ve),g in z[z.month.isin(["2026-07","2026-08"])].groupby(["water_band","venue_code"],observed=True):
  if len(g)>=5:vr.append({"water_band":str(wb),"venue_code":ve,"R":len(g),"H":int(g.head4.sum()),"rate":float(g.head4.mean())})
 pd.DataFrame(vr).to_csv(OUT/"julaug_water_venue.csv",index=False)
 # Independent prior-year environmental coverage only; outcomes intentionally not analyzed here.
 cov=[]
 for m in [7,8]:
  for d in range(1,32):
   p=ROOT/f"data/results/realtime/2025/{m:02d}/{d:02d}.csv"
   if not p.is_file():continue
   with p.open(encoding="utf-8-sig",newline="") as f:
    rr=list(csv.DictReader(f))
   vals=pd.to_numeric(pd.Series([r.get("水温(℃)") for r in rr]),errors="coerce")
   cov.append({"month":m,"day":d,"rows":len(rr),"water_n":int(vals.notna().sum()),"water_mean":float(vals.mean()) if vals.notna().any() else None})
 pd.DataFrame(cov).to_csv(OUT/"prior_year_env_coverage.csv",index=False)
 meta={"fixed_water_bands":["<25","25-30","30+"],"fixed_sr_st_split":"zero sign","jul_aug_within_season_test":True,"prior_year_outcomes_analyzed":False,"threshold_tuning":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n");print(pd.DataFrame(rec).to_string(index=False));print(pd.DataFrame(vr).to_string(index=False));print(pd.DataFrame(cov).groupby("month").agg(days=("day","count"),rows=("rows","sum"),water_n=("water_n","sum"),water_mean=("water_mean","mean")).to_string());print(json.dumps(meta));print("HEAD4_SEASON_FALSIFY_V17_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
