#!/usr/bin/env python3
from __future__ import annotations
import csv,json,os
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"]); START=date(2025,10,1); A=date(2026,4,1); B=date(2026,8,31)
WIN=-0.0299361318939513; REN2=-7.080000000000001; PLAYER=.215605
def rows(rel):
 p=ROOT/rel
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def ff(x):
 try:return float(str(x).replace("%","").strip())
 except:return np.nan
def ii(x):
 try:return int(float(x))
 except:return 0
def rc(x):
 s=str(x).strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)
def venue(c):return str(c.get("レース場コード","")).zfill(2)
def mk(c,b):return (venue(c),str(c.get(f"艇{b}_モーター番号","")).strip())
mh=defaultdict(lambda:[0,0]); ph=defaultdict(lambda:[0,0]); daily=[]; d=START
while d<=B:
 ymd=d.strftime("%Y/%m/%d"); cards=rows(f"data/programs/race_cards/{ymd}.csv")
 if d>=A:
  st={"date":str(d),"all_R":len(cards),"missing":0,"motor_win_pass":0,"motor_2ren_pass":0,"player_pass":0,"parent":0}
  for c in cards:
   a4=mh[mk(c,4)]; a3=mh[mk(c,3)]
   w4=a4[0]/a4[1] if a4[1] else np.nan; w3=a3[0]/a3[1] if a3[1] else np.nan
   wd=w4-w3 if np.isfinite(w4) and np.isfinite(w3) else np.nan
   rd=ff(c.get("艇4_モーター2連対率"))-ff(c.get("艇3_モーター2連対率"))
   reg=str(c.get("艇4_登録番号","")).strip(); p=ph[reg]; pw=p[0]/p[1] if p[1] else np.nan
   miss=not(np.isfinite(wd) and np.isfinite(rd) and np.isfinite(pw))
   st["missing"]+=int(miss); st["motor_win_pass"]+=int(np.isfinite(wd) and wd>=WIN); st["motor_2ren_pass"]+=int(np.isfinite(rd) and rd>=REN2); st["player_pass"]+=int(np.isfinite(pw) and pw>=PLAYER)
   st["parent"]+=int(miss or (wd>=WIN and rd>=REN2 and pw>=PLAYER))
  daily.append(st)
 rmap={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{ymd}.csv")}
 for c in cards:
  rr=rmap.get(rc(c.get("レースコード",""))); w=ii((rr or {}).get("1着_艇番"))
  if w not in range(1,7):continue
  for b in range(1,7):
   k=mk(c,b)
   if k[1]: mh[k][1]+=1; mh[k][0]+=int(w==b)
   reg=str(c.get(f"艇{b}_登録番号","")).strip()
   if reg: ph[reg][1]+=1; ph[reg][0]+=int(w==b)
 d+=timedelta(days=1)
def summ(k):
 x=np.array([r[k] for r in daily],dtype=float); return {"mean":float(x.mean()),"median":float(np.median(x)),"p95":float(np.quantile(x,.95)),"max":int(x.max())}
rates=np.array([r["parent"]/r["all_R"] if r["all_R"] else 0 for r in daily])
out={"days":len(daily),"all_R":summ("all_R"),"parent":summ("parent"),"missing":summ("missing"),"parent_rate":{"mean":float(rates.mean()),"median":float(np.median(rates)),"p95":float(np.quantile(rates,.95)),"max":float(rates.max()),"today_20260920":34/168,"days_ge_today_rate":int((rates>=34/168).sum())},"gate":{"motor_win_pass":summ("motor_win_pass"),"motor_2ren_pass":summ("motor_2ren_pass"),"player_pass":summ("player_pass")},"daily":daily,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
Path("/tmp/head4_exact_parent").mkdir(exist_ok=True); Path("/tmp/head4_exact_parent/result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n"); print(json.dumps(out,ensure_ascii=False,indent=2)); print("HEAD4_EXACT_PARENT_REPLAY_OK"); print("SEPTEMBER_UNREAD")
