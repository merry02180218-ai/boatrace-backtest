#!/usr/bin/env python3
"""August 2026 exact-as-available replay of current 4HEAD LIVE production.
Uses strict no-backfill universe, rebuilt V93 primitives, frozen head-prob/v283,
BoatraceCSV pre-close od3, current 4-6 ticket + JPY10k Dutch semantics.
August truth is joined only after decisions are frozen. September is blocked.
"""
from __future__ import annotations
import os, math, json, glob, csv, bisect
from pathlib import Path
from collections import defaultdict
import numpy as np, pandas as pd
import audit_4head_headprob_pass_rescue as hpmod
import audit_4head_86r_v283_closing_odds as v283build
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v281_4head_opponent_third_scenario as v281
import analyze_v282_4head_conditional_third as v282
from head4_v291_downstream_inference import load_artifact,score_second,score_conditional_third
import run_4head_v291_third010_live as live

OUT=Path("/tmp/head4_aug_exact_live_profit"); OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parent
BOATS=(1,2,3,5,6); BANK=10000

def rows(path):
 p=ROOT/path
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rc(x):
 s=str(x).strip(); return (s[:-2] if s.endswith(".0") else s).zfill(12)
def ff(x,d=np.nan):
 try:
  v=float(x); return v if math.isfinite(v) else d
 except:return d

def add_start_features(long):
 q=long.copy(); cache={}; vals={}; hist={b:[] for b in range(1,7)}; allv=[]
 # Build prior-only lane bias through July, then update chronologically in August.
 for ds in pd.date_range("2025-10-01","2026-08-31"):
  d=str(ds.date()); ymd=d.replace("-","/")
  rr=rows(f"data/previews/stt/{ymd}.csv")
  g=float(np.mean(allv)) if allv else .15
  bias={b:(float(np.mean(hist[b]))-g if hist[b] else 0.0) for b in range(1,7)}
  if d.startswith("2026-08"):
   for r in rr:
    code=rc(r.get("レースコード",""))
    raw={}
    for b in range(1,7):
     v=ff(r.get(f"艇{b}_スタート展示"))
     if math.isfinite(v):raw[b]=v
    if len(raw)==6:
     corr={b:raw[b]-bias[b] for b in raw}
     def strength(a):
      order=sorted(a,key=lambda b:(a[b],b)); rank={b:i+1 for i,b in enumerate(order)}
      st={b:(6-rank[b])/5 for b in a}; return rank,st
     rrk,rs=strength(raw); crk,cs=strength(corr)
     vals[code]={b:{"suf_st_raw":raw[b],"suf_st_raw_rank":rrk[b],"suf_st_raw_strength":rs[b],
                    "suf_st_corr_rank":crk[b],"suf_st_corr_strength":cs[b]} for b in raw}
  for r in rr:
   for b in range(1,7):
    v=ff(r.get(f"艇{b}_スタート展示"))
    if math.isfinite(v) and -.30<v<1: hist[b].append(v); allv.append(v)
 for i,r in q.iterrows():
  z=vals.get(str(r.race_code).zfill(12),{}).get(int(r.boat),{})
  for k in ("suf_st_raw","suf_st_raw_rank","suf_st_raw_strength","suf_st_corr_rank","suf_st_corr_strength"):q.loc[i,k]=z.get(k,np.nan)
 return q

def od3():
 out={}
 for p in sorted(glob.glob(str(ROOT/"data/previews/od3/2026/08/*.csv"))):
  q=pd.read_csv(p,dtype={"レースコード":str})
  for _,r in q.iterrows():
   code=str(r["レースコード"]).zfill(12); m={}
   for a in range(1,7):
    for b in range(1,7):
     if b==a:continue
     for c in range(1,7):
      if c in (a,b):continue
      key=f"3連単_{a}-{b}-{c}"; v=pd.to_numeric(pd.Series([r.get(key)]),errors="coerce").iloc[0]
      if pd.notna(v) and float(v)>0:m[f"{a}-{b}-{c}"]=float(v)
   if len(m)==120:out[code]=m
 return out

def truth():
 # Result source is BoatraceCSV public realtime CSV. This function is called
 # only after the full 851-race decision table has been frozen.
 import requests
 from io import StringIO
 out={}
 for ds in pd.date_range("2026-08-01","2026-08-31"):
  if ds>=pd.Timestamp("2026-09-01"):raise RuntimeError("SEPTEMBER_RESULT_ACCESS_BLOCKED")
  url=f"https://boatracecsv.github.io/data/results/realtime/{ds:%Y/%m/%d}.csv"
  resp=requests.get(url,timeout=20)
  if resp.status_code==404:continue
  resp.raise_for_status(); q=pd.read_csv(StringIO(resp.text))
  rcc=next((x for x in q.columns if "レース" in str(x) and "コード" in str(x)),None)
  c1=next((x for x in q.columns if "1着" in str(x) and "艇" in str(x)),None)
  c2=next((x for x in q.columns if "2着" in str(x) and "艇" in str(x)),None)
  c3=next((x for x in q.columns if "3着" in str(x) and "艇" in str(x)),None)
  if not all((rcc,c1,c2,c3)):raise RuntimeError(f"RESULT_SCHEMA_{ds.date()}_{list(q.columns)}")
  for _,r in q.iterrows():
   code=rc(r.get(rcc,""))
   try:a=(int(float(r[c1])),int(float(r[c2])),int(float(r[c3])))
   except:continue
   out[code]=a
 if not out:raise RuntimeError("NO_AUGUST_TRUTH")
 return out

def motor_priors():
 hist=defaultdict(lambda:[0,0]); snaps={}
 for ds in pd.date_range("2025-11-01","2026-08-31"):
  d=str(ds.date());ymd=d.replace("-","/"); cards={rc(r.get("レースコード","")):r for r in rows(f"data/programs/race_cards/{ymd}.csv")}
  if d.startswith("2026-08"):
   for code,card in cards.items():
    j=code[8:10]; z={}
    for b in (3,4):
     mno=str(card.get(f"艇{b}_モーター番号","")).strip(); n,w=hist[(j,mno)]; z[b]=(w/n if n else None)
    snaps[code]=z
  rm={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{ymd}.csv")}
  for code,card in cards.items():
   rr=rm.get(code); 
   if not rr:continue
   try:winner=int(float(rr.get("1着_艇番")))
   except:continue
   j=code[8:10]
   for b in range(1,7):
    mno=str(card.get(f"艇{b}_モーター番号","")).strip()
    if mno:
     hist[(j,mno)][0]+=1;hist[(j,mno)][1]+=int(winner==b)
 return snaps

def ecdf(x,refs,missing=.5):
 if x is None or not math.isfinite(float(x)) or not refs:return missing
 return bisect.bisect_right(refs,float(x))/len(refs)

def main():
 strict=pd.read_csv(os.environ["STRICT_ROWS"],dtype={"race_code":str});strict.race_code=strict.race_code.astype(str).str.zfill(12)
 strict=strict[(strict.month=="2026-08")&strict.strict_post_executable.astype(str).str.lower().isin(["true","1"])].copy()
 if len(strict)!=851:raise RuntimeError(f"STRICT_AUG_EXPECT_851_GOT_{len(strict)}")
 v=pd.read_csv(os.environ["V93_ROWS"],dtype={"race_code":str});v.race_code=v.race_code.astype(str).str.zfill(12);v=v[v.race_code.isin(set(strict.race_code))].copy()
 if set(v.race_code)!=set(strict.race_code):raise RuntimeError(f"V93_COVERAGE_{v.race_code.nunique()}/851")
 # Build v283 long table from pre-result V93/player primitives, then current exhibition/scenario/relative transforms.
 long=v283build.build_long_all(v); long=add_start_features(long)
 art=load_artifact(); sf=list(art["v283_SECOND"]["features"]);cf=list(art["v283_COND_THIRD"]["features"])
 hps=hpmod.headprob_scores(); hps.race_code=hps.race_code.astype(str).str.zfill(12); hm=dict(zip(hps.race_code,hps.head_prob))
 om=od3(); motors=motor_priors()
 nf=json.loads((ROOT/"artifacts/head4_newfeature_fixed156_production.json").read_text())
 refs=nf["ecdf_sorted_reference"]; weights=nf["weights"]; thr=float(nf["production_threshold"]); missing=float(nf.get("score_transform",{}).get("missing_value_rank",.5))
 pre=strict.set_index("race_code"); decisions=[]
 for code,g in long.groupby("race_code"):
  if code not in hm or code not in om:raise RuntimeError(f"MISSING_HP_OR_OD3_{code}")
  sr=[]
  for _,r in g.iterrows():
   x={"boat":int(r.boat)}
   for f in sf:
    if f not in r:raise RuntimeError(f"SECOND_FEATURE_MISSING_{f}")
    x[f]=r[f]
   sr.append(x)
  p2=score_second(sr,art);pc=score_conditional_third(v283build.conditional_rows(g,sf,cf),art)
  tickets=live.production_tickets(p2,pc); ovs=[om[code][t] for t in tickets]; comp=live.composite_odds(ovs)
  pairs=[tuple(map(int,t.split("-")[1:])) for t in tickets]
  mass=0.0; allj={}
  for s in BOATS:
   for t in BOATS:
    if s!=t:allj[(s,t)]=math.exp(.60*math.log(max(p2[s],1e-12))+.40*math.log(max(pc[(s,t)],1e-12)))
  den=sum(allj.values());mass=sum(allj[x]/den for x in pairs)
  hp=float(hm[code]); rr=pre.loc[code]; st=float(rr.st4_adv_inside);orig=float(rr.orig4_adv_inside)
  old164=(st>=-.6000000000000001 and orig>=-.057777777777777706)
  baseformula=(comp>=7 and mass>=.425) or (comp<7 and hp>=.22 and mass>=.375 and comp>=3)
  base120=old164 and (baseformula or (comp>=2.5 and hp+1.5*mass>=.82))
  by={int(r.boat):r for _,r in g.iterrows()};b3=by[3];b4=by.get(4)
  # Boat 4 row is not in opponent long table; derive head current values from opponent scenario h4_* columns.
  h4={k:ff(g.iloc[0].get("h4_"+k)) for k in ("cur_ex","cur_st","cur_orig_straight","cur_orig_avg")}
  wall_ready=all(math.isfinite(x) for x in h4.values()) and all(math.isfinite(ff(b3.get(k))) for k in ("cur_ex","cur_st","cur_orig_straight","cur_orig_avg"))
  attack4=(.20*h4["cur_ex"]+.40*h4["cur_st"]+.25*h4["cur_orig_straight"]+.15*h4["cur_orig_avg"]) if wall_ready else None
  stgap=(ff(b3.get("cur_st"))-h4["cur_st"]) if wall_ready else None
  wall=(.20*(ff(b3.get("cur_ex"))-h4["cur_ex"])+.40*stgap+.25*(ff(b3.get("cur_orig_straight"))-h4["cur_orig_straight"])+.15*(ff(b3.get("cur_orig_avg"))-h4["cur_orig_avg"])) if wall_ready else None
  mp=motors.get(code,{3:None,4:None}); md=(mp.get(4)-mp.get(3)) if mp.get(4) is not None and mp.get(3) is not None else None
  # card motor 2-ren difference
  ds=f"2026/08/{code[6:8]}"; cards={rc(x.get("レースコード","")):x for x in rows(f"data/programs/race_cards/{ds}.csv")};card=cards.get(code,{})
  m2d=ff(card.get("艇4_モーター2連対率"))-ff(card.get("艇3_モーター2連対率"))
  raw={"hp":hp,"mass":mass,"st":st,"orig":orig,"market_conf":-math.log(max(comp,1e-12)),
       "motor_win_rev":(-md if md is not None else None),"motor_2ren_rev":(-m2d if math.isfinite(m2d) else None),
       "attack4":attack4,"stwall_center":(-abs(stgap-.10) if stgap is not None else None),"wall_rev":(-wall if wall is not None else None)}
  score=sum(float(weights[k])*ecdf(raw.get(k),refs.get(k) or [],missing) for k in weights)
  expansion=(not base120) and st>=-.80 and orig>=-.35 and score>=thr
  selected=bool(base120 or expansion); shadow=hp<.10
  stakes=live.dutch(tickets,ovs) if selected and not shadow else [{"combo":t,"odds":o,"stake":0} for t,o in zip(tickets,ovs)]
  decisions.append({"date":str(rr.date),"race_code":code,"jcd":code[8:10],"rno":int(code[10:12]),"head_prob":hp,"mass":mass,"comp":comp,
   "old164":int(old164),"baseformula":int(baseformula),"rescue082":int(old164 and comp>=2.5 and hp+1.5*mass>=.82),"base120":int(base120),"newfeature_add":int(expansion),"selected":int(selected),"shadow":int(shadow),"production_bet":int(selected and not shadow),
   "tickets":"|".join(tickets),"ticket_count":len(tickets),"stake":sum(x["stake"] for x in stakes),"stake_plan":json.dumps(stakes,ensure_ascii=False),"nf_score":score})
 d=pd.DataFrame(decisions)
 if len(d)!=851:raise RuntimeError(f"DECISION_COUNT_{len(d)}")
 # Freeze complete. Only now join August truth.
 tr=truth(); missing_truth=set(d.race_code)-set(tr)
 # A missing top-3 result means 3連単 was not established. Refund the race stake.
 pays=[];hits=[];head=[]
 for _,r in d.iterrows():
  a=tr.get(r.race_code); head.append(int(a is not None and a[0]==4)); actual=f"{a[0]}-{a[1]}-{a[2]}" if a else ""
  plan=json.loads(r.stake_plan); hit=0
  pay=float(r.stake) if (r.production_bet and r.race_code in missing_truth) else 0.0
  if r.production_bet and actual:
   for x in plan:
    if x["combo"]==actual and int(x["stake"])>0:hit=1;pay=float(x["stake"])*float(x["odds"])
  hits.append(hit);pays.append(pay)
 d["head4"]=head;d["hit"]=hits;d["payout"]=pays;d["profit"]=d.payout-d.stake
 b=d[d.production_bet==1].copy().sort_values(["date","race_code"])
 equity=b.profit.cumsum(); peak=equity.cummax().clip(lower=0); dd=peak-equity
 loss=mx=0
 for x in b.hit:
  loss=loss+1 if not x else 0;mx=max(mx,loss)
 venue=b.groupby("jcd").agg(R=("race_code","size"),stake=("stake","sum"),payout=("payout","sum"),profit=("profit","sum"),hits=("hit","sum"),base120=("base120","sum"),newfeature_add=("newfeature_add","sum")).reset_index();venue["roi"]=100*venue.payout/venue.stake
 daily=b.groupby("date").agg(R=("race_code","size"),stake=("stake","sum"),payout=("payout","sum"),profit=("profit","sum")).reset_index();daily["roi"]=100*daily.payout/daily.stake
 out={"strict_R":851,"decision_R":len(d),"production_BET_R":len(b),"shadow_selected_R":int(((d.selected==1)&(d.shadow==1)).sum()),
      "bet_per_day_mean":float(daily.R.mean()),"bet_per_day_median":float(daily.R.median()),"bet_per_day_max":int(daily.R.max()),
      "head4":int(b.head4.sum()),"hits":int(b.hit.sum()),"stake":int(b.stake.sum()),"payout":float(b.payout.sum()),"profit":float(b.profit.sum()),
      "roi":float(100*b.payout.sum()/b.stake.sum()),"max_drawdown":float(dd.max()),"max_losing_streak":int(mx),
      "base120_BET_R":int((b.base120==1).sum()),"newfeature_add_BET_R":int((b.newfeature_add==1).sum()),"trifecta_not_established_R":int(len(missing_truth)),"trifecta_not_established_BET_R":int(b.race_code.isin(missing_truth).sum()),
      "SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 d.to_csv(OUT/"race_detail.csv",index=False);daily.to_csv(OUT/"daily.csv",index=False);venue.to_csv(OUT/"venue.csv",index=False)
 # Diagnose why current LIVE base120 is much broader than the frozen 120R research sample.
 diag={k:int(b[k].sum()) for k in ("old164","baseformula","rescue082","base120","newfeature_add")}
 diag["base120_via_baseformula_R"]=int(((b.base120==1)&(b.baseformula==1)).sum())
 diag["base120_via_rescue_only_R"]=int(((b.base120==1)&(b.baseformula==0)&(b.rescue082==1)).sum())
 diag["base120_headprob_lt018_R"]=int(((b.base120==1)&(b.head_prob<.18)).sum())
 diag["base120_headprob_ge018_R"]=int(((b.base120==1)&(b.head_prob>=.18)).sum())
 (OUT/"base120_diagnostic.json").write_text(json.dumps(diag,ensure_ascii=False,indent=2)+"\n")
 print("BASE120_DIAGNOSTIC",json.dumps(diag,ensure_ascii=False))
 (OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(out,ensure_ascii=False,indent=2));print(venue.to_string(index=False));print("HEAD4_AUG_EXACT_LIVE_PROFIT_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
