#!/usr/bin/env python3
"""v22: fixed August matching controlling p, PLAYER_HISTORY, SR/ST magnitude and venue. No tuning."""
import json
from pathlib import Path
import pandas as pd
import audit_4head_env_waku_v16 as v16
OUT=Path("/tmp/head4_aug_match_full_v22"); OUT.mkdir(exist_ok=True)

def main():
 v16.main()
 z=pd.read_csv("/tmp/head4_env_waku_v16/detail.csv",dtype={"race_code":str})
 cols=["water_c","p","b4_pl_all_p2","w10_rel4_b3_sr","w10_rel4_b3_st"]
 for c in cols:z[c]=pd.to_numeric(z[c],errors="coerce")
 z["GE30"]=z.water_c>=30;z["BOTH"]=(z.w10_rel4_b3_sr>0)&(z.w10_rel4_b3_st>0)
 dev=z[z.month.isin(["2026-03","2026-04","2026-05"])].copy()
 aug=z[(z.month=="2026-08")&z.BOTH&z.water_c.notna()].copy()
 controls=["p","b4_pl_all_p2","w10_rel4_b3_sr","w10_rel4_b3_st"]
 mus={c:float(dev[c].mean()) for c in controls}; sds={c:(float(dev[c].std()) or 1.0) for c in controls}
 tr=aug[aug.GE30].copy();co=aug[~aug.GE30].copy()

 def match(require_same_venue):
  pairs=[]
  for _,r in tr.iterrows():
   pool=co[co.venue_code==r.venue_code] if require_same_venue else co
   if pool.empty:continue
   d=sum(((pool[c]-r[c])/sds[c])**2 for c in controls)
   d=d.dropna()
   if d.empty:continue
   j=d.idxmin();q=pool.loc[j]
   pairs.append({"treated_race":r.race_code,"control_race":q.race_code,"venue_code":r.venue_code,
    "distance":float(d.loc[j]**0.5),"treated_H":int(r.head4),"control_H":int(q.head4),
    **{f"treated_{c}":float(r[c]) for c in controls},**{f"control_{c}":float(q[c]) for c in controls}})
  return pd.DataFrame(pairs)

 summaries=[]
 for name,same in [("FULL4",False),("FULL4_SAME_VENUE",True)]:
  p=match(same);p.to_csv(OUT/(name.lower()+"_pairs.csv"),index=False)
  summaries.append({"match":name,"pairs":len(p),"treated_unique":int(p.treated_race.nunique()) if len(p) else 0,
   "control_unique":int(p.control_race.nunique()) if len(p) else 0,
   "GE30_rate":float(p.treated_H.mean()) if len(p) else None,"LT30_rate":float(p.control_H.mean()) if len(p) else None,
   "diff":float((p.treated_H-p.control_H).mean()) if len(p) else None,
   "median_distance":float(p.distance.median()) if len(p) else None,"max_distance":float(p.distance.max()) if len(p) else None})
 pd.DataFrame(summaries).to_csv(OUT/"matching_summary.csv",index=False)

 # Leave-one-venue-out on the fixed FULL4 matching to detect venue dependence.
 loo=[]
 for ve in sorted(aug.venue_code.dropna().unique()):
  aa=aug[aug.venue_code!=ve];tt=aa[aa.GE30];cc=aa[~aa.GE30];pairs=[]
  for _,r in tt.iterrows():
   if cc.empty:continue
   d=sum(((cc[c]-r[c])/sds[c])**2 for c in controls);d=d.dropna()
   if d.empty:continue
   q=cc.loc[d.idxmin()];pairs.append((int(r.head4),int(q.head4),float(d.min()**0.5)))
  if pairs:
   loo.append({"left_out_venue":ve,"pairs":len(pairs),"GE30_rate":sum(x[0] for x in pairs)/len(pairs),"LT30_rate":sum(x[1] for x in pairs)/len(pairs),"diff":sum(x[0]-x[1] for x in pairs)/len(pairs),"median_distance":float(pd.Series([x[2] for x in pairs]).median())})
 pd.DataFrame(loo).to_csv(OUT/"leave_one_venue_out.csv",index=False)
 meta={"month":"2026-08","water_cut_c":30,"signal":"rel4_b3_sr>0 AND rel4_b3_st>0","controls":controls,
 "scaling":"Mar-May mean/sd only","matching":"nearest LT30 with replacement; outcome-blind","same_venue_sensitivity":True,"leave_one_venue_out":True,
 "threshold_tuning":False,"model_refit":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
 print(pd.DataFrame(summaries).to_string(index=False));print(pd.DataFrame(loo).to_string(index=False));print(json.dumps(meta));print("HEAD4_AUG_MATCH_FULL_V22_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
