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
import analyze_v205_3head_operational_replay as v205
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
  actual_second=int(parts[1]) if len(parts)==3 and parts[0]=="1" else -1
  actual_third=int(parts[2]) if len(parts)==3 and parts[0]=="1" else -1
  for b in (2,3,4,5,6):
   q={"race_code":r.race_code,"month":str(r.month),"boat":b,"actual_opponent":int(b in actual),
      "actual_second":int(b==actual_second),"actual_third":int(b==actual_third)}
   for k in ("all_win","all_p2","frame_win","frame_p2","recent_p2"): q["pl_"+k]=r.get(f"b{b}_pl_{k}")
   # Candidate-normalized Waku10 primitives for fine-grained opponent-role scans.
   # Keep legacy sparse boat-specific columns below for comparability with prior opponent model.
   for metric in ("wr","st","sr","pastwin"):
    q["waku_own_"+metric]=r.get(f"w10_b{b}_{metric}")
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
  for quantile in (.70,.75,.80,.85,.90,.95):
   t=float(g.gap.quantile(quantile)); m=g.gap>=t
   rows.append({"family":name,"q":quantile,"threshold":t,"swap_R":int(m.sum()),"old_hits":int(g.loc[m,"old"].sum()),"new_hits":int(g.loc[m,"new"].sum()),"net_hits":int((g.loc[m,"new"]-g.loc[m,"old"]).sum())})
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
  def zscore_map(v):
   a=np.array(list(v.values()),dtype=float); mu=float(a.mean()); sd=float(a.std()) or 1.0
   return {k:(x-mu)/sd for k,x in v.items()}
  bz,pz=zscore_map(bv),zscore_map(pv); actual=str(r0["actual_combo"])
  formal=v299.STRATEGIES["HYBRID"](p2,pc,base)[:3]
  for wgt in (0.00,0.05,0.10,0.15,0.20,0.25,0.30):
   mix={ab:bz[ab]+wgt*pz[ab] for ab in pairs}
   top=sorted(pairs,key=lambda ab:mix[ab],reverse=True)[:3]
   blend_rows.append({"race_code":code,"w":wgt,"hit":int(actual in {f"1-{a}-{b}" for a,b in top}),"tickets":str(top),"formal_tickets":str(formal),"parity":int(top==formal) if wgt==0 else None})
 bd=pd.DataFrame(blend_rows); blend=[]
 for wgt,g in bd.groupby("w"):
  blend.append({"w":float(wgt),"R":int(len(g)),"hits":int(g.hit.sum()),"rate":float(g.hit.mean()),"parity_R":int(g.parity.fillna(0).sum()) if wgt==0 else None})
 print("DEV_HYBRID_INCLUDED_BLEND",json.dumps(blend,ensure_ascii=False))
 pd.DataFrame(blend).to_csv(OUT/"dev_hybrid_included_blend.csv",index=False)
 # Structure-preserving HYBRID inclusion. w2/w3=0 must reproduce formal HYBRID exactly.
 struct_rows=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
  if month not in DEV or code not in byrank: continue
  p2,pc=v365.formal_post_five6(r0); base=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  formal=v299.STRATEGIES["HYBRID"](p2,pc,base)[:3]
  sm={int(x.boat):float(x.opp_score) for _,x in rank[rank.race_code.eq(code)].iterrows()}
  pairs=[(a,b) for a in (2,3,4,5,6) for b in (2,3,4,5,6) if a!=b]
  logb={ab:float(np.log(max(base.get(ab,0.0),1e-12))) for ab in pairs}; actual=str(r0["actual_combo"])
  for w2 in (0.00,0.05,0.10,0.15,0.20):
   for w3 in (0.00,0.05,0.10,0.15,0.20):
    adj={ab:logb[ab]+w2*sm.get(ab[0],0.0)+w3*sm.get(ab[1],0.0) for ab in pairs}
    top=v299.hybrid_order(p2,pc,adj)[:3]
    struct_rows.append({"race_code":code,"w2":w2,"w3":w3,"hit":int(actual in {f"1-{a}-{b}" for a,b in top}),"parity":int(top==formal) if w2==0 and w3==0 else None})
 sd=pd.DataFrame(struct_rows); struct=[]
 for (w2,w3),g in sd.groupby(["w2","w3"]):
  struct.append({"w2":float(w2),"w3":float(w3),"R":int(len(g)),"hits":int(g.hit.sum()),"rate":float(g.hit.mean()),"parity_R":int(g.parity.fillna(0).sum()) if w2==0 and w3==0 else None})
 print("DEV_HYBRID_STRUCTURE_PRESERVED",json.dumps(struct,ensure_ascii=False))
 pd.DataFrame(struct).to_csv(OUT/"dev_hybrid_structure_preserved.csv",index=False)
 # Fine-grained DEV-only feature scan focused on the third-place bonus inside the preserved HYBRID.
 # Each raw feature is standardized within each race across boats; no SUPPORT labels are used.
 fine=[]
 # Fine scan must use candidate-normalized columns only. Legacy waku__w10_bN_* columns
 # are intentionally excluded because they are sparse boat-identity columns, not comparable across boats.
 feature_cols=[x for x in q.columns if x.startswith("pl_") or x.startswith("waku_own_")]
 for feat in feature_cols:
  qq=q[q.month.isin(DEV)][["race_code","boat",feat]].copy()
  qq[feat]=pd.to_numeric(qq[feat],errors="coerce")
  if qq[feat].notna().sum()<30: continue
  fmap={}; varying_r=0
  for code,g in qq.groupby("race_code"):
   vals=g[feat].astype(float); med=float(vals.median()) if vals.notna().any() else 0.0; vals=vals.fillna(med)
   sdv=float(vals.std(ddof=0))
   if sdv>1e-12: varying_r+=1
   sdv=sdv or 1.0; muv=float(vals.mean())
   fmap[str(code)]={int(b):float((v-muv)/sdv) for b,v in zip(g.boat,vals)}
  if varying_r<30: continue
  for sign in (-1.0,1.0):
   for w3 in (0.02,0.05,0.08,0.10,0.15,0.20,0.30):
    hits=0; changed=0; n=0
    for r0 in rr["H078_M375"]:
     code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
     if month not in DEV or code not in fmap: continue
     p2,pc=v365.formal_post_five6(r0); base=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
     formal=v299.STRATEGIES["HYBRID"](p2,pc,base)[:3]
     pairs=[(a,b) for a in (2,3,4,5,6) for b in (2,3,4,5,6) if a!=b]
     adj={ab:float(np.log(max(base.get(ab,0.0),1e-12)))+sign*w3*fmap[code].get(ab[1],0.0) for ab in pairs}
     top=v299.hybrid_order(p2,pc,adj)[:3]; actual=str(r0["actual_combo"]); n+=1
     hits+=int(actual in {f"1-{a}-{b}" for a,b in top}); changed+=int(top!=formal)
    fine.append({"feature":feat,"sign":int(sign),"w3":w3,"R":n,"hits":hits,"rate":hits/n if n else None,"changed_R":changed,"delta_hits":hits-98,"varying_R":varying_r})
 fd=pd.DataFrame(fine).sort_values(["hits","changed_R"],ascending=[False,True])
 fd.to_csv(OUT/"dev_third_feature_fine_scan.csv",index=False)
 print("DEV_THIRD_FEATURE_FINE_TOP",json.dumps(fd.head(30).to_dict("records"),ensure_ascii=False))

 # Role-specific third-place model using only candidate-normalized pre-result features.
 # Generate month-held-out OOF predictions: each DEV month is scored by a model that never trained on that month.
 role_features=[x for x in q.columns if x.startswith("pl_") or x.startswith("waku_own_")]
 third_oof=pd.Series(np.nan,index=q.index,dtype=float)
 oof_meta=[]
 for held_month in DEV:
  train_mask=q.month.isin([m for m in DEV if m!=held_month])
  test_mask=q.month.eq(held_month)
  role_model=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),
                       ("lr",LogisticRegression(C=.25,max_iter=2000,class_weight="balanced"))])
  role_model.fit(q.loc[train_mask,role_features].apply(pd.to_numeric,errors="coerce"),
                 q.loc[train_mask,"actual_third"].astype(int))
  third_oof.loc[test_mask]=role_model.predict_proba(
      q.loc[test_mask,role_features].apply(pd.to_numeric,errors="coerce"))[:,1]
  oof_meta.append({"held_month":held_month,"train_R":int(q.loc[train_mask,"race_code"].nunique()),
                   "test_R":int(q.loc[test_mask,"race_code"].nunique())})
 if q.loc[q.month.isin(DEV),"third_oof_score"].notna().any() if "third_oof_score" in q.columns else False:
  raise RuntimeError("third_oof_score unexpectedly pre-existing")
 q["third_oof_score"]=third_oof
 if q.loc[q.month.isin(DEV),"third_oof_score"].isna().any():
  raise RuntimeError("missing third OOF predictions")

 third_maps_raw={}; third_maps_z={}
 for code,g in q[q.month.isin(DEV)].groupby("race_code"):
  raw={int(row.boat):float(row.third_oof_score) for _,row in g.iterrows()}
  vals=np.array(list(raw.values()),dtype=float); mu=float(vals.mean()); sdv=float(vals.std()) or 1.0
  third_maps_raw[str(code)]=raw
  third_maps_z[str(code)]={b:(v-mu)/sdv for b,v in raw.items()}

 role_scan=[]
 role_specs=[("raw",w) for w in (0.02,0.05,0.10,0.15,0.20,0.30,0.50)]
 role_specs += [("z",w) for w in (0.01,0.02,0.05,0.08,0.10,0.15,0.20)]
 for score_mode,role_w3 in role_specs:
  hits=changed=rescued=lost=0; n=0; month_stats={}
  score_maps=third_maps_raw if score_mode=="raw" else third_maps_z
  for r0 in rr["H078_M375"]:
   code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
   if month not in DEV or code not in score_maps: continue
   p2,pc=v365.formal_post_five6(r0); base=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
   formal=v299.STRATEGIES["HYBRID"](p2,pc,base)[:3]
   pairs=[(a,b) for a in (2,3,4,5,6) for b in (2,3,4,5,6) if a!=b]
   adj={ab:float(np.log(max(base.get(ab,0.0),1e-12)))+role_w3*score_maps[code].get(ab[1],0.0) for ab in pairs}
   top=v299.hybrid_order(p2,pc,adj)[:3]; actual=str(r0["actual_combo"])
   old_hit=int(actual in {f"1-{a}-{b}" for a,b in formal}); new_hit=int(actual in {f"1-{a}-{b}" for a,b in top})
   n+=1; hits+=new_hit; changed+=int(top!=formal); rescued+=int(old_hit==0 and new_hit==1); lost+=int(old_hit==1 and new_hit==0)
   ms=month_stats.setdefault(month,{"R":0,"formal_hits":0,"new_hits":0,"changed_R":0,"rescued":0,"lost":0})
   ms["R"]+=1; ms["formal_hits"]+=old_hit; ms["new_hits"]+=new_hit; ms["changed_R"]+=int(top!=formal)
   ms["rescued"]+=int(old_hit==0 and new_hit==1); ms["lost"]+=int(old_hit==1 and new_hit==0)
  role_scan.append({"score_mode":score_mode,"w3":role_w3,"R":n,"hits":hits,"rate":hits/n if n else None,
                    "delta_hits":hits-98,"changed_R":changed,"rescued":rescued,"lost":lost,
                    "monthly":month_stats})
 role_df=pd.DataFrame([{k:v for k,v in row.items() if k!="monthly"} for row in role_scan])
 role_df=role_df.sort_values(["hits","changed_R"],ascending=[False,True])
 role_df.to_csv(OUT/"dev_third_role_oof_scan.csv",index=False)
 role_top=sorted(role_scan,key=lambda row:(row["hits"],-row["changed_R"]),reverse=True)[:10]
 (OUT/"dev_third_role_oof_top.json").write_text(json.dumps({"features":role_features,"oof":oof_meta,"top":role_top},ensure_ascii=False,indent=2))
 print("DEV_THIRD_ROLE_OOF_TOP",json.dumps(role_top,ensure_ascii=False))

 # Re-audit the original 41-feature sparse PH/Waku model out-of-fold.
 # This directly tests whether the earlier in-sample 100/190 survives month-held-out scoring.
 def build_month_oof(target_col,feature_list):
  scores=pd.Series(np.nan,index=q.index,dtype=float)
  folds=[]
  for held_month in DEV:
   train_mask=q.month.isin([m for m in DEV if m!=held_month])
   test_mask=q.month.eq(held_month)
   fold_model=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),
                        ("lr",LogisticRegression(C=.25,max_iter=2000,class_weight="balanced"))])
   fold_model.fit(q.loc[train_mask,feature_list].apply(pd.to_numeric,errors="coerce"),
                  q.loc[train_mask,target_col].astype(int))
   scores.loc[test_mask]=fold_model.predict_proba(
       q.loc[test_mask,feature_list].apply(pd.to_numeric,errors="coerce"))[:,1]
   folds.append({"held_month":held_month,"train_R":int(q.loc[train_mask,"race_code"].nunique()),
                 "test_R":int(q.loc[test_mask,"race_code"].nunique())})
  if scores.loc[q.month.isin(DEV)].isna().any():
   raise RuntimeError("missing OOF predictions for "+target_col)
  return scores,folds

 legacy_oof_results={}
 for legacy_target in ("actual_opponent","actual_third"):
  legacy_scores,legacy_folds=build_month_oof(legacy_target,usable)
  score_col="legacy41_oof_"+legacy_target
  q[score_col]=legacy_scores
  maps_raw={}; maps_z={}
  for code,g in q[q.month.isin(DEV)].groupby("race_code"):
   raw={int(row.boat):float(getattr(row,score_col)) for _,row in g.iterrows()}
   vals=np.array(list(raw.values()),dtype=float); mu=float(vals.mean()); sdv=float(vals.std()) or 1.0
   maps_raw[str(code)]=raw
   maps_z[str(code)]={b:(v-mu)/sdv for b,v in raw.items()}
  scans=[]
  specs=[("raw",w) for w in (0.02,0.05,0.10,0.15,0.20,0.30,0.50)]
  specs += [("z",w) for w in (0.01,0.02,0.05,0.08,0.10,0.15,0.20)]
  for score_mode,legacy_w3 in specs:
   score_maps=maps_raw if score_mode=="raw" else maps_z
   hits=changed=rescued=lost=0; n=0; monthly={}
   for r0 in rr["H078_M375"]:
    code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
    if month not in DEV or code not in score_maps: continue
    p2,pc=v365.formal_post_five6(r0); base=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    formal=v299.STRATEGIES["HYBRID"](p2,pc,base)[:3]
    pairs=[(a,b) for a in (2,3,4,5,6) for b in (2,3,4,5,6) if a!=b]
    adj={ab:float(np.log(max(base.get(ab,0.0),1e-12)))+legacy_w3*score_maps[code].get(ab[1],0.0) for ab in pairs}
    top=v299.hybrid_order(p2,pc,adj)[:3]; actual=str(r0["actual_combo"])
    old_hit=int(actual in {f"1-{a}-{b}" for a,b in formal}); new_hit=int(actual in {f"1-{a}-{b}" for a,b in top})
    n+=1; hits+=new_hit; changed+=int(top!=formal)
    rescued+=int(old_hit==0 and new_hit==1); lost+=int(old_hit==1 and new_hit==0)
    ms=monthly.setdefault(month,{"R":0,"formal_hits":0,"new_hits":0,"changed_R":0,"rescued":0,"lost":0})
    ms["R"]+=1; ms["formal_hits"]+=old_hit; ms["new_hits"]+=new_hit; ms["changed_R"]+=int(top!=formal)
    ms["rescued"]+=int(old_hit==0 and new_hit==1); ms["lost"]+=int(old_hit==1 and new_hit==0)
   scans.append({"target":legacy_target,"score_mode":score_mode,"w3":legacy_w3,"R":n,"hits":hits,
                 "rate":hits/n if n else None,"delta_hits":hits-98,"changed_R":changed,
                 "rescued":rescued,"lost":lost,"monthly":monthly})
  top_scans=sorted(scans,key=lambda row:(row["hits"],-row["changed_R"]),reverse=True)[:10]
  legacy_oof_results[legacy_target]={"folds":legacy_folds,"top":top_scans}
  pd.DataFrame([{k:v for k,v in row.items() if k!="monthly"} for row in scans]).sort_values(
      ["hits","changed_R"],ascending=[False,True]).to_csv(OUT/f"dev_legacy41_{legacy_target}_oof_scan.csv",index=False)
 (OUT/"dev_legacy41_oof_top.json").write_text(json.dumps(legacy_oof_results,ensure_ascii=False,indent=2))
 print("DEV_LEGACY41_OOF_TOP",json.dumps(legacy_oof_results,ensure_ascii=False))

 # Frozen SUPPORT evaluation for the best month-held-out DEV candidate:
 # original 41-feature opponent-membership score, raw third-side bonus w3=.05.
 frozen_support_w3=0.05
 fs_rows=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
  if month not in SUP: continue
  p2,pc=v365.formal_post_five6(r0); base=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
  formal=v299.STRATEGIES["HYBRID"](p2,pc,base)[:3]
  sm={int(row.boat):float(row.opp_score) for _,row in q[q.race_code.eq(code)].iterrows()}
  pairs=[(a,b) for a in (2,3,4,5,6) for b in (2,3,4,5,6) if a!=b]
  adj={ab:float(np.log(max(base.get(ab,0.0),1e-12)))+frozen_support_w3*sm.get(ab[1],0.0) for ab in pairs}
  new=v299.hybrid_order(p2,pc,adj)[:3]
  actual=str(r0["actual_combo"])
  old_hit=int(actual in {f"1-{a}-{b}" for a,b in formal})
  new_hit=int(actual in {f"1-{a}-{b}" for a,b in new})
  pay=int(payouts.get(code,0))
  fs_rows.append({"race_code":code,"month":month,"actual":actual,"formal":str(formal),"new":str(new),
                  "changed":int(new!=formal),"formal_hit":old_hit,"new_hit":new_hit,"payout":pay})
 fs=pd.DataFrame(fs_rows); fs.to_csv(OUT/"support_frozen_legacy41_w3_005.csv",index=False)
 monthly={}
 for month,g in fs.groupby("month"):
  monthly[month]={"R":int(len(g)),"formal_hits":int(g.formal_hit.sum()),"new_hits":int(g.new_hit.sum()),
                  "changed_R":int(g.changed.sum()),
                  "rescued":int(((g.formal_hit==0)&(g.new_hit==1)).sum()),
                  "lost":int(((g.formal_hit==1)&(g.new_hit==0)).sum())}
 def support_metrics(col):
  n=len(fs); hits=int(fs[col].sum()); ret=int(fs.loc[fs[col].eq(1),"payout"].sum()); stake=n*300
  return {"R":n,"hits":hits,"rate":hits/n if n else None,"return":ret,"stake":stake,
          "roi":ret/stake if stake else None}
 frozen_support={
  "rule":"legacy41 actual_opponent model trained on DEV only; third-side raw bonus w3=.05",
  "selection_basis":"best month-held-out DEV candidate frozen before this SUPPORT evaluation",
  "w3":frozen_support_w3,
  "formal":support_metrics("formal_hit"),
  "new":support_metrics("new_hit"),
  "changed_R":int(fs.changed.sum()),
  "rescued":int(((fs.formal_hit==0)&(fs.new_hit==1)).sum()),
  "lost":int(((fs.formal_hit==1)&(fs.new_hit==0)).sum()),
  "monthly":monthly,
  "support_used_for_selection":False,
  "september_outcomes_read":False,
  "production_changed":False
 }
 (OUT/"support_frozen_legacy41_w3_005.json").write_text(json.dumps(frozen_support,ensure_ascii=False,indent=2))
 print("SUPPORT_FROZEN_LEGACY41_W3_005",json.dumps(frozen_support,ensure_ascii=False))


 # DEV-only HYBRID miss anatomy and deterministic rescue candidates.
 # No SUPPORT/September outcomes are used to choose or score these candidate rules.
 miss_rows=[]; rescue_eval=[]
 gate_values=(-0.50,-0.25,-0.10,0.00,0.10,0.25,0.50)
 rule_names=("hybrid4","joint_next","same_second_next","other_second_next","reverse_t1")
 all_dev_cases=[]
 for r0 in rr["H078_M375"]:
  rescue_code=str(r0["race_code"]).zfill(12); rescue_month=rescue_code[:4]+"-"+rescue_code[4:6]
  if rescue_month not in DEV: continue
  rescue_p2,rescue_pc=v365.formal_post_five6(r0)
  rescue_prob=v299.pair_prob(rescue_p2,rescue_pc,prod.TICKET_ALPHA)
  rescue_formal=v299.STRATEGIES["HYBRID"](rescue_p2,rescue_pc,rescue_prob)[:3]
  rescue_full=v299.STRATEGIES["HYBRID"](rescue_p2,rescue_pc,rescue_prob)
  rescue_joint=v299.joint_order(rescue_prob)
  rescue_formal_set=set(rescue_formal)
  rescue_actual=str(r0["actual_combo"])
  rescue_parts=rescue_actual.split("-")
  actual_pair=(int(rescue_parts[1]),int(rescue_parts[2])) if len(rescue_parts)==3 and rescue_parts[0]=="1" else None
  formal_hit=int(actual_pair in rescue_formal_set) if actual_pair else 0
  first_second=int(rescue_formal[0][0])
  def first_not_formal(seq,pred=lambda pair:True):
   return next((pair for pair in seq if pair not in rescue_formal_set and pred(pair)),None)
  rescue_candidates={
   "hybrid4": first_not_formal(rescue_full),
   "joint_next": first_not_formal(rescue_joint),
   "same_second_next": first_not_formal(rescue_joint,lambda pair:pair[0]==first_second),
   "other_second_next": first_not_formal(rescue_joint,lambda pair:pair[0]!=first_second),
   "reverse_t1": ((rescue_formal[0][1],rescue_formal[0][0])
                  if (rescue_formal[0][1],rescue_formal[0][0]) not in rescue_formal_set else None),
  }
  case={"race_code":rescue_code,"month":rescue_month,"actual_pair":actual_pair,"formal":rescue_formal,
        "formal_hit":formal_hit,"payout":int(payouts.get(rescue_code,0)),
        "prob":rescue_prob,"candidates":rescue_candidates}
  all_dev_cases.append(case)
  if not formal_hit and actual_pair:
   formal_seconds={int(a) for a,b in rescue_formal}; formal_thirds={int(b) for a,b in rescue_formal}
   hybrid_rank=(rescue_full.index(actual_pair)+1) if actual_pair in rescue_full else None
   joint_rank=(rescue_joint.index(actual_pair)+1) if actual_pair in rescue_joint else None
   miss_rows.append({"race_code":rescue_code,"month":rescue_month,"actual_second":actual_pair[0],"actual_third":actual_pair[1],
      "second_covered":int(actual_pair[0] in formal_seconds),"third_covered":int(actual_pair[1] in formal_thirds),
      "both_components_covered":int(actual_pair[0] in formal_seconds and actual_pair[1] in formal_thirds),
      "hybrid_rank":hybrid_rank,"joint_rank":joint_rank,
      **{f"hit_{name}":int(pair==actual_pair) if pair else 0 for name,pair in rescue_candidates.items()}})
 miss_df=pd.DataFrame(miss_rows); miss_df.to_csv(OUT/"dev_hybrid_miss_anatomy.csv",index=False)
 miss_summary={
  "miss_R":int(len(miss_df)),
  "second_covered":int(miss_df.second_covered.sum()),
  "third_covered":int(miss_df.third_covered.sum()),
  "both_components_covered":int(miss_df.both_components_covered.sum()),
  "hybrid_rank_counts":{str(k):int(v) for k,v in miss_df.hybrid_rank.value_counts().sort_index().items()},
  "joint_rank_counts":{str(k):int(v) for k,v in miss_df.joint_rank.value_counts().sort_index().items()},
  "candidate_direct_rescues":{name:int(miss_df[f"hit_{name}"].sum()) for name in rule_names}
 }
 # Always-swap and score-gap-gated swap of formal ticket #3.
 for rule_name in rule_names:
  for rescue_gate in gate_values:
   total_hits=total_return=changed_count=rescued_count=lost_count=0
   monthly_stats={}
   for case in all_dev_cases:
    candidate=case["candidates"].get(rule_name)
    formal=list(case["formal"]); new=list(formal)
    do_swap=False; score_gap=None
    if candidate is not None:
     old_score=float(case["prob"].get(formal[2],0.0)); cand_score=float(case["prob"].get(candidate,0.0))
     score_gap=float(np.log(max(cand_score,1e-12))-np.log(max(old_score,1e-12)))
     do_swap=score_gap>=rescue_gate
    if do_swap:new[2]=candidate
    new_hit=int(case["actual_pair"] in set(new)) if case["actual_pair"] else 0
    old_hit=int(case["formal_hit"])
    total_hits+=new_hit; changed_count+=int(do_swap and new!=formal)
    rescued_count+=int(old_hit==0 and new_hit==1); lost_count+=int(old_hit==1 and new_hit==0)
    if new_hit: total_return+=case["payout"]
    ms=monthly_stats.setdefault(case["month"],{"R":0,"formal_hits":0,"new_hits":0,"changed_R":0,"rescued":0,"lost":0})
    ms["R"]+=1; ms["formal_hits"]+=old_hit; ms["new_hits"]+=new_hit
    ms["changed_R"]+=int(do_swap and new!=formal); ms["rescued"]+=int(old_hit==0 and new_hit==1); ms["lost"]+=int(old_hit==1 and new_hit==0)
   rescue_eval.append({"rule":rule_name,"gate_loggap":rescue_gate,"R":len(all_dev_cases),"hits":total_hits,
      "rate":total_hits/len(all_dev_cases),"delta_hits":total_hits-98,"changed_R":changed_count,
      "rescued":rescued_count,"lost":lost_count,"return":total_return,"stake":len(all_dev_cases)*300,
      "roi":total_return/(len(all_dev_cases)*300),"monthly":monthly_stats})
 # Extra-ticket diagnostics: add deterministic 4th candidate instead of replacing.
 add_eval=[]
 for rule_name in ("hybrid4","joint_next","same_second_next","other_second_next","reverse_t1"):
  hits=ret=added=0; monthly_stats={}
  for case in all_dev_cases:
   candidate=case["candidates"].get(rule_name)
   tickets=list(case["formal"])
   if candidate is not None and candidate not in tickets:
    tickets.append(candidate); added+=1
   hit=int(case["actual_pair"] in set(tickets)) if case["actual_pair"] else 0
   hits+=hit
   if hit:ret+=case["payout"]
   ms=monthly_stats.setdefault(case["month"],{"R":0,"formal_hits":0,"new_hits":0,"added_R":0})
   ms["R"]+=1; ms["formal_hits"]+=int(case["formal_hit"]); ms["new_hits"]+=hit
   ms["added_R"]+=int(candidate is not None and candidate not in case["formal"])
  stake=len(all_dev_cases)*300+added*100
  add_eval.append({"rule":rule_name,"R":len(all_dev_cases),"hits":hits,"rate":hits/len(all_dev_cases),
                   "delta_hits":hits-98,"added_R":added,"return":ret,"stake":stake,"roi":ret/stake if stake else None,
                   "monthly":monthly_stats})
 rescue_sorted=sorted(rescue_eval,key=lambda row:(row["hits"],row["roi"],-row["changed_R"]),reverse=True)
 add_sorted=sorted(add_eval,key=lambda row:(row["hits"],row["roi"]),reverse=True)

 # DEV-only selective 4th-ticket gates for same_second_next.
 # Goal: keep most of its 8 rescues without paying for the 4th ticket on all 190 races.
 formal_dev_return=sum(case["payout"] for case in all_dev_cases if case["formal_hit"])
 same_add_scan=[]
 gate_specs=[]
 for rank_max in (4,5,6,7,8,10,12):
  gate_specs.append(("joint_rank",rank_max))
 for ratio3_min in (0.25,0.40,0.50,0.60,0.75,1.00,1.25,1.50):
  gate_specs.append(("ratio_vs_t3",ratio3_min))
 for ratio2_min in (0.25,0.40,0.50,0.60,0.70,0.80,0.90):
  gate_specs.append(("ratio_vs_same2",ratio2_min))
 for rank_max in (5,6,7,8):
  for ratio3_min in (0.40,0.60,0.75,1.00):
   gate_specs.append(("rank_and_ratio3",(rank_max,ratio3_min)))
 for gate_type,gate_value in gate_specs:
  added_count=rescues=added_return=0; monthly_stats={}
  for case in all_dev_cases:
   candidate=case["candidates"].get("same_second_next")
   if candidate is None: continue
   joint_seq=v299.joint_order(case["prob"])
   candidate_rank=(joint_seq.index(candidate)+1) if candidate in joint_seq else 999
   cand_prob=float(case["prob"].get(candidate,0.0))
   formal3_prob=float(case["prob"].get(case["formal"][2],0.0))
   formal2_prob=float(case["prob"].get(case["formal"][1],0.0))
   ratio3=cand_prob/max(formal3_prob,1e-12)
   ratio2=cand_prob/max(formal2_prob,1e-12)
   if gate_type=="joint_rank": use_add=candidate_rank<=int(gate_value)
   elif gate_type=="ratio_vs_t3": use_add=ratio3>=float(gate_value)
   elif gate_type=="ratio_vs_same2": use_add=ratio2>=float(gate_value)
   else:
    rank_max,ratio3_min=gate_value
    use_add=candidate_rank<=int(rank_max) and ratio3>=float(ratio3_min)
   if not use_add: continue
   added_count+=1
   is_rescue=int(case["formal_hit"]==0 and case["actual_pair"]==candidate)
   rescues+=is_rescue
   if is_rescue: added_return+=case["payout"]
   ms=monthly_stats.setdefault(case["month"],{"added_R":0,"rescues":0,"added_return":0})
   ms["added_R"]+=1; ms["rescues"]+=is_rescue
   if is_rescue: ms["added_return"]+=case["payout"]
  total_hits=98+rescues; total_return=formal_dev_return+added_return; total_stake=57000+added_count*100
  same_add_scan.append({"gate_type":gate_type,"gate_value":gate_value,"added_R":added_count,
                        "rescues":rescues,"hits":total_hits,"rate":total_hits/190,
                        "added_return":added_return,"marginal_roi":added_return/(added_count*100) if added_count else None,
                        "return":total_return,"stake":total_stake,"roi":total_return/total_stake if total_stake else None,
                        "monthly":monthly_stats})
 same_add_by_hits=sorted(same_add_scan,key=lambda row:(row["hits"],row["roi"],-row["added_R"]),reverse=True)
 same_add_by_roi=sorted([row for row in same_add_scan if row["rescues"]>=2],
                        key=lambda row:(row["roi"],row["hits"],-row["added_R"]),reverse=True)
 pd.DataFrame([{k:v for k,v in row.items() if k!="monthly"} for row in same_add_by_hits]).to_csv(OUT/"dev_same_second_selective_add_scan.csv",index=False)

 # DEV-only market-value gate for the same-second 4th ticket.
 # Uses the repository's user-approved closing-odds series. HEAD floor .78 is conservative.
 odds_df=v205.load_odds()
 odds_idx=odds_df.set_index("race_code",drop=False) if not odds_df.empty else pd.DataFrame()
 market_cases=[]; odds_covered=0
 for case in all_dev_cases:
  candidate=case["candidates"].get("same_second_next")
  if candidate is None: continue
  code=case["race_code"]; ticket=f"1-{candidate[0]}-{candidate[1]}"
  if odds_df.empty or code not in odds_idx.index: continue
  oddrow=odds_idx.loc[code]; oddrow=oddrow.iloc[-1] if isinstance(oddrow,pd.DataFrame) else oddrow
  try: closing_odds=float(oddrow[ticket])
  except: continue
  if not np.isfinite(closing_odds) or closing_odds<=0: continue
  odds_covered+=1
  cand_prob=float(case["prob"].get(candidate,0.0))
  t3_prob=float(case["prob"].get(case["formal"][2],0.0))
  ratio3=cand_prob/max(t3_prob,1e-12)
  ev_floor=.78*cand_prob*closing_odds
  market_cases.append({"case":case,"candidate":candidate,"ticket":ticket,"closing_odds":closing_odds,
                       "cand_prob":cand_prob,"ratio3":ratio3,"ev_floor":ev_floor})
 market_specs=[]
 for cut in (0.60,0.75,0.90,1.00,1.10,1.20,1.25,1.30,1.40,1.50,1.75,2.00):
  market_specs.append(("ev_floor",cut,None))
 for cut in (8,10,12,15,20,25,30,40,50):
  market_specs.append(("odds",cut,None))
 for ratio_cut in (1.00,1.10,1.20,1.25,1.30,1.40):
  for ev_cut in (0.75,0.90,1.00,1.10,1.20,1.30):
   market_specs.append(("ratio_ev",ratio_cut,ev_cut))
 market_scan=[]
 for gate_type,cut1,cut2 in market_specs:
  added_count=rescues=added_return=0; monthly_stats={}
  for mc in market_cases:
   if gate_type=="ev_floor": use_add=mc["ev_floor"]>=float(cut1)
   elif gate_type=="odds": use_add=mc["closing_odds"]>=float(cut1)
   else: use_add=mc["ratio3"]>=float(cut1) and mc["ev_floor"]>=float(cut2)
   if not use_add: continue
   case=mc["case"]; added_count+=1
   is_rescue=int(case["formal_hit"]==0 and case["actual_pair"]==mc["candidate"])
   rescues+=is_rescue
   if is_rescue: added_return+=case["payout"]
   ms=monthly_stats.setdefault(case["month"],{"added_R":0,"rescues":0,"added_return":0})
   ms["added_R"]+=1; ms["rescues"]+=is_rescue
   if is_rescue: ms["added_return"]+=case["payout"]
  total_hits=98+rescues; total_return=formal_dev_return+added_return; total_stake=57000+added_count*100
  market_scan.append({"gate_type":gate_type,"cut1":cut1,"cut2":cut2,"odds_coverage_R":odds_covered,
                      "added_R":added_count,"rescues":rescues,"hits":total_hits,"rate":total_hits/190,
                      "added_return":added_return,"marginal_roi":added_return/(added_count*100) if added_count else None,
                      "return":total_return,"stake":total_stake,"roi":total_return/total_stake if total_stake else None,
                      "monthly":monthly_stats})
 market_by_roi=sorted([row for row in market_scan if row["rescues"]>=2],
                      key=lambda row:(row["roi"],row["hits"],-row["added_R"]),reverse=True)
 market_by_hits=sorted(market_scan,key=lambda row:(row["hits"],row["roi"],-row["added_R"]),reverse=True)
 pd.DataFrame([{k:v for k,v in row.items() if k!="monthly"} for row in market_by_roi]).to_csv(OUT/"dev_same_second_market_gate_scan.csv",index=False)
 market_report={"coverage_R":odds_covered,"top_roi":market_by_roi[:20],"top_hits":market_by_hits[:20],
                "closing_odds_selection":True,"september_outcomes_read":False,"production_changed":False}
 (OUT/"dev_same_second_market_gate_report.json").write_text(json.dumps(market_report,ensure_ascii=False,indent=2))
 print("DEV_SAME_SECOND_MARKET_GATE",json.dumps(market_report,ensure_ascii=False))

 # Frozen one-shot SUPPORT check for the selected DEV market gate.
 # Selection rule was frozen before opening Jul-Aug outcomes:
 # same_second_next + ratio_vs_formal3 >= 1.40 + EV floor (.78 * pair_prob * closing_odds) >= .75.
 frozen_ratio_cut=1.40; frozen_ev_cut=.75
 support_market_rows=[]
 for r0 in rr["H078_M375"]:
  code=str(r0["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
  if month not in SUP: continue
  p2_s,pc_s=v365.formal_post_five6(r0); prob_s=v299.pair_prob(p2_s,pc_s,prod.TICKET_ALPHA)
  formal_s=v299.STRATEGIES["HYBRID"](p2_s,pc_s,prob_s)[:3]; formal_set_s=set(formal_s)
  first_second_s=int(formal_s[0][0])
  joint_s=v299.joint_order(prob_s)
  candidate_s=next((pair for pair in joint_s if pair not in formal_set_s and pair[0]==first_second_s),None)
  closing_odds_s=None; ratio3_s=None; ev_floor_s=None; add_s=False
  if candidate_s is not None and not odds_df.empty and code in odds_idx.index:
   odds_row_s=odds_idx.loc[code]; odds_row_s=odds_row_s.iloc[-1] if isinstance(odds_row_s,pd.DataFrame) else odds_row_s
   ticket_s=f"1-{candidate_s[0]}-{candidate_s[1]}"
   try: closing_odds_s=float(odds_row_s[ticket_s])
   except: closing_odds_s=None
   if closing_odds_s is not None and np.isfinite(closing_odds_s) and closing_odds_s>0:
    cand_prob_s=float(prob_s.get(candidate_s,0.0))
    formal3_prob_s=float(prob_s.get(formal_s[2],0.0))
    ratio3_s=cand_prob_s/max(formal3_prob_s,1e-12)
    ev_floor_s=.78*cand_prob_s*closing_odds_s
    add_s=bool(ratio3_s>=frozen_ratio_cut and ev_floor_s>=frozen_ev_cut)
  actual_s=str(r0["actual_combo"])
  actual_parts_s=actual_s.split("-")
  actual_pair_s=(int(actual_parts_s[1]),int(actual_parts_s[2])) if len(actual_parts_s)==3 and actual_parts_s[0]=="1" else None
  formal_hit_s=int(actual_pair_s in formal_set_s) if actual_pair_s else 0
  rescue_hit_s=int(add_s and candidate_s==actual_pair_s) if actual_pair_s else 0
  new_hit_s=int(formal_hit_s or rescue_hit_s)
  pay_s=int(payouts.get(code,0))
  support_market_rows.append({"race_code":code,"month":month,"formal_hit":formal_hit_s,"rescue_hit":rescue_hit_s,
      "new_hit":new_hit_s,"added":int(add_s),"candidate":str(candidate_s),"closing_odds":closing_odds_s,
      "ratio3":ratio3_s,"ev_floor":ev_floor_s,"payout":pay_s})
 support_market=pd.DataFrame(support_market_rows)
 support_market.to_csv(OUT/"support_frozen_same_second_market_gate.csv",index=False)
 support_monthly={}
 for month,g in support_market.groupby("month"):
  support_monthly[month]={"R":int(len(g)),"formal_hits":int(g.formal_hit.sum()),"new_hits":int(g.new_hit.sum()),
                          "added_R":int(g.added.sum()),"rescues":int(g.rescue_hit.sum()),
                          "return":int(g.loc[g.new_hit.eq(1),"payout"].sum())}
 support_formal_return=int(support_market.loc[support_market.formal_hit.eq(1),"payout"].sum())
 support_new_return=int(support_market.loc[support_market.new_hit.eq(1),"payout"].sum())
 support_added_R=int(support_market.added.sum()); support_R=len(support_market)
 support_market_result={
   "rule":"same_second_next fourth ticket; ratio_vs_formal3 >= 1.40; EV_floor(.78*pair_prob*closing_odds) >= .75",
   "selection_basis":"DEV-only frozen before SUPPORT outcome evaluation",
   "R":support_R,
   "formal":{"hits":int(support_market.formal_hit.sum()),"return":support_formal_return,
             "stake":support_R*300,"roi":support_formal_return/(support_R*300) if support_R else None},
   "new":{"hits":int(support_market.new_hit.sum()),"return":support_new_return,
          "stake":support_R*300+support_added_R*100,
          "roi":support_new_return/(support_R*300+support_added_R*100) if support_R else None},
   "added_R":support_added_R,"rescues":int(support_market.rescue_hit.sum()),
   "monthly":support_monthly,"support_used_for_selection":False,
   "september_outcomes_read":False,"production_changed":False
 }
 (OUT/"support_frozen_same_second_market_gate.json").write_text(json.dumps(support_market_result,ensure_ascii=False,indent=2))
 print("SUPPORT_FROZEN_SAME_SECOND_MARKET_GATE",json.dumps(support_market_result,ensure_ascii=False))

 pd.DataFrame([{k:v for k,v in row.items() if k!="monthly"} for row in rescue_sorted]).to_csv(OUT/"dev_hybrid_miss_rescue_swap_scan.csv",index=False)
 pd.DataFrame([{k:v for k,v in row.items() if k!="monthly"} for row in add_sorted]).to_csv(OUT/"dev_hybrid_miss_rescue_add_scan.csv",index=False)
 miss_report={"summary":miss_summary,"top_swap":rescue_sorted[:15],"add_ticket":add_sorted,
              "same_second_selective_top_hits":same_add_by_hits[:15],
              "same_second_selective_top_roi":same_add_by_roi[:15]}
 (OUT/"dev_hybrid_miss_rescue_report.json").write_text(json.dumps(miss_report,ensure_ascii=False,indent=2))
 print("DEV_HYBRID_MISS_RESCUE",json.dumps(miss_report,ensure_ascii=False))

 (OUT/"support_eval.json").write_text(json.dumps(support_eval,ensure_ascii=False,indent=2))
 print("SUPPORT_EVAL",json.dumps(support_eval,ensure_ascii=False))
 coef=model.named_steps["lr"].coef_[0]
 cf=pd.DataFrame({"feature":usable,"coef":coef}).sort_values("coef",key=lambda s:s.abs(),ascending=False)
 cf.to_csv(OUT/"dev_model_coefficients.csv",index=False)
 meta={"stage":"DEV_MODEL_FROZEN","parent_R":int(z.race_code.nunique()),"dev_R":int(z[z.month.isin(DEV)].race_code.nunique()),"support_R":int(z[z.month.isin(SUP)].race_code.nunique()),"selection_used_support_outcomes":False,"september_outcomes_read":False,"production_changed":False,"ph_missing":int(z["b1_pl_recent_p2"].isna().sum()),"waku_columns":int(len(w.columns)-1),"model_features":len(usable),"top_model_coefficients":cf.head(20).to_dict("records"),"top":s.head(20).to_dict("records") if len(s) else []}
 (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)); print(json.dumps(meta,ensure_ascii=False))
if __name__=="__main__": main()
