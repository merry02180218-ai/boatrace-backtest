#!/usr/bin/env python3
"""v18: fixed high-water falsification for venue/month concentration. No threshold tuning."""
import json
from pathlib import Path
import pandas as pd
import audit_4head_env_waku_v16 as v16

OUT=Path("/tmp/head4_water30_falsify_v18"); OUT.mkdir(exist_ok=True)

def stat(g,label,axis,value):
    return {"axis":axis,"value":str(value),"split":label,"R":len(g),"H":int(g.head4.sum()),"rate":float(g.head4.mean()) if len(g) else None}

def main():
    v16.main()
    z=pd.read_csv("/tmp/head4_env_waku_v16/detail.csv",dtype={"race_code":str})
    z["water_c"]=pd.to_numeric(z.water_c,errors="coerce")
    z["sr"]=pd.to_numeric(z.w10_rel4_b3_sr,errors="coerce")
    z["st"]=pd.to_numeric(z.w10_rel4_b3_st,errors="coerce")
    z["high_water"]=z.water_c>=30
    z["sr_gt0"]=z.sr>0
    z["st_gt0"]=z.st>0
    z["both_gt0"]=z.sr_gt0 & z.st_gt0
    rec=[]
    # Predeclared fixed 30C and zero-sign rules; no cut search.
    for axis in ["month","venue_code"]:
        for value,g in z[z.high_water].groupby(axis):
            rec.append(stat(g,"BASE",axis,value))
            for label,m in [("SR_GT0",g.sr_gt0),("SR_LE0",~g.sr_gt0),("ST_GT0",g.st_gt0),("ST_LE0",~g.st_gt0),("BOTH_GT0",g.both_gt0)]:
                rec.append(stat(g[m],label,axis,value))
    pd.DataFrame(rec).to_csv(OUT/"high_water_month_venue.csv",index=False)

    # Leave-one-venue-out: does the 30C effect survive removal of each venue?
    loo=[]
    hi=z[z.high_water].copy()
    for ve in sorted(hi.venue_code.dropna().unique()):
        g=hi[hi.venue_code!=ve]
        for label,m in [("BASE",pd.Series(True,index=g.index)),("SR_GT0",g.sr_gt0),("ST_GT0",g.st_gt0),("BOTH_GT0",g.both_gt0)]:
            q=g[m]
            loo.append({"left_out_venue":ve,"split":label,"R":len(q),"H":int(q.head4.sum()),"rate":float(q.head4.mean()) if len(q) else None})
    pd.DataFrame(loo).to_csv(OUT/"leave_one_venue_out.csv",index=False)

    # Fixed water comparison inside the same positive signal groups.
    wb=[]
    for label,m in [("ALL",pd.Series(True,index=z.index)),("SR_GT0",z.sr_gt0),("ST_GT0",z.st_gt0),("BOTH_GT0",z.both_gt0)]:
        for band,bm in [("LT30",z.water_c<30),("GE30",z.water_c>=30)]:
            q=z[m & bm]
            wb.append({"signal":label,"water":band,"R":len(q),"H":int(q.head4.sum()),"rate":float(q.head4.mean()) if len(q) else None})
    pd.DataFrame(wb).to_csv(OUT/"fixed_water_contrast.csv",index=False)
    meta={"water_cut_c":30,"signal_cut":"zero sign","cuts_predeclared":True,"threshold_tuning":False,"descriptive_falsification":True,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(pd.DataFrame(wb).to_string(index=False))
    print(pd.DataFrame(rec).to_string(index=False))
    print(pd.DataFrame(loo).to_string(index=False))
    print(json.dumps(meta))
    print("HEAD4_WATER30_FALSIFY_V18_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__": main()
