#!/usr/bin/env python3
"""Audit restored historical Waku10 against frozen v288 source, without outcomes.
Reconstructs exact v222/v288 normalized Waku10 edge from shared/native Waku10. No threshold tuning.
"""
from pathlib import Path
import csv,json,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import verify_v288_operational_pre_replay as v
SRC=Path("analysis_v243_3head_expand_feature_audit.csv")
OUT=Path("research_v288_waku10_restored_membership.json")
def num(q,c): return pd.to_numeric(q[c],errors="coerce")
def rc(x):
 s=str(x or "").strip()
 return (s[:-2] if s.endswith(".0") else s).zfill(12)
def read_csv_rows(p):
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def shared_day(day):
 y,m,d=day[:4],day[4:6],day[6:8]; root=Path("data/shared_historical/waku10_boatcast")/y/m/d
 if not root.is_dir(): return {}
 out={}
 for fp in sorted(root.glob("*.txt")):
  lines=fp.read_text(encoding="utf-8-sig",errors="ignore").splitlines()
  if len(lines)<8 or not lines[0].startswith("data="):continue
  try: jo,rr=map(int,fp.stem.split("_"))
  except: continue
  row={}
  for b,line in enumerate(lines[2:8],1):
   a=line.split("\t")
   if len(a)>=4: row[f"艇{b}_枠番別平均ST"]=a[2]
  out[f"{day}{jo:02d}{rr:02d}"]=row
 return out
def native_day(day):
 p=Path("data/programs/waku10")/day[:4]/day[4:6]/f"{day[6:8]}.csv"
 return {rc(r.get("レースコード")):r for r in read_csv_rows(p)}
def clamp(x,a=0,b=1): return max(a,min(b,x))
def restored(code):
 day=code[:8]; m=code[4:6]
 mp=shared_day(day) if m in {"03","04","05","06","07"} else native_day(day)
 r=mp.get(code)
 if not r and m=="07": r=native_day(day).get(code)
 if not r:return None
 try:
  s3=float(r["艇3_枠番別平均ST"]); s4=float(r["艇4_枠番別平均ST"])
  return clamp((.24-s3)/.14)-clamp((.24-s4)/.14)
 except:return None
def build_membership(q,wcol):
 q=q.copy();q["month"]=q.date.astype(str).str[:7];q["_target"]=v.target(q).astype(int)
 ms=sorted(q.month.unique());cs=v.precols(q);pred=[]
 for i,m in enumerate(ms):
  if i<2:continue
  tr=q[q.month.isin(ms[:i])].copy();te=q[q.month==m].copy();fs=v.learned_features(tr,cs);ts=v.score_with(tr,tr,fs)
  te["_score"]=v.score_with(tr,te,fs); st=float(ts.quantile(v.S_Q));at=float(ts.quantile(v.A_Q))
  te["grade"]=__import__("numpy").where(te._score>=st,"S",__import__("numpy").where(te._score>=at,"A","B"));pred.append(te)
 u=pd.concat(pred,ignore_index=True);u=u[u.grade.isin(["S","A"])].copy()
 final=u._target.eq(1);core=(num(u,wcol)<=v.WAKU34)&(num(u,"f__c_b3_minus_b4_st")>=v.ST34)&(num(u,"f__c_b3_meetst")<=v.MEETST)
 s=final&core;p=u.bet.eq(1)
 a=p&(~s)&(num(u,"f__c_b3_minus_b4_st")>=v.A_ST34)&(num(u,"f__c_wall12_weak")<=v.A_WALL)
 b=p&(~s)&(~a)&(num(u,"f__c_b3_minus_b2_motor")>=v.B_MOTOR)&(num(u,"f__c_b3_inside_nst")<=v.B_NST)
 u["route"]=__import__("numpy").where(s,"S",__import__("numpy").where(a,"A",__import__("numpy").where(b,"B","NO_BET")))
 return u[u.route!="NO_BET"][["race_code","month","route"]].copy()
def main():
 q=pd.read_csv(SRC,dtype={"race_code":str});q["race_code"]=q.race_code.map(rc);q.date=q.date.astype(str)
 q["_restored_waku34"]=[restored(c) for c in q.race_code]
 old=num(q,"f__c_b3_minus_b4_waku_st");new=num(q,"_restored_waku34")
 audit={}
 for m,g in q.assign(_old=old,_new=new).groupby(q.date.str[:7]):
  both=g._old.notna()&g._new.notna()
  audit[m]={"rows":len(g),"restored":int(g._new.notna().sum()),"old_present":int(g._old.notna().sum()),"both":int(both.sum()),
            "exact_1e9":int(((g._old-g._new).abs()<=1e-9)[both].sum())}
 oldsel=build_membership(q,"f__c_b3_minus_b4_waku_st"); newsel=build_membership(q,"_restored_waku34")
 missing=q[(q.date.astype(str).str[:7]=="2026-06") & q["_restored_waku34"].isna()][["race_code","date","f__c_b3_minus_b4_waku_st"]].to_dict("records")
 focus=q[q.race_code.eq("202605040103")][["race_code","date","f__c_b3_minus_b4_waku_st","_restored_waku34","f__c_b3_minus_b4_st","f__c_b3_meetst","f__c_wall12_weak","f__c_b3_minus_b2_motor","f__c_b3_inside_nst","bet"]].to_dict("records")
 o=set(oldsel.race_code);n=set(newsel.race_code)
 out={"policy":{"thresholds_changed":False,"outcomes_read":False,"sep2026_read":False,"waku_formula":"clamp((0.24-ST3)/0.14)-clamp((0.24-ST4)/0.14), exact v222 normalized-strength edge"},
      "coverage":audit,"old_selected":len(o),"restored_selected":len(n),"added":sorted(n-o),"removed":sorted(o-n),
      "old_monthly":oldsel.groupby("month").size().to_dict(),"restored_monthly":newsel.groupby("month").size().to_dict(),
      "restored_routes":newsel.groupby(["month","route"]).size().unstack(fill_value=0).to_dict("index"),
      "june_missing_restored":missing,"removed_focus_preonly":focus}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+chr(10),encoding="utf-8");print(json.dumps(out,ensure_ascii=False,indent=2));print("V288_WAKU10_RESTORED_MEMBERSHIP_OK")
if __name__=="__main__":main()
