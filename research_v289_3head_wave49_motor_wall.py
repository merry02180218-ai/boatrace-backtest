from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave47_head_condition_zoning as w47
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASE=Path('v288_operational_pre_replay_94_baseline_codes.csv')
CUT=.365448

def n(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')
def c(d,b,m): return n(d[f'card__艇{b}_{m}'])
def feat(d):
    x=pd.DataFrame(index=d.index)
    m23,m22=c(d,3,'モーター2連対率'),c(d,2,'モーター2連対率')
    m33,m32=c(d,3,'モーター3連対率'),c(d,2,'モーター3連対率')
    st3,st2=c(d,3,'全国平均ST'),c(d,2,'全国平均ST')
    x['m2gap']=m23-m22; x['m3gap']=m33-m32; x['stgap']=st3-st2
    x['b2m2']=m22; x['b2m3']=m32; x['b2st']=st2
    x['m2_st']=x.m2gap*(st2-st3); x['m3_st']=x.m3gap*(st2-st3)
    return x

def run(train,test):
    p3,tops=w47.wave36(base.build_static(train),train.settle__actual_combo.astype(str),base.build_static(test))
    q=test[['date','race_code','settle__actual_combo']].copy().reset_index(drop=True)
    q['p3']=p3; q['top5']=tops; q=q[q.p3>=CUT].copy().reset_index(drop=True)
    allx=pd.concat([train,test],ignore_index=True); X=feat(allx)
    y=train.settle__actual_combo.astype(str).str.startswith('3-').astype(int)
    model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.08,class_weight='balanced'))
    model.fit(X.iloc[:len(train)],y); sc=model.predict_proba(X.iloc[len(train):])[:,1]
    sm=test[['race_code']].copy().reset_index(drop=True); sm['score']=sc
    q=q.merge(sm,on='race_code'); q['head3']=q.settle__actual_combo.str.startswith('3-').astype(int); q['hit']=np.array([a in t.split(';') for a,t in zip(q.settle__actual_combo,q.top5)],dtype=int)
    return q

def st(q):
    return {'races':len(q),'head_hits':int(q['head3'].sum()),'head_rate':float(q['head3'].mean()) if len(q) else None,'ticket_hits':int(q['hit'].sum()),'ticket_rate':float(q['hit'].mean()) if len(q) else None}

def main():
    d=pd.read_csv(SRC,dtype=str).fillna(''); d=d[d.date<'2026-09-01'].copy(); d['month']=d.date.str[:7]
    ex=set(pd.read_csv(BASE,dtype=str).race_code.astype(str)); assert len(ex)==94
    d=d[~d.race_code.astype(str).isin(ex)]; d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True)
    feb=d[d.month=='2026-02'].copy(); mar=d[d.month=='2026-03'].copy(); q=run(feb,mar).sort_values(['date','race_code']).reset_index(drop=True)
    base_s=st(q); th=float(q.score.quantile(.40)); s=q[q.score>=th].copy(); mid=len(q)//2; boundary=q.iloc[mid-1].date+'|'+q.iloc[mid-1].race_code; k=s.date+'|'+s.race_code
    out={'wave':'49-motor-wall','march_baseline':base_s,'march_wave49':st(s),'early':st(s[k<=boundary]),'late':st(s[k>boundary]),'keep':.60,'threshold':th,'head_lift':st(s)['head_rate']-base_s['head_rate'],'september_outcomes_read':False,'jul_aug_used':False,'adoption_status':'NO_ADOPTION_NO_PRISTINE_PERIOD'}
    Path('research_v289_3head_wave49_motor_wall.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False),flush=True)
if __name__=='__main__': main()
