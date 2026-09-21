#!/usr/bin/env python3
"""v15: predeclared Waku10 SR/ST validation inside frozen candidates + month/venue diagnostics. No retuning on Jun-Aug."""
import json
from pathlib import Path
import numpy as np,pandas as pd
import audit_4head_frozen_ph_rel43_v13 as v13
OUT=Path("/tmp/head4_waku_sr_st_v15");OUT.mkdir(exist_ok=True)
def rate(g): return {"R":len(g),"H":int(g.head4.sum()),"rate":float(g.head4.mean()) if len(g) else None}
def main():
 v13.main();z=pd.read_csv("/tmp/head4_frozen_ph_rel43_v13/frozen_detail.csv",dtype={"race_code":str});z.race_code=z.race_code.str.zfill(12)
 w=v13.w10.build_waku(z.race_code.tolist());keep=["race_code","w10_b4_sr","w10_rel4_b1_sr","w10_rel4_b3_sr","w10_rel4_inside_min_sr","w10_rel4_b1_st","w10_rel4_b3_st"]
 z=z.merge(w[keep],on="race_code",how="left",validate="one_to_one",suffixes=("","_new"))
 # Fixed candidate rules chosen only from DEV Mar-May medians/directions, then frozen.
 dev=z[z.month.isin(["2026-03","2026-04","2026-05"])]
 dirs={"w10_b4_sr":-1,"w10_rel4_b1_sr":1,"w10_rel4_b3_sr":1,"w10_rel4_inside_min_sr":1,"w10_rel4_b1_st":-1,"w10_rel4_b3_st":1}
 cuts={c:float(pd.to_numeric(dev[c],errors="coerce").median()) for c in dirs}
 rules={"BASE":np.ones(len(z),bool)}
 for c,d in dirs.items():
  x=pd.to_numeric(z[c],errors="coerce");rules[c]=x.le(cuts[c]) if d<0 else x.ge(cuts[c])
 # simple consensus: number of six DEV-fixed favorable conditions
 score=sum(m.astype(int) for k,m in rules.items() if k!="BASE");rules["CONSENSUS_4OF6"]=score.ge(4);rules["CONSENSUS_5OF6"]=score.ge(5)
 rec=[]
 periods={"DEV_MAR_MAY":["2026-03","2026-04","2026-05"],"VAL_JUN":["2026-06"],"HOLD_JUL_AUG":["2026-07","2026-08"]}
 for rn,m in rules.items():
  for per,months in periods.items():rec.append({"rule":rn,"period":per,**rate(z[m&z.month.isin(months)])})
 pd.DataFrame(rec).to_csv(OUT/"fixed_rule_validation.csv",index=False)
 # Descriptive month and venue stability; no rule selection from these outputs.
 diag=[]
 for (mo,ve),g in z.groupby(["month","venue_code"]):
  if len(g)>=5:diag.append({"month":mo,"venue_code":ve,**rate(g)})
 pd.DataFrame(diag).to_csv(OUT/"month_venue.csv",index=False)
 meta={"dev_fixed_cuts":cuts,"directions":dirs,"selection_data":"DEV_MAR_MAY only","jun_aug_used_for_rule_selection":False,"temperature_water_data_used":False,"season_hypothesis_tested_indirectly_by_month_venue":True,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
 print(pd.DataFrame(rec).to_string(index=False));print(json.dumps(meta));print("HEAD4_WAKU_SR_ST_V15_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
