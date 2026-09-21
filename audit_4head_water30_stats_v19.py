#!/usr/bin/env python3
"""v19: fixed uncertainty + month/water interaction audit. No threshold tuning."""
import json, math
from pathlib import Path
import pandas as pd
from scipy.stats import fisher_exact
import audit_4head_env_waku_v16 as v16

OUT=Path("/tmp/head4_water30_stats_v19"); OUT.mkdir(exist_ok=True)

def wilson(h,n,z=1.959963984540054):
    if n==0:return (None,None)
    p=h/n; den=1+z*z/n
    cen=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return cen-half,cen+half

def row(label,a_h,a_n,b_h,b_n):
    # A=GE30, B=LT30. Fisher two-sided, fixed comparison.
    lo,hi=wilson(a_h,a_n); blo,bhi=wilson(b_h,b_n)
    table=[[a_h,a_n-a_h],[b_h,b_n-b_h]]
    odds,p=fisher_exact(table,alternative="two-sided")
    return {"comparison":label,"GE30_R":a_n,"GE30_H":a_h,"GE30_rate":a_h/a_n if a_n else None,
            "GE30_wilson_lo":lo,"GE30_wilson_hi":hi,"LT30_R":b_n,"LT30_H":b_h,
            "LT30_rate":b_h/b_n if b_n else None,"LT30_wilson_lo":blo,"LT30_wilson_hi":bhi,
            "rate_diff":a_h/a_n-b_h/b_n if a_n and b_n else None,"odds_ratio":odds,"fisher_p":p}

def main():
    v16.main()
    z=pd.read_csv("/tmp/head4_env_waku_v16/detail.csv",dtype={"race_code":str})
    z["water_c"]=pd.to_numeric(z.water_c,errors="coerce")
    z["sr"]=pd.to_numeric(z.w10_rel4_b3_sr,errors="coerce")
    z["st"]=pd.to_numeric(z.w10_rel4_b3_st,errors="coerce")
    z["GE30"]=z.water_c>=30; z["SR"]=z.sr>0; z["ST"]=z.st>0; z["BOTH"]=z.SR & z.ST
    rec=[]
    for sig in ["ALL","SR","ST","BOTH"]:
        m=pd.Series(True,index=z.index) if sig=="ALL" else z[sig]
        a=z[m & z.GE30]; b=z[m & ~z.GE30 & z.water_c.notna()]
        rec.append(row(sig,int(a.head4.sum()),len(a),int(b.head4.sum()),len(b)))
    pd.DataFrame(rec).to_csv(OUT/"fixed_fisher_wilson.csv",index=False)

    # Predeclared July/August 2x2 cells: separates month from fixed water>=30.
    cells=[]
    ja=z[z.month.isin(["2026-07","2026-08"])].copy()
    for month in ["2026-07","2026-08"]:
        for water in ["LT30","GE30"]:
            wm=ja.GE30 if water=="GE30" else (~ja.GE30 & ja.water_c.notna())
            for sig in ["ALL","SR","ST","BOTH"]:
                sm=pd.Series(True,index=ja.index) if sig=="ALL" else ja[sig]
                q=ja[(ja.month==month) & wm & sm]
                lo,hi=wilson(int(q.head4.sum()),len(q))
                cells.append({"month":month,"water":water,"signal":sig,"R":len(q),"H":int(q.head4.sum()),"rate":float(q.head4.mean()) if len(q) else None,"wilson_lo":lo,"wilson_hi":hi})
    pd.DataFrame(cells).to_csv(OUT/"july_august_water_cells.csv",index=False)

    # Fixed within-month GE30 vs LT30 Fisher tests; no model fitting/cut search.
    month_tests=[]
    for month in ["2026-07","2026-08"]:
        g=ja[ja.month==month]
        for sig in ["ALL","SR","ST","BOTH"]:
            sm=pd.Series(True,index=g.index) if sig=="ALL" else g[sig]
            a=g[sm & g.GE30]; b=g[sm & ~g.GE30 & g.water_c.notna()]
            month_tests.append(row(month+"|"+sig,int(a.head4.sum()),len(a),int(b.head4.sum()),len(b)))
    pd.DataFrame(month_tests).to_csv(OUT/"within_month_fisher.csv",index=False)

    meta={"water_cut_c":30,"signal_cut":"zero sign","months_fixed":["2026-07","2026-08"],"tests":"two-sided Fisher + 95% Wilson","threshold_tuning":False,"model_refit":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(pd.DataFrame(rec).to_string(index=False))
    print(pd.DataFrame(cells).to_string(index=False))
    print(pd.DataFrame(month_tests).to_string(index=False))
    print(json.dumps(meta))
    print("HEAD4_WATER30_STATS_V19_OK")
    print("SEPTEMBER_UNREAD")

if __name__=="__main__":main()
