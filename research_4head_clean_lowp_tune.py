#!/usr/bin/env python3
"""Tune low-p rescue on DEV Mar-May + VAL June only; Jul-Aug evaluation only."""
from pathlib import Path
import json, sys, itertools
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_4head_clean_long_dataset as ds
import research_4head_clean_6m_headmodel as hm

ds.START=pd.Timestamp("2026-03-01").date()
ds.END=pd.Timestamp("2026-08-31").date()
ds.WARMUP=pd.Timestamp("2025-10-01").date()
ds.main()
z=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",dtype={"race_code":str})
z["race_code"]=z["race_code"].str.zfill(12)
hm.main()
sc=pd.read_csv("/tmp/head4_clean_6m_headmodel/scored.csv",dtype={"race_code":str})
sc["race_code"]=sc["race_code"].str.zfill(12)
d=sc[["race_code","p"]].merge(z,on="race_code",how="left",validate="one_to_one")

orig="orig4_adv_inside"; mw="motor_win_diff_4v3"; m2="motor_2ren_diff_4v3"; st="st4_adv_inside"
base=d["p"].ge(.36)&d[orig].ge(-.06)
dev=d["month"].isin(["2026-03","2026-04","2026-05"])
val=d["month"].eq("2026-06")
hold=d["month"].isin(["2026-07","2026-08"])

# Coarse, predeclared grid. Selection uses DEV+VAL only; HOLD is evaluated afterward.
pmins=[.32,.325,.33,.335,.34,.345,.35,.355]
orig_cuts=[-.12,-.09,-.06,-.03,0.0]
mw_cuts=[-.08,-.05,-.03,0.0,.03,.05]
m2_cuts=[-10.0,-7.0,-4.0,0.0,4.0]
st_cuts=[-.8,-.6,-.4,-.2]
rows=[]
for pmin,oc,mwc,m2c,stc in itertools.product(pmins,orig_cuts,mw_cuts,m2_cuts,st_cuts):
    rescue=d["p"].ge(pmin)&d["p"].lt(.36)&d[orig].ge(oc)&d[mw].ge(mwc)&d[m2].ge(m2c)&d[st].ge(stc)
    combined=base|rescue
    rec={"pmin":pmin,"orig_cut":oc,"mw_cut":mwc,"m2_cut":m2c,"st_cut":stc}
    for nm,mask in [("DEV",dev),("VAL",val)]:
        s=d[combined&mask]
        rec[nm+"_R"]=len(s);rec[nm+"_H"]=int(s["head4"].sum());rec[nm+"_rate"]=float(s["head4"].mean()) if len(s) else None
    # monthly stability on selection data only
    rates=[]; counts=[]
    for mo in ["2026-03","2026-04","2026-05","2026-06"]:
        s=d[combined&d["month"].eq(mo)]
        rates.append(float(s["head4"].mean()) if len(s) else np.nan);counts.append(len(s))
    rec["SEL_R"]=rec["DEV_R"]+rec["VAL_R"];rec["SEL_H"]=rec["DEV_H"]+rec["VAL_H"]
    rec["SEL_rate"]=rec["SEL_H"]/rec["SEL_R"] if rec["SEL_R"] else None
    rec["monthly_min_rate"]=float(np.nanmin(rates));rec["monthly_mean_R"]=float(np.mean(counts))
    rows.append(rec)
g=pd.DataFrame(rows)
# Require more volume than base, >=40% each selection month, and prioritize validation + stability.
eligible=g[(g["monthly_mean_R"]>=65)&(g["monthly_min_rate"]>=.40)&(g["VAL_R"]>=50)].copy()
if len(eligible):
    eligible["score"]=eligible["VAL_rate"]*3+eligible["SEL_rate"]+np.minimum(eligible["monthly_mean_R"],100)/1000
    chosen=eligible.sort_values(["score","monthly_mean_R"],ascending=False).iloc[0]
else:
    # fallback reported explicitly, still chosen without HOLD
    g["score"]=g["VAL_rate"].fillna(0)*3+g["SEL_rate"].fillna(0)+np.minimum(g["monthly_mean_R"],100)/1000
    chosen=g.sort_values(["score","monthly_mean_R"],ascending=False).iloc[0]

params={k:float(chosen[k]) for k in ["pmin","orig_cut","mw_cut","m2_cut","st_cut"]}
rescue=d["p"].ge(params["pmin"])&d["p"].lt(.36)&d[orig].ge(params["orig_cut"])&d[mw].ge(params["mw_cut"])&d[m2].ge(params["m2_cut"])&d[st].ge(params["st_cut"])
combined=base|rescue
evals=[]
for per,months in [("MAR",["2026-03"]),("APR",["2026-04"]),("MAY",["2026-05"]),("JUN",["2026-06"]),("JUL",["2026-07"]),("AUG",["2026-08"]),("DEV_MAR_MAY",["2026-03","2026-04","2026-05"]),("VAL_JUN",["2026-06"]),("HOLD_JUL_AUG",["2026-07","2026-08"])]:
    s=d[combined&d["month"].isin(months)]
    evals.append({"period":per,"R":len(s),"H":int(s["head4"].sum()),"rate":float(s["head4"].mean()) if len(s) else None})
out=Path("/tmp/head4_clean_lowp_tune");out.mkdir(exist_ok=True)
g.sort_values(["score","monthly_mean_R"],ascending=False).head(100).to_csv(out/"top100_selection.csv",index=False)
result={"chosen":params,"eligible_count":int(len(eligible)),"evaluation":evals,"selection_uses":["2026-03","2026-04","2026-05","2026-06"],"holdout_used_for_selection":False,"continuous_warmup_from":"2025-10-01","legacy_candidate_gate_used":False,"waku10_used":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
(out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
print("LOWP_TUNE_RESULT")
print(json.dumps(result,indent=2))
print("SEPTEMBER_UNREAD")
