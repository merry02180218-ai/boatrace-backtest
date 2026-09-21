#!/usr/bin/env python3
"""Independent audit of player-history features against strictly prior-date results."""
import csv,json,os
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path
import pandas as pd,numpy as np
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"]); START=date(2025,10,1); END=date(2026,8,31)
def rows(rel):
 p=ROOT/rel
 if not p.is_file():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rc(x):
 s=str(x).strip();return (s[:-2] if s.endswith(".0") else s).zfill(12)
def ii(x):
 try:return int(float(x))
 except:return 0
def blank():return {"n":0,"w":0,"p2":0,"nf":defaultdict(int),"wf":defaultdict(int),"p2f":defaultdict(int),"r":deque(maxlen=30)}
def stat(q,b):
 if q is None:return [1/6,1/3,.125,.25,1/3]
 n=q["n"];return [(q["w"]+2/6)/(n+2),(q["p2"]+2/3)/(n+2),(q["wf"][b]+3*.125)/(q["nf"][b]+3),(q["p2f"][b]+3*.25)/(q["nf"][b]+3),sum(q["r"])/len(q["r"]) if q["r"] else 1/3]
def main():
 z=pd.read_csv("/tmp/head4_v93_all_parent/v93_all_parent.csv",dtype={"race_code":str});z.race_code=z.race_code.astype(str).str.zfill(12); target=set(z.race_code)
 stored=z.set_index("race_code")
 players=defaultdict(blank); checked=0;mismatch=[];snap=[];d=START
 names=["all_win","all_p2","frame_win","frame_p2","recent_p2"]
 while d<=END:
  y=d.strftime("%Y/%m/%d"); cards={rc(x.get("レースコード","")):x for x in rows(f"data/programs/race_cards/{y}.csv")}
  # Compare BEFORE reading this date's result file.
  for code,card in cards.items():
   if code not in target:continue
   checked+=1
   for b in range(1,7):
    reg=str(card.get(f"艇{b}_登録番号","")).strip();vals=stat(players.get(reg),b)
    for k,v in zip(names,vals):
     col=f"b{b}_pl_{k}"; got=float(stored.loc[code,col])
     if not np.isclose(got,v,rtol=0,atol=1e-12,equal_nan=True):
      mismatch.append({"race_code":code,"boat":b,"feature":col,"stored":got,"independent":v})
   if b==4:snap.append({"race_code":code,"date":str(d),"reg":reg,"prior_n":players.get(reg,{}).get("n",0) if players.get(reg) else 0,"b4_pl_all_p2_independent":vals[1],"b4_pl_all_p2_stored":float(stored.loc[code,"b4_pl_all_p2"])})
  # Only now may this day's outcomes update state for future dates.
  rm={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{y}.csv")}
  for code,card in cards.items():
   rr=rm.get(code);w=ii((rr or {}).get("1着_艇番"));sec=ii((rr or {}).get("2着_艇番"))
   if w not in range(1,7) or sec not in range(1,7) or w==sec:continue
   for b in range(1,7):
    reg=str(card.get(f"艇{b}_登録番号","")).strip()
    if reg:
     q=players[reg];q["n"]+=1;q["w"]+=int(w==b);q["p2"]+=int(w==b or sec==b);q["nf"][b]+=1;q["wf"][b]+=int(w==b);q["p2f"][b]+=int(w==b or sec==b);q["r"].append(int(w==b or sec==b))
  d+=timedelta(days=1)
 out=Path("/tmp/head4_player_history_audit_v10");out.mkdir(exist_ok=True)
 pd.DataFrame(mismatch).to_csv(out/"mismatches.csv",index=False);pd.DataFrame(snap).to_csv(out/"b4_snapshots.csv",index=False)
 meta={"checked_races":checked,"checked_cells":checked*30,"mismatches":len(mismatch),"strict_prior_date":True,"same_day_results_used_for_features":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (out/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n");print(json.dumps(meta,ensure_ascii=False,indent=2))
 if mismatch: print("MISMATCH_SAMPLE",json.dumps(mismatch[:20],ensure_ascii=False));raise RuntimeError("PLAYER_HISTORY_MISMATCH")
 print("PLAYER_HISTORY_INDEPENDENT_AUDIT_V10_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
