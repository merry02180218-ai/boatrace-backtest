#!/usr/bin/env python3
"""Analyze rescue quality for 0.32<=p<0.36 without touching production.
Reports predeclared 4-vs-3 motor and exhibition strata; no Jul-Aug threshold selection.
"""
from pathlib import Path
import json,sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_4head_clean_6m_motor_stability as ms
# build canonical prior-only motor dataset and scored/exhibition inputs
ms.main()
d=pd.read_csv("/tmp/head4_clean_6m_motor/detail.csv",dtype={"race_code":str})
# normalize likely merged names
def col(*xs):
 for x in xs:
  if x in d.columns:return x
 raise KeyError(xs)
pcol=col("p")
ocol=col("orig4_adv_inside")
mw=col("motor_win_diff_4v3")
m2=col("motor_2ren_diff_4v3")
st=col("st4_adv_inside")
d["band"]=pd.cut(d[pcol],[-1,.32,.33,.34,.35,.36,2],right=False,labels=["lt32","32_33","33_34","34_35","35_36","ge36"])
base=d[pcol].ge(.36)&d[ocol].ge(-.06)
low=d[pcol].ge(.32)&d[pcol].lt(.36)&d[ocol].ge(-.06)
gates={
"LOW_ALL":low,
"LOW_MOTOR_WIN":low&d[mw].ge(-0.0299361318939513),
"LOW_MOTOR_2REN":low&d[m2].ge(-7.08),
"LOW_MOTOR_BOTH":low&d[mw].ge(-0.0299361318939513)&d[m2].ge(-7.08),
"LOW_ST_M060":low&d[st].ge(-.60),
"LOW_MOTOR_BOTH_ST":low&d[mw].ge(-0.0299361318939513)&d[m2].ge(-7.08)&d[st].ge(-.60),
}
rec=[]
for name,mask in {"BASE_GE36":base,**gates}.items():
 for per,months in [("MAR",["2026-03"]),("APR",["2026-04"]),("MAY",["2026-05"]),("JUN",["2026-06"]),("JUL",["2026-07"]),("AUG",["2026-08"]),("DEV_MAR_MAY",["2026-03","2026-04","2026-05"]),("VAL_JUN",["2026-06"]),("HOLD_JUL_AUG",["2026-07","2026-08"])]:
  s=d[mask&d.month.isin(months)];rec.append({"gate":name,"period":per,"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
# combined base+rescue
for name,mask in gates.items():
 cm=base|mask
 for per,months in [("DEV_MAR_MAY",["2026-03","2026-04","2026-05"]),("VAL_JUN",["2026-06"]),("HOLD_JUL_AUG",["2026-07","2026-08"])]:
  s=d[cm&d.month.isin(months)];rec.append({"gate":"BASE_PLUS_"+name,"period":per,"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
out=Path("/tmp/head4_clean_lowp_rescue");out.mkdir(exist_ok=True);pd.DataFrame(rec).to_csv(out/"compare.csv",index=False);(out/"result.json").write_text(json.dumps({"records":rec,"p_band":[.32,.36],"orig_gate":-.06,"thresholds_predeclared":True,"holdout_used_for_selection":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False},indent=2)+"\n")
print("LOWP_RESCUE_RESULT");print(pd.DataFrame(rec).to_string(index=False));print("SEPTEMBER_UNREAD")
