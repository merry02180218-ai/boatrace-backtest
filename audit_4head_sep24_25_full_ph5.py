#!/usr/bin/env python3
"""Audit Sep24-25 PH5 head gate on the full race universe, before target-day outcomes.
Compares adopted PH5 selection with the legacy LIVE monitoring_parent pre-gate.
"""
from __future__ import annotations
import csv,json,math,os
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path
from statistics import mean
import numpy as np
from backtest import race_features,grade_score,clamp,pct_motor
from backtest_v4 import clean_name
from backtest_v51_lane_corrected_tickets import corrected_direct

ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
ART=json.loads((Path(__file__).resolve().parent/"artifacts/head4_ph5_production_v31_20260831.json").read_text())
WIN=-0.0299361318939513; REN2=-7.080000000000001; PLAYER=.215605
BOATS=range(1,7); OTH=(1,2,3,5,6)

def rows(rel):
 p=ROOT/rel
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rc(x):
 s=str(x or "").strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)
def ff(x,default=np.nan):
 try:
  v=float(str(x).replace("%","").strip());return v if math.isfinite(v) else default
 except:return default
def ii(x):
 try:return int(float(x))
 except:return 0
def venue(card):return str(card.get("レース場コード","")).zfill(2)
def mkey(card,b):return (venue(card),str(card.get(f"艇{b}_モーター番号","")).strip())
def blank():
 return {"n":0,"w":0,"p2":0,"nf":defaultdict(int),"wf":defaultdict(int),"p2f":defaultdict(int),"r":deque(maxlen=30)}
def pstat(s,b):
 n=s["n"]
 return {
  "all_win":(s["w"]+2/6)/(n+2),
  "all_p2":(s["p2"]+2/3)/(n+2),
  "frame_win":(s["wf"][b]+3*.125)/(s["nf"][b]+3),
  "frame_p2":(s["p2f"][b]+3*.25)/(s["nf"][b]+3),
  "recent_p2":sum(s["r"])/len(s["r"]) if s["r"] else 1/3,
 }
def score(row):
 vals=[]
 for i,k in enumerate(ART["features"]):
  x=ff(row.get(k),float(ART["imputer_median"][i]))
  vals.append((x-float(ART["scaler_mean"][i]))/float(ART["scaler_scale"][i]))
 z=float(ART["intercept"])+sum(float(b)*x for b,x in zip(ART["coef"],vals))
 return 1/(1+math.exp(-z))

def build_state(target):
 motors=defaultdict(lambda:[0,0])
 preg=defaultdict(lambda:[0,0])
 pnames=defaultdict(blank)
 stsum=defaultdict(list);stall=[]
 d=date(2025,10,1)
 while d<target:
  y=d.strftime("%Y/%m/%d")
  cards=rows(f"data/programs/race_cards/{y}.csv")
  rm={rc(r.get("レースコード")):r for r in rows(f"data/results/realtime/{y}.csv")}
  for card in cards:
   rr=rm.get(rc(card.get("レースコード")))
   if rr is None:continue
   w=ii(rr.get("1着_艇番"));s=ii(rr.get("2着_艇番"))
   if w not in BOATS or s not in BOATS or w==s:continue
   for b in BOATS:
    mk=mkey(card,b)
    if mk[1]:motors[mk][1]+=1;motors[mk][0]+=int(w==b)
    reg=str(card.get(f"艇{b}_登録番号","")).strip()
    if reg:preg[reg][1]+=1;preg[reg][0]+=int(w==b)
    nm=clean_name(card.get(f"艇{b}_選手名",""))
    if nm:
     q=pnames[nm];q["n"]+=1;q["w"]+=int(w==b);q["p2"]+=int(w==b or s==b)
     q["nf"][b]+=1;q["wf"][b]+=int(w==b);q["p2f"][b]+=int(w==b or s==b);q["r"].append(int(w==b or s==b))
  for r in rows(f"data/previews/stt/{y}.csv"):
   for b in BOATS:
    v=ff(r.get(f"艇{b}_スタート展示"))
    if math.isfinite(v) and -.30<v<1.0:stsum[b].append(v);stall.append(v)
  d+=timedelta(days=1)
 g=mean(stall) if stall else .15
 bias={b:(mean(stsum[b])-g if stsum[b] else 0.0) for b in BOATS}
 return motors,preg,pnames,bias

def audit_day(target):
 motors,preg,pnames,bias=build_state(target)
 y=target.strftime("%Y/%m/%d");day8=target.strftime("%Y%m%d")
 cards=rows(f"data/programs/race_cards/{y}.csv")
 waku={rc(r.get("レースコード")):r for r in rows(f"data/programs/waku10/{y}.csv")}
 tk={rc(r.get("レースコード")):r for r in rows(f"data/previews/tkz/{y}.csv")}
 st={rc(r.get("レースコード")):r for r in rows(f"data/previews/stt/{y}.csv")}
 og={rc(r.get("レースコード")):r for r in rows(f"data/previews/original_exhibition/{y}.csv")}
 out=[]
 for card in cards:
  code=rc(card.get("レースコード"));wk=waku.get(code)
  if wk is None:continue
  try:exv,stv,osv=corrected_direct(code,tk,st,og,bias)
  except Exception:continue
  x=race_features(card,wk)
  if not x:continue
  row={}
  ok=True
  for b in OTH:
   try:
    z=x[b]
    motor=.62*pct_motor(z["motor2"])+.38*pct_motor(z["motor3"])
    q=clamp((z["wr"]-3.0)/5.0);loc=clamp((z["local"]-2.5)/5.5);ww=clamp(z["waku_wr"]/8.0)
    nst=clamp((.24-z["nst"])/.14);gr=grade_score(z["grade"])
    direct=.35*exv[b]+.20*stv[b]+.25*osv[b]["turn"]+.20*osv[b]["avg"]
    parts={"grade":gr,"national":q,"local":loc,"motor":motor,"waku":ww,"nst":nst,"direct":direct}
    for k,v in parts.items():row[f"opp_{k}_b{b}_v93"]=v
   except Exception:
    ok=False;break
  if not ok:continue
  nm=clean_name(card.get("艇4_選手名",""))
  ps=pstat(pnames[nm],4) if nm else pstat(blank(),4)
  for k,v in ps.items():row[f"b4_pl_{k}"]=v
  hp=score(row)
  try:orig=float(osv[4]["avg"])-sum(float(osv[b]["avg"]) for b in (1,2,3))/3
  except:continue
  a4=motors.get(mkey(card,4),(0,0));a3=motors.get(mkey(card,3),(0,0))
  mw4=a4[0]/a4[1] if a4[1] else np.nan;mw3=a3[0]/a3[1] if a3[1] else np.nan
  md=mw4-mw3 if math.isfinite(mw4) and math.isfinite(mw3) else np.nan
  m2=ff(card.get("艇4_モーター2連対率"))-ff(card.get("艇3_モーター2連対率"))
  reg4=str(card.get("艇4_登録番号","")).strip();pr=preg.get(reg4,(0,0));pw=pr[0]/pr[1] if pr[1] else np.nan
  missing=not all(math.isfinite(v) for v in (md,m2,pw))
  parent=missing or (md>=WIN and m2>=REN2 and pw>=PLAYER)
  selected=bool(hp>=.36 and orig>=-.06)
  out.append({"date":day8,"race_code":code,"hp":hp,"orig4_adv_inside":orig,
              "monitoring_parent":bool(parent),"selected":selected,
              "parent_motor_win_diff_4v3":md,"parent_motor_2ren_diff_4v3":m2,"parent_player4_all_win_prior":pw})
 return out

def main():
 allrows=[]
 for d in (date(2026,9,24),date(2026,9,25)):allrows+=audit_day(d)
 summary={}
 for day in ("20260924","20260925"):
  q=[r for r in allrows if r["date"]==day];sel=[r for r in q if r["selected"]]
  summary[day]={
   "scored_R":len(q),"ph5_selected_R":len(sel),
   "selected_in_monitoring_parent_R":sum(r["monitoring_parent"] for r in sel),
   "selected_missed_by_monitoring_parent_R":sum(not r["monitoring_parent"] for r in sel),
   "selected_codes":[r["race_code"] for r in sel],
   "missed_codes":[r["race_code"] for r in sel if not r["monitoring_parent"]],
   "hp_max":max((r["hp"] for r in q),default=None),
  }
 out={"profile":"HEAD4_SEP24_25_FULL_PH5_VS_LEGACY_PARENT","summary":summary,"rows":allrows,
      "target_day_results_used":False,"payout_used":False}
 Path("/tmp").joinpath("head4_sep24_25_full_ph5.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(summary,ensure_ascii=False,indent=2))
 print("HEAD4_SEP24_25_FULL_PH5_AUDIT_OK")
if __name__=="__main__":main()
