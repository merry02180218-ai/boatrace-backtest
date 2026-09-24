#!/usr/bin/env python3
"""DEV OOF test: current HYBRID + PH/Waku third-side w3=.05 + promoted 1-5 topup.
September outcomes unread. Research only; no production mutation.
"""
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import backtest as bt
import run_1head_player_history_expansion as phbase
import research_4head_waku10_rel43_v4 as wsrc
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import onehead_production_profile as prod
import onehead_five_second_topup as topup

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6); W3=.05
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-phwaku-w3-five-topup"; OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except: return np.nan
def load_csv(root,rel):
 p=Path(root)/rel
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def bycode(rs):return {str(r.get("レースコード","")).zfill(12):r for r in rs}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--prepared",required=True,type=Path); a=ap.parse_args()
 x=pickle.load(a.prepared.open("rb")); rr=x["rows"]
 if len(rr["H078_M375"])!=236: raise RuntimeError("frozen universe drift")
 d=pd.DataFrame(rr["H078_M375"]); d["race_code"]=d.race_code.astype(str).str.zfill(12)
 d["month"]=d.race_code.str.slice(0,4)+"-"+d.race_code.str.slice(4,6); d=d[d.month.isin(DEV)].copy()
 target=set(d.race_code)
 from datetime import date
 phrows=phbase.build_canonical_ph_snapshots(target,date(2025,10,1),date(2026,8,31),os.environ["BOATRACECSV_LOCAL_ROOT"])
 ph=pd.DataFrame([{"race_code":k,**v} for k,v in phrows.items()]); ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
 w=wsrc.build_waku(d.race_code.tolist()); w["race_code"]=w.race_code.astype(str).str.zfill(12)
 z=d.merge(ph,on="race_code",how="left",validate="one_to_one",suffixes=("","_ph")).merge(w,on="race_code",how="left",validate="one_to_one")
 rows=[]
 for _,r in z.iterrows():
  parts=str(r.actual_combo).split("-"); actual=set(map(int,parts[1:])) if len(parts)==3 and parts[0]=="1" else set()
  for b in BOATS:
   q={"race_code":r.race_code,"month":str(r.month),"boat":b,"actual_opponent":int(b in actual)}
   for k in ("all_win","all_p2","frame_win","frame_p2","recent_p2"):q["pl_"+k]=r.get(f"b{b}_pl_{k}")
   for col in w.columns:
    cl=col.lower()
    if col!="race_code" and (f"b{b}" in cl or f"_{b}_" in cl):q["waku__"+col]=r.get(col)
   rows.append(q)
 q=pd.DataFrame(rows)
 feats=[c for c in q.columns if c.startswith("pl_") or c.startswith("waku__")]
 usable=[c for c in feats if pd.to_numeric(q[c],errors="coerce").notna().sum()>=30]
 oof=pd.Series(np.nan,index=q.index,dtype=float)
 for held in DEV:
  tr=~q.month.eq(held); te=q.month.eq(held)
  model=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(C=.25,max_iter=2000,class_weight="balanced"))])
  model.fit(q.loc[tr,usable].apply(pd.to_numeric,errors="coerce"),q.loc[tr,"actual_opponent"].astype(int))
  oof.loc[te]=model.predict_proba(q.loc[te,usable].apply(pd.to_numeric,errors="coerce"))[:,1]
 if oof.isna().any():raise RuntimeError("missing OOF")
 q["score"]=oof
 scoremaps={code:{int(r.boat):float(r.score) for _,r in g.iterrows()} for code,g in q.groupby("race_code")}
 root=os.environ["BOATRACECSV_LOCAL_ROOT"]; cache={}; out=[]
 v365.install_payout_cache(rr["H078_M375"]); payouts=v365.payouts_for(rr["H078_M375"])
 for r in rr["H078_M375"]:
  code=str(r["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
  if month not in DEV:continue
  p2,pc=v365.formal_post_five6(r); baseprob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  formal=v299.STRATEGIES["HYBRID"](p2,pc,baseprob)[:3]
  sm=scoremaps[code]; pairs=[(a,b) for a in BOATS for b in BOATS if a!=b]
  adj={ab:float(np.log(max(baseprob.get(ab,0.0),1e-12)))+W3*sm.get(ab[1],0.0) for ab in pairs}
  phw=v299.hybrid_order(p2,pc,adj)[:3]
  day=code[:8]
  if day not in cache:
   ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
   cache[day]=bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv"))
  card=cache[day].get(code,{})
  if not card:raise RuntimeError("missing card "+code)
  xf=bt.race_features(card,{})
  local_edge=ff(xf[5]["local"])-ff(xf[4]["local"])
  straight_edge=ff(r.get("straight5"))-ff(r.get("straight4")); core_edge=ff(r.get("core5"))-ff(r.get("core4"))
  rg=topup.regime_meta(p2,local_edge,straight_edge,core_edge,prod.FIVE_SECOND_TOPUP_P2_RATIO_MIN)
  fire=bool(rg["applied"])
  # Compare topup after baseline HYBRID vs after PH/Waku-adjusted HYBRID using same frozen regime.
  fstr=[f"1-{a}-{b}" for a,b in formal]; pstr=[f"1-{a}-{b}" for a,b in phw]
  fextra=topup.extra_tickets(pc,fstr,3) if fire else []; pextra=topup.extra_tickets(pc,pstr,3) if fire else []
  actual=str(r["actual_combo"]); pay=int(payouts.get(code,0))
  out.append({"race_code":code,"month":month,"fire":int(fire),"actual":actual,
   "formal":str(fstr),"phw":str(pstr),"formal_changed":int(fstr!=pstr),
   "base_hit":int(actual in fstr),"phw_hit":int(actual in pstr),
   "topup_hit":int(actual in fstr+fextra),"combined_hit":int(actual in pstr+pextra),
   "base_extra":len(fextra),"combined_extra":len(pextra),"payout":pay})
 e=pd.DataFrame(out)
 if len(e)!=190 or int(e.base_hit.sum())!=98:raise RuntimeError(f"sentinel drift R={len(e)} hits={int(e.base_hit.sum())}")
 def met(hit,extra_col=None):
  stake=len(e)*300+(int(e[extra_col].sum())*100 if extra_col else 0)
  ret=int(e.loc[e[hit].eq(1),"payout"].sum())
  return {"R":len(e),"hits":int(e[hit].sum()),"stake":stake,"return":ret,"roi":ret/stake}
 summary={"w3":W3,"score":"month-held-out OOF legacy41 actual_opponent","base":met("base_hit"),
  "phw_only":met("phw_hit"),"topup_only":met("topup_hit","base_extra"),"combined":met("combined_hit","combined_extra"),
  "changed_R":int(e.formal_changed.sum()),"fires":int(e.fire.sum()),
  "combined_rescued_vs_topup":int(((e.topup_hit==0)&(e.combined_hit==1)).sum()),
  "combined_lost_vs_topup":int(((e.topup_hit==1)&(e.combined_hit==0)).sum()),
  "monthly":[],"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
 for m,g in e.groupby("month"):
  summary["monthly"].append({"month":m,"R":len(g),"base":int(g.base_hit.sum()),"phw":int(g.phw_hit.sum()),"topup":int(g.topup_hit.sum()),"combined":int(g.combined_hit.sum()),"changed_R":int(g.formal_changed.sum()),"fires":int(g.fire.sum())})
 e.to_csv(OUT/"rows.csv",index=False); (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 print("DEV_PHW_W3_005_PLUS_1TO5",json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":main()
