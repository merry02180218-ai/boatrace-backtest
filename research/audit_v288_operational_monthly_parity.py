#!/usr/bin/env python3
from pathlib import Path
import sys, json, numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import verify_v288_operational_pre_replay as v

SRC=Path("analysis_v243_3head_expand_feature_audit.csv")
OUT=Path("research_v288_operational_monthly_parity.json")

def n(q,c): return pd.to_numeric(q[c],errors="coerce")

def main():
 q=pd.read_csv(SRC,dtype={"race_code":str}); q.date=q.date.astype(str); q["month"]=q.date.str[:7]; q["_target"]=v.target(q).astype(int)
 ms=sorted(q.month.unique()); cs=v.precols(q); pred=[]; pre={}
 for i,m in enumerate(ms):
  if i<2: continue
  tr=q[q.month.isin(ms[:i])].copy(); te=q[q.month==m].copy()
  fs=v.learned_features(tr,cs); ts=v.score_with(tr,tr,fs); te["_score"]=v.score_with(tr,te,fs)
  st=float(ts.quantile(v.S_Q)); at=float(ts.quantile(v.A_Q))
  te["grade"]=np.where(te._score>=st,"S",np.where(te._score>=at,"A","B")); pred.append(te)
  pre[m]={"source_rows":int(len(te)),"train_months":ms[:i],"S":int((te.grade=="S").sum()),"A":int((te.grade=="A").sum()),"B":int((te.grade=="B").sum())}
 u=pd.concat(pred,ignore_index=True); u=u[u.grade.isin(["S","A"])].copy()
 final=u._target.eq(1)
 core=(n(u,"f__c_b3_minus_b4_waku_st")<=v.WAKU34)&(n(u,"f__c_b3_minus_b4_st")>=v.ST34)&(n(u,"f__c_b3_meetst")<=v.MEETST)
 s=final&core; purch=u.bet.eq(1)
 a=purch&(~s)&(n(u,"f__c_b3_minus_b4_st")>=v.A_ST34)&(n(u,"f__c_wall12_weak")<=v.A_WALL)
 b=purch&(~s)&(~a)&(n(u,"f__c_b3_minus_b2_motor")>=v.B_MOTOR)&(n(u,"f__c_b3_inside_nst")<=v.B_NST)
 u["route"]=np.where(s,"S",np.where(a,"A",np.where(b,"B","NO_BET")))
 sel=u[u.route!="NO_BET"].copy()
 monthly={}
 for m in ms:
  g=sel[sel.month==m]
  monthly[m]={"races":int(len(g)),"S":int((g.route=="S").sum()),"A":int((g.route=="A").sum()),"B":int((g.route=="B").sum()),"boat3_wins":int((n(g,"result_winner")==3).sum()) if "result_winner" in g else None}
 out={"source_months":ms,"scored_months":ms[2:],"pre_grade_monthly":pre,"selected_monthly":monthly,
      "combined_selected":int(len(sel)),"expected_operational_total":94,"parity_94":bool(len(sel)==94),
      "sep2026_present":bool(any(m=="2026-09" for m in ms))}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(out,ensure_ascii=False,indent=2))
 if len(sel)!=94: raise RuntimeError(f"v288 operational parity mismatch: got {len(sel)}, expected 94")
 print("V288_OPERATIONAL_MONTHLY_PARITY_OK")
if __name__=="__main__": main()
