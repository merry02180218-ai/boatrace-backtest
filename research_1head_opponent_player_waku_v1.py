#!/usr/bin/env python3
"""1HEAD opponent PLAYER_HISTORY + Waku10 DEV diagnostic.
Frozen H078/M375 parent only. No production mutation. September outcomes unread.
"""
import argparse,json,pickle,os
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import run_1head_player_history_expansion as phbase
import research_4head_waku10_rel43_v4 as wsrc
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import onehead_production_profile as prod
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-opponent-ph-waku-v1"; OUT.mkdir(parents=True,exist_ok=True)
DEV=("2026-02","2026-03","2026-04","2026-05","2026-06"); SUP=("2026-07","2026-08")
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--prepared",required=True,type=Path); a=ap.parse_args()
 x=pickle.load(open(a.prepared,"rb")); rr=x["rows"]
 if len(rr["LIVE165"])!=165 or len(rr["H078_M375"])!=236: raise RuntimeError("frozen universe drift")
 live={str(r["race_code"]).zfill(12) for r in rr["LIVE165"]}
 # Start from the full H078/M375 universe; formal/PH head selection remains frozen downstream.
 d=pd.DataFrame(rr["H078_M375"]); d["race_code"]=d.race_code.astype(str).str.zfill(12)
 d["month"]=d.race_code.str.slice(0,4)+"-"+d.race_code.str.slice(4,6)
 d=d[d.month.isin(DEV+SUP)].copy()
 target_codes=set(d.race_code)
 from datetime import date
 phrows=phbase.build_canonical_ph_snapshots(target_codes,date(2025,10,1),date(2026,8,31),os.environ["BOATRACECSV_LOCAL_ROOT"])
 ph=pd.DataFrame([{"race_code":k,**v} for k,v in phrows.items()])
 ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
 w=wsrc.build_waku(d.race_code.tolist()); w["race_code"]=w.race_code.astype(str).str.zfill(12)
 z=d.merge(ph,on="race_code",how="left",validate="one_to_one",suffixes=("","_ph")).merge(w,on="race_code",how="left",validate="one_to_one")
 rows=[]
 for _,r in z.iterrows():
  parts=str(r.actual_combo).split("-"); actual=set(map(int,parts[1:])) if len(parts)==3 and parts[0]=="1" else set()
  for b in (2,3,4,5,6):
   q={"race_code":r.race_code,"month":str(r.month),"boat":b,"actual_opponent":int(b in actual)}
   for k in ("all_win","all_p2","frame_win","frame_p2","recent_p2"): q["pl_"+k]=r.get(f"b{b}_pl_{k}")
   for col in w.columns:
    cl=col.lower()
    if col!="race_code" and (f"b{b}" in cl or f"_{b}_" in cl): q["waku__"+col]=r.get(col)
   rows.append(q)
 q=pd.DataFrame(rows); q.to_csv(OUT/"boat_rows.csv",index=False)
 dev=q[q.month.isin(DEV)]; sig=[]
 for col in [x for x in q.columns if x.startswith("pl_") or x.startswith("waku__")]:
  x=pd.to_numeric(dev[col],errors="coerce"); y=dev.actual_opponent
  if x.notna().sum()<30: continue
  sig.append({"feature":col,"n":int(x.notna().sum()),"actual_mean":float(x[y.eq(1)].mean()),"other_mean":float(x[y.eq(0)].mean()),"delta":float(x[y.eq(1)].mean()-x[y.eq(0)].mean())})
 s=pd.DataFrame(sig)
 if len(s): s=s.sort_values("delta",key=lambda x:x.abs(),ascending=False)
 s.to_csv(OUT/"dev_signal.csv",index=False)
 # DEV-only transparent opponent-membership reranker. SUPPORT labels remain unopened here.
 feats=[x for x in q.columns if x.startswith("pl_") or x.startswith("waku__")]
 usable=[x for x in feats if pd.to_numeric(dev[x],errors="coerce").notna().sum()>=30]
 X=dev[usable].apply(pd.to_numeric,errors="coerce"); y=dev.actual_opponent.astype(int)
 model=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(C=.25,max_iter=2000,class_weight="balanced"))])
 model.fit(X,y)
 q["opp_score"]=model.predict_proba(q[usable].apply(pd.to_numeric,errors="coerce"))[:,1]
 # Result-free frozen ranking output; evaluation of SUPPORT will be a separate next stage.
 rank=q.sort_values(["race_code","opp_score"],ascending=[True,False]).copy()
 dev_codes=set(q[q.month.isin(DEV)].race_code)
 rank["opp_rank"]=rank.groupby("race_code").cumcount()+1
 rank.to_csv(OUT/"frozen_opponent_ranking.csv",index=False)
 # Open SUPPORT only after DEV model is frozen. Evaluate a simple 3-ticket ordered-pair policy:
 # top-2 opponent scores produce (A,B),(B,A), plus (A,C). Compare formal HYBRID on same support races.
 support_codes=set(q[q.month.isin(SUP)].race_code)
 byrank={k:g.sort_values("opp_score",ascending=False).boat.astype(int).tolist() for k,g in rank.groupby("race_code")}
 v365.install_payout_cache(rr["H078_M375"]); payouts=v365.payouts_for(rr["H078_M375"])
 ev=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12)
  if code not in support_codes: continue
  p2,pc=v365.formal_post_five6(r0); prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]
  bs=byrank[code]; new=[(bs[0],bs[1]),(bs[1],bs[0]),(bs[0],bs[2])]
  actual=str(r0["actual_combo"]); fh=int(actual in {f"1-{a}-{b}" for a,b in formal}); nh=int(actual in {f"1-{a}-{b}" for a,b in new})
  pay=int(payouts.get(code,0))
  ev.append({"race_code":code,"month":code[:6],"actual":actual,"formal":str(formal),"new":str(new),"formal_hit":fh,"new_hit":nh,"payout":pay})
 e=pd.DataFrame(ev); e.to_csv(OUT/"support_ticket_compare.csv",index=False)
 def met(hit):
  h=int(e[hit].sum()); n=len(e); ret=int(e.loc[e[hit].eq(1),"payout"].sum()); stake=n*300
  return {"R":n,"hits":h,"rate":h/n if n else None,"return":ret,"stake":stake,"roi":ret/stake if stake else None}
 support_eval={"formal":met("formal_hit"),"ph_waku":met("new_hit"),"rescued":int(((e.formal_hit==0)&(e.new_hit==1)).sum()),"lost":int(((e.formal_hit==1)&(e.new_hit==0)).sum())}
 # Conservative overlay: keep formal HYBRID and only use PH/Waku to score formal-ticket components.
 # No wholesale replacement. DEV-derived boat score is used only to reorder the same formal 3 tickets.
 # This cannot change ticket membership/hit count; it prepares targeted diagnostics for later one-ticket swaps.
 overlay=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12)
  if code not in byrank: continue
  p2,pc=v365.formal_post_five6(r0); prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]
  sm={int(x.boat):float(x.opp_score) for _,x in rank[rank.race_code.eq(code)].iterrows()}
  scored=sorted(formal,key=lambda ab:sm.get(int(ab[0]),0)+sm.get(int(ab[1]),0),reverse=True)
  overlay.append({"race_code":code,"month":code[:6],"formal":str(formal),"overlay_order":str(scored),
                  "actual":str(r0["actual_combo"]),"formal_hit":int(str(r0["actual_combo"]) in {f"1-{a}-{b}" for a,b in formal})})
 pd.DataFrame(overlay).to_csv(OUT/"formal_overlay_order.csv",index=False)
 # DEV-only one-ticket weakness study. Keep first two formal tickets fixed and inspect only ticket #3.
 # Candidate replacement comes from the best PH/Waku ordered pair not already in formal.
 swap=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
  if month not in DEV or code not in byrank: continue
  p2,pc=v365.formal_post_five6(r0); prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]; fs=set(formal); bs=byrank[code]
  sm={int(x.boat):float(x.opp_score) for _,x in rank[rank.race_code.eq(code)].iterrows()}
  alts=[(a,b) for a in bs for b in bs if a!=b and (a,b) not in fs]
  alts=sorted(alts,key=lambda ab:sm.get(ab[0],0)+sm.get(ab[1],0),reverse=True)
  alt=alts[0] if alts else None
  actual=str(r0["actual_combo"]); f3=f"1-{formal[2][0]}-{formal[2][1]}"; astr=f"1-{alt[0]}-{alt[1]}" if alt else ""
  swap.append({"race_code":code,"month":month,"formal3":f3,"alt":astr,
    "formal3_hit":int(actual==f3),"alt_hit":int(actual==astr),
    "formal3_score":sm.get(int(formal[2][0]),0)+sm.get(int(formal[2][1]),0),
    "alt_score":(sm.get(int(alt[0]),0)+sm.get(int(alt[1]),0)) if alt else None,
    "score_gap":((sm.get(int(alt[0]),0)+sm.get(int(alt[1]),0))-(sm.get(int(formal[2][0]),0)+sm.get(int(formal[2][1]),0))) if alt else None})
 sw=pd.DataFrame(swap); sw.to_csv(OUT/"dev_ticket3_swap_diagnostic.csv",index=False)
 scans=[]
 for t in (.00,.05,.10,.15,.20,.25,.30,.40):
  m=sw.score_gap>=t; n=int(m.sum())
  if not n: continue
  old=int(sw.loc[m,"formal3_hit"].sum()); new=int(sw.loc[m,"alt_hit"].sum())
  scans.append({"gap":t,"swap_R":n,"old_hits":old,"new_hits":new,"net_hits":new-old})
 pd.DataFrame(scans).to_csv(OUT/"dev_ticket3_swap_scan.csv",index=False)
 print("DEV_SWAP_SCAN",json.dumps(scans,ensure_ascii=False))
 # Frozen before SUPPORT: swap only formal ticket #3 when PH/Waku alternative score gap >= .20.
 frozen_gap=.20
 hs=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
  if month not in SUP or code not in byrank: continue
  p2,pc=v365.formal_post_five6(r0); prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]; fs=set(formal); bs=byrank[code]
  sm={int(x.boat):float(x.opp_score) for _,x in rank[rank.race_code.eq(code)].iterrows()}
  alts=[(a,b) for a in bs for b in bs if a!=b and (a,b) not in fs]
  alts=sorted(alts,key=lambda ab:sm.get(ab[0],0)+sm.get(ab[1],0),reverse=True)
  alt=alts[0] if alts else None
  oldscore=sm.get(int(formal[2][0]),0)+sm.get(int(formal[2][1]),0)
  gap=(sm.get(int(alt[0]),0)+sm.get(int(alt[1]),0)-oldscore) if alt else -999
  new=list(formal); swapped=bool(alt and gap>=frozen_gap)
  if swapped:new[2]=alt
  actual=str(r0["actual_combo"]); oh=int(actual in {f"1-{a}-{b}" for a,b in formal}); nh=int(actual in {f"1-{a}-{b}" for a,b in new})
  pay=int(payouts.get(code,0))
  hs.append({"race_code":code,"month":month,"swapped":int(swapped),"gap":gap,"formal_hit":oh,"overlay_hit":nh,"payout":pay,"actual":actual,"formal":str(formal),"overlay":str(new)})
 h=pd.DataFrame(hs); h.to_csv(OUT/"support_frozen_gap020.csv",index=False)
 def hm(col):
  n=len(h); hits=int(h[col].sum()); ret=int(h.loc[h[col].eq(1),"payout"].sum()); stake=n*300
  return {"R":n,"hits":hits,"rate":hits/n if n else None,"return":ret,"stake":stake,"roi":ret/stake if stake else None}
 hold={"frozen_gap":frozen_gap,"swap_R":int(h.swapped.sum()),"formal":hm("formal_hit"),"overlay":hm("overlay_hit"),
       "rescued":int(((h.formal_hit==0)&(h.overlay_hit==1)).sum()),"lost":int(((h.formal_hit==1)&(h.overlay_hit==0)).sum()),
       "selection_used_support_outcomes":False,"september_outcomes_read":False}
 (OUT/"support_frozen_gap020.json").write_text(json.dumps(hold,ensure_ascii=False,indent=2))
 print("FROZEN_GAP020_HOLDOUT",json.dumps(hold,ensure_ascii=False))
 # DEV-only ablation: measure transparent feature families separately before any new SUPPORT opening.
 # PLAYER_HISTORY p2 family is causal prior-date history; Waku ST/WR/pastwin families are evaluated independently.
 fams={
  "PH_P2":["pl_frame_p2","pl_all_p2","pl_recent_p2"],
  "WAKU_ST":[x for x in rank.columns if x.startswith("waku__") and x.endswith("_st")],
  "WAKU_WR":[x for x in rank.columns if x.startswith("waku__") and x.endswith("_wr")],
  "WAKU_PASTWIN":[x for x in rank.columns if x.startswith("waku__") and x.endswith("_pastwin")],
 }
 ab=[]
 for name,cols0 in fams.items():
  cols=[x for x in cols0 if x in rank.columns and rank.loc[rank.race_code.isin(dev_codes),x].notna().sum()>=30]
  train=rank[rank.race_code.isin(dev_codes)].copy()
  if not cols: continue
  pipe=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(C=.25,max_iter=2000,class_weight="balanced"))])
  pipe.fit(train[cols].apply(pd.to_numeric,errors="coerce"),train["actual_opponent"].astype(int))
  tmp=rank[rank.race_code.isin(dev_codes)].copy(); tmp["fs"]=pipe.predict_proba(tmp[cols].apply(pd.to_numeric,errors="coerce"))[:,1]
  for code,g in tmp.groupby("race_code"):
   r0=next((z for z in rr["H078_M375"] if str(z["race_code"]).zfill(12)==code),None)
   if r0 is None: continue
   p2,pc=v365.formal_post_five6(r0); prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA); formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]; fs=set(formal)
   sm={int(x.boat):float(x.fs) for _,x in g.iterrows()}; bs=sorted(sm,key=sm.get,reverse=True)
   alts=[(a,b) for a in bs for b in bs if a!=b and (a,b) not in fs]
   if not alts: continue
   alt=max(alts,key=lambda q:sm.get(q[0],0)+sm.get(q[1],0)); gap=sm[alt[0]]+sm[alt[1]]-(sm.get(formal[2][0],0)+sm.get(formal[2][1],0))
   actual=str(r0["actual_combo"])
   ab.append({"family":name,"race_code":code,"gap":gap,"old":int(actual==f"1-{formal[2][0]}-{formal[2][1]}"),"new":int(actual==f"1-{alt[0]}-{alt[1]}")})
 ad=pd.DataFrame(ab); rows=[]
 for name,g in ad.groupby("family"):
  for q in (.70,.75,.80,.85,.90,.95):
   t=float(g.gap.quantile(q)); m=g.gap>=t
   rows.append({"family":name,"q":q,"threshold":t,"swap_R":int(m.sum()),"old_hits":int(g.loc[m,"old"].sum()),"new_hits":int(g.loc[m,"new"].sum()),"net_hits":int((g.loc[m,"new"]-g.loc[m,"old"]).sum())})
 pd.DataFrame(rows).to_csv(OUT/"dev_feature_family_ablation.csv",index=False)
 print("DEV_FAMILY_ABLATION",json.dumps(rows,ensure_ascii=False))
 # DEV-only blend study: PH/Waku is INCLUDED in the existing HYBRID pair score, never used as a replacement policy.
 # Normalize the existing HYBRID ordered-pair score and PH/Waku opponent score within each race, then blend.
 blend_rows=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
  if month not in DEV or code not in byrank: continue
  p2,pc=v365.formal_post_five6(r0); base=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  sm={int(x.boat):float(x.opp_score) for _,x in rank[rank.race_code.eq(code)].iterrows()}
  pairs=[(a,b) for a in (2,3,4,5,6) for b in (2,3,4,5,6) if a!=b]
  bv={ab:float(base.get(ab,0.0)) for ab in pairs}; pv={ab:sm.get(ab[0],0)+sm.get(ab[1],0) for ab in pairs}
  def z(v):
   a=np.array(list(v.values()),dtype=float); mu=float(a.mean()); sd=float(a.std()) or 1.0
   return {k:(x-mu)/sd for k,x in v.items()}
  bz,pz=z(bv),z(pv); actual=str(r0["actual_combo"])
  for wgt in (0.05,0.10,0.15,0.20,0.25,0.30):
   mix={ab:bz[ab]+wgt*pz[ab] for ab in pairs}
   top=sorted(pairs,key=lambda ab:mix[ab],reverse=True)[:3]
   blend_rows.append({"race_code":code,"w":wgt,"hit":int(actual in {f"1-{a}-{b}" for a,b in top}),"tickets":str(top)})
 bd=pd.DataFrame(blend_rows); blend=[]
 for wgt,g in bd.groupby("w"):
  blend.append({"w":float(wgt),"R":int(len(g)),"hits":int(g.hit.sum()),"rate":float(g.hit.mean())})
 print("DEV_HYBRID_INCLUDED_BLEND",json.dumps(blend,ensure_ascii=False))
 pd.DataFrame(blend).to_csv(OUT/"dev_hybrid_included_blend.csv",index=False)



 (OUT/"support_eval.json").write_text(json.dumps(support_eval,ensure_ascii=False,indent=2))
 print("SUPPORT_EVAL",json.dumps(support_eval,ensure_ascii=False))
 coef=model.named_steps["lr"].coef_[0]
 cf=pd.DataFrame({"feature":usable,"coef":coef}).sort_values("coef",key=lambda s:s.abs(),ascending=False)
 cf.to_csv(OUT/"dev_model_coefficients.csv",index=False)
 meta={"stage":"DEV_MODEL_FROZEN","parent_R":int(z.race_code.nunique()),"dev_R":int(z[z.month.isin(DEV)].race_code.nunique()),"support_R":int(z[z.month.isin(SUP)].race_code.nunique()),"selection_used_support_outcomes":False,"september_outcomes_read":False,"production_changed":False,"ph_missing":int(z["b1_pl_recent_p2"].isna().sum()),"waku_columns":int(len(w.columns)-1),"model_features":len(usable),"top_model_coefficients":cf.head(20).to_dict("records"),"top":s.head(20).to_dict("records") if len(s) else []}
 (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)); print(json.dumps(meta,ensure_ascii=False))
if __name__=="__main__": main()
