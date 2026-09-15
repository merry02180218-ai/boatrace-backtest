#!/usr/bin/env python3
"""Wave9: Kiryu boat2 KEEP/DROP composite guard with strict fold-local LOO preprocessing."""
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

IN='analysis_v351_kiryu_boat2_wave8.csv'
OUT='analysis_v351_kiryu_boat2_wave9_loo.csv'
SUM='analysis_v351_kiryu_boat2_wave9_loo_summary.csv'
SHARED=['b2_ex','b2_ex_rank','b2_ex_vs_best','b2_st','b2_st_rank','b2_st_vs_best','b2_turn','b2_turn_rank','b2_turn_vs_best','b2_straight','b2_straight_rank','b2_straight_vs_best','b2_orig_avg','b2_orig_avg_rank','b2_orig_avg_vs_best']
HALF=['b2_half','b2_half_rank','b2_half_vs_best']

def loo(q,features,name,C):
 rows=[]
 for i in range(len(q)):
  tr=q.index!=q.index[i]; te=~tr
  Xtr=q.loc[tr,features]; ytr=q.loc[tr,'keep2'].astype(int); Xte=q.loc[te,features]
  pipe=Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler()),('lr',LogisticRegression(C=C,class_weight='balanced',max_iter=5000))])
  pipe.fit(Xtr,ytr); p=float(pipe.predict_proba(Xte)[0,1]); pred=int(p>=.5)
  r=q.iloc[i]
  rows.append({'model':name,'C':C,'race_code':r.race_code,'actual_keep2':int(r.keep2),'pred_keep2':pred,'p_keep2':p,'correct':int(pred==int(r.keep2))})
 return rows

def main():
 q=pd.read_csv(IN,dtype={'race_code':str});q.race_code=q.race_code.astype(str).str.zfill(12);q=q[q.race_code.str[:8]<'20260901'].reset_index(drop=True)
 allrows=[]
 for C in [.01,.03,.1,.3,1.0]:
  allrows+=loo(q,SHARED,'SHARED',C);allrows+=loo(q,SHARED+HALF,'SHARED_PLUS_HALF',C)
 o=pd.DataFrame(allrows);o.to_csv(OUT,index=False,encoding='utf-8-sig')
 ss=[]
 for (m,C),g in o.groupby(['model','C']):
  y=g.actual_keep2.to_numpy();p=g.pred_keep2.to_numpy();tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
  # DROP2 is positive operational action: predicted keep=0
  drop_pred=int((p==0).sum());drop_actual=int((y==0).sum());drop_tp=int(((p==0)&(y==0)).sum());false_drop=int(((p==0)&(y==1)).sum())
  ss.append({'model':m,'C':C,'R':len(g),'accuracy':accuracy_score(y,p),'drop_pred':drop_pred,'drop_actual':drop_actual,'correct_drop':drop_tp,'false_drop_damage':false_drop,'drop_precision':drop_tp/drop_pred if drop_pred else np.nan,'drop_recall':drop_tp/drop_actual if drop_actual else np.nan,'keep_correct':int(((p==1)&(y==1)).sum())})
 s=pd.DataFrame(ss).sort_values(['C','model']);s.to_csv(SUM,index=False,encoding='utf-8-sig')
 print('KIRYU_R',len(q),'KEEP2',int(q.keep2.sum()),'DROP2',int((1-q.keep2).sum()))
 print(s.to_string(index=False))
 # paired half increment at each C
 for C in sorted(s.C.unique()):
  a=s[(s.C==C)&(s.model=='SHARED')].iloc[0];b=s[(s.C==C)&(s.model=='SHARED_PLUS_HALF')].iloc[0]
  print('HALF_INCREMENT','C',C,'ACC_PP',(b.accuracy-a.accuracy)*100,'DROP_CORRECT_DELTA',int(b.correct_drop-a.correct_drop),'FALSE_DROP_DELTA',int(b.false_drop_damage-a.false_drop_damage))
 print('SEPTEMBER_OUTCOMES_USED',False);print('PRODUCTION_CHANGED',False)
if __name__=='__main__':main()
