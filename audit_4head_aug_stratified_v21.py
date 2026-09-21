#!/usr/bin/env python3
"""v21: fixed stratified August GE30 audit controlling baseline p + PLAYER_HISTORY. No tuning."""
import json
from pathlib import Path
import pandas as pd
from scipy.stats import fisher_exact
import audit_4head_env_waku_v16 as v16

OUT=Path("/tmp/head4_aug_stratified_v21"); OUT.mkdir(exist_ok=True)

def main():
    v16.main()
    z=pd.read_csv("/tmp/head4_env_waku_v16/detail.csv",dtype={"race_code":str})
    for c in ["water_c","p","b4_pl_all_p2","w10_rel4_b3_sr","w10_rel4_b3_st"]:
        z[c]=pd.to_numeric(z[c],errors="coerce")
    z["GE30"]=z.water_c>=30
    z["BOTH"]=(z.w10_rel4_b3_sr>0)&(z.w10_rel4_b3_st>0)
    # Strata edges fixed exclusively from Mar-May, before Jul-Aug outcomes.
    dev=z[z.month.isin(["2026-03","2026-04","2026-05"])]
    p_edges=[-1e9]+[float(x) for x in dev.p.quantile([.33,.67]).values]+[1e9]
    ph_edges=[-1e9]+[float(x) for x in dev.b4_pl_all_p2.quantile([.33,.67]).values]+[1e9]
    z["p_bin"]=pd.cut(z.p,p_edges,include_lowest=True,duplicates="drop")
    z["ph_bin"]=pd.cut(z.b4_pl_all_p2,ph_edges,include_lowest=True,duplicates="drop")
    aug=z[(z.month=="2026-08")&z.BOTH&z.water_c.notna()].copy()

    # Exact fixed strata; compare GE30 vs LT30 only where both sides exist.
    rows=[]; pooled=[]
    for (pb,hb),g in aug.groupby(["p_bin","ph_bin"],observed=True):
        a=g[g.GE30]; b=g[~g.GE30]
        if len(a) and len(b):
            odds,pv=fisher_exact([[int(a.head4.sum()),len(a)-int(a.head4.sum())],[int(b.head4.sum()),len(b)-int(b.head4.sum())]])
        else: odds,pv=None,None
        rows.append({"p_bin":str(pb),"ph_bin":str(hb),"GE30_R":len(a),"GE30_H":int(a.head4.sum()),"GE30_rate":float(a.head4.mean()) if len(a) else None,
                     "LT30_R":len(b),"LT30_H":int(b.head4.sum()),"LT30_rate":float(b.head4.mean()) if len(b) else None,"odds_ratio":odds,"fisher_p":pv})
        if len(a) and len(b):
            pooled.append((a,b))
    pd.DataFrame(rows).to_csv(OUT/"fixed_strata.csv",index=False)

    # Standardized rates: equal target weights = combined stratum counts; only overlap strata.
    total=sum(len(a)+len(b) for a,b in pooled)
    ge=lt=0.0; overlap_ge=overlap_lt=0
    for a,b in pooled:
        w=(len(a)+len(b))/total if total else 0
        ge+=w*float(a.head4.mean()); lt+=w*float(b.head4.mean())
        overlap_ge+=len(a); overlap_lt+=len(b)
    summary={"overlap_strata":len(pooled),"overlap_GE30_R":overlap_ge,"overlap_LT30_R":overlap_lt,
             "standardized_GE30_rate":ge if total else None,"standardized_LT30_rate":lt if total else None,
             "standardized_diff":ge-lt if total else None}

    # Nearest-neighbor sensitivity: fixed distance on standardized p and PH using Mar-May mean/sd,
    # one LT30 control per GE30 case, with replacement, outcome never used in matching.
    mu_p=float(dev.p.mean()); sd_p=float(dev.p.std()) or 1.0
    mu_h=float(dev.b4_pl_all_p2.mean()); sd_h=float(dev.b4_pl_all_p2.std()) or 1.0
    tr=aug[aug.GE30].copy(); co=aug[~aug.GE30].copy(); pairs=[]
    for _,r in tr.iterrows():
        d=((co.p-r.p)/sd_p)**2+((co.b4_pl_all_p2-r.b4_pl_all_p2)/sd_h)**2
        if len(d):
            j=d.idxmin(); c=co.loc[j]
            pairs.append({"treated_race":r.race_code,"control_race":c.race_code,"distance":float(d.loc[j]**0.5),"treated_H":int(r.head4),"control_H":int(c.head4),"treated_p":r.p,"control_p":c.p,"treated_ph":r.b4_pl_all_p2,"control_ph":c.b4_pl_all_p2})
    pdf=pd.DataFrame(pairs); pdf.to_csv(OUT/"nearest_neighbor_pairs.csv",index=False)
    if len(pdf):
        summary.update({"matched_pairs":len(pdf),"matched_GE30_rate":float(pdf.treated_H.mean()),"matched_LT30_rate":float(pdf.control_H.mean()),"matched_diff":float((pdf.treated_H-pdf.control_H).mean()),"median_distance":float(pdf.distance.median())})
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    meta={"month":"2026-08","water_cut_c":30,"signal":"rel4_b3_sr>0 AND rel4_b3_st>0","controls":["p","b4_pl_all_p2"],"strata_edges":"Mar-May tertiles fixed before Jul-Aug","matching":"nearest LT30 by Mar-May standardized p+PLAYER_HISTORY; with replacement; outcome-blind","threshold_tuning":False,"model_refit":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(pd.DataFrame(rows).to_string(index=False)); print(json.dumps(summary)); print(json.dumps(meta)); print("HEAD4_AUG_STRATIFIED_V21_OK"); print("SEPTEMBER_UNREAD")

if __name__=="__main__":main()
