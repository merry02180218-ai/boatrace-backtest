#!/usr/bin/env python3
"""4HEAD v23: PLAYER_HISTORY + Waku10 soft reranking with baseline feature ablation.
DEV Mar-May fit; June selects family/cut under volume floor; Jul-Aug report only.
September blocked. Research only.
"""
import csv,json,os
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_4head_waku10_rel43_v4 as w4
from backtest_v4 import clean_name

BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv")
TRUTH=Path("/tmp/head4_clean_long_dataset/dataset.csv")
OUT=Path("/tmp/head4_player_waku_soft_ablation_v23");OUT.mkdir(exist_ok=True)
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
DEV={"2026-03","2026-04","2026-05"};VAL={"2026-06"};HOLD={"2026-07","2026-08"}
BOATS=range(1,7)

def rows(rel):
 p=ROOT/rel
 if not p.is_file():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rc(x):
 s=str(x or "").strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)
def blank():return {'n':0,'w':0,'p2':0,'nf':defaultdict(int),'wf':defaultdict(int),'p2f':defaultdict(int),'r':deque(maxlen=30)}
def pstat(s,b):
 n=s['n'];nf=s['nf'][b];r=list(s['r'])
 return {'all_win':(s['w']+2/6)/(n+2),'all_p2':(s['p2']+2/3)/(n+2),
 'frame_win':(s['wf'][b]+3*.125)/(nf+3),'frame_p2':(s['p2f'][b]+3*.25)/(nf+3),
 'recent_p2':sum(r)/len(r) if r else 1/3}
def build_ph():
 state=defaultdict(blank); rec=[]; d=date(2025,10,1); end=date(2026,8,31)
 while d<=end:
  ymd=d.strftime("%Y/%m/%d"); cards=rows(f"data/programs/race_cards/{ymd}.csv")
  results={rc(x.get("レースコード")):x for x in rows(f"data/results/realtime/{ymd}.csv")}
  for card in sorted(cards,key=lambda x:rc(x.get("レースコード"))):
   code=rc(card.get("レースコード")); names={b:clean_name(card.get(f"艇{b}_選手名","")) for b in BOATS}
   if d>=date(2026,3,1) and all(names.values()):
    q={'race_code':code}
    for b,n in names.items():
     st=pstat(state[n],b)
     for k,v in st.items():q[f"b{b}_pl_{k}"]=v
    rec.append(q)
   rr=results.get(code)
   if rr:
    try:w=int(float(rr.get("1着_艇番")));sec=int(float(rr.get("2着_艇番")))
    except:continue
    if w not in BOATS or sec not in BOATS or w==sec:continue
    for b,n in names.items():
     if not n:continue
     s=state[n];s['n']+=1;s['w']+=int(w==b);s['p2']+=int(w==b or sec==b);s['nf'][b]+=1;s['wf'][b]+=int(w==b);s['p2f'][b]+=int(w==b or sec==b);s['r'].append(int(w==b or sec==b))
  d+=timedelta(days=1)
 return pd.DataFrame(rec)
def fit(tr,qs,feats):
 p=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))]);p.fit(tr[feats],tr.head4)
 return [p.predict_proba(q[feats])[:,1] for q in qs]
def main():
 z=pd.read_csv(BASE,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12);z['month']=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 t=pd.read_csv(TRUTH,usecols=['race_code','head4'],dtype={'race_code':str});t.race_code=t.race_code.astype(str).str.zfill(12)
 z=z.merge(t,on='race_code',how='left',validate='one_to_one');z=z[z.head4.isin([0,1])].copy()
 # Parent may already contain PLAYER_HISTORY. Avoid pandas _x/_y collisions by using
 # the independently rebuilt causal PH table as the canonical source.
 phcols=[x for x in z.columns if '_pl_' in x]
 if phcols:z=z.drop(columns=phcols)
 z=z.merge(w4.build_waku(z.race_code.tolist()),on='race_code',how='left',validate='one_to_one').merge(build_ph(),on='race_code',how='left',validate='one_to_one')
 forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
 numeric=[c for c in z if c not in {'head4','race_code','month'} and pd.to_numeric(z[c],errors='coerce').notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forbidden)]
 added=[c for c in numeric if c.startswith('w10_') or '_pl_' in c or c.startswith('opp_waku_b')]
 base=[c for c in numeric if c not in added]
 # Baseline reduction families: remove correlated/low-priority blocks from original head features.
 def keep(excludes):return [c for c in base if not any(x in c.lower() for x in excludes)]
 reduced={
  'BASE_FULL':base,
  'BASE_DROP_BOAT':keep(('boat_top',)),
  'BASE_DROP_LOCAL':keep(('local_',)),
  'BASE_DROP_TOP3':keep(('top3',)),
  'BASE_CORE':keep(('boat_top','local_','top3')),
 }
 ph4=['b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_win','b4_pl_frame_p2','b4_pl_recent_p2']
 phrel=[]
 for k in ('all_win','all_p2','frame_win','frame_p2','recent_p2'):
  z[f'rel4_b3_pl_{k}']=z[f'b4_pl_{k}']-z[f'b3_pl_{k}'];phrel.append(f'rel4_b3_pl_{k}')
 waku=['w10_rel4_b3_wr','w10_rel4_b3_st','w10_rel4_b3_sr']
 families={}
 for bn,bf in reduced.items():
  families[bn]=bf
  families[bn+'_PH4']=bf+ph4
  families[bn+'_PH4_REL43']=bf+ph4+phrel
  families[bn+'_PH4_W43']=bf+ph4+waku
  families[bn+'_PH4_REL43_W43']=bf+ph4+phrel+waku
 tr=z[z.month.isin(DEV)].copy();va=z[z.month.isin(VAL)].copy();ho=z[z.month.isin(HOLD)].copy()
 out=[]
 for label,feats in families.items():
  ps=fit(tr,[tr,va,ho],feats)
  for q,p in zip((tr,va,ho),ps):q[label]=p
  cand=[]
  for cut in np.arange(.10,.501,.01):
   s=va[va[label]>=cut]
   if len(s)>=45:cand.append((float(s.head4.mean()),len(s),float(cut)))
  if not cand:continue
  chosen=sorted(cand,key=lambda x:(x[0],x[1]),reverse=True)[0][2]
  for period,q in [('DEV',tr),('VAL',va),('HOLD',ho)]:
   s=q[q[label]>=chosen];out.append({'model':label,'period':period,'cut':chosen,'features':len(feats),'R':len(s),'head4':int(s.head4.sum()),'rate':float(s.head4.mean()) if len(s) else None})
 comp=pd.DataFrame(out);comp.to_csv(OUT/'comparison.csv',index=False)
 val=comp[comp.period.eq('VAL')].sort_values(['rate','R'],ascending=[False,False]);val.to_csv(OUT/'validation_ranking.csv',index=False)
 meta={'selection':'June only; >=45 selections to preserve volume','holdout_used_for_selection':False,'feature_ablation':list(reduced),'player_history_features':ph4+phrel,'waku43_features':waku,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'note':'historical results only update causal prior-day PLAYER_HISTORY state; target labels attached after feature construction'}
 (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
 print(comp.to_string(index=False));print("TOP_JUNE");print(val.head(12).to_string(index=False));print(json.dumps(meta,ensure_ascii=False));print("HEAD4_PLAYER_WAKU_SOFT_ABLATION_V23_OK");print("SEPTEMBER_UNREAD")
if __name__=='__main__':main()
