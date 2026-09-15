from __future__ import annotations
import argparse, json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
from statistics import mean
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct, ff, norm_metric

CANDS=[1,2,4,5,6]
STATIC=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','モーター2連対率','モーター3連対率','ボート2連対率']
DIRECT_COMMON=['ex','st']; DIRECT_ORIG=['turn','straight','lap','avg']

def bycode(rs): return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def combo(x):
 s=''.join(c for c in str(x) if c.isdigit()); return tuple(map(int,s[:3])) if len(s)>=3 else None
def st_bias(sums,allv):
 g=mean(allv) if allv else .15
 return {b:(mean(sums[b])-g if sums[b] else 0.) for b in range(1,7)}
def update_st(rs,sums,allv):
 for r in rs:
  for b in range(1,7):
   v=ff(r.get(f'艇{b}_スタート展示'))
   if v is not None and -.30<v<1.: sums[b].append(v); allv.append(v)
def orig_all6(r,target):
 if not r:return False
 for k in range(1,5):
  if norm_metric(r.get(f'計測項目{k}',''))==target and all(ff(r.get(f'艇{b}_値{k}')) is not None for b in range(1,7)):return True
 return False

def load_direct(codes):
 wanted=set(codes); days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted}); out={}; sums=defaultdict(list);allv=[]
 d=date(2025,10,1); last=max(days); dayset=set(days)
 while d<=last:
  ymd=d.strftime('%Y/%m/%d'); sr=rows(f'data/previews/stt/{ymd}.csv'); bias=st_bias(sums,allv)
  if d in dayset:
   tk=bycode(rows(f'data/previews/tkz/{ymd}.csv')); st=bycode(sr); og=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    tr=tk.get(code,{}); ss=st.get(code,{}); oo=og.get(code,{})
    common=bool(tr and ss and all(ff(tr.get(f'艇{b}_展示タイム')) is not None for b in range(1,7)) and all(ff(ss.get(f'艇{b}_スタート展示')) is not None for b in range(1,7)))
    ex,stsc,os=corrected_direct(code,tk,st,og,bias)
    out[code]={'common':common,'ex':ex,'st':stsc,'os':os,'turn':orig_all6(oo,'回り足') or orig_all6(oo,'まわり足'),'straight':orig_all6(oo,'直線'),'lap':orig_all6(oo,'一周')}
  update_st(sr,sums,allv); d+=timedelta(days=1)
 return out

def base_rows(races,direct,variant,venue_ok):
 rr=[]
 for _,r in races.iterrows():
  code=str(int(r.rc)).zfill(12); actual=combo(r.settle__actual_combo); di=direct.get(code)
  if variant!='A' and (not di or not di['common']):continue
  jcd=code[8:10]
  for a in CANDS:
   for b in CANDS:
    if a==b:continue
    z={'race_code':code,'second':a,'third':b,'y':int(actual==(3,a,b))}
    for lane in CANDS:z[f'slane{lane}']=int(a==lane);z[f'tlane{lane}']=int(b==lane)
    for m in STATIC:
     va=pd.to_numeric(r[f'card__艇{a}_{m}'],errors='coerce');vb=pd.to_numeric(r[f'card__艇{b}_{m}'],errors='coerce');v3=pd.to_numeric(r[f'card__艇3_{m}'],errors='coerce')
     for n,v in [('s',va),('t',vb),('sg3',va-v3),('tg3',vb-v3),('smt',va-vb),('pm',(va+vb)/2)]:z[f'{n}_{m}']=v
    z['same_side']=int((a<3)==(b<3));z['second_inner']=int(a<3);z['third_inner']=int(b<3)
    if variant in ('B','C'):
     for m in DIRECT_COMMON:
      q=di[m];z[f's_{m}']=q[a];z[f't_{m}']=q[b];z[f'sg3_{m}']=q[a]-q[3];z[f'tg3_{m}']=q[b]-q[3];z[f'smt_{m}']=q[a]-q[b];z[f'head3_{m}']=q[3]
    if variant=='C':
     for m in ['turn','straight','lap']:
      q={x:di['os'][x][m] for x in range(1,7)}; ready=venue_ok.get(jcd,{}).get(m,False) and di[m]
      if ready:
       z[f's_{m}']=q[a];z[f't_{m}']=q[b];z[f'sg3_{m}']=q[a]-q[3];z[f'tg3_{m}']=q[b]-q[3];z[f'smt_{m}']=q[a]-q[b];z[f'head3_{m}']=q[3]
     q={x:di['os'][x]['avg'] for x in range(1,7)}
     if venue_ok.get(jcd,{}).get('avg',False):
      z['s_avg']=q[a];z['t_avg']=q[b];z['sg3_avg']=q[a]-q[3];z['tg3_avg']=q[b]-q[3];z['smt_avg']=q[a]-q[b];z['head3_avg']=q[3]
    rr.append(z)
 return pd.DataFrame(rr)
def cvscore(x):
 feats=[c for c in x if c not in ['race_code','second','third','y']]; caps=[];aucs=[]
 for tr,va in GroupKFold(5).split(x,groups=x.race_code):
  m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0));m.fit(x.iloc[tr][feats],x.iloc[tr].y);v=x.iloc[va].copy();v['p']=m.predict_proba(v[feats])[:,1]
  top=v.sort_values(['race_code','p','second','third'],ascending=[1,0,1,1]).groupby('race_code').head(3); truth=v[v.y.eq(1)][['race_code','second','third']];caps.append(sum(((g.y==1).any()) for _,g in top.groupby('race_code'))/max(1,len(truth)));aucs.append(roc_auc_score(v.y,v.p))
 return {'features':len(feats),'capture':float(np.mean(caps)),'auc':float(np.mean(aucs)),'fold_capture':caps}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',default='analysis_v289_3head_wave21_allrace_feature_settled.csv');ap.add_argument('--phase',choices=['feb','march'],default='feb');a=ap.parse_args()
 use=['date','race_code_norm','settle__actual_combo','settle__winner']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC];df=pd.read_csv(a.source,usecols=use,low_memory=False);df.date=pd.to_datetime(df.date);df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64');feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')&(df.settle__winner==3)].copy()
 direct=load_direct([str(int(x)).zfill(12) for x in feb.rc.dropna()]); venue_ok={}
 for jcd in sorted({str(int(x)).zfill(12)[8:10] for x in feb.rc.dropna()}):
  cs=[c for c in direct if c[8:10]==jcd];venue_ok[jcd]={m:(sum(bool(direct[c].get(m,False)) for c in cs)/len(cs)>=.8 if cs else False) for m in ['turn','straight','lap']};venue_ok[jcd]['avg']=any(venue_ok[jcd].values())
 res={}
 for v in 'ABC':
  x=base_rows(feb,direct,v,venue_ok);res[v]={'pair_rows':len(x),'races':x.race_code.nunique(),**cvscore(x)}
 winner=max(res,key=lambda k:(res[k]['capture'],res[k]['auc']));out={'phase':'FEB_ONLY_FREEZE','results':res,'frozen_winner':winner,'venue_ok':venue_ok,'september_outcomes_read':False,'production_changed':False};Path('research_v289_3head_exhibition_v5_feb.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
