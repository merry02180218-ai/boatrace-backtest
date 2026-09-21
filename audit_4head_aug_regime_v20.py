#!/usr/bin/env python3
"""v20: fixed August-regime decomposition. Descriptive/falsification only; no threshold tuning."""
import json
from pathlib import Path
import pandas as pd
from scipy.stats import fisher_exact
import audit_4head_env_waku_v16 as v16

OUT=Path("/tmp/head4_aug_regime_v20"); OUT.mkdir(exist_ok=True)

def med(g,c):
    x=pd.to_numeric(g[c],errors="coerce")
    return float(x.median()) if x.notna().any() else None

def main():
    v16.main()
    z=pd.read_csv("/tmp/head4_env_waku_v16/detail.csv",dtype={"race_code":str})
    z["water_c"]=pd.to_numeric(z.water_c,errors="coerce")
    z["sr"]=pd.to_numeric(z.w10_rel4_b3_sr,errors="coerce")
    z["st"]=pd.to_numeric(z.w10_rel4_b3_st,errors="coerce")
    z["GE30"]=z.water_c>=30; z["BOTH"]=(z.sr>0)&(z.st>0)
    # Fixed four July/August cells. Compare composition, not tune a gate.
    rows=[]
    cols=["b4_pl_all_p2","w10_b4_sr","w10_rel4_b1_sr","w10_rel4_b3_sr","w10_rel4_b3_st",
          "p","orig4_adv_inside","water_c","air_c","wind_m","wave_cm"]
    ja=z[z.month.isin(["2026-07","2026-08"])].copy()
    for mo in ["2026-07","2026-08"]:
      for wb,wm in [("LT30",~ja.GE30 & ja.water_c.notna()),("GE30",ja.GE30)]:
        g=ja[(ja.month==mo)&wm&ja.BOTH]
        r={"month":mo,"water":wb,"R":len(g),"H":int(g.head4.sum()),"rate":float(g.head4.mean()) if len(g) else None,
           "venues":int(g.venue_code.nunique()),"max_venue_share":float(g.venue_code.value_counts(normalize=True).max()) if len(g) else None}
        for c in cols:
          if c in g.columns:r[c+"_median"]=med(g,c)
        rows.append(r)
    pd.DataFrame(rows).to_csv(OUT/"fixed_cell_composition.csv",index=False)

    # Venue composition counts for transparency.
    vc=ja[ja.BOTH].groupby(["month","GE30","venue_code"]).size().reset_index(name="R")
    vc.to_csv(OUT/"venue_composition.csv",index=False)

    # Predeclared PLAYER_HISTORY distribution: b4 all-p2 quartile bins fixed globally from Mar-May only.
    dev=z[z.month.isin(["2026-03","2026-04","2026-05"])]
    p2=pd.to_numeric(dev.b4_pl_all_p2,errors="coerce")
    qs=[float(x) for x in p2.quantile([.25,.5,.75]).values]
    bins=[-1e9]+qs+[1e9]
    z["p2_bin"]=pd.cut(pd.to_numeric(z.b4_pl_all_p2,errors="coerce"),bins,include_lowest=True,duplicates="drop")
    ph=[]
    for (mo,ge,b),g in z[z.month.isin(["2026-07","2026-08"])&z.BOTH].groupby(["month","GE30","p2_bin"],observed=True):
      ph.append({"month":mo,"water":"GE30" if ge else "LT30","p2_bin":str(b),"R":len(g),"H":int(g.head4.sum()),"rate":float(g.head4.mean())})
    pd.DataFrame(ph).to_csv(OUT/"player_history_fixed_bins.csv",index=False)

    # Is August GE30 venue mix itself different? Fisher per venue, descriptive multiplicity warning.
    aug=ja[(ja.month=="2026-08")&ja.BOTH]
    vr=[]
    for ve in sorted(aug.venue_code.dropna().unique()):
      a=aug[aug.venue_code==ve]; b=aug[aug.venue_code!=ve]
      # association venue vs high-water membership, not outcome
      tab=[[int(a.GE30.sum()),int((~a.GE30).sum())],[int(b.GE30.sum()),int((~b.GE30).sum())]]
      odds,p=fisher_exact(tab)
      vr.append({"venue_code":ve,"venue_R":len(a),"venue_GE30":int(a.GE30.sum()),"other_R":len(b),"other_GE30":int(b.GE30.sum()),"fisher_p":p})
    pd.DataFrame(vr).to_csv(OUT/"august_venue_water_mix.csv",index=False)
    meta={"purpose":"explain August regime without selecting a new gate","water_cut_c":30,"signal":"rel4_b3_sr>0 AND rel4_b3_st>0","player_history_bins":"Mar-May quartiles fixed before Jul-Aug","threshold_tuning":False,"model_refit":False,"multiple_testing_selection":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
    (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(pd.DataFrame(rows).to_string(index=False)); print(pd.DataFrame(ph).to_string(index=False)); print(pd.DataFrame(vr).to_string(index=False))
    print(json.dumps(meta)); print("HEAD4_AUG_REGIME_V20_OK"); print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
