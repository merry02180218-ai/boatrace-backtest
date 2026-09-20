#!/usr/bin/env python3
"""Rebuild v93-compatible pre-result feature rows for every exact LIVE parent race.
Uses race cards/waku10, causal daily player/ST state, and archived exhibition.
No target outcomes, payouts or odds are read.
"""
from __future__ import annotations
import csv,json,os
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path
from statistics import mean
import pandas as pd
import analyze_4head_exhibition_original_trainonly as ex
from backtest import race_features,grade_score,clamp,pct_motor
OUT=Path("/tmp/head4_v93_all_parent");OUT.mkdir(exist_ok=True); ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
BOATS=range(1,7); OTH=(1,2,3,5,6); START=date(2025,10,1); A=date(2026,4,1); B=date(2026,8,31)
def rows(rel):
 p=ROOT/rel
 if not p.is_file():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rc(x):s=str(x).strip();return (s[:-2] if s.endswith(".0") else s).zfill(12)
def ii(x):
 try:return int(float(x))
 except:return 0
def ff(x,d=None):
 try:return float(x)
 except:return d
def blank():return {"n":0,"w":0,"p2":0,"nf":defaultdict(int),"wf":defaultdict(int),"p2f":defaultdict(int),"r":deque(maxlen=30)}
def pstat(raw,b):
 if raw is None:return {"all_win":1/6,"all_p2":1/3,"frame_win":.125,"frame_p2":.25,"recent_p2":1/3}
 n=raw["n"];return {"all_win":(raw["w"]+2/6)/(n+2),"all_p2":(raw["p2"]+2/3)/(n+2),"frame_win":(raw["wf"][b]+3*.125)/(raw["nf"][b]+3),"frame_p2":(raw["p2f"][b]+3*.25)/(raw["nf"][b]+3),"recent_p2":sum(raw["r"])/len(raw["r"]) if raw["r"] else 1/3}
def main():
 parent=pd.read_csv(os.environ["PARENT_EXHIBITION"],dtype={"race_code":str});parent["race_code"]=parent.race_code.astype(str).str.zfill(12); want=set(parent.race_code)
 players=defaultdict(blank);stsum=defaultdict(list);stall=[];rec=[];d=START
 while d<=B:
  ymd=d.strftime("%Y/%m/%d");cards={rc(x.get("レースコード","")):x for x in rows(f"data/programs/race_cards/{ymd}.csv")};waku={rc(x.get("レースコード","")):x for x in rows(f"data/programs/waku10/{ymd}.csv")}; strows=rows(f"data/previews/stt/{ymd}.csv")
  g=mean(stall) if stall else .15;bias={b:(mean(stsum[b])-g if stsum[b] else 0.0) for b in BOATS}
  daycodes={x for x in want if x.startswith(d.strftime("%Y%m%d"))}
  if daycodes:
   # exact archived exhibition features, with prior-only ST correction
   old=ex.PRELOAD,ex.END;ex.PRELOAD=d;ex.END=d; ex.rows=rows
   ef=ex.build_ex(daycodes); ex.PRELOAD,ex.END=old
   em={str(r.race_code).zfill(12):r for _,r in ef.iterrows()}
   for code in daycodes:
    card=cards.get(code);wk=waku.get(code);er=em.get(code)
    if card is None or wk is None or er is None or not int(er.get("basic_complete",0)):continue
    x=race_features(card,wk)
    if not x:continue
    row={"date":str(d),"race_code":code}
    # preserve fields expected by downstream feature builders.
    for b in BOATS:
     ps=pstat(players.get(str(card.get(f"艇{b}_登録番号","")).strip()),b)
     for k,v in ps.items():row[f"b{b}_pl_{k}"]=v
    # v93 primitives from same formula. Current exhibition strength components are
    # recovered from corrected_direct inside ex builder only for structural fields;
    # use source archived rows directly here.
    tk={rc(r.get("レースコード","")):r for r in rows(f"data/previews/tkz/{ymd}.csv")};st={rc(r.get("レースコード","")):r for r in strows};og={rc(r.get("レースコード","")):r for r in rows(f"data/previews/original_exhibition/{ymd}.csv")}
    from backtest_v51_lane_corrected_tickets import corrected_direct
    exv,stv,osv=corrected_direct(code,tk,st,og,bias)
    for b in OTH:
     z=x[b];motor=.62*pct_motor(z["motor2"])+.38*pct_motor(z["motor3"]);q=clamp((z["wr"]-3)/5);loc=clamp((z["local"]-2.5)/5.5);ww=clamp(z["waku_wr"]/8);nst=clamp((.24-z["nst"])/.14)
     direct=.35*exv[b]+.20*stv[b]+.25*osv[b]["turn"]+.20*osv[b]["avg"]
     parts={"grade":grade_score(z["grade"]),"national":q,"local":loc,"motor":motor,"waku":ww,"nst":nst,"direct":direct}
     for k,v in parts.items():row[f"opp_{k}_b{b}_v93"]=v
    rec.append(row)
  # ingest target day's result only after all target-day rows frozen
  rm={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{ymd}.csv")}
  for code,card in cards.items():
   rr=rm.get(code);w=ii((rr or {}).get("1着_艇番"));s=ii((rr or {}).get("2着_艇番"))
   if w not in BOATS or s not in BOATS or w==s:continue
   for b in BOATS:
    reg=str(card.get(f"艇{b}_登録番号","")).strip()
    if reg:
     q=players[reg];q["n"]+=1;q["w"]+=int(w==b);q["p2"]+=int(w==b or s==b);q["nf"][b]+=1;q["wf"][b]+=int(w==b);q["p2f"][b]+=int(w==b or s==b);q["r"].append(int(w==b or s==b))
  for r in strows:
   for b in BOATS:
    v=ff(r.get(f"艇{b}_スタート展示"))
    if v is not None and -.30<v<1:stsum[b].append(v);stall.append(v)
  d+=timedelta(days=1)
 z=pd.DataFrame(rec);z.to_csv(OUT/"v93_all_parent.csv",index=False);out={"parent_R":len(parent),"rebuilt_R":len(z),"coverage":len(z)/len(parent),"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False};(OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n");print(json.dumps(out,ensure_ascii=False,indent=2));print("HEAD4_V93_ALL_PARENT_REBUILD_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
