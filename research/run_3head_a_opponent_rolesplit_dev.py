#!/usr/bin/env python3
"""3HEAD A+.60 role-split opponent development.
Selection/development: Nov 2025-Jan 2026 only. March never used here. Sep-2026 unread.
Architecture follows 1HEAD/4HEAD: separate SECOND and conditional THIRD, compared with V221 direct pair.
"""
from __future__ import annotations
import json, numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import analyze_v221_3head_scenario_pair as v221

OPP=[1,2,4,5,6]
MONTHS=['2025-11','2025-12','2026-01']

def ii(x,d=0):
 try:return int(float(x))
 except:return d

def combo(x):
 return v221.v166.combo(x)

def candidate_vec(r,b,role,sec=0):
 # Candidate-local player/history + prior exhibition, plus position and 3-attack context.
 x=[float(b),float(b in (1,2)),float(b in (4,5,6)),float(b==1),float(b==2),float(b==4),float(b==5),float(b==6)]
 for k in ['vh_p12_display','vh_p12_overall','vh_p12_turn','vh_p12_straight','vh_delta_display','vh_delta_turn','vh_delta_straight',
           'pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2']:
  x.append(v221.xtra(r,b,k))
 # relative to attacking boat3
 for k in ['vh_p12_display','vh_p12_turn','vh_p12_straight','pl_all_win','pl_all_p2','pl_frame_p2']:
  x.append(v221.xtra(r,b,k)-v221.xtra(r,3,k))
 mak=v221.ff(r.get('structure_3makuri'),v221.ff(r.get('score_3makuri'),.5))
 ms=v221.ff(r.get('structure_3makurizashi'),v221.ff(r.get('score_3makurizashi'),.5))
 x += [mak,ms,mak-ms,mak*float(b in (1,2)),mak*float(b in (4,5,6)),ms*float(b in (1,2)),ms*float(b in (4,5,6))]
 if role=='THIRD':
  x += [float(sec),float(sec in (1,2)),float(sec in (4,5,6)),float(b<sec),float(b>sec)]
  for k in ['vh_p12_display','vh_p12_turn','vh_p12_straight','pl_all_win','pl_frame_p2']:
   x.append(v221.xtra(r,b,k)-v221.xtra(r,sec,k))
 return np.asarray(x,float)

def fit_role(train,role):
 X=[];y=[];n=0
 for _,r in train.iterrows():
  a=combo(r.get('actual_combo'))
  if len(a)!=3 or a[0]!=3 or a[1] not in OPP or a[2] not in OPP or a[1]==a[2]:continue
  n+=1;sec=a[1]
  for b in OPP:
   if role=='THIRD' and b==sec:continue
   X.append(candidate_vec(r,b,role,sec)); y.append(int(b==(a[1] if role=='SECOND' else a[2])))
 if n<40: raise RuntimeError(f'{role} training 3-head races too small: {n}')
 m=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))]);m.fit(np.asarray(X),np.asarray(y));return m,n

def role_order(r,m,role,sec=0):
 z=[]
 for b in OPP:
  if role=='THIRD' and b==sec:continue
  p=float(m.predict_proba(candidate_vec(r,b,role,sec).reshape(1,-1))[0,1]);z.append((p,b))
 return sorted(z,key=lambda q:(-q[0],q[1]))

def pair_order(r,sm,tm):
 ss=role_order(r,sm,'SECOND');z=[]
 for ps,s in ss:
  for pt,t in role_order(r,tm,'THIRD',s):
   z.append((ps*pt,s,t))
 z.sort(key=lambda q:(-q[0],q[1],q[2]));return z

def ranks(actual,ss,tt,pairs):
 s,t=actual
 sr=next(i+1 for i,(_,b) in enumerate(ss) if b==s)
 tr=next(i+1 for i,(_,b) in enumerate(tt) if b==t)
 pr=next(i+1 for i,(_,a,b) in enumerate(pairs) if a==s and b==t)
 return sr,tr,pr

def main():
 raw=pd.read_csv(v221.SRC,dtype={'race_code':str});dc=v221.v165.pc(raw,['date','race_date','ymd']);vc=v221.v165.pc(raw,['venue','jcd','stadium','place'])
 y,_=v221.v165.target(raw);basefs=v221.v165.feats(raw);raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y
 raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<v221.CONTAM)].copy();d=v221.build(raw,dc)
 # Cohort membership is reconstructed from frozen A+.60 race codes produced by the adopted loss-structure development.
 import sys;sys.path.insert(0,str(v221.ROOT/'research'))
 import run_3head_a_loss_structure_dev as ls
 import run_3head_wave20_manual_gate as w20
 rr={}
 for k,(a,b) in ls.DEV.items():
  x,res,audit=w20.build_pre_enhanced(a,b,True);rr[k]=(x,res)
 fr={k:w20.prep_month(x,res) for k,(x,res) in rr.items()};scores,_=w20.make_pre_scores(fr);days,cache=w20.prefetch_sources();post,_=w20.build_motor_exhibition(days,cache)
 selected={}
 for k in ['nov','dec','jan']:
  q=scores[k].merge(post,on=['rc','date'],how='left',validate='one_to_one');rn=pd.to_numeric(q.race_no,errors='coerce');pre=pd.to_numeric(q.pre_score,errors='coerce')
  m=(rn>=1)&(rn<=12)&(pre>=.925)&ls.mask(q,ls.A['conds'])&(pd.to_numeric(q.post_motor_inner_rank_edge,errors='coerce')>=.60)
  selected[k]=set(str(int(x)).zfill(12) for x in q.loc[m,'rc'])
 if sum(map(len,selected.values()))!=118:raise RuntimeError('adopted cohort drift')
 rec=[]
 for mon in MONTHS:
  first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first]
  sm,ns=fit_role(tr,'SECOND');tm,nt=fit_role(tr,'THIRD');direct,_=v221.fit_pair(tr,True)
  te=d[(d._date>=first)&(d._date<nextm)&d.race_code.astype(str).str.zfill(12).isin(selected[{'2025-11':'nov','2025-12':'dec','2026-01':'jan'}[mon]])].copy()
  for _,r in te.iterrows():
   a=combo(r.get('actual_combo'))
   if len(a)!=3 or a[0]!=3:continue
   ss=role_order(r,sm,'SECOND');tt=role_order(r,tm,'THIRD',a[1]);po=pair_order(r,sm,tm)
   sr,trr,pr=ranks((a[1],a[2]),ss,tt,po)
   vo=v221.order(r,direct,True);actual=f'3-{a[1]}-{a[2]}';vr=vo.index(actual)+1
   rec.append({'month':mon,'race_code':str(r.race_code).zfill(12),'second':a[1],'third':a[2],'second_rank':sr,'third_rank_cond_actual_second':trr,'pair_rank_factorized':pr,'pair_rank_v221':vr})
 z=pd.DataFrame(rec)
 if len(z)!=54:raise RuntimeError(f'head-win cohort drift {len(z)} !=54')
 def met(g):
  return {'n':len(g),'second_top1':float((g.second_rank<=1).mean()),'second_top2':float((g.second_rank<=2).mean()),
   'third_top1':float((g.third_rank_cond_actual_second<=1).mean()),'third_top2':float((g.third_rank_cond_actual_second<=2).mean()),
   **{f'factor_pair_top{k}':float((g.pair_rank_factorized<=k).mean()) for k in [1,2,4,6,10]},
   **{f'v221_pair_top{k}':float((g.pair_rank_v221<=k).mean()) for k in [1,2,4,6,10]}}
 out={'policy':{'head_purchase':'A+.60 frozen','selection_months':MONTHS,'march_used':False,'sep2026_used':False,'odds_used':False},
      'overall':met(z),'monthly':{m:met(g) for m,g in z.groupby('month')},'rows':z.to_dict('records')}
 open('research_3head_a_opponent_rolesplit_dev.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
 z.to_csv('research_3head_a_opponent_rolesplit_dev.csv',index=False)
 print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
